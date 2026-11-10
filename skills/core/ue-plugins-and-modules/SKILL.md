---
name: ue-plugins-and-modules
description: >-
  Use when creating a plugin or choosing plugin vs project module; structuring runtime/editor or
  content-only plugins; wiring modules; enabling or troubleshooting plugin loading/content mounts;
  or packaging for distribution. Covers `.uplugin` fields (FileVersion, Modules, CanContainContent,
  EnabledByDefault, Plugins), Source/Content/Resources layout, EHostType (Runtime, Editor,
  Developer, UncookedOnly, ServerOnly, ClientOnly) and ELoadingPhase, IModuleInterface
  StartupModule/ShutdownModule, IPluginManager/IPlugin queries, engine/project and explicitly
  loaded plugins, and dependency hierarchy.
metadata:
  engine-version: "5.8"
  category: tooling
---

# Plugins & modules

A **plugin** is a self-contained, portable feature bundle: a `.uplugin` descriptor file plus
one or more C++ modules and optional content/resources. Use plugins when the feature is
reusable across projects, optional (so it can be disabled), or ships as an editor tool.
Compare with project modules (`ue-module-and-build-system`): project modules compile into your
game and can't travel without it; plugins drop into any project's `Plugins/` folder.

## When to use this skill

- Creating a reusable runtime system, editor tool, or third-party SDK wrapper.
- Deciding whether to put new code in a project module or a plugin.
- Structuring a plugin that contains both runtime and editor modules.
- Enabling, disabling, or adding a dependency on another plugin.
- A plugin or its modules fail to load at startup.
- Plugin content doesn't mount or assets aren't found under `/PluginName/`.

## Plugin vs project module

| | Project module | Plugin |
|---|---|---|
| Lives in | `Source/<Name>/` inside the project | `Plugins/<Name>/` in the project or engine |
| Portability | Not portable (game-specific) | Drop into any project and enable |
| Optional? | Always compiled | Can be disabled per-project |
| Can bundle content? | No (content lives in project `Content/`) | Yes (`CanContainContent: true`) |
| Multiple modules? | One `.Build.cs` per module | Many modules, each with its own `.Build.cs` |



## Plugin folder structure

```
Plugins/MyFeature/
├── MyFeature.uplugin           # required: plugin descriptor
├── Source/
│   ├── MyFeature/              # runtime module (Build.cs, Public/, Private/)
│   └── MyFeatureEditor/        # optional editor-only module
├── Content/                    # optional: assets mounted at /MyFeature/
├── Config/
│   └── DefaultMyFeature.ini   # optional: plugin ini (game plugin convention)
└── Resources/
    └── Icon128.png             # 128x128 png shown in Plugin Browser
```

Each subdirectory under `Source/` is its own module with its own `*.Build.cs`
(`ue-module-and-build-system`). Plugin content mounts under `/MyFeature/...`
(`ue-project-structure`). The engine and UnrealBuildTool discover plugins by scanning for
`.uplugin` files; organise plugins in subdirectories under `Plugins/` as needed, but the
engine won't scan into a discovered plugin's own subdirectories.

## The `.uplugin` descriptor

The descriptor is JSON and maps to `FPluginDescriptor`
(`Runtime/Projects/Public/PluginDescriptor.h`:38). A minimal code plugin:

```json
{
  "FileVersion": 3,
  "FriendlyName": "My Feature",
  "Version": 1,
  "VersionName": "1.0",
  "EnabledByDefault": true,
  "CanContainContent": false,
  "Modules": [
    { "Name": "MyFeature",       "Type": "Runtime", "LoadingPhase": "Default" },
    { "Name": "MyFeatureEditor", "Type": "Editor",  "LoadingPhase": "Default" }
  ],
  "Plugins": [
    { "Name": "EnhancedInput", "Enabled": true }
  ]
}
```

Key fields (`FPluginDescriptor` fields, `PluginDescriptor.h`):

