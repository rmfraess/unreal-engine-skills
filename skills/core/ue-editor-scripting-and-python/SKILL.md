---
name: ue-editor-scripting-and-python
description: >-
  Automate Unreal Editor tasks with Python (the unreal module, startup scripts, commandlets),
  Editor Utility Widgets/Blueprints (UEditorUtilityWidget, UEditorUtilityObject,
  UEditorUtilityWidgetBlueprint, UAssetActionUtility), editor subsystems (UEditorActorSubsystem,
  UEditorAssetSubsystem, ULevelEditorSubsystem, UAssetEditorSubsystem, UEditorUtilitySubsystem),
  and UFUNCTION specifiers (BlueprintCallable, CallInEditor, ScriptMethod, ScriptName). Use when
  batch-processing assets, building dockable UMG tools, running CI commandlets, automating
  repetitive editor tasks, or exposing C++ APIs to editor Python/Blueprints. Editor-only, not
  packaged-game logic. Use ue-blueprint-cpp-integration for runtime Blueprint API exposure and
  ue-umg-and-slate for widget layout/input; load together as needed.
metadata:
  engine-version: "5.8"
  category: tooling
---

# Editor scripting & Python

Everything in this skill is **editor-only**: it lives in editor modules or behind
`WITH_EDITOR` and is stripped from packaged games. The two main paths are: the
**Python Script Plugin** (`unreal` module) for quick automation and pipeline scripts, and
**Blutility** (Editor Utility Widgets/Blueprints) for in-editor UI tools callable by
artists and designers.

## When to use this skill

- Batch operations on assets — rename, set properties, reimport, generate LODs.
- Custom in-editor UMG panels (Editor Utility Widgets) for artists.
- Context-menu scripted actions triggered from the Content Browser or Level.
- Headless commandlet runs in CI without the full editor UI.
- Exposing a C++ function so it appears in Python/Blueprints with the correct name.
- Obtaining a reference to an editor subsystem from C++ or Python.

## Approach comparison

| Approach | When to choose |
|---|---|
| **Python** (PythonScriptPlugin) | Pipeline automation, batch asset ops, CI jobs, quick scripts |
| **Editor Utility Widget** (Blutility) | Artist-facing tool panels with UMG UI in the editor |
| **Editor Utility Blueprint** | No-UI scripted actions on assets or actors |
| **C++ editor module + UEditorSubsystem** | Robust reusable tools, Slate/menu extensions |
| **Commandlet** | Headless batch processing, `-run=pythonscript` in CI |

---

## Python (`unreal` module)

Enable the **Python Editor Script Plugin** (Plugins > Scripting). The plugin bundles
Python 3.11.8; no separate install is needed. The `unreal` module is generated at startup
from whatever is reflected to Blueprints — any `BlueprintCallable` function or class
exposed by any enabled plugin is automatically available.

**Naming convention:** C++ class `UEditorAssetSubsystem` → Python class
`unreal.EditorAssetSubsystem`. Function `GetAllLevelActors()` → `get_all_level_actors()`.
Enum values become `UPPER_SNAKE_CASE`. The `U`/`A`/`F`/`T` prefix is dropped, and so is
`Kismet` in Blueprint function libraries: `UKismetMaterialLibrary` → `unreal.MaterialLibrary`,
`UKismetMathLibrary` → `unreal.MathLibrary`, `UKismetSystemLibrary` → `unreal.SystemLibrary`.

**Reading/setting properties:**
```python
import unreal

actor = unreal.EditorActorSubsystem().get_actor_reference("PersistentLevel.MyActor")
# BlueprintReadWrite → direct attribute access
val = actor.some_property
# EditAnywhere → use get/set_editor_property for pre/post-edit notifications
actor.set_editor_property("hidden_in_game", True)
```

**Transactions (undo/redo support):**
```python
with unreal.ScopedEditorTransaction("Batch rename"):
    for asset in assets:
        subsystem.rename_asset(asset.get_path_name(), new_path)
```

