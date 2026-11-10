---
name: ue-automation-and-testing
description: Write and run automated tests for Unreal Engine projects — simple/complex
  automation tests (IMPLEMENT_SIMPLE_AUTOMATION_TEST, IMPLEMENT_COMPLEX_AUTOMATION_TEST),
  BDD-style Spec tests (DEFINE_SPEC, BEGIN_DEFINE_SPEC, Describe/It/BeforeEach/AfterEach),
  functional in-level tests (AFunctionalTest), low-level tests (Catch2-based LLTs),
  latent/async commands, EAutomationTestFlags, FAutomationTestBase assertion API
  (TestTrue/TestEqual/TestNotNull/AddError), and running tests from the editor, CLI,
  or CI. Use when writing unit or integration tests for gameplay logic or systems,
  setting up headless CI test runs, verifying data/content, or catching regressions.
metadata:
  engine-version: "5.8"
  category: tooling
---

# Automation & testing

Unreal has a layered test ecosystem. Each layer trades world setup cost against richness:

| Layer | Runs | Best for |
|---|---|---|
| **Low-level tests (LLT)** | thin process, no editor/game | pure C++ module logic, fastest CI |
| **Simple automation test** | editor or commandlet | unit/feature tests, no world required |
| **Complex automation test** | editor or commandlet | same code over many inputs (content stress) |
| **Spec** (`DEFINE_SPEC`) | editor or commandlet | BDD-style behavior docs, latent/async scenarios |
| **Functional test** (`AFunctionalTest`) | full world in a test level | gameplay integration, AI, abilities |
| **Gauntlet** | full device sessions | large-scale, perf, device/platform testing |

## When to use this skill

- Writing C++ unit or integration tests for game systems (damage, inventory, save data).
- Expressing multi-case behavior specs that should read like documentation.
- Testing gameplay mechanics that require actors, physics, or a running world.
- Running tests headless in CI on every commit.
- Reaching devices or larger sessions via Gauntlet.

## Mental model

Tests live outside `UObject` reflection — they are not Blueprints-visible. The
`FAutomationTestBase` base class provides the assertion API (`TestTrue`, `TestEqual`, …)
and is instantiated once as a global at startup. `RunTest` must return `true`; use the
assertion methods rather than `check`/`ensure` so failures record cleanly instead of
crashing.

`EAutomationTestFlags` controls two orthogonal dimensions: **context** (where the test
can run: `EditorContext`, `ClientContext`, `ServerContext`, `CommandletContext`,
`ProgramContext`) and **filter** (which CI bucket: `SmokeFilter`, `EngineFilter`,
`ProductFilter`, `PerfFilter`, `StressFilter`). Every test must specify at least one
context and one filter.

## Simple automation test

```cpp
// Private/Tests/DamageTest.cpp
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDamageMathTest, "MyGame.Combat.DamageMath",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FDamageMathTest::RunTest(const FString& Parameters)
{
    const float Result = ComputeDamage(100.f, 0.5f);
    TestEqual(TEXT("Half damage"), Result, 50.f);
    TestTrue(TEXT("Non-negative"), Result >= 0.f);
    return true;   // returning false also marks the test failed
}
```

Key rules:
- Place tests in `Private/Tests/` of the relevant module; name the file
  `<ClassFilename>Test.cpp`.
- The dotted path string (`"MyGame.Combat.DamageMath"`) is what the browser and
  command-line filter use.
- Always combine a context flag and a filter flag with `|`.
- Add `"AutomationController"` and `"AutomationUtils"` to `PrivateDependencyModuleNames`
  in your `Build.cs` if you need automation utilities.

## Complex automation test

Complex tests run the **same `RunTest` body over a set of inputs** provided by
`GetTests`. Use them for content stress (load all maps, compile all Blueprints):

```cpp
IMPLEMENT_COMPLEX_AUTOMATION_TEST(FLoadAllMapsTest, "MyGame.Maps.LoadAll",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

void FLoadAllMapsTest::GetTests(TArray<FString>& OutBeautifiedNames,
                                TArray<FString>& OutTestCommands) const
{
    // populate OutBeautifiedNames and OutTestCommands in parallel
}

bool FLoadAllMapsTest::RunTest(const FString& Parameters)
{
    // Parameters is one entry from OutTestCommands
    return true;
}
```

