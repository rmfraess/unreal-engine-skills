---
name: plugins-and-modules
description: >-
  Use when creating or maintaining Unreal plugins. Covers descriptors, modules, dependencies, loading phases, packaging, editor-runtime boundaries, and distribution.
license: UNLICENSED
metadata:
  engine-version: "5.8"
  category: tooling
  hermes:
    tags: [unreal-engine, ue5, plugins, modules]
    related_skills: [navigating-engine-source]
---

# Plugins & modules

A **plugin** is a self-contained, portable feature bundle: a `.uplugin` descriptor file plus
one or more C++ modules and optional content/resources. Use plugins when the feature is
reusable across projects, optional (so it can be disabled), or ships as an editor tool.
Compare with project modules (`module-and-build-system`): project modules compile into your
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

Choose a plugin when: the feature will be used in more than one project, it is optional, or it
is an editor-only tool you want to ship separately.

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
(`module-and-build-system`). Plugin content mounts under `/MyFeature/...`
(`project-structure`). The engine and UnrealBuildTool discover plugins by scanning for
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

Each `Modules` entry declares a module name, host `Type`, and `LoadingPhase`. Keep runtime code
in runtime host types and editor integrations in an editor module so packaged targets never
acquire editor-only dependencies. Load `module-and-build-system` for the authoritative host-type
and loading-phase tables, `Build.cs` dependencies, registration macros, and load verification.

## Module C++ wiring

Every plugin module still needs exactly one registration macro in one `.cpp`, and shutdown must
mirror startup registrations. Keep plugin-specific ownership here; use `module-and-build-system`
for the canonical `IMPLEMENT_MODULE`, `IModuleInterface`, and editor/runtime wiring patterns.

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
(`module-and-build-system`).

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

Engine source (UE 5.8, under the verified `<UE_ENGINE_ROOT>/Engine/Source/`):
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

Real example descriptor: `<UE_ENGINE_ROOT>/Engine/Plugins/FX/Niagara/Niagara.uplugin`

Official docs (UE 5.8):
- Plugins in Unreal Engine —
  <https://dev.epicgames.com/documentation/unreal-engine/plugins-in-unreal-engine>
- Setting Up Your Production Pipeline —
  <https://dev.epicgames.com/documentation/unreal-engine/setting-up-your-production-pipeline-in-unreal-engine>

Related skills: `module-and-build-system` (build mechanics, Build.cs, IMPLEMENT_MODULE
variants), `project-structure` (.uproject layout, enabling plugins), `editor-scripting-and-python`
(editor automation within plugins).

Deep-dive references in this skill:
- [references/uplugin-descriptor.md](references/uplugin-descriptor.md) — full `.uplugin`
  field reference, `FPluginDescriptor` field-by-field, module descriptor detail.
- [references/plugin-structure-and-modules.md](references/plugin-structure-and-modules.md) —
  plugin folder conventions, multi-module patterns, editor vs runtime split, content config.
- [references/plugin-dependencies-and-packaging.md](references/plugin-dependencies-and-packaging.md) —
  plugin dependency rules, `FPluginReferenceDescriptor`, explicit-load plugins, packaging for
  distribution, `bOptional` dependencies.