**Progress feedback for long jobs:**
```python
with unreal.ScopedSlowTask(len(assets), "Processing...") as task:
    task.make_dialog(True)
    for asset in assets:
        if task.should_cancel():
            break
        task.enter_progress_frame(1, f"Processing {asset.get_name()}")
        # ... do work
```

**Startup scripts** — add paths under Project Settings → Plugins → Python → Startup
Scripts (stored in `UPythonScriptPluginSettings::StartupScripts`,
`Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PythonScriptPluginSettings.h:67`).
Auto-detected `init_unreal.py` in any `Content/Python` folder also runs on startup.

**Commandlet (headless):** `UPythonScriptCommandlet` runs a script without the full UI:
```
UnrealEditor-Cmd.exe MyProject.uproject -run=pythonscript -script="my_script.py"
```
Source: `Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PythonScriptCommandlet.h:10`.

See [references/python-api.md](references/python-api.md) for the C++↔Python mapping,
`get_editor_subsystem`, type coercion, logging, and subsystem access patterns.

---

## Editor Utility Widgets & Blueprints (Blutility)

Blutility classes live in `Editor/Blutility/`. The module is `Blutility`; add it to your
editor module's `PrivateDependencyModuleNames`.

### Key classes

| Class | Base | Purpose |
|---|---|---|
| `UEditorUtilityWidget` | `UUserWidget` | Dockable UMG panel running in the editor |
| `UEditorUtilityWidgetBlueprint` | `UWidgetBlueprint` | Asset that generates `UEditorUtilityWidget` |
| `UEditorUtilityObject` | `UObject` | Editor-only utility with no UI; runs on demand |
| `UAssetActionUtility` | `UEditorUtilityObject` | Right-click scripted actions in the Content Browser |
| `UEditorUtilityTask` | `UObject` | Background task managed by `UEditorUtilitySubsystem` |

**`UEditorUtilityWidget`** (`Editor/Blutility/Classes/EditorUtilityWidget.h:27`):
inherits `UUserWidget`; runs entirely in editor. `Run()` is a `BlueprintImplementableEvent`
called when the widget is auto-run. Use `TabDisplayName` to set the panel name.

**`UEditorUtilityObject`** (`Editor/Blutility/Classes/EditorUtilityObject.h:20`):
pure-logic utility, no UI. Set `bRunEditorUtilityOnStartup = true` to auto-run after
asset discovery.

**`UAssetActionUtility`** (`Editor/Blutility/Classes/AssetActionUtility.h:60`):
any `UFUNCTION(BlueprintCallable)` on a subclass appears as a right-click option in the
Content Browser. Populate `SupportedClasses` (class defaults) to filter which asset types
show the action. `GetSupportedClass()` is deprecated since UE 5.2.

**`UEditorUtilitySubsystem`** manages widget tabs and utility tasks
(`Editor/Blutility/Public/EditorUtilitySubsystem.h:47`):
```cpp
// Open an Editor Utility Widget tab from C++:
UEditorUtilitySubsystem* EUS = GEditor->GetEditorSubsystem<UEditorUtilitySubsystem>();
EUS->SpawnAndRegisterTab(MyWidgetBlueprint);  // line 88
// From Python:
// eus = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
// eus.spawn_and_register_tab(widget_bp)
```

See [references/editor-utility-widgets.md](references/editor-utility-widgets.md) for
Widget setup, tab lifecycle, `UEditorUtilityTask`, and scripted-actions detail.

---

## Editor scripting subsystems

All subsystems inherit `UEditorSubsystem`. Access them via
`GEditor->GetEditorSubsystem<T>()` in C++ or `unreal.get_editor_subsystem(T)` in Python.

### `UEditorActorSubsystem` (`Editor/UnrealEd/Public/Subsystems/EditorActorSubsystem.h:49`)

Actor-level operations in the current level editor world:

```cpp
UEditorActorSubsystem* AS = GEditor->GetEditorSubsystem<UEditorActorSubsystem>();
TArray<AActor*> All   = AS->GetAllLevelActors();       // :166
TArray<AActor*> Sel   = AS->GetSelectedLevelActors();  // :181
AActor* Placed = AS->SpawnActorFromClass(MyClass, Location); // :228
AS->DestroyActor(ActorToRemove);                       // :236
```

