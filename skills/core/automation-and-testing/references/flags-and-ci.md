# `EAutomationTestFlags`, CI patterns & Gauntlet — deep reference

Deep dive for [../SKILL.md](../SKILL.md). Covers the full `EAutomationTestFlags`
reference, CI command-line recipes, report export, and a Gauntlet overview. Grounded
in UE 5.8 (`Runtime/Core/Public/Misc/AutomationTest.h`:88).

## `EAutomationTestFlags` reference

Every test must OR together at least one **context** flag and one **filter** flag.

### Context flags (where the test can run)

| Flag | Value | Meaning |
|---|---|---|
| `EditorContext` | `0x01` | within the editor |
| `ClientContext` | `0x02` | within a game client |
| `ServerContext` | `0x04` | within a dedicated server |
| `CommandletContext` | `0x08` | within a commandlet (`-run=...`) |
| `ProgramContext` | `0x10` | a standalone program (not editor/game) |

`EAutomationTestFlags_ApplicationContextMask` — a convenience constant that ORs all
five context flags. Common in specs that should run anywhere:
```cpp
EAutomationTestFlags::ProductFilter | EAutomationTestFlags_ApplicationContextMask
```

### Filter flags (which CI bucket)

| Flag | Value | Typical purpose |
|---|---|---|
| `SmokeFilter` | `0x01000000` | fastest; run on every commit, seconds |
| `EngineFilter` | `0x02000000` | engine-level tests, longer-running |
| `ProductFilter` | `0x04000000` | product/game-specific tests |
| `PerfFilter` | `0x08000000` | performance benchmarks |
| `StressFilter` | `0x10000000` | stress / stability |
| `NegativeFilter` | `0x20000000` | tests whose correct outcome is failure |

### Feature flags (optional runtime requirements)

| Flag | Value | Meaning |
|---|---|---|
| `NonNullRHI` | `0x0100` | requires a rendering backend |
| `RequiresUser` | `0x0200` | requires interactive user session |

### One-off flags

| Flag | Value | Meaning |
|---|---|---|
| `Disabled` | `0x10000` | skip without commenting out; never returned in filter |
| `SupportsAutoRTFM` | `0x20000` | run inside a transactional commit and an abort |

### Priority flags (UE5+)

| Flag | Value |
|---|---|
| `CriticalPriority` | `0x00100000` |
| `HighPriority` | `0x00200000` |
| `MediumPriority` | `0x00400000` |
| `LowPriority` | `0x00800000` |

Priority is optional but useful for CI triage. Tests without a priority flag are
treated as unclassified. Convenience masks: `EAutomationTestFlags_PriorityMask`,
`EAutomationTestFlags_HighPriorityAndAbove`, `EAutomationTestFlags_MediumPriorityAndAbove`.

## CI command-line recipes

### Run a test path prefix
```
UnrealEditor-Cmd.exe MyGame.uproject
  -ExecCmds="Automation RunTest StartsWith:MyGame.Combat;Quit"
  -unattended -nopause -nullrhi
```
`RunTest` and `RunTests` are both accepted aliases in UE 5.8.2. Bare terms use
substring matching; `StartsWith:` supplies prefix semantics.

### Run individual tests by name
```
-ExecCmds="Automation RunTest ^MyGame.Combat.DamageMath$+^MyGame.Inventory.AddItem$;Quit"
```
Separate filters with `+`; `^...$` selects a full test name exactly.

### Run a named test group
```
-ExecCmds="Automation RunTest Group:CI_Smoke;Quit"
```
`UAutomationControllerSettings::Groups` owns config-backed group names and filters.
Confirm the named group exists in the project before using it in CI.

### Export results
```
-ReportExportPath="TestResults/"
```
Writes JSON and HTML files consumable by the Automation Test Report Server.
Use a new empty directory for every ordinary CI launch. An old `index.json` can make a
terminated or incomplete launch look successful if the pipeline only checks that a file
exists.

### Resume an interrupted run
```
-ReportExportPath="TestResults/" -ResumeRunTest
```
Reads the existing JSON and skips tests already marked as run. In-progress tests
from the previous run are marked as failed. Use this only for intentional resumption, not
as the default CI recipe.

### Completion and exit-status contract

`RunTest`/`RunTests` queues test work. A following `Quit` or `SoftQuit` is also queued and
is processed only after earlier automation commands finish. `Quit` requests forced exit;
`SoftQuit` requests non-forced exit. At that final command, the controller checks report
errors and command-line errors, emits
`**** TEST COMPLETE. EXIT CODE: 0|-1 ****`, and requests process exit.

On Windows UE 5.8.2 / CL 56702186, the distinction affects observable status: forced
`Quit` terminates with the requested byte status (`-1` appears to the caller as non-zero),
and a live run left the just-emitted marker absent from the persisted log despite the forced
exit path's flush attempt. `SoftQuit` posts a clean quit request. A real failed `SoftQuit`
probe produced a failed fresh report and marker `-1` but process status `0`, because the
clean launch path returns its editor initialization result after leaving the main loop.
`-unattended` only suppresses interactive UI.

A CI wrapper should apply a bounded timeout and require every signal below:

1. The editor process exits before the timeout.
2. The process exit status is zero.
3. A fresh `ReportExportPath/index.json` exists, parses, contains the expected test set,
   and has zero `failed`, `notRun`, and `inProcess` counts.
4. For `SoftQuit`, the completion marker appears in the current launch's log and reports
   zero. Retain a `Quit` marker when present, but do not require it after forced termination.

Any non-zero process status, timeout, stale/missing report, incomplete counts, unexpected
test set, or missing/non-zero `SoftQuit` marker is unsuccessful verification. Wait for
process exit; do not infer completion from the report appearing on disk. For a regression
check of the wrapper itself, launch a deliberately failing test in a separate fresh process.
Prefer `Quit` when CI requires test failure to propagate as a non-zero process status; with
`SoftQuit`, the report and marker must reject the false-zero process result.

### Headless flags to always include in CI
```
-unattended      # suppress dialogs / pop-ups
-nopause         # do not pause on exit
-nullrhi         # skip GPU / render backend (for non-rendering tests)
-nosplash        # skip splash screen
```
Add `-nullrhi` only when tests do not require rendering. Remove it for
`NonNullRHI`-flagged tests, screenshot comparison tests, or any assertion whose evidence
depends on a rendered frame. A NullRHI run provides no rendering acceptance evidence.

## Test naming convention

The dotted `PrettyName` string should follow a `Namespace.Category.TestName`
pattern:
```
MyGame.Combat.DamageMath
MyGame.Inventory.AddItemIncreasesCount
```
- Put all tests for a module under the same top-level namespace.
- Keep names short; the full path must be unique across the project.
- File location convention: `Source/<Module>/Private/Tests/<ClassFilename>Test.cpp`.

## Suppressing log noise during tests

`FAutomationTestBase` has static flags for controlling how log output maps to test
results:

```cpp
FAutomationTestBase::bSuppressLogWarnings = true;   // don't fail on log warnings
FAutomationTestBase::bElevateLogWarningsToErrors = true; // turn warnings into errors
FAutomationTestBase::SuppressedLogCategories.Add(TEXT("LogNetTraffic"));
```

`AddExpectedMessage` / `AddExpectedError` registers patterns that, when logged during
a test, are consumed rather than counted as unexpected failures.

## Gauntlet overview

**Gauntlet** is Unreal's full-session automation harness, designed for:
- Device farms (console, mobile, PC).
- Multi-process tests (server + clients).
- Long-running perf and stress sessions.
- Build-and-deploy pipelines.

Gauntlet wraps an `FAutomationTestBase`-based or functional test run inside a
managed session:
1. Build and cook the project.
2. Deploy to target device(s) via Gauntlet infrastructure.
3. Launch game sessions, connect clients.
4. Run tests and capture logs, screenshots, profiling data.
5. Collect and report results.

Gauntlet tests are implemented as C# `ITestNode` scripts that orchestrate UE
sessions. They live outside the game project (in `Engine/Source/Programs/AutomationTool/`)
and are invoked via `RunUAT.bat`:

```
RunUAT.bat RunUnreal -Project=MyGame -Test=GauntletTest_MyGame -Platform=Win64 -Configuration=Development
```

Gauntlet is covered in the official docs at:
<https://dev.epicgames.com/documentation/unreal-engine/gauntlet-automation-framework-in-unreal-engine>

For most projects, functional tests + command-line automation runner cover CI needs.
Gauntlet is warranted when targeting multiple devices, needing real network sessions,
or running hour-scale stability/performance tests.

## Source citations (UE 5.8)

- `Runtime/Core/Public/Misc/AutomationTest.h`:88 — `EAutomationTestFlags` enum with
  all values and documentation comments.
- `Runtime/Core/Public/Misc/AutomationTest.h`:144–149 — convenience mask constants
  (`EAutomationTestFlags_ApplicationContextMask`, `EAutomationTestFlags_FilterMask`,
  `EAutomationTestFlags_PriorityMask`, etc.).
- `Runtime/Core/Public/Misc/AutomationTest.h`:1608–1611 — `bSuppressLogWarnings`,
  `bElevateLogWarningsToErrors`, `SuppressedLogCategories`.
- `Engine/Source/Developer/AutomationController/Private/AutomationCommandline.cpp`:133–163,
  211–227 — `+`, substring, prefix, and exact filters; :478–504 — queued quit completion,
  report-error check, marker, and status request; :610–628 — `RunTest`/`RunTests` aliases;
  :726–745 — forced `Quit` and non-forced `SoftQuit` queue entries.
- `Engine/Source/Developer/AutomationController/Public/AutomationControllerSettings.h`:
  185–216 — config-backed group names and filters.
- `Engine/Source/Developer/AutomationController/Private/AutomationControllerManager.cpp`:332–395 —
  report initialization and optional resume; :725–768 — JSON generation/write;
  :1093–1155 — final report export after test completion.
- `Engine/Source/Runtime/Core/Private/Windows/WindowsPlatformMisc.cpp`:1474–1521 — forced exit uses
  `TerminateProcess` with the requested status; non-forced exit uses `PostQuitMessage`.
- `Engine/Source/Runtime/Launch/Private/Launch.cpp`:146–204 — the clean editor main loop returns its
  initialization result after exit is requested.