| JSON key | Field | Notes |
|---|---|---|
| `FileVersion` | — | Always `3` for current UE. Required. |
| `Version` | `Version` | Integer; must increase with each release. |
| `VersionName` | `VersionName` | Human-readable version string shown in UI. |
| `EnabledByDefault` | `EnabledByDefault` (`EPluginEnabledByDefault`:28) | `true`/`false`/omit (unspecified). |
| `CanContainContent` | `bCanContainContent`:127 | Must be `true` for the `Content/` folder to mount. |
| `Modules` | `Modules`:90 — `TArray<FModuleDescriptor>` | Code modules; see below. |
| `Plugins` | `Plugins`:174 — `TArray<FPluginReferenceDescriptor>` | Other plugins this one depends on. |

For full field reference see
[references/uplugin-descriptor.md](references/uplugin-descriptor.md).

## Module types and loading phases

Each entry in `Modules` maps to `FModuleDescriptor`
(`Runtime/Projects/Public/ModuleDescriptor.h`:154). The two most important fields:

**Type** (`EHostType`, `ModuleDescriptor.h`:82) — controls which targets load the module:

| Type | Loads in |
|---|---|
| `Runtime` | All targets (game, editor, server, client) |
| `RuntimeNoCommandlet` | Runtime, but not editor commandlets |
| `Editor` | Editor only — stripped from packaged games |
| `EditorNoCommandlet` | Editor, not commandlets |
| `Developer` / `DeveloperTool` | Builds with developer tools enabled |
| `UncookedOnly` | Uncooked builds only (Blueprint nodes, etc.) |
| `ServerOnly` / `ClientOnly` | Dedicated server or client targets |
| `Program` | Standalone programs only |

**LoadingPhase** (`ELoadingPhase`, `ModuleDescriptor.h`:24) — controls when the module is
loaded relative to engine startup. Common choices:

| Phase | When | Use for |
|---|---|---|
| `PostConfigInit` | After config, before CoreUObject | Low-level hooks |
| `PreDefault` | Just before Default | Types/factories other modules depend on |
| `Default` | Standard — after game modules are loaded | Nearly all gameplay/plugin code |
| `PostEngineInit` | After engine is fully initialized | Systems that need everything available |
| `None` | Not loaded automatically | Load on demand via `FModuleManager` |

All phases are in `ELoadingPhase::Type` (`ModuleDescriptor.h`:26–59). Cross-reference
`ue-module-and-build-system` for the build-side implications of each phase.

## Module C++ wiring

Every plugin module needs exactly one registration macro in one `.cpp`:

```cpp
// MyFeatureModule.cpp
#include "Modules/ModuleManager.h"
#include "MyFeatureModule.h"

IMPLEMENT_MODULE(FMyFeatureModule, MyFeature)

void FMyFeatureModule::StartupModule()
{
    // Load any modules this one depends on to guarantee ordering
    FModuleManager::Get().LoadModuleChecked(TEXT("MyDependency"));
    // Register services, type actions, detail customizations…
}

void FMyFeatureModule::ShutdownModule()
{
    // Mirror every registration from StartupModule
}
```

- `IMPLEMENT_MODULE` is in `Runtime/Core/Public/Modules/ModuleManager.h`:946. It registers
  the module with the `FModuleManager` and installs UE's memory allocator overrides
  (`PER_MODULE_BOILERPLATE`). Every plugin module must have exactly one call.
- `IModuleInterface::StartupModule()`:49 / `ShutdownModule()`:79 in
  `Runtime/Core/Public/Modules/ModuleInterface.h`.
- Use `FDefaultModuleImpl` (no startup logic) or `FDefaultGameModuleImpl` (gameplay module)
  when you don't need custom init. See `ue-module-and-build-system` for these helpers.

Editor module pattern — guard editor-only includes with `#if WITH_EDITOR` in headers shared
with runtime modules:

```cpp
// MyFeatureEditor/Private/MyFeatureEditorModule.cpp
#include "Modules/ModuleManager.h"

class FMyFeatureEditorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override { /* register detail panels, asset actions */ }
    virtual void ShutdownModule() override { /* unregister */ }
};

IMPLEMENT_MODULE(FMyFeatureEditorModule, MyFeatureEditor)
```

## Enabling plugins

**In a project:** add to the `.uproject` `Plugins` array or use Edit → Plugins in the editor.
Each entry is a `FPluginReferenceDescriptor` (`PluginReferenceDescriptor.h`:26):

```json
"Plugins": [
  { "Name": "MyFeature", "Enabled": true }
]
```