Python: `unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()`

### `UEditorAssetSubsystem` (`Editor/UnrealEd/Public/Subsystems/EditorAssetSubsystem.h:38`)

Content-browser asset operations (the preferred replacement for `UEditorAssetLibrary`):

```cpp
UEditorAssetSubsystem* EAS = GEditor->GetEditorSubsystem<UEditorAssetSubsystem>();
UObject* Loaded = EAS->LoadAsset("/Game/MyFolder/MyAsset"); // :54
EAS->SaveAsset("/Game/MyFolder/MyAsset");                   // :296
EAS->DuplicateAsset("/Game/Src", "/Game/Dst");              // :185
EAS->RenameAsset("/Game/Src", "/Game/Dst");                 // :215
EAS->DeleteAsset("/Game/MyFolder/MyAsset");                 // :155
```

### `ULevelEditorSubsystem` (`Editor/LevelEditor/Public/LevelEditorSubsystem.h:38`)

Level-file and viewport operations:

```cpp
ULevelEditorSubsystem* LS = GEditor->GetEditorSubsystem<ULevelEditorSubsystem>();
LS->NewLevel("/Game/Maps/MyLevel");        // :147
LS->LoadLevel("/Game/Maps/Existing");      // :167
LS->SaveCurrentLevel();                    // :174
LS->EditorRequestBeginPlay();              // :78
```

### `UAssetEditorSubsystem` (`Editor/UnrealEd/Public/Subsystems/AssetEditorSubsystem.h:112`)

Open assets in their specialized asset editors programmatically.

### `UUnrealEditorSubsystem` (`Editor/UnrealEd/Public/Subsystems/UnrealEditorSubsystem.h:17`)

Viewport camera query/set (`GetLevelViewportCameraInfo`, `SetLevelViewportCameraInfo`)
and `GetEditorWorld()`.

See [references/editor-subsystems.md](references/editor-subsystems.md) for all subsystem
methods and Python equivalents.

---

## Exposing C++ to editor scripting

### `UFUNCTION(BlueprintCallable)` — surfaces to both Blueprints and Python

Any `BlueprintCallable` function on a `UCLASS` is reflected to Python automatically. In
Python the class name loses its prefix and the function name becomes `snake_case`.

### ToolsetRegistry and MCP return values