## Spec style (BDD)

Specs express behavior in `Describe`/`It` blocks with scoped `BeforeEach`/`AfterEach`
setup. Each `It` becomes an independently runnable test. Use `BEGIN_DEFINE_SPEC` to
add member variables; `DEFINE_SPEC` when the class body can stay empty.

```cpp
BEGIN_DEFINE_SPEC(FInventorySpec, "MyGame.Inventory",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)
    TSharedPtr<FInventorySystem> Inv;
END_DEFINE_SPEC(FInventorySpec)

void FInventorySpec::Define()
{
    BeforeEach([this]()
    {
        Inv = MakeShared<FInventorySystem>();
    });

    Describe("AddItem", [this]()
    {
        It("should increase count by one", [this]()
        {
            Inv->AddItem(TEXT("Sword"), 1);
            TestEqual(TEXT("Count"), Inv->GetCount(TEXT("Sword")), 1);
        });

        It("should reject a stack over the limit", [this]()
        {
            TestFalse(TEXT("Over limit"),
                Inv->AddItem(TEXT("Arrows"), 9999));
        });
    });

    AfterEach([this]() { Inv.Reset(); });
}
```

- Name spec files `<FeatureName>.spec.cpp` — not `*Test.cpp`.
- `xDescribe` / `xIt` disable a block without deleting it.
- Use `LatentIt` / `LatentBeforeEach` when a test step spans multiple frames (passes a
  `FDoneDelegate`).
- Pass `EAsyncExecution::TaskGraph` / `::ThreadPool` to `It` / `BeforeEach` to control
  which thread each block runs on.

See [references/spec-and-latent-commands.md](references/spec-and-latent-commands.md)
for BeforeEach scoping, parameterized tests, async/latent patterns, and `Redefine`.

## Functional tests (in a level)

`AFunctionalTest` is a `UCLASS` actor placed in a dedicated test map. The automation
runner discovers it through the **Functional Testing Editor** plugin, starts each
actor, and collects results.

Override the key virtual functions in a C++ child class:

```cpp
// MyFunctionalTest.h
UCLASS()
class MYGAME_API AMyFunctionalTest : public AFunctionalTest
{
    GENERATED_BODY()
protected:
    virtual void PrepareTest() override;      // start async setup (streaming, server)
    virtual bool IsReady_Implementation();    // return false while still loading
    virtual void StartTest();                 // main test body
};
```

```cpp
// MyFunctionalTest.cpp — inside StartTest:
void AMyFunctionalTest::StartTest()
{
    AMyActor* Target = Cast<AMyActor>(FindActorByTag(TEXT("Target")));
    AssertIsValid(Target, TEXT("Target actor found"));
    AssertTrue(Target->Health > 0.f, TEXT("Target is alive"));
    FinishTest(EFunctionalTestResult::Succeeded, TEXT("OK"));
}
```

Important:
- `FinishTest` **must** be called or the test times out. Set `TimeLimit` in the actor's
  details to bound CI runs.
- Use `AssertTrue` / `AssertIsValid` / `AssertEqual_Float` (the functional-test assert
  family from `AFunctionalTest`) rather than the `FAutomationTestBase` macros.
- Register spawned actors with `AddActorToDestroyOnTestEnd` so cleanup is automatic.

See [references/functional-tests.md](references/functional-tests.md) for `PrepareTest`
and `IsReady` patterns, Ground Truth Data, and Blueprint functional test setup.

## Low-level tests (Catch2 / LLT)

LLTs compile a separate thin executable per module using **Catch2** — no editor, no
game framework — giving the fastest possible CI iteration for module-internal logic.
They live in a `Tests/` directory alongside the module and require a dedicated
`<Module>Tests.Target.cs` build target. See the official doc and
`Developer/LowLevelTestsRunner/` for the runner harness.

