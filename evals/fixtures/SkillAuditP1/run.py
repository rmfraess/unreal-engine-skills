"""Build and run the isolated P1 probe; requires UE_ENGINE_ROOT and Windows UE 5.8.2."""
import json
import os
from pathlib import Path
import subprocess


def main():
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
    subprocess.run([
        str(engine / "Build/BatchFiles/Build.bat"), "SkillAuditP1Editor", "Win64", "Development",
        str(project / "SkillAuditP1.uproject"), "-WaitMutex", "-NoHotReloadFromIDE", "-NoUBA",
        "-Log=" + str(saved / "Build.log"),
    ], env=env, check=True, timeout=600)

    report = saved / "Report/index.json"
    # Never accept a previous run's report as this execution's evidence.
    report.unlink(missing_ok=True)
    args = [
        str(engine / "Binaries/Win64/UnrealEditor-Cmd.exe"), str(project / "SkillAuditP1.uproject"),
        "-unattended", "-nopause", "-nop4", "-nosplash", "-nullrhi",
        "-ddc=InstalledNoZenLocalFallback", "-LocalDataCachePath=" + str(saved / "DDC"),
        "-SharedDataCachePath=None", "-UserDir=" + str(saved / "User"),
        "-abslog=" + str(saved / "Probe.log"), "-ReportExportPath=" + str(report.parent),
        "-ExecCmds=Automation RunTests SkillAudit.P1;Quit",
    ]
    print(subprocess.list2cmdline(args), flush=True)
    with (saved / "Process.log").open("w", encoding="utf-8") as log:
        subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=300)
    results = json.loads(report.read_text(encoding="utf-8-sig"))
    tests = results["tests"]
    assert len(tests) == 1, results
    assert tests[0]["fullTestPath"] == "SkillAudit.P1.CoreContracts", tests
    assert tests[0]["state"] == "Success", tests
    assert results["failed"] == 0 and results["notRun"] == 0, results
    print("PASS: SkillAudit.P1.CoreContracts; fresh editor report:", report)


if __name__ == "__main__":
    main()