Resolve a documented integration shorthand against the installed toolsets or reflected service before diagnosing an Editor failure; a missing top-level alias does not establish a missing engine capability. Inspect the installed declaration, use its actual reflected method, and verify the returned identity. See [Python API discovery](references/python-api.md#resolve-integration-shorthand) for the environment-preflight recipe.

When exposing an editor service through ToolsetRegistry, inspect its schema and call the actual MCP tool with a known successful fixture and an invalid input. In UE 5.8, a reflected function's direct return is serialized as `returnValue`; a separate C++ output reference can be omitted even when native C++ or Python receives it. Preserve existing callers and, when needed, expose a direct result struct containing success, details and error. Verify both the transport and the underlying data independently: a correctly serialized legacy reader may still return incorrect values. For automated registry/JSON coverage, see `ue-automation-and-testing`; a registry test alone is not an external MCP transport test.

A synchronous service function that wraps a delegate-based engine API can block and pump `FHttpModule::Get().GetHttpManager().Tick(0.f)` until its callback fires, but that delivers only completions raised from HTTP callbacks. Work driven by the core ticker or the EOS SDK tick (an on-demand sign-in, for example) cannot progress while the game thread is blocked, so the call runs to its timeout and the work finishes just after it returns. Read how the engine API completes before choosing a blocking wrapper over an async tool result; if you block, hold the callback state in a shared pointer so a late callback is harmless, and make the timeout error name the precondition (which async tool to run first).

### `UFUNCTION(meta = (CallInEditor = "true"))` — Details panel button

Marks a function to appear as a button in the actor Details panel when an instance is
selected in the editor. Works on `AActor` and `UActorComponent` subclasses.
Source: `Runtime/CoreUObject/Public/UObject/ObjectMacros.h:1047`.

```cpp
UFUNCTION(BlueprintCallable, Category = "Validation", meta = (CallInEditor = "true"))
void ValidateSetup();
```

### `meta = (ScriptMethod)` — hoist a static function as an instance method in Python

A static `BlueprintFunctionLibrary` function that takes a struct or object as its first
parameter can be re-surfaced in Python as a method on that type:

```cpp
UFUNCTION(BlueprintCallable, meta = (ScriptMethod))
static FVector ScaleVector(const FVector& V, float Factor);
// Python: v.scale_vector(2.0)  instead of  unreal.MyLib.scale_vector(v, 2.0)
```

Source: `Runtime/CoreUObject/Public/UObject/ObjectMacros.h:1723`. Related specifiers:
`ScriptMethodSelfReturn` (:1726), `ScriptMethodMutable` (:1729).

### `meta = (ScriptName = "PythonName")` — override the Python/scripting name

```cpp
UFUNCTION(BlueprintCallable, meta = (ScriptName = "load_texture"))
static UTexture* LoadTexture_Internal(const FString& Path);
// Python: unreal.MyLib.load_texture(path)
```

Source: `Runtime/CoreUObject/Public/UObject/ObjectMacros.h:1285`.

---

## Version notes

- **`UEditorAssetLibrary` / `UEditorLevelLibrary`** (EditorScriptingUtilities plugin) were
  deprecated in UE 5.0. `UEditorLevelLibrary` functions carry
  `UE_DEPRECATED(5.0, "... Use the function in Editor Actor Utilities Subsystem")`.
  Prefer `UEditorAssetSubsystem` and `UEditorActorSubsystem` in all new code.
- `UAssetActionUtility::GetSupportedClass()` deprecated UE 5.2; use the `SupportedClasses`
  array in class defaults instead.
- Python 3.11.8 is the embedded version for UE 5.8 (VFX Reference Platform CY2024).
  Set `UE_PYTHON_DIR` to embed a different CPython build (requires source rebuild).

## Gotchas

- **Editor-only code in a runtime module** → packaging failure. Put editor code behind
  `WITH_EDITOR` or in a module with type `Editor`.
- **Python does not ship with the game** — it is a tooling/editor-only plugin.
- **Direct attribute set vs `set_editor_property`** — direct set bypasses pre/post-edit
  callbacks; `set_editor_property` triggers them (same as changing in Details panel). Use
  `set_editor_property` for `EditAnywhere` properties.
- **Struct arrays come back as copies** — `get_editor_property` on a `TArray<FStruct>` returns a copy. Calling `set_editor_property` on elements while iterating changes only those copies and fails silently. Build `lst = list(obj.get_editor_property(name))`, edit `lst[i]`, assign the whole list back, then re-read and `assert` the new values.
- **Multi-frame work from one call** — a blocking Python loop never advances frames, so camera moves, streaming and screenshots can't settle inside it. Register `unreal.register_slate_post_tick_callback(fn)` as a frame-stepping state machine (set camera → wait N frames → `unreal.AutomationLibrary.take_high_res_screenshot(w, h, path)` → next) and unregister it at the end. One call then captures a whole fixed view set. The same applies to sampling: `time.sleep` inside a call freezes the game thread, so repeated `frame_timing()` or perf readings in one call return the same stale frame, and `take_high_res_screenshot` is only queued (one shot per call per frame). Take each perf sample, and each one-off screenshot after a camera move, in a separate call, or let the post-tick state machine take them (one sample per tick interval, results written to a file the next call reads).
- **`EditorLoadingAndSavingUtils.reload_packages` on dirty packages opens a modal "reload these assets?" dialog** with the default interaction mode. Pass `unreal.ReloadPackagesInteractionMode.ASSUME_POSITIVE` to discard the in-memory changes without a dialog (e.g. after `git checkout` restored the file a stray save overwrote), then confirm the package left `get_dirty_content_packages()`. Without that mode the dialog blocks the game thread, and every remote/MCP call with it, until answered. Recovery: a rising `gameThreadStallSeconds` in the health heartbeat means the Editor is waiting on the dialog. List windows, capture only the Editor's `Message` window, and answer it. A background click may not register on a modal dialog, so re-capture and escalate to a foreground click. Then re-read dirty packages and `git status` to confirm the outcome.
- **Material Custom nodes: never rewrite a wired node's `inputs` from Python.** `CustomInput.Input`, the wire, is protected, so Python can't read it. Assigning a new `inputs` list therefore drops every existing link, and `connect_material_expressions` may then reject the rebuilt pins. Read names with `i.get_editor_property("input_name")`; there is no `input_name` attribute. To change what a wired Custom node computes, **wrap it**: create a new Custom node whose `Prev` input takes the old node's output (plus the same source nodes the old one reads, found via `list_connections`), compute the replacement there, and reconnect the old node's single consumer to the new node. Setting `inputs` is safe only on nodes you just created, because you rewire every pin afterwards. `list_connections` names a single-output node's pin (for example WorldPosition `XYZ`), but `connect_material_expressions` may want `""` for it; retry with `""` before treating it as a failure. Before and after any graph edit, compare `MaterialNodeService.list_connections(material)` (fields `source_expression_id`, `source_output`, `target_expression_id`, `target_input`) against the expected links, and only then compile or save.
- **`MaterialNodeService.list_expressions` includes nodes inside called material functions.** Selecting "the first `WorldPosition`" by class can return a shared function's node, and wiring it edits that function. Filter to expressions whose outer is the material itself before choosing or connecting nodes.
- **`MaterialNodeService` returns empty lists while PIE runs** (`list_expressions`, `list_connections`), although the material is intact (`MaterialEditingLibrary.get_num_material_expressions` still counts the nodes). Stop PIE before any graph lookup or edit. For a material A/B perf test, toggle the variant with PIE stopped, then start PIE and sample, once per variant.
- **Reading an engine material's graph:** `MaterialNodeService.export_material_graph` (and `list_expressions`) need the full object path, `/Engine/.../M.M`; a package path returns nothing. The export omits NamedReroute declaration-to-usage links, so ancestry traced through the JSON misses whatever flows through reroutes. Confirm the real wiring with `MaterialEditingLibrary.get_inputs_for_material_expression` + `get_material_expression_input_names` (and `get_input_node_output_name_for_material_expression` for the output pin) before choosing an injection point.
- **Any Editor kill with dirty packages leaves an autosave "Restore Packages" prompt on the next start** — a deliberate force-kill, and also a build script that closes the Editor to rebuild C++. Even a diagnostic toggle set back to its old value, or regenerated PCG/map output, counts as dirty. The prompt blocks the game thread and MCP before the map loads (signal file stuck on `/Temp/Untitled_0`, `mcpListening: false`, `gameThreadStallSeconds` climbing with no new log lines). **Prevent it:** before a rebuild or relaunch, revert or reload diagnostic edits until `get_dirty_content_packages()` and `get_dirty_map_packages()` are empty, saving only task-owned changes you mean to keep. When every dirty package is a discardable diagnostic or regeneration (the files on disk are the accepted state), stop the Editor yourself (`taskkill /F /PID <pid>` with single slashes from bash, or `Stop-Process -Id <pid> -Force`; `//F` is rejected), then rewrite `Saved/Autosaves/PackageRestoreData.json` — UTF-16LE JSON — with `"Packages": []` and `"RestoreEnabled": false`, then run the build/launch script: the Editor opens straight into the map. **If it appears:** `list_windows` finds it by title; answer **Skip Restore** (the saved files are the accepted state) with a foreground click, or ask the user to click it — background clicks/keys do not land on this Slate modal. Then verify the reloaded assets match the committed version before building on them.
- **Dumping a UObject's scalar settings** (e.g. a PCG node's settings, which have no `export_text`): loop `dir(obj)` and wrap the **whole** read in `try: v = obj.get_editor_property(p)`; a bare `getattr`/`callable(getattr(...))` probe raises on protected properties (`bUseSeed`) before your `try` runs. Keep `isinstance(v, (int, float, bool))` values.
- **Change a reusable helper script by editing its file, not by `str.replace` on its source before `exec`.** Files in a Windows checkout read back with `\r\n`, so multi-line replacement targets silently miss and the patched helper runs unchanged. Add a parameter to the helper instead (e.g. which mesh names to toggle) and assert the patched behaviour once.
- **Bulk renames/moves: follow [references/bulk-rename-and-move.md](references/bulk-rename-and-move.md)** (baseline → user moves maps/folders → scripted asset renames → redirector resave+delete → labels → Nanite rebuild → text → builds, cold-load compare, tests). Non-map assets rename fine by script; only maps need the user.
- **Renaming or moving a map or a content folder: let the user do the move in the Content Browser, then finish by script.** `rename_asset` on a `World` returns False when any class default object soft-references the map, which per-user Editor settings such as recent maps and saved views do. AssetRenameManager then asks "Continue with rename?", and both MCP calls and Slate post-tick callbacks auto-answer Cancel. The failed call has still loaded the map as a resident asset, so restart the Editor before the next level change. Ask the user to right-click → Rename, then drag into the target folder → Move Here, clicking OK when asked. Then:
  0. Before handing over a folder move: confirm that every package being deleted has no referencer outside the deleted set (`get_referencers` on each package, filtered to outside paths). Save a baseline to a scratch JSON: per-map actor count, class counts, labels, ISM instance totals per mesh, and the folder's package list. Delete dead packages with `git rm` while the Editor is closed (`SystemLibrary.quit_editor()` after checking that nothing is dirty), because deleting them in the Editor raises reference dialogs. In every map being moved, set `enable_nanite` False on each `LandscapeProxy` that has it on and save: the generated `LandscapeNaniteMesh` is a private object inside the map package and keeps its old path, so the moved map fails to save with "Illegal reference to private object … belongs to an external map". Record which landscapes you turned off. After the move, turn them back on and `save_current_level()`; the save's `PreSave` rebuilds the mesh, while setting the property alone does not. Relaunch, then `EditorLoadingAndSavingUtils.new_blank_map(False)` so no open map lives inside the folder being moved. Give the user numbered steps: Ctrl-select the subfolders, drag onto the target, **Move Here**, OK on prompts, no **Save All**, and report any save prompt.
  - **If the move half-fails** (a save error on one map): don't fix it in place. Assets that had no referencers are already deleted from the old folder, so the old-path map loads with missing meshes. Kill the Editor without saving, check that `PackageRestoreData.json` lists no packages, `git checkout HEAD -- <old folder>`, delete the copies under the new folder, then `git status` for referencers outside both folders that the move resaved (e.g. a shared mesh pointing at a moved material) and revert them. Fix the cause, compare against the baseline, and hand the move back.
  1. List `get_assets_by_path` in the old folder; a rename plus a move leaves one `ObjectRedirector` per step.
  2. Delete each redirector with `EditorAssetLibrary.delete_asset` once `get_referencers` shows only the other redirectors. Clear the remaining referencers by resaving them and rescanning (see the reference); 5.8 Python has no `fixup_referencers`.
  3. Update script paths, the default maps in `DefaultEngine.ini` and any LFS rule naming the old path, then check `git check-attr filter` on the new file.
  4. Verify after a cold restart: `load_level` the new map, compare its actor count with the earlier evidence, check that the log has a clean `MapCheck` and no missing-package lines, and load the bench map back. Read `GameMapsSettings` paths with `.export_text()`, because a `SoftObjectPath` prints as `{}`.