```cpp
#include "TestHarness.h"   // Developer/LowLevelTestsRunner/Public/TestHarness.h

TEST_CASE("MyModule / FormatFString / basic substitution", "[smoke]")
{
    FString Out = FString::Printf(TEXT("v=%d"), 42);
    CHECK(Out == TEXT("v=42"));
}
```

LLTs are the right choice when your logic has no UObject or world dependency and you
want sub-second CI feedback. See
[references/low-level-tests.md](references/low-level-tests.md) for target setup and
build invocation.

## Assertion reference

`FAutomationTestBase` assertions (all record failures without stopping execution unless
you return `false` or call `UE_RETURN_ON_ERROR`):

| Assertion | Notes |
|---|---|
| `TestTrue(What, Expr)` | fails if `Expr` is false |
| `TestFalse(What, Expr)` | fails if `Expr` is true |
| `TestEqual(What, Actual, Expected)` | float/double overloads accept a `Tolerance` |
| `TestNotNull(What, Ptr)` | fails if pointer is null |
| `TestNull(What, Ptr)` | fails if pointer is non-null |
| `TestValid(What, Value)` | TWeakObjectPtr / TOptional validity |
| `AddError(Message)` | unconditional failure record |
| `AddWarning(Message)` | non-failing annotation |
| `UE_RETURN_ON_ERROR(Cond, Msg)` | record error and `return false` if condition fails |

## Testing reflected tool results

For an Editor tool exposed through ToolsetRegistry, keep two distinct checks: direct C++ tests establish behavior and a registry test exercises reflection and JSON serialization. With the registry registered, call `UToolsetRegistry::ExecuteTool(toolset, tool, input_json)`, check the result pointer, completion and error, then parse the async string result's `Value` as JSON and assert the actual `returnValue` fields. Use a latent test if the call is not already complete; never block the game thread waiting for it. Run a separate real MCP call to verify the external transport: registry execution alone does not cover that boundary. For risk-acceptance APIs, assert the published default is off, the default result explains the affected object and risk without mutation, and explicit opt-in returns the remaining warning with independently verified state effects. Include invalid input and hard failures that override cannot resolve, so approval is not requested for an unrelated blocker; parity with the previous implementation only proves parity, not correctness.

For a path-based editor asset reader that needs an override not present in a suitable fixture, create an authorized, uniquely named unsaved public asset in a new mounted `/Game` package, hold the package and asset with `TStrongObjectPtr`, and verify `UEditorAssetLibrary::LoadAsset` resolves its object path before testing. Do not use `RF_Transient`, `RF_Standalone`, registry publication, or save: `IsAsset()` rejects transient objects, and the loaded-object lookup resolves the public asset without writing a package. Assert the parent and override differ, then verify no dirty packages remain; release strong references and let GC reclaim the test-only objects. Material base-property overrides can compile shaders and populate the shared DDC even when no asset is saved.

## Running tests

**Editor:** Tools → Test Automation → Automation tab → select tests → Start Tests.

**Command line / CI (headless):**
```
UnrealEditor-Cmd.exe MyProject.uproject
  -ExecCmds="Automation RunTest MyGame.Combat;Quit"
  -unattended -nopause -nullrhi
  -ReportExportPath="TestResults/"
```
Flags:
- `-ExecCmds="Automation RunTest <filter>"` — dotted prefix runs all tests under it.
- `-ExecCmds="Automation RunTest Group:MyGroup;Quit"` — named test group (configured
  via `AutomationTestGroup` in `DefaultEngine.ini`).
- `-ReportExportPath` — writes JSON + HTML for a report server.
- `-ResumeRunTest` — resume an interrupted run from a saved JSON report.

Parse the exit code and log for pass/fail in your CI pipeline. A non-zero exit code
indicates test failures when `-unattended` is set. Check the discovered test names and completed count for any documented filter: a narrow name can omit sibling regression tests while still producing a passing run.

