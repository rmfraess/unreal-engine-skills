"""Build and run the isolated UE 5.8.2 contract probes."""
import argparse
import json
import msvcrt
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


COMPLETION_PATTERN = re.compile(r"\*\*\*\* TEST COMPLETE\. EXIT CODE: (-?\d+) \*\*\*\*")
BUILD_TIMEOUT = 600
EDITOR_TIMEOUT = 300
READINESS_TIMEOUT = 5


def run_editor_case(engine, project, saved, env, *, name, test, command, quit_command,
                    expect_failure, expect_process_failure=False, require_marker=True,
                    extra_args=()):
    case_dir = saved / "AutomationCI" / name
    if case_dir.exists():
        deadline = time.monotonic() + READINESS_TIMEOUT
        while True:
            try:
                shutil.rmtree(case_dir)
                break
            except PermissionError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
    report_dir = case_dir / "Report"
    report_dir.mkdir(parents=True)
    report = report_dir / "index.json"
    args = [
        str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(project / "SkillAuditP1.uproject"),
        "-unattended", "-nopause", "-nop4", "-nosplash", "-nullrhi",
        "-ddc=InstalledNoZenLocalFallback", "-LocalDataCachePath=" + str(saved / "DDC"),
        "-SharedDataCachePath=None", "-UserDir=" + str(case_dir / "User"),
        "-abslog=" + str(case_dir / "Editor.log"), "-ReportExportPath=" + str(report_dir),
        f"-ExecCmds=Automation {command} {test};{quit_command}",
        *extra_args,
    ]
    command_line = subprocess.list2cmdline(args)
    (case_dir / "Command.txt").write_text(command_line + "\n", encoding="utf-8")
    print(command_line, flush=True)

    timed_out = False
    return_code = None
    try:
        with (case_dir / "Process.log").open("w", encoding="utf-8") as log:
            completed = subprocess.run(
                args, env=env, stdout=log, stderr=subprocess.STDOUT,
                check=False, timeout=EDITOR_TIMEOUT,
            )
        return_code = completed.returncode
    except subprocess.TimeoutExpired:
        timed_out = True

    editor_log = case_dir / "Editor.log"
    log_text = ""
    results = None
    read_error = None
    deadline = time.monotonic() + READINESS_TIMEOUT
    while time.monotonic() < deadline:
        try:
            log_text = editor_log.read_text(encoding="utf-8", errors="replace")
            parsed = json.loads(report.read_text(encoding="utf-8-sig"))
            if not isinstance(parsed, dict):
                raise TypeError("report root is not an object")
            results = parsed
            if not require_marker or COMPLETION_PATTERN.search(log_text):
                read_error = None
                break
        except TypeError as error:
            read_error = str(error)
            break
        except (OSError, UnicodeError, ValueError) as error:
            read_error = str(error)
        time.sleep(0.1)
    markers = COMPLETION_PATTERN.findall(log_text)
    marker_exit_code = int(markers[-1]) if markers else None
    report_error = read_error
    if results is not None:
        try:
            tests = results.get("tests")
            if not isinstance(tests, list) or len(tests) != 1:
                raise ValueError("report must contain exactly one test")
            result = tests[0]
            if not isinstance(result, dict) or result.get("fullTestPath") != test:
                raise ValueError(f"report does not contain expected test {test}")
            if results.get("notRun") != 0 or results.get("inProcess") != 0:
                raise ValueError("report contains incomplete tests")
            if expect_failure:
                if result.get("state") != "Fail" or results.get("failed") != 1 or result.get("errors", 0) < 1:
                    raise ValueError("report does not contain the expected failure")
            elif (result.get("state") != "Success"
                  or results.get("succeeded", 0) + results.get("succeededWithWarnings", 0) != 1
                  or results.get("failed") != 0):
                raise ValueError("report does not contain the expected success")
        except (TypeError, ValueError) as error:
            report_error = str(error)

    evidence = {
        "command": command_line,
        "expectedTest": test,
        "expectedFailure": expect_failure,
        "expectedProcessFailure": expect_process_failure,
        "quitCommand": quit_command,
        "timedOut": timed_out,
        "processExitCode": return_code,
        "completionMarkerExitCode": marker_exit_code,
        "report": str(report),
        "reportCreatedOn": results.get("reportCreatedOn") if isinstance(results, dict) else None,
        "reportError": report_error,
    }
    (case_dir / "Result.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )

    failures = []
    if timed_out:
        failures.append("editor process timed out")
    if require_marker and marker_exit_code is None:
        failures.append("completion marker is missing")
    if report_error:
        failures.append(f"report is missing or incomplete: {report_error}")
    if expect_process_failure:
        if return_code in (None, 0):
            failures.append(f"expected non-zero process status, got {return_code}")
    elif return_code != 0:
        failures.append(f"expected zero process status, got {return_code}")
    if expect_failure:
        if marker_exit_code == 0:
            failures.append(f"failing test marker reported {marker_exit_code}")
    else:
        if marker_exit_code not in (None, 0):
            failures.append(f"passing test marker reported {marker_exit_code}")
    if failures:
        raise AssertionError("; ".join(failures))

    outcome = "EXPECTED FAILURE" if expect_failure else "PASS"
    print(f"{outcome}: {test}; evidence: {case_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-ci-contract", action="store_true")
    args = parser.parse_args()
    root = os.environ.get("UE_ENGINE_ROOT")
    if not root:
        raise SystemExit("Set UE_ENGINE_ROOT to the directory containing Engine/.")
    engine = Path(root).resolve() / "Engine"
    version = json.loads((engine / "Build/Build.version").read_text(encoding="utf-8"))
    actual = tuple(version[k] for k in ("MajorVersion", "MinorVersion", "PatchVersion"))
    if actual != (5, 8, 2) or version["Changelist"] != 56702186:
        raise SystemExit(f"Expected UE 5.8.2 / CL 56702186, got {version}")
    project = Path(__file__).resolve().parent
    saved = project / "Saved"
    for folder in (saved / "Temp", project / "Content"):
        folder.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "TEMP": str(saved / "Temp"), "TMP": str(saved / "Temp"),
        "DOTNET_CLI_HOME": str(saved / "DotNet"),
        "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1", "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
        "UE-LocalDataCachePath": str(saved / "DDC"), "UE-SharedDataCachePath": "None",
    })

    lock_path = saved / "AutomationCI.lock"
    with lock_path.open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        # ponytail: global fixture lock; split per case only if parallel throughput matters.
        case_count = 3 if args.verify_ci_contract else 1
        lock_timeout = BUILD_TIMEOUT + case_count * (EDITOR_TIMEOUT + 2 * READINESS_TIMEOUT)
        deadline = time.monotonic() + lock_timeout + READINESS_TIMEOUT
        while True:
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise SystemExit("Timed out waiting for another SkillAuditP1 run.")
                time.sleep(0.25)
        try:
            subprocess.run([
                str(engine / "Build/BatchFiles/Build.bat"), "SkillAuditP1Editor", "Win64", "Development",
                str(project / "SkillAuditP1.uproject"), "-WaitMutex", "-NoHotReloadFromIDE", "-NoUBA",
                "-Log=" + str(saved / "Build.log"),
            ], env=env, check=True, timeout=BUILD_TIMEOUT)
            run_editor_case(
                engine, project, saved, env,
                name="pass", test="SkillAudit.P1.CoreContracts",
                command="RunTests", quit_command="SoftQuit", expect_failure=False,
            )
            if not args.verify_ci_contract:
                return
            run_editor_case(
                engine, project, saved, env,
                name="intentional-failure-quit", test="SkillAudit.P2.AutomationFailureProbe",
                command="RunTest", quit_command="Quit", expect_failure=True,
                expect_process_failure=True,
                require_marker=False,
                extra_args=("-SkillAuditIntentionalFailure",),
            )
            run_editor_case(
                engine, project, saved, env,
                name="intentional-failure-softquit", test="SkillAudit.P2.AutomationFailureProbe",
                command="RunTest", quit_command="SoftQuit", expect_failure=True,
                extra_args=("-SkillAuditIntentionalFailure",),
            )
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