- **Drop Python references to a world before changing levels.** A variable still holding the map's package, an actor or a component (e.g. `p = load_package(map)` before `save_packages([p])`) keeps the old world from being garbage-collected, and `new_blank_map`/`load_level` in the same call then hits the fatal "World Memory Leaks" assert and kills the Editor. Save in one call and switch levels in the next, or `del` every such variable first. Save the open map with `LevelEditorSubsystem.save_current_level()`, which holds no package handle; after a crash, check the file's timestamp and reload it before assuming the save was lost.
- **Copy a map with Save As plus a relaunch, never duplicate-then-load.** `duplicate_asset` on a `World` and `EditorLoadingAndSavingUtils.save_map(world, NewPath)` both leave the new map resident (RF_Standalone; `collect_garbage` does not free it), so any later `load_level` of it hits the same "World Memory Leaks" fatal. Use `save_map(world, NewPath)` from the open source map (the source file is untouched), check nothing is dirty, `SystemLibrary.quit_editor()`, and relaunch with `-Map NewPath`. `unreal.PythonTools.get_resident_maps()` lists a resident copy: never load a level while it is non-empty.
- **Generators can write shared assets as a side effect.** A PCG Generate (or any builder) may rewrite textures or meshes that other maps also use. `execute_python` saves nothing by itself, so after an exploratory Generate list `get_dirty_content_packages()`, save only the map you own, and drop the rest with `reload_packages(..., ASSUME_POSITIVE)` (after `git checkout` if a stray save already reached disk).
- **Long Python jobs block the editor UI** — wrap with `unreal.ScopedSlowTask` and yield
  `enter_progress_frame` to keep the editor responsive and allow cancellation.