For a disposable project testing a changed plugin, copy the plugin source into that project's `Plugins/` directory, build and launch that copy, and compare its changed source files with the reviewed files. Check the Editor log's `InternalLoadLibrary` path and verify it loaded the newly built module before crediting results: an external plugin directory can build a project-local DLL while the Editor loads the original plugin's stale DLL. When copying changed C++ into an existing disposable build, do not preserve an older source mtime: `copy2` can make UBT say "up to date" while the DLL still contains a test mutation. Refresh the copied source mtime and verify the build actually recompiles it. Compare a separately executed script against the reviewed script at its actual execution path; its absence from the built plugin copy does not prove it was not exercised. Preserve the test log before any relaunch script clears it. Run tests that use the global Undo/Redo stack only in a disposable Editor session; they can otherwise undo unrelated work or retain transactions referencing destroyed fixtures.

For an Editor guard regression, establish its world and fixture preconditions explicitly, assert the intended rejection and warning, then pair it with an allowed-path control using the same fixture. Snapshot transaction queue and package dirty state after fixture setup; verify rejection preserves them as well as the relevant data and references before restoring the fixture and exercising success. A false return alone can come from an unrelated map, streaming, or identity guard. For identity replacement, require both the destination's presence and the source's absence; test intentional same-asset no-ops separately. Record the actual test world and distinguish a synthetic actor-lifecycle test from a saved World Partition streaming integration test.

For a Landscape brush guard, create an imported Landscape with real paint allocations and attach a concrete transient `ALandscapeBlueprintBrushBase` test subclass holding a reflected LayerInfo reference through `AddBrushToLayer`; assert membership, owner and ordinary edit-layer class so the test reaches the brush path. If the external MCP fixture needs a scratch-only reflected helper to attach the brush, disclose the helper and hash-compare the production files with the reviewed candidate; fixture instrumentation is not an exact full-build match. For a risk-acceptance path, test the default rejection and returned explanation, explicit opt-in with the warning retained, actual changed target and still-unrepaired external reference, and Undo/Redo; independently assert that opt-in cannot bypass missing components or conflicting references. Put blend metadata on the custom layer itself and exercise both full replacement and stale-cache repair through Undo/Redo, because base-layer metadata cannot establish custom-layer transaction coverage. Detach with `RemoveBrush` before destroying the actor, then run the brush-free positive control. A native subclass exercises the actor/reference path but does not establish Blueprint-generated-class behavior or saved rendering. Keep reflected test fixtures out of placement and Blueprint type pickers where supported; an actor fixture must remain concrete to spawn.

In a disposable, clean Editor fixture, protect a potentially successful guard probe with its own scoped transaction and a recorded transactional sentinel: inside `unreal.ScopedEditorTransaction`, require a transactional fixture object's `modify(False)` to succeed before invoking the operation. Close the scope before Undo and restore in `finally`, including on unexpected success. `modify(False)` records into an already open transaction; it does not create one. A bare Undo after a rejected or no-op operation can otherwise undo an unrelated transaction. Check the Undo result where exposed, compare the relevant state afterward, and report cleanup as unverified if a failed Undo cannot be detected; unchanged state alone cannot prove that a no-op transaction was removed.

## Gotchas

- For VibeUE suite runs in a disposable host, seed a harmless `Config/DefaultGame.ini` before launch and unset `PYTHONUNBUFFERED` in the Editor process environment. Otherwise settings persistence tests can lack a loaded config layer, and Python output-capture tests can fail when write-through splits `print` arguments. Use a fresh disposable host for a full-suite run: an earlier auto-save can leave a `Saved/Untitled_*.umap` package that collides with a newly created temporary world and triggers unrelated save and cleanup failures. Preserve prior evidence and do not delete the saved map without authorization. Distinguish setup failures from plugin regressions.
- **Missing both a context and a filter flag** → the test never appears in the browser.
- **Using `check`/`ensure` instead of `TestTrue`/`AddError`** → crashes the whole run
  instead of recording a failure.
- **Functional test with no timeout** → CI hangs indefinitely.
- **Non-deterministic tests** (frame timing, RNG, network) → flaky; seed or mock inputs.
- **Spec variable capture inside `Describe`** — local variables captured by lambda go
  out of scope before the `It` runs; capture `this` and use member variables.
