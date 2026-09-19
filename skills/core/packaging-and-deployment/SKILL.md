---
name: packaging-and-deployment
description: >-
  Use when cooking or packaging Unreal projects. Covers BuildCookRun, configurations, staging, Pak and IoStore, chunks, platforms, DLC, and verification.
license: UNLICENSED
metadata:
  engine-version: "5.8"
  category: tooling
  hermes:
    tags: [unreal-engine, ue5, packaging, deployment]
    related_skills: [navigating-engine-source]
---

# Packaging & deployment

Shipping an Unreal project involves three distinct stages that run in sequence:
**build** (compile the game executable), **cook** (convert assets to the target
platform's runtime format), and **package** (assemble the cooked assets and executable
into a distributable build, typically inside pak/IoStore containers). Each stage can fail
independently; diagnosing a failure means identifying which stage it belongs to.

## When to use this skill

- Producing a runnable build for a platform (automated CI or manual).
- Diagnosing a cook or package failure, or a build that works in PIE but breaks packaged.
- Configuring what content ships: always-cook directories, never-cook exclusions, shader sharing.
- Setting up pak chunking for streaming installs, patching, or DLC.
- Choosing the right build configuration and target for a given deployment scenario.

## Build configurations and targets

**Target types** — defined by `*.Target.cs` files, one per target:

| Target | Produces | Use for |
|---|---|---|
| `Game` | Cooked, monolithic game executable | Shipping, QA, end-user builds |
| `Editor` | Modular editor + DLL set | Development only; never packaged for end users |
| `Client` | Game executable, no server code | Client-only in a client/server split |
| `Server` | Headless game server, no client rendering | Dedicated server for multiplayer |
| `Program` | Standalone program (e.g. ShaderCompileWorker) | Engine tooling |

Source: `TargetType` enum — `Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/TargetRules.cs`:21.

**Build configurations** — controls optimization and what debugging/logging facilities are
compiled in:

| Configuration | Optimized? | `check`/`ensure`? | Logging? | Use for |
|---|---|---|---|---|
| `Debug` | No | Yes | Full | Full engine+game debug (slow) |
| `DebugGame` | Engine yes, game no | Yes | Full | Debug game modules only |
| `Development` | Yes | Yes | Full | Daily iteration; editor default |
| `Test` | Yes | Some | Some | Performance test; shipping-like |
| `Shipping` | Max | No | Minimal | Release builds |

Source: `UnrealTargetConfiguration` enum —
`Engine/Source/Programs/UnrealBuildTool/Configuration/UEBuildTarget.cs`:1147.

The packaging UI (`EProjectPackagingBuildConfigurations`) mirrors these five values as
`PPBC_Debug … PPBC_Shipping` — see `ProjectPackagingSettings.h`:18.

**Key rule:** always test the Shipping (or Test) configuration before release. `check()`
macros, most `UE_LOG` calls, and the console are stripped or limited in Shipping — never
put logic inside a `check` or rely on console state in packaged builds. See
`logging-and-assertions`.

## The cook process

Cooking converts editor assets (`.uasset`, textures, audio) into the target platform's
runtime format. The cooker is invoked as a special commandlet mode of `UnrealEditor-cmd`.

**What gets cooked:** assets reachable via hard or soft references from the startup map
and any "always cook" directories/entries. Unreferenced content is not cooked. This is
why a purely string-loaded asset (soft path with no reference) silently disappears unless
you declare it via the Asset Manager or `DirectoriesToAlwaysCook`.

**Cook modes:**
- **By-the-book (CBTB):** entire cook runs up front; produces the full set of cooked
  packages before packaging. Required for final/CI builds.
- **Cook on the fly (COTF):** a cook server on the host machine serves packages on demand
  as a connected device requests them. Faster iteration, but not suitable for final builds.

**Cook rules** (per primary asset, set via Asset Manager or `DefaultGame.ini`):
- `AlwaysCook` — include regardless of reference.
- `NeverCook` — exclude even if referenced (e.g. editor-only test assets).
- `Unknown` — follow reference graph (default).

