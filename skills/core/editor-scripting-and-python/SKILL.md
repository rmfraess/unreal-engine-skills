---
name: editor-scripting-and-python
description: >-
  Use when automating UE Editor via Python or Blutility. Covers editor subsystems, APIs, Editor Utility Widgets, asset operations, and editor-only boundaries.
license: UNLICENSED
metadata:
  engine-version: "5.8"
  category: tooling
  hermes:
    tags: [unreal-engine, ue5, editor, scripting, python]
    related_skills: [navigating-engine-source]
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
Enum values become `UPPER_SNAKE_CASE`. The `U`/`A`/`F`/`T` prefix is dropped.

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
- **Long Python jobs block the editor UI** — wrap with `unreal.ScopedSlowTask` and yield
  `enter_progress_frame` to keep the editor responsive and allow cancellation.
- **Treating `time.sleep()` as an Unreal frame wait** — Python normally blocks the editor/game thread, so sleeping does not advance component registration, shader/render-resource readiness, foliage rebuilds, visibility, SceneCapture work, or render-target completion. Use a verified post-tick callback, latent automation command, or other tick-driven state machine. For visual evidence after asset load/import/reimport, load `unreal-editor-python` and follow **Tick-Driven Render Verification**; missing target pixels are inconclusive, not asset failure.
- **Unexposed editor settings classes** — if a native config class lacks an `unreal.ClassName` binding, load its verified `/Script/Module.ClassName` with `load_class` and obtain its default object. Use the native property names when snake-case aliases do not exist. In UE 5.8.2, `LevelEditorPlaySettings` was accessible this way with `NewWindowWidth`, `NewWindowHeight`, and `CenterNewWindow`; no new plugin or reflection wrapper was needed.
- **Live reflected containers** — a map returned by `get_editor_property` can be a live
  view: item assignment may change native state even when a later property setter rejects
  a read-only property. Copy the container before preparing edits, avoid mutating shared
  struct values, use proper edit notifications, and inspect state after a failed setter.
- **Rotation construction** — use named `pitch=`, `yaw=`, and `roll=` arguments for new `unreal.Rotator` values. Verified UE 5.8.2 positional construction `Rotator(-22, 52, 0)` yielded roll=-22, pitch=52, yaw=0; read camera rotation back before capture.
- **Imported mesh validation** — a non-null material instance is not proof of complete rendering dependencies. Follow its parent chain to a material and query Asset Registry package dependencies; missing plugin master materials and missing vendor textures require different remedies. Verify a rendered representative before scaling up placement.
- **Exact transform restoration** — in verified UE 5.8.2 bindings, the `Rotator(...)`
  constructor rounded native double angles. For exact restore, create an empty Rotator
  and assign its pitch/yaw/roll properties with the retained native values; then compare
  native state again. Do not weaken exact-restore checks to hide constructor loss.
- **Struct inspection** — reflected function discovery may omit native struct helpers.
  Verify installed bindings before assuming absence: `HitResult.to_dict()` exposes typed
  hit actors/components, while `StructBase.export_text()` can retain native connection
  references. Prefer typed dictionaries where available; validate any text parsing against
  exact field boundaries and known object identities.
- **VibeUE Python pre-execution saves** — inspect the installed execution wrapper before using `execute_python_code` under a selective-save or dirty-state-preservation constraint. Verified VibeUE 5.0 `UPythonTools::ExecutePythonCode` gathers dirty content and world packages and calls `UEditorLoadingAndSavingUtils::SavePackages` before executing the script. An in-script dirty check is too late. Prefer dedicated read operations until the dirty/save boundary is independently established; never use this wrapper merely to inspect unknown dirty state.
- **Post-tick work can outlive an adapter timeout** — a callback registered by `execute_python_code` can begin a long native compile before the HTTP response flushes, so the client may time out while the callback continues and saves successfully. Do not retry the mutation. Read its progress artifact, WorkflowService run journal, Editor heartbeat, and persisted asset state first. On Windows, make advisory progress checkpoints tolerant of `Path.replace()` sharing violations caused by concurrent readers; the authoritative run journal must still close.
- **Forgetting to save** — call `EAS->SaveAsset()` or the Python equivalent; unsaved
  changes to assets are lost when the editor closes.
- **Hardcoding asset paths** — use the Asset Registry to discover paths dynamically; see
  `asset-management`.
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

Related skills: `subsystems`, `plugins-and-modules`, `asset-management`.