**Engine vs project plugins:**
- Engine plugins live under the engine's `Engine/Plugins/`. Available to all projects.
- Project plugins live under the project's `Plugins/`. Local to that project.

The plugin manager discovers all `.uplugin` files in both locations at startup.

## Content-only plugins

A plugin with no source modules but with `CanContainContent: true` and a `Content/` folder
mounts as a content package. The descriptor omits the `Modules` array entirely:

```json
{
  "FileVersion": 3,
  "FriendlyName": "Shared Assets",
  "Version": 1,
  "VersionName": "1.0",
  "EnabledByDefault": true,
  "CanContainContent": true
}
```

Assets are referenced as `/SharedAssets/...` in the asset browser. No C++ required.

## Querying plugins at runtime

`IPluginManager` (`Runtime/Projects/Public/Interfaces/IPluginManager.h`:284) is the singleton
for querying and mounting plugins. `IPlugin` (`IPluginManager.h`:110) represents one plugin.

```cpp
#include "Interfaces/IPluginManager.h"

// Check if a plugin is enabled (safe to query during gameplay)
TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("MyFeature"));
if (Plugin.IsValid() && Plugin->IsEnabled())
{
    FString ContentPath = Plugin->GetMountedAssetPath(); // e.g. "/MyFeature/"
    FString BaseDir    = Plugin->GetBaseDir();           // filesystem path
}

// Enumerate all enabled plugins with content
for (TSharedRef<IPlugin> P : IPluginManager::Get().GetEnabledPluginsWithContent())
{
    // P->GetName(), P->GetMountedAssetPath(), P->GetDescriptor()
}
```

Key `IPluginManager` methods (all pure virtual, `IPluginManager.h`):

| Method | Line | Notes |
|---|---|---|
| `Get()` | 667 | Singleton accessor |
| `FindPlugin(Name)` | 393 | Find by name; returns null if not discovered |
| `FindEnabledPlugin(Name)` | 404 | Returns null if not enabled |
| `GetEnabledPlugins()` | 428 | All enabled plugins |
| `GetEnabledPluginsWithContent()` | 435 | Enabled plugins that can contain content |
| `GetDiscoveredPlugins()` | 454 | All discovered plugins (enabled or not) |

Key `IPlugin` methods:

| Method | Notes |
|---|---|
| `GetName()` | Internal name (matches folder/`.uplugin`) |
| `IsEnabled()` | Whether the plugin is currently enabled |
| `IsMounted()` | Whether content is mounted (content plugins) |
| `GetMountedAssetPath()` | Virtual root, e.g. `/MyFeature/` |
| `GetBaseDir()` | Filesystem path to plugin directory |
| `GetDescriptor()` | Full `FPluginDescriptor` struct |
| `GetType()` | `EPluginType` — Engine / Project / External / Mod |

For explicit-load plugins and runtime mounting see
[references/plugin-dependencies-and-packaging.md](references/plugin-dependencies-and-packaging.md).

## Plugin dependency hierarchy

Plugins can declare dependencies on other plugins via the `Plugins` array in `.uplugin`. The
dependency must be enabled before the plugin that depends on it. The engine enforces a
one-way hierarchy: engine modules/plugins are higher-level than project modules/plugins. An
engine plugin cannot depend on a project plugin; a project plugin can depend on an engine
plugin. Circular dependencies don't link.

For code-level dependencies between modules inside or across plugins, list the module in
`PublicDependencyModuleNames` / `PrivateDependencyModuleNames` in `Build.cs`
(`ue-module-and-build-system`).

## Updating a forked plugin submodule