Shader code can be shared across materials via `bShareMaterialShaderCode` in
`UProjectPackagingSettings` — reduces duplication at a small load-time cost.

## UAT BuildCookRun — the canonical pipeline

The Unreal Automation Tool (`RunUAT.bat` / `RunUAT.sh`) orchestrates the full pipeline
via its `BuildCookRun` command:

```
Engine/Build/BatchFiles/RunUAT.bat BuildCookRun \
  -project=D:/MyGame/MyGame.uproject \
  -noP4 \
  -platform=Win64 \
  -clientconfig=Shipping \
  -build \
  -cook \
  -allmaps \
  -stage \
  -pak \
  -archive \
  -archivedirectory=D:/Builds/MyGame_Shipping
```

Each flag maps to a stage: `-build` compiles the target, `-cook` runs the cooker,
`-stage` copies to a staging directory, `-pak` wraps cooked content into .pak/IoStore
containers, `-archive` copies the final build to the output path. Omit any stage to skip
it (e.g. skip `-build` when the executable is already built by a separate CI step).

Packaging is complete when every selected stage succeeds, a clean launch outside the editor
loads the startup map and representative soft-referenced content, and the target-platform
Shipping build completes its smoke test without missing-package errors.

Add `-iostore` to enable IoStore container output (`.utoc`/`.ucas`) instead of classic
`.pak`-only output. This matches enabling `bUseIoStore` in Project Settings.