- **Forgetting to save** — call `EAS->SaveAsset()` or the Python equivalent; unsaved
  changes to assets are lost when the editor closes.
- **Background viewport captures need real rendering, not just healthy Slate ticks.** The Editor's `Background Process` override can disable viewport rendering while post-tick callbacks continue, leaving an Automation screenshot task waiting. For a bounded capture, preserve the performance CDO's `bThrottleCPUWhenNotForeground`, disable it only in memory with `PropertyAccessChangeNotifyMode.NEVER`, and restore it in every cleanup path without saving preferences. If the settings class has no generated Python wrapper, resolve `/Script/UnrealEd.EditorPerformanceSettings` and use the installed C++ property name rather than assuming a snake-case alias. Preserve the base realtime flag separately from override-inclusive `is_realtime`, and restore the full viewport state; stop without overwriting later user navigation when interference is detected.
- **Track dirty state yourself for read-only or no-write work.** `execute_python` neither saves nor reports what a script dirtied: compare `unreal.PythonTools.get_dirty_packages()` before and after. Revert any authorized diagnostic edits and verify dirty state. Before an authorized save, assert that dirty packages are task-owned. After an MCP timeout, inspect the actual outcome (log, dirty packages) before retrying.
- **Idempotent builders must not re-save unchanged assets.** Every `save_asset` rewrites the `.uasset` bytes, so a builder that re-applies identical settings and saves on each run puts a binary diff in every commit. Compare the current value (code string, texture setting, parameter) first and only set, recompile and save when it differs.
- **Confirm referencers with loaded assets before deleting.** After you remove a reference (for example by clearing a material instance's parameters) and save, `AssetRegistry.get_referencers` can still list the old referencer. Call `unreal.EditorAssetLibrary.find_package_referencers_for_asset(path, True)`, which loads to confirm, and delete only when it returns empty.
- **Hardcoding asset paths** — use the Asset Registry to discover paths dynamically; see
  `ue-asset-management`.
- **`SpawnActorFromClass` vs `SpawnActor`** — `SpawnActorFromClass` on
  `UEditorActorSubsystem` places into the editor world and notifies the editor; use it
  instead of `UWorld::SpawnActor` for editor-placed actors.

## References & source material

Engine source (UE 5.8):

**Blutility** (`Engine/Source/Editor/Blutility/`):
- `Classes/EditorUtilityWidget.h` — `UEditorUtilityWidget`:27, `Run()`:34, `TabDisplayName`:74
- `Classes/EditorUtilityObject.h` — `UEditorUtilityObject`:20, `bRunEditorUtilityOnStartup`:41
- `Classes/AssetActionUtility.h` — `UAssetActionUtility`:60, `SupportedClasses`, deprecated `GetSupportedClass()`:71
- `Classes/EditorUtilityTask.h` — `UEditorUtilityTask`:32, `FinishExecutingTask()`:56
- `Public/EditorUtilitySubsystem.h` — `UEditorUtilitySubsystem`:47, `SpawnAndRegisterTab`:88, `RegisterAndExecuteTask`:140, `TryRun`:76

**Editor subsystems** (`Engine/Source/Editor/UnrealEd/Public/Subsystems/`):
- `EditorActorSubsystem.h` — `UEditorActorSubsystem`:49, `GetAllLevelActors`:166, `SpawnActorFromClass`:228, `DestroyActor`:236
- `EditorAssetSubsystem.h` — `UEditorAssetSubsystem`:38, `LoadAsset`:54, `SaveAsset`:296, `DuplicateAsset`:185, `RenameAsset`:215, `DeleteAsset`:155
- `AssetEditorSubsystem.h` — `UAssetEditorSubsystem`:112
- `UnrealEditorSubsystem.h` — `UUnrealEditorSubsystem`:17, `GetLevelViewportCameraInfo`:32

**Level editor** (`Engine/Source/Editor/LevelEditor/Public/`):
- `LevelEditorSubsystem.h` — `ULevelEditorSubsystem`:38, `NewLevel`:147, `LoadLevel`:167, `SaveCurrentLevel`:174, `EditorRequestBeginPlay`:78

**Python plugin** (`Engine/Plugins/Experimental/PythonScriptPlugin/`):
- `Source/PythonScriptPlugin/Public/IPythonScriptPlugin.h` — `IPythonScriptPlugin`:11, `ExecPythonCommand`:54
- `Source/PythonScriptPlugin/Private/PythonScriptCommandlet.h` — `UPythonScriptCommandlet`:10
- `Source/PythonScriptPlugin/Private/PythonScriptPluginSettings.h` — `StartupScripts`:67, `AdditionalPaths`:71

**Reflection/meta specifiers** (`Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h`):
- `CallInEditor`:1005, `ScriptName`:1243, `ScriptMethod`:1671, `ScriptMethodSelfReturn`:1674, `ScriptMethodMutable`:1677

**Deprecated (EditorScriptingUtilities plugin, prefer subsystems)**:
- `Engine/Plugins/Editor/EditorScriptingUtilities/Source/EditorScriptingUtilities/Public/EditorAssetLibrary.h`
- `Engine/Plugins/Editor/EditorScriptingUtilities/Source/EditorScriptingUtilities/Public/EditorLevelLibrary.h` (deprecated UE 5.0)

Official docs (UE 5.8):
- Scripting and Automating the Unreal Editor — <https://dev.epicgames.com/documentation/unreal-engine/scripting-and-automating-the-unreal-editor>
- Scripting the Unreal Editor Using Python — <https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-python>
- Scripting the Unreal Editor Using Blueprints — <https://dev.epicgames.com/documentation/unreal-engine/scripting-the-unreal-editor-using-blueprints>
- Python API Reference — <https://dev.epicgames.com/documentation/unreal-engine/PythonAPI>

Deep-dive references in this skill:
- [references/editor-subsystems.md](references/editor-subsystems.md) — all subsystem classes,
  their methods, and Python equivalents.
- [references/editor-utility-widgets.md](references/editor-utility-widgets.md) — Blutility
  class hierarchy, tab lifecycle, `UEditorUtilityTask`, scripted actions.
- [references/python-api.md](references/python-api.md) — C++↔Python naming rules, type
  mapping, `get_editor_subsystem`, transactions, logging, commandlet invocation.
- [references/bulk-rename-and-move.md](references/bulk-rename-and-move.md) — mass asset/map/label
  renames with baseline, redirector cleanup, text updates and verification.

Related skills: `ue-subsystems`, `ue-plugins-and-modules`, `ue-asset-management`.