- Treat fork synchronization and local submodule integration as separate operations: fetching or updating the fork's default branch does not update the project's checked-out plugin or gitlink. Fetch fork and upstream, inspect both worktrees, divergence and active branch, and preserve integration-specific commits. Preview divergent merges with `git merge-tree --write-tree`; never replace an integration checkout with upstream's default branch. For a clean detached submodule whose current commit is an ancestor of the published target, update with `git switch --detach <exact-target>` after verifying the ancestry; this preserves the project's normal detached-submodule workflow.
- Before merging with unrelated dirty files, compare them against the incoming merge-base diff and predicted conflicts; preserve staged, unstaged and untracked work separately, and pause if ownership or overlap is uncertain. Snapshot the tracked dirty patch in scratch and compare it after the merge, because an apparently clean conflict resolution does not prove the user's edits survived. Review both sides of each conflict; choose an entire side only after confirming it retains the other side's required behavior and tests.
- Sync a fork's default branch only by a non-destructive fast-forward when it has no unique commits. For a divergent integration branch, obtain required commit authorization, merge upstream, and verify both the old integration tip and upstream tip are ancestors of the result. Publish the plugin commit before committing or pushing the parent gitlink; before pushing either repository, inspect its outgoing commits and current remote ref so unrelated work is not published accidentally. For an authorized pointer-only commit, inspect and stage just the submodule path and verify the staged gitlink: it records the submodule's committed HEAD, not its uncommitted files. Read back both remote refs and the parent gitlink. Report the active integration branch, upstream containment, parent gitlink commit status, remaining submodule dirt, and any unverified build or running Editor separately; a fetched or merged source revision is not a loaded and tested plugin.
- To assess what a fork could contribute upstream, fetch current refs and inventory non-merge commits across all fork branches, then inspect each candidate's diff and search upstream source, issues and PRs for equivalent or superseding work. Reachability alone does not prove unique functionality: changes can be merged under different commits or moved to another project. Group independently reviewable fixes, rank by usefulness and preparation, distinguish historical tests from fresh upstream-base verification, and flag private inventory, credentials and license-sensitive data before proposing publication. Reconcile carried documentation against newer upstream behavior rather than copying it unchanged.
- For an authorized upstream contribution from a project-specific integration branch, inspect upstream's current contribution target and recent PR bases, then isolate only the intended fix on that base; never submit the integration branch with unrelated commits. To preserve an active dirty checkout, use a separate `GIT_INDEX_FILE` in scratch: validate that its native absolute path is nonempty before `git read-tree <upstream-base>`, stage explicitly selected worktree paths, and inspect `git diff --cached --name-status <upstream-base>` and `--check <upstream-base>` before creating a commit from the staged tree and an approved branch ref. Unset `GIT_INDEX_FILE` before checking the real checkout: an empty or stale alternate index can misleadingly report every tracked file deleted. The bare `git diff --cached` compares against the active checkout's HEAD, not the alternate index's base, and can falsely show unrelated changes. Verify the commit's parent and exact changed files, push only the authorized fork branch, and read back its remote ref and upstream comparison. Opening a PR is a separate publication action when the user reserves review first; leave the active checkout and its uncommitted work untouched.
- Keep upstream PR descriptions focused on the standalone change; omit unrelated project names and describe an untested platform simply as unverified.
- To verify a contribution against an upstream base without disturbing the integration checkout, export that exact commit with `git archive` into a unique scratch directory, overlay only the intended files and record their hashes, then use the plugin's documented standalone `RunUAT BuildPlugin` route with a new scratch package directory. Inspect the script and UAT's output-directory cleanup first; UAT may also update shared logs and caches. Verify the built artifact and distinguish this isolated compile from an Editor run of the exact same snapshot. Do not claim platform coverage from a host-only Editor build.
- Before rebuilding, claim exclusive Editor ownership and verify live project, map, PIE and dirty packages. Inspect the build script's side effects, preserve logs it clears, pass the explicit map, and require a current successful build manifest after readiness.
- Derive focused regression checks from the actual upstream diff: run the matching automation tests and exercise the changed operation through its real Editor or PIE consumer. A successful compile or graph-pin readback alone does not prove that a stack input is exposed; inspect the resulting consumer state and use a known-working control before attributing an empty result to a regression.
- Run mutating Editor regression fixtures in an unsaved scratch world (`EditorLoadingAndSavingUtils.new_blank_map(False)`), not a production map. Save nothing; after tests, account for every dirty package before returning to the saved map. Loading the saved map can release test-only undo references and clear unsaved fixture packages without saving or deleting assets; verify clean state afterward. Inspect fixture operations for implicit saves before running them; use an isolated, authorized test asset when saving is necessary, disclose retained content, and obtain required authorization before deletion.
- Snapshot camera/viewport state before a restart and restore it afterward. A restart marks an active WorkflowService run interrupted; attach the post-restart build/test evidence and finish that same journal explicitly after verification.