- **Test module depends on the editor** — tests that need `WITH_EDITOR` types must be
  placed in an `Editor`-category module; don't put them in `Runtime`.
- **`AddErrorS` / `AddWarningS`** — deprecated since 5.4; use `AddError` / `AddWarning`.
- **`TestEqualInsensitive`** — deprecated since 5.5; use `TestEqual` (strings are
  case-insensitive by default now).

## Version notes

- `EAutomationTestFlags_ApplicationContextMask` is a convenience constant combining all
  context flags; commonly used in specs: `EAutomationTestFlags::ProductFilter |
  EAutomationTestFlags_ApplicationContextMask`.
- Priority flags (`CriticalPriority`, `HighPriority`, etc.) were added in UE5; they are
  optional but useful for CI triage.
- Low-level tests (Catch2-based LLTs) are the recommended direction for new pure-logic
  tests added since UE 5.0. The `FAutomationTestBase` stack remains the right choice
  for tests that need the engine or editor context.

## References & source material

Engine source (UE 5.8):
- `Runtime/Core/Public/Misc/AutomationTest.h` — `EAutomationTestFlags`:88,
  `FAutomationTestBase`:1594, `RunTest`:2653, `TestEqual`:1985, `TestFalse`:2367,
  `TestNull`:2530, `TestTrue`:2603, `FAutomationSpecBase`:2899, `Describe`:2757,
  `BeforeEach`:2821, `It`:2789, `IAutomationLatentCommand`:525,
  `DEFINE_LATENT_AUTOMATION_COMMAND`:3796, `ADD_LATENT_AUTOMATION_COMMAND`:4087,
  `IMPLEMENT_SIMPLE_AUTOMATION_TEST`:4297, `DEFINE_SPEC`:4339, `BEGIN_DEFINE_SPEC`:4346.
- `Developer/FunctionalTesting/Classes/FunctionalTest.h` — `AFunctionalTest`:249,
  `FinishTest`:678, `PrepareTest`:777, `IsReady_Implementation`:814, `AddError`:659.
- `Developer/LowLevelTestsRunner/Public/TestHarness.h` — Catch2 bridge/harness header.
- `Developer/CQTest/` — `CQTest` module (`TEST`, `TEST_CLASS`, `ASSERT_THAT` macros).

Official docs (UE 5.8):
- Automation Test Framework —
  <https://dev.epicgames.com/documentation/unreal-engine/automation-test-framework-in-unreal-engine>
- Write C++ Tests —
  <https://dev.epicgames.com/documentation/unreal-engine/write-cplusplus-tests-in-unreal-engine>
- Automation Spec —
  <https://dev.epicgames.com/documentation/unreal-engine/automation-spec-in-unreal-engine>
- Functional Testing —
  <https://dev.epicgames.com/documentation/unreal-engine/functional-testing-in-unreal-engine>
- Run Automation Tests —
  <https://dev.epicgames.com/documentation/unreal-engine/run-automation-tests-in-unreal-engine>
- Low-Level Tests —
  <https://dev.epicgames.com/documentation/unreal-engine/low-level-tests-in-unreal-engine>
- Gauntlet Automation Framework —
  <https://dev.epicgames.com/documentation/unreal-engine/gauntlet-automation-framework-in-unreal-engine>
- CQTest —
  <https://dev.epicgames.com/documentation/unreal-engine/cqtest-test-framework-for-unreal-engine>

Deep-dive references in this skill:
- [references/spec-and-latent-commands.md](references/spec-and-latent-commands.md) —
  Spec scoping, parameterized tests, latent/async patterns, `Redefine`.
- [references/functional-tests.md](references/functional-tests.md) — `AFunctionalTest`
  lifecycle, Ground Truth Data, Blueprint setup.
- [references/low-level-tests.md](references/low-level-tests.md) — Catch2/LLT target
  setup, build invocation, CQTest.
- [references/flags-and-ci.md](references/flags-and-ci.md) — `EAutomationTestFlags`
  reference table, CI command patterns, report server, Gauntlet overview.

Related skills: `ue-logging-and-assertions`, `ue-debugging-techniques`.