UAT script path (C#): `Engine/Source/Programs/AutomationTool/Scripts/BuildCookRun.Automation.cs`.

Full BuildCookRun flag reference: [references/buildcookrun-and-uat.md](references/buildcookrun-and-uat.md).

## Pak files and the IoStore container format

After cooking, content is packaged into containers for distribution:

- **Classic pak (`.pak`):** a simple archive format; a single monolithic file or one per
  chunk. Still fully supported; adequate for many projects.
- **IoStore (`.utoc` + `.ucas`):** the modern default. `.utoc` is the table of contents;
  `.ucas` holds the bulk payload. Offers faster I/O via the IoDispatcher because packages
  are addressed by hash ID rather than path. Enabled via `bUseIoStore = true` in Project
  Settings (or `-iostore` flag to UAT).

Both formats support compression (`bCompressed`, `PackageCompressionFormat`) and
encryption (configured via the crypto key system, not the deprecated ini flags).

**Chunking** splits content across multiple pak/IoStore containers for streaming installs,
DLC, or patching. Each configured chunk is packaging metadata that may produce numbered
container files (for example `pakchunk1-Windows.pak`); the platform/launcher/patch/DLC
integration decides how those files are delivered and mounted. Do not infer from a chunk ID
alone that a file is downloaded separately or that chunk 0 is always the complete base install.
Configure chunk generation with `bGenerateChunks` and Primary Asset Rules, then generate and
inspect the manifests required by the selected delivery path.

Details: [references/pak-iostore-and-chunking.md](references/pak-iostore-and-chunking.md).

## ProjectPackagingSettings — what ships

`UProjectPackagingSettings` (`UCLASS(config=Game, defaultconfig)`) persists to
`Config/DefaultGame.ini` under section `[/Script/UnrealEd.ProjectPackagingSettings]`.
Key properties (verified in
`Engine/Source/Developer/DeveloperToolSettings/Classes/Settings/ProjectPackagingSettings.h`):

| Property | Effect |
|---|---|
| `BuildConfiguration` (`PPBC_*`) | Which configuration to build |
| `bUseIoStore` | Use `.utoc`/`.ucas` IoStore containers |
| `bUseZenStore` | Use Zen Server as cooked data store (requires `bUseIoStore`) |
| `bGenerateChunks` | Split content into numbered chunks |
| `bGenerateNoChunks` | Override all platforms to disable chunking |
| `bChunkHardReferencesOnly` | Only hard-reference dependencies follow their chunk |
| `bCompressed` | Compress cooked packages |
| `PackageCompressionFormat` | Comma-separated list (e.g. `Oodle`) |
| `bShareMaterialShaderCode` | Deduplicate shader bytecode across materials |
| `DirectoriesToAlwaysCook` | Force-cook these content paths regardless of references |
| `DirectoriesToNeverCook` | Exclude these paths even if referenced |
| `MapsToCook` | Explicit map list when not using `-allmaps` |
| `bCookAll` | Cook every asset in the content directory |
| `bSkipEditorContent` | Exclude `/Game/Editor*` folders from the cook |

Access in code: `GetDefault<UProjectPackagingSettings>()` (editor only).

## Platforms, Device Profiles, and scalability

Each platform target (Win64, Android, iOS, console) requires its SDK and platform files.
Platform-specific packaging overrides live in `Config/[Platform]/[Platform]Game.ini`.

**Device Profiles** (`DeviceProfiles.ini`) set per-platform CVars and scalability groups —
the correct way to vary rendering quality per platform. Never hardcode `r.*` CVars in
C++ or Blueprint; use Device Profiles so the cooker and runtime can select them correctly.

A **Client/Server** split (`Game` + `Server` targets built separately) is the standard
multiplayer packaging pattern; the server binary runs headless and ships without rendering
modules. See `networking-and-replication`.

## Content-on-demand / IoStore On-Demand (optional/experimental scope)

UE 5.8.2 exposes the IoStore On-Demand interfaces under the experimental runtime source tree,
but this is not a generic “ship a CDN” switch. UAT enables the path with
`-applyiostoreondemand`, which adds `-CompileIoStoreOnDemand` and forces chunk manifests; the
settings default to disabled when no On-Demand settings are supplied. Treat hosting,
authentication/authorization, mount policy, failure recovery, patch compatibility, and target
platform support as project-owned delivery infrastructure. For ordinary shipping distribution,
use the project’s validated container/patch/DLC pipeline until an On-Demand integration has
been tested end to end.

## Shipping vs. development (mind the gap)

| Behavior | Development | Shipping |
|---|---|---|
| `check()` / `ensure()` | Fire, assert | Compiled out (`DO_CHECK=0`) |
| `UE_LOG(...)` | All categories | Most stripped; use sparingly |
| Console commands | Available | Removed |
| `WITH_EDITOR` code | Included | Excluded |
| Editor modules | Loaded | Not present |

Always smoke-test a **packaged Shipping build** before release — PIE and Development
builds mask many of these gaps. Guard editor-only code with `#if WITH_EDITOR` so it
compiles out of runtime targets. See `logging-and-assertions` for `verify` vs `check`.

## Gotchas

- **Editor-only API in runtime code** — cook/link errors; gate with `#if WITH_EDITOR`.
- **Content not reachable** — not cooked → missing at runtime. Hard-ref or add to
  `DirectoriesToAlwaysCook`. Use the Asset Audit window to inspect chunk assignments.
- **Works in PIE, broken packaged** — typically editor-only deps, uncooked assets, or
  absolute file paths.
- **`check`/`ensure`/`UE_LOG` used for logic** — silently does nothing in Shipping;
  never put required side-effects inside them.
- **Hardcoded `r.*` CVars** — bypass Device Profiles and platform-specific scalability.
- **Forgot `-iostore` flag with IoStore settings** — UAT and Project Settings must agree.
- **bUseZenStore without bUseIoStore** — Zen Store is a no-op unless IoStore is enabled.
- **Wrong target cooked** — cooking the Editor target instead of Game produces an
  unrunnable result; confirm the `BuildTarget` in `ProjectPackagingSettings`.
- **Cook time blowup** — enable iterative cooking (`-iterate` flag to UAT) during
  iteration; disable for final CI builds to guarantee a clean output.

## Version notes

- **IoStore:** `bUseIoStore` is a project/platform setting; the UE 5.8.2 source does not make
  this generic skill’s “modern” wording a universal default. Inspect the effective project
  settings and UAT arguments. Classic `.pak` output remains a separate supported choice where
  the target platform permits it.
- **Zenserver cooked output store (UE 5.8):** the release notes describe Zenserver as enabled by
  default for the new cooked-output workflow, while existing projects that disabled Zen remain
  disabled. `GetUseZenStoreEffective()` still requires both `bUseZenStore` and `bUseIoStore`.
- **Incremental Cooking (Beta, UE 5.8):** Zen-backed incremental cooking reduces recooking of
  unchanged native assets, including Blueprints and World Partition tiles. Keep it separate from
  ordinary `-iterate`/iterative cook guidance, and do not treat the Beta workflow as a clean
  release-cook replacement.
- **Blueprint nativization** is deprecated (removed in UE5, `UE_DEPRECATED(5.0, ...)`);
  do not rely on it.

## References & source material

Engine source (UE 5.8):
- `UProjectPackagingSettings` (properties, enums, cook rules) —
  `Engine/Source/Developer/DeveloperToolSettings/Classes/Settings/ProjectPackagingSettings.h`:179.
  `EProjectPackagingBuildConfigurations`:18, `EAssetRegistryWritebackMethod`:106,
  `bUseIoStore`:250, `bGenerateChunks`:265, `bCompressed`:323, `DirectoriesToAlwaysCook`:568.
- `TargetType` enum — `Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/TargetRules.cs`:21.
- `UnrealTargetConfiguration` enum (Debug…Shipping) —
  `Engine/Source/Programs/UnrealBuildTool/Configuration/UEBuildTarget.cs`:1147.
- `BuildCookRun` UAT command class —
  `Engine/Source/Programs/AutomationTool/Scripts/BuildCookRun.Automation.cs`:24.
- IoStore container format (`EIoStoreTocVersion`, `FIoStoreTocHeader`) —
  `Engine/Source/Runtime/Core/Internal/IO/IoStore.h`:25.
- IoStore On-Demand (`IOnDemandIoStore`:647, `FOnDemandRequest`:46) —
  `Engine/Source/Runtime/Experimental/IoStore/OnDemandCore/Public/IO/IoStoreOnDemand.h`.
- `WITH_EDITOR`, `WITH_EDITORONLY_DATA` preprocessor guards —
  `Engine/Source/Runtime/Core/Public/Misc/Build.h`:66.

Official docs (UE 5.8, all fetched and confirmed live):
- Build Configurations Reference —
  <https://dev.epicgames.com/documentation/unreal-engine/build-configurations-reference-for-unreal-engine>
- Build Operations: Cook, Package, Deploy, and Run —
  <https://dev.epicgames.com/documentation/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine>
- Cooking and Chunking —
  <https://dev.epicgames.com/documentation/unreal-engine/cooking-content-and-creating-chunks-in-unreal-engine>
- Project Launcher Reference —
  <https://dev.epicgames.com/documentation/unreal-engine/using-the-project-launcher-in-unreal-engine>
- Patching, Content Delivery, and DLC —
  <https://dev.epicgames.com/documentation/unreal-engine/patching-content-delivery-and-dlc-in-unreal-engine>
- Sharing and Releasing Projects —
  <https://dev.epicgames.com/documentation/unreal-engine/sharing-and-releasing-projects-for-unreal-engine>

Deep-dive references in this skill:
- [references/cook-and-build-configs.md](references/cook-and-build-configs.md) — cook
  pipeline internals, cook rules, shader sharing, iterative cook, cook commandlet options.
- [references/buildcookrun-and-uat.md](references/buildcookrun-and-uat.md) — full
  BuildCookRun flag reference, UAT structure, CI patterns.
- [references/pak-iostore-and-chunking.md](references/pak-iostore-and-chunking.md) —
  pak vs IoStore format details, chunk assignment (Asset Manager, Primary Asset Labels,
  config overrides), compression, encryption.
- [references/platform-and-dlc.md](references/platform-and-dlc.md) — platform targets,
  Device Profiles, Client/Server split, IoStore On-Demand / content-on-demand, patching.

Related skills: `module-and-build-system`, `asset-management`, `logging-and-assertions`,
`networking-and-replication`, `project-structure`.