## Gotchas

- **Editor module type mismatch** — a module containing `#if WITH_EDITOR` editor-only code
  must be `Type: "Editor"` (or `EditorNoCommandlet`), not `Runtime`. Packaging will fail or
  strip the code if the type is wrong.
- **Missing plugin dependency** in `.uplugin` — the dependency plugin may not be enabled or
  may load after the dependent, causing startup failures even if code links fine.
- **Content not mounting** — `CanContainContent` must be `true` and assets placed under
  `Content/`. Check `IPlugin::IsMounted()` at runtime to confirm.
- **Circular plugin/module deps** — won't link. Factor shared types into a lower-level module.
- **Engine vs project plugin confusion** — engine plugins are available globally; project
  plugins are local. Copying a plugin between the two locations changes its `EPluginType`.
- **Wrong LoadingPhase** — if another module at `Default` phase needs your plugin's types but
  your plugin loads at `Default` too, ordering is undefined. Use `PreDefault` for providers.
- **bExplicitlyLoaded** — plugins with this flag set in the descriptor do not load
  automatically. They must be mounted via `IPluginManager::MountExplicitlyLoadedPlugin`
  (`IPluginManager.h`:556).
- **Config files not packaged** — plugin config files are not automatically packaged; copy
  them to the project's `Config/` folder before distribution.

## References & source material

Set `UE_ENGINE_ROOT` to the installation directory containing `Engine/`; read
`Engine/Build/Build.version` there for the exact local version.
Engine source (UE 5.8; paths below relative to `Engine/Source/` under that root):
- `Runtime/Projects/Public/PluginDescriptor.h` — `FPluginDescriptor`:38,
  `EPluginEnabledByDefault`:28, `Modules` field:90, `bCanContainContent`:127,
  `Plugins` field:174.
- `Runtime/Projects/Public/ModuleDescriptor.h` — `FModuleDescriptor`:154,
  `EHostType` namespace:82, `ELoadingPhase` namespace:24.
- `Runtime/Projects/Public/PluginReferenceDescriptor.h` — `FPluginReferenceDescriptor`:26,
  `bEnabled`:32, `bOptional`:35.
- `Runtime/Projects/Public/Interfaces/IPluginManager.h` — `IPlugin`:110, `IPluginManager`:284,
  `FindPlugin`:393, `FindEnabledPlugin`:404, `GetEnabledPlugins`:428,
  `GetEnabledPluginsWithContent`:435, `GetDiscoveredPlugins`:454, `Get()`:667.
- `Runtime/Core/Public/Modules/ModuleManager.h` — `IMPLEMENT_MODULE`:946.
- `Runtime/Core/Public/Modules/ModuleInterface.h` — `IModuleInterface`, `StartupModule`:49,
  `ShutdownModule`:79.

Real example descriptor: `Engine/Plugins/FX/Niagara/Niagara.uplugin` under `UE_ENGINE_ROOT`.

Official docs (UE 5.8):
- Plugins in Unreal Engine —
  <https://dev.epicgames.com/documentation/unreal-engine/plugins-in-unreal-engine>
- Setting Up Your Production Pipeline —
  <https://dev.epicgames.com/documentation/unreal-engine/setting-up-your-production-pipeline-in-unreal-engine>

Related skills: `ue-module-and-build-system` (build mechanics, Build.cs, IMPLEMENT_MODULE
variants), `ue-project-structure` (.uproject layout, enabling plugins), `ue-editor-scripting-and-python`
(editor automation within plugins).

Deep-dive references in this skill:
- [references/uplugin-descriptor.md](references/uplugin-descriptor.md) — full `.uplugin`
  field reference, `FPluginDescriptor` field-by-field, module descriptor detail.
- [references/plugin-structure-and-modules.md](references/plugin-structure-and-modules.md) —
  plugin folder conventions, multi-module patterns, editor vs runtime split, content config.
- [references/plugin-dependencies-and-packaging.md](references/plugin-dependencies-and-packaging.md) —
  plugin dependency rules, `FPluginReferenceDescriptor`, explicit-load plugins, packaging for
  distribution, `bOptional` dependencies.
