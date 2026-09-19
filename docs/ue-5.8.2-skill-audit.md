# Unreal Engine 5.8.2 skill upgrade audit — Markdown diff report

**Repository:** `D:/Dev/Personal/unreal-engine-skills`  
**Baseline commit:** `8e5ba6c83195061839cc4492148cfbf00265a7ff` (`master`); current working-tree additions are accounted for in the final validation notes.  
**Repository routing verified:** `origin` fetch/push = `https://github.com/rmfraess/unreal-engine-skills.git`. The working tree contains seven modified skills and one additional supporting reference from outside this report's edits; they were preserved. This is not a clean-checkout audit.  
**Pinned engine:** UE `5.8.2`, installed read-only at `C:/Program Files/Epic Games/UE_5.8`; `Engine/Build/Build.version` reports Major 5, Minor 8, Patch 2, Changelist `56702186`, CompatibleChangelist `55116800`, promoted release branch `++UE5+Release-5.8`.  
**Scope:** every repository skill in repository-path order, one skill at a time; each `SKILL.md` and every file below its skill directory is read in full. No skill files are modified by this audit.

## Evidence and comparison basis

- Epic’s UE 5.8 release notes: [Unreal Engine 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), fully fetched locally at `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md` (the fetched release-notes document includes the UE 5.8 Upgrade Notes and Deprecations sections).
- Epic’s 5.8.1 hotfix notes: [5.8.1 Hotfix Released](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), fetched directly during this audit.
- Epic’s 5.8.2 hotfix notes: [5.8.2 Hotfix Released](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335), fully fetched locally at `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/forums.unrealengine.com-d1d8d96bf4.md`.
- Epic’s major-release announcement: [Unreal Engine 5.8 is now available](https://www.unrealengine.com/news/unreal-engine-5-8-is-now-available).
- Installed-source verification uses paths under `C:/Program Files/Epic Games/UE_5.8/Engine/`; paths are paired with the symbol and the installed `5.8.2` `Build.version` above. Line numbers in repository skills are treated as claims to check, not as authority.
- Marketplace skills are not checked with the engine citation checker. No other project or vendor installation was entered; product-specific findings are therefore marked as unresolved where installed-product/vendor evidence is absent.

## Method and validation boundary

The audit looks for: 5.8/5.8.1/5.8.2 behavior changes, Upgrade Notes and Deprecations, stale or incorrect API guidance, missing practical 5.8 features, unsupported beta/experimental claims, duplication, and citations that do not identify a verifiable source. Recommendations are intentionally scoped to actionable skill upgrades; “no changes” means no evidence-led upgrade was found, not that every possible API claim was compile-tested.

The repository’s citation-existence baseline was run by the parent audit with the available Node `v26.7.0`, not the repository-prescribed Node 22: core scope exited 0, scanned 202 Markdown files, checked 584 citations, and found all cited paths. This proves path existence only—not symbol/API correctness, documentation-version correctness, or per-skill completeness—and is not called a prescribed validation pass.

**Final coverage:** 62 of 62 skills: 47 core, 10 Ultra Dynamic Sky, 5 Ultra Dynamic Weather. The original inventory contained 155 supporting files; the current tree contains **156**, including `profiling-and-optimization/references/windows-pie-baselines.md`, reviewed during final reconciliation. Total scope is **218 skill-directory files**. Every skill is classified below; partial verification is not an approval of the unresolved claims.

**Target release rechecked 2026-09-18:** Epic's major-release announcement and official hotfix announcement identify 5.8 and released **5.8.2**; the installed `Build.version` matches **5.8.2 / CL 56702186**. A search for 5.8.3 found a future-fix discussion, not a released hotfix announcement. Therefore **5.8.2 is the latest stable release verified by this audit**, not a promise about releases published after this check. Epic documentation is generally versioned at 5.8, not per hotfix; the 5.8.1/5.8.2 notes and exact installed source bridge that granularity gap.

**Reading this report:** P1 fixes correctness or unsafe workflow guidance; P2 improves current capability, clarity, or maintainability; P3 is lower-impact polish. Diff blocks are proposed edits for human approval, not a directly applicable patch set. Repository locations are relative to the owning skill unless fully qualified. Earlier core locations reference the audited baseline; use the named passage when later working-tree insertions shifted lines. A supporting source establishes only the claim it is cited for, not every sentence in the skill. No Unreal compilation, PIE, cook, package, render, or vendor-asset execution is claimed.

**Disposition:** 59 skill sections are classified as findings; `core/game-thread-performance` has no changes recommended; `core/mover-movement-system` and `ultra-dynamic-sky/uds-sun-moon-stars` are classified as partially verified. Finding-bearing sections also carry claim-level evidence gaps; these totals are coverage dispositions, not 59 fully validated integrations.

---

## core/actors-and-components

**Status:** findings  
**Repository path:** `skills/core/actors-and-components/`  
**Files reviewed:** `SKILL.md`; `references/actor-lifecycle.md`; `references/attachment-and-transforms.md`; `references/components-and-registration.md`; `references/spawning-and-destroying.md`.

### Verified recommendations

#### A&C-01 — correct component/actor `BeginPlay` ordering

- **Priority:** P1 — correctness; the current wording can make an agent put actor initialization before a component is ready, causing order-dependent bindings or null/uninitialized state.
- **Locations:** `SKILL.md:61-68` and `SKILL.md:228-237`; `references/actor-lifecycle.md:52-63`; `references/components-and-registration.md:95-103`.
- **Finding:** the main lifecycle text says that `BeginPlay` starts gameplay and that the actor then drives component `BeginPlay`, which is broadly incomplete; the supporting component reference explicitly says component `BeginPlay` runs “after the owning actor’s `BeginPlay`,” which conflicts with the installed source. In UE 5.8.2’s normal base implementation, `AActor::BeginPlay()` loops over registered components and calls `UActorComponent::BeginPlay()` before `ReceiveBeginPlay()`. An overriding actor must still call `Super::BeginPlay()` first if it relies on that ordering.
- **Exact proposed replacement:**

```diff
--- a/skills/core/actors-and-components/SKILL.md
+++ b/skills/core/actors-and-components/SKILL.md
@@
-4. **`BeginPlay`** — gameplay starts. Do gameplay init here (spawning, timers, delegate bindings),
-   **not** in the constructor.
+4. **`BeginPlay`** — gameplay starts. In the normal `Super::BeginPlay()` path,
+   `AActor::BeginPlay()` starts registered component `BeginPlay()` calls before the actor's
+   `ReceiveBeginPlay()` event. Call `Super::BeginPlay()` first in overrides, then do gameplay
+   init (spawning, timers, delegate bindings), **not** in the constructor.
@@
-Then `BeginPlay` runs on the actor, which in turn drives `BeginPlay` on its components.
+In the base actor route, `AActor::BeginPlay()` registers actor ticks, calls `BeginPlay()` on
+   each registered component, and then dispatches the actor's Blueprint `ReceiveBeginPlay()`.
+   An actor override can change the order if it executes code before `Super::BeginPlay()`, so
+   call `Super` first when component initialization must already have happened.
--- a/skills/core/actors-and-components/references/actor-lifecycle.md
+++ b/skills/core/actors-and-components/references/actor-lifecycle.md
@@
-Then `BeginPlay` runs on the actor, which in turn drives `BeginPlay` on its components.
+In the base actor route, `AActor::BeginPlay()` calls `BeginPlay()` on each registered component
+before it dispatches the actor's Blueprint `ReceiveBeginPlay()` event. Call `Super::BeginPlay()`
+first in an actor override when that ordering is required.
--- a/skills/core/actors-and-components/references/components-and-registration.md
+++ b/skills/core/actors-and-components/references/components-and-registration.md
@@
-- `UActorComponent::BeginPlay` (`ActorComponent.h`:936) runs when gameplay starts, after the owning actor's
-  `BeginPlay`. Bind delegates and start gameplay interactions here. The mirror cleanup is `EndPlay` (`:949`);
-  `UninitializeComponent` (`:955`) mirrors `InitializeComponent`.
+- `UActorComponent::BeginPlay` (`ActorComponent.h`:936) runs when gameplay starts; the base
+  `AActor::BeginPlay()` calls it on each registered component before the actor's
+  `ReceiveBeginPlay()` event. Bind delegates and start component gameplay interactions here.
+  Call `Super::BeginPlay()` first in an actor override when component setup must precede actor
+  code. The mirror cleanup is `EndPlay` (`:949`); `UninitializeComponent` (`:955`) mirrors
+  `InitializeComponent`.
```

- **Practical task benefit:** agents will produce lifecycle overrides that do not assume the actor’s Blueprint event precedes component startup; this removes a real initialization-order bug without adding a new abstraction.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/Actor.cpp:4738-4848` (`AActor::DispatchBeginPlay`, `AActor::BeginPlay`) loops through registered components at `4816-4826` and calls `ReceiveBeginPlay()` at `4846`; `.../Engine/Private/Components/ActorComponent.cpp:1648-1662` is `UActorComponent::BeginPlay()`. The declaration comment at `.../Engine/Classes/Components/ActorComponent.h:925-943` states that component Blueprint `ReceiveBeginPlay` is called before the owning actor’s `BeginPlay`. UE 5.8.2 source. The UE 5.8 [Actor Lifecycle](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-actor-lifecycle) documentation is the matching conceptual reference.

### No-change checks

- `CreateDefaultSubobject`, `SetupAttachment`, runtime `AttachToComponent`, component registration, deferred spawning, collision handling, mobility, and tick guidance map to UE 5.8.2 declarations in `Actor.h`, `ActorComponent.h`, `SceneComponent.h`, `World.h`, `EngineTypes.h`, and `CoreUObject/Public/UObject/Object.h`.
- The 5.8 release notes, 5.8.1 hotfix notes, and 5.8.2 hotfix notes reviewed for this skill did not identify a behavior-changing actor/component lifecycle or spawning migration that warrants a separate upgrade item. The 5.8.2 World Partition Blueprint attachment-hierarchy fix is recorded for the World Partition skill, where its operational context belongs.

### Unresolved questions / verification gaps

- The official actor-lifecycle page was verified as the matching Epic topic, but this audit did not perform a packaged-project runtime test of every lifecycle path (load, PIE duplication, network spawn, deferred spawn, and streaming resurrection).
- The repository’s cited line numbers were compared with the installed 5.8.2 source for the named symbols; line-number drift should still be expected in later hotfixes.

---

## core/ai-and-navigation

**Status:** findings  
**Repository path:** `skills/core/ai-and-navigation/`  
**Files reviewed:** `SKILL.md`; `references/behavior-tree-deep-dive.md`; `references/eqs-deep-dive.md`; `references/navigation-deep-dive.md`; `references/perception-and-statetree.md`.

### Verified recommendations

#### AI-NAV-01 — document the UE 5.8 EQS client-strip option

- **Priority:** P2 — practical packaging optimization; server-only EQS assets otherwise remain eligible for client builds.
- **Location:** precise insertion point after `SKILL.md:182-184` (“Enable EQS in Project Settings”), or after `references/eqs-deep-dive.md:134-138`.
- **Finding:** the skill covers server-only AI in passing but does not expose the UE 5.8 `UEnvQuery::bStripFromClientBuilds` switch.
- **Exact proposed addition:**

```diff
--- a/skills/core/ai-and-navigation/SKILL.md
+++ b/skills/core/ai-and-navigation/SKILL.md
@@
 `FQueryFinishedSignature` is declared in `EnvQueryManager.h`. Enable EQS in Project Settings
 → AI → Enable EQS. The EQS Testing Pawn (`AEQSTestingPawn`) lets you visualize query results
 in the editor viewport without running the game.
+
+For EQS assets used only by server-side AI, enable `UEnvQuery::bStripFromClientBuilds` in
+UE 5.8. This excludes the query from client builds; do not enable it for a query a client
+must load or execute.
```

- **Practical task benefit:** reduces client package contents and makes the server-only intent explicit without changing runtime AI behavior.
- **Verified evidence:** UE 5.8 release notes, [AI EQS](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#aieqs), lines 6170-6174 of the fetched notes; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/AIModule/Classes/EnvironmentQuery/EnvQuery.h:39-61`, `UEnvQuery::bStripFromClientBuilds`, `NeedsLoadForClient`, and `NeedsLoadForEditorGame`, UE 5.8.2.

#### AI-NAV-02 — add per-static-mesh navigation area costs

- **Priority:** P2 — useful authoring capability for navigation-heavy levels; avoids requiring a separate modifier volume for every static mesh whose walkable surface should carry an area class.
- **Location:** precise insertion point after `references/navigation-deep-dive.md:36-38`, before the query-filter subsection at line 40.
- **Finding:** the navigation reference explains `UNavArea`, `UNavModifierComponent`, and `ANavModifierVolume`, but omits UE 5.8’s per-mesh `UNavCollision` surface-area path.
- **Exact proposed addition:**

```diff
--- a/skills/core/ai-and-navigation/references/navigation-deep-dive.md
+++ b/skills/core/ai-and-navigation/references/navigation-deep-dive.md
@@
 - `UNavModifierComponent` on an actor — applies the area to the actor's collision.
 - `ANavModifierVolume` — a level-placed volume with an assigned `NavArea` class.
+
+UE 5.8 also supports a custom area on a static mesh's walkable surface through
+`UNavCollision::bUseSurfaceArea` and `AreaClass`. The surface area is applied during
+triangle rasterization/voxelization; it is mutually exclusive with `bIsDynamicObstacle`.
+Use this when the mesh itself should carry a traversal class, and use a modifier component
+or volume when the area is authored independently of the mesh.
```

- **Practical task benefit:** gives level and AI agents a native way to encode “walk around this mesh” or other per-mesh traversal costs and clarifies when the existing modifier tools remain the better fit.
- **Verified evidence:** UE 5.8 release notes, [Navigation: Per-Mesh Control Over Walkable Surfaces](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#navigationpermeshcontroloverwalkablesurfaces), lines 1093-1099, and [AI Navigation](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#ainavigation), lines 6206-6209; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/AI/Navigation/NavCollisionBase.h:33-40`, `UNavCollisionBase::bIsDynamicObstacle`/`bUseSurfaceArea`, and `.../NavigationSystem/Public/NavCollision.h:62-79`, `UNavCollision::AreaClass`, UE 5.8.2.

### No-change checks

- Behavior Tree node instancing, `NodeMemory`, `FinishLatentTask`, EQS request execution, perception delegate names, navigation invokers, and the StateTree component/task declarations were checked against the installed 5.8.2 headers. The named APIs exist with the documented modules and the snippets do not require a 5.8 migration rewrite.
- UE 5.8 adds StateTree starting-state/compiler workflows and queued compilation controls, but the checked skill is a runtime decision and authoring guide rather than a StateTree editor-release-notes guide. No unsupported beta/experimental label was found that needs correction; the release notes’ experimental state-centric view is not presented as the normal runtime API.
- The 5.8.1 notes and 5.8.2 notes were checked for AI, navigation, EQS, and StateTree regressions. They contain fixes and diagnostics but no conflicting change to the core BT/EQS/perception API guidance. The 5.8.2 known issue is Mac/Xcode 26.4+ animation-editor compilation, outside this skill.

### Unresolved questions / verification gaps

- No packaged client/server cook was run to prove `bStripFromClientBuilds` behavior; the recommendation is source-and-release-note verified only.
- Navigation invoker and World Partition behavior were not exercised in a streamed test map, and no project-specific nav settings were available.
- StateTree task behavior was verified from declarations, not from a compiled custom task or a running StateTree asset; the report does not claim a full StateTree runtime validation.

---

## core/animation-system

**Status:** findings  
**Repository path:** `skills/core/animation-system/`  
**Files reviewed:** `SKILL.md`; `references/anim-instance-and-update.md`; `references/montages-and-slots.md`; `references/motion-matching-and-warping.md`; `references/state-machines-and-blending.md`.

### Verified recommendations

#### ANIM-01 — keep UObject reads out of `NativeThreadSafeUpdateAnimation`

- **Priority:** P1 — correctness under parallel animation evaluation; the current sample directly calls character UObject methods from the worker-thread override it recommends for thread-safe work.
- **Locations:** `SKILL.md:84-99`; the rule at `SKILL.md:102-109` is the insertion point for the explicit snapshot requirement.
- **Finding:** `NativeThreadSafeUpdateAnimation` is correctly identified as a worker-thread hook, but the sample dereferences `OwnerCharacter` and calls `GetVelocity()`, `GetCharacterMovement()`, `IsFalling()`, and `GetActorRotation()` there. Those reads should be gathered on the game thread and passed as value snapshots; caching a UObject pointer is not the same as making arbitrary UObject access thread-safe.
- **Exact proposed replacement:**

```diff
--- a/skills/core/animation-system/SKILL.md
+++ b/skills/core/animation-system/SKILL.md
@@
 void UMyAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
 {
     Super::NativeUpdateAnimation(DeltaSeconds);
     // Keep lightweight — prefer NativeThreadSafeUpdateAnimation for heavy logic
     if (!OwnerCharacter) { OwnerCharacter = Cast<ACharacter>(TryGetPawnOwner()); }
+    if (OwnerCharacter)
+    {
+        CachedVelocity = OwnerCharacter->GetVelocity();
+        CachedActorRotation = OwnerCharacter->GetActorRotation();
+        if (const UCharacterMovementComponent* Movement = OwnerCharacter->GetCharacterMovement())
+            CachedIsFalling = Movement->IsFalling();
+    }
 }
 
 void UMyAnimInstance::NativeThreadSafeUpdateAnimation(float DeltaSeconds)
 {
     Super::NativeThreadSafeUpdateAnimation(DeltaSeconds);
-    if (!OwnerCharacter) { return; }
-    const FVector Vel = OwnerCharacter->GetVelocity();
-    Speed     = Vel.Size2D();
-    bIsFalling = OwnerCharacter->GetCharacterMovement()->IsFalling();
-    Direction = UKismetAnimationLibrary::CalculateDirection(Vel, OwnerCharacter->GetActorRotation());
+    Speed = CachedVelocity.Size2D();
+    bIsFalling = CachedIsFalling;
+    Direction = UKismetAnimationLibrary::CalculateDirection(CachedVelocity, CachedActorRotation);
 }
```

Add value members beside the existing animation variables:

```diff
@@
     UPROPERTY(BlueprintReadOnly, Category="Locomotion") bool  bIsFalling = false;
+    FVector CachedVelocity = FVector::ZeroVector;
+    FRotator CachedActorRotation = FRotator::ZeroRotator;
+    bool CachedIsFalling = false;
```

Also sharpen the rule:

```diff
@@
-`NativeThreadSafeUpdateAnimation` — worker-thread update; no `UWorld` queries, no spawning,
-  no non-thread-safe engine calls. This is where to put heavy per-frame computation.
+`NativeThreadSafeUpdateAnimation` — worker-thread update; consume only value snapshots prepared
+  on the game thread (or data marshalled through an `FAnimInstanceProxy`). Do not dereference
+  the owner actor, query `UWorld`, spawn, or call other non-thread-safe engine APIs here.
+  This is where to put heavy pure computation over those snapshots.
```

- **Practical task benefit:** prevents a sample copied into a multithreaded AnimBP from racing on game objects; it preserves parallel evaluation while making the data handoff explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Animation/AnimInstance.h:1437-1444` (`UAnimInstance::NativeUpdateAnimation` and `NativeThreadSafeUpdateAnimation`) explicitly directs gathering data in the former and identifies the latter as a worker-thread hook; `.../AnimInstance.h:1436-1457` also verifies the lifecycle overrides. The installed 5.8.2 `UAnimInstance` declaration is the API authority. The matching Epic [Animation Blueprints](https://dev.epicgames.com/documentation/unreal-engine/animation-blueprints-in-unreal-engine) guidance is the documentation reference.

#### ANIM-02 — do not imply every Pose Search path is production-ready

- **Priority:** P2 — expectation management; the current wording can cause agents to present newly added 5.8 experimental APIs as a stable baseline.
- **Locations:** `references/motion-matching-and-warping.md:17-18` and `references/motion-matching-and-warping.md:126-132`.
- **Finding:** the general Pose Search plugin can remain a supported option, but UE 5.8 release notes explicitly mark the new `UPoseSearchInteractionLibrary::MotionMatchMulti` as **Experimental**. The reference should separate the stable plugin/node guidance from any new experimental multi-character API instead of allowing a blanket “production-ready” reading.
- **Exact proposed replacement:**

```diff
--- a/skills/core/animation-system/references/motion-matching-and-warping.md
+++ b/skills/core/animation-system/references/motion-matching-and-warping.md
@@
-The Pose Search plugin ships with UE 5.8 and is production-ready (stabilized in 5.4).
-Enable it in Edit → Plugins → Animation → Pose Search.
+The Pose Search plugin ships with UE 5.8 and its core database/schema and Motion Matching
+AnimGraph workflow are suitable for production evaluation; validate the exact node and
+database workflow against the target project. Enable it in Edit → Plugins → Animation →
+Pose Search. Do not generalize that stability claim to APIs explicitly labeled Experimental
+in the UE 5.8 release notes.
@@
 ## Chooser (Dynamic Asset Selection)
@@
 The **Chooser** system (`Dynamic Asset Selection` doc page) lets designers build lookup
 tables that select animation assets at runtime based on `FGameplayTag` context, character
 state, or other parameters. The `FChooserTable` evaluates a decision tree of conditions and
 returns an animation (or montage, or blend space). This is a lighter-weight alternative to
 a full Motion Matching database for deterministic asset selection.
+
+UE 5.8 also adds `UPoseSearchInteractionLibrary::MotionMatchMulti`, but the release notes
+label it **Experimental**. Treat it as an opt-in experiment, not as the default production
+multi-character integration.
```

- **Practical task benefit:** keeps agents from silently promoting an experimental 5.8 API while retaining the useful stable Pose Search recommendation.
- **Verified evidence:** the UE 5.8 release notes’ Pose Search section, lines 3311-3329 of the fetched notes, labels `UPoseSearchInteractionLibrary::MotionMatchMulti` “Experimental”; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Animation/PoseSearch/Source/Runtime/Public/PoseSearch/PoseSearchLibrary.h:56-66,141-194` verifies `FMotionMatchingState` and `UPoseSearchLibrary` in UE 5.8.2. The matching Epic [Motion Matching](https://dev.epicgames.com/documentation/unreal-engine/motion-matching-in-unreal-engine) page is the official topic.

### No-change checks

- `UAnimInstance` lifecycle hooks, montage play/stop/section APIs, `FOnMontageEndedMCDelegate`, `FOnMontageEnded`, notify signatures, linked anim layers, state-machine queries, root-motion properties, Motion Warping, and Pose Search library paths were checked against the installed 5.8.2 source. The API names and module locations in the skill are present.
- The 5.8.1 notes’ animation fixes and the 5.8.2 notes’ animation/Control Rig/Sequencer fixes were checked; they are hotfix corrections, not a migration requiring changes to the core animation workflow here. The 5.8 notes’ montage, animation-thread, and Pose Search material was considered; no unsupported beta claim was added to the baseline.
- No deprecation in the checked 5.8 Upgrade Notes requires replacing the documented `LinkAnimClassLayers`, `MotionWarpingComponent`, montage, or notify APIs. The reference correctly keeps older layer-overlay names as historical context.

### Unresolved questions / verification gaps

- No multi-character animation stress test or thread sanitizer run was performed; ANIM-01 is a source-grounded safety correction, not a runtime proof of every engine-thread interaction.
- Pose Search “production” suitability is not a guarantee for a particular database, schema, platform, or content set; the proposed wording intentionally avoids a blanket certification.
- No project-specific Animation Budget Allocator or Animation Sharing configuration was available, so their performance tradeoffs were not independently measured.

---

## core/asset-management

**Status:** findings  
**Repository path:** `skills/core/asset-management/`  
**Files reviewed:** `SKILL.md`; `references/asset-manager-and-bundles.md`; `references/asset-registry.md`; `references/streamable-manager.md`.

### Verified recommendations

#### ASSET-01 — correct the `FAssetData::TagsAndValues` type and access model

- **Priority:** P2 — compile/API accuracy; agents copying the type table may try to treat cooked asset tags as a mutable `TMap`.
- **Location:** `references/asset-registry.md:30-41`, specifically the `TagsAndValues` row at line 38 and the immediately following access paragraph.
- **Finding:** In the installed UE 5.8.2 source, the public representation used by `FAssetData` is `FAssetDataTagMapSharedView`. It supports `FindTag`, `Contains`, `ContainsKeyValue`, `Num`, `ForEach`, and `CopyMap`; the old `TMap<FName,FString>` description is not the actual field type and hides that cooked fixed tag values are read through a view.
- **Exact proposed replacement:**

```diff
--- a/skills/core/asset-management/references/asset-registry.md
+++ b/skills/core/asset-management/references/asset-registry.md
@@
-| `TagsAndValues` | `TMap<FName,FString>` | searchable UPROPERTY values |
+| `TagsAndValues` | `FAssetDataTagMapSharedView` | searchable UPROPERTY values; use `FindTag`, `Contains`, `ForEach`, or `CopyMap` |
@@
-Convert to a loaded object with `AssetData.GetAsset()` (triggers a load) or check if already
-loaded with `AssetData.IsAssetLoaded()`.
+Read tags through the view without loading the asset:
+```cpp
+if (AssetData.TagsAndValues.ContainsKeyValue(FName("WeaponType"), TEXT("Rifle")))
+{
+    // matched a searchable tag
+}
+```
+Convert to a loaded object with `AssetData.GetAsset()` (triggers a load) or check if already
+loaded with `AssetData.IsAssetLoaded()`. Use `AssetData.TagsAndValues.CopyMap()` only when a
+loose `FAssetDataTagMap` copy is actually needed.
```

- **Practical task benefit:** avoids a misleading container assumption in registry filters and makes the no-load tag-query path explicit for cooked and editor registries.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/AssetRegistry/AssetData.h:226-232` declares `FAssetData::TagsAndValues` as `FAssetDataTagMapSharedView`; `.../AssetRegistry/AssetDataTagMap.h:302-388` declares the view and its `FindTag`, `ContainsKeyValue`, `Contains`, `Num`, `CopyMap`, and `ForEach` APIs. UE 5.8.2 source. The matching Epic [Asset Registry](https://dev.epicgames.com/documentation/unreal-engine/asset-registry-in-unreal-engine) topic is the official documentation reference.

### No-change checks

- Hard/soft reference semantics, `TObjectPtr`/`TSoftObjectPtr`/`TSoftClassPtr`, streamable handles, `UAssetManager` primary assets and bundles, `FPrimaryAssetId`, `ScanPathsForPrimaryAssets`, dependency queries, and `GetClassPathName()` were checked against UE 5.8.2 declarations. The APIs and module names in the snippets are present.
- UE 5.8 release notes’ Asset Registry section adds memory-mapped tag storage and the Streamable Manager section adds opt-in just-in-time/trickled async loading. These are implementation/opt-in tuning details, not a reason to rewrite the baseline workflow; the existing reference already warns to measure streaming behavior.
- The 5.8.1 and 5.8.2 hotfix notes were checked for asset registry, streaming, Asset Manager, or soft-reference migrations. No conflicting public API change or required upgrade step was found. No beta/experimental claim is made by this skill.

### Unresolved questions / verification gaps

- No cooked `AssetRegistry.bin` was inspected and no async-load/cook size benchmark was run; the tag-map correction is declaration-grounded, not a performance measurement.
- The report does not certify that every documented virtual path resolves in a particular project or plugin; no project content registry was available.
- The UE 5.8 docs pages were checked by topic URL; no separate project-specific Asset Manager configuration was available to validate bundle discovery settings.

---

## core/audio-and-metasounds

**Status:** findings  
**Repository path:** `skills/core/audio-and-metasounds/`  
**Files reviewed:** `SKILL.md`; `references/attenuation-and-spatialization.md`; `references/audiocomponent-and-playback.md`; `references/metasound-parameters-and-builder.md`; `references/mixing-classes-submixes-concurrency.md`.

### Verified recommendations

#### AUDIO-01 — allow direct `USoundWave` playback and correct the absolute claim

- **Priority:** P2 — guidance accuracy; the current “never” wording needlessly rules out a valid engine path.
- **Location:** `SKILL.md:41-43`.
- **Finding:** `USoundWave` derives from `USoundBase`, and the public `PlaySound2D`/`PlaySoundAtLocation` APIs accept `USoundBase*`. A wave can therefore be played directly. MetaSounds and SoundCues remain the right recommendation when composition, variation, or parameter control is needed, but direct wave playback is not invalid.
- **Exact proposed replacement:**

```diff
--- a/skills/core/audio-and-metasounds/SKILL.md
+++ b/skills/core/audio-and-metasounds/SKILL.md
@@
 Prefer **MetaSounds** for new dynamic audio. SoundCues remain fully supported and are
 simpler for lightweight randomization. `USoundWave` is never played directly in gameplay
 code — it is the leaf asset referenced inside cues or MetaSound graphs.
+Prefer **MetaSounds** for new dynamic audio. SoundCues remain fully supported and are
+simpler for lightweight randomization. `USoundWave` is also a valid direct `USoundBase`
+input to `PlaySound2D`, `PlaySoundAtLocation`, or an audio component; use a Cue or MetaSound
+when you need composition, variation, or parameterized DSP.
```

- **Practical task benefit:** agents can choose the smallest valid playback path for a simple wave without losing the modern-graph recommendation for dynamic audio.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Sound/SoundWave.h:421` declares `USoundWave : public USoundBase`; `.../Engine/Classes/Kismet/GameplayStatics.h:680,732-736` declares playback functions taking `USoundBase*`. UE 5.8.2 source. The matching Epic [Working with Audio](https://dev.epicgames.com/documentation/unreal-engine/working-with-audio-in-unreal-engine) topic is the official reference.

#### AUDIO-02 — replace the nonexistent `UGameplayStatics::AddSoundToMix` call

- **Priority:** P1 — compile correctness; the cited function does not exist in the installed UE 5.8.2 source, so copying the submix-effect recipe fails.
- **Location:** `references/mixing-classes-submixes-concurrency.md:62-70`.
- **Finding:** submix effects are added through `UAudioMixerBlueprintLibrary::AddSubmixEffect` (preset path) or the `FMixerDevice::AddSubmixEffect` lower-level API. `UGameplayStatics::AddSoundToMix` was not found in the engine source. Sound Mix push/pop is a separate class-mix operation and should not be substituted for a submix DSP effect.
- **Exact proposed replacement:**

```diff
--- a/skills/core/audio-and-metasounds/references/mixing-classes-submixes-concurrency.md
+++ b/skills/core/audio-and-metasounds/references/mixing-classes-submixes-concurrency.md
@@
 1. Create a `USoundEffectSubmixPreset` subclass (e.g., built-in
    `USubmixEffectReverbPreset`, `USubmixEffectEQPreset`).
 2. Drag it onto the submix in the editor, or add it via
-   `UGameplayStatics::AddSoundToMix` from code.
+   `UAudioMixerBlueprintLibrary::AddSubmixEffect(WorldContextObject, SoundSubmix, Preset)`
+   from code (`AudioMixerBlueprintLibrary.h`).
 3. Effects run in serial order in the chain.
```

- **Practical task benefit:** turns a non-compiling example into the actual UE 5.8.2 runtime API and keeps Sound Mix and Submix responsibilities distinct.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/AudioMixer/Public/AudioMixerBlueprintLibrary.h:238-240` declares `UAudioMixerBlueprintLibrary::AddSubmixEffect`; `.../AudioMixer/Private/AudioMixerBlueprintLibrary.cpp:127-144` implements it. A source search under `.../Engine/Source` found no `AddSoundToMix` symbol. UE 5.8.2 source. Official topic: [Submixes](https://dev.epicgames.com/documentation/unreal-engine/submixes-in-unreal-engine).

#### AUDIO-03 — describe the actual MetaSound output return type

- **Priority:** P1 — API accuracy; the main skill describes a `UMetasoundGeneratorHandle` as if it were returned by the C++ API, while the installed declaration returns a weak pointer to the generator.
- **Location:** `SKILL.md:152-154`.
- **Finding:** `UMetaSoundSource::GetGeneratorForAudioComponent` returns `TWeakPtr<Metasound::FMetasoundGenerator>`. The Blueprint `UMetasoundGeneratorHandle` is a separate wrapper. The deeper reference already demonstrates the correct `WeakPtr.Pin()` pattern; the top-level wording should match it rather than implying a direct handle return.
- **Exact proposed replacement:**

```diff
--- a/skills/core/audio-and-metasounds/SKILL.md
+++ b/skills/core/audio-and-metasounds/SKILL.md
@@
-MetaSounds also expose **outputs** (e.g., a float metering value). Read them
-through `UMetasoundGeneratorHandle` obtained from `UMetaSoundSource::
-GetGeneratorForAudioComponent` — available only while the sound is playing.
+MetaSounds also expose **outputs** (e.g., a float metering value). In C++,
+`UMetaSoundSource::GetGeneratorForAudioComponent` returns a
+`TWeakPtr<Metasound::FMetasoundGenerator>`; pin and validate it only while the sound
+is playing. The Blueprint `UMetasoundGeneratorHandle` is a separate wrapper for
+Blueprint-facing output access.
```

- **Practical task benefit:** prevents a C++ caller from using the wrong return type and directs it to handle generator lifetime safely.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/Metasound/Source/MetasoundEngine/Public/MetasoundSource.h:326` declares `UMetaSoundSource::GetGeneratorForAudioComponent` as `TWeakPtr<Metasound::FMetasoundGenerator>`; lines 338-343 separately declare generator-instance delegates. UE 5.8.2 source. Official topic: [MetaSounds](https://dev.epicgames.com/documentation/unreal-engine/metasounds-in-unreal-engine).

### No-change checks

- `UAudioComponent` playback and parameter setters, `USoundBase` attenuation/concurrency/virtualization properties, Quartz clock creation and `PlayQuantized`, MetaSound Builder entry points, Audio Modulation, and the attenuation fields were checked against UE 5.8.2 source. The named declarations and owning modules exist except for the one removed call above.
- UE 5.8 release notes add MetaSound Node Configuration (Experimental) and MetaSound Templates (Experimental). The skill’s Builder API is already honestly labeled Beta; the new editor-focused experimental features are not silently presented as runtime production APIs, so no speculative expansion is recommended.
- The 5.8.1 and 5.8.2 hotfix notes were checked for audio, MetaSound, Quartz, attenuation, and concurrency changes. They contain fixes but no required migration to the existing playback or parameter APIs. The 5.8.2 known issue is unrelated to this skill.

### Unresolved questions / verification gaps

- No audio-device playback, virtualization, or MetaSound generator lifetime test was run; these findings are source/API corrections, not audio-output validation.
- HRTF, Audio Gameplay Volumes, Audio Modulation, and MetaSound Builder behavior depend on enabled plugins and project settings that were not inspected in a project.
- The release-note classification of MetaSound Templates and Node Configuration is verified as Experimental, but no recommendation is made about adoption without a project’s audio authoring needs.

---

## core/automation-and-testing

**Status:** findings  
**Repository path:** `skills/core/automation-and-testing/`  
**Files reviewed:** `SKILL.md`; `references/flags-and-ci.md`; `references/functional-tests.md`; `references/low-level-tests.md`; `references/spec-and-latent-commands.md`.

### Verified recommendations

#### TEST-01 — replace the removed functional-test cleanup helper

- **Priority:** P1 — compile correctness; copying the current cleanup instruction calls a symbol that is absent from UE 5.8.2.
- **Locations:** `SKILL.md:200`; `references/functional-tests.md` cleanup section (the `AddActorToDestroyOnTestEnd` example).
- **Finding:** UE 5.8.2 exposes `AFunctionalTest::RegisterAutoDestroyActor(AActor*)`; no `AddActorToDestroyOnTestEnd` declaration or definition was found under `Engine/Source`. The sample should use the actual method and keep the lifetime caveat: registration limits the actor’s lifespan when the test finishes.
- **Exact proposed replacement:**

```diff
--- a/skills/core/automation-and-testing/SKILL.md
+++ b/skills/core/automation-and-testing/SKILL.md
@@
-- Register spawned actors with `AddActorToDestroyOnTestEnd` so cleanup is automatic.
+- Register spawned actors with `RegisterAutoDestroyActor(Actor)` so the functional test
+  limits their lifespan during test cleanup.
--- a/skills/core/automation-and-testing/references/functional-tests.md
+++ b/skills/core/automation-and-testing/references/functional-tests.md
@@
-- Use `AddActorToDestroyOnTestEnd` for spawned actors so every run leaves the level clean.
+- Use `RegisterAutoDestroyActor(Actor)` for spawned actors so every run leaves the level
+  clean. This is `AFunctionalTest::RegisterAutoDestroyActor` in UE 5.8.2.
```

- **Practical task benefit:** turns a non-compiling functional-test cleanup recipe into the current API and prevents test actors leaking into later runs.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Developer/FunctionalTesting/Classes/FunctionalTest.h:390-391` declares the `AutoDestroyActors` array and `:731-734` declares `AFunctionalTest::RegisterAutoDestroyActor`; a source search found no `AddActorToDestroyOnTestEnd`. UE 5.8.2 source. Matching Epic topic: [Functional Testing](https://dev.epicgames.com/documentation/unreal-engine/functional-testing-in-unreal-engine).

#### TEST-02 — stop describing removed assertions as merely deprecated

- **Priority:** P1 — compile correctness; the current gotcha sends agents toward names that are not present in the installed public header.
- **Location:** `SKILL.md:277-279`, the “Gotchas” bullets.
- **Finding:** `AddErrorS`, `AddWarningS`, and `TestEqualInsensitive` were not found in UE 5.8.2 `Runtime/Core/Public/Misc/AutomationTest.h`. The replacement is not a 5.8-specific new API—the existing `AddError`, `AddWarning`, and case-insensitive `TestEqual` overloads are the current calls—but the wording should say unavailable/removed for this target rather than only “deprecated.”
- **Exact proposed replacement:**

```diff
--- a/skills/core/automation-and-testing/SKILL.md
+++ b/skills/core/automation-and-testing/SKILL.md
@@
-- **`AddErrorS` / `AddWarningS`** — deprecated since 5.4; use `AddError` / `AddWarning`.
-- **`TestEqualInsensitive`** — deprecated since 5.5; use `TestEqual` (strings are
-  case-insensitive by default now).
+- **Legacy assertion names** — `AddErrorS`, `AddWarningS`, and `TestEqualInsensitive`
+  are not available in the UE 5.8.2 public automation header. Use `AddError`,
+  `AddWarning`, and `TestEqual` instead; the string overloads of `TestEqual` use
+  case-insensitive comparison by default.
```

- **Practical task benefit:** avoids compile failures and preserves the important case-sensitive escape hatch (`TestEqualSensitive`) for tests that require it.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Private/Misc/AutomationTest.cpp:2161-2192` implements the `TestEqual` string/view overloads with `ESearchCase::IgnoreCase`; `:2293-2323` implements `TestEqualSensitive`; `.../Runtime/Core/Public/Misc/AutomationTest.h` declares `AddError`/`AddWarning` and contains no matches for the three legacy names. UE 5.8.2 source.

#### TEST-03 — retain the CI command recipe, but make the exit-code condition explicit

- **Priority:** P2 — CI reliability; the current line “a non-zero exit code indicates test failures when `-unattended` is set” omits the required quit path and can cause a pipeline to treat a still-running process as a completed test run.
- **Locations:** `SKILL.md:249-264`; `references/flags-and-ci.md:67-112`.
- **Finding:** `Automation RunTest` remains accepted as an alias for `Automation RunTests` in UE 5.8.2, and `+` is the source-supported separator for multiple test names, so those recipes do not need a spelling migration. The process exit status is assigned when the final `Quit`/`SoftQuit` command is processed: the commandlet checks `ReportsHaveErrors()` or command-line errors and then emits `TEST COMPLETE. EXIT CODE` before `RequestExitWithStatus`. Clarify that CI must wait for that completion marker/process exit, and that `-nullrhi` excludes rendering tests.
- **Exact proposed addition:**

```diff
--- a/skills/core/automation-and-testing/SKILL.md
+++ b/skills/core/automation-and-testing/SKILL.md
@@
 Parse the exit code and log for pass/fail in your CI pipeline. A non-zero exit code
-indicates test failures when `-unattended` is set.
+is produced after the queued `Quit` command reaches the completed state and the
+controller reports errors (or a command-line error). Wait for process exit and/or the
+`**** TEST COMPLETE. EXIT CODE: ... ****` marker; `-unattended` only suppresses UI.
--- a/skills/core/automation-and-testing/references/flags-and-ci.md
+++ b/skills/core/automation-and-testing/references/flags-and-ci.md
@@
 Writes JSON and HTML files consumable by the Automation Test Report Server.
+The process exit status is the CI gate only after `Quit`/`SoftQuit` completes; retain the
+log marker as a diagnostic, not as a substitute for waiting on process exit.
```

- **Practical task benefit:** prevents CI from reading a partial report or assuming `-unattended` itself changes test result semantics; it also preserves the valid `RunTest` alias rather than “fixing” a working command.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Developer/AutomationController/Private/AutomationCommandline.cpp:610-611` accepts both `RunTests` and `RunTest`; `:133-134` splits multiple names on `+`; `:493-504` maps reported errors to `RequestExitWithStatus`; `:780-798` lists the supported commands. UE 5.8.2 source. Matching Epic topics: [Run Automation Tests](https://dev.epicgames.com/documentation/unreal-engine/run-automation-tests-in-unreal-engine) and [Automation Test Framework](https://dev.epicgames.com/documentation/unreal-engine/automation-test-framework-in-unreal-engine).

### No-change checks

- `EAutomationTestFlags` values, `EAutomationTestFlags_ApplicationContextMask`, `NegativeFilter`, `SupportsAutoRTFM`, `IMPLEMENT_SIMPLE_AUTOMATION_TEST`, `DEFINE_SPEC`, `LatentIt`, and the `EAsyncExecution` overloads are present in `Runtime/Core/Public/Misc/AutomationTest.h` in UE 5.8.2. The flags reference correctly documents the context/filter distinction and the `+` multi-test separator is source-verified.
- `AFunctionalTest::PrepareTest`, `IsReady_Implementation`, `StartTest`, `FinishTest`, `AssertTrue`, `AssertIsValid`, and `AssertEqual_Float` are present in `Developer/FunctionalTesting/Classes/FunctionalTest.h`; only the cleanup helper name required correction.
- `Developer/LowLevelTestsRunner/Public/TestHarness.h:73-78` includes Catch2 headers and `:121-201` supplies the LLT assertion bridge. The LLT reference’s Catch2 model and `TEST_CASE`/`CHECK` examples match the installed harness. CQTest is present as a separate developer module in the installation, but no project test target was available to validate module setup.
- UE 5.8 release-note test material includes automated-testing navigation-map startup fixes, not a migration of the core automation/spec/functional/LLT APIs. The 5.8.1 and 5.8.2 hotfix notes were checked for automation, functional-test, LLT, and Gauntlet changes; no additional required migration was identified for this skill.

### Unresolved questions / verification gaps

- No project was compiled and no `UnrealEditor-Cmd.exe` automation run was executed; command and API checks are source/declaration-grounded, not end-to-end CI validation.
- The repository’s `AutomationTestGroups` `.ini` example was not matched by a `AutomationTestGroups` symbol in installed engine source. Treat that configuration snippet as unresolved until the target project’s 5.8 docs or settings class confirms it; the report does not recommend adding it.
- No Gauntlet device session, dedicated-server functional test, low-level test target, or report-server upload was run. Vendor/platform-specific CI behavior remains outside this audit.

---

## core/blueprint-cpp-integration

**Status:** findings  
**Repository path:** `skills/core/blueprint-cpp-integration/`  
**Files reviewed:** `SKILL.md`; `references/blueprint-interfaces.md`; `references/ufunction-specifiers.md`; `references/uproperty-specifiers.md`.

### Verified recommendations

#### BP-CPP-01 — remove the misleading pure-node caching claim

- **Priority:** P2 — Blueprint runtime correctness/performance; an agent may assume a pure getter is memoized and put world queries or other expensive work behind it.
- **Locations:** `SKILL.md:44-46`; `references/ufunction-specifiers.md:21-29`.
- **Finding:** The top-level example calls a pure result “cached per evaluation,” while the deep reference correctly warns that Blueprint can re-evaluate a pure node for each connected read. The skill should state the operational rule once: purity removes execution pins; it does not provide application-level memoization.
- **Exact proposed replacement:**

```diff
--- a/skills/core/blueprint-cpp-integration/SKILL.md
+++ b/skills/core/blueprint-cpp-integration/SKILL.md
@@
-// Pure query — no exec pins, result cached per evaluation
+// Pure query — no exec pins; do not assume application-level memoization
 UFUNCTION(BlueprintPure, Category="Combat")
 float GetHealthPercent() const;
--- a/skills/core/blueprint-cpp-integration/references/ufunction-specifiers.md
+++ b/skills/core/blueprint-cpp-integration/references/ufunction-specifiers.md
@@
-Removes exec pins. The node is a data source evaluated on demand. Rules:
+Removes exec pins. The node is a data source evaluated on demand; purity does not create
+application-level memoization. Rules:
```

- **Practical task benefit:** keeps expensive queries out of pure Blueprint functions unless the caller explicitly caches a value, reducing accidental repeated work without changing the C++/UHT contract.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h:1026` defines the `BlueprintPure` function flag; the repository’s own `references/ufunction-specifiers.md:27-29` documents repeated evaluation. UE 5.8.2 source plus the matching Epic [UFunctions](https://dev.epicgames.com/documentation/unreal-engine/ufunctions-in-unreal-engine) topic. The exact number of calls remains graph/compiler dependent, so the replacement deliberately avoids a stronger execution-count claim.

#### BP-CPP-02 — keep interface dispatch and private-property rules explicit

- **Priority:** P1 — compile/runtime correctness; these are the two boundary mistakes most likely to break copied examples: calling a Blueprint interface through the native vtable, or exposing a private field without the required metadata.
- **Locations:** `SKILL.md:209-219`, `SKILL.md:242-250`; `references/blueprint-interfaces.md:105-150`; `references/uproperty-specifiers.md:65-72`.
- **Finding:** No UE 5.8.2 migration is needed, but the current guidance is worth retaining verbatim in any approved upgrade: test `Implements<>` and dispatch through generated `Execute_<FuncName>` for Blueprint-capable interface events; use `AllowPrivateAccess="true"` for private Blueprint-readable properties. Do not collapse these into a generic `Cast<>` or “private is fine” rule.
- **Exact proposed addition:**

```diff
--- a/skills/core/blueprint-cpp-integration/SKILL.md
+++ b/skills/core/blueprint-cpp-integration/SKILL.md
@@
 Use `Execute_<FuncName>` for any `BlueprintNativeEvent`/`BlueprintImplementableEvent` on an
 interface — it is the only path that correctly dispatches to Blueprint overrides.
+For a private `UPROPERTY` exposed to Blueprint, keep `meta=(AllowPrivateAccess="true")` on
+the property; this metadata changes UHT access validation, not C++ visibility.
```

- **Practical task benefit:** preserves the source-verified rules at the point where agents are most likely to copy a declaration or call site; no new abstraction or feature is introduced.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/UObject/Interface.h:18-40` declares the `UInterface`/`IInterface` base pair, and `.../CoreUObject/Public/UObject/ObjectMacros.h:1351` declares `AllowPrivateAccess`; generated `Execute_` dispatch is produced for interface events by UHT. UE 5.8.2 source. Matching Epic topics: [Interfaces](https://dev.epicgames.com/documentation/unreal-engine/interfaces-in-unreal-engine) and [Metadata Specifiers](https://dev.epicgames.com/documentation/unreal-engine/metadata-specifiers-in-unreal-engine).

### No-change checks

- `BlueprintCallable`, `BlueprintPure`, `BlueprintImplementableEvent`, `BlueprintNativeEvent`, `CallInEditor`, `BlueprintAuthorityOnly`, `BlueprintCosmetic`, and the documented UFUNCTION metadata names are present in `Runtime/CoreUObject/Public/UObject/ObjectMacros.h` in UE 5.8.2.
- `EditAnywhere`, `EditDefaultsOnly`, `EditInstanceOnly`, the visible-property family, `BlueprintReadOnly`, `BlueprintReadWrite`, `BlueprintGetter`, `BlueprintSetter`, and `BlueprintAssignable` are present in the installed `UP` enum. `ExposeOnSpawn`, `AllowPrivateAccess`, `EditCondition`, range, picker, and display metadata remain valid; no 5.8 replacement is warranted.
- `UBlueprintFunctionLibrary`, `TSubclassOf`, `TSoftObjectPtr`, `TSoftClassPtr`, `UINTERFACE`, `TScriptInterface`, and interface `Execute_` rules in the four reviewed files map to the UE 5.8.2 headers. The `Cast<>` caveat is intentionally preserved for Blueprint-only interface implementations.
- UE 5.8 release notes contain Blueprint compiler/editor fixes and new editor features, but no 5.8 UFUNCTION/UPROPERTY/UINTERFACE syntax migration applicable to these examples. The 5.8.1 hotfix’s Blueprint compiler reentrancy fix and the 5.8.2 hotfix’s Blueprint attachment-hierarchy fix are corrective engine changes, not new boundary syntax. Sources: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project Blueprint was compiled in UE 5.8.2, so generated-node display, custom getter/setter UHT diagnostics, and interface dispatch were not end-to-end tested.
- The report does not assert that every listed metadata tag has identical editor UX in every 5.8.2 asset type; editor customization and plugin metadata remain project-specific.
- No project-specific Blueprint compiler settings, nativization/build target, or vendor plugin interface was available for validation.

---

## core/blueprint-fundamentals

**Status:** findings  
**Repository path:** `skills/core/blueprint-fundamentals/`  
**Files reviewed:** `SKILL.md`; `references/blueprint-class-and-generated-class.md`; `references/cpp-blueprint-boundary.md`; `references/graphs-variables-and-components.md`.

### Verified recommendations

#### BP-FUND-01 — correct the Blueprint tick-default statement

- **Priority:** P1 — performance/debugging correctness; the current rule can make an agent hunt for a Blueprint-only default that is not the engine default and can lead to unnecessary per-frame work.
- **Location:** `SKILL.md:203-205`.
- **Finding:** UE 5.8.2 initializes `AActor::PrimaryActorTick.bCanEverTick` to `false`. A Blueprint based directly on `AActor` can be enabled for ticking when it contains a non-empty `Event Tick` because the Kismet compiler treats `AActor` as a universal parent; a native parent can additionally opt in with `meta=(ChildCanTick)` or project engine settings. It is not correct to say all Blueprint actors have ticking enabled by default while C++ actors do not.
- **Exact proposed replacement:**

```diff
--- a/skills/core/blueprint-fundamentals/SKILL.md
+++ b/skills/core/blueprint-fundamentals/SKILL.md
@@
-- **Tick left on by default** — Blueprint actors have `bCanEverTick = true` by default (unlike
-  C++ actors where you opt in). Disable it in Class Defaults for actors that don't need per-frame
-  work.
+- **Tick is opt-in** — `AActor::PrimaryActorTick.bCanEverTick` defaults to `false` in UE 5.8.2.
+  A non-empty Blueprint `Event Tick` can cause the Kismet compiler to enable ticking for a
+  Blueprint based directly on `AActor`; native parent classes and project settings can change
+  the eligibility. Remove unused Event Tick graphs and disable ticking for actors that do not
+  need per-frame work.
```

- **Practical task benefit:** avoids both false alarms (“every Blueprint ticks”) and missed performance work (an actual Event Tick graph can opt a Blueprint into ticking).
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/Actor.cpp:274-282` (`AActor::InitializeDefaults`) sets `bCanEverTick = false`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/KismetCompiler/Private/KismetCompiler.cpp:5504-5608` (`FKismetCompilerContext::SetCanEverTick`) explains the Blueprint Event Tick/compiler and `bCanBlueprintsTickByDefault` conditions. UE 5.8.2 source. Matching Epic topic: [Blueprint Best Practices](https://dev.epicgames.com/documentation/unreal-engine/blueprint-best-practices-in-unreal-engine).

#### BP-FUND-02 — qualify Construction Script world and gameplay side effects

- **Priority:** P1 — editor/runtime correctness; the current “don't work there” absolute can hide valid guarded construction-time setup while failing to warn that editor reruns must be idempotent.
- **Locations:** `SKILL.md:206-207`; `references/graphs-variables-and-components.md:39-57`.
- **Finding:** `AActor::ExecuteConstruction` does run the Construction Script/`OnConstruction` path for actor construction, and the reference itself lists procedural setup and child spawning as valid uses. The gotcha should distinguish construction-time execution from gameplay: world queries and spawning are possible in an appropriate construction world, but gameplay-only calls, transient side effects, and unguarded persistent mutations are unsafe because editor property changes rerun the script.
- **Exact proposed replacement:**

```diff
--- a/skills/core/blueprint-fundamentals/SKILL.md
+++ b/skills/core/blueprint-fundamentals/SKILL.md
@@
-- **Construction Script runs in editor** — world queries, spawning, and gameplay calls don't work
-  there. Only use idempotent setup (set component properties, adjust scale, assign materials).
+- **Construction Script runs in editor and at construction time** — it may run in an editor
+  preview world as well as during spawn. Keep setup idempotent; guard or avoid gameplay-only
+  side effects, and clean up anything the script creates before a rerun. World queries and
+  construction-time child spawning are valid only when their world/context and editor behavior
+  are explicitly handled.
--- a/skills/core/blueprint-fundamentals/references/graphs-variables-and-components.md
+++ b/skills/core/blueprint-fundamentals/references/graphs-variables-and-components.md
@@
-This makes the Construction Script the right place for procedural setup that depends on
-properties — layout-sensitive component configuration, runtime parameter setup, spawning child
-actors. It must be **idempotent** because it can run many times (each property edit triggers a
-re-run). Never rely on persistent state accumulated across multiple Construction Script runs.
+This makes the Construction Script the right place for idempotent procedural setup that depends
+on properties — layout-sensitive component configuration, construction-time parameter setup,
+and carefully managed child actors. It can run many times (each property edit may trigger a
+re-run), so clean up or replace anything it creates and never rely on persistent state accumulated
+across runs. Guard gameplay-only work and world-dependent queries for the execution context.
```

- **Practical task benefit:** preserves useful construction-time workflows without encouraging duplicate actors, editor-only gameplay side effects, or scripts that break when a property is edited.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h:3439-3445` declares `ExecuteConstruction` and `OnConstruction`; the source implementation invokes construction in the actor lifecycle. The reviewed reference’s `USimpleConstructionScript::ExecuteScriptOnActor` path remains valid. UE 5.8.2 source. Matching Epic topic: [Construction Script](https://dev.epicgames.com/documentation/unreal-engine/construction-script-in-unreal-engine).

### No-change checks

- `UBlueprint`, `UBlueprintCore`, `UBlueprintGeneratedClass`, `EBlueprintType`, `USimpleConstructionScript`, `UCS_Node`, `FPointerToUberGraphFrame`, timeline storage, graph categories, `TSubclassOf`, `TObjectPtr`, and Blueprint/C++ boundary examples map to the installed UE 5.8.2 declarations.
- The two-object explanation is correct for cooked runtime content, while editor/PIE can hold the editor asset and generated class together. No class-layout migration is recommended; line references should remain search anchors rather than hard contracts.
- Event graph, function, macro, interface, local-variable, SCS/native-component, Construction Script, CDO, recompile, and binary-asset merge guidance was checked against the four files and matching Epic Blueprint/compiler/construction topics. No additional 5.8 API rewrite is supported by the source.
- UE 5.8 release notes include Blueprint compiler/editor improvements and 5.8.2 fixes a World Partition Blueprint attachment-hierarchy failure; these do not change the core generated-class, graph, or SCS authoring model. The 5.8.1 compiler reentrancy fix and 5.8.2 fix are recorded as hotfix context, not as a new skill feature. Sources: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No Blueprint asset was opened, compiled, reinstanced, or run in PIE/cooked mode during this audit; compiler behavior was inspected in source only.
- The exact effective Blueprint tick default also depends on project `bCanBlueprintsTickByDefault`, native parent metadata, and whether an Event Tick graph is non-empty; those project settings were not available.
- Construction Script behavior with editor transactions, spawned construction actors, and World Partition was not runtime-tested. The report does not certify arbitrary editor-side spawning as safe.

---

## core/character-and-movement

**Status:** findings  
**Repository path:** `skills/core/character-and-movement/`  
**Files reviewed:** `SKILL.md`; `references/movement-modes-and-custom.md`; `references/networked-movement.md`; `references/root-motion-and-launch.md`.

### Verified recommendations

#### CHAR-MOVE-01 — add the UE 5.8 movement-base migration warning

- **Priority:** P1 — upgrade/compile correctness for CMC extensions; UE 5.8 deprecates movement-base APIs that take `UPrimitiveComponent*` and introduces `FMovementBaseInterfaceData`.
- **Locations:** precise insertion point after `SKILL.md:247` (`ReplicatedMovementMode` bullet) and after `references/networked-movement.md:187` in its Version notes.
- **Finding:** The skill explains prediction and custom saved moves but omits the 5.8 movement-base conversion. Code extending `UCharacterMovementComponent` or handling `FBasedMovementInfo`, `SetBase`, `RevertMove`, `GetLastServerMovementBase`, or the old `MovementBaseUtility` overloads must migrate to the UObject/interface-data path rather than treating the old `UPrimitiveComponent*` APIs as the long-term contract.
- **Exact proposed addition:**

```diff
--- a/skills/core/character-and-movement/SKILL.md
+++ b/skills/core/character-and-movement/SKILL.md
@@
 - `ReplicatedMovementMode` (`Character.h:703`) replicates the enum to simulated
   proxies so they can transition physics locally.
+- **UE 5.8 movement-base migration:** movement-base APIs that take
+  `UPrimitiveComponent*` are deprecated. For CMC extensions and code handling
+  `FBasedMovementInfo`, use `FMovementBaseInterfaceData` and its
+  `PhysicsObjectOwner`/`IPhysicsBodyInstanceOwner` path. A primitive component can
+  still seed the new struct, but do not add new code against the deprecated overloads.
+  See `ACharacter::OnRep_ReplicatedBasedMovement()` for Epic's conversion pattern.
--- a/skills/core/character-and-movement/references/networked-movement.md
+++ b/skills/core/character-and-movement/references/networked-movement.md
@@
 - The prediction RPC pair changed from `ServerMove`/`ClientAdjustPosition` to
   `ServerMovePacked`/`ClientMoveResponsePacked` for bandwidth efficiency. The old
   names are `DEPRECATED_CHARACTER_MOVEMENT_RPC`-marked in 5.8 (`CMC.h:2635`).
   Existing code using the old names still compiles but should migrate.
+- UE 5.8 also converts movement bases from a `UPrimitiveComponent*` contract to
+  `FMovementBaseInterfaceData`. `SetBase(UPrimitiveComponent*)`, old
+  `MovementBaseUtility` overloads, and related `FBasedMovementInfo`/CMC extension
+  paths are deprecated with fixups. Use `MovementBaseInterface.h`, populate the
+  struct from the owning `UObject`, and follow `ACharacter::OnRep_ReplicatedBasedMovement()`
+  when custom networking code needs the new representation.
```

- **Practical task benefit:** catches a real 5.8 source-compatibility seam before a custom movement component accumulates deprecation warnings or fails when deprecated fixups are removed; it also permits non-primitive movement bases.
- **Verified evidence:** UE 5.8 release notes [Character and Movement Base Upgrade Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#characterandmovementbasenotes), fetched release-note lines 6903-6913, explicitly describe `FMovementBaseInterfaceData` replacing `UPrimitiveComponent` and identify `ACharacter`, `UCharacterMovementComponent`, `FBasedMovementInfo`, `FCharacterNetworkMoveData`, `FClientAdjustment`, and `MovementBaseUtility`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Interfaces/MovementBaseInterface.h:11-71` declares `FMovementBaseInterfaceData`; `.../GameFramework/CharacterMovementComponent.h:904-910, 1608-1614, 1854-1861, 2420-2424` shows deprecated and replacement APIs; `.../GameFramework/Character.h:89-96, 146-202` shows the deprecated movement-base field/utilities and new owner representation. UE 5.8.2 source.

#### CHAR-MOVE-02 — keep Mover’s status and 5.8 capabilities scoped

- **Priority:** P2 — architectural decision quality; the current skill correctly calls Mover experimental but does not point to the concrete 5.8 changes that may justify an evaluation.
- **Locations:** `SKILL.md:270-288`; `references/networked-movement.md:149-164`.
- **Finding:** UE 5.8 release notes describe Mover as continuing work toward leaving Experimental status, so the existing Experimental label must remain. A concise 5.8 note can mention scheduled layered moves, expanded rollback/prediction, optional Iris support in Network Prediction, and non-capsule movement support as evaluation criteria without presenting them as a CMC replacement or a production guarantee.
- **Exact proposed addition:**

```diff
--- a/skills/core/character-and-movement/SKILL.md
+++ b/skills/core/character-and-movement/SKILL.md
@@
 APIs, data formats, and properties are still subject to breaking changes.
+UE 5.8 adds practical evaluation points—scheduled layered moves, expanded rollback/prediction,
+optional Iris support through Network Prediction, and broader non-capsule movement support—
+but Epic still describes the work as moving Mover toward leaving **Experimental** status.
+Keep CMC for established character code unless the project can test Mover's plugin, networking,
+and content compatibility.
```

- **Practical task benefit:** gives teams a bounded reason to evaluate Mover while preventing a premature migration from the stable CMC path.
- **Verified evidence:** UE 5.8 release notes [Mover](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#mover) state the Experimental-status direction and list rollback/prediction, scheduled layered moves, optional Iris support, and non-capsule improvements; installed plugin source under `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/` contains `UMoverComponent` and movement-mode APIs. UE 5.8.2 source.

### No-change checks

- `ACharacter`, `UCharacterMovementComponent`, `UMovementComponent`, input accumulation/consumption, built-in movement modes, `PhysCustom`, `SetMovementMode`, movement-mode delegates, CMC prediction, `FSavedMove_Character`, compressed flags, network smoothing, root motion sources, `LaunchCharacter`, and custom gravity names remain present in UE 5.8.2.
- `ServerMovePacked`/`ClientMoveResponsePacked` are still the preferred packed RPC path and the repository’s deprecation note is directionally correct. `RunTest`-style old names are not involved in this skill.
- Root-motion source IDs, `ApplyRootMotionSource`, `RemoveRootMotionSource`, montage root motion, `RepRootMotion`, custom-gravity caveats, plane constraints, crouch prerequisites, rotation-mode warnings, and SpringArm attachment guidance were checked against the four files and installed headers. No additional source-backed rewrite was warranted.
- The 5.8.1 and 5.8.2 hotfix notes were checked for character movement, Mover, root motion, and networked movement. The 5.8.2 release-note fixes are corrective (including Mover/MetaHuman interactions), not a further required migration of the CMC examples. Sources: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No custom CMC or Mover module was compiled, and no client/server movement replay, moving-base, root-motion, or correction test was run. The migration is release-note/header verified, not runtime validated.
- The exact conversion of project-specific `FBasedMovementInfo` serialization and custom `FCharacterNetworkMoveData` depends on the project’s extension points; Epic's `OnRep_ReplicatedBasedMovement()` is a pattern, not a drop-in adapter for every subclass.
- Mover backend, Iris enablement, non-capsule shape constraints, and performance require a project map/content test. No plugin/vendor project was entered.

---

## core/coding-standards

**Status:** findings  
**Repository path:** `skills/core/coding-standards/`  
**Files reviewed:** `SKILL.md`; `references/formatting-and-includes.md`; `references/naming-conventions.md`; `references/reflection-and-uht.md`.

### Verified recommendations

#### CODING-01 — qualify `check` and `ensure` by build configuration

- **Priority:** P1 — safety/debugging correctness; the current wording can make an agent rely on an assertion that is compiled out in shipping or put side effects in an expression that is not always evaluated.
- **Locations:** `SKILL.md:209-215`; `references/reflection-and-uht.md:185-195` (the UHT/common-gotchas cross-reference should be consistent with the main error guidance).
- **Finding:** The main skill says `check` “aborts in all builds” and `ensure` fires in non-shipping builds. In UE 5.8.2, `check` is defined under `#if DO_CHECK`, and the header explicitly says `check` expressions are evaluated only when enabled while `verify` expressions are always evaluated. State the build-gated behavior and keep the no-side-effects rule.
- **Exact proposed replacement:**

```diff
--- a/skills/core/coding-standards/SKILL.md
+++ b/skills/core/coding-standards/SKILL.md
@@
-- `check(Condition)` for invariants — aborts in all builds if violated. Never put side effects
-  inside a `check`.
-- `ensure(Condition)` for recoverable "shouldn't happen" — fires once in non-shipping builds,
-  returns bool so you can handle the failure.
+- `check(Condition)` for invariants — when `DO_CHECK` is enabled, a failure reports and
+  aborts. It can compile out in shipping/configurations with checks disabled, and the
+  expression is not evaluated when disabled. Never put side effects inside a `check`.
+- `ensure(Condition)` for recoverable "shouldn't happen" — build configuration controls
+  whether ensure handling is enabled; it reports a failure and returns a boolean when enabled.
+  Handle the false result, and do not use it as a shipping-only data-validation boundary.
--- a/skills/core/coding-standards/references/formatting-and-includes.md
+++ b/skills/core/coding-standards/references/formatting-and-includes.md
@@
 ## Source material
@@
 - `Runtime/Core/Public/Windows/WindowsPlatform.h`:209–210 — `DLLEXPORT`/`DLLIMPORT` definition.
+- `Runtime/Core/Public/Misc/AssertionMacros.h`:175–177, 221–230 — `check` expressions
+  are build-gated and are only evaluated when enabled; use `verify` when an expression must
+  always be evaluated.
```

- **Practical task benefit:** prevents shipping-only behavior changes and avoids the classic `check(DoWork())` side-effect bug; it gives reviewers a precise reason to prefer explicit validation for trust-boundary inputs.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Misc/AssertionMacros.h:175-177` documents evaluation semantics and `:221-230` defines `check` only under `DO_CHECK`; `:108-119` declares ensure failure handling. UE 5.8.2 source. Matching Epic topic: [Assertions](https://dev.epicgames.com/documentation/unreal-engine/assertions-in-unreal-engine).

#### CODING-02 — avoid treating the UE 5.8 source line table as a fixed API contract

- **Priority:** P2 — maintenance; the repository gives exact line numbers throughout four references, and patch releases already move declarations.
- **Locations:** `SKILL.md:238-246`; all line-oriented source tables in the three references.
- **Finding:** The symbol names and header paths are useful, but line numbers are descriptive evidence for the pinned installation rather than durable lookup instructions. The skill already says lines drift in places; apply that rule consistently to the source tables and prefer `HeaderPath — Symbol` first, followed by the 5.8.2 observed line range.
- **Exact proposed addition:**

```diff
--- a/skills/core/coding-standards/SKILL.md
+++ b/skills/core/coding-standards/SKILL.md
@@
 Engine evidence: `Actor.h` lines 5–32 use IWYU-style fine-grained includes ending with
 `"Actor.generated.h"` at line 32; `Character.h` lines 5–19 show `CoreMinimal.h` first and
 `"Character.generated.h"` at line 19.
+These line numbers are observations from the pinned UE 5.8.2 installation. Search by the
+header path and symbol when applying the rule to another 5.8 patch release.
```

- **Practical task benefit:** agents will reach the right declaration after hotfix line drift instead of copying a stale line number as if it were a compiler contract.
- **Verified evidence:** the installed UE 5.8.2 files under `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/` contain the cited headers and symbols; this is a documentation-quality correction, not a changed engine API. Matching Epic topic: [Epic C++ Coding Standard](https://dev.epicgames.com/documentation/unreal-engine/epic-cplusplus-coding-standard-for-unreal-engine).

### No-change checks

- Prefixes, PascalCase/`b` booleans, `In`/`Out` naming, enum/flag style, Allman braces, tabs, `nullptr`, `override`, `TEXT`, `MoveTemp`, explicit lambda capture, `TObjectPtr`, `#pragma once`, generated-header-last, IWYU, forward declarations, API exports, UHT macros, and `WithValidation` remain present or applicable in UE 5.8.2 source. No syntax migration is recommended for these conventions.
- The UFUNCTION/UPROPERTY/UCLASS/USTRUCT/UENUM declarations and `GENERATED_BODY()` examples in `reflection-and-uht.md` map to `ObjectMacros.h` and the installed engine classes. The `TObjectPtr` guidance is consistent with the 5.8 headers.
- UE 5.8 release notes include a UHT format-string fix and the 5.8.2 hotfix fixes generated UHT output inclusion in installed builds; these are tool corrections, not a new reflection syntax requirement. The 5.8.1 Blueprint compiler reentrancy fix does not alter the coding-standard examples. Sources: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project was built with UHT/UBT, so diagnostics for every malformed prefix, generated-header placement, namespace case, include cycle, and export boundary were not exhaustively compile-tested.
- `DO_CHECK`, `DO_ENSURE`, shipping/test configuration, unity-build behavior, and module export settings are target/build-specific; the source check verifies the macro contract, not every project configuration.
- The report does not attempt to prove every rule in Epic’s broader style guide is enforced by UHT; style recommendations and compiler requirements remain distinct.

---

## core/control-rig-and-ik

**Status:** findings  
**Repository path:** `skills/core/control-rig-and-ik`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/coding-standards`, before `skills/core/core-types-and-containers`

**Files reviewed:**

- `skills/core/control-rig-and-ik/SKILL.md`
- `skills/core/control-rig-and-ik/references/animgraph-ik-nodes.md`
- `skills/core/control-rig-and-ik/references/control-rig-graph.md`
- `skills/core/control-rig-and-ik/references/ik-retargeter.md`

### Verified recommendations

#### RIG-01 — update the Modular Rig namespace deprecation wording to the 5.8.2 API reality

- **Priority:** P1 — compile correctness; agents following the current text may search for or call a symbol that is not present in the pinned public source.
- **Locations:** `SKILL.md:251-252`; `references/control-rig-graph.md:143-145`.
- **Finding:** The skill calls `GetRigModuleNameSpace()` deprecated and directs readers to `GetRigModulePrefix()`. Literal search across the installed UE 5.8.2 `Engine/Source` returns no `GetRigModuleNameSpace` declaration or use; `UControlRig::GetRigModulePrefix()` is the current public method. Replace “deprecated” with “not present in UE 5.8.2” so the guidance distinguishes a removed/absent helper from a still-callable deprecation shim.
- **Exact proposed replacement:**

```diff
--- a/skills/core/control-rig-and-ik/SKILL.md
+++ b/skills/core/control-rig-and-ik/SKILL.md
@@
- **ModularRig path deprecation** — `GetRigModuleNameSpace()` was deprecated in 5.6;
-  use `GetRigModulePrefix()` instead.
+ **ModularRig path API** — `GetRigModuleNameSpace()` is not present in the UE 5.8.2
+  installed source; use `UControlRig::GetRigModulePrefix()` instead.
--- a/skills/core/control-rig-and-ik/references/control-rig-graph.md
+++ b/skills/core/control-rig-and-ik/references/control-rig-graph.md
@@
-and reconnect modules without opening the editor. The deprecated `GetRigModuleNameSpace()`
-(5.6+) is replaced by `GetRigModulePrefix()` on `UControlRig`.
+and reconnect modules without opening the editor. `GetRigModuleNameSpace()` is not present
+in UE 5.8.2; use `GetRigModulePrefix()` on `UControlRig`.
```

- **Practical task benefit:** prevents failed 5.8.2 code searches and makes migration instructions actionable for modular-rig tooling.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Animation/ControlRig/Source/ControlRig/Public/ControlRig.h:123-127` — `UControlRig::GetRigModulePrefix`; whole installed `Engine/Source` literal search found no `GetRigModuleNameSpace`. UE 5.8.2 source.

#### RIG-02 — replace the stale Control Rig node “TSubclassOf class” model with the 5.8.2 asset reference

- **Priority:** P1 — editor/runtime setup correctness; a user who treats the node as a raw `TSubclassOf` can miss the strong asset-reference path and copy a deprecated accessor into custom tooling.
- **Locations:** `SKILL.md:62-65`; `references/animgraph-ik-nodes.md:118-125`.
- **Finding:** The overview says the Control Rig AnimGraph node’s primary property is “Control Rig Class — `TSubclassOf<UControlRig>`”. In 5.8.2 `FAnimNode_ControlRig` owns `ControlRigClass_DEPRECATED` plus `FControlRigAssetStrongReference ControlRigAssetReference`, and `GetControlRigClass()` is marked deprecated in favor of `GetControlRigAssetReference()`. Preserve `SetControlRigClass()` only as a compatibility/runtime setter, but teach new editor-node tooling to use the asset reference.
- **Exact proposed replacement:**

```diff
--- a/skills/core/control-rig-and-ik/SKILL.md
+++ b/skills/core/control-rig-and-ik/SKILL.md
@@
- **Control Rig Class** — `TSubclassOf<UControlRig>` asset to evaluate.
+ **Control Rig asset reference** — in UE 5.8.2 the node stores an
+  `FControlRigAssetStrongReference`; `ControlRigClass_DEPRECATED` and
+  `GetControlRigClass()` are compatibility paths. New tooling should use the asset
+  reference and `GetControlRigAssetReference()`.
--- a/skills/core/control-rig-and-ik/references/animgraph-ik-nodes.md
+++ b/skills/core/control-rig-and-ik/references/animgraph-ik-nodes.md
@@
 ## Control Rig node
 
+In UE 5.8.2, prefer the node’s `FControlRigAssetStrongReference` asset field for new
tooling. `FAnimNode_ControlRig::ControlRigClass_DEPRECATED` and
`GetControlRigClass()` remain only as deprecated compatibility paths; use
`GetControlRigAssetReference()` when reading the selected rig asset.
```

- **Practical task benefit:** reduces broken editor extensions and makes asset loading/reference behavior explicit instead of encouraging class-only assumptions.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Animation/ControlRig/Source/ControlRig/Public/AnimNode_ControlRig.h:64-79` — `FAnimNode_ControlRig::ControlRigClass_DEPRECATED`, `ControlRigAssetReference`, `GetControlRigAssetReference`, and deprecated `GetControlRigClass`. UE 5.8.2 source.

#### RIG-03 — add the practical UE 5.8 retargeting features without overstating stability

- **Priority:** P2 — workflow value; this is a scoped feature addition for runtime/offline retargeting, not a required migration.
- **Locations:** insertion after `references/ik-retargeter.md:129` (the runtime-retargeting section); optional overview pointer after `SKILL.md:259`.
- **Finding:** The UE 5.8 release notes add Foot Definition for retargeting and Retarget Override Sets. The reference already exposes `bUseCustomOverrideSets` but does not explain the authoring/runtime selection workflow. Add concise guidance: define foot plane/toes for foot transfer quality, author an override set on one retargeter, then select it for a run; do not create separate retargeter assets for every relationship. These are documented 5.8 features and are not labeled Beta/Experimental in the release notes.
- **Exact proposed addition:**

```diff
--- a/skills/core/control-rig-and-ik/references/ik-retargeter.md
+++ b/skills/core/control-rig-and-ik/references/ik-retargeter.md
@@
 ## Runtime retargeting
 
+### UE 5.8 foot definition and override sets
+
+UE 5.8 adds Foot Definition settings for more controlled foot/toe transfer and Retarget
+Override Sets for selecting different op-stack relationships from one `UIKRetargeter`.
+Author the foot plane/toes on the target IK Rig where foot fidelity matters. Author and
+name an override set in the retargeter, then select that set for the runtime/offline
+retarget operation; do not duplicate the retargeter asset solely for this relationship.
+Treat the override selection as part of the runtime configuration and validate the chosen
+set in a representative pose before shipping.
```

- **Practical task benefit:** lets gameplay retargeting support multiple body/foot relationships with fewer assets and gives artists a direct 5.8 upgrade path for foot placement quality.
- **Verified evidence:** [UE 5.8 Release Notes — Foot Definition for Retargeting](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#foot-definition-for-retargeting) and [Retarget Override Sets](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#retarget-override-sets); `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Animation/IKRig/Source/IKRig/Public/AnimNodes/AnimNode_RetargetPoseFromMesh.h` — `bUseCustomOverrideSets`, `CustomRetargetProfile`, `RetargetSourceMode`. UE 5.8.2 source and version-matched docs.

#### RIG-04 — classify the newly surfaced Control Rig simulation plugins explicitly

- **Priority:** P2 — risk control; the release notes’ “Beta” wording and installed descriptors must govern production advice.
- **Locations:** insertion after `SKILL.md:42` (Control Rig feature list) and in the version-notes block after `SKILL.md:259`.
- **Finding:** UE 5.8 release notes move Control Rig Physics to Beta and introduce Control Rig Dynamics. The installed descriptors are more precise: `ControlRigPhysics.uplugin` sets `IsBetaVersion: true` and `IsExperimentalVersion: false`; `ControlRigDynamics.uplugin` sets `IsExperimentalVersion: true`. Add both as optional features with their exact status; do not present them as stable replacements for the existing animation/IK path.
- **Exact proposed addition:**

```diff
--- a/skills/core/control-rig-and-ik/SKILL.md
+++ b/skills/core/control-rig-and-ik/SKILL.md
@@
 ## Version notes
 
+- UE 5.8 **Control Rig Physics is Beta** (`Engine/Plugins/Experimental/ControlRigPhysics/
+  ControlRigPhysics.uplugin`, `IsBetaVersion: true`). It is suitable for targeted
+  prototypes and controlled production trials, but keep a fallback animation path.
+- UE 5.8 **Control Rig Dynamics is Experimental** (`Engine/Plugins/Experimental/
+  ControlRigDynamics/ControlRigDynamics.uplugin`, `IsExperimentalVersion: true`).
+  Do not make it a hard dependency without validating plugin availability and cooked behavior.
```

- **Practical task benefit:** prevents accidental stability promises and makes plugin enablement/cooked dependency review part of adopting 5.8 simulation features.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/ControlRigPhysics/ControlRigPhysics.uplugin:15-16` (`IsBetaVersion: true`, `IsExperimentalVersion: false`); `.../ControlRigDynamics/ControlRigDynamics.uplugin:15-16` (`IsExperimentalVersion: true`); [UE 5.8 Release Notes — Control Rig Physics](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#animate-with-control-rig-physics-beta). UE 5.8.2 installed descriptors.

### No-change checks

- `FAnimNode_IKRig`, `FAnimNode_RetargetPoseFromMesh`, `UIKRigComponent::SetIKRigGoalPositionAndRotation`, `FIKRigGoal`, `EIKRigGoalTransformSource`, `URigHierarchy`, `FRigUnitContext`, `UModularRigController`, `GetRigModulePrefix`, and `FControlRigExecuteContext` used by the references are present in the installed UE 5.8.2 plugin source. Their usages do not require a broad rewrite.
- The existing IK Rig goal-space warning, `LODThreshold` guidance, retarget-source selection, `CustomRetargetProfile`, Control Rig threading/initialization cautions, and Control Rig/AnimBP ordering guidance remain applicable.
- UE 5.8.1 hotfix notes include a Control Rig `GetUserData` registry crash fix; 5.8.2 hotfix notes include IK/retargeting JSON and rotation-normalization fixes. These are engine fixes, not a reason to change the C++ goal/graph API examples: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No Control Rig, IK Rig, retargeter, Physics, or Dynamics asset was opened, compiled, cooked, or evaluated in a project during this audit; asset migration and runtime solver behavior remain unverified.
- The installed plugin descriptors and headers establish availability/status and API names, not performance, network determinism, or backward compatibility of existing project assets.
- Marketplace/vendor Control Rig modules and project-specific custom RigVM units were not inspected; their 5.8.2 compatibility is unknown.

---

## core/core-types-and-containers

**Status:** findings  
**Repository path:** `skills/core/core-types-and-containers`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/control-rig-and-ik`, before `skills/core/cpp-fundamentals`

**Files reviewed:**

- `skills/core/core-types-and-containers/SKILL.md`
- `skills/core/core-types-and-containers/references/containers.md`
- `skills/core/core-types-and-containers/references/math-types.md`
- `skills/core/core-types-and-containers/references/strings-and-text.md`
- `skills/core/core-types-and-containers/references/utility-types.md`

### Verified recommendations

#### TYPES-01 — correct quaternion composition order

- **Priority:** P1 — gameplay/math correctness; the current comments can produce reversed local/world rotation composition and visible animation or transform errors.
- **Locations:** `SKILL.md:176-180`; `references/math-types.md:90-106`.
- **Finding:** The skill says `Q * Rot` applies `Q` then `Rot` and describes quaternion composition as left-to-right. UE 5.8.2’s `TQuat<T>::operator*` documentation says `C = A * B` first applies `B` then `A` (“right first, then left”). The FTransform rule is intentionally opposite, so keep the transform statement separate and fix only quaternion comments.
- **Exact proposed replacement:**

```diff
--- a/skills/core/core-types-and-containers/SKILL.md
+++ b/skills/core/core-types-and-containers/SKILL.md
@@
-FQuat Comp = Q * Rot;                         // compose: apply Q then Rot
+FQuat Comp = Q * Rot;                         // compose: apply Rot then Q
--- a/skills/core/core-types-and-containers/references/math-types.md
+++ b/skills/core/core-types-and-containers/references/math-types.md
@@
-// Composition (apply LocalRot then Q)
+// Composition (right first, then left: apply LocalRot then Q)
 FQuat Combined = Q * LocalRot;
@@
-**UE quaternion convention:** `Q * V` rotates vector V by quaternion Q. Composition is
-left-to-right: `A * B` applies A first, then B.
+**UE quaternion convention:** `Q * V` rotates vector V by quaternion Q. Quaternion
+composition is right-to-left: `A * B` produces a rotation that applies `B` first, then `A`.
+This is opposite to the composition order documented for `FTransform`.
```

- **Practical task benefit:** prevents reversed yaw/pitch/roll composition in gameplay, animation, and camera code, especially where the skill’s examples are copied verbatim.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Math/Quat.h:205-214` — `TQuat<T>::operator*` order contract; `.../Math/TransformVectorized.h:51-58` — intentionally opposite `TTransform<T>` order. UE 5.8.2 source.

#### TYPES-02 — document the UE 5.8 compact-set build switch and reflected-container limit

- **Priority:** P2 — build/serialization correctness; projects enabling the memory/performance switch need to know that explicit compact/sparse types are not interchangeable at UPROPERTY boundaries.
- **Locations:** `SKILL.md:247-253`; `references/containers.md:203-207`.
- **Finding:** The current version note says `TSet` “may” use `TCompactSet` and the public API is unchanged, but UE 5.8 adds a target/build option `bUseCompactSetAsDefault` (default false) that changes the underlying `TSet`/`TMap` implementation. The 5.8 release note also states explicit `TCompactSet`/`TSparseSet` forms cannot be used as `UPROPERTY`s. Add the opt-in and reflection caveat; do not imply that all projects get compact sets automatically.
- **Exact proposed addition:**

```diff
--- a/skills/core/core-types-and-containers/SKILL.md
+++ b/skills/core/core-types-and-containers/SKILL.md
@@
 - **UE 5.5+:** `TSet` may internally use `TCompactSet`; the public API is unchanged.
+- **UE 5.8:** `TargetRules.bUseCompactSetAsDefault` (default `false`) opts a target into
+  compact `TSet`/`TMap` internals. `TCompactSet`/`TSparseSet` and their map forms remain
+  explicit implementation choices and cannot be used as `UPROPERTY` container types;
+  keep reflected members as `TSet`/`TMap`.
--- a/skills/core/core-types-and-containers/references/containers.md
+++ b/skills/core/core-types-and-containers/references/containers.md
@@
 ## Version notes
 
+UE 5.8 exposes `TargetRules.bUseCompactSetAsDefault` (`BuildConfiguration` XML/config,
+default `false`) to compile `TSet` and `TMap` against compact-set internals. The public
+`TSet`/`TMap` spelling is the portable choice. Do not replace a reflected member with an
+explicit `TCompactSet`/`TSparseSet` (or explicit map form): those implementation types are
+not valid `UPROPERTY` container types according to the 5.8 upgrade notes.
```

- **Practical task benefit:** enables deliberate memory/performance trials without breaking reflection or assuming a project-wide default that is not enabled.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/TargetRules.cs:1702-1708` — `bUseCompactSetAsDefault`, default `false`; `.../UEBuildTarget.cs:6645-6651` — compile definition; `Runtime/Core/Public/Containers/Set.h:12-15` — implementation switch; [UE 5.8 Release Notes — containers](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8). UE 5.8.2 source.

### No-change checks

- `TArray`, `TMap`, `TSet`, `TQueue` (default `EQueueMode::Spsc`), `TArrayView`, `TInlineAllocator`, `TFixedAllocator`, `TStaticArray`, `TStringBuilder`, `FStringView`, `FName`, `FText`, `TOptional`, `TVariant`, `TTuple`, `TPair`, LWC aliases, and the cited math/string methods are present in UE 5.8.2 source. No broad API rewrite is justified.
- `UPROPERTY`/GC guidance, `TQueue` single-consumer restriction, `TMap::Find` pointer return, `TArray` invalidation warning, `FName` case behavior, `FText::EqualTo`, LWC float/double boundaries, and optional/variant safety rules remain applicable.
- The UE 5.8 release notes’ `FText::AsMemory` overload, FName pool/hash changes, `TVariantPtr` acceptance, and compact-set work are scoped additions or implementation details rather than reasons to rewrite the skill’s basic type-selection table. The 5.8.1 and 5.8.2 hotfix sources contain no container/math migration that changes these examples: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project target was compiled with `bUseCompactSetAsDefault`, and no reflected asset/property containing containers was serialized or loaded under both implementations; migration and binary-compatibility behavior remain untested.
- The report verifies header contracts and UBT configuration but not every overload’s ABI, allocator performance, or platform-specific `TCHAR` width in a built target.
- No runtime test was run for the quaternion examples; the order correction is grounded in the installed source documentation, not a rendered transform comparison.

---

## core/cpp-fundamentals

**Status:** findings  
**Repository path:** `skills/core/cpp-fundamentals`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/core-types-and-containers`, before `skills/core/debugging-techniques`

**Files reviewed:**

- `skills/core/cpp-fundamentals/SKILL.md`
- `skills/core/cpp-fundamentals/references/object-creation-and-gc.md`
- `skills/core/cpp-fundamentals/references/reflection-macros.md`
- `skills/core/cpp-fundamentals/references/uobject-lifecycle-and-cdo.md`

### Verified recommendations

#### CPP-01 — correct the nested-USTRUCT GC statement

- **Priority:** P1 — memory/lifetime correctness; the current wording can lead authors to omit `UPROPERTY` from nested UObject references and produce objects that are not reachable by GC.
- **Locations:** `SKILL.md:199-203`; `references/reflection-macros.md:177-179`.
- **Finding:** A `USTRUCT` instance is a value, non-GC object, but that does not mean its reflected UObject properties are invisible to GC. When the struct itself is reachable through a reflected member, UE emits GC reference information for the struct’s nested properties. The existing sentence “there is nothing for the GC to track in a value type” is too broad and contradicts the engine’s `FStructProperty::EmitReferenceInfo` path.
- **Exact proposed replacement:**

```diff
--- a/skills/core/cpp-fundamentals/SKILL.md
+++ b/skills/core/cpp-fundamentals/SKILL.md
@@
-`UPROPERTY` inside a struct still enables serialization and editor exposure; it does not imply
-  GC ownership (there is nothing for the GC to track in a value type).
+`UPROPERTY` inside a struct still enables serialization and editor exposure. The struct itself
+  is a value and is not a GC object, but reflected UObject references inside it are traversed
+  when the containing struct/member is reachable through the UObject property graph; those
+  nested references still need `UPROPERTY`.
--- a/skills/core/cpp-fundamentals/references/reflection-macros.md
+++ b/skills/core/cpp-fundamentals/references/reflection-macros.md
@@
-`USTRUCT` structs are **not** garbage-collected. A `UPROPERTY` inside a struct enables
-serialization and editor exposure but does not constitute GC ownership. Struct lifetimes follow
-their containing UObject or stack frame.
+`USTRUCT` structs are **not** garbage-collected as objects. A `UPROPERTY` inside a struct enables
+serialization/editor exposure, and reflected UObject references in that struct are included in
+GC traversal when the containing struct is itself reachable. Struct lifetime still follows its
+containing UObject or stack frame; it is not an independent GC root.
```

- **Practical task benefit:** preserves both halves of the rule: value structs do not become GC roots, while nested `UObject` references remain visible and safe when reflected.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Private/UObject/GarbageCollection.cpp:6953-6975` — `FStructProperty::EmitReferenceInfo` checks nested properties and emits their reference schema. UE 5.8.2 source.

### No-change checks

- `GENERATED_BODY`, generated-header-last, `UCLASS`/`UPROPERTY`/`UFUNCTION`/`USTRUCT`/`UENUM`/`UINTERFACE` examples, CDO access through `GetDefaultObject`/`GetDefault`/`GetMutableDefault`, `CreateDefaultSubobject` vs `NewObject` vs `SpawnActor`, `TObjectPtr`, `TWeakObjectPtr`, `FGCObject`, `TStrongObjectPtr`, `AddToRoot`, `MarkAsGarbage`, and the `BeginDestroy`/`IsReadyForFinishDestroy`/`FinishDestroy` sequence are present in UE 5.8.2 source and remain applicable.
- The direct `UClass::ClassDefaultObject` field is still marked `UE_DEPRECATED(5.6)` in `Class.h`; the recommended `GetDefaultObject()` and global default helpers are current. `PostInitProperties` is documented by `Object.h:222-226` as occurring after construction and property/config initialization, matching the lifecycle reference.
- UE 5.8 release notes’ UHT format-string correction, compact-set work, GC improvements, and the 5.8.1/5.8.2 fixes for Blueprint/CDO and generated-output timing do not introduce a new UObject construction syntax. Sources: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No sample module was run through UHT/UBT, and no GC stress test exercised a nested USTRUCT containing a UObject reference; the correction is source-grounded but not runtime-tested in a project.
- Exact constructor/config/serialization ordering can vary with object flags, async loading, Blueprint re-instancing, and custom `TStructOpsTypeTraits`; those project-specific cases were not exhaustively exercised.
- Marketplace modules and generated code were not inspected, so their UObject ownership and custom struct reference hooks remain unknown.

---

## core/data-driven-design

**Status:** findings  
**Repository path:** `skills/core/data-driven-design`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/cpp-fundamentals`, before `skills/core/debugging-techniques`

**Files reviewed:**

- `skills/core/data-driven-design/SKILL.md`
- `skills/core/data-driven-design/references/config-and-developer-settings.md`
- `skills/core/data-driven-design/references/curves-and-runtime-data.md`
- `skills/core/data-driven-design/references/data-assets-and-validation.md`
- `skills/core/data-driven-design/references/datatables-and-composite.md`

### Verified recommendations

#### DATA-DRIVEN-01 — document the UE 5.8 editor DataTable object-export path

- **Priority:** P2 — practical editor-pipeline feature; it lets tooling emit JSON with nested struct fields as JSON objects instead of requiring a second custom serializer.
- **Locations:** insertion after `SKILL.md:89`; insertion after `references/datatables-and-composite.md:37` (the import/export subsection).
- **Finding:** The skill covers runtime `CreateTableFromCSVString`/`CreateTableFromJSONString` and import workflows, but omits the UE 5.8 release-note addition for DataTable struct export as objects. UE 5.8.2 exposes editor-only Blueprint/Python-facing helpers for CSV/JSON strings and files. The JSON helpers explicitly pass `EDataTableExportFlags::UseJsonObjectsForStructs`; do not present these editor helpers as packaged-runtime APIs.
- **Exact proposed addition:**

```diff
--- a/skills/core/data-driven-design/SKILL.md
+++ b/skills/core/data-driven-design/SKILL.md
@@
 `UCompositeDataTable` (`CompositeDataTable.h`:13) — a `UDataTable` subclass that stacks
 parent tables; higher-index parents win on duplicate row names. Use for DLC or per-platform row
 overrides without duplicating the base table. See
 [references/datatables-and-composite.md](references/datatables-and-composite.md).
+
+### UE 5.8 editor export helpers
+
+For editor automation, `UDataTableFunctionLibrary` exposes `ExportDataTableToCSVString`,
+`ExportDataTableToCSVFile`, `ExportDataTableToJSONString`, and
+`ExportDataTableToJSONFile`. The JSON helpers use
+`EDataTableExportFlags::UseJsonObjectsForStructs`, so nested reflected structs are emitted as
+JSON objects. These declarations are under `#if WITH_EDITOR`; keep them in editor tooling or
+commandlets, not packaged gameplay code. Check the returned `bool` and treat file-write errors
+as failures.
--- a/skills/core/data-driven-design/references/datatables-and-composite.md
+++ b/skills/core/data-driven-design/references/datatables-and-composite.md
@@
 JSON format: an array of objects, each with a `"Name"` field (the row key), or the key column
 set by `ImportKeyField`.
+
+### UE 5.8 editor export helpers
+
+`UDataTableFunctionLibrary` adds editor scripting helpers for exporting a table to CSV or JSON
+strings/files: `ExportDataTableToCSVString`, `ExportDataTableToCSVFile`,
+`ExportDataTableToJSONString`, and `ExportDataTableToJSONFile`. The JSON helpers call
+`GetTableAsJSON(EDataTableExportFlags::UseJsonObjectsForStructs)`, preserving nested reflected
+structs as JSON objects. The declarations are guarded by `WITH_EDITOR`, so use this path from
+editor automation/commandlets only; packaged runtime code should use the runtime import APIs
+or its own serializer.
```

- **Practical task benefit:** gives editor tools a supported UE 5.8 export path and avoids shipping code that links editor-only DataTable utilities.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Kismet/DataTableFunctionLibrary.h:166-233` — editor guard and four export declarations; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/DataTableFunctionLibrary.cpp:422-477` — implementations and `UseJsonObjectsForStructs`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/DataTable.h:318-358` — editor-only table output versus runtime string import. UE 5.8.2 source. Release-note match: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), “DataTable export struct to string and file as objects.”

#### DATA-DRIVEN-02 — state the 5.8 Data Validation cook-time controls next to the CI command

- **Priority:** P2 — CI observability; large projects can distinguish validator cost from ordinary cook time and make external-object loading behavior explicit.
- **Locations:** `references/data-assets-and-validation.md:130-137`; `SKILL.md:244-247`.
- **Finding:** The existing commandlet recipe is still applicable, but the UE 5.8 release notes add cook-time controls that are absent from the skill: external objects are preloaded for cook validation by default, and per-validator duration reporting is enabled by default. These are release-note-backed operational settings, not proof that every project’s commandlet invocation returns the desired CI exit status.
- **Exact proposed addition:**

```diff
--- a/skills/core/data-driven-design/SKILL.md
+++ b/skills/core/data-driven-design/SKILL.md
@@
 Run validation from the Content Browser (**Asset Actions → Validate Assets**) or via
 `UnrealEditor-Cmd.exe MyProject.uproject -run=DataValidation` for CI. The Data Validation plugin
 calls `IsDataValid` on `UDataTable` itself (engine implementation) and on `UObject`-derived
 assets that override it.
+For cook-time validation, UE 5.8 also exposes `DataValidation.LoadExternalObjectsForCookValidation`
+and `DataValidation.ReportCookValidationStats`; both are enabled by default in the 5.8 release.
+Set them explicitly in the CI invocation/config when reproducible external-object loading or
+per-validator timing is part of the build contract, and parse the commandlet log/exit status
+rather than assuming a successful process launch means all assets passed.
--- a/skills/core/data-driven-design/references/data-assets-and-validation.md
+++ b/skills/core/data-driven-design/references/data-assets-and-validation.md
@@
 Outputs validation results to the log; non-zero exit code on failures. Wire this into your build
 pipeline to catch content errors before they reach the game.
+
+UE 5.8 cook-time validation adds the `DataValidation.LoadExternalObjectsForCookValidation`
+and `DataValidation.ReportCookValidationStats` controls. The release notes describe both as
+enabled by default: the first preloads external objects before validators run, and the second
+reports total duration per validator. Pin their values in CI if those defaults are part of the
+pipeline contract.
```

- **Practical task benefit:** makes validation timing and dependency-loading behavior visible in CI without changing the asset schema.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), “Cook-time validation improvements” (`DataValidation.LoadExternalObjectsForCookValidation`, `DataValidation.ReportCookValidationStats`). The installed 5.8.2 source tree did not expose these names through the bounded declaration search, so the CVar declaration/implementation path is an unresolved source-location gap; the recommendation is explicitly release-note-backed, not claimed as locally source-verified. 5.8.1 and 5.8.2 hotfix searches found no DataTable/Data Validation API migration affecting this guidance: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### No-change checks

- `FTableRowBase`, `UDataTable` typed lookup (`FindRow`, `GetAllRows`, `ForeachRow`), `FDataTableRowHandle`, `UCompositeDataTable` layering, `bStripFromClientBuilds`, `UDataAsset`/`UPrimaryDataAsset`, Asset Manager primary IDs, soft references, `FRuntimeFloatCurve`, `UCurveTable`, config properties, `UDeveloperSettings`, and `IsDataValid(FDataValidationContext&)` remain source-compatible in UE 5.8.2.
- `UDataTable::CreateTableFromCSVString` and `CreateTableFromJSONString` are not the same API surface as the editor `UDataTableFunctionLibrary` fill/export helpers: the former are outside the `WITH_EDITOR` block in `DataTable.h:346-358`, while the latter are declared under `WITH_EDITOR` in `DataTableFunctionLibrary.h:166-243`. Preserve that runtime/editor boundary.
- `UCompositeDataTable` has both `AppendParentTables`/`RemoveParentTables` and single-table `AddParentTable`/`RemoveParentTable` in UE 5.8.2 (`CompositeDataTable.h:57-62`); the existing singular/plural mentions are not an API removal.
- 5.8.1/5.8.2 hotfix material reviewed; no additional data-container migration was found that justifies changing the existing container-selection guidance.

### Unresolved questions / verification gaps

- No project DataTable was imported/exported, no nested-struct JSON output was compared, and no editor-only Blueprint/Python call was executed. The export recommendation is declaration/implementation verified only.
- No Data Validation commandlet or cook was run, so the existing “non-zero exit code on failures” statement remains project/toolchain unverified; the added CVar defaults come from the verified 5.8 release-note block, not a locally located declaration.
- No Asset Manager scan, async bundle load, config save, or Data Only Blueprint asset was exercised under UE 5.8.2. Vendor/project-specific asset schemas and validation plugins were not inspected.

---

## core/debugging-techniques

**Status:** findings  
**Repository path:** `skills/core/debugging-techniques`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/cpp-fundamentals`, before `skills/core/delegates-and-events`

**Files reviewed:**

- `skills/core/debugging-techniques/SKILL.md`
- `skills/core/debugging-techniques/references/draw-debug-and-console.md`
- `skills/core/debugging-techniques/references/gameplay-debugger.md`
- `skills/core/debugging-techniques/references/visual-logger.md`

### Verified recommendations

#### DEBUG-01 — guard DrawDebug calls instead of claiming they are callable no-ops in Shipping/Test

- **Priority:** P1 — build correctness; unguarded `DrawDebug*` calls can fail to compile when `ENABLE_DRAW_DEBUG` is false.
- **Locations:** `SKILL.md:106-107`, `SKILL.md:326-327`; `references/draw-debug-and-console.md:9-11`.
- **Finding:** The skill says DrawDebug functions are automatically stripped from release builds and need no manual guards. In UE 5.8.2 `DrawDebugHelpers.h` places declarations inside `#if ENABLE_DRAW_DEBUG` and its `#else` explicitly says users must not call the functions in Shipping/Test because that generates a compile error. Keep debug code behind `#if ENABLE_DRAW_DEBUG` or a project debug module boundary. On-screen messages are a separate API and are compiled, but their implementation is disabled in Shipping/Test.
- **Exact proposed replacement:**

```diff
--- a/skills/core/debugging-techniques/SKILL.md
+++ b/skills/core/debugging-techniques/SKILL.md
@@
-All functions are guarded by `#if ENABLE_DRAW_DEBUG` (which evaluates to false in Shipping),
-so they are automatically stripped from release builds — no manual `#if` guards needed.
+The declarations are guarded by `#if ENABLE_DRAW_DEBUG` (normally false in Shipping/Test).
+Guard call sites with `#if ENABLE_DRAW_DEBUG` or keep them in a debug-only module; the
+header’s disabled branch intentionally does not provide callable DrawDebug declarations.
+`GEngine->AddOnScreenDebugMessage` is a separate API: it remains declared, but its message
+storage/drawing implementation is disabled in Shipping/Test.
@@
- - **`DrawDebug*` and `GEngine->AddOnScreenDebugMessage` in Shipping** — both are stripped.
-  They are dev tools; never rely on them for gameplay feedback.
+- **`DrawDebug*` in Shipping/Test** — the declarations can be absent when
+  `ENABLE_DRAW_DEBUG` is false; guard the call site. `AddOnScreenDebugMessage` is callable but
+  has no visible debug output in Shipping/Test. Neither is gameplay feedback.
--- a/skills/core/debugging-techniques/references/draw-debug-and-console.md
+++ b/skills/core/debugging-techniques/references/draw-debug-and-console.md
@@
-All functions below are declared in `DrawDebugHelpers.h` and guarded by
-`#if ENABLE_DRAW_DEBUG`. They are no-ops in Shipping builds. The common parameter tail is:
+All functions below are declared in `DrawDebugHelpers.h` only when
+`ENABLE_DRAW_DEBUG` is true. The disabled branch intentionally removes the declarations, so
+guard call sites in Shipping/Test builds. The common parameter tail is:
```

- **Practical task benefit:** prevents packaging/Shipping compile failures and keeps debug instrumentation from being mistaken for a release-safe runtime API.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/DrawDebugHelpers.h:13-17,228-232`; `.../Engine/Private/UnrealEngine.cpp:12466-12470` — on-screen message implementation is build-gated. UE 5.8.2 source.

#### DEBUG-02 — correct DrawDebug default lifetime semantics

- **Priority:** P1 — debugging correctness; the current “one frame” statement hides persistent-looking lines for one second and can mislead reproduction timing.
- **Locations:** `SKILL.md:100-101`; `references/draw-debug-and-console.md:35-40`.
- **Finding:** UE 5.8.2 `GetDebugLineLifeTime` maps `LifeTime <= 0` to the line batcher’s `DefaultLifeTime`, and `ULineBatchComponent` initializes that default to `1.0f`. `LifeTime = -1` and `LifeTime = 0` are therefore not one-frame semantics for the common line/sphere helpers. A persistent line uses `bPersistentLines=true` and is assigned `-1` internally.
- **Exact proposed replacement:**

```diff
--- a/skills/core/debugging-techniques/SKILL.md
+++ b/skills/core/debugging-techniques/SKILL.md
@@
- - `LifeTime` — seconds the shape is visible; `-1` means one frame; `0.f` on most shapes
-  means "use duration", which defaults to one frame from the game's perspective.
+- `LifeTime` — seconds the shape is visible; for the common line-batcher helpers, `<= 0`
+  selects `ULineBatchComponent::DefaultLifeTime` (1.0 second in UE 5.8.2), not one frame.
+  Use a small positive duration when the lifetime must be explicit.
@@
- - **`LifeTime = -1.f`** — in `DrawDebugLine`/`DrawDebugSphere`, `-1.f` means "use the default
-  duration" (one frame), NOT "persist forever". Use `bPersistentLines = true` for persistence,
-  then call `FlushPersistentDebugLines` to clear.
+- **`LifeTime <= 0.f`** — in `DrawDebugLine`/`DrawDebugSphere`, this selects the line batcher
+  default (1.0 second in UE 5.8.2); it is not a one-frame guarantee. Use a positive duration
+  for an explicit window. Use `bPersistentLines = true` for persistence, then call
+  `FlushPersistentDebugLines` to clear.
--- a/skills/core/debugging-techniques/references/draw-debug-and-console.md
+++ b/skills/core/debugging-techniques/references/draw-debug-and-console.md
@@
- - `LifeTime = -1.f` — "use the engine default", which is one frame for most functions.
+- `LifeTime <= 0.f` — use the line batcher default for the common helpers (1.0 second in
+  UE 5.8.2); do not assume one frame.
```

- **Practical task benefit:** makes transient-vs-persistent evidence predictable and avoids diagnosing a stale one-second shape as current state.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/DrawDebugHelpers.cpp:125-145` — lifetime selection; `.../Private/Components/LineBatchComponent.cpp:147-153` — `DefaultLifeTime = 1.0f`. UE 5.8.2 source.

#### DEBUG-03 — pass a FName to Gameplay Debugger key binding

- **Priority:** P1 — compile correctness; the current reference passes `EKeys::Q` where the UE 5.8.2 overload requires `FName`.
- **Locations:** `references/gameplay-debugger.md:142-149`.
- **Finding:** `FGameplayDebuggerAddonBase::BindKeyPress` overloads take `FName KeyName`; the modifier type is correctly `FGameplayDebuggerInputModifier`. Replace `EKeys::Q` with an explicit FName. Do not add an `InputCore` dependency just for this call.
- **Exact proposed replacement:**

```diff
--- a/skills/core/debugging-techniques/references/gameplay-debugger.md
+++ b/skills/core/debugging-techniques/references/gameplay-debugger.md
@@
-BindKeyPress(EKeys::Q, FGameplayDebuggerInputModifier::Shift,
+BindKeyPress(FName(TEXT("Q")), FGameplayDebuggerInputModifier::Shift,
              this, &FMySystemCategory::OnKeyPressed,
              EGameplayDebuggerInputMode::Local);
```

- **Practical task benefit:** makes the copied category example compile against the 5.8.2 API and keeps the sample’s dependency surface minimal.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/GameplayDebugger/Public/GameplayDebuggerAddonBase.h:43-78` — `BindKeyPress(FName, ...)`; `.../GameplayDebuggerTypes.h:360-381` — `FGameplayDebuggerInputModifier`. UE 5.8.2 source.

#### DEBUG-04 — document UE 5.8’s split Visual Logger recording/rendering/tool gates

- **Priority:** P2 — diagnostics/build control; projects can now keep trace recording while omitting Visual Logger output devices or the visualizer tool.
- **Locations:** insertion after `references/visual-logger.md:19`; `SKILL.md:172-175` and source-material list.
- **Finding:** UE 5.8 release notes introduce `UE_DEBUG_RECORDING_ENABLED`, `UE_DEBUG_RECORDING_USING_VLOG`, `UE_DEBUG_RENDERING_ENABLED`, and `UE_DEBUG_VISUALIZER_TOOL_ENABLED`. The current “`ENABLE_VISUAL_LOG` controls everything” wording is a compatibility simplification, not the complete 5.8 model. Add the split-gate summary and retain the compatibility note: `ENABLE_VISUAL_LOG` enables all three areas, while trace-only recording can bypass most VisualLogger functionality.
- **Exact proposed addition:**

```diff
--- a/skills/core/debugging-techniques/references/visual-logger.md
+++ b/skills/core/debugging-techniques/references/visual-logger.md
@@
 All `UE_VLOG*` macros evaluate to nothing unless `ENABLE_VISUAL_LOG` is defined (it is defined
 in Editor, Development, and DebugGame builds, not in Shipping or Test by default). Inside a
 recording session, every macro short-circuits on `FVisualLogger::IsRecording()` so inactive
 sessions have zero overhead.
+
+UE 5.8 also splits debug recording into independent gates: `UE_DEBUG_RECORDING_ENABLED`
+(VisualLogger and/or Insights trace capture), `UE_DEBUG_RECORDING_USING_VLOG` (the classic
+VisualLogger recording/output-device path), `UE_DEBUG_RENDERING_ENABLED` (immediate debug
+drawing), and `UE_DEBUG_VISUALIZER_TOOL_ENABLED` (analysis UI/tools). `ENABLE_VISUAL_LOG`
+remains a compatibility switch that enables all three areas. A trace-only configuration can
+record without the classic VisualLogger category/output-device features.
```

- **Practical task benefit:** supports lower-overhead Insights traces and prevents build-configuration mistakes when a project needs recording but not editor visualization.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/VisualLogger/VisualLoggerDefines.h:8-28`; [UE 5.8 Release Notes — Visual Logger](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8). UE 5.8.2 source and version-matched docs.

### No-change checks

- `UE_LOG`, `ensure`, `check`, DrawDebug shape names/signatures, `GEngine` screen-message overloads, `UE_VLOG*` macros, `SetIsRecordingToTrace`, Gameplay Debugger registration/unregistration, `CollectData`/`DrawData`, data-pack serialization, Live Coding cautions, and the listed console commands remain recognizable in UE 5.8.2.
- The 5.8 release notes’ Rewind Debugger frame-jump and Visual Logger trace changes complement, rather than replace, the existing workflow. 5.8.1/5.8.2 hotfix debug entries are fixes (including Visual Logger/Insights and Chaos/animation diagnostic fixes), not API migrations for these examples: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No Shipping/Test target was compiled, so the exact project macro combinations and link behavior were not runtime/build tested; the guard recommendation follows the installed headers’ disabled branch.
- No PIE/networked Gameplay Debugger session, Visual Logger file/trace, Rewind Debugger session, or rendered debug-draw capture was run.
- The CVar command list is source-spot-checked, not a complete inventory of platform/plugin-specific console variables; project-specific debug categories and vendor integrations remain unverified.

---

## core/delegates-and-events

**Status:** findings  
**Repository path:** `skills/core/delegates-and-events`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/debugging-techniques`, before `skills/core/editor-scripting-and-python`

**Files reviewed:**

- `skills/core/delegates-and-events/SKILL.md`
- `skills/core/delegates-and-events/references/binding-and-lifetime.md`
- `skills/core/delegates-and-events/references/delegate-types-matrix.md`
- `skills/core/delegates-and-events/references/dynamic-and-blueprint.md`

### Verified recommendations

#### DELEGATE-01 — remove `UPROPERTY()` from the FDelegateHandle example

- **Priority:** P1 — UHT/build correctness; `FDelegateHandle` is a native handle, not a reflected property type, and the current copyable snippet invites a malformed UPROPERTY declaration.
- **Locations:** `references/binding-and-lifetime.md:95-111`.
- **Finding:** The reference places `UPROPERTY()` immediately before `FDelegateHandle ScoreHandle`, then says the specifier is “not needed” merely to show intent. That is still presented as code a reader can copy. Store the handle as an ordinary member; do not annotate it with UPROPERTY.
- **Exact proposed replacement:**

```diff
--- a/skills/core/delegates-and-events/references/binding-and-lifetime.md
+++ b/skills/core/delegates-and-events/references/binding-and-lifetime.md
@@
-// Store in a UPROPERTY or member (not a local) so it survives past the binding scope
-UPROPERTY()                          // not needed for FDelegateHandle but shows intent
+// Store as an ordinary member (not a local) so it survives past the binding scope.
+// FDelegateHandle is a native handle; do not mark it UPROPERTY.
 FDelegateHandle ScoreHandle;
```

- **Practical task benefit:** keeps the example UHT-valid and makes the lifetime requirement clear without implying that GC/reflection owns the delegate handle.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Delegates/IDelegateInstance.h:15` — native `FDelegateHandle`; the 5.8.2 `UPROPERTY` specifier set contains no reflected `FDelegateHandle` property type. UE 5.8.2 source.

#### DELEGATE-02 — correct the `DECLARE_EVENT` access guarantee

- **Priority:** P2 — API contract correctness; callers must not rely on an access restriction the engine explicitly says is not enforced.
- **Locations:** `SKILL.md:184-189`; `references/delegate-types-matrix.md:83-116`.
- **Finding:** The skill describes `DECLARE_EVENT` as making `Broadcast` accessible only to the owner. UE 5.8.2’s `DelegateCombinations.h` says this behavior “is not enforced” and calls the type deprecated for new delegates. Replace the absolute access claim with its intended-but-not-enforced status and keep the plain-private-multicast recommendation.
- **Exact proposed replacement:**

```diff
--- a/skills/core/delegates-and-events/SKILL.md
+++ b/skills/core/delegates-and-events/SKILL.md
@@
-`DECLARE_EVENT(OwnerType, EventName)` creates a `TMulticastDelegate` subclass whose
-`Broadcast` is only accessible to `OwnerType` (friend). It is marked deprecated in the source comment
-(`DelegateCombinations.h:30`) — prefer plain `DECLARE_MULTICAST_DELEGATE`
-with a private broadcast method for the same encapsulation pattern.
+`DECLARE_EVENT(OwnerType, EventName)` creates the legacy owner-intended wrapper, but the
+access restriction is **not enforced**. UE 5.8.2 marks it deprecated for new delegates;
+prefer a plain `DECLARE_MULTICAST_DELEGATE` kept private with an explicit registration accessor
+or owner-only broadcast method.
--- a/skills/core/delegates-and-events/references/delegate-types-matrix.md
+++ b/skills/core/delegates-and-events/references/delegate-types-matrix.md
@@
-Only `OwnerType` can call `Broadcast`. The comment in `DelegateCombinations.h:30`
-marks it deprecated: "consider deprecated for new delegates, use normal multicast instead."
+The owner restriction is an intent, not an enforced access guarantee. The comment in
`DelegateCombinations.h:30` marks it deprecated for new delegates: use normal multicast with
an explicit private/registration-accessor pattern instead.
```

- **Practical task benefit:** prevents accidental security/encapsulation assumptions around event firing and aligns new code with the supported 5.8 pattern.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Delegates/DelegateCombinations.h:28-32` — non-enforced/deprecated comment. UE 5.8.2 source.

#### DELEGATE-03 — explicitly migrate the newly deprecated FUNC_DECLARE_* macros

- **Priority:** P2 — 5.8 warning cleanup; old macro names still compile through compatibility definitions but now produce deprecation diagnostics.
- **Locations:** insertion after `SKILL.md:43`; `references/delegate-types-matrix.md:26-27`.
- **Finding:** The matrix records that `FUNC_DECLARE_*` is deprecated in 5.8 but does not give a direct replacement rule. Add a one-line migration table: use the corresponding `DECLARE_*` macro from `DelegateCombinations.h`; do not copy the internal `UE_PRIVATE_DECLARE_*` helpers.
- **Exact proposed addition:**

```diff
--- a/skills/core/delegates-and-events/SKILL.md
+++ b/skills/core/delegates-and-events/SKILL.md
@@
 Dynamic delegate params must be **named** in the macro.
+
+**UE 5.8 migration:** replace legacy `FUNC_DECLARE_DELEGATE`,
+`FUNC_DECLARE_MULTICAST_DELEGATE`, `FUNC_DECLARE_EVENT`, and dynamic/TS variants with the
+corresponding public `DECLARE_*` macro. The `FUNC_DECLARE_*` compatibility macros are
+deprecated; `UE_PRIVATE_DECLARE_*` names are implementation details, not user API.
```

- **Practical task benefit:** removes 5.8 deprecation warnings without coupling project code to private macro names.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Delegates/Delegate.h:246-252` — `FUNC_DECLARE_*` definitions carry `UE_DEPRECATED_MACRO(5.8)`; `DelegateCombinations.h:19-64` — public replacement macros. UE 5.8.2 source.

### No-change checks

- Single-cast/multicast/dynamic family selection, named dynamic parameters, payload limits, `BindUObject`/`AddUObject`, weak-lambda forms, raw/lambda lifetime warnings, `AddDynamic`/`RemoveDynamic`, `Broadcast`/`ExecuteIfBound`, TS multicast, `FDelegateHandle`, data-pack-independent delegate serialization, and Blueprint dispatcher guidance remain applicable in UE 5.8.2.
- `TDynamicDelegate`/`TDynamicMulticastDelegate` are the current template names, and the public `DECLARE_*` macros in the references are current. The `FDelegateHandle::IsValid()` caveat remains correct: it does not prove a binding is still registered.
- UE 5.8 release notes include delegate-related fixes/deprecations (including `FCoreDelegates::OnPostEngineInit` → `FCoreDelegates::GetOnPostEngineInit()` and fixes for conditional delegate definitions); no existing example uses the affected core delegate. 5.8.1/5.8.2 hotfix delegate entries are bug fixes, not a family/API migration: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project module was built with UHT, and no dynamic dispatcher was saved/reloaded through an editor transaction; reflection diagnostics and serialized binding behavior remain untested.
- No concurrent TS multicast stress test or destruction-during-broadcast runtime test was run; source declarations establish available APIs, not project-specific thread safety.
 - No vendor/plugin delegate wrappers were inspected; their lifetime contracts may differ from Core delegate instances.
 
---

## core/editor-scripting-and-python

**Working-tree reconciliation:** read the added Gotchas concerning unexposed settings, live reflected containers, Rotator construction/restoration, imported dependencies, struct helpers, VibeUE pre-execution saves, and post-tick timeout handling. Their integration-specific live observations are **partially verified**, not reproduced here. In particular, VibeUE 5.0 `UPythonTools::ExecutePythonCode`, WorkflowService journal behavior, and the claimed Rotator precision behavior need their matching installed source/bindings or retained execution evidence; Epic 5.8 source alone cannot certify that adapter. Preserve the explicit save/timeout/rollback cautions rather than treating these as generic native Python guarantees. Earlier findings below refer to their named baseline passages, not shifted current line numbers.

**Status:** findings  
**Repository path:** `skills/core/editor-scripting-and-python`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/delegates-and-events`, before `skills/core/logging-and-assertions`

**Files reviewed:**

- `skills/core/editor-scripting-and-python/SKILL.md`
- `skills/core/editor-scripting-and-python/references/editor-subsystems.md`
- `skills/core/editor-scripting-and-python/references/editor-utility-widgets.md`
- `skills/core/editor-scripting-and-python/references/python-api.md`

### Verified recommendations

#### EDITOR-PYTHON-01 — use the `CallInEditor` UFUNCTION specifier, not function metadata

- **Priority:** P1 — editor-tool correctness; the current snippet can be accepted as an unrelated metadata key while failing to expose the Details-panel button.
- **Locations:** `SKILL.md:208-216`.
- **Finding:** UE 5.8.2 declares `CallInEditor` in the UFUNCTION specifier enum. The skill presents it only as `meta=(CallInEditor="true")`; replace both the prose and copyable example with the actual specifier form.
- **Exact proposed replacement:**

```diff
--- a/skills/core/editor-scripting-and-python/SKILL.md
+++ b/skills/core/editor-scripting-and-python/SKILL.md
@@
-### `UFUNCTION(meta = (CallInEditor = "true"))` — Details panel button
+### `UFUNCTION(CallInEditor)` — Details panel button
@@
-UFUNCTION(BlueprintCallable, Category = "Validation", meta = (CallInEditor = "true"))
+UFUNCTION(BlueprintCallable, CallInEditor, Category = "Validation")
 void ValidateSetup();
```

- **Practical task benefit:** makes the example produce the intended Details-panel action instead of silently missing the button.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h:1043-1047` — `EFunctionFlags` exposes `CallInEditor` as a UFUNCTION specifier. UE 5.8.2 source.

#### EDITOR-PYTHON-02 — correct the FName/FText Python wrapper types

- **Priority:** P1 — script/API correctness; type annotations and strict generated stubs are wrong if names/text are documented as ordinary `str` values.
- **Locations:** `references/python-api.md:27-35`.
- **Finding:** UE 5.8.2’s Python generator maps `FNameProperty` to `Name` and `FTextProperty` to `Text`; only `FStrProperty` maps to `str`. Python may coerce strings for inputs, but the return/type mapping is not uniformly `str`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/editor-scripting-and-python/references/python-api.md
+++ b/skills/core/editor-scripting-and-python/references/python-api.md
@@
-| `FString` / `FName` / `FText` | `str` | Transparent bidirectional |
+| `FString` | `str` | Native string mapping |
+| `FName` | `unreal.Name` | Python may coerce compatible strings for inputs |
+| `FText` | `unreal.Text` | Python may coerce compatible strings for inputs; preserve text semantics |
```

- **Practical task benefit:** prevents incorrect strict typing, comparisons, and method calls in generated Python tooling.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyGenUtil.cpp:3357-3365` — generated property types; `PyConversion.cpp:761-763` — native property conversion registrations. UE 5.8.2 source.

#### EDITOR-PYTHON-03 — narrow the automatic Python export rule to the actual predicates

- **Priority:** P2 — API discoverability; “whatever is reflected” overstates what appears in the generated module and leads to missing-class debugging.
- **Locations:** `SKILL.md:45-48`; `references/python-api.md:10-15`.
- **Finding:** UE 5.8.2 exports functions with Blueprint-callable/event flags (subject to exclusions), properties with Blueprint-visible/assignable flags, and classes that satisfy the Python generator’s script-exposure predicate such as BlueprintType/BlueprintGenerated classes. `EditAnywhere` is an editor-only export path, not a universal property rule, and a class is not exported merely because its plugin is enabled.
- **Exact proposed replacement:**

```diff
--- a/skills/core/editor-scripting-and-python/SKILL.md
+++ b/skills/core/editor-scripting-and-python/SKILL.md
@@
-from whatever is reflected to Blueprints — any `BlueprintCallable` function or class
-exposed by any enabled plugin is automatically available.
+from the script-exposure predicates for the enabled classes and functions. Functions need
+Blueprint-callable/event exposure (and are still filtered by internal/no-export metadata);
+classes need a script-visible class form such as `BlueprintType` or a Blueprint-generated class.
+Do not assume that enabling a plugin exports every reflected field.
--- a/skills/core/editor-scripting-and-python/references/python-api.md
+++ b/skills/core/editor-scripting-and-python/references/python-api.md
@@
-to Blueprints. It is **not** pre-generated; it automatically includes any class or function
-that is `BlueprintCallable`, `BlueprintPure`, `BlueprintAssignable`, `BlueprintReadWrite`,
-or `EditAnywhere` in any enabled plugin or project module.
+to Blueprints. It is **not** pre-generated; export is filtered by the plugin predicates:
+Blueprint-callable/event functions and Blueprint-visible/assignable properties are exported
+(subject to no-export/internal filters), while classes must satisfy the script-visible class
+predicate. Editor-only `CPF_Edit` properties are handled separately in the editor context;
+`EditAnywhere` is not a universal runtime export rule.
```

- **Practical task benefit:** makes missing Python symbols diagnosable and prevents relying on a plugin-enable side effect that does not exist.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyGenUtil.cpp:1538-1557`, `1609-1624`, and `1805-1815` — `IsScriptExposedClass`, `IsScriptExposedProperty`, `IsScriptExposedFunction`, and editor-only property predicates. UE 5.8.2 source.

#### EDITOR-PYTHON-04 — document the new UE 5.8 Optional-property bridge

- **Priority:** P2 — scoped 5.8 feature adoption; Python tools can now preserve unset-vs-set state instead of inventing sentinel values.
- **Locations:** insertion after `references/python-api.md:81` and in the main skill’s Python section after line 63.
- **Finding:** UE 5.8 release notes add Python read/write support for `TOptional`/Optional properties, with `None` representing unset. The current utility-types material mentions `TOptional` elsewhere but gives Python users no version-matched workflow.
- **Exact proposed addition:**

```diff
--- a/skills/core/editor-scripting-and-python/references/python-api.md
+++ b/skills/core/editor-scripting-and-python/references/python-api.md
@@
 val = actor.get_editor_property("hidden_in_game")
 ```
+
+### UE 5.8 Optional properties
+
+Optional reflected properties are readable and writable from Python. `None` means the
+optional is unset; a value sets it. Preserve that distinction rather than replacing
+`None` with a sentinel string or zero.
--- a/skills/core/editor-scripting-and-python/SKILL.md
+++ b/skills/core/editor-scripting-and-python/SKILL.md
@@
 actor.set_editor_property("hidden_in_game", True)
 ```
+For reflected Optional properties in UE 5.8, Python supports read/write access and uses
+`None` for the unset state.
```

- **Practical task benefit:** enables lossless editor batch edits for optional fields and avoids destructive sentinel conversions.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), “Optional property support to Python”; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyConversion.cpp:1035-1045` and `1209-1215` — `FOptionalProperty` conversion with `Py_None`. UE 5.8.2 source.

#### EDITOR-PYTHON-05 — make SupportedClasses mandatory for utility actions

- **Priority:** P2 — 5.8 validation/build hygiene; an unfiltered utility action now fails data validation instead of silently appearing for every asset.
- **Locations:** `SKILL.md:122-125`; `references/editor-utility-widgets.md` scripted-action setup section (insert after the SupportedClasses example).
- **Finding:** The skill says to populate `SupportedClasses` to filter actions but omits the UE 5.8 validation rule. Add an explicit requirement for both `UAssetActionUtility` and `UActorActionUtility` unless the action intentionally targets the global base class.
- **Exact proposed addition:**

```diff
--- a/skills/core/editor-scripting-and-python/SKILL.md
+++ b/skills/core/editor-scripting-and-python/SKILL.md
@@
 Content Browser. Populate `SupportedClasses` (class defaults) to filter which asset types
 show the action. `GetSupportedClass()` is deprecated since UE 5.2.
+In UE 5.8, leave `SupportedClasses` empty only when the action is intentionally global;
+otherwise the action fails data validation. Use `UObject` for a global asset action or
+`AActor` for a global actor action when that is the explicit intent.
--- a/skills/core/editor-scripting-and-python/references/editor-utility-widgets.md
+++ b/skills/core/editor-scripting-and-python/references/editor-utility-widgets.md
@@
 [insert after the SupportedClasses setup paragraph]
+UE 5.8 validation requires a non-empty `SupportedClasses` array for ordinary asset/actor
+actions. For an intentionally global action, add `UObject` to `UAssetActionUtility` or
+`AActor` to `UActorActionUtility` rather than relying on an empty array.
```

- **Practical task benefit:** avoids invalid utility assets and makes action scope explicit to users and validation.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), “Require that SupportedClasses be filled out”; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/Blutility/Classes/AssetActionUtility.h:81-107` and `ActorActionUtility.h:28-45` — SupportedClasses model. UE 5.8.2 source.

### No-change checks

- `GEditor->GetEditorSubsystem<T>()` / `unreal.get_editor_subsystem`, editor-only module boundaries, `UEditorActorSubsystem`, `UEditorAssetSubsystem`, `ULevelEditorSubsystem`, `UAssetEditorSubsystem`, `UUnrealEditorSubsystem`, `UEditorUtilitySubsystem`, transactions, `ScopedSlowTask`, startup scripts, `-run=pythonscript`, `-ExecutePythonScript`, ScriptMethod, ScriptName, and the `GetSupportedClass()` deprecation remain applicable in UE 5.8.2.
- The installed `PythonScriptCommandlet` parses `-Script=` and returns `-1` on execution errors; the repository’s lowercase `-script=` spelling is accepted by the command-line conventions but should be normalized in future edits to match the source’s canonical spelling.
- 5.8.1/5.8.2 hotfix documents contain no additional editor-scripting API migration that changes these recommendations; the relevant 5.8 additions are Optional properties, editor utility naming tokens, and SupportedClasses validation: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No editor process executed a Python script against a real project, so wrapper coercions, stub-generation output, transaction undo, Optional property persistence, and commandlet exit behavior were not runtime-tested here.
- Python plugin/vendor package installation, project-specific `ScriptNoExport` metadata, and generated module contents were not exhaustively enumerated.
- No utility asset was run through UE 5.8 data validation; the SupportedClasses requirement is release-note/source grounded but project validation output remains unobserved.
 
---

## core/enhanced-input

**Status:** findings  
**Repository path:** `skills/core/enhanced-input`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/editor-scripting-and-python`, before `skills/core/logging-and-assertions`

**Files reviewed:**

- `skills/core/enhanced-input/SKILL.md`
- `skills/core/enhanced-input/references/actions-and-contexts.md`
- `skills/core/enhanced-input/references/binding-and-setup.md`
- `skills/core/enhanced-input/references/modifiers-and-triggers.md`

### Verified recommendations

#### ENHANCED-INPUT-01 — do not describe `FInputActionValue::Get<T>()` as type-checking

- **Priority:** P1 — input correctness; the current warning encourages developers to trust a false zero result and can silently turn an axis or touch input into the wrong gameplay state.
- **Locations:** `SKILL.md:202-203`; insertion after `references/actions-and-contexts.md:32`.
- **Finding:** UE 5.8.2’s `Get<bool>()`, `Get<Axis1D>()`, `Get<Axis2D>()`, and `Get<Axis3D>()` specializations read/convert the stored components; they do not compare the action’s `ValueType` and reject a mismatch. For example, `Get<bool>()` returns `IsNonZero()` for a non-zero Axis2D value, while `Get<Axis2D>()` returns the X/Y components even if the action is Boolean. The skill should require matching the asset type or explicitly inspecting `GetValueType()` instead of saying a mismatch silently returns zero.
- **Exact proposed replacement:**

```diff
--- a/skills/core/enhanced-input/SKILL.md
+++ b/skills/core/enhanced-input/SKILL.md
@@
-Reading the wrong type silently returns zero (e.g. `Get<bool>()` on an Axis2D action returns
-`false`). The correct type is whatever `EInputActionValueType` the action asset declares.
+`Get<T>()` is a component conversion, not a runtime `ValueType` assertion. It does not reject a
+mismatch: `Get<bool>()` tests whether any stored component is non-zero, and vector getters read
+the corresponding components even when the action asset declares another type. Match the getter
+to the action's `EInputActionValueType`, or inspect `Value.GetValueType()` before converting.
--- a/skills/core/enhanced-input/references/actions-and-contexts.md
+++ b/skills/core/enhanced-input/references/actions-and-contexts.md
@@
 Source: `InputActionValue.h`:10–20. The underlying storage in `FInputActionValue` is always
 `FVector` with unused components zeroed.
+
+`Get<T>()` does not validate `ValueType`; the UE 5.8.2 specializations convert the stored
+components (`Get<bool>()` uses `IsNonZero()`, while vector getters return the stored X/Y/Z
+components). Treat the action asset's `ValueType` as the contract and use `GetValueType()` when
+a generic handler must distinguish types.
```

- **Practical task benefit:** prevents false “zero input” diagnoses and avoids Boolean/vector handlers accepting a value with unintended semantics.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/InputActionValue.h:102-124` — no type check in `Get<T>()` and explicit `GetValueType()`; `:203-227` — four getter specializations. UE 5.8.2 source.

#### ENHANCED-INPUT-02 — preserve state in custom stateful modifiers and triggers during mapping rebuilds

- **Priority:** P2 — hot-reload/remapping stability; stateful custom smoothing, hold, and combo-like logic should not reset or re-fire when control mappings are rebuilt.
- **Locations:** insertion after `references/modifiers-and-triggers.md:158`; insertion after `SKILL.md:249`.
- **Finding:** UE 5.8 release notes document state transfer during `RebuildControlMappings`. UE 5.8.2 calls `OnTriggerReinstanced` and `OnModifierReinstanced` for matching old/new instances and exposes BlueprintNativeEvent receive hooks for custom state. The current custom trigger recipe does not tell authors where to copy their own state.
- **Exact proposed addition:**

```diff
--- a/skills/core/enhanced-input/SKILL.md
+++ b/skills/core/enhanced-input/SKILL.md
@@
 - **Action fires on context add when key is held** → default `FModifyContextOptions`
   sets `bIgnoreAllPressedKeysUntilRelease = true`; the key must be released and re-pressed.
   Set `bIgnoreAllPressedKeysUntilRelease = false` to override.
+- **Stateful custom modifier/trigger resets during a mapping rebuild** → override
+  `ReceiveModifierReinstanced` or `ReceiveTriggerReinstanced` and copy custom runtime state
+  from the old same-class instance. UE 5.8 invokes these hooks when a matching mapping is
+  reinstanced; do not use a global/static cache as a workaround.
--- a/skills/core/enhanced-input/references/modifiers-and-triggers.md
+++ b/skills/core/enhanced-input/references/modifiers-and-triggers.md
@@
 Add to a mapping's `Triggers[]` array in the IMC asset or construct one in C++ and push it to
 the mapping via `UInputMappingContext::MapKey` before adding the context.
+
+### Preserving custom state across mapping rebuilds (UE 5.8)
+
+`RebuildControlMappings` can replace a trigger or modifier instance. UE 5.8 calls
+`OnTriggerReinstanced`/`OnModifierReinstanced` for matching same-class instances and then
+dispatches to the BlueprintNativeEvent hooks `ReceiveTriggerReinstanced` and
+`ReceiveModifierReinstanced`. Copy custom state there, calling the parent implementation when
+overridden:
+
+```cpp
+void UMyInputTrigger::ReceiveTriggerReinstanced_Implementation(
+    const UInputTrigger* OldTrigger)
+{
+    Super::ReceiveTriggerReinstanced_Implementation(OldTrigger);
+    const UMyInputTrigger* Old = Cast<UMyInputTrigger>(OldTrigger);
+    if (Old)
+        CustomElapsed = Old->CustomElapsed;
+}
+```
+
+Use the analogous `ReceiveModifierReinstanced_Implementation` hook for stateful modifiers. This
+is a 5.8 state-preservation feature, not a guarantee that unrelated or newly added mappings
+retain state; continue to handle initial state explicitly.
```

- **Practical task benefit:** prevents false `Started`/`Triggered` transitions and lost smoothing/hold progress when contexts or mappings are rebuilt.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/InputTriggers.h:175-194` — trigger reinstance contract and receive event; `InputModifiers.h:57-76` — modifier counterpart; `EnhancedInputSubsystemInterface.cpp:1134-1167` — matching mapping state transfer. UE 5.8.2 source. Release-note match: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), Enhanced Input fixes around trigger/modifier state preservation during `RebuildControlMappings`.

#### ENHANCED-INPUT-03 — add the UE 5.8 CommonUI/CommonInput integration as an optional path

- **Priority:** P2 — scoped feature adoption; UI-heavy projects can use one Enhanced Input action asset for gameplay/UI actions and platform-specific CommonUI action presentation instead of maintaining duplicate input data.
- **Locations:** insertion after `SKILL.md:57`; insertion after `references/binding-and-setup.md:191`.
- **Finding:** UE 5.8 release material describes a unified Enhanced Input and Common Input/UI workflow. In the installed 5.8.2 plugins, CommonInput settings expose Enhanced Input support and Enhanced Input click/back actions, `UCommonActionWidget` accepts a `UInputAction`, and `UCommonActivatableWidget` can own an input mapping and priority. This is optional and requires the CommonUI/CommonInput plugins; the current skill should not imply that enabling Enhanced Input alone creates the UI integration.
- **Exact proposed addition:**

```diff
--- a/skills/core/enhanced-input/SKILL.md
+++ b/skills/core/enhanced-input/SKILL.md
@@
 Setup is complete when each action delivers the expected value type to its handler, context
 priority resolves conflicting mappings, and removing a context stops its bindings.
+
+### Optional UE 5.8 CommonUI integration
+
+For projects using CommonUI/CommonInput, enable Enhanced Input support in Common Input settings
+and reference the same `UInputAction` assets from `UCommonActionWidget` or the
+`UCommonActivatableWidget` input-mapping fields. CommonUI can then present platform-specific
+action icons and apply/remove a widget-owned mapping context with its configured priority. Add
+`CommonInput`/`CommonUI` module dependencies only to modules that use those APIs; this path is
+not required for gameplay-only Enhanced Input.
--- a/skills/core/enhanced-input/references/binding-and-setup.md
+++ b/skills/core/enhanced-input/references/binding-and-setup.md
@@
 Source: `EnhancedInputSubsystems.h`:108–187 (`UEnhancedInputWorldSubsystem`).
+
+## CommonUI/CommonInput integration in UE 5.8
+
+When the project uses CommonUI, `UCommonInputSettings` can enable Enhanced Input support and
+provide Enhanced Input click/back actions. `UCommonActionWidget` exposes
+`SetEnhancedInputAction`/`EnhancedInputAction`, while `UCommonActivatableWidget` exposes an
+optional `InputMapping` and `InputMappingPriority` that are applied with the widget lifecycle.
+This requires the CommonInput/CommonUI plugins and their module dependencies; it is not a
+replacement for adding the local-player Enhanced Input context in gameplay-only projects.
```

- **Practical task benefit:** removes duplicated UI/gameplay action definitions where CommonUI is already in use while keeping the plugin/dependency boundary explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/CommonUI/Source/CommonInput/Public/CommonInputSettings.h:24-75` — Enhanced Input support and click/back accessors; `CommonInputBaseTypes.h:101-129` — Enhanced Input click/back action properties; `CommonUI/Public/CommonActionWidget.h:41-60,108-115` — action setter/property; `CommonUI/Public/CommonActivatableWidget.h:229-235` — widget mapping and priority; `CommonUI/CommonUI.Build.cs:13-23` — EnhancedInput/CommonInput module dependencies. UE 5.8.2 source. Release-note match: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), “Unified Input System: Common UI and Enhanced Input.”

#### ENHANCED-INPUT-04 — remove the stale “abstract action” label

- **Priority:** P2 — authoring clarity; the Content Browser can create `UInputAction` assets, so calling the type abstract contradicts the source and confuses setup.
- **Locations:** `SKILL.md:64`.
- **Finding:** `UInputAction` is declared `UCLASS(MinimalAPI, BlueprintType)` and derives from `UDataAsset`; it is not declared `Abstract`. The behavior and value-type guidance remains valid.
- **Exact proposed replacement:**

```diff
--- a/skills/core/enhanced-input/SKILL.md
+++ b/skills/core/enhanced-input/SKILL.md
@@
-| `UInputAction` | Abstract action data asset; carries a `ValueType` (`EInputActionValueType`) |
+| `UInputAction` | Action data asset; carries a `ValueType` (`EInputActionValueType`) |
```

- **Practical task benefit:** makes the asset-authoring model match the class metadata and avoids telling users a creatable asset is abstract.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/EnhancedInput/Source/EnhancedInput/Public/InputAction.h:54-56` — `UCLASS(MinimalAPI, BlueprintType)` and `UInputAction : public UDataAsset`. UE 5.8.2 source.

### No-change checks

- `DefaultKeyMappings` replacing deprecated `UInputMappingContext::Mappings`, `FModifyContextOptions` defaults, mapping priority, `ETriggerEvent` transitions, action accumulation, `BindAction` overloads, runtime injection, world subsystem setup, and legacy binding deletion behind `ENHANCED_INPUT_ALLOW_LEGACY_BINDING` remain applicable in UE 5.8.2.
- The Combo trigger deprecation is already recorded in `references/modifiers-and-triggers.md:138-140`; no second replacement recipe is needed. UE 5.8 release notes explicitly deprecate it because it can corrupt mapping contexts.
- The installed 5.8.2 source uses `EnhancedInput.IgnoreHeldDigitalActionKeysOnFlush` and `EnhancedInput.CorrectTouchBoolActionKeys` compatibility CVars for the release-note fixes; the skill’s held-key warning is conceptually correct, but project behavior can still be CVar/config dependent.
- 5.8.1/5.8.2 hotfix searches found no additional Enhanced Input API migration; their input-adjacent entries are fixes, not a new binding-family replacement: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project input assets were opened, no mappings were rebuilt in PIE, and no CommonUI widget was instantiated; source/declaration checks do not prove the project’s generated bindings, priorities, or focus routing.
- The CommonUI unified workflow was release-note and installed-plugin source verified, but its exact user-settings migration and platform glyph behavior were not exercised in a project.
- No runtime check confirmed the CVar compatibility behavior for held-key flushes, touch Boolean actions, or stateful custom trigger/modifier reinstance in a packaged or multiplayer build.

---

## core/game-thread-performance

**Status:** no changes  
**Repository path:** `skills/core/game-thread-performance`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/enhanced-input`, before `skills/core/gameplay-ability-system`

**Files reviewed:**

- `skills/core/game-thread-performance/SKILL.md`

### Verified recommendations

- No UE 5.8.2-specific replacement is justified for this skill’s scoped guidance. The existing `stat unit`/`stat game` triage, cycle-counter macros, game-thread ownership boundary, timer/event alternative, and worker-task-to-game-thread handoff remain applicable.
- The 5.8 release-note performance changes reviewed (including Mass scheduling and reduced game-thread work in feature-specific systems) do not change the generic rule to measure the project hotspot before moving work or to keep UObject/actor mutation on the game thread.

### No-change checks

- `DECLARE_CYCLE_STAT`, `SCOPE_CYCLE_COUNTER`, and `QUICK_SCOPE_CYCLE_COUNTER` remain declared in `Stats.h`; `TRACE_CPUPROFILER_EVENT_SCOPE` remains available in the Core profiling headers. `LevelTick.cpp` still defines tick/stat categories used by the recommended workflow.
- `AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, ...)` remains a valid engine pattern. The example’s `TWeakObjectPtr` is captured without dereferencing UObject state on the worker, and the result is applied through a game-thread task.
- 5.8.1/5.8.2 hotfixes reviewed; the game-thread-adjacent entries are bug fixes and do not require a new generic performance recipe: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project trace, Insights session, `stat unit` capture, or before/after benchmark was run. The skill remains measurement guidance, not evidence of a particular project’s bottleneck or improvement.
- No worker-thread stress test or race detector run was performed; engine declarations do not establish that arbitrary project functions are thread-safe.

**Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Stats/Stats.h:123-132,221-230`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/ProfilingDebugging/CpuProfilerTrace.h`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/LevelTick.cpp:60-67,104-128`. UE 5.8.2 source. Official docs: [Unreal Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine), [Trace](https://dev.epicgames.com/documentation/en-us/unreal-engine/trace-in-unreal-engine-5), [Stat Commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine).

---

## core/gameplay-ability-system

**Status:** findings  
**Repository path:** `skills/core/gameplay-ability-system/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/game-thread-performance`, before `skills/core/logging-and-assertions`

**Files reviewed:**

- `skills/core/gameplay-ability-system/SKILL.md`
- `skills/core/gameplay-ability-system/references/ability-system-component.md`
- `skills/core/gameplay-ability-system/references/gameplay-abilities.md`
- `skills/core/gameplay-ability-system/references/attributes-and-effects.md`
- `skills/core/gameplay-ability-system/references/ability-tasks-and-cues.md`

### Verified recommendations

#### GAS-01 — correct the Gameplay Event activation-path description

- **Priority:** P1 — correctness; an agent following the current wording may treat event-triggered abilities as a bypass of activation checks and build a second, unsafe validation path around them.
- **Locations:** `references/gameplay-abilities.md:140-154`; the main skill delegates this topic at `SKILL.md:196-197`.
- **Finding:** the reference says Gameplay Events activate abilities “without the normal `TryActivateAbility` path.” UE 5.8.2 does not call the public method directly, but `UAbilitySystemComponent::HandleGameplayEvent` resolves the event tag and its direct parents, then `TriggerAbilityFromGameplayEvent` calls `InternalTryActivateAbility`. The internal function is the shared path documented in source as performing `CanActivateAbility`, instancing, networking/prediction, and activation. The event helper also copies the payload and overwrites its `EventTag` with the dispatched tag.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-ability-system/references/gameplay-abilities.md
+++ b/skills/core/gameplay-ability-system/references/gameplay-abilities.md
@@
-Abilities can be triggered by `FGameplayEventData` payloads without the normal `TryActivateAbility`
-path. Useful for animation notify-driven attacks or external system triggers:
+Abilities can be triggered by `FGameplayEventData` payloads without calling the public
+`TryActivateAbility` method directly. `UAbilitySystemComponent::HandleGameplayEvent` resolves the
+event tag and its direct parents, then `TriggerAbilityFromGameplayEvent` calls
+`InternalTryActivateAbility`, so the shared activation checks, instancing, networking, and
+prediction path still apply. The helper copies the payload and sets its `EventTag` to the dispatched
+tag. This is useful for animation-notify-driven attacks or external system triggers:
```

- **Practical task benefit:** keeps event-driven abilities on the same authority, tag, cost/cooldown, and prediction checks as direct activation while preserving the useful distinction that callers use the event API rather than the public activation method.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/GameplayAbilities/Source/GameplayAbilities/Private/AbilitySystemComponent_Abilities.cpp:2496-2527` (`TriggerAbilityFromGameplayEvent`), `2564-2605` (`HandleGameplayEvent`), and `1704-1705` (`InternalTryActivateAbility` source contract). UE 5.8.2. Epic comparison basis: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), GAS section.

#### GAS-02 — document conditional granted-effect lifetime control added in UE 5.8

- **Priority:** P2 — practical authoring/correctness; designers otherwise have to implement ad-hoc removal code or may assume an on-application effect ends with its owner when UE’s default is independent lifetime.
- **Locations:** `SKILL.md:201-220`; insertion in `references/attributes-and-effects.md` after the GE Components table at `:142-154`.
- **Finding:** the skill lists `UAdditionalEffectsGameplayEffectComponent` only as a conditional-application component. UE 5.8 adds `FConditionalGameplayEffect::RemovalPolicy` and `StackCountToRemove`, allowing an on-application granted GE to be removed when the owning active GE is removed. The default remains `GrantedEffectControlsOwnLifetime`; `RemoveGrantedEffectOnEnd` is invalid for an Instant owning GE or Instant granted GE and is editor-validated as an error.
- **Exact proposed addition:**

```diff
--- a/skills/core/gameplay-ability-system/SKILL.md
+++ b/skills/core/gameplay-ability-system/SKILL.md
@@
 optionally add GE Components (grants/requires/removes tags, immunity,
 stacking). Apply from C++:
+
+`UAdditionalEffectsGameplayEffectComponent` can also control the lifetime of an
+`OnApplicationGameplayEffects` entry in UE 5.8: leave the default
+`GrantedEffectControlsOwnLifetime` when the child effect is independent, or select
+`RemoveGrantedEffectOnEnd` when the child must be removed with the active owning GE.
+That policy is only meaningful for non-Instant effects; the editor rejects an Instant
+owning or granted GE, and `StackCountToRemove` controls how many child stacks are removed
+(`INDEX_NONE` means all).
--- a/skills/core/gameplay-ability-system/references/attributes-and-effects.md
+++ b/skills/core/gameplay-ability-system/references/attributes-and-effects.md
@@
 | `UChanceToApplyGameplayEffectComponent` | Probability gate |
 | `UBlockAbilityTagsGameplayEffectComponent` | Blocks ability activation by tag while active |
+
+For `UAdditionalEffectsGameplayEffectComponent::OnApplicationGameplayEffects`, UE 5.8 adds
+`FConditionalGameplayEffect::RemovalPolicy`: `GrantedEffectControlsOwnLifetime` is the default,
+while `RemoveGrantedEffectOnEnd` removes matching active child effects when the owning GE ends.
+`StackCountToRemove` is used with the latter policy; `INDEX_NONE` removes all matching stacks.
+Do not use that policy with an Instant owning or granted GE: Instant effects are not retained in
+the active-effect container, and the component's editor validation reports the configuration as
+invalid.
```

- **Practical task benefit:** gives ability/effect authors a native, data-driven way to keep temporary child effects in sync with a parent effect and avoids invalid Instant configurations.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), cached lines 6673-6688 (GAS `RemovalPolicy`, stack removal, validation); `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/GameplayAbilities/Source/GameplayAbilities/Public/GameplayEffect.h:477-518` (`EGameplayEffectGrantedEffectRemovalPolicy`, `FConditionalGameplayEffect`); `.../Source/GameplayAbilities/Public/GameplayEffectComponents/AdditionalEffectsGameplayEffectComponent.h:18-64`; `.../Private/GameplayEffectComponents/AdditionalEffectsGameplayEffectComponent.cpp:117-181` (`OnActiveGameplayEffectRemoved`, `IsDataValid`). UE 5.8.2.

#### GAS-03 — add the UE 5.8 active-effect-handle migration note

- **Priority:** P1 — compile/deprecation correctness for custom GAS integrations; code that manufactures handles from integers or maintains the former global ownership map will warn and may rely on an invalid ownership model.
- **Locations:** insertion in `SKILL.md` Version notes after `:321`; insertion in the engine-source list after `:342`.
- **Finding:** the current skill explains applying effects but does not mention that UE 5.8 changed `FActiveGameplayEffectHandle` ownership and deprecated the integer constructor plus global-map cleanup helpers. The installed handle now stores a weak owning ASC; the instant sentinel is deliberately invalid and has no usable owner.
- **Exact proposed addition:**

```diff
--- a/skills/core/gameplay-ability-system/SKILL.md
+++ b/skills/core/gameplay-ability-system/SKILL.md
@@
 - `GetAbilitySystemComponentFromActorInfo_Checked()` deprecated in 5.5; use `GetAbilitySystemComponentFromActorInfo_Ensured()`.
+- `FActiveGameplayEffectHandle(int32)` is deprecated in 5.8. Use `GenerateNewHandle(OwningASC)`
+  for a valid custom handle or `GetInstantExecutedHandle()` for an already-executed Instant GE;
+  do not use the deprecated `ResetGlobalHandleMap()`/`RemoveFromGlobalMap()` helpers. The instant
+  sentinel's `GetOwningAbilitySystemComponent()` is undefined, and a removed active effect returns
+  no owning ASC.
@@
 - `AbilitySystemGlobals.h` — `UAbilitySystemGlobals::InitGlobalData()`:69.
+- `ActiveGameplayEffectHandle.h` — `FActiveGameplayEffectHandle`:17, `GenerateNewHandle`:38,
+  `GetInstantExecutedHandle`:48, `GetOwningAbilitySystemComponent`:64.
```

- **Practical task benefit:** prevents deprecation warnings and avoids trying to recover an ASC from an instant or already-removed effect handle.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), cached lines 6688 and 12861-12862; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/GameplayAbilities/Source/GameplayAbilities/Public/ActiveGameplayEffectHandle.h:21-70,92-108`. UE 5.8.2.

#### GAS-04 — remove the obsolete mandatory manual `InitGlobalData()` startup step

- **Priority:** P1 — startup guidance correctness; the current prerequisite tells every project to add a redundant call and attributes silent prediction failures to omitting it, while UE 5.8.2 initializes the singleton lazily on first request.
- **Locations:** `SKILL.md:44-46` and `SKILL.md:289`; keep the source-material citation at `SKILL.md:342` but update the explanatory text as shown.
- **Finding:** `UAbilitySystemGlobals::Get()` routes through `IGameplayAbilitiesModule::Get().GetAbilitySystemGlobals()`. In UE 5.8.2, the GameplayAbilities module creates and roots the configured globals object and calls `InitGlobalData()` when that singleton is first requested. `InitGlobalData()` is idempotent, so an explicit call is not harmful but is no longer a required project startup step.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-ability-system/SKILL.md
+++ b/skills/core/gameplay-ability-system/SKILL.md
@@
-3. Call `UAbilitySystemGlobals::Get().InitGlobalData()` exactly once at startup — typically in
-   `UAssetManager::StartInitialLoading` or your game module's startup function. This is required
-   for target data and montage prediction; omitting it causes silent failures.
+3. Do not add a mandatory manual `InitGlobalData()` startup call for UE 5.8.2. The
+   GameplayAbilities module lazily creates its configured globals singleton on the first
+   `UAbilitySystemGlobals::Get()`/`GetAbilitySystemGlobals()` request and calls `InitGlobalData()`
+   itself. An explicit call is idempotent but redundant; keep the configured globals class and
+   Gameplay Abilities settings valid.
@@
- - **`InitGlobalData()` not called** — montage and target-data prediction break silently.
+- **Invalid AbilitySystemGlobals configuration** — the module cannot create the configured globals
+  singleton. UE 5.8.2 performs the global-data initialization lazily; an extra manual
+  `InitGlobalData()` call is not a prerequisite.
```

- **Practical task benefit:** removes unnecessary startup boilerplate and directs debugging toward the actual configured globals class/settings rather than a call that the module already performs.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/GameplayAbilities/Source/GameplayAbilities/Private/GameplayAbilitiesModule.cpp:24-43` (`FGameplayAbilitiesModule::GetAbilitySystemGlobals` creates, roots, and initializes the singleton); `.../Private/AbilitySystemGlobals.cpp:63-96` (`UAbilitySystemGlobals::InitGlobalData`, including the UE5.3+ automatic-initialization comment and idempotence guard); `.../Public/AbilitySystemGlobals.h:63-72`. UE 5.8.2.

#### GAS-05 — do not describe `NonInstanced` as removed in 5.5

- **Priority:** P1 — version/API correctness; the current gotcha overstates removal and hides the 5.8 compatibility behavior that affects state and replication choices.
- **Locations:** `SKILL.md:296-297` and `SKILL.md:313-315`.
- **Finding:** UE 5.8.2 still declares `EGameplayAbilityInstancingPolicy::NonInstanced`, marked `UE_DEPRECATED_FORGAME(5.5)`. `UGameplayAbility::GetInstancingPolicy()` maps it to `InstancedPerActor` unless the compatibility CVar `AbilitySystem.Fix.AllowNonInstancedAbilities` is enabled. The recommendation to avoid it is sound, but “removed” is false and should not be presented as an enum/API removal.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-ability-system/SKILL.md
+++ b/skills/core/gameplay-ability-system/SKILL.md
@@
-- **`NonInstanced` removed in 5.5** — `UE_DEPRECATED_FORGAME(5.5, ...)` in 5.8; use
-  `InstancedPerActor` as the default.
+- **`NonInstanced` policy deprecated, not removed** — UE 5.8.2 still declares the enum but marks
+  it `UE_DEPRECATED_FORGAME(5.5)`. Unless the compatibility CVar
+  `AbilitySystem.Fix.AllowNonInstancedAbilities` is enabled, `GetInstancingPolicy()` treats it as
+  `InstancedPerActor`. Use `InstancedPerActor` for persistent state/RPC or replicated ability
+  state; use `InstancedPerExecution` for independent concurrent executions.
@@
-- `NonInstanced` policy deprecated in 5.5; `InstancedPerActor` is the recommended default.
+- `NonInstanced` policy deprecated in 5.5 (still declared in 5.8.2, not removed); use
+  `InstancedPerActor` for persistent state/RPC or replicated ability state and
+  `InstancedPerExecution` for independent executions.
```

- **Practical task benefit:** prevents false “API removed” migrations while still steering new ability code away from the deprecated policy and toward the policy matching its state/replication needs.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/GameplayAbilities/Source/GameplayAbilities/Public/Abilities/GameplayAbilityTypes.h:37-55` (`EGameplayAbilityInstancingPolicy`); `.../Private/Abilities/GameplayAbility.cpp:34-43,102-117` (`AbilitySystem.Fix.AllowNonInstancedAbilities`, constructor default, and policy mapping). UE 5.8.2.

### No-change checks

- ASC owner/avatar lifetime guidance, `InitAbilityActorInfo`, authority-only `GiveAbility`, attribute callbacks and replication, Gameplay Effect duration/modifier semantics, component-based GE authoring, cost/cooldown commit ordering, ability-task factories and cleanup, Gameplay Cue tags/routing, and the `Checked` → `Ensured` deprecation note remain applicable after the targeted corrections.
- `HandleGameplayEvent` traverses direct parent tags and broadcasts event delegates after attempting triggered abilities; the report does not recommend changing that established event model.
- No exact GAS entries were found in the fetched 5.8.1 or 5.8.2 hotfix notes under the searched `Gameplay Ability`, `GameplayAbilities`, `Gameplay Effect`, `AbilitySystem`, `GAS`, and `Gameplay Cue` terms. The 5.8 release-note changes above are therefore the actionable GAS upgrade items identified here; this is not a claim that every hotfix subsystem fix was runtime-tested.

### Unresolved questions / verification gaps

- No UE 5.8.2 project was compiled with `GameplayAbilities`, and no UHT/generated-code, Blueprint ability, PIE, dedicated-server, prediction-reconciliation, replication-mode, or cooked client/server run was performed.
- The `RemovalPolicy` recommendation was declaration/editor-validation/source verified; no active-effect stack scenario was run to observe matching-effect query behavior or designer asset-validation UI.
- The active-effect-handle migration was source/release-note verified; no custom integration using handles was compiled, and no lifetime test observed the weak owning-ASC result after removal.
- Official GAS conceptual pages linked by the repository were not treated as version-specific API authority where their page metadata could not be independently checked in this pass; the actionable API claims above use the installed UE 5.8.2 source and the versioned 5.8 release notes.

---

## core/gameplay-architecture-planning

**Status:** findings  
**Repository path:** `skills/core/gameplay-architecture-planning/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/gameplay-ability-system`, before `skills/core/logging-and-assertions`

**Files reviewed:**

- `skills/core/gameplay-architecture-planning/SKILL.md`
- `skills/core/gameplay-architecture-planning/references/decision-matrices.md`

### Verified recommendations

#### ARCH-01 — classify the message-bus option instead of implying a built-in subsystem

- **Priority:** P1 — architecture/API correctness; a planning agent may invent or depend on a `UGameplayMessageSubsystem` that is not present in the installed UE 5.8.2 source, or may silently introduce an experimental plugin as if it were a stable core service.
- **Locations:** `SKILL.md:42-48,72-74,195-196`; `references/decision-matrices.md:57-69` (especially the “Decoupled local feature broadcast by tag” row).
- **Finding:** “Gameplay Messages” is listed as a generic communication choice without naming its provider or stability. A source scan of the installed UE 5.8.2 Engine found no `UGameplayMessageSubsystem`, `GameplayMessageSubsystem`, or `FGameplayMessage` API. UE 5.8 does ship `Engine/Plugins/Experimental/AsyncMessageSystem`, but its module is disabled by default and marked experimental; its concrete type is `FAsyncGameplayMessageSystem`, not the commonly named Gameplay Message Subsystem.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-architecture-planning/references/decision-matrices.md
+++ b/skills/core/gameplay-architecture-planning/references/decision-matrices.md
@@
-| Decoupled local feature broadcast by tag | Gameplay Message Subsystem when already adopted | Introducing it for a single direct relationship |
+| Decoupled local feature broadcast by tag | An existing project message bus or an explicitly selected plugin | Assuming UE 5.8 provides a stable `UGameplayMessageSubsystem`, or introducing a bus for one direct relationship |
@@
 Document event order and teardown. A good communication map answers what happens if the receiver
 does not yet exist, the asset is still loading, the sender is destroyed, or a client joins late.
+“Gameplay Messages” is not a stable built-in API name to use in a UE 5.8.2 plan. The installed
+engine’s `AsyncMessageSystem` plugin is **Experimental**, disabled by default, and exposes
+`FAsyncGameplayMessageSystem`; select and validate that plugin explicitly before making it an
+architecture dependency. Otherwise name the project’s actual bus or use a direct/interface/
+delegate boundary.
```

- **Practical task benefit:** stops architecture plans from depending on a nonexistent or unstated message API and makes the plugin/stability decision visible before implementation.
- **Verified evidence:** installed UE 5.8.2 source scan found no `UGameplayMessageSubsystem`, `GameplayMessageSubsystem`, or `FGameplayMessage`; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/AsyncMessageSystem/AsyncMessageSystem.uplugin:12-22` (`EnabledByDefault=false`, `IsExperimentalVersion=true`, module `AsyncMessageSystem`); `.../Source/AsyncMessageSystem/Public/AsyncGameplayMessageSystem.h:14-30` (`FAsyncGameplayMessageSystem`). No matching Async Message entry was found in the fetched [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8); the classification is installed-descriptor/source verified, not release-note documented.

#### ARCH-02 — add the UE 5.8 MassCore/MassSignals planning boundary

- **Priority:** P2 — practical module planning; a data-oriented design selected from the current “Mass” label can otherwise pull in the broad stack or retain a deprecated header/dependency when only core entity functionality is needed.
- **Locations:** insertion after `SKILL.md:72-74` in the framework-commitments question list and after `references/decision-matrices.md:104` in the data/architecture guidance.
- **Finding:** UE 5.8’s release notes split core entity functionality into a new `MassCore` module and make Mass Signals core; the installed source marks `MassEntityMacros.h` deprecated and directs consumers to `Mass/EntityMacros.h` from `MassCore`. The planning skill mentions Mass but does not tell an agent to distinguish the minimum module boundary or the changed include.
- **Exact proposed addition:**

```diff
--- a/skills/core/gameplay-architecture-planning/SKILL.md
+++ b/skills/core/gameplay-architecture-planning/SKILL.md
@@
 - Existing framework commitments such as GAS, CommonUI, Gameplay Messages, Mass, or a project
   plugin architecture.
+- If Mass is a candidate in UE 5.8, whether the design needs only `MassCore` entity primitives,
+  `MassSignals`, or the broader `Mass`/`MassGameplay` stack; include the chosen modules and
+  thread/scheduling assumptions in the plan.
```

```diff
--- a/skills/core/gameplay-architecture-planning/references/decision-matrices.md
+++ b/skills/core/gameplay-architecture-planning/references/decision-matrices.md
@@
 | Runtime state | Plain/USTRUCT/UObject/component state | Do not mutate shared definition assets |
 | Disk persistence | SaveGame or external profile/backend | Requires schema versioning and migration policy |
+| Large-scale homogeneous simulation | MassCore/MassEntity/MassGameplay as required by the design | Extra module/plugin surface and thread/scheduling constraints; do not choose the broad stack without a scale requirement |
@@
 Define the seam precisely: base class, exposed properties, callable functions, implementable
 events, assignable delegates, and which side owns the invariant. Avoid duplicating the same rule
 in C++ and Blueprint.
+
+For UE 5.8 Mass plans, prefer the smallest module set that owns the required API. The old
+`MassEntityMacros.h` include is a deprecated compatibility header; use `Mass/EntityMacros.h`
+from `MassCore` for new code. Treat off-game-thread entity creation and sparse/virtual fragments
+as design assumptions to validate in a representative prototype, not as a generic replacement
+for Actor/Component architecture.
```

- **Practical task benefit:** gives architecture plans a version-correct Mass dependency decision and prevents broad data-oriented adoption without a demonstrated scale need.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), cached lines 1079-1091 (Mass overhaul, Mass Signals, `MassCore`); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/MassEntity/Public/MassEntityMacros.h:3-7` (`UE_DEPRECATED_HEADER(5.8)` migration); `.../Source/Runtime/Mass/MassCore/MassCore.Build.cs:7-21`; `.../Source/Runtime/Mass/MassSignals/MassSignals.Build.cs:5-21`. UE 5.8.2.

### No-change checks

- The Actor/Component/Game Framework/Subsystem lifetime matrix, authority placement, PlayerState-versus-Pawn rule, GameMode server-only rule, C++/Blueprint seam guidance, soft-reference loading distinction, SaveGame separation, and Fast Array “measure before adding” rule match the installed UE 5.8.2 class/module declarations.
- The skill’s instruction to inspect the existing project and avoid speculative abstractions is retained; no framework is recommended merely because UE 5.8 added it.
- The 5.8.1 and 5.8.2 hotfix notes were checked for architecture, subsystem, Mass, and message-system entries; no additional migration was identified. No 5.8 hotfix text changes the stable Game Framework or Subsystem lifetime rules.

### Unresolved questions / verification gaps

- No project architecture, `.uproject` plugin list, Build.cs graph, network topology, or save schema was available for project-specific recommendations.
- The AsyncMessageSystem descriptor/header was inspected, but no API usage, plugin enablement, tick-group scheduling, thread-safety, or shutdown scenario was compiled or run; it remains an experimental option, not a validated recommendation.
- Mass module declarations and the release-note split were inspected, but no Mass processor/entity workload, off-thread creation test, or performance measurement was run. The report does not claim that every Mass feature is safe for an arbitrary project.

## core/gameplay-framework

**Status:** findings  
**Repository path:** `skills/core/gameplay-framework/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/gameplay-architecture-planning`, before `skills/core/logging-and-assertions`

**Files reviewed:**

- `skills/core/gameplay-framework/SKILL.md`
- `skills/core/gameplay-framework/references/gamemode-and-state.md`
- `skills/core/gameplay-framework/references/controllers-and-pawns.md`
- `skills/core/gameplay-framework/references/init-and-login-flow.md`

### Verified recommendations

#### FRAMEWORK-01 — correct match-state ownership in the deep reference

- **Priority:** P1 — API/replication correctness; an implementation agent could look for a replicated `MatchState` on the server-only GameMode or pair the wrong class when the client-visible property belongs to GameState.
- **Locations:** `references/gamemode-and-state.md:70-91`; the main summary at `SKILL.md:35-36,51-54` is already directionally correct.
- **Finding:** the reference says `AGameMode` adds a replicated `FName MatchState`. UE 5.8.2 declares `AGameMode::MatchState` as `UPROPERTY(Transient)` and server-side state-machine storage; `AGameState::MatchState` is the `ReplicatedUsing=OnRep_MatchState` client-visible mirror. The pairing recommendation later in the same paragraph is correct, but the first sentence is not.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-framework/references/gamemode-and-state.md
+++ b/skills/core/gameplay-framework/references/gamemode-and-state.md
@@
-`AGameMode` adds a replicated `FName MatchState` (`GameMode.h`:69) and a state machine that
-drives it. Valid states are constants in the `MatchState` namespace (`GameMode.h`:16–27):
+`AGameMode` adds a transient, server-side `FName MatchState` (`GameMode.h`:67–69) and a state
+machine that drives it. `AGameState` mirrors the value in its replicated
+`MatchState` property (`GameState.h`:33–35) and calls `OnRep_MatchState` on clients. Valid states
+are constants in the `MatchState` namespace (`GameMode.h`:16–27):
```

- **Practical task benefit:** makes the server-authoritative state machine and client replication path explicit, preventing invalid client reads or edits against GameMode.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/GameFramework/GameMode.h:65-79` (`AGameMode::MatchState`, `SetMatchState`, `K2_OnSetMatchState`); `.../Classes/GameFramework/GameState.h:28-39,53-68` (`AGameState::MatchState`, `ReplicatedUsing=OnRep_MatchState`, `ElapsedTime`). UE 5.8.2. Epic comparison: [Game Mode and Game State](https://dev.epicgames.com/documentation/unreal-engine/game-mode-and-game-state-in-unreal-engine) and [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8).

#### FRAMEWORK-02 — qualify PlayerState “always relevant” with UE 5.8 Iris prioritization

- **Priority:** P2 — scale/replication clarity; “always relevant” is still the relevancy rule, but readers can incorrectly infer that every PlayerState is sent every frame without Iris scheduling/budget effects.
- **Locations:** `references/controllers-and-pawns.md:113-119`; add the same qualification to the PlayerState role row at `SKILL.md:37-39` or keep the reference as the single detailed source.
- **Finding:** UE 5.8.2 still constructs `APlayerState` with `bAlwaysRelevant=true`, so the existing ownership guidance is not removed. UE 5.8 release notes also state that PlayerStates are prioritized with `NetObjectCountLimiter` by default; the installed `BaseEngine.ini` defines `PlayerStatePrioritizer`, and its config favors the owning connection. The reference should distinguish relevancy from replication prioritization and preserve the “keep it lean” advice.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-framework/references/controllers-and-pawns.md
+++ b/skills/core/gameplay-framework/references/controllers-and-pawns.md
@@
-`APlayerState` is always relevant (never culled) on all clients; keep it lean. Use it for:
+`APlayerState` sets `bAlwaysRelevant=true`, so it is not distance-culled by the normal actor
+relevancy test; keep it lean. With Iris in UE 5.8.2, the default `PlayerStatePrioritizer` uses a
+`NetObjectCountLimiter` configuration to prioritize PlayerState updates (including an owning-
+connection fast lane). Prioritization/budgeting is separate from the always-relevant rule and
+does not make per-frame or per-property replication free. Use it for:
```

- **Practical task benefit:** preserves the correct PlayerState lifetime/relevancy choice while making the 5.8 network-budget behavior visible for large player counts.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), cached line 7426; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/PlayerState.cpp:20-34` (`bAlwaysRelevant=true`); `.../Engine/Config/BaseEngine.ini:1495` (`PlayerStatePrioritizer` definition); `.../Engine/Source/Runtime/Engine/Public/GameFramework/PlayerStateCountLimiterConfig.h:8-24` and `.../Private/GameFramework/PlayerStateCountLimiterConfig.cpp:7-15`. UE 5.8.2.

### No-change checks

- GameModeBase/GameMode and GameStateBase/GameState hierarchy, server-only GameMode rule, PlayerState/Pawn lifetime split, controller possession override points, `OnPostLogin` replacement for deprecated `DispatchPostLogin`, `RestartPlayer` flow, `UGameInstance` lifetime, subsystem access, default-class properties, `AHUD` legacy status, and Enhanced Input preference remain applicable.
- `AController::Possess`/`UnPossess` remain final in the installed 5.8.2 header; `OnPossess`/`OnUnPossess` and pawn-side `PossessedBy`/`UnPossessed` remain the extension points.
- The 5.8 release-note and fetched 5.8.1/5.8.2 hotfix searches found no additional GameMode, GameState, login, possession, or HUD API migration requiring a recipe beyond the two qualifications above.

### Unresolved questions / verification gaps

- No multiplayer PIE, dedicated-server, reconnect, seamless-travel, spectator, or respawn scenario was executed; login ordering and PlayerState persistence are source-reviewed only.
- The Iris PlayerState prioritizer configuration was read from engine config/source, but no connection with a constrained replication budget was run to observe update scheduling or late-join behavior.
- No project `.ini`/`.uproject` was available, so per-project GameMode overrides, custom net drivers, online subsystem login, and target-specific Iris settings remain unverified.


## core/gameplay-tags

**Status:** findings  
**Repository path:** `skills/core/gameplay-tags/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/gameplay-framework`, before `skills/core/importing-content`

**Files reviewed:**

- `skills/core/gameplay-tags/SKILL.md`
- `skills/core/gameplay-tags/references/native-tags.md`
- `skills/core/gameplay-tags/references/containers-and-queries.md`
- `skills/core/gameplay-tags/references/tag-driven-patterns.md`

### Verified recommendations

#### TAGS-01 — narrow the “no runtime tags” statement and preserve Fast Replication safety

- **Priority:** P1 — API/replication correctness; the current mental model overstates an engine restriction and can lead agents to reject legitimate late native-tag registration or, worse, add tags after a fast-replication dictionary is assumed stable.
- **Locations:** `SKILL.md:29-40`; `references/native-tags.md:37-45`; the fast-replication caveat at `references/containers-and-queries.md:137-147` should remain the single serialization warning.
- **Finding:** `RequestGameplayTag` only looks up an existing dictionary entry, so ordinary gameplay code cannot invent a tag by requesting an arbitrary name. However, UE 5.8.2 still exposes `UGameplayTagsManager::AddNativeGameplayTag`, whose source comment explicitly permits adding after initial startup with default settings while warning that it can invalidate `FastReplication`. The statement that tags cannot be created at runtime and that all post-lock additions are simply unsafe is too absolute; distinguish ordinary lookup, native registration, and replicated-dictionary stability.
- **Exact proposed replacement:**

```diff
--- a/skills/core/gameplay-tags/SKILL.md
+++ b/skills/core/gameplay-tags/SKILL.md
@@
- Tags are registered once (at module load for native; at ini/DataTable load for config)
-  before gameplay begins. You cannot create arbitrary runtime tags.
+ `RequestGameplayTag` only looks up the registered dictionary; it does not create an arbitrary
+ tag. Native/module code can explicitly call `UGameplayTagsManager::AddNativeGameplayTag` after
+ initial startup, but late additions can invalidate `FastReplication` and should not be used to
+ grow replicated gameplay vocabulary during play. Treat project/config/DataTable tags as a
+ startup-loaded dictionary and register macro-defined native tags at file scope in a `.cpp`.
```

```diff
--- a/skills/core/gameplay-tags/references/native-tags.md
+++ b/skills/core/gameplay-tags/references/native-tags.md
@@
 The tag dictionary lock (`DoneAddingNativeTags`, `GameplayTagsManager.h`:412)
-is called during engine startup after all module constructors have run. After that point,
-adding new native tags is unsafe.
+is called during engine startup after the normal native-tag registration window. Macro-defined
+native tags still belong at file scope in a `.cpp`; for an intentional late registration, the
+public `AddNativeGameplayTag` API is available, but its UE 5.8 contract warns that it can
+invalidate `FastReplication`. Do not add late replicated vocabulary unless the project has
+chosen a compatible dictionary/replication strategy.
```

- **Practical task benefit:** prevents a false “impossible” diagnosis while keeping the important network-dictionary constraint and file-scope macro rule visible.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/GameplayTags/Classes/GameplayTagsManager.h:367-375` (`RequestGameplayTag` lookup contract), `395-412` (`AddNativeGameplayTag` and `DoneAddingNativeTags`), and `414-429` (startup delegate APIs); `.../Classes/GameplayTagsSettings.h:127-133` (`FastReplication`/`bDynamicReplication`). UE 5.8.2.

#### TAGS-02 — replace the deprecated last-chance native-tag callback in new guidance

- **Priority:** P2 — UE 5.8 deprecation hygiene; code copied from older tag-registration integrations will warn and use the less precise callback when the current manager exposes distinct add/done-registration helpers.
- **Locations:** insertion in `references/native-tags.md` after `:60`; insertion in `SKILL.md` Version notes after `:237`.
- **Finding:** UE 5.8.2 marks `UGameplayTagsManager::OnLastChanceToAddNativeTags()` `UE_DEPRECATED(5.8)` and names `CallOrRegister_OnAddNativeTagsDelegate` as the replacement for registering additional native tags during initialization. The current reference already uses `CallOrRegister_OnDoneAddingNativeTagsDelegate` for code that waits until registration is complete, but it does not explain that this is a different phase.
- **Exact proposed addition:**

```diff
--- a/skills/core/gameplay-tags/references/native-tags.md
+++ b/skills/core/gameplay-tags/references/native-tags.md
@@
 `CallOrRegister_OnDoneAddingNativeTagsDelegate` is at `GameplayTagsManager.h`:429.
+
+If code needs to add native tags during the initialization window, use
+`UGameplayTagsManager::CallOrRegister_OnAddNativeTagsDelegate(...)`. Do not copy the deprecated
+`OnLastChanceToAddNativeTags()` API in UE 5.8. Use the `OnDoneAddingNativeTags` callback above
+when the requirement is to wait until tag registration has finished rather than to add a tag.
--- a/skills/core/gameplay-tags/SKILL.md
+++ b/skills/core/gameplay-tags/SKILL.md
@@
 - The `ClearInvalidTags` setting on `UGameplayTagsSettings` was deprecated in 5.5.
+- `UGameplayTagsManager::OnLastChanceToAddNativeTags()` is deprecated in 5.8; use
+  `CallOrRegister_OnAddNativeTagsDelegate(...)` for initialization-time additions and
+  `CallOrRegister_OnDoneAddingNativeTagsDelegate(...)` when waiting for completion.
```

- **Practical task benefit:** gives migration code the correct UE 5.8 replacement and prevents an “add” callback from being confused with a “done” callback.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/GameplayTags/Classes/GameplayTagsManager.h:410-429`, including `UE_DEPRECATED(5.8)` on `OnLastChanceToAddNativeTags` and the two `CallOrRegister_...` APIs. UE 5.8.2.

### No-change checks

- Native tag macro placement, `FNativeGameplayTag` conversion/lifetime, `FGameplayTagContainer` explicit/parent arrays, exact versus hierarchical matching, empty-`HasAll` semantics, query expression building, `ReplaceTagFast`, `FastReplication`/dynamic replication distinction, and the GAS/tag-driven examples remain applicable to UE 5.8.2.
- `UE_DEFINE_GAMEPLAY_TAG`/`UE_DEFINE_GAMEPLAY_TAG_COMMENT`/`UE_DEFINE_GAMEPLAY_TAG_STATIC` and the `.cpp` static assertion remain present; no macro rewrite is justified.
- The fetched UE 5.8.1 and 5.8.2 hotfix notes had no exact Gameplay Tags/native-tag/serialization hits. The 5.8 release-note scripting entry mentions `FindReferencesByTag` in the Gameplay Tags Toolset, but the installed 5.8.2 source/plugin scan found no matching symbol; it is not promoted to a source-grounded API recommendation here.

### Unresolved questions / verification gaps

- No project tag dictionary, native-tag module load order, fast-replication client/server parity, or packaged network run was tested.
- Late `AddNativeGameplayTag` registration was source-verified but not exercised after `DoneAddingNativeTags`; the interaction with project-specific dictionary loading and live replication remains project/config dependent.
- The release-note `FindReferencesByTag` toolset item could not be mapped to a local 5.8.2 symbol or plugin file, so its exact invocation and availability remain unresolved.


## core/importing-content

**Status:** findings  
**Repository path:** `skills/core/importing-content/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/gameplay-tags`, before `skills/core/landscape-and-foliage`

**Files reviewed:**

- `skills/core/importing-content/SKILL.md`
- `skills/core/importing-content/references/interchange-framework.md`
- `skills/core/importing-content/references/mesh-and-texture-import.md`
- `skills/core/importing-content/references/reimport-and-import-data.md`

### Verified recommendations

#### IMPORT-01 — separate runtime Interchange from the editor-only Interchange plugin

- **Priority:** P1 — packaged-build correctness; the current runtime recipe tells agents to enable an editor-only plugin and can create an invalid target dependency.
- **Locations:** `references/reimport-and-import-data.md:182-195`, especially the step at `:187`.
- **Finding:** UE 5.8.2 exposes the import manager and core translator/factory modules through the runtime Interchange plugin, while the installed `InterchangeEditor.uplugin` declares `InterchangeEditor`, `InterchangeEditorPipelines`, and `InterchangeEditorUtilities` as `Editor` modules restricted to `Editor`/`Program` targets. The reference should not make enabling **Interchange Editor** a packaged-runtime prerequisite. The editor plugin can remain enabled for editor automation; it is not a runtime module dependency.
- **Exact proposed replacement:**

```diff
--- a/skills/core/importing-content/references/reimport-and-import-data.md
+++ b/skills/core/importing-content/references/reimport-and-import-data.md
@@
-1. Enable the **Interchange Framework** and **Interchange Editor** plugins.
+1. Enable the **Interchange Framework** runtime plugin and the translator/factory plugins
+   required by the formats you will import. Enable **Interchange Editor** only for editor
+   import/reimport tooling; its modules are editor-only and are not a packaged-runtime
+   prerequisite.
```

- **Practical task benefit:** avoids putting editor-only modules into a game target and makes the runtime dependency audit format-specific instead of UI-driven.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Interchange/Runtime/Interchange.uplugin:13-23,30-92` declares runtime modules; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Interchange/Editor/InterchangeEditor.uplugin:22-48` declares editor modules with `TargetAllowList` `Editor`/`Program`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Interchange/Engine/Public/InterchangeManager.h:647-694` exposes `ImportAsset`/`ScriptedImportAssetAsync` for the manager. UE 5.8.2.

#### IMPORT-02 — document UE 5.8 OpenUSD Interchange support with its experimental boundary

- **Priority:** P1 — feature-discovery and stability correctness; the supported-format table omits a practical UE 5.8 import path and does not distinguish asset import from level import or plugin maturity.
- **Locations:** `SKILL.md:67-78,261-269`; `references/interchange-framework.md:7-18,56-80`.
- **Finding:** The UE 5.8 release notes state that USD through Interchange is production ready for asset import and experimental for level import, and add schema-handler ordering, custom schema translators, render contexts, Nanite build settings, groom attributes, collapsing, and Chaos Cloth. The installed optional `InterchangeOpenUSD` plugin is disabled by default and marked `IsExperimentalVersion: true`; its runtime module is `InterchangeOpenUSDImport`, with `UInterchangeUSDTranslator` and `UInterchangeUsdPipeline` in source. Add USD to the format map, but keep the optional-plugin and level-import qualification explicit. The 5.8.1 hotfix fixes incorrect MaterialX primvar baking for referenced MaterialX materials through Interchange USD; the 5.8.2 hotfix fixes MaterialX materials being shared across targets on USD Pregen imports. Those fixes support using 5.8.2, not declaring USD Pregen production-ready.
- **Exact proposed additions:**

```diff
--- a/skills/core/importing-content/SKILL.md
+++ b/skills/core/importing-content/SKILL.md
@@
-| Scene / level import | FBX, glTF, GLB, MaterialX | FBX scene legacy |
+| Scene / level import | FBX, glTF, GLB, MaterialX, USD* | FBX scene legacy |
+
+`*` UE 5.8 release notes characterize USD asset import as production ready and USD level
+import as experimental. The installed `InterchangeOpenUSD` plugin is optional and marked
+experimental, so enable and validate it explicitly rather than treating USD as a universally
+enabled built-in translator.
@@
 - `UInterchangeFbxTranslatorSettings::bUseUfbxParser` (still experimental in 5.8) enables the
   ufbx SDK instead of the Autodesk FBX SDK — useful for open-source builds.
+- UE 5.8 adds/extends OpenUSD Interchange asset import. `UInterchangeUSDTranslator` and
+  `UInterchangeUsdPipeline` are supplied by the optional experimental `InterchangeOpenUSD`
+  plugin; asset import is the supported path, while level import and USD Pregen remain
+  experimental. The 5.8.1 and 5.8.2 hotfix notes include USD/MaterialX fixes; re-test those
+  workflows on the pinned hotfix rather than inferring parity from the editor UI.
--- a/skills/core/importing-content/references/interchange-framework.md
+++ b/skills/core/importing-content/references/interchange-framework.md
@@
 | `InterchangeEditor` | `Engine/Plugins/Interchange/Editor/Source/InterchangeEditor/` | Editor-side pipeline dialog, preview window |
+| `InterchangeOpenUSDImport` | `Engine/Plugins/Interchange/Extensions/OpenUSD/Source/Import/` | Optional experimental `UInterchangeUSDTranslator`, `UInterchangeUsdPipeline` for USD asset/scene import |
```

- **Practical task benefit:** lets an agent choose USD for asset import when authorized, avoids silently enabling an experimental level/Pregen path, and surfaces the 5.8.1/5.8.2 hotfix relevance.
- **Verified evidence:** [UE 5.8 Release Notes — USD Import with Interchange](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), lines 1542-1564 in the fetched page; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Interchange/Extensions/OpenUSD/InterchangeOpenUSD.uplugin:5-18,23-33` (`EnabledByDefault: false`, `IsExperimentalVersion: true`, runtime/editor modules); `.../Source/Import/Public/InterchangeUsdTranslator.h:61-69,171-197` (`UInterchangeUsdTranslatorSettings`, `UInterchangeUSDTranslator`); `.../Source/Import/Public/InterchangeUSDPipeline.h:13-16,64-75` (`UInterchangeUsdPipeline`); [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), Interchange USD/MaterialX fix; [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335), USD Pregen MaterialX sharing fix. UE 5.8.2 source/hotfix material.

#### IMPORT-03 — use the non-deprecated scene factory-node accessor

- **Priority:** P2 — migration/compiler hygiene; scene-reimport automation copied from pre-5.8 code will compile through a deprecated wrapper and obscure the current API.
- **Locations:** insertion in `references/reimport-and-import-data.md` after `:136` (the alternate-source reimport example), or in a new scene-reimport subsection before `:138`.
- **Finding:** `UInterchangeSceneImportAsset::GetFactoryNode(...)` overloads are marked `UE_DEPRECATED(5.8)` and forward to `GetFactoryNodeFromPath(...)`. The importing references describe scene and factory-node workflows but do not name this 5.8 migration.
- **Exact proposed addition:**

```diff
--- a/skills/core/importing-content/references/reimport-and-import-data.md
+++ b/skills/core/importing-content/references/reimport-and-import-data.md
@@
 Mgr.ImportAsset(TEXT("/Game/Meshes"), NewSrc, Params);
 ```
+
+For scene-import readback, replace the deprecated UE 5.8
+`UInterchangeSceneImportAsset::GetFactoryNode(...)` overloads with
+`GetFactoryNodeFromPath(...)` (or `GetFactoryNodeFromUniqueID(...)` when the node UID is the
+authoritative key).
```

- **Practical task benefit:** removes deprecation warnings from scene-reimport tools and makes the lookup key explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Interchange/Engine/Public/InterchangeSceneImportAsset.h:69-98` marks both `GetFactoryNode` overloads `UE_DEPRECATED(5.8)` and exposes `GetFactoryNodeFromPath`/`GetFactoryNodeFromUniqueID`. UE 5.8.2.

### No-change checks

- Interchange’s translator → pipeline → factory model, `FImportAssetParameters::ReimportAsset` being an object (`TObjectPtr<UObject>`), synchronous `ImportAsset` overloads, asynchronous `ImportAssetAsync`/`ReimportAssetAsync` result handling, `FImportResult::OnDone`, `CanReimport`, `UInterchangeAssetImportData`, legacy FBX import-data distinction, `bIsAutomated`, `OverridePipelines`, mesh/texture property names/defaults, collision prefixes, sRGB/compression rules, UDIM setting, and experimental uFBX labeling remain source-compatible with UE 5.8.2.
- The installed source confirms `UInterchangeGenericMeshPipeline::bBuildNanite = true`, `bGenerateLightmapUVs = false`, `bCollision = true`, `CombineStaticMeshesBehavior = DoNotCombine`, `UInterchangeGenericTexturePipeline::bImportUDIMs = true`, and `UInterchangeFbxTranslatorSettings::bUseUfbxParser = false`; no default-value rewrite beyond the scoped additions is justified.
- The fetched [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8) add the Interchange import-dialog UI rework and experimental uFBX stabilization. The 5.8.1/5.8.2 hotfix items are captured above; they do not justify claiming a general reimport API rewrite.

### Unresolved questions / verification gaps

- No source asset was imported, reimported, cooked, or opened in an actual UE 5.8.2 project; no created-asset count, package dirtiness, skeleton preservation, texture color-space result, or rendered output was measured.
- Runtime Interchange format coverage remains target/plugin/config dependent; no packaged runtime exercised translator inclusion or the additional cook-content requirement.
- OpenUSD plugin files and declarations were inspected, but no USD asset, level import, USD Pregen graph, schema-handler reorder, MaterialX scene, or hotfix regression case was run. Marketplace/vendor importer behavior was not inspected.
- No legacy-to-Interchange conversion was executed; `RegisterImportDataConverter`/`ConvertImportData` declarations were source-verified, not runtime-proven.

---



## core/landscape-and-foliage

**Working-tree reconciliation:** read the revised target-layer/weight-sampling guidance and added spline/persistence paragraph. UE 5.8.2 `Engine/Source/Runtime/Landscape/Classes/LandscapeProxy.h` declares `FLandscapeTargetLayerSettings`, `TargetLayers`, and deprecated `FLandscapeEditorLayerSettings`; this supports the direction of the current edit. LAND-03 still applies to the separate `references/landscape.md` example, not the already-corrected main-skill receiver name. The claimed save/reopen and exact-restoration observations were not repeated; spline transforms, signed tangents, service-region partial writes and rollback remain **partially verified** integration claims. No additional replacement is proposed without matching execution evidence.

**Status:** findings  
**Repository path:** `skills/core/landscape-and-foliage/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/importing-content`, before `skills/core/levels-and-world-partition`

**Files reviewed:**

- `skills/core/landscape-and-foliage/SKILL.md`
- `skills/core/landscape-and-foliage/references/landscape.md`
- `skills/core/landscape-and-foliage/references/foliage-and-hism.md`
- `skills/core/landscape-and-foliage/references/pcg.md`

### Verified recommendations

#### LAND-01 — correct the inconsistent 8129 landscape-size example

- **Priority:** P1 — authoring/import correctness; the current sentence pairs a 8129×8129 heightmap with component parameters that mathematically produce 8065×8065, which can send an agent to import or create an invalid-size landscape.
- **Locations:** `SKILL.md:58-65`; the matching formula and 4033 example at `references/landscape.md:10-29` are already internally consistent.
- **Finding:** With 32 components, 4 subsections per component, and 63 quads per subsection, one axis is `32 × 4 × 63 = 8064` quads and therefore `8065` vertices. A 8129×8129 landscape uses 32 components, 2 subsections per component, and 127 quads per subsection. Keep both examples, but do not attach the wrong parameter tuple to 8129.
- **Exact proposed replacement:**

```diff
--- a/skills/core/landscape-and-foliage/SKILL.md
+++ b/skills/core/landscape-and-foliage/SKILL.md
@@
-Common valid size: 8129 × 8129 vertices
-(32 × 32 components, 4 sections/component, 63 quads/section). Heights are stored as 16-bit
-values mapping to ±256 m at default Z scale 100.
+For example, 32 × 32 components with 4 sections/component and 63 quads/section produce
+8065 × 8065 vertices (`32 × 4 × 63 + 1`). The also-common 8129 × 8129 size uses
+32 × 32 components with 2 sections/component and 127 quads/section. Heights are stored as
+16-bit values mapping to ±256 m at default Z scale 100.
```

- **Practical task benefit:** prevents a concrete heightmap/component mismatch while preserving the valid-size rule.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Landscape/Classes/LandscapeProxy.h:924-930` exposes `ComponentSizeQuads`, `SubsectionSizeQuads`, and `NumSubsections`; [Landscape Technical Guide](https://dev.epicgames.com/documentation/unreal-engine/landscape-technical-guide-in-unreal-engine) supplies the valid-size convention. UE 5.8.2; arithmetic independently evaluated as 8064+1 and 8128+1.

#### LAND-02 — replace the deprecated singular Landscape Nanite-component wording

- **Priority:** P1 — API/migration correctness; UE 5.8.2 marks the singular serialized property deprecated and stores Nanite components in an array.
- **Locations:** `SKILL.md:88-93`; `references/landscape.md:103-114`.
- **Finding:** `ALandscapeProxy::NaniteComponent` is `UE_DEPRECATED(all, "NaniteComponent has been deprecated, use NaniteComponents instead.")`; the live property is `TArray<TObjectPtr<ULandscapeNaniteComponent>> NaniteComponents`. The conceptual statement that Nanite landscape support creates a component is understandable, but source/API guidance should name the array and not teach the old member.
- **Exact proposed replacement:**

```diff
--- a/skills/core/landscape-and-foliage/SKILL.md
+++ b/skills/core/landscape-and-foliage/SKILL.md
@@
-Set `bEnableNanite = true` on the `ALandscapeProxy` to render the landscape as a Nanite
-mesh on supported platforms. The engine generates and maintains a `ULandscapeNaniteComponent`
-alongside the traditional LOD components. LOD settings under `NaniteLODIndex` control the
-source LOD used for Nanite mesh generation (default 0). See `nanite-and-rendering`.
+Set `bEnableNanite = true` on the `ALandscapeProxy` to render the landscape as a Nanite
+mesh on supported platforms. The engine stores generated Nanite components in the proxy's
+`NaniteComponents` array alongside the traditional LOD components; the legacy singular
+`NaniteComponent` property is deprecated. `NaniteLODIndex` controls the source LOD used for
+Nanite mesh generation (default 0). See `nanite-and-rendering`.
--- a/skills/core/landscape-and-foliage/references/landscape.md
+++ b/skills/core/landscape-and-foliage/references/landscape.md
@@
-1. Generates a `ULandscapeNaniteComponent` (`LandscapeNaniteComponent.h`) at the LOD
-   specified by `NaniteLODIndex` (usually 0 for highest detail).
+1. Generates/maintains entries in `ALandscapeProxy::NaniteComponents`
+   (`LandscapeProxy.h`; the singular `NaniteComponent` property is deprecated) at the LOD
+   specified by `NaniteLODIndex` (usually 0 for highest detail).
```

- **Practical task benefit:** prevents new code or asset tooling from binding to the deprecated singular property and makes multi-component handling explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Landscape/Classes/LandscapeProxy.h:489-503,691-696` — `bEnableNanite`, editor settings, `NaniteComponent_DEPRECATED`, and `NaniteComponents`. UE 5.8.2.

#### LAND-03 — fix the landscape layer-weight example’s receiver type

- **Priority:** P1 — compile/API correctness; the reference calls `GetLayerWeightAtLocation` on `ULandscapeInfo`, but UE 5.8.2 declares that method on `ULandscapeComponent`.
- **Locations:** `references/landscape.md:118-141`, especially `:132-135`.
- **Finding:** `ULandscapeInfo` exposes component maps and `ForAllLandscapeComponents`, but no `GetLayerWeightAtLocation`. `ULandscapeComponent::GetLayerWeightAtLocation(...)` is the source API. Its component map is documented as valid in editor only, while `ALandscapeProxy::GetHeightAtLocation` and collision tracing are the runtime-safe height paths. The example must not present the current `Info->...` call as compilable runtime C++.
- **Exact proposed replacement:**

```diff
--- a/skills/core/landscape-and-foliage/references/landscape.md
+++ b/skills/core/landscape-and-foliage/references/landscape.md
@@
-        // Layer weight sampling requires ULandscapeInfo::GetLayerWeightAtLocation
-        // (available in editor; limited at runtime without cook-time bake).
-        float Weight = Info->GetLayerWeightAtLocation(WorldLoc, LayerInfoObj);
+        // ULandscapeInfo has no GetLayerWeightAtLocation in UE 5.8.2. In an editor
+        // inspection, resolve the containing ULandscapeComponent (for example through
+        // Info->XYtoComponentMap) and call its API instead:
+        // float Weight = Component->GetLayerWeightAtLocation(WorldLoc, LayerInfoObj);
+        // XYtoComponentMap is editor-only; for runtime gameplay, bake the needed layer
+        // data or use a supported runtime query such as landscape collision/physical material.
```

- **Practical task benefit:** prevents a compile failure and stops an editor-only layer map from being presented as a packaged-runtime query.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Landscape/Classes/LandscapeComponent.h:1262` declares `ULandscapeComponent::GetLayerWeightAtLocation`; `.../Private/LandscapeEdit.cpp:2816-2828` implements it; `.../Classes/LandscapeInfo.h:187-191` documents `XYtoComponentMap` as editor-only and keeps `XYtoCollisionComponentMap` valid; `.../Classes/LandscapeProxy.h:1101-1105` exposes runtime height/physical-material queries. UE 5.8.2.

#### LAND-04 — expose the UE 5.8 actor/component-less PCG mode as experimental

- **Priority:** P2 — scoped 5.8 feature discovery; runtime PCG users can avoid partition actors/local PCG components, but the source marks the mode experimental and documents unsupported target-actor/component-dependent functionality.
- **Locations:** insertion in `SKILL.md` Version notes after `:272`; insertion in `references/pcg.md` after `:164`.
- **Finding:** UE 5.8 release notes list actor/component-less runtime generation among the PCG performance changes. UE 5.8.2 exposes `UPCGComponent::UseActorComponentlessGeneration()` and the advanced `bUseActorComponentlessGeneration` override, explicitly marked `[EXPERIMENTAL]`. Add it as an opt-in alternative, not as a replacement for partitioned generation, and record that actor/component-dependent nodes are unsupported in this mode.
- **Exact proposed addition:**

```diff
--- a/skills/core/landscape-and-foliage/SKILL.md
+++ b/skills/core/landscape-and-foliage/SKILL.md
@@
 - `UPCGComponent.GenerationTrigger = GenerateAtRuntime` enables the runtime generation
   scheduler (new in 5.3+; scheduler policy expanded in 5.6/5.7).
+- UE 5.8 exposes experimental actor/component-less runtime generation through the PCG
+  component/graph advanced settings (`bUseActorComponentlessGeneration`, queried by
+  `UseActorComponentlessGeneration()`). It avoids partition actors and local PCG components,
+  but nodes that depend on a target actor/component are unsupported; validate the graph before
+  using it in a shipped runtime.
--- a/skills/core/landscape-and-foliage/references/pcg.md
+++ b/skills/core/landscape-and-foliage/references/pcg.md
@@
 For environments that stream at runtime (open world), use `GenerateAtRuntime` with a
 partitioned PCG component on a persistent actor. The `UPCGSubsystem` scheduler handles
 loading/unloading cells as the player moves.
+
+UE 5.8 also exposes an **experimental** actor/component-less runtime mode in the advanced
+component/graph settings (`bUseActorComponentlessGeneration`). Query the effective mode with
+`UPCGComponent::UseActorComponentlessGeneration()`. It avoids partition actors and local
+components, but functionality that requires a target actor/component is not supported.
```

- **Practical task benefit:** gives open-world runtime teams a version-matched memory/actor-overhead option while preserving a clear experimental stop gate.
- **Verified evidence:** [UE 5.8 Release Notes — PCG Performance](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), lines 982-998 in the fetched page; `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/PCG/Source/PCG/Public/PCGComponent.h:304-305,845-851` (`UseActorComponentlessGeneration`, experimental property). UE 5.8.2.

### No-change checks

- Landscape component/section math, edit-layer model, spline ownership, heightmap/material/weightmap concepts, landscape grass, foliage-type hierarchy, HISM batch APIs and translated instance space, procedural-foliage editor-time boundary, PCG graph/settings/element model, `Generate`/`GenerateLocal`/`Cleanup` lifecycle, completion delegates, generation triggers, partitioned generation, managed-resource cleanup, collision/culling cautions, and Nanite material caveats remain applicable after the targeted corrections.
- The installed source confirms `bEnableNanite` defaults false, `NaniteLODIndex` defaults 0, `bNaniteSkirtEnabled` defaults false, `FPCGLandscapeDataProps::bGetLayerWeights` defaults true, and HISM `AddInstances`/`BuildTreeIfOutdated` signatures; no blanket default rewrite is justified.
- The UE 5.8 release notes add PCG manual editing, complex attributes, embedded subgraphs, graph-parameter hierarchy, GPU/runtime performance improvements, and new PCG nodes. These are editor/graph-authoring features rather than a reason to rewrite the existing C++ lifecycle recipe without a project asset test.
- The cached 5.8.1 hotfix fixes a landscape spline-tangent regression, older landscape-foliage loading crash, and several PCG rotation/seed/async-processing issues. The cached 5.8.2 hotfix fixes landscape editor shutdown/foliage cases and a PCG grid-linkage race; no additional stable landscape/foliage API migration was justified. Sources: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No landscape, landscape material/layer asset, foliage map, HISM component, procedural-foliage volume, PCG graph, World Partition cell, or packaged runtime was opened or executed under UE 5.8.2.
- The corrected layer-weight example still requires project-specific component resolution and data availability; no editor query or cooked runtime bake was exercised.
- Experimental actor/component-less PCG generation, GPU sampling, partitioned cleanup, resource ownership, and graph nodes that require actor/component context were not runtime-tested.
- No performance capture measured landscape component count, HISM rebuild cost, foliage culling, PCG graph spikes, or Nanite landscape fallback behavior.

---

## core/levels-and-world-partition

**Status:** findings  
**Repository path:** `skills/core/levels-and-world-partition/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/landscape-and-foliage/` and before `skills/core/logging-and-assertions/`  
**Files reviewed:**
- `skills/core/levels-and-world-partition/SKILL.md`
- `skills/core/levels-and-world-partition/references/world-partition-streaming.md`
- `skills/core/levels-and-world-partition/references/level-instances.md`
- `skills/core/levels-and-world-partition/references/data-layers-and-hlod.md`

### Verified recommendations

#### WP-01 — Correct the HLOD residency description

- **Location:** `skills/core/levels-and-world-partition/references/data-layers-and-hlod.md:113-114`.
- **Priority:** P1 — the current sentence gives the wrong streaming model and can lead teams to assume HLOD memory is permanently resident.
- **Task benefit:** keeps HLOD memory/visibility expectations aligned with World Partition cells and makes debugging a missing HLOD representation tractable.
- **Evidence:** installed UE 5.8.2 `Engine/Source/Runtime/Engine/Public/WorldPartition/HLOD/HLODRuntimeSubsystem.h:50-64` exposes `OnCellShown`, `OnCellHidden`, and `GetHLODObjectsForCell`; `:113-127` stores HLOD data keyed by cell. This is source-verified for the pinned engine. Official UE 5.8 HLOD notes: <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#hlodux>.
- **Proposed replacement:**

```diff
- HLOD proxies live in the *always-loaded* part of the world and are swapped out by the
- actual actors when the corresponding cell activates.
+ HLOD objects are associated with the runtime cell they represent and are shown/hidden with
+ that cell; they are not a universal always-loaded substitute for unloaded source actors.
+ The runtime subsystem exposes `GetHLODObjectsForCell`, `OnCellShown`, and `OnCellHidden`.
+ Validate the generated HLOD cell's runtime hash and streaming range when diagnosing HLOD
+ residency or memory, rather than assuming every HLOD proxy is always resident.
```

#### WP-02 — Add the UE 5.8 World Partition Insights and selection-scoped HLOD workflow

- **Locations:** `skills/core/levels-and-world-partition/SKILL.md:240-264` (version/reference area) and `skills/core/levels-and-world-partition/references/world-partition-streaming.md:101-110` (debug commands).
- **Priority:** P2 — this is a useful 5.8 workflow omission, not an API compatibility break.
- **Task benefit:** gives teams a supported way to correlate per-cell streaming behavior with captures and to rebuild only the selected HLOD region instead of rebuilding the whole world.
- **Evidence:** UE 5.8 release notes add **World Partition Insights** for per-cell analysis/session playback and **Build HLODs for Selection / Selected Region**: <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#worldpartitioninsights> and <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#hlodux>. Installed editor source exposes `SWorldPartitionEditorGrid2D::BuildHLODsForSelection` and `BuildHLODsForSelectedRegions` in `Engine/Source/Editor/WorldPartitionEditor/Public/WorldPartition/SWorldPartitionEditorGrid2D.h:28-31,97-102`, and `IWorldPartitionEditorModule::BuildHLODs` in `Engine/Source/Editor/WorldPartitionEditor/Public/WorldPartitionEditorModule.h:166-169` (UE 5.8.2).
- **Proposed addition:**

```diff
+### UE 5.8 diagnostics and scoped HLOD builds
+
+Use World Partition Insights in Unreal Insights/Editor for per-cell streaming analysis and
+session playback. In the World Partition editor, prefer **Build HLODs for Selection** or
+**Build HLODs for Selected Region** while iterating on a bounded area; use the full HLOD
+build for final world output. These are editor workflows, not runtime C++ APIs.
```

#### WP-03 — Record the pinned hotfix baseline for landscape layers and World Partition cooking

- **Location:** `skills/core/levels-and-world-partition/SKILL.md:230-238`, after the existing version notes.
- **Priority:** P2 — prevents a 5.8.0/5.8.1 editor or cook failure from being misdiagnosed as a World Partition design error.
- **Task benefit:** makes the documented baseline reproducible for CI and editor triage.
- **Evidence:** the official 5.8.2 hotfix announcement lists a fix for a crash when cooking World Partition levels with `basedonreleaseversion`, and the 5.8.1/5.8.2 release material lists World Partition/landscape bug fixes. URLs: <https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335> and <https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864>. This is release-note evidence, not a claim that every project experiences the bug.
- **Proposed addition:**

```diff
+ - Audit and CI results for World Partition cooking should use the pinned UE 5.8.2 hotfix
+   baseline. The 5.8.2 announcement specifically includes a fix for a crash when cooking
+   World Partition levels with `basedonreleaseversion`; landscape-layer editing also has
+   hotfix crash fixes. Do not compare 5.8.0/5.8.1 editor or cook failures with 5.8.2
+   behavior without recording the exact engine build and commandlet arguments.
```

### No-change checks

- `UWorld::GetWorldPartition`, `UWorld::GetDataLayerManager`, `UWorldPartitionStreamingSourceComponent`, `EStreamingSourceTargetState`, `TargetGrids`, `UDataLayerManager::SetDataLayerInstanceRuntimeState`, `EDataLayerRuntimeState`, legacy `ULevelStreaming`, OFPA, `ALevelInstance`, `APackedLevelActor`, and the commandlet-oriented HLOD workflow remain represented by declarations in installed UE 5.8.2 source. No API replacement was justified for those passages.
- The existing `UDataLayerSubsystem` (5.3) and `TargetHLODLayers` (5.4) deprecation notes are retained; `DataLayerManager.h:121-123` and `WorldPartitionStreamingSource.h` confirm the relevant versioned annotations. The inspected 5.8 release notes did not justify duplicating those older migration notes.

### Unresolved questions and verification gaps

- No project was opened, converted, cooked, run in PIE, run on a dedicated server, or captured in Unreal Insights. Cell load latency, HLOD visibility, Data Layer replication, server streaming, OFPA source-control behavior, and Level Instance runtime behavior therefore remain unvalidated beyond declarations and official documentation.
- UE 5.8.2 source also exposes `UExternalDataLayerManager`/external-data-layer actor-descriptor fields (`WorldPartition.h:507-510`, `WorldPartitionActorDesc.h:321-326`), but the fetched 5.8 release-note material did not establish a new stable workflow relevant to this skill. Whether to add an External Data Layer recipe needs a project/content workflow check; it is not promoted here as a verified 5.8-only upgrade.
- The installed editor source confirms selection-scoped HLOD commands, but no editor invocation or output package was exercised. Treat the workflow addition as source/docs verified, not end-to-end validated.

**Source/doc set checked:** installed UE 5.8.2 headers listed above; UE 5.8 release notes; 5.8.1 hotfix page; 5.8.2 hotfix page. No marketplace/vendor plugin evidence was used.

## core/lighting-and-lumen

**Working-tree reconciliation:** read the current exposure replacement and added viewport/post-reload comparison constraints. The main skill now distinguishes compensation from camera EV100 and avoids blindly replacing fixed exposure; preserve that correction. The requirement to hold Game Settings exposure/camera/presentation state constant is useful verification guidance, not a reproduced render test. Existing additions do not resolve every renderer issue discussed below; current file locations shift after these insertions.

**Status:** findings  
**Repository path:** `skills/core/lighting-and-lumen/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/levels-and-world-partition/` and before `skills/core/logging-and-assertions/`  
**Files reviewed:**
- `skills/core/lighting-and-lumen/SKILL.md`
- `skills/core/lighting-and-lumen/references/shadows-and-postprocess.md`
- `skills/core/lighting-and-lumen/references/lumen-gi-and-reflections.md`
- `skills/core/lighting-and-lumen/references/light-components-and-mobility.md`

### Verified recommendations

#### LIGHT-01 — Update MegaLights classification and add Lumen Lite's beta status

- **Locations:** `skills/core/lighting-and-lumen/SKILL.md:227-234` and `skills/core/lighting-and-lumen/references/light-components-and-mobility.md:158-162`.
- **Priority:** P1 — the current version note calls MegaLights experimental after Epic moved it to Production Ready in UE 5.8; it also omits the new Lumen Lite path.
- **Task benefit:** prevents teams from rejecting a supported many-light path because of stale status, while keeping the separate Lumen Lite beta and its platform qualification explicit.
- **Evidence:** UE 5.8 release notes state that MegaLights enters Production Ready and list transmission, froxel translucency, IES, lighting-channel, cloud-shadow, first-person, and visualization support; they introduce **Lumen Lite (Beta)** as an irradiance-field/probe-occlusion medium-quality setting. Official URLs: <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#megalights> and <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#lumenlite(beta)>. Installed UE 5.8.2 source confirms `ULightComponent::bAllowMegaLights` and `MegaLightsShadowMethod` in `Engine/Source/Runtime/Engine/Classes/Components/LightComponent.h:166-179`, and Lumen irradiance-field/probe-occlusion implementation symbols in `Engine/Source/Runtime/Renderer/Private/Lumen/LumenIrradianceFieldGather.cpp:88-108`.
- **Proposed replacement/addition:**

```diff
- - MegaLights (`bAllowMegaLights` on `ULightComponent`, line 171) is a UE5.5+ feature
-   for stochastic many-light rendering; present in 5.8 but still experimental.
+ - MegaLights (`bAllowMegaLights` / `MegaLightsShadowMethod` on `ULightComponent`) is
+   Production Ready in UE 5.8. It adds stochastic many-light lighting with new support for
+   transmission, froxel translucency, IES in volumetrics/translucency, lighting channels,
+   cloud shadows, first-person geometry, and dedicated visualization views. It still needs
+   per-platform and per-scene performance measurement; use the light's opt-in property and
+   project/Post Process settings deliberately.
+ - Lumen Lite is **Beta**, not a universal replacement for the existing Lumen quality paths.
+   It uses Lumen irradiance fields with probe occlusion as a medium-quality GI option and is
+   the new default path for current-generation handheld-console scalability; validate its
+   lighting and performance on each target before shipping.
```

#### LIGHT-02 — Add UE 5.8 experimental Fog Screen Space Scattering without inventing a public C++ recipe

- **Locations:** `skills/core/lighting-and-lumen/SKILL.md:127-139` and `skills/core/lighting-and-lumen/references/shadows-and-postprocess.md:161-168`.
- **Priority:** P2 — this is a scoped 5.8 feature omission; it must remain explicitly experimental.
- **Task benefit:** gives fog-heavy projects a discoverable 5.8 option and states its unsupported volume types before artists spend time tuning it.
- **Evidence:** UE 5.8 release notes describe experimental Fog Screen Space Scattering (FSSS), support for Volumetric Fog and Local Fog Volumes, and lack of Volumetric Cloud/Heterogeneous Volume support: <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#fsss-fogscreenspacescattering(experimental)>. Installed UE 5.8.2 renderer source exposes `FFogUniformParameters::EnableFSSS`, `FSSSSceneColorScatteringAmountScale`, `FSSSSceneColorScatteringAmountPower`, `FSSSSpreadScale`, and `FSSSBlurControl` in `Engine/Source/Runtime/Renderer/Private/FogRendering.h:35-39`, with `RenderFogScreenSpaceScatteringMipChain` in `DeferredShadingRenderer.h:605-608` and its invocation in `DeferredShadingRenderer.cpp:3760-3776`.
- **Proposed addition:**

```diff
+### UE 5.8 FSSS (Experimental)
+
+UE 5.8 adds experimental Fog Screen Space Scattering on the exponential-height-fog
+pipeline. It targets Volumetric Fog and Local Fog Volumes; Volumetric Clouds and
+Heterogeneous Volumes are not supported. Treat the feature as editor/project-setting
+experimentation only: the installed renderer exposes internal FSSS uniform parameters, but
+this skill does not add an unverified public C++ setter or promise artifact-free output.
```

#### LIGHT-03 — Correct the Software Ray Tracing platform requirement

- **Locations:** `skills/core/lighting-and-lumen/SKILL.md:89-93` and `skills/core/lighting-and-lumen/references/lumen-gi-and-reflections.md:35-51`.
- **Priority:** P1 — the current “all DX11+ hardware” statement is incompatible with the version-matched Epic requirement.
- **Task benefit:** prevents a project from selecting Lumen Software Ray Tracing for an unsupported RHI/GPU and then debugging a configuration failure as a content problem.
- **Evidence:** version-matched Epic Lumen Technical Details states Software Ray Tracing requires DirectX 12 with Shader Model 6 and lists the platform support requirements: <https://dev.epicgames.com/documentation/unreal-engine/lumen-technical-details-in-unreal-engine?application_version=5.8#software-ray-tracing>. The UE 5.8 Lumen overview confirms that enabling Lumen enables Generate Mesh Distance Fields for this path: <https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine?application_version=5.8#getting-started-with-lumen>. Installed renderer source exposes `DoesPlatformSupportLumenGI` in `Engine/Source/Runtime/RenderCore/Public/RenderUtils.h:644-649` (UE 5.8.2).
- **Proposed replacement:**

```diff
- - **Software Ray Tracing** — traces against Signed Distance Fields; works on all
-   DX11+ hardware; requires `Generate Mesh Distance Fields` in project settings.
+ - **Software Ray Tracing** — traces against Signed Distance Fields; in UE 5.8's Lumen
+   supported path it requires a DirectX 12 RHI with Shader Model 6 support, not arbitrary
+   DX11 hardware, and requires `Generate Mesh Distance Fields` in project settings.
+   Confirm the target GPU/RHI against Epic's UE 5.8 platform requirements before choosing
+   this path.
```

```diff
-### Software Ray Tracing (SRT)
+### Software Ray Tracing (SRT; UE 5.8 DX12/SM6 requirement)
 - Traces against per-mesh Signed Distance Fields (SDFs) and the Global Distance Field.
-- Supported on any DX11/DX12 GPU (no RT hardware required).
+- Supported on the UE 5.8 Lumen path on DirectX 12 with Shader Model 6; dedicated hardware
+  ray-tracing support is not required, but legacy DX11 is not a supported assumption.
```

### No-change checks

- The `FPostProcessSettings` Lumen fields, override-bit requirement, `AEM_Manual`, `UReflectionCaptureComponent`, light mobility hierarchy, light-function RectLight limitation, VSM controls, and sky/fog component declarations match installed UE 5.8.2 source. No replacement was justified for those passages.
- The version-matched Lumen documentation confirms the existing statements that new projects enable Lumen and dependencies, Static light contributions are disabled for Lumen GI, software tracing needs mesh distance fields, and hardware tracing is the higher-quality but higher-update-cost path.
- The 5.8.1 hotfix material includes a VSM fix for primitives with forced static invalidation and WPO; this does not change the documented VSM API or justify a recipe change. The 5.8.2 hotfix material contained no additional lighting API migration that applies to these files.

### Unresolved questions and verification gaps

- No project, target RHI, GPU, PIE session, packaged build, Lumen visualization, MegaLights visualization, or performance capture was run. All quality/performance claims remain documentation/source grounded, not end-to-end validated.
- FSSS renderer parameters are source-visible, but the editor property/console-variable exposure and final user-facing enablement were not exercised. Do not add a C++ configuration example until that surface is verified in an actual UE 5.8.2 editor build.
- Lumen Lite's scalability integration was identified from the 5.8 release notes and irradiance-field source, but no handheld-console or PC scalability profile was inspected. Its beta behavior and visual parity remain project/target dependent.

**Source/doc set checked:** installed UE 5.8.2 Engine light, scene, renderer, and fog files listed above; version-matched Lumen docs; UE 5.8 release notes; 5.8.1 hotfix page; 5.8.2 hotfix page. No marketplace/vendor plugin evidence was used.

## core/logging-and-assertions

**Status:** findings  
**Repository path:** `skills/core/logging-and-assertions`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/editor-scripting-and-python`, before `skills/core/memory-and-gc`

**Files reviewed:**

- `skills/core/logging-and-assertions/SKILL.md`
- `skills/core/logging-and-assertions/references/assertions.md`
- `skills/core/logging-and-assertions/references/log-categories-and-verbosity.md`
- `skills/core/logging-and-assertions/references/structured-logging.md`

### Verified recommendations

#### LOG-ASSERT-01 — qualify the Shipping assertion table by its build configuration

- **Priority:** P1 — release-safety correctness; the current reference implies that `ensure` diagnostics are active in Shipping Editor by default, which is false for the installed 5.8.2 defaults.
- **Locations:** `references/assertions.md:9-15`.
- **Finding:** `Build.h` sets `DO_ENSURE` in Shipping to `USE_ENSURES_IN_SHIPPING`, whose default is `0`. The expression is still evaluated when `DO_ENSURE=0`, but the reporting implementation is absent. State the opt-in explicitly instead of listing Shipping Editor as an always-active configuration.
- **Exact proposed replacement:**

```diff
--- a/skills/core/logging-and-assertions/references/assertions.md
+++ b/skills/core/logging-and-assertions/references/assertions.md
@@
-| `DO_ENSURE` | `ensure`, `ensureMsgf`, `ensureAlways`, `ensureAlwaysMsgf` | Debug, Development, Test, Shipping Editor |
+| `DO_ENSURE` | `ensure`, `ensureMsgf`, `ensureAlways`, `ensureAlwaysMsgf` | Debug, Development, Test; Shipping only when `USE_ENSURES_IN_SHIPPING=1` (default 0) |
@@
-In shipping (`DO_ENSURE=0`): the expression evaluates (no compilation out), but
-`EnsureFailed` / crash reporting is never invoked.
+In shipping (`DO_ENSURE=0`, the default): the expression evaluates, but `EnsureFailed` /
+crash reporting is never invoked. A target that sets `USE_ENSURES_IN_SHIPPING=1` enables the
+reporting path.
```

- **Practical task benefit:** prevents teams from assuming production crash-report telemetry exists when their target has compiled ensure reporting out.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Misc/Build.h:205-212`, `325-334`; `Misc/AssertionMacros.h:362-368`, `467-474` — `DO_ENSURE`/`USE_ENSURES_IN_SHIPPING` and disabled branch. UE 5.8.2 source.

#### LOG-ASSERT-02 — replace deprecated `FLogRecord::GetFormat()` in structured-log tooling

- **Priority:** P1 — 5.8 deprecation/build hygiene; custom output devices copied from the reference will compile with a deprecation warning and retain the old TCHAR-format contract.
- **Locations:** `references/structured-logging.md:97-113`; `SKILL.md:222-223` source-material list.
- **Finding:** UE 5.8.2 marks `FLogRecord::GetFormat()` and `SetFormat()` deprecated in favor of UTF-8 accessors. The reference’s accessor list presents `GetFormat()` as current and omits `GetUtf8Format()`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/logging-and-assertions/references/structured-logging.md
+++ b/skills/core/logging-and-assertions/references/structured-logging.md
@@
-const TCHAR*            GetFormat()     // format string (e.g. "Loading '{Name}'")
+const UTF8CHAR*         GetUtf8Format() // current UE 5.8 format accessor
@@
 `FLogRecord::FormatMessageTo(FWideStringBuilderBase&)` produces the human-readable string
 by substituting field values into the format template.
+`GetFormat()`/`SetFormat()` remain compatibility APIs but are `UE_DEPRECATED(5.8)`; use
+`GetUtf8Format()`/`SetUtf8Format()` for custom log consumers.
--- a/skills/core/logging-and-assertions/SKILL.md
+++ b/skills/core/logging-and-assertions/SKILL.md
@@
-  `FLogRecord`:181, `SerializeForLog`:297.
+  `FLogRecord`:181, `GetUtf8Format`:203, `SerializeForLog`:297.
```

- **Practical task benefit:** removes UE 5.8 deprecation noise and keeps log consumers on the current UTF-8 representation.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Logging/StructuredLog.h:196-204` — `GetFormat` deprecated and `GetUtf8Format` current. UE 5.8.2 source.

#### LOG-ASSERT-03 — state the new UE 5.8 logging-header and fatal-helper boundaries explicitly

- **Priority:** P2 — migration clarity; the source-material list is version-labeled but the body does not tell readers why a previously compiling include or helper may warn.
- **Locations:** `SKILL.md:213-226`; `references/assertions.md:115-126`.
- **Finding:** UE 5.8 places category macros in `Logging/LogCategory.h` (including `DEFINE_LOG_CATEGORY_STATIC`) and keeps `LowLevelFatalErrorHandler` as a 5.7-deprecated wrapper. Make the public include and replacement explicit in the practical text.
- **Exact proposed addition:**

```diff
--- a/skills/core/logging-and-assertions/SKILL.md
+++ b/skills/core/logging-and-assertions/SKILL.md
@@
 `DECLARE_LOG_CATEGORY_EXTERN` generates an `extern` struct; `DEFINE_LOG_CATEGORY` provides
 the definition. A file-private category uses `DEFINE_LOG_CATEGORY_STATIC` and needs no
 header declaration — appropriate for a single `.cpp` implementation file.
+In UE 5.8, include `Logging/LogCategory.h` when using the category declaration/definition
+macros directly; `DEFINE_LOG_CATEGORY_STATIC` is defined there. Keep
+`Logging/LogMacros.h` for logging-call macros.
--- a/skills/core/logging-and-assertions/references/assertions.md
+++ b/skills/core/logging-and-assertions/references/assertions.md
@@
 This is a macro (`AssertionMacros.h`:591) that calls
 `UE::Assert::Private::ProcessLowLevelFatalError`. The older function
 `LowLevelFatalErrorHandler` was deprecated in 5.7.
+Do not call `LowLevelFatalErrorHandler` in new code; use the `LowLevelFatalError(...)` macro.
```

- **Practical task benefit:** avoids 5.8 header-order surprises and removes the deprecated fatal-helper call from new diagnostics.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Logging/LogCategory.h:142-168`; `Misc/AssertionMacros.h:584-595`. UE 5.8.2 source.

### No-change checks

- Category declaration/definition, compile-time versus runtime verbosity, `UE_LOG`/`UE_CLOG`, `%s`/`FString` handling, `UE_LOGFMT` positional/named field rules, `UE_LOGFMT_EX`, `UE_LOG_CONTEXT`, `FLogRecord` fields, `SerializeForLog`, `check`/`verify`/`ensure` selection, side-effect placement, on-screen-message gating, and log destinations remain applicable after the targeted corrections.
- `check`/`verify`/`ensure` user-facing macro signatures are unchanged in 5.8.2; `checkSlow` is Debug-only by default because `DO_GUARD_SLOW=0` in Development. `verify` and `ensure` expressions still evaluate when their reporting family is disabled, while only `verify` remains the side-effect-preserving hard-check recommendation.
- UE 5.8 release notes and 5.8.1/5.8.2 hotfixes contain logging/assertion fixes and the `FLogRecord` UTF-8 API transition but no new category family. Sources: [5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No Debug/Development/Test/Shipping target was compiled to observe macro expansion, output routing, or `USE_ENSURES_IN_SHIPPING` overrides.
- No custom `FOutputDevice` consumed a structured log record, so UTF-8 lifetime/encoding and downstream serialization behavior were source-reviewed but not runtime-tested.
- No crash reporter or packaged Shipping build was exercised; exact project logging configuration may route severities differently from the documented defaults.
 
---

## core/materials-and-shaders

**Status:** findings  
**Repository path:** `skills/core/materials-and-shaders/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/logging-and-assertions/` and before `skills/core/memory-and-gc/`  
**Files reviewed:**
- `skills/core/materials-and-shaders/SKILL.md`
- `skills/core/materials-and-shaders/references/material-instances-and-parameters.md`
- `skills/core/materials-and-shaders/references/material-graph-and-domains.md`
- `skills/core/materials-and-shaders/references/material-cpp-and-collections.md`

### Verified recommendations

#### MAT-01 — Fix the per-instance custom-data API example

- **Location:** `skills/core/materials-and-shaders/references/material-cpp-and-collections.md:192-205`.
- **Priority:** P1 — the current three-argument call is named as a `UPrimitiveComponent` custom-primitive-data call, but the installed `UPrimitiveComponent::SetCustomPrimitiveDataFloat` takes only `(DataIndex, Value)`. The per-instance ISM/HISM API is `SetCustomDataValue(InstanceIndex, CustomDataIndex, Value, ...)`.
- **Task benefit:** prevents a compile failure and makes the recommended single-MID/per-instance variation pattern usable for ISM/HISM content.
- **Evidence:** UE 5.8.2 `Engine/Source/Runtime/Engine/Classes/Components/PrimitiveComponent.h:1167-1185` declares component custom primitive data, including `SetCustomPrimitiveDataFloat(int32 DataIndex, float Value)`. `Engine/Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h:321-331` declares `SetCustomDataValue(int32 InstanceIndex, int32 CustomDataIndex, float CustomDataValue, bool bMarkRenderStateDirty = false)` and `SetCustomData`. HISM overrides the same API in `HierarchicalInstancedStaticMeshComponent.h:302-310`.
- **Proposed replacement:**

```diff
- For `UInstancedStaticMeshComponent` and `UHierarchicalInstancedStaticMeshComponent`,
- creating one MID per instance is prohibitively expensive. Instead, the material
- can use `GetCustomPrimitiveData` or read per-instance float data stored via
- `SetCustomPrimitiveDataFloat`:
+ For `UInstancedStaticMeshComponent` and `UHierarchicalInstancedStaticMeshComponent`,
+ creating one MID per instance is prohibitively expensive. Instead, configure
+ `NumCustomDataFloats` and write per-instance data with `SetCustomDataValue` or
+ `SetCustomData`; the material reads it with the `PerInstanceCustomData` expression.
 
 ```cpp
- // Store 4 floats per instance at index 0:
- ISMComp->SetCustomPrimitiveDataFloat(InstanceIndex, 0, MyValue);
+ // Configure NumCustomDataFloats >= 1 on the ISM/HISM, then set slot 0 for one instance:
+ ISMComp->SetCustomDataValue(InstanceIndex, 0, MyValue);
 ```
```

#### MAT-02 — Add the UE 5.8 Substrate Toon Shading status without changing the stable MID guidance

- **Locations:** `skills/core/materials-and-shaders/SKILL.md:212-223` and `skills/core/materials-and-shaders/references/material-graph-and-domains.md:127-149`.
- **Priority:** P2 — scoped feature discovery; the existing Substrate runtime-parameter statement remains valid.
- **Task benefit:** lets stylized-material authors find the new 5.8 path while preventing experimental NPR work from being presented as a stable replacement for ordinary material graphs.
- **Evidence:** UE 5.8 release notes classify Substrate NPR/Toon Shading as **Experimental**, describe its legacy Substrate Blendable GBuffer mode and Lumen/light support, and link the feature: <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#substratenprshading(experimental)>. Installed UE 5.8.2 declarations expose `EMaterialShadingModel::MSM_Strata` in `Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h:707-727`, `FMaterialCompiler::SubstrateToonBSDF` in `Engine/Source/Runtime/Engine/Public/MaterialCompiler.h:740-746`, and Substrate result/topology interfaces in `Engine/Source/Runtime/Engine/Public/Materials/MaterialExpression.h:458-481`.
- **Proposed addition:**

```diff
+### Substrate Toon Shading (Experimental in UE 5.8)
+
+UE 5.8 adds Substrate Toon Shading as an **Experimental** stylized path. It uses the
+Substrate Blendable GBuffer mode and a Toon Profile/Toon BSDF workflow; Epic lists support
+for local lights, sky lights, and Lumen GI. Keep this separate from the stable material
+instance API: `UMaterialInstanceDynamic::Set*ParameterValue` remains the runtime parameter
+path, but no production guarantee is implied for the experimental toon graph.
```

### No-change checks

- `UMaterialInterface`, `UMaterial`, `UMaterialInstance`, `UMaterialInstanceConstant`, `UMaterialInstanceDynamic`, `CreateDynamicMaterialInstance`, the scalar/vector/texture setters, MID index-cache pair, `UKismetMaterialLibrary`, and the two-collection limit match UE 5.8.2 declarations/source. `ParameterCollection.h:13-18` and `HLSLMaterialTranslator.cpp:5056-5074` confirm the two-collection ceiling.
- The existing MIC/MID lifetime, replication, `UPROPERTY`, parameter-name, static-switch, material-domain, usage-flag, and Lumen/Substrate separation guidance did not require a 5.8.2 API replacement.
- The 5.8.1/5.8.2 hotfix material notes include fixes for overridden-parameter validation and shader/material crashes, but no versioned public API migration that applies to these recipes. Do not convert those bug fixes into untested workaround instructions.

### Unresolved questions and verification gaps

- No material asset was opened, compiled, migrated to Substrate, rendered, or profiled in the UE 5.8.2 editor. Shader permutations, PSO precache behavior, Lumen/Substrate visual parity, custom-data buffer sizing, and platform limits remain unvalidated in a project.
- The installed declarations confirm Substrate Toon compiler plumbing, but the project-setting enablement, Toon Profile asset workflow, and final editor UX were not exercised. Keep the proposed addition docs/release-note grounded and experimental.
- No marketplace material or vendor plugin was inspected; vendor-specific Substrate compatibility remains an evidence gap.

**Source/doc set checked:** installed UE 5.8.2 Engine material, component, and compiler files listed above; version-matched material/Lumen docs; UE 5.8 release notes; 5.8.1 hotfix page; 5.8.2 hotfix page. No marketplace/vendor plugin evidence was used.

## core/memory-and-gc

**Working-tree reconciliation:** read the added Windows Editor out-of-memory section. Its separation of RAM, VRAM and committed memory, approval boundary, and configured-versus-effective capacity checks are useful safeguards. Windows WMI classes, pagefile registry behavior and host observations are outside Epic engine-source authority and were not exercised in this audit; mark that subsection **partially verified** rather than claiming UE 5.8.2 validates every Windows configuration. No system settings were changed.

**Status:** findings  
**Repository path:** `skills/core/memory-and-gc`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/logging-and-assertions`, before `skills/core/module-and-build-system`

**Files reviewed:**

- `skills/core/memory-and-gc/SKILL.md`
- `skills/core/memory-and-gc/references/object-pointer-types.md`
- `skills/core/memory-and-gc/references/smart-pointers.md`
- `skills/core/memory-and-gc/references/uobject-gc-and-roots.md`

### Verified recommendations

#### MEMORY-GC-01 — remove the false prohibition on weak UObject pointers as map/set keys

- **Priority:** P1 — compile/API correctness; the current sentence sends authors to a different key type even though UE 5.8.2 provides hashing and equality for `TWeakObjectPtr`.
- **Locations:** `references/object-pointer-types.md:68-73`.
- **Finding:** `FWeakObjectPtr` has a `GetTypeHash()` implementation and equality operators in 5.8.2, so `TWeakObjectPtr<T>` can be used as a `TMap` key or `TSet` element. The actual caveat is that the key is non-owning and can become invalid; callers must handle stale entries and understand null weak pointers compare equal.
- **Exact proposed replacement:**

```diff
--- a/skills/core/memory-and-gc/references/object-pointer-types.md
+++ b/skills/core/memory-and-gc/references/object-pointer-types.md
@@
-`TWeakObjectPtr` cannot be used as a `TMap` key or `TSet` element; use `TObjectKey<T>` for that.
+`TWeakObjectPtr` can be used as a `TMap` key or `TSet` element in UE 5.8.2 because it
+provides equality and `GetTypeHash()`. It remains non-owning: remove or skip stale keys
+after GC, and remember that invalid weak pointers compare equal. Use `TObjectKey<T>` instead
+when you want an immutable object-identity key without weak-pointer invalidation semantics.
```

- **Practical task benefit:** prevents unnecessary key-type rewrites and makes stale-key handling explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Public/UObject/WeakObjectPtr.h:161-183`, `371-379`, `582-586` — equality and `GetTypeHash`; `ObjectKey.h:219-242` — alternate immutable identity key. UE 5.8.2 source.

#### MEMORY-GC-02 — correct the default shared-pointer thread-safety mode

- **Priority:** P1 — concurrency/performance correctness; the current table and prose label the default as `ESPMode::Fast`/non-thread-safe, while UE 5.8.2 defaults the public shared-pointer templates to `ESPMode::ThreadSafe`.
- **Locations:** `references/smart-pointers.md:18-23`, `109-118`; `SKILL.md` smart-pointer summary section (insert next to its thread-safety guidance).
- **Finding:** `SharedPointerFwd.h` declares `TSharedPtr`, `TSharedRef`, `TWeakPtr`, and `TSharedFromThis` with default `ESPMode::ThreadSafe`. Projects may explicitly select `ESPMode::NotThreadSafe` for single-threaded hot paths, but the reference’s “Fast by default” statement is reversed for UE 5.8.2.
- **Exact proposed replacement:**

```diff
--- a/skills/core/memory-and-gc/references/smart-pointers.md
+++ b/skills/core/memory-and-gc/references/smart-pointers.md
@@
-| `TSharedPtr<T>` | yes | shared (ref-counted) | no (`ESPMode::Fast`) |
-| `TSharedRef<T>` | **no** (never null) | shared (ref-counted) | no (`ESPMode::Fast`) |
-| `TWeakPtr<T>` | yes | non-owning observer | no |
+| `TSharedPtr<T>` | yes | shared (ref-counted) | yes by default (`ESPMode::ThreadSafe`) |
+| `TSharedRef<T>` | **no** (never null) | shared (ref-counted) | yes by default (`ESPMode::ThreadSafe`) |
+| `TWeakPtr<T>` | yes | non-owning observer | yes by default (`ESPMode::ThreadSafe`) |
@@
-By default, `TSharedPtr`/`TSharedRef`/`TWeakPtr` are **not** thread-safe (uses `ESPMode::Fast`,
-a non-atomic ref-count). For cross-thread sharing, use the thread-safe mode:
+By default, `TSharedPtr`/`TSharedRef`/`TWeakPtr` use `ESPMode::ThreadSafe` in UE 5.8.2.
+For a demonstrably single-threaded hot path, opt into `ESPMode::NotThreadSafe` explicitly;
+otherwise keep the default:
@@
-TSharedPtr<FWorkItem, ESPMode::ThreadSafe> WorkItem = MakeShared<FWorkItem, ESPMode::ThreadSafe>();
+TSharedPtr<FWorkItem, ESPMode::ThreadSafe> WorkItem = MakeShared<FWorkItem, ESPMode::ThreadSafe>();
```

- **Practical task benefit:** avoids false race warnings for default pointers and prevents accidentally choosing a faster mode for data that crosses threads.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Templates/SharedPointerFwd.h:22-27` — default `ESPMode::ThreadSafe`; `SharedPointer.h:692-696` — mode-dependent `TSharedPtr`. UE 5.8.2 source.

#### MEMORY-GC-03 — add the UE 5.8 pending-actor incremental-GC controls

- **Priority:** P2 — scoped 5.8 operational feature; streaming-heavy projects can reduce purge pressure based on actor counts instead of relying only on level counts.
- **Locations:** insertion after `SKILL.md:55` and `references/uobject-gc-and-roots.md:64`.
- **Finding:** UE 5.8 adds optional repeated incremental GC while streaming actors are pending purge, plus a low-memory actor-count threshold. The current GC guidance mentions incremental reachability but omits these version-matched controls; they are disabled or effectively unlimited by default and should not be presented as a universal tuning change.
- **Exact proposed addition:**

```diff
--- a/skills/core/memory-and-gc/SKILL.md
+++ b/skills/core/memory-and-gc/SKILL.md
@@
 `TObjectPtr` members enable GC write barriers that make incremental marking safe.
+UE 5.8 also adds optional actor-count-based streaming purge controls:
+`s.ContinuouslyIncrementalGCWhileActorsPendingPurge` (disabled by default) and
+`s.LevelStreamingLowMemoryActorsPendingPurgeCount`; partitioned-world projects also have
+`wp.Runtime.LevelStreamingContinuouslyIncrementalGCWhileActorsPendingPurgeForWP`. Tune these
+only against streaming/memory telemetry.
--- a/skills/core/memory-and-gc/references/uobject-gc-and-roots.md
+++ b/skills/core/memory-and-gc/references/uobject-gc-and-roots.md
@@
 Raw `T* UPROPERTY` works but
 does not participate in the write barrier, which can cause objects to be missed in an incremental
 pass and only collected on the next full pass.
+
+UE 5.8 adds actor-count-aware streaming purge controls: enable
+`s.ContinuouslyIncrementalGCWhileActorsPendingPurge` only when measurements justify repeated
+incremental passes, and use `s.LevelStreamingLowMemoryActorsPendingPurgeCount` for the low-memory
+threshold. These controls are disabled/unbounded by default; they are not a replacement for
+correct reflected ownership.
```

- **Practical task benefit:** gives streaming teams a version-correct tuning hook while keeping the ownership rule primary.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), Foundation/Core GC entry; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/CoreSettings.cpp:27-33`, `156-161`, `184-189` and `World.cpp:5162-5174` — CVar defaults and use. UE 5.8.2 source.

#### MEMORY-GC-04 — record the UE 5.8 shared-pointer API removals and additions

- **Priority:** P2 — migration clarity; code using removed `WeakPtr` state on `TSharedFromThis` or missing move/cast helpers needs an explicit version note.
- **Locations:** insertion in `references/smart-pointers.md` after line 118 and in its Version/selection guidance.
- **Finding:** UE 5.8 release notes remove the public `WeakPtr` member from `TSharedFromThis` and add rvalue constructors plus `StaticCastShared/Weak...` helpers. The current reference does not mention this change.
- **Exact proposed addition:**

```diff
--- a/skills/core/memory-and-gc/references/smart-pointers.md
+++ b/skills/core/memory-and-gc/references/smart-pointers.md
@@
 Thread-safe versions use atomic operations for ref-counting; reads and copies are always safe
 from multiple threads; writes and resets must still be synchronized externally. Only use the
 thread-safe mode when you actually share across threads — it is measurably slower.
+UE 5.8 keeps `TSharedFromThis::AsShared()` as the public self-reference path; do not access
+a removed `WeakPtr` member. Use `AsShared().ToWeakPtr()` when a weak self-reference is needed,
+and use the rvalue-aware `StaticCastShared...`/`StaticCastWeakPtr(...)` helpers for casts.
```

- **Practical task benefit:** prevents 5.8 compile failures in shared-service code and uses the current weak-self/cast API.
- **Verified evidence:** [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), Core API changes; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Templates/SharedPointer.h:48-56`, `1970-1984` and `SharedPointerFwd.h:22-27`. UE 5.8.2 source.

### No-change checks

- UObject-versus-C++ ownership split, reflected `TObjectPtr`/raw pointer rules, weak/soft/strong pointer selection, `FGCObject`, roots, clustering, incremental reachability, `NewObject`, `CreateDefaultSubobject`, `AddToRoot`/`RemoveFromRoot`, `MarkAsGarbage`, `IsValid`, `TSharedFromThis::AsShared`, and the no-`delete` UObject rule remain applicable in UE 5.8.2.
- `TObjectPtr`’s `UE_OBJECT_PTR_GC_BARRIER` default is enabled in the installed 5.8.2 `ObjectPtr.h`; this supports the existing write-barrier recommendation. Raw `T* UPROPERTY` remains source-compatible but does not get the same object-pointer barrier path.
- 5.8.1/5.8.2 hotfixes contain GC/streaming bug fixes but no additional pointer-family migration that changes these recommendations: [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No compiled target ran a forced GC while mutating nested pointers, weak map keys, strong pointers, or streaming levels; source contracts were verified without runtime lifetime stress.
- No project measured the new actor-count GC CVars, and the partitioned-world CVar path was not exercised.
- Exact `TStrongObjectPtr` cycle behavior depends on object graphs and owner destruction; no leak detector or reference-chain run was performed.

---

## core/meshes-static-and-skeletal

**Status:** findings  
**Repository path:** `skills/core/meshes-static-and-skeletal/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/materials-and-shaders/`, before `skills/core/module-and-build-system/`  
**Files reviewed:** `SKILL.md`; `references/instanced-meshes.md`; `references/materials-lods-collision.md`; `references/skeletal-meshes.md`; `references/static-meshes.md`.

### Verified recommendations

#### MESH-01 — correct the missing-socket transform contract

- **Priority:** P1 — attachment correctness; the current reference tells agents that a missing socket returns identity, while UE 5.8.2 returns the component transform, which can place a supposedly validated attachment at an unexpected world-space location.
- **Location:** `references/static-meshes.md:81-83`.
- **Finding:** `USceneComponent::GetSocketTransform` documents that a missing socket or bone returns the component transform in the requested space. `GetSocketByName`/`DoesSocketExist` should still be used when absence is an error, but “identity” is not the engine contract.
- **Exact proposed replacement:**

```diff
--- a/skills/core/meshes-static-and-skeletal/references/static-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/static-meshes.md
@@
-`GetSocketTransform` returns identity if the socket name is not found — always check
-with `GetSocketByName` first. Sockets defined in the Static Mesh Editor are stored on the
-`UStaticMesh` asset and are shared across all component instances.
+`GetSocketTransform` returns the component's transform in the requested space if the socket
+name is not found. Check `DoesSocketExist` or `GetSocketByName` first when a missing socket
+must be rejected. Sockets defined in the Static Mesh Editor are stored on the `UStaticMesh`
+asset and are shared across all component instances.
```

- **Practical task benefit:** prevents a missing socket from being diagnosed as an identity transform and makes the attachment failure check explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Components/SceneComponent.h:795-801` — `USceneComponent::GetSocketTransform` return contract; `:827-832` — `DoesSocketExist`. UE 5.8.2 source.

#### MESH-02 — make Nanite asset editing editor/build-only and call the rebuild notification

- **Priority:** P1 — editor/runtime and derived-data correctness; the current sample labels asset Nanite configuration as “at runtime” and says `SetNaniteSettings` triggers a rebuild, but the settings/accessors are under `WITH_EDITORONLY_DATA`, the setter only assigns the struct, and `NotifyNaniteSettingsChanged` is the hook that calls `PostEditChangeProperty`.
- **Locations:** `SKILL.md:209-220`; `references/static-meshes.md:85-104`; `references/skeletal-meshes.md:145-153`.
- **Finding:** In UE 5.8.2, `UStaticMesh::GetNaniteSettings`, `SetNaniteSettings`, and `NotifyNaniteSettingsChanged` are declared in the editor-only-data block; `USkeletalMesh` exposes its Nanite settings and notification hook in the same block. `SetNaniteSettings` itself only copies `NaniteSettings = Settings`; it does not rebuild derived Nanite data. This guidance should describe an editor/asset-build operation, not gameplay mutation.
- **Exact proposed replacement:**

```diff
--- a/skills/core/meshes-static-and-skeletal/SKILL.md
+++ b/skills/core/meshes-static-and-skeletal/SKILL.md
@@
-// Enable Nanite on a static mesh asset at runtime (editor / cooking context):
+// Configure Nanite on a static-mesh asset in an editor/asset-build context;
+// these settings are not gameplay-runtime controls:
 FMeshNaniteSettings Settings = MyStaticMesh->GetNaniteSettings();
 Settings.bEnabled = true;
 MyStaticMesh->SetNaniteSettings(Settings);
-// Note: triggers a rebuild; call from editor utilities, not gameplay code.
+MyStaticMesh->NotifyNaniteSettingsChanged(); // invokes PostEditChangeProperty
+// Save/mark the package as appropriate and let the editor/cook build derived data.
```

```diff
--- a/skills/core/meshes-static-and-skeletal/references/static-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/static-meshes.md
@@
-Since 5.7, direct member access is deprecated (`UE_DEPRECATED(5.7, ...)`). Use:
+Since 5.7, direct member access is deprecated (`UE_DEPRECATED(5.7, ...)`). In UE 5.8.2
+the settings accessors are editor-only-data APIs; use them in editor/asset-build code,
+not gameplay code:
@@
 FMeshNaniteSettings NS = MyMesh->GetNaniteSettings();   // line 855
 NS.bEnabled = true;
 MyMesh->SetNaniteSettings(NS);                          // line 864
-// Call PostEditChange / MarkPackageDirty to trigger rebuild in-editor.
+MyMesh->NotifyNaniteSettingsChanged();                 // calls PostEditChangeProperty
+// Save/mark the package as appropriate; derived Nanite data is built by editor/cook.
```

```diff
--- a/skills/core/meshes-static-and-skeletal/references/skeletal-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/skeletal-meshes.md
@@
-Enable via the Skeletal Mesh Editor's Nanite Settings panel, or in C++ using the same
-`GetNaniteSettings()` / `SetNaniteSettings()` accessors as static meshes.
+Enable via the Skeletal Mesh Editor's Nanite Settings panel, or from editor/asset-build
+code with `GetNaniteSettings()` / `SetNaniteSettings()`, followed by
+`NotifyNaniteSettingsChanged()`. These accessors are not gameplay-runtime controls.
```

- **Practical task benefit:** avoids shipping code that mutates editor-only asset settings without rebuilding derived data and gives editor automation the missing notification step.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/StaticMesh.h:855-882` — accessor/setter/notification implementation inside `WITH_EDITORONLY_DATA`; `.../Engine/SkeletalMesh.h:962-984` — skeletal settings and notification block. UE 5.8.2 source.

#### MESH-03 — describe skeletal Nanite as a render path with explicit morph fallback, not one-draw production magic

- **Priority:** P1 — visual correctness and performance expectations; the current wording promises production readiness, one GPU draw call, and an implied morph-target fallback without stating the actual 5.8.2 gates.
- **Locations:** `SKILL.md:271-272`; `references/skeletal-meshes.md:145-156`.
- **Finding:** UE 5.8.2 has a `Nanite::FSkinnedSceneProxy` path, but `FSkinnedMeshComponentHelper::ShouldNaniteSkin` is gated by `IsDisallowNanite`, `IsForceDisableNanite`, the global `ShouldRenderNaniteSkinnedMeshes()` switch, platform `UseNanite`, and valid Nanite resources. The helper does not test active morph targets. The Nanite update signature receives morph-target maps/weights but `FSkeletalMeshObjectNanite::Update` initializes dynamic data from component-space bone transforms and does not pass those morph arguments into the initialized data. Therefore a project that requires morph deformation must explicitly force the traditional path; do not claim that the engine automatically falls back or that the character is one draw call.
- **Exact proposed replacement:**

```diff
--- a/skills/core/meshes-static-and-skeletal/SKILL.md
+++ b/skills/core/meshes-static-and-skeletal/SKILL.md
@@
-- Skeletal mesh Nanite (full Nanite skinning) is production-ready since 5.7 with a single
-  draw call per character and Virtual Shadow Map support; animation LODs still apply.
+- Skeletal mesh Nanite has a supported skinned render path in UE 5.8.2, but its actual
+  use is gated by project/platform settings, valid built Nanite resources, and material
+  audit results. It does not guarantee one draw call per character; material sections and
+  render passes still matter. Animation LODs still apply.
+- Morph targets are not consumed by the Nanite skinned update path in 5.8.2. If a mesh
+  needs morph deformation, explicitly use the traditional skinned path (for example,
+  disallow Nanite on that component) and verify the result in the target project.
```

```diff
--- a/skills/core/meshes-static-and-skeletal/references/skeletal-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/skeletal-meshes.md
@@
-In 5.8, Nanite for skeletal meshes is production-ready (since 5.7). Enabling it gives:
-- One GPU draw call for the entire character (vs. one per material section).
-- Virtual Shadow Map support.
-- Animation LODs (not geometry LODs — bones/sections can be stripped per LOD).
+UE 5.8.2 contains a Nanite skinned-mesh render path on platforms and projects that pass
+the engine’s Nanite gates. It can use Virtual Shadow Maps and still obey animation LOD
+settings; it does **not** guarantee one GPU draw call for an entire character.
@@
-Enable via the Skeletal Mesh Editor's Nanite Settings panel, or in C++ using the same
-`GetNaniteSettings()` / `SetNaniteSettings()` accessors as static meshes.
+Enable it in the Skeletal Mesh Editor or in editor/asset-build code; see the editor-only
+settings boundary above.
@@
-Limitations: Morph targets are not supported with Nanite on skeletal meshes. Cloth
-simulation output is still rendered via the traditional path when cloth is enabled.
+Limitations: the 5.8.2 Nanite skinned update receives morph-target inputs but does not
+consume them when initializing its dynamic data. Explicitly disallow Nanite when morph
+deformation is required. Cloth, materials, platform support, and fallback behavior remain
+project-dependent and must be tested rather than inferred from the presence of Nanite data.
```

- **Practical task benefit:** prevents visual regressions for facial morphs, avoids false one-draw budgeting, and tells agents which component/platform gates to inspect before enabling the path.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/SkinnedMeshComponentHelper.h:197-205` — `ShouldNaniteSkin` gates; `.../Engine/Private/Components/SkinnedMeshComponent.cpp:607-634` — Nanite versus traditional scene-proxy selection; `.../Engine/Private/SkeletalRenderNanite.cpp:449-477` — morph inputs accepted by the update signature but omitted from `FDynamicSkelMeshObjectDataNanite::Init`; `:479-488` — section-based processing setup. UE 5.8.2 source.

#### MESH-04 — mark the ISM ID API preliminary and forbid the documented HISM/editor-invalid cases

- **Priority:** P1 — instance identity correctness; the reference calls `FPrimitiveInstanceId` “stable” and recommends it without the explicit engine warning that the interface is preliminary, unavailable for HISM, and unreliable after some editor manipulations.
- **Location:** `references/instanced-meshes.md:82-94`.
- **Finding:** UE 5.8.2’s `UInstancedStaticMeshComponent` header labels the ID-based interface preliminary and says it may only be used when no other operations invalidate IDs; it explicitly says it cannot be used on HISM and that editor-edited ISMs can lose tracking. Keep the example scoped to an unmodified runtime ISM and validate IDs with `IsValidId`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/meshes-static-and-skeletal/references/instanced-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/instanced-meshes.md
@@
-Newer code should prefer the stable `FPrimitiveInstanceId`-based API to avoid
-index-shifting problems:
+UE 5.8.2 exposes a **preliminary** `FPrimitiveInstanceId` interface. Use it only for a
+runtime ISM whose ID-tracking mode is preserved; do not use this interface on HISM, and
+do not assume editor-edited ISMs retain IDs:
@@
-`FPrimitiveInstanceId` is stable across `RemoveInstance` operations because removal
-no longer swaps with the last element when using the ID API.
+The ID API avoids ordinary index-shift bookkeeping for supported ISM operations, but IDs
+can still become invalid when unsupported mutations or editor changes lose tracking.
+Check `ISMC->IsValidId(Id)` before using a retained ID and fall back to an index lookup or
+rebuild the mapping when the component’s ID mode is not valid.
```

- **Practical task benefit:** prevents invalid-ID assertions and incorrect instance updates when an agent applies the sample to HISM or editor-authored data.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h:287-315` — preliminary-interface/HISM/editor warning and ID declarations; `.../Engine/Private/InstancedStaticMesh.cpp:3815-3828` — ID creation checks the primitive-data mode. UE 5.8.2 source.

#### MESH-05 — use `SetNumCustomDataFloats` instead of mutating the count field directly

- **Priority:** P1 — per-instance material data correctness; assigning the public count field directly can leave an existing custom-data buffer at the wrong size, while the engine setter documents that it reallocates the full buffer and resets values.
- **Location:** `references/instanced-meshes.md:96-111`.
- **Finding:** `NumCustomDataFloats` is a public reflected property, but UE 5.8.2 also provides `SetNumCustomDataFloats`. The header explicitly says the setter applies to all instances, reallocates the full custom-data buffer, and resets values to zero. Configure the count before adding instances, or deliberately use the setter and repopulate values when changing an existing component.
- **Exact proposed replacement:**

```diff
--- a/skills/core/meshes-static-and-skeletal/references/instanced-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/instanced-meshes.md
@@
-// Set the custom data float count (must be done before adding instances):
-ISMC->NumCustomDataFloats = 4;   // 4 floats per instance
+// Set the custom data float count before adding instances:
+ISMC->SetNumCustomDataFloats(4); // reallocates the buffer; existing values reset
@@
     /*bMarkRenderStateDirty=*/true);
```

- **Practical task benefit:** ensures `PerInstanceSMCustomData` has the expected stride and avoids silent zeroed/stale material channels after changing the layout.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h:179-194` — count and buffer layout; `:321-327` — setter contract; `.../Engine/Private/InstancedStaticMesh.cpp:3697-3716` — bulk addition allocates `NumCustomDataFloats * Count`. UE 5.8.2 source.

#### MESH-06 — remove the leader-pose draw-call reduction claim

- **Priority:** P2 — performance guidance accuracy; leader pose saves duplicate pose/bone-transform evaluation, but it does not merge arbitrary follower material sections into a single draw call.
- **Location:** `references/skeletal-meshes.md:122-124`.
- **Finding:** `LeaderPoseComponent` is documented as supplying component-space transforms to a follower, and the implementation adds a tick prerequisite and maintains follower components. Each skinned component still owns a scene proxy and its own sections/materials. The benefit should be described as shared pose evaluation, not a guaranteed shared draw call.
- **Exact proposed replacement:**

```diff
--- a/skills/core/meshes-static-and-skeletal/references/skeletal-meshes.md
+++ b/skills/core/meshes-static-and-skeletal/references/skeletal-meshes.md
@@
-The follower components contribute their sections to the same draw call set as the
-leader, significantly reducing rendering cost compared to independent animation
-evaluation. All followers must share the same `USkeleton` as the leader.
+Leader pose shares component-space bone transforms and establishes a tick dependency, so
+it avoids independent animation/pose evaluation on followers. Followers remain separate
+components and can still submit their own material sections and render work; no draw-call
+reduction is guaranteed. All followers must share a compatible `USkeleton` and should be
+profiled with their actual section/material setup.
```

- **Practical task benefit:** keeps modular-character budgeting honest and prevents agents from using leader pose as a substitute for section/material consolidation.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Components/SkinnedMeshComponent.h:308-314` — follower transform contract; `.../Engine/Private/Components/SkinnedMeshComponent.cpp:3224-3254` — follower registration and tick prerequisite; `:607-634` — each component’s scene-proxy selection. UE 5.8.2 source.

### No-change checks

- Static/skeletal asset-versus-component ownership, `TObjectPtr` component members, `SetStaticMesh`, `SetSkeletalMesh`, `SetAnimInstanceClass`, material-slot indexing, `UMaterialInstanceDynamic`, static/skeletal socket lookup, `SetSkeletalMesh(..., false)`, `UPhysicsAsset`, `SetPhysicsAsset`, `UBodySetup`, and component-level collision responses remain applicable in UE 5.8.2.
- `USceneComponent::GetSocketTransform` accepts socket or bone names and returns the component transform on a miss; the correction above is limited to the false identity statement. `GetSocketByName` validation remains useful.
- `ECollisionTraceFlag::CTF_UseComplexAsSimple` remains a static-shape-only choice for Chaos; the installed Chaos enum says complex-as-simple can be used for static shapes, not moved dynamic bodies. No change is needed to the existing warning against simulated dynamic bodies.
- `UInstancedStaticMeshComponent::AddInstance`, `AddInstances`, `UpdateInstanceTransform`, `BatchUpdateInstancesTransforms`, `RemoveInstance`, component-level materials/collision, and the ISM/HISM high-level choice remain present. The header documents `bMarkRenderStateDirty` as the immediate-visibility control and recommends setting it only on the last update in a batch.
- `GetMaterialRelevance(ERHIFeatureLevel::Type)` remains deprecated since 5.7 in the installed `MeshComponent.cpp`; `GetMaterialRelevance(EShaderPlatform)` is the current overload. The reviewed repository files do not use the old overload in a code sample, so no additional hunk is required.
- The UE 5.8 release notes, Upgrade Notes/Deprecations material, 5.8.1 hotfix page, and 5.8.2 hotfix page were checked for mesh, Nanite, skeletal, collision, and instancing migrations. No additional public mesh API migration was confirmed beyond the editor-only Nanite boundary, the preliminary ID interface warning, and the source-backed behavior corrections above. Sources: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No sample project imported, built, or rendered a static/skeletal asset under UE 5.8.2. Nanite material audit, fallback selection, morph/cloth visuals, VSM behavior, platform support, shader compilation, cooked output, and actual draw/pass counts remain untested.
- The installed source proves the skeletal Nanite gates and that morph inputs are not consumed by `FSkeletalMeshObjectNanite::Update`; it does not by itself establish a complete product policy for every material, cloth/deformer combination, or platform. Keep those claims project-tested.
- No runtime test exercised leader-pose followers with mismatched skeletons, missing bones, LOD synchronization, physics assets, or animation-thread reads. The source contracts were inspected without PIE or animation profiling.
- No HISM/ISM stress test measured tree rebuilds, GPU buffer updates, navigation updates, ID invalidation, or per-instance custom-data upload cost. The ID interface remains preliminary as documented by the engine.
- Marketplace/vendor mesh importers and product-specific Nanite limitations were not inspected; no other project or plugin installation was entered. Treat vendor-specific workflows as unresolved.

---

## core/module-and-build-system

**Status:** findings  
**Repository path:** `skills/core/module-and-build-system/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/memory-and-gc/`, before the next repository-path skill  
**Files reviewed:** `SKILL.md`; `references/build-cs-reference.md`; `references/module-cpp-and-phases.md`; `references/target-cs-reference.md`.

### Verified recommendations

#### MODULE-01 — distinguish deprecated `Developer` from `DeveloperTool`

- **Priority:** P1 — packaging/build correctness; the current table conflates two different host filters and can leave an obsolete `Developer` module type in a project descriptor.
- **Location:** `SKILL.md:196-207`, the `ModuleHostType` table.
- **Finding:** In UE 5.8.2, `Developer` is explicitly deprecated and has ambiguous editor/program-only semantics. `DeveloperTool` is the type whose inclusion is governed by `bBuildDeveloperTools`. The table’s combined `Developer / DeveloperTool` row is therefore not a safe migration rule.
- **Exact proposed replacement:**

```diff
--- a/skills/core/module-and-build-system/SKILL.md
+++ b/skills/core/module-and-build-system/SKILL.md
@@
-| `Developer` / `DeveloperTool` | builds with developer tools enabled |
+| `Developer` | **Deprecated/ambiguous**; UE 5.8.2 accepts it for editor/program targets, including editor modes. Use `UncookedOnly` for uncooked editor/program modules, or `DeveloperTool` when `bBuildDeveloperTools` should control inclusion. |
+| `DeveloperTool` | any target where `bBuildDeveloperTools` is enabled |
```

- **Practical task benefit:** prevents developer utilities or Blueprint-node modules from being included in the wrong targets and gives agents the current replacement choices instead of preserving a deprecated descriptor value.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Projects/Public/ModuleDescriptor.h:101-107` marks `Developer` as deprecated due to ambiguity and recommends `UncookedOnly` or `DeveloperTool`; `.../Runtime/Projects/Private/ModuleDescriptor.cpp:600-621` implements the host filtering; `.../Engine/Source/Programs/UnrealBuildTool/Configuration/Descriptors/ModuleDescriptor.cs:644-647` emits the deprecation warning and `:794-802` maps `Developer` to editor/program and `DeveloperTool` to `bBuildDeveloperTools`. UE 5.8.2 source.

#### MODULE-02 — separate PCH selection from IWYU enforcement

- **Priority:** P1 — build guidance correctness; the current example calls `UseExplicitOrSharedPCHs` “required for IWYU compliance” and the reference can make readers confuse the deprecated module property with the active target-level gate.
- **Locations:** `SKILL.md:68-76`; `references/build-cs-reference.md:35-44`.
- **Finding:** UE 5.8.2’s `ModuleRules.PCHUsage` chooses PCH behavior, while `ModuleRules.IWYUSupport` controls module IWYU behavior only when `TargetRules.bEnforceIWYU` is enabled. `ModuleRules.bEnforceIWYU` is the deprecated property; `TargetRules.bEnforceIWYU` remains an active target property. `UseExplicitOrSharedPCHs` is the normal modern PCH mode, but it is not itself the complete IWYU contract and C++ module mode can force `NoPCHs`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/module-and-build-system/SKILL.md
+++ b/skills/core/module-and-build-system/SKILL.md
@@
-        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;  // required for IWYU compliance
+        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;  // modern UE PCH mode; IWYU is configured separately
@@
-`PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs` enables IWYU-safe precompiled headers.
-  Each `.cpp` must include its matching `.h` first, and no monolithic headers (`Engine.h`).
+`PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs` is the normal modern PCH choice. IWYU
+  enforcement is separately controlled by target-level `TargetRules.bEnforceIWYU` and the
+  module’s `IWYUSupport`; each `.cpp` should include its matching `.h` first and avoid
+  monolithic headers such as `Engine.h`.
--- a/skills/core/module-and-build-system/references/build-cs-reference.md
+++ b/skills/core/module-and-build-system/references/build-cs-reference.md
@@
-| `IWYUSupport` | `IWYUSupport` enum (default `Full`) | IWYU enforcement level; with `UseExplicitOrSharedPCHs`, warns on monolithic header includes. Replaces `bEnforceIWYU` (deprecated in 5.2). |
+| `IWYUSupport` | `IWYUSupport` enum (default `Full`) | Module IWYU support level. The deprecated **module** `bEnforceIWYU` property was replaced in 5.2; target-level `TargetRules.bEnforceIWYU` remains the UE 5.8 enforcement gate. |
```

- **Practical task benefit:** avoids a false “PCH equals IWYU” rule, preserves the useful explicit-PCH recommendation, and prevents agents from editing the wrong `bEnforceIWYU` property when diagnosing include-order warnings.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/ModuleRules.cs:816-846` computes `PCHUsage` and returns `NoPCHs` when `Target.bEnableCppModules` is true; `:1133-1137` declares `IWYUSupport`; `.../Configuration/Rules/ModuleRules.Obsolete.cs:20-35` marks the module property `bEnforceIWYU` obsolete; `.../Configuration/Rules/TargetRules.cs:1779-1782` declares active target `bEnforceIWYU`; `.../Configuration/UEBuildModuleCPP.cs:2433-2442` gates first-include checks on both `Rules.IWYUSupport` and `Target.bEnforceIWYU`. UE 5.8.2 source.

#### MODULE-03 — document the distinct UE 5.8 C++20-module build opt-in

- **Priority:** P2 — scoped build-system discovery; the current one-line distinction is conceptually correct but omits the installed UBT switch that changes PCH/unity behavior and compiles module-interface files.
- **Location:** `SKILL.md:22`, the note immediately after the module mental model; add the version note at that point rather than expanding the general module tutorial.
- **Finding:** UE modules and C++20 language modules remain different mechanisms, but UE 5.8.2 exposes `TargetRules.bEnableCppModules`. When enabled, UBT defines `WITH_CPP_MODULES`, compiles `.ixx` module interfaces, disables the default unity-build path, and makes `ModuleRules.PCHUsage` resolve to `NoPCHs`. This is a source-verified build opt-in, not a claim that every project or toolchain is ready for wholesale conversion.
- **Exact proposed replacement:**

```diff
--- a/skills/core/module-and-build-system/SKILL.md
+++ b/skills/core/module-and-build-system/SKILL.md
@@
-Note: UE modules are independent of C++20 language modules.
+Note: UE modules and C++20 language modules are distinct concepts. UE 5.8.2 UBT also has
+the opt-in `TargetRules.bEnableCppModules`; when enabled, it defines `WITH_CPP_MODULES=1`,
+compiles `.ixx` module interfaces, disables the default unity/PCH path, and does not replace
+the need to declare normal UE module dependencies. Treat this as a targeted toolchain/build
+experiment until the project’s compilers, modules, UHT, and plugins have been built together.
```

- **Practical task benefit:** stops an agent from assuming that “UE module” means a C++20 module and gives build engineers the actual switch and side effects needed for a controlled experiment.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/TargetRules.cs:2371-2379` declares `TargetRules.bEnableCppModules`; `.../Configuration/UEBuildTarget.cs:6608-6616` emits `WITH_CPP_MODULES`; `.../Configuration/UEBuildModuleCPP.cs:679-691` compiles `InputFiles.IXXFiles` when the switch is enabled and `:1017-1025` avoids the always-unity generated-file path; `.../Configuration/Rules/TargetRules.cs:1835-1842` makes the default unity setting false for C++ modules; `.../Configuration/Rules/ModuleRules.cs:825-828` selects `NoPCHs`. UE 5.8.2 source. No stronger production-readiness claim is made.

### No-change checks

- `ModuleRules`, `TargetRules`, `ModuleDescriptor`, `IModuleInterface`, `FModuleManager`, `FDefaultModuleImpl`, `FDefaultGameModuleImpl`, `IMPLEMENT_MODULE`, `IMPLEMENT_PRIMARY_GAME_MODULE`, dependency visibility, `RuntimeDependencies`, `PublicSystemIncludePaths`, target gating, `ExtraModuleNames`, and the loading-phase names used by the four repository files are present in UE 5.8.2 with the documented owning modules.
- `BuildSettingsVersion.V7` is the UE 5.8 default-settings entry and `Latest = V7`; `EngineIncludeOrderVersion.Unreal5_8` exists and `Latest = Unreal5_8` in `TargetRules.cs:123-177,188-242`. The existing target examples therefore do not need a version-number rewrite.
- `IModuleInterface::StartupModule`, `PreUnloadCallback`, `PostLoadCallback`, `ShutdownModule`, and `SupportsDynamicReloading` retain the lifecycle contracts described in `ModuleInterface.h:40-101`, including loading dependent modules in `StartupModule` when they must remain available during shutdown. No lifecycle rewrite is justified.
- The fetched UE 5.8 release notes, Upgrade Notes/Deprecations material, 5.8.1 hotfix page, and 5.8.2 hotfix page were checked for UBT/module/build migrations. No additional public module API migration was confirmed beyond the `V7`/include-order source contracts and the descriptor deprecation recorded above. Sources: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- No project was regenerated, compiled, linked, packaged, or run under UE 5.8.2; the module, UBT, and descriptor claims are source/declaration checks, not end-to-end build validation.
- `bEnableCppModules` was verified in installed UBT source, but no matching 5.8 documentation workflow, project `.ixx` target, compiler/toolchain matrix, UHT interaction, or plugin compatibility test was available. Keep MODULE-03 experimental/targeted rather than presenting it as a migration path.
- The `Developer`/`DeveloperTool` filters were inspected in descriptor code, but no game/client/server/editor/program target was built to observe the final compiled and loaded module set.
- Module loading order, Live Coding, DLL unload safety, and third-party runtime dependency staging remain project- and platform-dependent; no custom module or external library was exercised.

---

## core/mover-movement-system

**Status:** partially verified  
**Repository path:** `skills/core/mover-movement-system/`  
**UE target:** 5.8.2 (`++UE5+Release-5.8`, CL 56702186)  
**Audit order:** after `skills/core/module-and-build-system/`; last audited repository-path skill so far  

**Files reviewed:**
- `skills/core/mover-movement-system/SKILL.md`
- `skills/core/mover-movement-system/references/cmc-migration.md`
- `skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md`
- `skills/core/mover-movement-system/references/modes-transitions-and-modifiers.md`
- `skills/core/mover-movement-system/references/networking-and-backends.md`
### Verified recommendations

#### MOVER-01 — Do not document the input-producer flag as a working UE 5.8.2 gate without qualification

- **Priority:** P1 — input correctness and debugging; the current recipe tells users that setting `bGatherInputFromAllInputProducerComponents` to false suppresses automatic component producers, but the installed UE 5.8.2 `BeginPlay` implementation does not read that property.
- **Locations:** `skills/core/mover-movement-system/SKILL.md:167-171`; the explanatory comments in `references/networking-and-backends.md` do not currently cover this flag.
- **Finding:** `MoverComponent.h:223-239` documents `bGatherInputFromAllInputProducerComponents` as the switch controlling component discovery. However, `UMoverComponent::BeginPlay` in `MoverComponent.cpp:292-312` unconditionally enumerates owner components implementing `UMoverInputProducerInterface` and appends them to `InputProducers`; `MoverComponent.cpp:340-353` then calls every valid entry. This is a source-level contract mismatch, not proof of the intended future behavior.
- **Exact proposed replacement:**

```diff
--- a/skills/core/mover-movement-system/SKILL.md
+++ b/skills/core/mover-movement-system/SKILL.md
@@
 - If the **owning actor** implements `IMoverInputProducerInterface`, the
   MoverComponent auto-registers it as its `InputProducer` at BeginPlay
   (`MoverComponent.cpp:292-302`). Actor components implementing the interface
-  are also gathered when `bGatherInputFromAllInputProducerComponents` is true
-  (`MoverComponent.h:232`).
+  are enumerated by the UE 5.8.2 `BeginPlay` implementation
+  (`MoverComponent.cpp:304-311`). Although the header documents
+  `bGatherInputFromAllInputProducerComponents` (`MoverComponent.h:230-232`) as the
+  gate, this installed source path does not read the flag. Until that source/API
+  mismatch is resolved or confirmed by Epic, do not rely on setting the flag to
+  false to suppress component producers; use one explicit producer and audit all
+  owner components that implement the interface.
```

- **Practical task benefit:** avoids silent input composition/order bugs when a pawn contains multiple input-producing components and gives agents a concrete containment strategy while the engine contract is unclear.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/MoverComponent.h:223-242` (`InputProducer`, flag, and documented contract); `.../Source/Mover/Private/MoverComponent.cpp:239-312` (`BeginPlay` discovery); `:340-353` (`ProduceInput` invokes every `InputProducers` entry). UE 5.8.2 installed source.

#### MOVER-02 — Qualify layered-move replication by backend instead of presenting it as universal

- **Priority:** P1 — network correctness; a project using the default Network Prediction backend can incorrectly assume that an arbitrary queued layered move is automatically transported to other endpoints.
- **Locations:** `skills/core/mover-movement-system/SKILL.md:241-246`; `skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md:8-14`.
- **Finding:** the repository says layered moves “replicate and participate in rollback” without naming the backend boundary. UE 5.8.2 `MoverComponent.h:316-334` calls automatic layered-move networking an advanced use case and explicitly says it is pending for general Mover, with Chaos Mover as the default networking path. The Chaos backend has distinct injection paths for layered moves (`ChaosMoverBackend.h:135-149`). Rollback participation and network transport are therefore separate claims.
- **Exact proposed replacements:**

```diff
--- a/skills/core/mover-movement-system/SKILL.md
+++ b/skills/core/mover-movement-system/SKILL.md
@@
 Layered moves (`FLayeredMoveBase`, `LayeredMove.h:74`) run *on top of* the
 current mode for a duration, each generating a proposed move mixed by
 `MixMode` (`EMoveMixMode`: additive / override velocity / override all) and
 `Priority`. They replicate and participate in rollback.
+ `FLayeredMoveBase` values participate in rollback, but network transport is
+ backend-dependent. The default Network Prediction path does not automatically
+ network every arbitrary queued move; ChaosMover has explicit move-injection and
+ scheduling paths. Confirm the selected backend before treating a queued move as
+ remote-authoritative state.
--- a/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
+++ b/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
@@
-`FLayeredMoveBase` (`LayeredMove.h:74`) = a struct that generates an
-`FProposedMove` alongside the active movement mode for some duration. They are
-stored in the sync state (`FLayeredMoveGroup`, `LayeredMove.h:191`), replicate
-to other clients, and are rewound/replayed during rollbacks — which is why
+`FLayeredMoveBase` (`LayeredMove.h:74`) = a struct that generates an
+`FProposedMove` alongside the active movement mode for some duration. They are
+stored in the sync state (`FLayeredMoveGroup`, `LayeredMove.h:191`) and are
+rewound/replayed during rollbacks. Whether they are transported to other
+endpoints depends on the backend: UE 5.8.2 documents automatic layered-move
+networking as pending for general Mover, while ChaosMover has explicit
+injection/scheduling support (`MoverComponent.h:316-334`,
+`ChaosMover/Backends/ChaosMoverBackend.h:135-149`). This is why
 `UMoverComponent::QueueLayeredMove`, `MoverComponent.h:314`)
 rather than applied immediately, and why they're cloned on queueing (configure
 fully *before* queueing).
```

- **Practical task benefit:** prevents client/server divergence caused by treating a local queue operation as universal replication and directs teams to the correct backend-specific scheduling path.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/MoverComponent.h:316-334` (`ScheduleLayeredMove` and the “only Chaos Mover networks them by default” contract); `.../Experimental/ChaosMover/Source/ChaosMover/Public/ChaosMover/Backends/ChaosMoverBackend.h:135-149` (networked/local layered-move injection). UE 5.8.2 source.

#### MOVER-03 — Replace the “locally-controlled instance” input-role statement

- **Priority:** P1 — authority/prediction correctness; the current wording excludes authority-owned Mover actors and can lead to server-side AI or platform input being placed in the wrong hook.
- **Location:** `skills/core/mover-movement-system/SKILL.md:66-69`.
- **Finding:** the installed API comment says `UMoverComponent::ProduceInput` is called on the owner’s instance “(autonomous or authority)” (`MoverComponent.h:185-186`). The ChaosMover backend separately exposes `GenerateInput` and `GenerateServerInput` (`ChaosMoverBackend.cpp:645-658`), so “locally-controlled” is too narrow for the general Mover contract. The input producer still must not read non-deterministic world state during simulation, and simulated proxies consume backend-provided state rather than authoring owner input.
- **Exact proposed replacement:**

```diff
--- a/skills/core/mover-movement-system/SKILL.md
+++ b/skills/core/mover-movement-system/SKILL.md
@@
-3. **`ProduceInput` runs only on the locally-controlled instance** and is *not*
-   re-run during resimulation — author intent there, don't simulate there.
+3. **`ProduceInput` is driven on the owning instance** (autonomous proxy or
+   authority, not only a local-player client; `MoverComponent.h:185-186`).
+   Simulated proxies consume backend-provided input/state. Keep producer output
+   deterministic and treat rollback as replay of recorded simulation inputs;
+   do not author one-shot world side effects from this hook.
```

- **Practical task benefit:** makes server-authoritative AI/platform movement and client prediction fit the same mental model without encouraging side effects in a replay-sensitive hook.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/MoverComponent.h:185-186` (owner roles); `.../Source/Mover/Public/MoverSimulationTypes.h:514-525` (`IMoverInputProducerInterface`); `.../Experimental/ChaosMover/Source/ChaosMover/Private/Backends/ChaosMoverBackend.cpp:645-658` (input/server-input paths). UE 5.8.2 source.

#### MOVER-04 — Pass a real logic class to the instanced activation example

- **Priority:** P1 — runtime correctness; the current template call passes a default-constructed, null `TSubclassOf`, so the example does not identify `UMyDashLogic` for `MakeAndQueueLayeredMove`.
- **Location:** `skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md:142-148`, specifically line 147.
- **Finding:** `MoverComponent.h:281-285` defaults the class argument to `MoveT::StaticClass()`, while `MoverComponent.cpp:2665-2683` searches registered moves using the supplied `MoveLogicClass`. The reference overrides the default with `TSubclassOf<UMyDashLogic>()`, which contains no class value.
- **Exact proposed replacement:**

```diff
--- a/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
+++ b/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
@@
-MoverComp->QueueLayeredMoveActivationWithContext(Params, TSubclassOf<UMyDashLogic>()); // :282
+MoverComp->QueueLayeredMoveActivationWithContext(Params, UMyDashLogic::StaticClass()); // :282
```

- **Practical task benefit:** makes the documented instanced-layered-move activation resolve the registered logic object instead of returning false or failing to construct the intended move.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/MoverComponent.h:255-285` (`RegisterMove` and activation template); `.../Source/Mover/Private/MoverComponent.cpp:2665-2683` (`MakeAndQueueLayeredMove` class lookup). UE 5.8.2 source.

#### MOVER-05 — Make the classic homing-move sample’s network data complete and simulation-safe

- **Priority:** P1 — rollback/network determinism; the sample serializes `Speed` but reads an unsynchronized `TWeakObjectPtr<AActor>` from `GenerateMove`, so the remote/resimulated move can target a different actor or immediately become invalid. `FLayeredMoveGroup::NetSerializeLayeredMovesArray` invokes the virtual serializer for each derived move (`LayeredMove.cpp:551-616`).
- **Location:** `skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md:67-113`.
- **Finding:** the sample’s `NetSerialize` at lines 108-113 omits `Target`; its async warning at lines 117-120 does not repair the synchronous path. `FLayeredMoveBase::NetSerialize` is virtual and the group dispatches it directly, so every field used by `GenerateMove` must be represented in the move’s deterministic data. A value snapshot is the smallest safe example; a truly dynamic actor target needs a separately replicated/network-resolvable identifier and is not supplied by this sample.
- **Exact proposed replacement:**

```diff
--- a/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
+++ b/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
@@
-    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Mover)
-    TWeakObjectPtr<AActor> Target;
+    // Capture this value before queueing; simulation code must use deterministic data.
+    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Mover)
+    FVector TargetLocation = FVector::ZeroVector;
@@
-        if (!Sync || !Target.IsValid()) { return false; }
+        if (!Sync) { return false; }
@@
-            (Target->GetActorLocation() - Sync->GetLocation_WorldSpace()).GetSafeNormal();
+            (TargetLocation - Sync->GetLocation_WorldSpace()).GetSafeNormal();
@@
         Super::NetSerialize(Ar);
         Ar << Speed;
-        // Serialize everything GenerateMove depends on; object refs need care
+        Ar << TargetLocation;
```

- **Practical task benefit:** gives agents a move that can be cloned, serialized, rolled back, and simulated without dereferencing a world UObject or silently dropping required target data.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/LayeredMove.h:74-176` (`FLayeredMoveBase::NetSerialize` contract); `.../Source/Mover/Private/LayeredMove.cpp:551-616` (derived-move allocation and virtual `NetSerialize` dispatch); `.../Source/Mover/Public/LayeredMove.h:162` (`AddReferencedObjects` is otherwise empty). UE 5.8.2 source.

#### MOVER-06 — Serialize the custom instant-effect field used to choose the movement mode

- **Priority:** P1 — ChaosMover network correctness; the custom effect stores `ModeName` and applies it, but the sample omits `UPROPERTY`/`NetSerialize`, while UE 5.8.2’s Chaos queue calls `Effect->NetSerialize(Ar)` for networked effects.
- **Location:** `skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md:172-200`.
- **Finding:** `FInstantMovementEffect::NetSerialize` is an empty virtual (`InstantMovementEffect.cpp:14-17`). `FChaosNetInstantMovementEffectsQueue::NetSerialize` dispatches to the concrete effect at `ChaosMoverSimulationTypes.cpp:231-278`. Without an override, a received `FSwapToModeAndStopEffect` keeps the default `ModeName` rather than the sender’s chosen mode.
- **Exact proposed addition:**

```diff
--- a/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
+++ b/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
@@
-    FName ModeName = DefaultModeNames::Falling;
+    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Mover)
+    FName ModeName = DefaultModeNames::Falling;
@@
     virtual FInstantMovementEffect* Clone() const override
     {
         return new FSwapToModeAndStopEffect(*this);
     }
+    virtual void NetSerialize(FArchive& Ar) override
+    {
+        Super::NetSerialize(Ar);
+        Ar << ModeName;
+    }
     virtual UScriptStruct* GetScriptStruct() const override
```

- **Practical task benefit:** preserves the requested movement-mode change across ChaosMover serialization and makes the sample’s “custom effect” contract match its actual simulation dependency.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/InstantMovementEffect.h:59-85` (virtual serializer); `.../Source/Mover/Private/InstantMovementEffect.cpp:14-17` (base is empty); `.../Experimental/ChaosMover/Source/ChaosMover/Private/ChaosMoverSimulationTypes.cpp:231-278` (concrete dispatch). UE 5.8.2 source.

#### MOVER-07 — Add the UE 5.8 scheduled-layered-move choice without making it the default

- **Priority:** P2 — synchronization quality for advanced networked physics; UE 5.8 release material calls out ahead-of-time layered-move scheduling, but the skill documents only scheduled instant effects.
- **Locations:** `skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md:207-214`; add the new subsection before `:216` “Choosing the right tool”.
- **Finding:** the installed API exposes `UMoverComponent::ScheduleLayeredMove` (`MoverComponent.h:316-338`) with an explicit delay/latency tradeoff and says to prefer `QueueLayeredMove` except when same-frame endpoint execution matters. ChaosMover has corresponding networked/local injection paths (`ChaosMoverBackend.h:135-149`). Epic’s UE 5.8 release notes describe layered moves being scheduled ahead for better synchronization. This is an advanced, backend-dependent capability, not a universal replacement for queueing.
- **Exact proposed addition:**

```diff
--- a/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
+++ b/skills/core/mover-movement-system/references/layered-moves-and-instant-effects.md
@@
 Fire-and-forget `QueueInstantMovementEffect` remains correct for the default
 Network Prediction backend.

+### Scheduled layered moves (advanced ChaosMover/networked-physics case)
+
+UE 5.8 adds `ScheduleLayeredMove` (`MoverComponent.h:316-338`) for a layered move
+that should execute on the same simulation frame at networked endpoints. It adds
+the configured scheduling delay and therefore trades responsiveness for fewer
+corrections; use ordinary `QueueLayeredMove` by default. The installed source
+documents automatic layered-move networking as pending for general Mover, while
+ChaosMover has explicit layered-move injection paths. Measure the delay and
+anticipation animation with the selected backend before adopting it.
```

- **Practical task benefit:** exposes a practical UE 5.8 synchronization tool for physics/networked movement while preventing a latency-heavy API from being applied to ordinary Network Prediction gameplay.
- **Verified evidence:** UE 5.8 release notes, “Mover: Improved Physics, Animation, and Networking,” state that layered moves can be scheduled ahead of time for better synchronization: <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8>. Installed UE 5.8.2 source: `.../Mover/Public/MoverComponent.h:316-338` (`ScheduleLayeredMove`); `.../ChaosMover/Public/ChaosMover/Backends/ChaosMoverBackend.h:135-149` (layered-move transport paths).

#### MOVER-08 — Gate async guidance on the selected backend and async implementation, not only the mode flag

- **Priority:** P2 — thread-safety and crash prevention; `bSupportsAsync` is an eligibility declaration, not a promise that a project/backend will schedule the mode off-thread.
- **Locations:** `skills/core/mover-movement-system/SKILL.md:390-393`; `skills/core/mover-movement-system/references/networking-and-backends.md:35-37`.
- **Finding:** UE 5.8.2’s `UBaseMovementMode` documents `bSupportsAsync` as an opt-in property (`MovementMode.h:116-124`), while the installed `ULayeredMoveLogic` separately requires `SupportsAsync()` when overriding `GenerateMove_Async` (`LayeredMoveBase.h:151-153,186-196`). The backend liaison and project settings still select whether async simulation runs. The current wording is directionally correct about avoiding UObject/world access but overstates the flag as the execution switch.
- **Exact proposed replacement:**

```diff
--- a/skills/core/mover-movement-system/SKILL.md
+++ b/skills/core/mover-movement-system/SKILL.md
@@
- - **Async simulation**: modes/transitions with `bSupportsAsync` may run off the
-  game thread (`MovementMode.h:121`) — no actor/world access in
-  `GenerateMove`/`SimulationTick` there; cache via the sim blackboard
-  (`GetSimBlackboard`, `MoverComponent.h:594`).
+- **Async simulation**: `bSupportsAsync` declares that a movement mode can support
+  worker-thread execution; the selected backend/settings must also schedule that
+  path (`MovementMode.h:116-124`). Keep `GenerateMove`/`SimulationTick` free of
+  actor/world access when it is selected and cache deterministic data in the sim
+  blackboard (`GetSimBlackboard`, `MoverComponent.h:594`). Instanced layered logic
+  has a separate `SupportsAsync()`/`GenerateMove_Async` contract
+  (`LayeredMoveBase.h:151-196`).
--- a/skills/core/mover-movement-system/references/networking-and-backends.md
+++ b/skills/core/mover-movement-system/references/networking-and-backends.md
@@
- `IsAsync()` liaisons run `SimulationTick` off the game thread — all modes,
- transitions, and layered moves involved must have `bSupportsAsync = true` and
- avoid touching UObjects/world state outside the provided params.
+ When an `IsAsync()` liaison/backend selects worker-thread simulation, all modes,
+ transitions, and layered moves involved must advertise their async implementation
+ (`bSupportsAsync` for modes; `SupportsAsync()` plus `_Async` overrides for
+ instanced layered logic) and avoid touching UObjects/world state outside the
+ provided params. The flags are capability gates, not a project-wide scheduler.
```

- **Practical task benefit:** avoids shipping code that passes a capability check but still reads game-thread state, and gives authors the missing instanced-layered-move contract.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Mover/Source/Mover/Public/MovementMode.h:116-124`; `.../Source/Mover/Public/LayeredMoveBase.h:151-153,186-196`; `.../Source/Mover/Public/Backends/MoverBackendLiaison.h:24` (backend interface). UE 5.8.2 source.

### No-change checks

- The installed UE 5.8.2 Mover plugin descriptor remains explicitly experimental (`Mover.uplugin:13-16`), not beta; keeping the skill’s Experimental classification and the recommendation to choose CMC when stability/legacy compatibility matters is correct. `ChaosMover.uplugin:13-16` is also experimental.
- `UMoverComponent::QueueNextMode`, `AddMovementModeFromClass`, `QueueLayeredMove`, `QueueMovementModifier`, `QueueInstantMovementEffect`, `ScheduleInstantMovementEffect`, `GetSyncState`, `GetPredictedTrajectory`, `OnPostSimulationRollback`, `FMoverDataStructBase`, `FMoverDataPersistence`, and the CMC mapping concepts remain represented by UE 5.8.2 declarations. No API rename was justified for those passages.
- The UE 5.8 source confirms the leading `FMoverSimContext` parameter on `UBaseMovementMode::GenerateMove`, the `FMoverDataStructBase` custom-state contract, and the separate `ULayeredMoveLogic`/`FLayeredMoveInstancedData` design. The existing version notes correctly identify the 5.8 ChaosMover split and the 5.7 instanced-layered-move introduction.
- The UE 5.8 release notes describe broader Mover improvements including rollback/prediction, optional Iris support in Network Prediction, adaptive time dilation, and ChaosMover trajectory/debugger work. Those are not added as generic recipes here because the repository files do not contain a matching verified project/settings workflow. Sources: [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8), [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864), [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335).

### Unresolved questions / verification gaps

- The `bGatherInputFromAllInputProducerComponents` mismatch is source-verified but not runtime-reproduced in an actor with the flag set false. It may be an engine implementation defect, a stale property, or a code path whose behavior is completed elsewhere; retain the qualification until a UE 5.8.2 project/editor test or Epic clarification resolves it.
- No Mover sample project was enabled, compiled, run in PIE, connected over a network, rolled back, or profiled under UE 5.8.2. Backend selection, Network Prediction settings, Chaos networked-physics settings, scheduled-event delay, correction frequency, and smoothing remain unvalidated.
- No custom layered move or instant effect was serialized through a live Network Prediction or ChaosMover session. The serializer findings are based on direct source dispatch and field inspection; dynamic actor-target resolution, object-reference lifetime, and security policy were intentionally not guessed.
- No plugin enablement, UHT/generated-code pass, Blueprint compilation, cooked build, dedicated server, Iris configuration, or Chaos Visual Debugger capture was exercised. The installed descriptors/source prove availability and experimental status, not production stability.
- Epic’s 5.8.1 and 5.8.2 hotfix pages were checked; no additional Mover-specific API migration was confirmed from those pages. Hotfix absence is not evidence that every Mover runtime issue is fixed.

**Source/doc set checked:** all five repository files listed above; installed UE 5.8.2 `Mover` and `ChaosMover` descriptors, public/private Mover source, `Mover/README.md`, and the targeted headers/implementations cited in each finding; UE 5.8 release notes; 5.8.1 hotfix page; 5.8.2 hotfix page. No marketplace/vendor project evidence was used.

---

## core/nanite-and-rendering

**Working-tree reconciliation:** read the added Native foliage wind section. It already distinguishes a documented Instanced Skinned Mesh/Transform Provider route from ordinary SkeletalMeshComponent and material-WPO routes. Preserve the component/asset-consumer separation and runtime-deformation gate. Its exact installed DynamicWindData/PVExportParams and vendor rotation-axis claims were not re-executed during reconciliation; they remain **partially verified** where they exceed the versioned source/doc evidence below. No component conversion, export, or wind mutation was performed.

**Status:** findings  
**Repository path:** `skills/core/nanite-and-rendering/`  
**Files reviewed:** `SKILL.md`; `references/nanite.md`; `references/rendering-pipeline.md`; `references/virtual-textures-and-shadows.md`.

### Verified recommendations

#### NANITE-RENDER-01 — remove the unsupported translucent diagnostic cvars and qualify fallback behavior

- **Priority:** P1 — correctness and debugging; agents following the current text can rely on two unverified cvars, believe a translucent mesh is guaranteed to use a Nanite fallback mesh, and miss the actual material-audit path.
- **Locations:** `skills/core/nanite-and-rendering/SKILL.md:85-98,264-269`; `references/nanite.md:87-103,134-142`.
- **Finding:** UE 5.8.2’s `FNaniteResourcesHelper::ShouldCreateNaniteProxy` rejects an unsupported blend mode and returns `false`; the Nanite shading path separately checks `Nanite::IsSupportedBlendMode` and can retry with a default material. That source does not support the blanket statement that translucent content “silently falls back to the fallback mesh.” The installed source also contains no confirmed `r.Nanite.ShowMaskedMaterialWarnings` or `r.Nanite.Validate` user diagnostic matching the current reference. `r.Nanite.AllowTranslucency` is disabled by default in the Nanite shading path and is not a production-support guarantee.
- **Exact proposed replacement:**

```diff
--- a/skills/core/nanite-and-rendering/SKILL.md
+++ b/skills/core/nanite-and-rendering/SKILL.md
@@
-Nanite works on **opaque and masked** materials. Translucent materials fall back to the
-fallback mesh. In UE 5.8 Nanite also supports:
+Nanite's standard material path supports **opaque and masked** materials. Translucent blend
+modes are not a blanket production-support case: in UE 5.8.2 the material audit can reject
+Nanite proxy creation for an unsupported blend mode, while the Nanite shading path separately
+rejects unsupported materials. Do not promise a Nanite fallback-mesh result for every
+translucent component; validate the component's conventional/fallback render path instead.
+In UE 5.8 Nanite also supports:
@@
-- **Translucent blend mode** — the Nanite fallback mesh is rendered instead.
+- **Translucent blend mode** — standard Nanite material evaluation is unsupported; use a
+  conventional/fallback mesh path unless an explicitly enabled experimental translucency
+  path has been validated for the target.
@@
-- **Nanite on translucent material** — silently falls back to the fallback mesh; no error
-  in log unless you enable `r.Nanite.ShowMaskedMaterialWarnings`.
+- **Nanite on translucent material** — do not assume a silent fallback. The 5.8.2 material
+  audit can decline Nanite proxy creation for unsupported blend modes; inspect the Output Log
+  and Primitive Debugger, and do not treat `r.Nanite.AllowTranslucency` as production support.
--- a/skills/core/nanite-and-rendering/references/nanite.md
+++ b/skills/core/nanite-and-rendering/references/nanite.md
@@
-- **Translucent materials** — Nanite cannot shade transparency; the fallback renders it.
+- **Translucent materials** — standard Nanite material evaluation rejects unsupported blend
+  modes; use the conventional/fallback path only when it is built and selected for the target.
@@
-- **`r.Nanite.ShowMaskedMaterialWarnings 1`** — logs meshes falling back due to material
-  issues.
-- **`r.Nanite.Validate 1`** — enables additional GPU-side validation (development builds).
+- **`r.Nanite.Visualize <mode>`** — use the editor Nanite visualization modes (for example
+  `Triangles`, `Clusters`, or `Primitives`) to confirm which content is using the Nanite path.
+- **Output Log and Primitive Debugger** — use the engine's material-audit warnings and the
+  editor's per-primitive status/fallback reason; do not rely on undocumented or absent
+  `r.Nanite.ShowMaskedMaterialWarnings`/`r.Nanite.Validate` commands.
```

- **Practical task benefit:** prevents invalid console-command recipes and makes translucent-material troubleshooting follow the actual 5.8.2 proxy/material checks instead of an assumed fallback outcome.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/Rendering/NaniteResourcesHelper.h:205-247,276-342` (`FNaniteResourcesHelper::ShouldCreateNaniteProxy`, `IsSupportedBlendMode`, and warning/audit path); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Renderer/Private/Nanite/NaniteShading.cpp:1102-1112` (`LoadShadingMaterial`, `Nanite::IsSupportedBlendMode`); `.../Runtime/Renderer/Private/Nanite/NaniteCullRaster.cpp:93-101` (`r.Nanite.Tessellation`, proving the nearby supported cvar is distinct); `.../Runtime/Engine/Classes/Engine/RendererSettings.h:1550-1553` (Nanite foliage setting) and `.../Runtime/Engine/Private/Rendering/NaniteResources.cpp:276-284,431-447` (the actual Nanite serialization path). UE 5.8.2 source. Matching Epic documentation: [Nanite in Unreal Engine, UE 5.8](https://dev.epicgames.com/documentation/unreal-engine/nanite-in-unreal-engine?application_version=5.8).

#### NANITE-RENDER-02 — classify Nanite foliage as experimental and retain the hotfix validation gate

- **Priority:** P1 — release-risk reduction; the current “supports Foliage” wording can make an agent enable a project-wide feature as if it were equivalent to ordinary static-mesh Nanite.
- **Locations:** `skills/core/nanite-and-rendering/SKILL.md:83-91`; `references/nanite.md:144-154`; `references/virtual-textures-and-shadows.md:146-153` is the related mobile/foliage limitation insertion point.
- **Finding:** UE 5.8.2 labels the project property `r.Nanite.Foliage` as **Nanite Foliage (Experimental)**, says it enables experimental features, and requires an editor restart. The 5.8.2 hotfix specifically fixes Nanite Voxel Foliage not rendering on some platforms and Nanite Assembly build crashes/non-determinism. Foliage should remain a scoped, target-validated experimental path rather than an unqualified supported category.
- **Exact proposed replacement:**

```diff
--- a/skills/core/nanite-and-rendering/SKILL.md
+++ b/skills/core/nanite-and-rendering/SKILL.md
@@
-- **Foliage**, including WPO wind animation (clamp displacement to avoid culling drift).
+- **Foliage Nanite (experimental in UE 5.8.2)**, including the voxel/curve paths used by
+  some foliage workflows. Enable the project setting only for a target-validated test;
+  clamp WPO displacement to avoid culling drift and retain a conventional fallback.
--- a/skills/core/nanite-and-rendering/references/nanite.md
+++ b/skills/core/nanite-and-rendering/references/nanite.md
@@
-- **Foliage Nanite**: uses voxelization and WPO animation. Foliage with small WPO offsets
-  is fine without `MaxEdgeLengthFactor`; large-scale wind requires it.
+- **Foliage Nanite (experimental in UE 5.8.2)**: `URendererSettings::bEnableNaniteFoliage`
+  (`r.Nanite.Foliage`) is explicitly marked experimental and requires an editor restart.
+  The 5.8.2 hotfix fixed Nanite Voxel Foliage failures on some platforms, so validate the
+  exact target, WPO amplitude, and fallback before shipping; large-scale wind may require
+  `MaxEdgeLengthFactor`.
```

- **Practical task benefit:** keeps agents from treating experimental foliage as ordinary Nanite and turns the 5.8.2 fix history into a concrete platform/fallback test requirement.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/RendererSettings.h:1549-1553` (`URendererSettings::bEnableNaniteFoliage`, display name/tool tip and `r.Nanite.Foliage`); UE 5.8 release notes, [Procedural Vegetation Editor (Experimental)](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#proceduralvegetationeditorexperimental); [5.8.2 Hotfix Released](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335), Nanite bug fixes at fetched note lines 283-286. UE 5.8.2 source/hotfix evidence.

#### NANITE-RENDER-03 — make optional Nanite streamable-page cooking an explicit per-platform policy

- **Priority:** P2 — package-size and fallback correctness; the current text implies that optional Nanite data is selected automatically by target support.
- **Locations:** `skills/core/nanite-and-rendering/SKILL.md:155-156`; precise insertion point after `references/nanite.md:17-19`.
- **Finding:** UE 5.8.2 exposes `URendererSettings::bNaniteStreamableBulkDataOptional` as an advanced per-platform setting. During an editor cook, `FResources::Serialize` sets `BULKDATA_OptionalPayload` only when `ShouldCookStreamablePagesAsOptional` reads that setting as true. “Target supports Nanite” alone is not the source-level condition.
- **Exact proposed addition:**

```diff
--- a/skills/core/nanite-and-rendering/SKILL.md
+++ b/skills/core/nanite-and-rendering/SKILL.md
@@
 Nanite data is divided into optional and required chunks. Cooked packages only include
 optional Nanite data if the target platform supports it. On low-end platforms, optional
 Nanite data can be stripped at cook time, leaving only the fallback mesh.
+
+For an explicit per-platform cook policy, use `URendererSettings::bNaniteStreamableBulkDataOptional`
+(Advanced Project Settings → Nanite → Cook Nanite streamable pages as optional). In UE 5.8.2,
+the editor cook applies `BULKDATA_OptionalPayload` to streamable pages only when this setting
+is true for the cooking target; it is not an automatic consequence of Nanite support. Verify
+the cooked target and its conventional fallback before relying on optional-page omission.
--- a/skills/core/nanite-and-rendering/references/nanite.md
+++ b/skills/core/nanite-and-rendering/references/nanite.md
@@
 3. **Pages** — clusters are packed into streaming pages. Root pages reside in memory at
    all times (`FResources::RootData`, `NaniteResources.h`:455); the remainder are streamed
    on demand from the `StreamablePages` bulk store (`:456`).
+
+The optional-page decision is a cook setting, not an automatic platform inference:
+`URendererSettings::bNaniteStreamableBulkDataOptional` is evaluated per target platform by
+`ShouldCookStreamablePagesAsOptional`; when true during a cook, `FResources::Serialize` marks
+the streamable bulk payload optional. Test the cooked package and fallback path on each target.
```

- **Practical task benefit:** gives packaging guidance that can actually be configured per platform and prevents an agent from assuming streamable data will be stripped merely because a target has limited Nanite support.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/RendererSettings.h:1555-1558` (`bNaniteStreamableBulkDataOptional`); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/Rendering/NaniteResources.cpp:276-284` (`ShouldCookStreamablePagesAsOptional`) and `:431-447` (`BULKDATA_OptionalPayload` around `StreamablePages.Serialize`). UE 5.8.2 source.

#### NANITE-RENDER-04 — replace deprecated mobile virtual-texture guidance

- **Priority:** P1 — upgrade correctness; UE 5.8.2 explicitly deprecates the mobile-specific setting/CVar and emits an ensure-style deprecation warning for the old CVar.
- **Locations:** `skills/core/nanite-and-rendering/references/virtual-textures-and-shadows.md:31-40,144-153`.
- **Finding:** the reference presents `bMobileVirtualTextures`/`r.Mobile.VirtualTextures` as the mobile switch while UE 5.8.2 marks `bMobileVirtualTextures_DEPRECATED` and `r.Mobile.VirtualTextures` deprecated since 5.8. The engine source directs projects to use `r.VirtualTextures` in per-platform engine ini files instead.
- **Exact proposed replacement:**

```diff
--- a/skills/core/nanite-and-rendering/references/virtual-textures-and-shadows.md
+++ b/skills/core/nanite-and-rendering/references/virtual-textures-and-shadows.md
@@
-| `bMobileVirtualTextures` | `r.Mobile.VirtualTextures` | VT on mobile — project setting deprecated in 5.8; override `bVirtualTextures` in per-platform .ini instead |
+| `bVirtualTextures` | `r.VirtualTextures` | Master VT switch; override it in the target's `<Platform>Engine.ini` when mobile/platform behavior differs |
@@
-- **Mobile VT**: requires base `r.VirtualTextures=1`; the `bMobileVirtualTextures`
-  project setting is deprecated in 5.8 (override `bVirtualTextures` per platform);
-  feature set is more limited than desktop (no RVT on all mobile paths).
+- **Mobile VT**: configure `r.VirtualTextures`/`bVirtualTextures` in the target's
+  per-platform engine ini. `bMobileVirtualTextures` and `r.Mobile.VirtualTextures` are
+  deprecated in 5.8; the latter's 5.8.2 CVar declaration directs callers to the platform
+  override. Keep mobile RVT/material support target-specific and validate the cooked path.
```

- **Practical task benefit:** removes a UE 5.8 deprecation warning from new project/configuration guidance and makes per-platform configuration explicit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/RendererSettings.h:368-370` (`bMobileVirtualTextures_DEPRECATED`); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/Texture.cpp:66-78` (`r.VirtualTextures` and `r.Mobile.VirtualTextures` with `FCVarDeprecationArgs{ TEXT("5.8")...}`). UE 5.8.2 source. Matching Epic documentation: [Virtual Texturing in Unreal Engine, UE 5.8](https://dev.epicgames.com/documentation/unreal-engine/virtual-texturing-in-unreal-engine?application_version=5.8).

#### NANITE-RENDER-05 — correct the forward-renderer/VSM configuration example

- **Priority:** P1 — render-path correctness; the current VR example tells agents that VSM is compatible with forward shading even though the UE 5.8.2 project setting explicitly selects ordinary Shadow Maps for forward shading.
- **Locations:** `skills/core/nanite-and-rendering/references/virtual-textures-and-shadows.md:134-142`; related forward/VSM statements at `SKILL.md:130-132,144-154`.
- **Finding:** `URendererSettings::ShadowMapMethod` is documented in the installed source to automatically use `Shadow Maps` when `bForwardShading` is enabled because Virtual Shadow Maps are not supported. The existing VR comment “VSM is compatible with forward but with reduced feature set” is therefore wrong for the project-level path described by the snippet.
- **Exact proposed replacement:**

```diff
--- a/skills/core/nanite-and-rendering/references/virtual-textures-and-shadows.md
+++ b/skills/core/nanite-and-rendering/references/virtual-textures-and-shadows.md
@@
 ; Nanite is disabled automatically in forward mode
-; VSM is compatible with forward but with reduced feature set
+; UE 5.8.2's RendererSettings selects ordinary Shadow Maps when Forward Shading is enabled;
+; do not rely on r.Shadow.Virtual.Enable=1 for this project path.
@@
-- **VSM with path tracer**: the path tracer uses its own shadow model and does not use VSM.
+- **VSM with forward shading**: the project setting is not supported; UE selects ordinary
+  Shadow Maps when Forward Shading is enabled. The path tracer likewise uses its own shadow
+  model and does not use VSM.
```

- **Practical task benefit:** prevents VR/forward projects from expecting VSM pages or Nanite/VSM integration that the project settings will replace with the ordinary shadow-map path.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/RendererSettings.h:665-668` (`URendererSettings::ShadowMapMethod` tooltip: “Virtual Shadow Maps are not supported” with Forward Shading). Matching Epic documentation: [Forward Shading Renderer, UE 5.8](https://dev.epicgames.com/documentation/unreal-engine/forward-shading-renderer-in-unreal-engine?application_version=5.8) and [Virtual Shadow Maps, UE 5.8](https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine?application_version=5.8).

#### NANITE-RENDER-06 — reconcile the contradictory forward/TSR table and prose

- **Priority:** P2 — configuration clarity; the same skill currently says TSR/TAAU are supported in forward shading and also says they require deferred shading.
- **Locations:** `skills/core/nanite-and-rendering/SKILL.md:156-176`.
- **Finding:** UE 5.8.2’s `URendererSettings::FixAntiAliasingOnShadingPathChange` sets desktop `DefaultFeatureAntiAliasing` to MSAA when `bForwardShading` is enabled and resets it when forward shading is disabled. Separately, `GetDefaultAntiAliasingMethod` retains `AAM_TSR` only when `SupportsTSR` is true. The source supports a qualified, platform/configuration-dependent statement, not the current contradictory “yes in the table” plus “requires deferred” claim.
- **Exact proposed replacement:**

```diff
--- a/skills/core/nanite-and-rendering/SKILL.md
+++ b/skills/core/nanite-and-rendering/SKILL.md
@@
| Method | Deferred | Forward | Notes |
|---|---|---|---|
-| TSR | yes | yes | Default UE5; best quality; requires temporal history |
-| TAAU | yes | yes | UE4-era temporal upsampler; lower quality than TSR |
+| TSR | supported when the target reports `SupportsTSR` | not the normal project default; validate the exact target/RHI | Requires temporal history; do not infer blanket forward support |
+| TAAU | temporal-AA/platform dependent | target/path dependent | UE4-era temporal upsampler; validate rather than promise forward support |
| FXAA | yes | yes | Spatial only; cheap; for low-end targets |
| MSAA | no | **yes only** | Hardware multi-sample; no Nanite support |
@@
-`RendererSettings.h`:863–866 maps `r.AntiAliasingMethod` to `EAntiAliasingMethod` (project
-setting `DefaultFeatureAntiAliasing`). Forward shading forces FXAA or MSAA; TSR/TAAU
-require deferred.
+In UE 5.8.2, `URendererSettings::FixAntiAliasingOnShadingPathChange` sets the desktop
+project default `DefaultFeatureAntiAliasing` to MSAA when `bForwardShading` is enabled and
+clears it when forward shading is disabled (`RendererSettings.cpp:201-215`). The renderer's
+`GetDefaultAntiAliasingMethod` separately falls back from TSR only when `SupportsTSR` is
+false (`SceneUtils.cpp:130-137`). Keep the exact shading-path/RHI/platform check in any
+forward TSR/TAAU advice; do not claim either blanket forward support or blanket deferred-only
+support from this table.
```

- **Practical task benefit:** removes an internal contradiction that can produce the wrong anti-aliasing config for VR and other forward-rendered targets while preserving the actual engine capability gate.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/RendererSettings.cpp:201-215` (`URendererSettings::FixAntiAliasingOnShadingPathChange`); `.../Runtime/Engine/Private/SceneUtils.cpp:74-147` (`GetDefaultAntiAliasingMethod`, `AAM_TSR`, `SupportsTSR`). UE 5.8.2 source. Matching Epic documentation: [Anti-Aliasing and Upscaling, UE 5.8](https://dev.epicgames.com/documentation/unreal-engine/anti-aliasing-and-upscaling-in-unreal-engine?application_version=5.8).

#### NANITE-RENDER-07 — pin the skill’s official documentation links to UE 5.8

- **Priority:** P2 — citation reproducibility; unqualified Epic URLs can resolve to a later engine version and undermine the report’s version-pinned guidance.
- **Location:** `skills/core/nanite-and-rendering/SKILL.md:326-343`.
- **Finding:** the reference list names UE 5.8 topics but omits `?application_version=5.8` on every URL. The audit used the version-matched pages; the skill should preserve that version selector when agents follow a citation.
- **Exact proposed replacement:**

```diff
--- a/skills/core/nanite-and-rendering/SKILL.md
+++ b/skills/core/nanite-and-rendering/SKILL.md
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/nanite-virtualized-geometry-in-unreal-engine>
-  <https://dev.epicgames.com/documentation/unreal-engine/nanite-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/nanite-virtualized-geometry-in-unreal-engine?application_version=5.8>
+  <https://dev.epicgames.com/documentation/unreal-engine/nanite-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine>
-  <https://dev.epicgames.com/documentation/unreal-engine/anti-aliasing-and-upscaling-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine?application_version=5.8>
+  <https://dev.epicgames.com/documentation/unreal-engine/anti-aliasing-and-upscaling-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/temporal-super-resolution-in-unreal-engine>
-  <https://dev.epicgames.com/documentation/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine>
-  <https://dev.epicgames.com/documentation/unreal-engine/virtual-texturing-in-unreal-engine>
-  <https://dev.epicgames.com/documentation/unreal-engine/forward-shading-renderer-in-unreal-engine>
-  <https://dev.epicgames.com/documentation/unreal-engine/designing-visuals-rendering-and-graphics-with-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/temporal-super-resolution-in-unreal-engine?application_version=5.8>
+  <https://dev.epicgames.com/documentation/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine?application_version=5.8>
+  <https://dev.epicgames.com/documentation/unreal-engine/virtual-texturing-in-unreal-engine?application_version=5.8>
+  <https://dev.epicgames.com/documentation/unreal-engine/forward-shading-renderer-in-unreal-engine?application_version=5.8>
+  <https://dev.epicgames.com/documentation/unreal-engine/designing-visuals-rendering-and-graphics-with-unreal-engine?application_version=5.8>
```

- **Practical task benefit:** keeps future agent research on the same UE 5.8 documentation revision used by this audit and prevents silent drift to later-version advice.
- **Verified evidence:** the version-matched Epic pages were fetched and checked during this audit: [Nanite Virtualized Geometry](https://dev.epicgames.com/documentation/unreal-engine/nanite-virtualized-geometry-in-unreal-engine?application_version=5.8), [Nanite](https://dev.epicgames.com/documentation/unreal-engine/nanite-in-unreal-engine?application_version=5.8), [Virtual Shadow Maps](https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine?application_version=5.8), [Anti-Aliasing and Upscaling](https://dev.epicgames.com/documentation/unreal-engine/anti-aliasing-and-upscaling-in-unreal-engine?application_version=5.8), [Virtual Texturing](https://dev.epicgames.com/documentation/unreal-engine/virtual-texturing-in-unreal-engine?application_version=5.8), and [Forward Shading Renderer](https://dev.epicgames.com/documentation/unreal-engine/forward-shading-renderer-in-unreal-engine?application_version=5.8). These are documentation-version recommendations, not API changes.

### No-change checks

- `FMeshNaniteSettings`, `GetNaniteSettings`/`SetNaniteSettings`, `IsNaniteEnabled`, `HasNaniteFallbackMesh`, `bDisallowNanite`, `bForceNaniteForMasked`, `WorldPositionOffsetDisableDistance`, `bEvaluateWorldPositionOffset`, `FGPUScene`, `FPostProcessSettings`, `ITemporalUpscaler`, `r.Nanite.Tessellation`, `r.Nanite.Visualize`, `r.Shadow.Virtual.Enable`, `r.VirtualTextures`, `r.ScreenPercentage`, and the render-thread queue concepts named by the skill remain present in UE 5.8.2. No rename or removal was justified for those passages.
- The UE 5.8 release notes’ practical Nanite-adjacent additions include experimental Procedural Vegetation Editor/Nanite foliage, experimental Mesh Terrain, Fast Geometry Streaming, and a Nanite build-settings schema for Interchange USD. Those workflows belong in their specialized skills; this section records the foliage status and does not duplicate their import/terrain guidance.
- The 5.8.1 hotfix notes include a Nanite Voxel Rasterizer GPU-crash fix and TSR fixes; the 5.8.2 hotfix notes include the Nanite Voxel Foliage platform-rendering fix and Nanite Assembly build crash/non-determinism fixes. These reinforce validation requirements above but do not establish a new public API migration.
- The report does not promote native Nanite ray tracing (`r.RayTracing.Nanite.Mode 1`) beyond the existing experimental qualification; the installed source and current skill do not provide a complete project/RHI compatibility recipe.

### Unresolved questions / verification gaps

- No static, skeletal, foliage, spline, translucent, VSM, forward, VR, or Nanite-tessellation asset was opened, rebuilt, rendered, or captured in an UE 5.8.2 project. All recommendations above are source/document/hotfix grounded, not runtime or cooked-build validation.
- The installed source proves the material audit and cvar/property declarations, but a component-specific final render path can vary with static-mesh, skeletal, foliage, scene-capture, ray-tracing, and platform code. Do not treat the audit as proof that every unsupported blend mode resolves to one identical conventional or fallback mesh path.
- No packaged target was cooked to verify optional Nanite streamable pages, fallback availability, virtual-texture page residency, VSM page allocation, or forward/VR anti-aliasing selection. A target matrix is required before shipping those settings.
- Third-party DLSS/FSR/XeSS plugins, vendor render paths, and marketplace assets were not inspected. `ITemporalUpscaler` availability and behavior beyond the engine interface remain project/plugin dependent.
- The official UE 5.8 pages and the 5.8 release/hotfix pages were checked; no 5.8.3 announcement was found in the pinned search context. This is not evidence that no later private fix exists.

**Source/doc set checked:** all four repository files listed above; installed UE 5.8.2 `Build.version`; `Engine/Source/Runtime/Engine` Nanite, renderer-settings, texture, scene, and static-mesh declarations/implementations; `Engine/Source/Runtime/Renderer` Nanite culling/shading/visualization and VSM declarations; UE 5.8 release notes; [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864); [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335); and the version-matched Epic documentation URLs cited above. No marketplace/vendor project evidence was used.

---

## core/navigating-engine-source

**Status:** findings  
**Repository path:** `skills/core/navigating-engine-source/`  
**Files reviewed:** `SKILL.md`; `references/finding-apis.md`; `references/module-map.md`; `references/source-conventions.md`.

### Verified recommendations

#### NAV-SOURCE-01 — update all embedded source-version claims to the pinned UE 5.8.2 build

- **Priority:** P1 — source-grounding correctness; a reader can otherwise inspect a 5.8.1 changelist while the audit and installed source are 5.8.2.
- **Locations:** `skills/core/navigating-engine-source/SKILL.md:265-270`; `references/module-map.md:3-5`; `references/source-conventions.md:3-5`.
- **Finding:** the main reference list says `Build.version` is 5.8.1/changelist 56057345, the module map says `PatchVersion 1`, and the source-conventions page says `Build.version: 5.8.1`. The verified installed file is promoted UE 5.8.2, changelist 56702186, compatible changelist 55116800, branch `++UE5+Release-5.8`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/navigating-engine-source/SKILL.md
+++ b/skills/core/navigating-engine-source/SKILL.md
@@
 Engine source (UE 5.8, under the verified `<UE_ENGINE_ROOT>/Engine/`):
-- Version file: `Build\\Build.version` (5.8.1, changelist 56057345).
+- Version file: `Build\\Build.version` (UE 5.8.2, changelist 56702186,
+  compatible changelist 55116800, branch `++UE5+Release-5.8`).
--- a/skills/core/navigating-engine-source/references/module-map.md
+++ b/skills/core/navigating-engine-source/references/module-map.md
@@
 Deep-dive companion to [../SKILL.md](../SKILL.md). Grounded in UE 5.8 at
 `<UE_ENGINE_ROOT>/Engine/Source` (version confirmed via
--`Engine\\Build\\Build.version`: MajorVersion 5, MinorVersion 8, PatchVersion 1).
+`Engine\\Build\\Build.version`: MajorVersion 5, MinorVersion 8, PatchVersion 2,
+Changelist 56702186).
--- a/skills/core/navigating-engine-source/references/source-conventions.md
+++ b/skills/core/navigating-engine-source/references/source-conventions.md
@@
 Deep-dive companion to [../SKILL.md](../SKILL.md). Grounded in UE 5.8 at
--`<UE_ENGINE_ROOT>/Engine/Source` (Build.version: 5.8.1).
+`<UE_ENGINE_ROOT>/Engine/Source` (Build.version: UE 5.8.2, changelist 56702186).
```

- **Practical task benefit:** prevents stale patch-level provenance from being copied into API decisions and makes the source-navigation guide agree with the engine actually used by this audit.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Build/Build.version:1-9` reports MajorVersion 5, MinorVersion 8, PatchVersion 2, Changelist 56702186, CompatibleChangelist 55116800, promoted release branch `++UE5+Release-5.8`. UE 5.8.2 installed source.

#### NAV-SOURCE-02 — narrow the UHT prefix rule to reflected types and preserve UHT exceptions

- **Priority:** P1 — compile-diagnostic accuracy; the current absolute wording treats ordinary C++ names as if UHT validates them and hides the actual reflected-type exceptions.
- **Locations:** `skills/core/navigating-engine-source/SKILL.md:101-116`; `references/source-conventions.md:11-28,131-141`.
- **Finding:** UE 5.8.2 UHT validates the Unreal prefix for reflected `UhtClass` objects, but `UhtClass::EngineNamePrefix` has class/interface/deprecated/Verse cases and `UhtScriptStruct::EngineNamePrefix` can select `T` or `F` through configuration. The table is useful as a convention, but “prefix violations are a compile error” should be scoped to UHT-parsed reflected declarations and should not imply that every C++ type or every struct uses one fixed prefix.
- **Exact proposed replacement:**

```diff
--- a/skills/core/navigating-engine-source/SKILL.md
+++ b/skills/core/navigating-engine-source/SKILL.md
@@
-UHT enforces naming conventions — knowing the prefix tells you what type you have
-and roughly where to look:
+For UHT-parsed reflected declarations, the Unreal prefix is both a naming convention and
+part of UHT validation. It is a navigation hint for ordinary C++ too, but ordinary
+non-reflected types are not thereby compile-time UHT errors:
@@
-Prefixes are enforced by UHT — a mismatch is a compile error.
+For reflected classes, UHT reports an invalid Unreal prefix during validation. Reflected
+structs can use the configured `T` or `F` prefix, and special/deprecated/Verse cases have
+their own handling; check the actual declaration rather than applying one prefix blindly.
--- a/skills/core/navigating-engine-source/references/source-conventions.md
+++ b/skills/core/navigating-engine-source/references/source-conventions.md
@@
-UE enforces type-name prefixes through UHT. Knowing the prefix tells you what
-kind of type you have and where to look:
+UHT validates Unreal prefixes for reflected declarations. For navigation, use the prefix
+as a strong hint for both reflected and ordinary engine types, but do not treat it as a
+universal C++ rule:
@@
-Prefix violations are a compile error under UHT — the tool will reject a
-`UCLASS` whose name does not start with `A` or `U`, a `USTRUCT` without `F`, etc.
+A reflected class with an invalid computed Unreal prefix is rejected by UHT. Reflected
+structs can use `F` or a configured `T` prefix, and UHT has special/deprecated/Verse cases;
+inspect the declaration and UHT validation for the type instead of assuming every
+`USTRUCT` must begin with `F`.
@@
-- Class prefix wrong (`class MyActor` instead of `AMy...`) | UHT error: "type does not comply with naming convention" | Rename; A for actors, U for UObjects, F for structs |
+- Reflected class/struct prefix wrong | UHT validation error for the computed Unreal prefix | Check the reflected type kind and UHT exceptions; use A/U for ordinary classes and F/T as applicable for structs |
```

- **Practical task benefit:** keeps the fast prefix heuristic while preventing agents from diagnosing non-reflected C++ names or configured `T`/special reflected types as unconditional UHT failures.
- **Verified evidence:** `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/Shared/EpicGames.UHT/Types/UhtClass.cs:587-610,1797-1810` (`EngineNamePrefix` and class-prefix validation); `.../Types/UhtScriptStruct.cs:898-904` (configured `T` versus `F` prefix); `.../Utils/UhtConfig.cs:197-202` (`IsStructWithTPrefix`). UE 5.8.2 UHT source.

#### NAV-SOURCE-03 — describe generated-header output separately from generated-cpp registration

- **Priority:** P2 — UHT workflow accuracy; agents troubleshooting generated code need to know which artifact contains class-body macros versus reflection definitions.
- **Locations:** `skills/core/navigating-engine-source/references/source-conventions.md:85-108`; precise insertion point after `SKILL.md:209-211`.
- **Finding:** the reference says `*.generated.h` contains “reflection tables” and `StaticClass`/virtual boilerplate as one undifferentiated artifact. UE 5.8.2 UHT generates a header containing declarations/macros such as `DECLARE_CLASS`, `DECLARE_SERIALIZER`, constructor helpers, and `Z_Construct` declarations; the code generator also has separate `*.generated.cpp`/`*.gen.cpp` filters where registration definitions are emitted. The existing do-not-edit and last-include rules remain correct.
- **Exact proposed replacement:**

```diff
--- a/skills/core/navigating-engine-source/references/source-conventions.md
+++ b/skills/core/navigating-engine-source/references/source-conventions.md
@@
 The `*.generated.h` file is produced by Unreal Header Tool (UHT) during the
 build phase before the C++ compiler runs. It contains:
- The `GENERATED_BODY()` macro expansion (reflection tables, `StaticClass()`,
-  virtual dispatch stubs, etc.)
- `DECLARE_SERIALIZER` and related boilerplate.
+- The `GENERATED_BODY()` macro expansion and class/struct helper macros such as
+  `DECLARE_CLASS`, constructor helpers, serializer declarations, and (where needed)
+  `Z_Construct_*` declarations.
+- Header-side reflection declarations and related boilerplate. Reflection registration
+  definitions/tables are emitted in generated `.gen.cpp`/`.generated.cpp` output as well;
+  do not treat the header as the complete generated reflection implementation.
@@
 The `GENERATED_BODY()` macro must appear as the **first statement** in the class
 body. Placing anything before it causes a UHT parse error.
--- a/skills/core/navigating-engine-source/SKILL.md
+++ b/skills/core/navigating-engine-source/SKILL.md
@@
 Never edit `*.generated.h` — it is produced by Unreal Header Tool (UHT) before
 the C++ compiler runs and regenerated on every build. Generated files live under
 the module's `Intermediate\\` folder, not in `Source\\`.
+
+The generated header supplies the header-side `GENERATED_BODY()`/reflection helper macros;
+UHT also emits generated `.gen.cpp`/`.generated.cpp` implementation output. Never edit
+either generated artifact; fix the reflected source header and rerun the build/UHT step.
```

- **Practical task benefit:** directs build-error investigation to the reflected source and the correct generated artifact instead of asking an agent to search for runtime registration tables in a header or edit generated output.
- **Verified evidence:** installed generated output `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/VirtualProduction/VirtualCameraCore/Intermediate/Build/Win64/UnrealGame/Inc/VCamCore/UHT/VCamTestActor.generated.h:20-50` contains `Z_Construct_UClass_AVCamTestActor` declaration, `DECLARE_CLASS2`, `DECLARE_SERIALIZER`, constructor helpers, and the `GENERATED_BODY` macro; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/Shared/EpicGames.UHT/Exporters/CodeGen/UhtCodeGenerator.cs:111-120` registers separate `*.generated.cpp`/`*.gen.cpp` and `*.generated.h` filters. UE 5.8.2 source/output.

#### NAV-SOURCE-04 — record the UE 5.8.2 UBT/UHT installed-build hotfix without inventing a generated-file workaround

- **Priority:** P2 — practical diagnosis; a missing generated output in an installed engine can be a UBT manifest problem, not a reason to hand-edit `Intermediate` files.
- **Location:** precise insertion point in `skills/core/navigating-engine-source/SKILL.md` after the generated-file rule at `:209-211`, and in `references/finding-apis.md` after Workflow 6 at `:114-118`.
- **Finding:** the 5.8.2 hotfix notes include a Build fix for missing files in the manifest that caused certain generated UHT outputs not to be included in installed builds. The current workflow predates that pinned hotfix and does not tell agents to distinguish an installed-build packaging defect from source/UHT failure.
- **Exact proposed addition:**

```diff
--- a/skills/core/navigating-engine-source/SKILL.md
+++ b/skills/core/navigating-engine-source/SKILL.md
@@
 Never edit `*.generated.h` — it is produced by Unreal Header Tool (UHT) before
 the C++ compiler runs and regenerated on every build. Generated files live under
 the module's `Intermediate\\` folder, not in `Source\\`.
+
+UE 5.8.2's hotfix notes include a UBT fix for generated UHT outputs missing from
+installed-build manifests. If an installed engine is missing a generated artifact,
+first verify the engine build/hotfix and regenerate through UBT; do not patch generated
+files or copy them into `Source\\`.
--- a/skills/core/navigating-engine-source/references/finding-apis.md
+++ b/skills/core/navigating-engine-source/references/finding-apis.md
@@
 When an API changed
 between versions, document the version it changed in the skill or code you produce.
+
+For installed-engine failures, distinguish UHT/source errors from an installed-build
+manifest issue: the UE 5.8.2 hotfix notes record a fix for certain generated UHT outputs
+missing from installed-build manifests. Verify the installed build and rerun the normal
+UBT/UHT generation path; never hand-edit generated output.
```

- **Practical task benefit:** gives agents a supported first diagnostic for missing generated files while preserving the no-manual-edit rule.
- **Verified evidence:** [5.8.2 Hotfix Released](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335), fetched note lines 160-162, “UnrealBuildTool: Fix an issue with missing files in the manifest that caused certain generated UHT outputs not to be included in installed builds.” UE 5.8.2 hotfix.

#### NAV-SOURCE-05 — pin the source-navigation Epic documentation URLs to UE 5.8

- **Priority:** P2 — citation reproducibility; the current links are labeled UE 5.8 but can resolve to the latest documentation revision.
- **Location:** `skills/core/navigating-engine-source/SKILL.md:278-286`.
- **Finding:** the official Modules, UBT, UHT, and IWYU links omit the `application_version=5.8` selector. The audit used version-matched documentation and should preserve that selector in the skill.
- **Exact proposed replacement:**

```diff
--- a/skills/core/navigating-engine-source/SKILL.md
+++ b/skills/core/navigating-engine-source/SKILL.md
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-modules>
+  <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-modules?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/unreal-build-tool-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/unreal-build-tool-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/unreal-header-tool-for-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/unreal-header-tool-for-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/include-what-you-use-iwyu-for-unreal-engine-programming>
+  <https://dev.epicgames.com/documentation/unreal-engine/include-what-you-use-iwyu-for-unreal-engine-programming?application_version=5.8>
```

- **Practical task benefit:** keeps source-navigation instructions tied to the same engine-version documentation used for this audit and avoids silent guidance drift.
- **Verified evidence:** version-matched Epic topics used for comparison: [Modules](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-modules?application_version=5.8), [UnrealBuildTool](https://dev.epicgames.com/documentation/unreal-engine/unreal-build-tool-in-unreal-engine?application_version=5.8), [Unreal Header Tool](https://dev.epicgames.com/documentation/unreal-engine/unreal-header-tool-for-unreal-engine?application_version=5.8), and [IWYU](https://dev.epicgames.com/documentation/unreal-engine/include-what-you-use-iwyu-for-unreal-engine-programming?application_version=5.8).

### No-change checks

- The five-way `Engine/Source` layout (`Runtime`, `Editor`, `Developer`, `Programs`, `ThirdParty`) matches the installed UE 5.8.2 tree. The distinction between editor/`WITH_EDITOR`, runtime, developer/tooling, plugin, and program code remains useful; no structural rewrite was required.
- The `UnrealHeaderToolMode.cs` implementation is part of `Programs/UnrealBuildTool` in UE 5.8.2, so the existing note that UHT is integrated into the UBT source tree remains correct. `EpicGames.UHT` is a shared UHT library/project referenced by UBT; this does not make UHT-generated outputs source files.
- `AActor`, `UWorld`, `UObject`, `FGameplayTag`, the module/export-macro examples, `*.generated.h`-last include ordering, `GENERATED_BODY()` placement, plugin module lookup, and focused-search workflow were checked against UE 5.8.2 paths/symbols. The API navigation method remains valid after the version corrections above.
- The module map’s representative module locations (`GameplayTags`, `Engine`, `AIModule`, `UMG`, `AssetRegistry`, `RenderCore`, `Renderer`, `TargetPlatform`, `FunctionalTesting`, `AutomationController`, and the listed plugin roots) were checked at source level. Availability in an installed tree still does not mean a project may use an editor/developer/plugin module in a packaged target.
- The 5.8.1 hotfix notes were checked for UHT/UBT/module/source-navigation changes and did not establish an additional public source-layout migration. The 5.8.2 UBT manifest fix is recorded above rather than treated as a source API change.

### Unresolved questions / verification gaps

- No custom project was run through UHT, UBT, IWYU, a full compile, Live Coding, or a packaged build under UE 5.8.2. The source examples establish declarations and UHT implementation behavior, not project-build success.
- The installed generated-header example came from an existing engine plugin Intermediate tree; the corresponding project’s full generated `.gen.cpp` output was not reconstructed in this audit. The artifact distinction is verified from UHT code-generation filters and header output, not from a fresh custom-project generation run.
- Plugin enablement can also be affected by plugin descriptors, dependencies, target type, and project configuration. The guide’s `.uproject` check is a useful minimum, but no project/plugin matrix was available to validate every plugin gating route.
- The report did not treat absent matches in broad searches as proof of removed APIs. Exact declaration checks were used where findings depend on a symbol; later patch releases can still move line numbers.
- The official UE 5.8 documentation and 5.8.1/5.8.2 hotfix pages were checked. No 5.8.3 announcement was found in the pinned search context; this does not prove that no later private fix exists.

**Source/doc set checked:** all four repository files listed above; installed UE 5.8.2 `Build.version`; `Engine/Source/Programs/UnrealBuildTool` and `Programs/Shared/EpicGames.UHT` source; representative generated UHT output under the installed engine Intermediate tree; module Build.cs/source locations cited above; UE 5.8 release notes; [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864); [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335); and the version-matched Epic documentation URLs cited above. No marketplace/vendor project evidence was used.

## core/networking-and-replication

**Status:** findings  
**Repository path:** `skills/core/networking-and-replication/`  
**Files reviewed:** `SKILL.md`; `references/fast-arrays.md`; `references/property-replication.md`; `references/replication-conditions-and-push-model.md`; `references/rpcs.md`.

### Verified recommendations

#### NET-REPL-01 — replace the deprecated public `NetUpdateFrequency` write in the canonical actor setup

- **Priority:** P1 — compile-warning and forward-compatibility correctness; agents copying the constructor example currently write a property that UE 5.8.2 explicitly marks deprecated.
- **Location:** `skills/core/networking-and-replication/SKILL.md:56-63`.
- **Finding:** the example assigns `NetUpdateFrequency = 10.f` while saying to use the setter in 5.5+. UE 5.8.2’s `AActor::NetUpdateFrequency` declaration is `UE_DEPRECATED(5.5)` and directs callers to `SetNetUpdateFrequency()`/`GetNetUpdateFrequency()`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/SKILL.md
+++ b/skills/core/networking-and-replication/SKILL.md
@@
-    NetUpdateFrequency = 10.f;   // updates/sec (use SetNetUpdateFrequency in 5.5+)
+    SetNetUpdateFrequency(10.f); // updates/sec
```

- **Practical task benefit:** copied examples compile without the known deprecation and keep the skill aligned with the public setter/getter contract.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h:902-905`, `AActor::NetUpdateFrequency` declaration and deprecation message; `SetNetUpdateFrequency()` declaration in the same `AActor` API. UE 5.8.2 `Build.version` is the pinned engine.

#### NET-REPL-02 — do not describe every plain replicated `TArray` as a whole-array transfer

- **Priority:** P1 — architecture and bandwidth guidance; the current statement can cause agents to replace a suitable ordinary replicated array with a more complex Fast Array for the wrong reason.
- **Location:** `skills/core/networking-and-replication/references/fast-arrays.md:8-16`.
- **Finding:** the reference says a plain replicated `TArray` replicates the entire array whenever one element changes. UE 5.8.2’s Fast Array header documents the generic replication path separately: `FArrayProperty::NetDeltaSerializeItem` iterates array elements and invokes property delta serialization, while Fast Array adds stable replication IDs/keys and item callbacks. The safer distinction is generic delta serialization versus Fast Array’s explicit item identity/callback model; do not promise an exact wire cost without measuring the element type and replication path.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/references/fast-arrays.md
+++ b/skills/core/networking-and-replication/references/fast-arrays.md
@@
-A plain `UPROPERTY(Replicated) TArray<FMyStruct>` replicates the **entire array** when any
-element changes. For large or frequently-modified arrays this wastes bandwidth and CPU.
+A plain `UPROPERTY(Replicated) TArray<FMyStruct>` uses Unreal's generic property-delta
+replication path when its element/property types support it; do not assume that every update
+transfers the entire array. It preserves ordinary array semantics, but it does not provide
+Fast Array's stable per-item replication IDs or item-level add/remove/change callbacks. Choose
+`FFastArraySerializer` when those identities/callbacks or its measured delta behavior justify
+the extra setup, and measure bandwidth/CPU for the actual element type and update pattern.
```

- **Practical task benefit:** prevents unnecessary migration and gives agents the real decision boundary: stable item identity/callbacks and measured cost, not an incorrect universal whole-array rule.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Net/Core/Classes/Net/Serialization/FastArraySerializer.h:183-220`, `FArrayProperty::NetDeltaSerializeItem` generic delta description and `FFastArraySerializer::FastArrayDeltaSerialize` identity/key description. The same file’s `:52-55` documents Fast Array’s own trade-off and non-guaranteed order.

#### NET-REPL-03 — put `PostReplicatedReceive` on the Fast Array serializer, not the item

- **Priority:** P1 — compile-time/API correctness; the current callback table tells readers to implement a serializer callback on the item struct, where the UE 5.8.2 template does not look for it.
- **Locations:** `skills/core/networking-and-replication/references/fast-arrays.md:135-147`; the item example at `:26-50`; the array-wrapper insertion point immediately before `:69`.
- **Finding:** `PostReplicatedAdd`, `PostReplicatedChange`, and `PreReplicatedRemove` are per-item callbacks. `PostReplicatedReceive` is detected on the derived array serializer and is called after each receiving `NetDeltaSerialize` call. The current table says “Implement these on the item struct” and lists `PostReplicatedReceive` beside the item callbacks, which is materially misleading.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/references/fast-arrays.md
+++ b/skills/core/networking-and-replication/references/fast-arrays.md
@@
     bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
     {
         return FFastArraySerializer::FastArrayDeltaSerialize<
             FInventoryItem, FInventoryArray>(Items, DeltaParms, *this);
     }
+
+    // Optional: called on the serializer after a receiving NetDeltaSerialize call.
+    void PostReplicatedReceive(
+        const FFastArraySerializer::FPostReplicatedReceiveParameters& Parameters);
 };
@@
-Implement these on the item struct. They run on the client after each delta is applied:
+Implement the first three callbacks on the item struct. They run on the client as each
+item-level add/change/removal is processed:
@@
 | `PostReplicatedAdd` | A new element arrived from the server |
 | `PostReplicatedChange` | An existing element's data changed |
 | `PreReplicatedRemove` | An element is about to be removed locally (before removal) |
-| `PostReplicatedReceive` | Called once after all per-element callbacks for a single update |
+| `PostReplicatedReceive` | Implement on `FInventoryArray`, not the item; called after a receiving `NetDeltaSerialize` call |
@@
-These are called per element as the delta is processed — the array may not be fully consistent
-when they fire. Do not modify `Items` from inside them.
+The first three are called per element as the delta is processed — the array may not be fully
+consistent when they fire. `PostReplicatedReceive` is the serializer-level hook for work after
+that receive call. Do not modify `Items` from inside the per-item callbacks.
```

- **Practical task benefit:** prevents a silent “callback never fires” integration error and makes the example compile against the actual template detection path.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Net/Core/Classes/Net/Serialization/FastArraySerializer.h:500-536` documents per-item callbacks and the serializer signature; `:699-705` (`CallPostReplicatedReceiveOrNot`) invokes `ArraySerializer.PostReplicatedReceive(...)`. UE 5.8.2 source.

#### NET-REPL-04 — correct the Push Model build-switch instruction

- **Priority:** P1 — build configuration correctness; “enable `WITH_PUSH_MODEL` in your Build.cs target” is not the supported location for the target-level switch and can send an agent looking for a nonexistent module rule property.
- **Location:** `skills/core/networking-and-replication/references/replication-conditions-and-push-model.md:105-118`.
- **Finding:** `WITH_PUSH_MODEL` is a compile-time macro consumed by Push Model headers. UE 5.8.2’s UBT exposes `bWithPushModel` on `TargetRules`, with the documented default enabled for editor targets; a module `Build.cs` is not the target-rules location. Runtime activation is separately controlled by `net.IsPushModelEnabled`. The existing ini example is useful, but it should not imply that an ini value can compile in support or that a `Build.cs` assignment is valid.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/references/replication-conditions-and-push-model.md
+++ b/skills/core/networking-and-replication/references/replication-conditions-and-push-model.md
@@
-Or enable `WITH_PUSH_MODEL` in your `Build.cs` target; check `PushModelMacros.h` for the
-preprocessor guard.
+`WITH_PUSH_MODEL` is a compile-time engine/target macro; do not try to set it in a module
+`Build.cs`. If the target configuration exposes `bWithPushModel`, set that in the target rules
+(`Target.cs`) and regenerate project files; otherwise treat the generated target's macro value
+as authoritative. This compile-time support is separate from the runtime
+`net.IsPushModelEnabled=1` setting above.
```

- **Practical task benefit:** separates UBT target configuration from module dependencies and runtime activation, reducing no-op Push Model setups and misleading Build.cs edits.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/UnrealBuildTool/Configuration/Rules/TargetRules.cs:1516-1527`, `TargetRules.bWithPushModel`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Net/Core/Public/Net/Core/PushModel/PushModelMacros.h:5`, `WITH_PUSH_MODEL`; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Net/Iris/Private/Iris/IrisConfig.cpp:15-30`, which demonstrates the separate runtime-CVar pattern for Iris. UE 5.8.2 source.

#### NET-REPL-05 — remove the false default-`_Validate` claim and make validation placement explicit

- **Priority:** P1 — security guidance; the current wording falsely suggests that omitting `WithValidation` leaves a generated always-true validation gate, which can make a reader place or audit trust checks in the wrong function.
- **Locations:** `skills/core/networking-and-replication/SKILL.md:160-171`; `references/rpcs.md:89-103`.
- **Finding:** UE 5.8.2 UHT sets `EFunctionFlags::NetValidate` when `WithValidation` is present and generates the validation declaration/check only when that flag is set. Its generated thunk calls `_Validate` only under that flag and calls `RPC_ValidateFailed` on false. It does not establish the reference’s “default `_Validate` that always returns true” behavior when the specifier is omitted. Epic’s version-matched RPC documentation describes `WithValidation` as an explicit option and documents the disconnect-on-failure behavior. Regardless of whether the optional pre-dispatch hook is used, authoritative checks must remain in the server implementation.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/SKILL.md
+++ b/skills/core/networking-and-replication/SKILL.md
@@
-|- `WithValidation` is required by Epic coding standards for all Server RPCs that accept parameters
-|  from untrusted clients. Returning `false` from `_Validate` disconnects the caller.
+|- For Server RPCs that accept untrusted input, enforce validation on the server. `WithValidation`
+|  adds the explicit UHT-generated `_Validate` pre-dispatch hook; returning `false` from it
+|  disconnects the caller. Keep authoritative authorization, range, ownership, and game-state
+|  checks in `_Implementation` as well; do not rely on a client or on a cosmetic RPC gate.
--- a/skills/core/networking-and-replication/references/rpcs.md
+++ b/skills/core/networking-and-replication/references/rpcs.md
@@
-Mandatory for all Server RPCs whose parameters come from untrusted client input. The validate
-function has the same signature as the RPC but returns `bool`:
+For a Server RPC that accepts untrusted client input, use `WithValidation` when the explicit
+pre-dispatch hook is useful. The validation function has the same signature as the RPC but
+returns `bool`; still perform authoritative authorization and state checks in
+`_Implementation`:
@@
-If `WithValidation` is omitted on a Server RPC, UHT generates a default `_Validate` that always
-returns true (a security gap for production titles).
+If `WithValidation` is omitted, UE 5.8.2 UHT does not require or dispatch a `_Validate` function;
+the generated thunk performs the validation call only when the function has the
+`EFunctionFlags::NetValidate` flag. Omission therefore does not create a safety check—validate
+untrusted input in `_Implementation`, or declare `WithValidation` and implement `_Validate`.
```

- **Practical task benefit:** keeps the security boundary in authoritative game logic and avoids both a nonexistent generated hook and the unsafe assumption that `WithValidation` replaces authorization/state validation.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/Shared/EpicGames.UHT/Specifiers/UhtFunctionSpecifiers.cs:316-326` (`WithValidationSpecifier` sets `EFunctionFlags::NetValidate`); `.../Types/UhtFunction.cs:899-924` (`needsValidate` and missing-function validation); `.../Exporters/CodeGen/UhtHeaderCodeGeneratorCppFile.cs:3505-3513` (conditional `_Validate` call and `RPC_ValidateFailed`). Epic’s UE 5.8 RPC page: <https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine?application_version=5.8>, “Server RPC Validation.”

#### NET-REPL-06 — qualify Iris maturity and preserve the installed 5.8.2 opt-in behavior

- **Priority:** P1 — migration and release-status accuracy; the current “beta and opt-in” sentence is incomplete against the UE 5.8 release notes, while treating Iris as universally production-ready would also overstate what the public docs, source defaults, and this generic skill establish.
- **Locations:** `skills/core/networking-and-replication/SKILL.md:70-73` and `:220-229`; `references/replication-conditions-and-push-model.md:159-173`.
- **Finding:** Epic’s UE 5.8 release notes call Iris “production-ready for licensees” and list protocol-mismatch/lifecycle diagnostics, serialization/cull/diagnostic refinements, re-enabled RPC DoS detection, and Scene Graph/RemoteObjects routing. The public UE 5.8 Iris documentation still describes Iris as opt-in, and the installed UE 5.8.2 source defines `net.Iris.UseIrisReplication` with default `0`; `AActor` also retains deprecation text describing the legacy hooks as part of “iris beta.” The skill should state these scopes together rather than collapsing licensee maturity, public-build defaults, and project migration into one label. The legacy hook named in the current text is also wrong: the UE 5.8.2 deprecated methods are `BeginReplication`/`EndReplication`, replaced by `OnReplicationStartedForIris`/`OnStopReplicationForIris`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/SKILL.md
+++ b/skills/core/networking-and-replication/SKILL.md
@@
-SetReplicates(true) at runtime triggers a replication start callback
-— in Iris projects (5.7+), override `OnReplicationStartedForIris` rather than the deprecated
-`OnReplicationStarted`.
+SetReplicates(true) can trigger an Iris replication-start callback when the actor is not already
+replicating. In UE 5.8.2, override `OnReplicationStartedForIris` (and use
+`OnStopReplicationForIris` for the matching stop hook); the legacy `BeginReplication` and
+`EndReplication` methods are deprecated as part of the Iris transition.
@@
-- **5.8 / Iris**: The Iris replication system remains beta and opt-in in 5.8
-  (`net.Iris.UseIrisReplication`, default off). It coexists with the
-  existing property/RPC model — existing `DOREPLIFETIME` and RPC code continues to work. Iris
-  replaces `OnReplicationStarted` (deprecated 5.7) with `OnReplicationStartedForIris`. For Push
-  Model with Iris, use `DOREPLIFETIME_WITH_PARAMS_FAST` + `bIsPushBased = true`. See
-  [references/replication-conditions-and-push-model.md](references/replication-conditions-and-push-model.md).
+- **5.8 / Iris**: Epic's 5.8 release notes call Iris production-ready for licensees, while the
+  public 5.8 documentation and UE 5.8.2 source keep it opt-in
+  (`net.Iris.UseIrisReplication`, default `0`). Treat it as a deliberate target/project choice,
+  verify the distribution and compatibility matrix, and test a server/client session before
+  enabling it. It coexists with the existing property/RPC model; existing `DOREPLIFETIME` and
+  RPC declarations are not an automatic migration. Iris-specific actor hooks are
+  `OnReplicationStartedForIris` and `OnStopReplicationForIris`; the deprecated legacy hooks are
+  `BeginReplication` and `EndReplication`. For Push Model with Iris, use
+  `DOREPLIFETIME_WITH_PARAMS_FAST` + `bIsPushBased = true`. See
+  [references/replication-conditions-and-push-model.md](references/replication-conditions-and-push-model.md).
--- a/skills/core/networking-and-replication/references/replication-conditions-and-push-model.md
+++ b/skills/core/networking-and-replication/references/replication-conditions-and-push-model.md
@@
-## Iris replication system (UE 5.8)
+## Iris replication system (UE 5.8)
@@
-Iris remains beta and opt-in in 5.8 (`net.Iris.UseIrisReplication`, default off). It coexists
-with the existing `DOREPLIFETIME` + RPC model:
+Epic's UE 5.8 release notes call Iris production-ready for licensees. The public documentation
+and the installed UE 5.8.2 source still make it an opt-in choice
+(`net.Iris.UseIrisReplication`, default `0`), so this generic skill must not imply that every
+project or distribution should enable it automatically. It coexists with the existing
+`DOREPLIFETIME` + RPC model:
@@
-|- `OnReplicationStarted` is deprecated since 5.7; override `OnReplicationStartedForIris` instead
-|  (`Actor.h`:3478).
+|- `BeginReplication` and `EndReplication` are deprecated since 5.7; use
+|  `OnReplicationStartedForIris` and `OnStopReplicationForIris` instead
+|  (`Actor.h`:3476-3500).
```

- **Practical task benefit:** agents will not enable a project-wide replication-system switch solely because a release note says “production-ready,” and they will override the actual 5.8.2 lifecycle symbols rather than a nonexistent `OnReplicationStarted` method.
- **Verified evidence:** UE 5.8 release notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:1101-1111` (“Iris: Production-Ready Replication System” for licensees); installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Net/Iris/Private/Iris/IrisConfig.cpp:15-30` (`CVarUseIrisReplication`, default `0`, `ShouldUseIrisReplication`); `.../Engine/Classes/GameFramework/Actor.h:3465-3499` (`OnReplicationStartedForIris`, `OnStopReplicationForIris`, deprecated `BeginReplication`/`EndReplication`). Public UE 5.8 documentation: <https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine?application_version=5.8>.

#### NET-REPL-07 — pin the official networking links to the audited UE 5.8 documentation revision

- **Priority:** P2 — citation reproducibility; the skill labels its links UE 5.8 but leaves the application-version selector off, allowing the documentation target to drift.
- **Locations:** `skills/core/networking-and-replication/SKILL.md:250-262`; `references/rpcs.md:4-7` and `:139-144`; `references/replication-conditions-and-push-model.md:172-174`; `references/property-replication.md:120-128`.
- **Finding:** the networking pages were fetched with `?application_version=5.8` for this audit. Preserve that selector in the repository links so later readers can distinguish the audited UE 5.8 pages from the rolling documentation.
- **Exact proposed replacement:**

```diff
--- a/skills/core/networking-and-replication/SKILL.md
+++ b/skills/core/networking-and-replication/SKILL.md
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/networking-overview-for-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/networking-overview-for-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/networking-and-multiplayer-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/networking-and-multiplayer-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/replicate-actor-properties-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/replicate-actor-properties-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/actor-network-dormancy-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/actor-network-dormancy-in-unreal-engine?application_version=5.8>
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine?application_version=5.8>
--- a/skills/core/networking-and-replication/references/rpcs.md
+++ b/skills/core/networking-and-replication/references/rpcs.md
@@
-[Remote Procedure Calls](https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine)
+[Remote Procedure Calls](https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine?application_version=5.8)
@@
-  <https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine?application_version=5.8>
--- a/skills/core/networking-and-replication/references/replication-conditions-and-push-model.md
+++ b/skills/core/networking-and-replication/references/replication-conditions-and-push-model.md
@@
-[Iris Replication System](https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine)
+[Iris Replication System](https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine?application_version=5.8)
```

- **Practical task benefit:** keeps citations reproducible for the pinned audit and reduces accidental guidance drift from future rolling docs.
- **Verified evidence:** Epic’s fetched UE 5.8 pages returned the versioned titles for [RPCs](https://dev.epicgames.com/documentation/unreal-engine/remote-procedure-calls-in-unreal-engine?application_version=5.8), [Replicate Actor Properties](https://dev.epicgames.com/documentation/unreal-engine/replicate-actor-properties-in-unreal-engine?application_version=5.8), and [Iris](https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine?application_version=5.8). The remaining listed networking topics were checked as versioned URL targets; this finding is link pinning, not a claim that every page’s examples were compile-tested.

### No-change checks

- The server-authoritative model, `HasAuthority()`/`GetLocalRole()`, ownership requirements for Server RPCs, Client/Server/Remote/NetMulticast execution matrix, reliable/unreliable distinction, and late-joiner rule for transient multicasts remain consistent with Epic’s UE 5.8 RPC documentation. The versioned page explicitly says reliable RPCs are resent until acknowledged and subsequent execution is suspended, while unreliable RPCs have no order guarantee.
- `COND_NetGroup` is not a property condition: UE 5.8.2 `CoreNetTypes.h:14-35` marks it as a subobject-only condition, and `UnrealNetwork.h:277-292` statically rejects it in `DOREPLIFETIME_CONDITION*`. The existing warning is retained.
- `DOREPLIFETIME_WITH_PARAMS_FAST` versus `_FAST_STATIC_ARRAY`, `FDoRepLifetimeParams`, `bIsPushBased`, `MARK_PROPERTY_DIRTY_FROM_NAME`, `COND_Custom`/`PreReplication`, `REPNOTIFY_OnChanged`/`REPNOTIFY_Always`, object-reference addressability, Fast Array dirty marking, stable IDs, non-guaranteed order, and `net.RPC.Debug` all have matching UE 5.8.2 declarations or implementation paths. No removal finding was inferred from broad or case-sensitive zero-match searches.
- `WithValidation` remains an accepted UE 5.8.2 UHT specifier and is used by installed engine RPC declarations; the correction above is specifically that it is explicit/conditional, not a universal language requirement or an automatically generated always-true gate when omitted.
- The 5.8.1 and 5.8.2 hotfix notes were checked for a networking-specific migration affecting this generic skill. The checked material did not establish a replacement for the ordinary property/RPC model; the 5.8 release-note Iris changes are recorded above with their licensee/opt-in qualification. Mover/Network Prediction-specific 5.8 changes remain in the separate Mover skill to avoid duplication.

### Unresolved questions / verification gaps

- No custom project was compiled or passed through UHT under UE 5.8.2, so the code blocks were checked against UHT/source declarations rather than a project build. The report does not claim that every combination of `WithValidation`, Blueprint RPCs, Iris, Push Model, Fast Arrays, static arrays, or custom serializers compiles in an arbitrary project.
- No dedicated-server/client session, packet-loss test, net emulation run, NetTrace capture, Iris protocol-compatibility test, RPC flood test, or bandwidth/CPU measurement was run. Reliability, dormancy, relevancy, ownership, Push Model, and Fast Array recommendations remain source/documentation-grounded, not runtime-validated.
- The generic array correction is based on the UE 5.8.2 Fast Array header’s description of generic delta serialization; no representative project was profiled to quantify when a plain `TArray` beats or loses to a Fast Array.
- The 5.8 release-note “production-ready for licensees” wording does not define the public-distribution support policy or guarantee a particular project/plugin target. Verify the actual distribution, target rules, enabled Iris modules, server/client protocol, and project migration plan before enabling Iris.
- `net.IsPushModelEnabled` was treated as a runtime setting from the repository guidance and Push Model source context; no fresh packaged target was built to prove the effective `WITH_PUSH_MODEL` value for every target type. The report therefore says to inspect generated target configuration rather than asserting a universal shipping default.
- No marketplace/vendor plugin project was entered. Product-specific replication layers, custom NetSerializers, Replication Graph configurations, and vendor networking claims remain outside this audit.
- The 5.8.3 status was not reinterpreted from this skill: no 5.8.3 announcement was found in the pinned search context, which does not prove that no later private or unreleased fix exists.

**Source/doc set checked:** all five repository files listed above; installed UE 5.8.2 `Build.version`; `Runtime/Engine/Classes/GameFramework/Actor.h`; `Runtime/Engine/Public/Net/UnrealNetwork.h`; `Runtime/CoreUObject/Public/UObject/CoreNetTypes.h`; `Runtime/Net/Core/Classes/Net/Serialization/FastArraySerializer.h`; `Runtime/Net/Core/Public/Net/Core/PushModel/PushModel.h`; `Runtime/Net/Core/Public/Net/Core/PushModel/PushModelMacros.h`; `Runtime/Net/Iris/Private/Iris/IrisConfig.cpp`; `Programs/Shared/EpicGames.UHT/Specifiers/UhtFunctionSpecifiers.cs`; `Programs/Shared/EpicGames.UHT/Types/UhtFunction.cs`; `Programs/Shared/EpicGames.UHT/Types/UhtClass.cs`; `Programs/Shared/EpicGames.UHT/Exporters/CodeGen/UhtHeaderCodeGeneratorCppFile.cs`; `Programs/UnrealBuildTool/Configuration/Rules/TargetRules.cs`; `Runtime/Engine/Private/DataReplication.cpp`; the versioned Epic UE 5.8 RPC, property-replication, and Iris documentation; UE 5.8 release notes; [5.8.1 Hotfix](https://forums.unrealengine.com/t/5-8-1-hotfix-released/2738864); and [5.8.2 Hotfix](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335). No marketplace/vendor project evidence was used.

---

## core/niagara-vfx

**Status:** findings  
**Repository path:** `skills/core/niagara-vfx/`  
**Files reviewed:** `SKILL.md`; `references/data-interfaces-and-performance.md`; `references/spawning-and-parameters.md`; `references/system-and-emitter-model.md`.

### Verified recommendations

#### NIAGARA-01 — correct the CPU/GPU collision matrix and qualify GPU ray tracing

- **Priority:** P1 — correctness; the current table assigns GPU scene-query mechanisms to CPU emitters and omits that the installed Collision Query data interface has both CPU and GPU execution paths. Agents following it can select a GPU-only collision mode for a CPU simulation or treat experimental ray tracing as ordinary collision support.
- **Locations:** `skills/core/niagara-vfx/SKILL.md:137-150`; `skills/core/niagara-vfx/references/data-interfaces-and-performance.md:42-49` and `:109-126`.
- **Finding:** UE 5.8.2 declares `UNiagaraDataInterfaceCollisionQuery::PerformQuerySyncCPU`/`PerformQueryAsyncCPU`, shader functions, and `CanExecuteOnTarget(...) { return true; }`; its CPU path is the world/geometry-query path while its GPU path uses scene data. `UNiagaraDataInterfaceAsyncGpuTrace` is GPU-only and may require a ray-tracing scene. Epic’s UE 5.8 collision page labels GPU hardware-ray-tracing collisions **Experimental**. The current `SKILL.md` row reverses the practical CPU/GPU distinction (`depth-buffer`, `distance-field`, and `ray-trace` appear under CPU) and “near-zero on game thread” is not a total-cost guarantee.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/SKILL.md
+++ b/skills/core/niagara-vfx/SKILL.md
@@
 | Feature | CPU emitters | GPU emitters |
 |---|---|---|
 | Max particle count | ~tens of thousands | millions |
 | Gameplay read-back | yes (position queries, events) | not supported |
-| Collision | depth-buffer, distance-field, ray-trace (5.7), or none | distance-field/scene-depth only |
+| Collision | CPU Collision Query/world geometry traces, or none; do not treat GPU scene queries as CPU traces | distance-field/scene-depth paths; `Async Gpu Trace` is GPU-only and hardware-ray-tracing collision is Experimental |
 | Per-particle callbacks | yes | no |
-| Game-thread cost | scales with count | near-zero on game thread |
+| Game-thread cost | CPU simulation/query work scales with count; measure it | no direct per-particle game-thread readback, but dispatch/render/GPU work still costs time |
```

```diff
--- a/skills/core/niagara-vfx/references/data-interfaces-and-performance.md
+++ b/skills/core/niagara-vfx/references/data-interfaces-and-performance.md
@@
 | DI | CPU/GPU | Mechanism |
 |---|---|---|
-| Collision Query | CPU | Per-particle line/capsule trace against `UWorld::LineTrace*` |
-| GPU Collision (Distance Field) | GPU | Distance-field scene query; no gameplay call-back |
-| GPU Collision (Depth Buffer) | GPU | Screen-space depth reprojection; view-dependent |
-| HWRT Collision | GPU (5.3+) | Hardware ray-tracing; most accurate; requires DXR |
+| Collision Query | CPU and GPU paths | CPU VM geometry queries; GPU shader path uses the scene data required by the DI |
+| Async Gpu Trace | GPU only | Latent GPU scene traces; the provider can require a ray-tracing scene |
+| GPU Collision (Distance Field/Depth Buffer) | GPU | Distance-field or screen-space depth collision; view/platform dependent |
+| HWRT Collision | GPU, Experimental | Hardware ray-tracing collision; requires a supported DXR configuration |
@@
-- Collision is limited to distance-field, depth-buffer, or HWRT (5.3+). No complex-mesh traces.
+- Collision uses the GPU-supported distance-field/depth-buffer paths or the separate async GPU
+  trace path; do not promise CPU-style complex-mesh traces or gameplay callbacks from GPU particles.
```

- **Practical task benefit:** prevents an invalid CPU/GPU collision choice and keeps experimental hardware ray tracing from being presented as a universal production path; it also directs agents to measure total render/GPU cost rather than optimize only game-thread time.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraDataInterfaceCollisionQuery.h:24-26,45-64` (`UNiagaraDataInterfaceCollisionQuery`, CPU query methods, shader methods, `CanExecuteOnTarget`, `RequiresGlobalDistanceField`, `RequiresDepthBuffer`); `.../Classes/NiagaraDataInterfaceAsyncGpuTrace.h:13-15,47-50` (`UNiagaraDataInterfaceAsyncGpuTrace`, GPU-only target and `RequiresRayTracingScene`); `.../Classes/NiagaraCollision.h:12-18` (`ENiagaraCollisionMode`); `.../Public/NiagaraGpuComputeDispatchInterface.h:29-35` (`FNiagaraGpuComputeDispatchInterface`). Epic UE 5.8 [Collisions in Niagara](https://dev.epicgames.com/documentation/unreal-engine/collisions-in-niagara-for-unreal-engine?application_version=5.8) explicitly labels GPU Ray Tracing Collisions Experimental. These are source/declaration checks, not a hardware or runtime collision validation.

#### NIAGARA-02 — migrate the Data Channel example off the legacy library/function

- **Priority:** P1 — API-forward compatibility; the current C++ example uses the UE 5.8.2 function that Epic marks “LEGACY” and names a class that does not match the installed declaration. New code will get the wrong migration signal and may accumulate deprecation work.
- **Locations:** `skills/core/niagara-vfx/references/data-interfaces-and-performance.md:84-105`, especially the example at `:90-101`; the explanatory replacement text at `:104-105`.
- **Finding:** in UE 5.8.2 the class is `UNiagaraDataChannelLibrary`, not `UNiagaraDataChannelFunctionLibrary`. `WriteToNiagaraDataChannel(...)` taking `FNiagaraDataChannelSearchParameters` is retained as a legacy function; its header says to use the non-legacy access-context API. The current source exposes `WriteToNiagaraDataChannel_WithContext(...)` with `FNDCAccessContextInst&`. The old function remains available in 5.8.2, so this is a migration recommendation, not an API-removal claim.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/references/data-interfaces-and-performance.md
+++ b/skills/core/niagara-vfx/references/data-interfaces-and-performance.md
@@
-// Access a Data Channel from C++ (typically via UNiagaraDataChannelFunctionLibrary):
+// Access a Data Channel from C++ with the UE 5.8 access-context API:
 #include "NiagaraDataChannelFunctionLibrary.h"
+#include "NiagaraDataChannelAccessContext.h"
 
-// Begin a write of one element to a channel asset; fill fields via the returned writer:
-UNiagaraDataChannelWriter* Writer = UNiagaraDataChannelFunctionLibrary::WriteToNiagaraDataChannel(
-    this,
-    ExplosionsChannel,                      // UNiagaraDataChannelAsset*
-    FNiagaraDataChannelSearchParameters(),  // locates where the data lands in the world
-    /*Count*/ 1,
-    /*bVisibleToGame*/ true, /*bVisibleToCPU*/ true, /*bVisibleToGPU*/ true,
-    TEXT("MyGame"));
+FNDCAccessContextInst AccessContext;
+AccessContext.Init(TNDCAccessContextType(FNDCAccessContext::StaticStruct()));
+FNDCAccessContext& Context = AccessContext.GetChecked<FNDCAccessContext>();
+Context.Location = GetActorLocation(); // world-space location in this AActor example
+Context.bOverrideLocation = true;
+
+// Begin a write of one element to a channel asset; fill fields via the returned writer:
+UNiagaraDataChannelWriter* Writer =
+    UNiagaraDataChannelLibrary::WriteToNiagaraDataChannel_WithContext(
+        this,
+        ExplosionsChannel,                  // UNiagaraDataChannelAsset*
+        AccessContext,
+        /*Count*/ 1,
+        /*bVisibleToBlueprint*/ true,
+        /*bVisibleToNiagaraCPU*/ true,
+        /*bVisibleToNiagaraGPU*/ true,
+        TEXT("MyGame"));
@@
-Data Channels are primarily a gameplay-to-Niagara bus. For cross-system communication within
-the same world, they replace the older approach of reading actor positions via DIs.
+Data Channels facilitate communication between game code and Niagara, or between Niagara
+systems, and can combine work into a shared simulation. They are not a blanket replacement for
Data Interfaces: use a DI when a system samples an external object/source, and use a Data Channel
when decoupled publishers/readers need shared data. Prefer the access-context API above for new
UE 5.8 code; the SearchParameters overload is retained for legacy compatibility.
```

- **Practical task benefit:** agents will emit the current class/function names, get the new routing/context API instead of starting from a legacy overload, and avoid substituting a cross-system bus for a Data Interface that owns external-source sampling.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraDataChannelFunctionLibrary.h:20-50` (`UNiagaraDataChannelLibrary` and legacy `WriteToNiagaraDataChannel`), `:137-163` (`ReadFromNiagaraDataChannel_WithContext` and `WriteToNiagaraDataChannel_WithContext`); `.../Public/NiagaraDataChannelAccessContext.h:112-169,235-276` (`FNDCAccessContext`, `FNDCAccessContextInst`); `.../Source/NiagaraBlueprintNodes/Private/K2Node_DataChannel_WithContext.cpp:21-39` binds Blueprint nodes to `UNiagaraDataChannelLibrary`. Epic UE 5.8 [Niagara Data Channels](https://dev.epicgames.com/documentation/unreal-engine/data-channels-in-niagara-for-unreal-engine?application_version=5.8) describes NDCs as communication between game code/Niagara and between systems. The replacement snippet was source-shaped but was not compiled in a project.

#### NIAGARA-03 — remove `Render` as a Niagara module stack group

- **Priority:** P1 — authoring correctness; the current execution model makes a renderer look like a writable stack group and can lead an agent to place modules or namespace writes where the editor does not support them.
- **Locations:** `skills/core/niagara-vfx/SKILL.md:38-40`; `skills/core/niagara-vfx/references/system-and-emitter-model.md:31-43` and `:48-63`.
- **Finding:** Epic’s UE 5.8 Key Concepts page distinguishes modules from items and identifies renderers as items, while the installed `ENiagaraScriptUsage` enum contains System/Emitter/Particle script usages plus particle event and simulation-stage usages—not a Render module-script usage. Renderer properties are consumed by the render path; they are not a normal user-authored module stack group. The current reference table’s `Render` row and `Output.*` “Render group” wording should be replaced, while preserving the valid event/simulation-stage concepts.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/SKILL.md
+++ b/skills/core/niagara-vfx/SKILL.md
@@
-Execution flows top-to-bottom within each **stack group**: Emitter Spawn → Emitter Update →
-Particle Spawn → Particle Update → Event Handlers → Render. Each stage carries a **namespace**
-(System, Emitter, Particle, User, Engine) that controls read/write access.
+Execution is organized around System, Emitter, and Particle stack groups. Each has Spawn and
+Update stages; Event Handler and Simulation Stage usages are optional advanced stages. Renderers
+are renderer-property items that consume simulation output after the relevant simulation work;
+they are not a general writable module stack group. Each module stage uses namespaces
+(System, Emitter, Particle, User, Engine) to control read/write access.
--- a/skills/core/niagara-vfx/references/system-and-emitter-model.md
+++ b/skills/core/niagara-vfx/references/system-and-emitter-model.md
@@
-Every emitter's module stack is divided into **groups** (run in this order per frame):
+System, Emitter, and Particle are the normal module stack groups. Event Handler and Simulation
+Stage are optional script usages; a renderer is an output item, not a module stack group.
@@
-| Event Handler | Generate / Listen | Conditional; same or next frame | Cross-emitter or particle-to-particle events |
-| Render | — | Every frame (render thread) | Defines how particles are drawn |
-| Simulation Stage (GPU only) | — | Multiple ordered passes | Fluid, grids, custom iterative algorithms |
+| Event Handler (`ParticleEventScript`) | Generate / Listen | Conditional; same or next frame | Cross-emitter or particle-to-particle events |
+| Simulation Stage (`ParticleSimulationStageScript`) | — | Multiple ordered passes; advanced GPU workflow | Fluid, grids, custom iterative algorithms |
+| Renderer item | Renderer properties, not a module stack group | Render path | Consumes particle/system outputs and defines drawing |
@@
-| `Output.*` | Renderer inputs | Render group | Particle/Render groups |
+| Renderer bindings | Renderer-specific inputs consumed by renderer items; do not model this as a writable Render group | Renderer item consumes simulation output |
```

- **Practical task benefit:** keeps module authoring, event handlers, simulation stages, and renderer configuration in their actual scopes, reducing invalid stack edits and namespace assumptions.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraCommon.h:1102-1132` (`ENiagaraScriptUsage`, including `ParticleEventScript`, `ParticleSimulationStageScript`, `EmitterSpawnScript`, `SystemSpawnScript`, and update usages) and `:1134-1161` (`ENiagaraScriptUsageMask`); `.../Classes/NiagaraEmitterHandle.h:101-102` (`ForEachEnabledRendererWithIndex`). Epic UE 5.8 [Niagara Key Concepts](https://dev.epicgames.com/documentation/unreal-engine/key-concepts-in-niagara-effects-for-unreal-engine?application_version=5.8) states that renderers are items rather than modules and documents the System/Emitter/Particle groups. This is a source/documentation model check, not a compiled editor asset check.

#### NIAGARA-04 — model standard and stateless emitters and capture the 5.8.2 null-data fix

- **Priority:** P1 — hotfix correctness; the current hierarchy promises a `UNiagaraEmitter` for every handle, but UE 5.8.2 explicitly fixes a crash when `Handle.GetEmitterData()` is null for a Stateless handle during original compilation.
- **Locations:** `skills/core/niagara-vfx/SKILL.md:31-36`; `skills/core/niagara-vfx/references/system-and-emitter-model.md:13-25` and `:80-86`; the version note at `SKILL.md:213-219`.
- **Finding:** `FNiagaraEmitterHandle` has `ENiagaraEmitterMode::Standard` and `Stateless`, exposes `GetEmitterData()`, `GetEmitterBase()`, `GetStatelessEmitter()`, and `GetEmitterMode()`, and can therefore represent more than the standard `UNiagaraEmitter` asset. The official UE 5.8 lightweight-emitter page calls lightweight emitters “stateless emitters” and describes their goal as reducing or eliminating tick. The 5.8.2 hotfix specifically fixes the null `GetEmitterData()` path. The skill should not make “one handle → non-null standard emitter data” an invariant.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/SKILL.md
+++ b/skills/core/niagara-vfx/SKILL.md
@@
-| Emitter | `UNiagaraEmitter` | `FNiagaraEmitterInstance` (internal) | One particle behavior set (sparks, smoke, decal); several per system |
+| Emitter | `UNiagaraEmitter` in Standard mode or `UNiagaraStatelessEmitter` in Stateless mode | mode-specific runtime representation | One particle behavior set; several handles can belong to a system |
@@
-Lightweight Emitters (reduced overhead for simple effects) are in active development; see
-  the Niagara Lightweight Emitters doc for current status.
+Lightweight Emitters are also called Stateless Emitters in UE 5.8. They target reduced or
+eliminated simulation tick overhead for supported module subsets; do not assume that every
+standard emitter module or runtime accessor applies to a Stateless emitter.
--- a/skills/core/niagara-vfx/references/system-and-emitter-model.md
+++ b/skills/core/niagara-vfx/references/system-and-emitter-model.md
@@
- └── FNiagaraEmitterHandle[]   — one handle per emitter in the system
-      └── UNiagaraEmitter      — emitter asset (may be shared across systems)
+ └── FNiagaraEmitterHandle[]   — one handle per emitter in the system
+      └── Standard: `UNiagaraEmitter` / `FVersionedNiagaraEmitterData`, or
+          Stateless: `UNiagaraStatelessEmitter`
@@
-`UNiagaraSystem::GetEmitterHandles()` returns the handle array. Each `FNiagaraEmitterHandle`
-carries a name, enabled flag, and a versioned reference to the `UNiagaraEmitter` asset.
+`UNiagaraSystem::GetEmitterHandles()` returns the handle array. Each `FNiagaraEmitterHandle`
+carries a name, enabled flag, emitter mode, and mode-specific instance/reference. In Standard
+mode use the versioned emitter data/base; in Stateless mode use the stateless accessor and do
+not assume `GetEmitterData()` is non-null.
@@
-## Lightweight Emitters (5.5+)
+## Lightweight / Stateless Emitters (5.5+)
@@
-Lightweight Emitters are a stripped-down emitter type optimized for simple single-burst effects
- (impacts, hit sparks) where the full stack overhead is unnecessary. They have reduced memory and
- CPU overhead. In 5.8, Lightweight Emitters support a subset of modules; see the
+Lightweight Emitters, also called Stateless Emitters, are a stripped-down emitter mode optimized
+to reduce or eliminate tick work for supported simple effects. They are not limited to a
+single-burst use case by this description, and they support a subset of modules. In 5.8, see the
 [Niagara Lightweight Emitters](https://dev.epicgames.com/documentation/unreal-engine/niagara-lightweight-emitters)
 doc for current feature coverage.
```

- **Practical task benefit:** agents will branch on emitter mode before dereferencing standard emitter data, and the skill will reflect the actual lightweight/stateless contract rather than the pre-hotfix crash assumption.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraEmitterHandle.h:15-20` (`ENiagaraEmitterMode`), `:81-95` (`GetEmitterData`, `GetEmitterBase`, `GetStatelessEmitter`, `GetEmitterMode`); UE 5.8.2 hotfix cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/forums.unrealengine.com-d1d8d96bf4.md:287-288`, [5.8.2 Hotfix Released](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335); Epic UE 5.8 [Niagara Lightweight Emitters](https://dev.epicgames.com/documentation/unreal-engine/niagara-lightweight-emitters?application_version=5.8). This verifies declarations and the release-note fix; no Stateless asset was compiled or run.

#### NIAGARA-05 — qualify parameter-setter timing instead of promising a universal one-frame latency

- **Priority:** P1 — temporal correctness; the current reference presents every setter call during execution as a one-frame-late operation, but the installed controller API makes the behavior conditional on the controller’s async configuration and simulation lifecycle.
- **Locations:** `skills/core/niagara-vfx/references/spawning-and-parameters.md:55-69` and `:146-173`; the related setter guidance in `skills/core/niagara-vfx/SKILL.md:87-113`.
- **Finding:** `FNiagaraSystemInstanceController.h` defines `NIAGARA_SYSTEM_INSTANCE_CONTROLLER_ASYNC` as `0` by default, where `SetVariable_Deferred` passes through to `SetVariable`; when the macro is enabled, the same operation is enqueued in the world manager’s deferred method queue. The component also exposes override-parameter storage and reset/synchronization APIs. Therefore “next simulation tick” is a useful conservative expectation for an already-running instance, but “there is a one-frame latency” is not a universal API guarantee across activation order, tick group, and controller configuration.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/references/spawning-and-parameters.md
+++ b/skills/core/niagara-vfx/references/spawning-and-parameters.md
@@
-3. On the next simulation tick, the value is forwarded into the live system instance's parameter
-   store and becomes visible to modules.
+3. The component stores the override and forwards it through the system-instance controller;
+   an already-running instance observes it on a subsequent applicable simulation step. The exact
+   same-frame/next-frame point depends on activation order, tick group, and whether the Niagara
+   controller is configured for deferred asynchronous operations.
@@
-Parameters set **before** `Activate()` are applied when the instance starts. Parameters set
-**during** execution take effect on the next tick — there is a one-frame latency. If you need
-instantaneous effect at spawn, set parameters before calling `Activate(true)` or before passing
-the component to a spawn function.
+Parameters set **before** `Activate()` are applied when the instance starts. For deterministic
+initial values, set them before calling `Activate(true)` or before handing the component to a
+spawn function. For an active instance, treat a setter as applying before a subsequent applicable
+simulation step; do not promise a universal one-frame latency without testing the project’s tick
+and controller configuration.
@@
-All `SetVariable*` calls after `SpawnSystemAtLocation` take effect on the first simulation tick
-(one-frame latency). For effects that are sensitive to the initial parameters, set them before
-activation by creating the component manually with `bAutoActivate = false`, setting parameters,
-then calling `Activate()`.
+`SetVariable*` calls after `SpawnSystemAtLocation` update the spawned component’s overrides and
+are observed by a subsequent applicable simulation step. For effects that are sensitive to the
+initial parameters, create the component with `bAutoActivate = false`, set parameters, then call
+`Activate()`. If exact frame ordering matters, verify it in the project’s chosen tick groups;
+the API does not make a universal one-frame promise.
```

- **Practical task benefit:** prevents frame-sensitive gameplay code from relying on an undocumented universal delay while preserving the safe pre-activation pattern for initial values.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraSystemInstanceController.h:11-25` (`NIAGARA_SYSTEM_INSTANCE_CONTROLLER_ASYNC` and deferred macro), `:107-112` (deferred controller methods), and `:161-164` (pooled reuse/internal deferred setter); `.../Public/NiagaraComponent.h:744-757` (`GetOverrideParameters`, `OnSystemFinished`, `SetUserParametersToDefaultValues`). This is a declaration/control-flow check; no project tick-order or PIE timing test was run.

#### NIAGARA-06 — correct component-pool ownership and reset semantics

- **Priority:** P1 — lifecycle correctness; the current text calls `UNiagaraComponentPool` a `UWorldSubsystem` and says manual-release callers must reset parameters themselves, neither of which matches the installed 5.8.2 reuse path.
- **Location:** `skills/core/niagara-vfx/references/spawning-and-parameters.md:116-130`.
- **Finding:** `UNiagaraComponentPool` derives from `UObject` and is returned by `FNiagaraWorldManager::Get(World)->GetComponentPool()`. On pooled reuse, `UNiagaraComponent::OnPooledReuse` calls `SetUserParametersToDefaultValues()` before the component is reused. `ManualRelease` controls when `ReleaseToPool()` is requested; it does not create a separate parameter-reset contract. Callers still need to apply the current instance’s overrides after acquisition and must not rely on prior component state.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/references/spawning-and-parameters.md
+++ b/skills/core/niagara-vfx/references/spawning-and-parameters.md
@@
-The pool lives on the `UWorld` as a `UNiagaraComponentPool` subsystem. Pool components must have
-`SetUserParametersToDefaultValues()` called before reuse to prevent parameter bleed-through
-between instances — the pooling system does this automatically for `AutoRelease` components, but
-you are responsible for `ManualRelease` components.
+`UNiagaraComponentPool` is a transient `UObject` owned by the Niagara world manager and accessed
+as `FNiagaraWorldManager::Get(World)->GetComponentPool()`; it is not a `UWorldSubsystem`. On
+pooled reuse, `UNiagaraComponent::OnPooledReuse` calls
+`SetUserParametersToDefaultValues()` to clear local overrides and prevent parameter bleed-through
+for pooled components. `ManualRelease` controls when `ReleaseToPool()` is requested; it does not
+remove the reuse reset. Apply each instance’s current overrides after acquisition and do not rely
+on the previous user-parameter values.
```

- **Practical task benefit:** avoids teaching agents to look up a nonexistent subsystem and avoids redundant/manual-only reset logic that obscures the actual reuse lifecycle.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraComponentPool.h:65-83` (`UNiagaraComponentPool : public UObject`), `.../Public/NiagaraWorldManager.h:199-200` (`GetComponentPool`), `.../Private/NiagaraComponent.cpp:1972-1979` (`OnPooledReuse` calls `SetUserParametersToDefaultValues`), and `:816-845` (`ReleaseToPool`, `ENCPoolMethod::ManualRelease`, pool reclaim). This source path check did not measure pool allocation or reuse performance.

#### NIAGARA-07 — add the scoped UE 5.8 Niagara features that materially affect authoring and profiling

- **Priority:** P2 — practical feature coverage; the current version notes omit two directly useful UE 5.8 additions that can replace custom trigger logic or change GPU sorting choices.
- **Locations:** precise insertion point after `skills/core/niagara-vfx/SKILL.md:213-219`, and optionally after the Niagara Debugger subsection at `references/data-interfaces-and-performance.md:153-165`.
- **Finding:** Epic’s UE 5.8 release notes add the `Spawn By Trigger` module, which spawns particles when a bool flips false-to-true, and add a GPU Bitonic Sort algorithm with a configurable count heuristic that can choose Bitonic over Radix. The installed Niagara content contains `SpawnByTrigger.uasset`; the installed source contains GPU sort declarations/implementation. These are feature-availability notes, not a claim that every renderer/platform or every threshold is faster.
- **Exact proposed addition:**

```diff
--- a/skills/core/niagara-vfx/SKILL.md
+++ b/skills/core/niagara-vfx/SKILL.md
@@
 ## Version notes
 
 - `SetNiagaraVariable*` (string overloads) deprecated since 5.3; use `SetVariable*` (FName).
 - `GetSystemInstance()` deprecated since 5.0; use `GetSystemInstanceController()`.
 - `NiagaraDataChannel` (cross-system communication) introduced in 5.3, expanded in 5.4/5.5.
-- Lightweight Emitters (reduced overhead for simple effects) are in active development; see
-  the Niagara Lightweight Emitters doc for current status.
+- **5.8:** The `Spawn By Trigger` emitter module spawns particles when a bool changes from
+  false to true; use it for a simple edge-triggered spawn instead of maintaining a custom
+  bool-edge module.
+- **5.8:** GPU particle sorting adds Bitonic Sort, and a configurable count heuristic can choose
+  Bitonic over Radix. Profile the target GPU/particle count rather than assuming one algorithm
+  wins universally.
+- Lightweight Emitters are also called Stateless Emitters; see the UE 5.8 documentation for
+  the supported module subset and current feature coverage.
```

- **Practical task benefit:** gives effect authors a native trigger module and makes the new GPU sorting option discoverable without promising a fixed performance result.
- **Verified evidence:** UE 5.8 release-notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:10542-10550` (`Spawn By Trigger` and GPU Bitonic Sort); installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Content/Modules/Emitter/SpawnByTrigger.uasset`; `.../Source/Niagara/Classes/NiagaraGPUSortInfo.h` (`FGPUSortInfo` declarations) and `.../Source/NiagaraVertexFactories/Private/NiagaraSortingGPU.cpp` (GPU sorting implementation); Epic UE 5.8 [Niagara Lightweight Emitters](https://dev.epicgames.com/documentation/unreal-engine/niagara-lightweight-emitters?application_version=5.8). Content/source presence and release-note text were verified; no editor module graph or GPU benchmark was run.

#### NIAGARA-08 — replace universal particle-count thresholds with measured budgets

- **Priority:** P1 — performance guidance accuracy; `~10k`, “tens of thousands,” “millions,” and “near-zero” are useful intuition but are presented as if they were portable engine limits.
- **Locations:** `skills/core/niagara-vfx/SKILL.md:137-150`; `skills/core/niagara-vfx/references/data-interfaces-and-performance.md:107-126` and `:167-176`.
- **Finding:** Niagara’s cost depends on module work, renderer, data interfaces, collision mode, GPU feature level, view count, memory bandwidth, scalability, and platform. Epic’s UE 5.8 debugging page directs users to the Niagara Debugger and profiling tools; it does not establish a universal CPU/GPU particle-count cutoff. The installed source also exposes GPU dispatch and asynchronous/overlap behavior, so “GPU” is not equivalent to free work or zero synchronization cost.
- **Exact proposed replacement:**

```diff
--- a/skills/core/niagara-vfx/SKILL.md
+++ b/skills/core/niagara-vfx/SKILL.md
@@
-| Max particle count | ~tens of thousands | millions |
+| Scale | CPU capacity varies with modules, data interfaces, collisions, and target frame budget | GPUs can handle very large counts, but capacity varies with shader work, renderer, memory, and platform |
@@
-Choose **CPU** when gameplay logic needs to read particle data or react to collisions. Choose
-**GPU** for massive counts (explosions, rain, ambient particles) where gameplay read-back is
-not required. Each emitter in a system chooses independently; a system can mix CPU and GPU
-emitters.
+Choose **CPU** when gameplay logic needs supported particle data/events or CPU collision behavior.
+Choose **GPU** when the workload benefits from GPU simulation and does not require direct
+per-particle game-thread read-back. Treat “massive” as a measured project/platform budget, not
+a fixed count; each emitter still chooses independently and systems can mix CPU and GPU emitters.
```

```diff
--- a/skills/core/niagara-vfx/references/data-interfaces-and-performance.md
+++ b/skills/core/niagara-vfx/references/data-interfaces-and-performance.md
@@
-- Scales to ~tens of thousands of particles before game-thread cost becomes significant.
+- There is no engine-wide particle-count cutoff; measure the selected modules, data interfaces,
+  collision path, and target frame budget with `stat Niagara`/the Niagara Debugger.
@@
-- Supports millions of particles; the only game-thread overhead is the dispatch call.
+- Can support very large particle counts on suitable hardware, but dispatch, render-thread/GPU,
+  memory, and renderer costs still apply; do not treat GPU simulation as zero total cost.
@@
-- **CPU emitter with thousands of particles** — VectorVM scales but each batch is a
-  game-thread synchronization point. Profile with `stat Niagara`; switch to GPU at ~10k+.
+- **CPU emitter with a measured budget overrun** — VectorVM and data-interface work scale with
+  the selected workload. Profile with `stat Niagara`/the Niagara Debugger and move work to GPU
+  only when the target platform and feature set support that trade-off; there is no universal
+  `~10k` switch point.
```

- **Practical task benefit:** preserves the CPU-versus-GPU decision while preventing agents from applying a threshold that can be wrong by platform, renderer, or module graph.
- **Verified evidence:** Epic UE 5.8 [Debugging and Optimization in Niagara](https://dev.epicgames.com/documentation/unreal-engine/debugging-and-optimization-in-niagara-effects-for-unreal-engine?application_version=5.8) documents the Niagara Debugger, particle counts, memory, GPU dispatch information, and performance budgeting; installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraGpuComputeDispatchInterface.h:29-35` (`FNiagaraGpuComputeDispatchInterface`) and `.../Source/Niagara/Classes/NiagaraDataInterface.h:724-734` (`PostSimulateCanOverlapFrames`, `PostStageCanOverlapTickGroups`). These are measurement/source boundaries, not a runtime profile of a particular project.

### No-change checks

- The core spawn declarations used by the skill are present in UE 5.8.2: `UNiagaraFunctionLibrary::SpawnSystemAtLocation` and `SpawnSystemAttached` in `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraFunctionLibrary.h`; `UNiagaraComponent::Activate`, `Deactivate`, `DeactivateImmediate`, `SetAsset`, `SetVariableFloat`, `SetVariableVec3`, `SetVariableBool`, `SetVariableInt`, `SetVariableLinearColor`, `SetVariableActor`, `OnSystemFinished`, and `bAutoDestroy` in `.../Public/NiagaraComponent.h`. The `bPreCullCheck` parameter and null-return warning remain appropriate, subject to the project’s scalability configuration.
- The `SetNiagaraVariable*` string-overload deprecation is real in the installed UE 5.8.2 header: `NiagaraComponent.h:463-475`, `:481-502`, `:508-529`, `:535-547`, and `:553-565` use `UE_DEPRECATED(5.3, ...)`; the FName `SetVariable*` forms remain the current alternatives. No removal finding was inferred from deprecation alone.
- The User Parameter model, `FNiagaraUserRedirectionParameterStore`, mesh override helpers, `GetVariableFloat`, `ENCPoolMethod::None`/`AutoRelease`/`ManualRelease`, `ReleaseToPool`, `OnSystemFinished`, `ANiagaraActor`, and mixed CPU/GPU emitter concepts have matching UE 5.8.2 declarations or implementation paths. The corrections above narrow wording rather than remove these APIs.
- The UE 5.8 release notes’ Niagara entries include the trigger module, GPU Bitonic Sort, Niagara Debug HUD filter control, random-jitter/ramp dynamic inputs, async factory workflows, and a Chaos Destruction data-interface indexing fix. The scoped trigger/sort additions are recorded above; the remaining editor-only or specialized entries do not justify adding a broad workflow section to this gameplay-oriented skill.
- The separately reviewed UE 5.8.1 and UE 5.8.2 hotfix material was checked for Niagara entries. The actionable 5.8.2 Stateless `GetEmitterData()` null crash fix is recorded in NIAGARA-04; no additional hotfix item established a required migration to the ordinary spawn/setter/pooling API in this generic skill.
- Epic’s UE 5.8 [Niagara Key Concepts](https://dev.epicgames.com/documentation/unreal-engine/key-concepts-in-niagara-effects-for-unreal-engine?application_version=5.8), [Niagara Data Channels](https://dev.epicgames.com/documentation/unreal-engine/data-channels-in-niagara-for-unreal-engine?application_version=5.8), [Collisions in Niagara](https://dev.epicgames.com/documentation/unreal-engine/collisions-in-niagara-for-unreal-engine?application_version=5.8), [Debugging and Optimization in Niagara](https://dev.epicgames.com/documentation/unreal-engine/debugging-and-optimization-in-niagara-effects-for-unreal-engine?application_version=5.8), and [Niagara Lightweight Emitters](https://dev.epicgames.com/documentation/unreal-engine/niagara-lightweight-emitters?application_version=5.8) were fetched with the UE 5.8 selector and matched the topics used above.

### Unresolved questions / verification gaps

- No UE project was generated or compiled under 5.8.2. The proposed Data Channel access-context snippet, all C++ spawn examples, UHT exposure, module dependency setup, and Blueprint-facing calls were checked against installed declarations but not compiled in a project.
- No Niagara System, emitter, module graph, Stateless emitter, Data Channel asset, or Niagara Debugger session was opened. The `SpawnByTrigger.uasset` check proves installed content presence only; it does not prove editor discoverability, module compatibility in every emitter mode, or a particular graph’s compile result.
- No CPU/GPU simulation, GPU ray-tracing collision, async trace, Data Channel read/write, event-handler, pooling reuse, pre-cull, scalability, shader-compilation, packaged-build, or cooked-content test was run. Claims above remain source/documentation/release-note grounded, not runtime-validated.
- The exact frame at which a parameter setter becomes visible can vary with activation order, tick group, controller async configuration, and system graph dependencies. Verify a project-specific timing contract before using a setter for same-frame gameplay authority.
- The current reference’s “CPU emitters only” event wording was not converted into an API-removal claim. Installed script-usage declarations and documentation establish event/simulation-stage concepts, but this audit did not run a representative GPU event-handler compile/runtime matrix.
- GPU sorting heuristics, collision support, particle capacities, renderers, Data Interfaces, and hardware-ray-tracing behavior remain platform and feature-level dependent. No benchmark, render capture, GPU crash test, or Unreal Insights capture was available.
- Niagara is an installed engine plugin and the repository’s module-dependency examples were not validated against a project’s enabled-plugin/configuration set. No marketplace/vendor Niagara project was entered, so vendor-specific emitters, modules, Data Interfaces, and pool wrappers remain outside scope.
- The pinned search context found no 5.8.3 announcement; that does not prove that no later private, unreleased, or distribution-specific Niagara fix exists.

**Source/doc set checked:** all four repository files listed above, each read in full; installed UE 5.8.2 `Build.version`; `Plugins/FX/Niagara/Source/Niagara/Public/NiagaraFunctionLibrary.h`; `Public/NiagaraComponent.h`; `Public/NiagaraSystemInstanceController.h`; `Public/NiagaraDataChannelFunctionLibrary.h`; `Public/NiagaraDataChannelAccessContext.h`; `Public/NiagaraDataChannelCommon.h`; `Public/NiagaraWorldManager.h`; `Public/NiagaraComponentPool.h`; `Public/NiagaraGpuComputeDispatchInterface.h`; `Classes/NiagaraEmitterHandle.h`; `Classes/NiagaraCommon.h`; `Classes/NiagaraDataInterface.h`; `Classes/NiagaraDataInterfaceCollisionQuery.h`; `Classes/NiagaraDataInterfaceAsyncGpuTrace.h`; `Classes/NiagaraCollision.h`; `Private/NiagaraComponent.cpp`; `Source/NiagaraBlueprintNodes/Private/K2Node_DataChannel_WithContext.cpp`; `Content/Modules/Emitter/SpawnByTrigger.uasset`; `Classes/NiagaraGPUSortInfo.h`; `NiagaraVertexFactories/Private/NiagaraSortingGPU.cpp`; the UE 5.8 release-notes cache; the UE 5.8.1 hotfix material; the UE 5.8.2 hotfix cache; and the version-matched Epic Niagara documentation URLs cited above. No marketplace/vendor project evidence was used.

---

## core/packaging-and-deployment

**Status:** findings  
**Repository path:** `skills/core/packaging-and-deployment/`  
**Files reviewed:** `SKILL.md`; `references/buildcookrun-and-uat.md`; `references/cook-and-build-configs.md`; `references/pak-iostore-and-chunking.md`; `references/platform-and-dlc.md`.

### Verified recommendations

#### PACK-01 — replace unsupported or misnamed BuildCookRun switches

- **Priority:** P1 — CI correctness; a copied command can silently ignore intended policy or fail with an unknown UAT parameter when it uses switches that are not declared by UE 5.8.2 `ProjectParams`.
- **Locations:** `skills/core/packaging-and-deployment/references/buildcookrun-and-uat.md:58-72` and `:74-83`; the `-warningsaserrors` argument in its example at `:104-121`; `skills/core/packaging-and-deployment/SKILL.md:90-124` for the canonical command context.
- **Finding:** UE 5.8.2 `ProjectParams.cs` parses `CookAll`, `SkipCookingEditorContent`, `Manifests`, `CreateChunkInstall`, `IoStore`, and the other documented stage flags. It does not define a `warningsaserrors` or `generatechunks` BuildCookRun parameter, and the supported skip-editor switch is `SkipCookingEditorContent`. Warning-as-error behavior is a project packaging setting (`bTreatWarningsAsErrorsOnCook`) read by the cooker, not the lowercase `-warningsaserrors` UAT switch shown here. Chunk manifest/install generation is represented by `-manifests` and `-createchunkinstall`, with the latter requiring staging and manifests.
- **Exact proposed replacement:**

```diff
--- a/skills/core/packaging-and-deployment/references/buildcookrun-and-uat.md
+++ b/skills/core/packaging-and-deployment/references/buildcookrun-and-uat.md
@@
 | `-allmaps` | Cook all maps discovered in the project |
 | `-map=<map>` | Cook only specified maps (repeatable) |
 | `-iterate` | Iterative cook — skip unchanged packages |
-| `-skipeditorcontent` | Skip `Editor/` content directories during cook |
+| `-SkipCookingEditorContent` | Skip editor content during cook |
 | `-cookall` | Cook every package in the Content/ directory |
 | `-compressed` | Compress cooked packages |
 | `-unversioned` | Remove version data from packages (smaller patches, fragile) |
-| `-warningsaserrors` | Treat cook warnings as errors (CI recommendation) |
 | `-ddc=<graph>` | Override DDC backend graph (e.g. a shared DDC network path) |
 | `-numcookerstospin=<N>` | Spin up N additional cook-worker processes |
@@
 | `-pak` | Wrap cooked content in `.pak` files |
 | `-iostore` | Use IoStore (`.utoc` / `.ucas`) container format |
 | `-makebinaryconfig` | Bake config into a binary file for faster startup |
-| `-generatechunks` | Split content into numbered chunks |
-| `-nochunks` | Override: disable chunking even if Project Settings enables it |
+| `-manifests` | Generate streaming-install manifests while cooking configured chunks |
+| `-createchunkinstall` | Generate streaming-install data from manifests; requires `-stage` and `-manifests` |
 | `-encrypt` | Apply encryption (key config comes from `CryptoKeys.json`) |
@@
   -iostore ^
   -archive ^
-  -archivedirectory=D:\Builds\MyGame_Win64_Shipping ^
-  -warningsaserrors
+  -archivedirectory=D:\Builds\MyGame_Win64_Shipping
```

Set cook warning policy in project configuration instead of inventing a UAT flag:

```diff
--- a/skills/core/packaging-and-deployment/references/cook-and-build-configs.md
+++ b/skills/core/packaging-and-deployment/references/cook-and-build-configs.md
@@
 `DirectoriesToAlwaysCook` and `DirectoriesToNeverCook` in `UProjectPackagingSettings`
 apply the same logic at directory granularity without touching the Asset Manager rules.
+
+For CI that must fail on cooker warnings, enable `bTreatWarningsAsErrorsOnCook` in
+`[/Script/UnrealEd.ProjectPackagingSettings]`. UE 5.8.2's cooker reads that setting and sets
+`GWarn->TreatWarningsAsErrors`; do not use an undocumented `-warningsaserrors` BuildCookRun flag.
```

- **Practical task benefit:** makes the reference command line use switches that UE 5.8.2 actually parses and gives CI an engine-supported warning policy path.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/AutomationTool/AutomationUtils/ProjectParams.cs:846-858` parses `SkipCookingEditorContent`, `Compressed`, `IoStore`, and cook flags; `:929-934` parses `Manifests`, `CreateChunkInstall`, and chunk-install paths; `:1644-1654` declares `[Help("manifests")]` and `[Help("createchunkinstall")]`; `:3359-3362` requires `-createchunkinstall` to use `-manifests` and `-stage`. The same UE 5.8.2 source has no `warningsaserrors` or `generatechunks` `ProjectParams` switch in the checked UAT source. `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Developer/DeveloperToolSettings/Classes/Settings/ProjectPackagingSettings.h:461-477` declares `bTreatWarningsAsErrorsOnCook`, and `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Editor/UnrealEd/Private/CookOnTheFlyServer.cpp:6630-6634` consumes it. The versioned Epic [Build Operations](https://dev.epicgames.com/documentation/unreal-engine/build-operations-cooking-packaging-deploying-and-running-projects-in-unreal-engine?application_version=5.8) page confirms BuildCookRun’s build/cook/stage/package/deploy/run stages. This is source-level flag verification; no UAT command was run.

#### PACK-02 — update Zen cooked-output and Incremental Cooking status without erasing project-config exceptions

- **Priority:** P1 — UE 5.8 workflow accuracy; the version note says Zen Store is off by default and treats `-iterate` as the only iteration story, while Epic’s UE 5.8 release notes promote Zenserver cooked output to the default workflow and keep Incremental Cooking explicitly Beta.
- **Locations:** `skills/core/packaging-and-deployment/SKILL.md:186-193` and `:226-233`; `references/cook-and-build-configs.md:121-130`; `references/pak-iostore-and-chunking.md:43-45`.
- **Finding:** Epic’s UE 5.8 release notes say Incremental Cooking remains **Beta**, uses Zen Server to compare changes, and that Zenserver as cooked output store is enabled by default for the new workflow while existing projects that disabled it remain disabled. The UE 5.8.2 source exposes `bUseZenStore`, `bUseIoStore`, and `GetUseZenStoreEffective()` (`bUseZenStore && bUseIoStore`), but does not encode a universal C++ default in the constructor. The versioned Zen documentation still contains older “as of 5.5 … disabled by default” wording, so the safe skill guidance is to report the release-note workflow change, retain the Beta label, and require inspection of the effective project/platform config rather than claiming every project is on or off.
- **Exact proposed replacement:**

```diff
--- a/skills/core/packaging-and-deployment/SKILL.md
+++ b/skills/core/packaging-and-deployment/SKILL.md
@@
 ## Version notes
 
-**IoStore as modern default:** `bUseIoStore` defaults to `true` for new projects as of
-  UE5. Classic `.pak`-only builds still work. Console platforms often require IoStore.
-**Zen Store** (`bUseZenStore`): introduced in UE5, off by default, used by some large
-  first-party titles to centralize cooked data.
+**IoStore:** `bUseIoStore` is a project/platform setting; the UE 5.8.2 source does not make
+  this generic skill’s “modern” wording a universal default. Inspect the effective project
+  settings and UAT arguments. Classic `.pak` output remains a separate supported choice where
+  the target platform permits it.
+**Zenserver cooked output store (UE 5.8):** the release notes describe Zenserver as enabled by
+  default for the new cooked-output workflow, while existing projects that disabled Zen remain
+  disabled. `GetUseZenStoreEffective()` still requires both `bUseZenStore` and `bUseIoStore`.
+**Incremental Cooking (Beta, UE 5.8):** Zen-backed incremental cooking reduces recooking of
+  unchanged native assets, including Blueprints and World Partition tiles. Keep it separate from
+  ordinary `-iterate`/iterative cook guidance, and do not treat the Beta workflow as a clean
+  release-cook replacement.
```

```diff
--- a/skills/core/packaging-and-deployment/references/cook-and-build-configs.md
+++ b/skills/core/packaging-and-deployment/references/cook-and-build-configs.md
@@
 Iterative cook is appropriate for rapid iteration during development. For CI/release
 builds, always do a full (non-iterative) cook from a clean Saved/Cooked directory to
 guarantee a deterministic output. A stale cooked package with the same hash as the
 source but a different runtime dependency can silently produce a broken build.
+
+UE 5.8 also documents **Incremental Cooking (Beta)** backed by Zenserver. It is a distinct
+Zen-backed iteration workflow, not a new guarantee that `-iterate` is safe for release builds.
+Use it for development iteration only until the project has verified its determinism, CI
+lifecycle, and clean-release process; inspect the effective `bUseZenStore`/`bUseIoStore`
+configuration because existing projects can retain Zen disabled.
```

- **Practical task benefit:** agents will not misclassify a Beta iteration path as a release cook, will know why Zen appears in UE 5.8 editor workflows, and will preserve existing-project configuration exceptions.
- **Verified evidence:** UE 5.8 release-notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:1141-1163` (Incremental Cooking Beta; Zenserver cooked output default/new-workflow and existing-project exception); installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Developer/DeveloperToolSettings/Classes/Settings/ProjectPackagingSettings.h:244-254` (`bUseIoStore`, `bUseZenStore`) and `:667-670` (`GetUseZenStoreEffective`); `.../Private/ProjectPackagingSettings.cpp:29-48` (constructor and invalid Zen-without-IoStore warning); `.../Programs/AutomationTool/AutomationUtils/ProjectParams.cs:814-831` (UAT IoStore/Zen switches). Epic UE 5.8 [Zen Storage Server as Cooked Output Store](https://dev.epicgames.com/documentation/unreal-engine/using-zen-storage-server-as-cooked-output-store-for-unreal-engine?application_version=5.8) and [Zenserver Streaming](https://dev.epicgames.com/documentation/unreal-engine/how-to-use-zenserver-streaming-to-play-on-target-in-unreal-engine?application_version=5.8) were fetched; the former retains older default-status wording, which is why the recommendation explicitly calls for effective-config inspection rather than a universal default claim.

#### PACK-03 — classify IoStore On-Demand/Zen streaming as constrained development or delivery infrastructure

- **Priority:** P1 — deployment and security accuracy; the current text presents On-Demand as a general shipped-game CDN system and says it requires an `IoStoreOnDemand` plugin without establishing that project-level plugin/hosting/security setup.
- **Locations:** `skills/core/packaging-and-deployment/SKILL.md:186-193`; `references/platform-and-dlc.md:67-97`.
- **Finding:** UE 5.8.2 exposes `UE::IoStore::IOnDemandIoStore`, request statuses, mount/install operations, and `TryGetOnDemandIoStore()`, but the UAT path is explicitly opt-in: `-applyiostoreondemand` forces the workflow, adds `-CompileIoStoreOnDemand`, and forces manifests; `IoStoreOnDemandSettings` defaults to disabled when no settings are supplied. Epic’s Zenserver streaming documentation warns that Zenserver is unauthenticated and intended for trusted networks/non-shipping development configurations. The current wording conflates this with a production CDN/content-delivery contract and asserts a plugin name that was not established by an installed `.uplugin` descriptor in this audit.
- **Exact proposed replacement:**

```diff
--- a/skills/core/packaging-and-deployment/SKILL.md
+++ b/skills/core/packaging-and-deployment/SKILL.md
@@
-## Content-on-demand / IoStore On-Demand
-
-The IoStore On-Demand system (`Runtime/Experimental/IoStore/OnDemand/`) allows a shipped
-game to fetch content from a CDN at runtime rather than requiring it to be installed
-upfront. The `IOnDemandIoStore` interface (`IoStoreOnDemand.h`) manages requests with
-statuses Pending / Ok / Cancelled / Error. This is the foundation for streaming installs,
-live-service content drops, and large-world on-demand streaming beyond what the base chunk
-system handles.
+## Content-on-demand / IoStore On-Demand (optional/experimental scope)
+
+UE 5.8.2 exposes the IoStore On-Demand interfaces under the experimental runtime source tree,
+but this is not a generic “ship a CDN” switch. UAT enables the path with
+`-applyiostoreondemand`, which adds `-CompileIoStoreOnDemand` and forces chunk manifests; the
+settings default to disabled when no On-Demand settings are supplied. Treat hosting,
+authentication/authorization, mount policy, failure recovery, patch compatibility, and target
+platform support as project-owned delivery infrastructure. For ordinary shipping distribution,
+use the project’s validated container/patch/DLC pipeline until an On-Demand integration has
+been tested end to end.
```

```diff
--- a/skills/core/packaging-and-deployment/references/platform-and-dlc.md
+++ b/skills/core/packaging-and-deployment/references/platform-and-dlc.md
@@
-The IoStore On-Demand system (`Runtime/Experimental/IoStore/OnDemand/`) enables a
-shipped game to fetch content from a CDN at runtime without requiring the full install
-upfront — the foundation for streaming installs and live-service drops.
+The IoStore On-Demand system lives under the experimental runtime source tree and is an
+optional integration, not a complete CDN/security service. In UE 5.8.2, UAT’s
+`-applyiostoreondemand` path compiles the On-Demand support and forces manifests; without that
+explicit path, `IoStoreOnDemandSettings` is initialized disabled. Validate the host groups,
+authorization model, install/mount lifecycle, failure handling, patch compatibility, and target
+platform before considering it for a shipped product.
@@
-The on-demand system requires chunks to be staged as IoStore containers (`bUseIoStore`
-must be true) and hosted on a CDN or HTTP server. The client mounts the table of
-contents (`.utoc`) eagerly and fetches `.ucas` blocks lazily as game code triggers loads.
+The on-demand workflow requires the project’s IoStore/manifest settings and an integration that
+can provide the generated containers and request service. The installed interface exposes
+request states and container/install operations; it does not by itself establish a public-CDN
+security or delivery contract. Keep the `bUseIoStore`/manifest prerequisites explicit and test
+the actual platform and host implementation.
```

- **Practical task benefit:** prevents a project from treating an experimental/optional interface as an authenticated production CDN and makes the required UAT opt-in visible.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Experimental/IoStore/OnDemandCore/Public/IO/IoStoreOnDemand.h:45-82` (`FOnDemandRequest` status API), `:646-782` (`IOnDemandIoStore`, factory, `TryGetOnDemandIoStore`); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/AutomationTool/AutomationUtils/ProjectParams.cs:1116-1129` (`ApplyIoStoreOnDemand`, `-CompileIoStoreOnDemand`, forced manifests, default `IoStoreOnDemandSettings`), `:2535-2542` (UAT help and settings); no installed `*IoStoreOnDemand*.uplugin` descriptor was found in the checked Engine tree. Epic UE 5.8 [Zenserver Streaming](https://dev.epicgames.com/documentation/unreal-engine/how-to-use-zenserver-streaming-to-play-on-target-in-unreal-engine?application_version=5.8) explicitly limits Zenserver streaming to trusted networks and non-shipping configurations and warns that it is unauthenticated. No CDN, platform, or production delivery test was run.

#### PACK-04 — separate chunk assignment from delivery, mounting, and download policy

- **Priority:** P1 — deployment correctness; chunk IDs and `.pak`/IoStore files do not themselves cause a launcher, platform, patcher, or runtime downloader to deliver or mount content.
- **Locations:** `skills/core/packaging-and-deployment/SKILL.md:126-145`; `references/pak-iostore-and-chunking.md:47-65`; `references/platform-and-dlc.md:99-155`.
- **Finding:** UE 5.8 documentation says chunking creates independently distributable collections and that higher-ID chunks are separated into files. The installed settings describe chunk generation, dependency assignment, and maximum sizes, while UAT separately exposes manifests and chunk-install generation. The current “Chunks 1+ are downloaded separately,” “chunk 0 is always present,” and fixed optional-pak/mount-priority language is too absolute for projects using different launchers, platform streaming-install systems, DLC plugins, patch manifests, or IoStore. Chunk assignment is packaging metadata; delivery/mount behavior must be configured and verified by the chosen platform/integration.
- **Exact proposed replacement:**

```diff
--- a/skills/core/packaging-and-deployment/SKILL.md
+++ b/skills/core/packaging-and-deployment/SKILL.md
@@
 **Chunking** splits content across multiple pak/IoStore containers for streaming installs,
-DLC, or patching. Each chunk maps to a numbered `.pak` / `.ucas` file (e.g.
-`pakchunk1-Windows.pak`). Chunk 0 is the base install; chunks 1+ are downloaded
-separately. Configure via `bGenerateChunks = true` and Primary Asset Rules.
+DLC, or patching. Each configured chunk is packaging metadata that may produce numbered
+container files (for example `pakchunk1-Windows.pak`); the platform/launcher/patch/DLC
+integration decides how those files are delivered and mounted. Do not infer from a chunk ID
+alone that a file is downloaded separately or that chunk 0 is always the complete base install.
+Configure chunk generation with `bGenerateChunks` and Primary Asset Rules, then generate and
+inspect the manifests required by the selected delivery path.
```

```diff
--- a/skills/core/packaging-and-deployment/references/pak-iostore-and-chunking.md
+++ b/skills/core/packaging-and-deployment/references/pak-iostore-and-chunking.md
@@
 Chunking splits a project's content into numbered containers for independent distribution.
 Each chunk produces one `pakchunkN-[Platform].pak` / `.utoc`/`.ucas` triplet.
 
-**Chunk 0** is the base install — always present, always downloaded. Everything not
-assigned to a higher chunk falls into chunk 0 by default.
+**Chunk 0** is the default/catch-all chunk for assets without another assignment in the
+documented Asset Manager model. Whether it is always present or how other chunks are installed
+is determined by the platform and delivery integration, not by the chunk ID alone.
 
-**Chunks 1+** are downloaded separately (streaming install, DLC, patch, on-demand).
+**Chunks 1+** are separate packaging outputs that can be delivered through streaming install,
+DLC, patch, or on-demand systems after their manifests and mount/download policy are configured.
@@
-Pak filenames follow the pattern `pakchunk[N]-[Platform][_s#].pak` where `_s#` suffix
-indicates a split chunk (when `MaxChunkSize` is hit).
+Generated names and split suffixes are implementation/output conventions, not a universal
+runtime mount-priority contract; inspect the staged manifest/container output for the target
+platform and delivery system.
```

```diff
--- a/skills/core/packaging-and-deployment/references/platform-and-dlc.md
+++ b/skills/core/packaging-and-deployment/references/platform-and-dlc.md
@@
-When the game mounts multiple paks at startup (base + patches + DLC), paks are sorted
-by priority (pak file name encodes the priority). A pak mounted later with higher
-priority overrides packages present in an earlier pak. The default priority ordering is:
-1. Base paks (pakchunk0, pakchunk1, …)
-2. Patch paks (pakchunk0-patch, …)
-3. DLC paks (optional paks)
+When a project mounts multiple containers at startup, the selected platform/patch/DLC
+integration defines mount order and conflict behavior. Do not use the illustrative filename
+groups below as a universal priority contract; validate the generated manifest and the runtime
+mount code for the target platform.
@@
-Custom mount priority can be set explicitly via `FPakPlatformFile::Mount()` if your
-code mounts paks at runtime.
+For legacy pak runtime mounting, custom code may call the installed `FPakPlatformFile::Mount()`
+path; that API does not define IoStore mount semantics or replace the platform’s delivery
+manifest.
```

- **Practical task benefit:** avoids shipping content that is chunked but never delivered/mounted and prevents filename conventions from being mistaken for a cross-platform patch-order guarantee.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Developer/DeveloperToolSettings/Classes/Settings/ProjectPackagingSettings.h:260-292` (`bGenerateChunks`, `bGenerateNoChunks`, `bChunkHardReferencesOnly`, `bForceOneChunkPerFile`, `MaxChunkSize`) and `:294-304` (HTTP chunk-install settings); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/AutomationTool/AutomationUtils/ProjectParams.cs:1644-1654` (manifest/chunk-install UAT controls). Epic UE 5.8 [Cooking Content and Creating Chunks](https://dev.epicgames.com/documentation/unreal-engine/cooking-content-and-creating-chunks-in-unreal-engine?application_version=5.8) describes chunks as independently distributable collections and documents Asset Manager/Primary Asset Label assignment; [Patching, Content Delivery, and DLC](https://dev.epicgames.com/documentation/unreal-engine/patching-content-delivery-and-dlc-in-unreal-engine?application_version=5.8) lists ChunkDownloader and platform delivery integrations. No platform launcher or runtime mount test was run.

### No-change checks

- The three-stage build/cook/package model, UAT `BuildCookRun` role, target/configuration distinctions, Shipping/Test advice, `-build`/`-cook`/`-stage`/`-pak`/`-iostore`/`-archive`, `-iterate`, `-allmaps`, `-cookall`, `-compressed`, `-unversioned`, `-ddc`, deploy/run flags, and `ProjectParams`/Project Launcher relationship have matching UE 5.8.2 source or versioned Epic documentation. The corrections above target flags and scope, not the core pipeline.
- `UProjectPackagingSettings` is `config=Game, defaultconfig`; the checked UE 5.8.2 header contains `UsePakFile`, `bUseIoStore`, `bUseZenStore`, `bGenerateChunks`, `bGenerateNoChunks`, `bChunkHardReferencesOnly`, `bForceOneChunkPerFile`, `MaxChunkSize`, compression, shader sharing, cook directories, culture, and warning settings used by the skill. `GetUseZenStoreEffective()` correctly requires both Zen and IoStore.
- The pak/IoStore distinction, `.utoc`/`.ucas` roles, compression settings, deprecated crypto-key fields, shader-sharing properties, Asset Manager/Primary Asset Label chunk assignment, Asset Audit/Size Map/Reference Viewer workflow, and `CryptoKeys.json`/Crypto settings guidance did not produce a separate UE 5.8.2 migration item after source comparison. The report does not preserve or reproduce any key material.
- Target type and configuration names match UE 5.8.2 UBT and Epic’s [Build Configurations Reference](https://dev.epicgames.com/documentation/unreal-engine/build-configurations-reference-for-unreal-engine?application_version=5.8). `Test` remains the Shipping-like configuration with selected diagnostics enabled; it is not identical to Shipping.
- The UE 5.8 release notes add packaging-adjacent Zen/Incremental Cooking changes and container options, while the 5.8.1 and 5.8.2 hotfix material checked here did not establish another generic BuildCookRun, pak/IoStore, chunk, or DLC API migration beyond the scoped corrections above.

### Unresolved questions / verification gaps

- No repository project was built, cooked, staged, packaged, launched, or inspected with UAT under UE 5.8.2. No claim here is a successful shipping-build validation.
- The `-warningsaserrors`/`-generatechunks` conclusions are based on the checked UE 5.8.2 `ProjectParams` source; a custom automation script, wrapper, or future installed UAT build could add aliases. Verify the actual `RunUAT` binary/help output used by a project before relying on a wrapper-specific switch.
- No clean-versus-iterative/incremental cook comparison, Zen lifecycle test, DDC restore test, or determinism diff was run. Incremental Cooking remains Beta, and the versioned Zen documentation and 5.8 release-note default wording do not define every project/template/platform configuration.
- No target SDK, console/Apple/Android launcher, HTTP Chunk Installer, ChunkDownloader, GooglePAD, DLC plugin, patch manifest, IoStore On-Demand host, or platform mount implementation was entered. Platform-specific claims remain unresolved beyond the installed cross-platform source and Epic overview pages.
- Zenserver remote streaming has security and trust-boundary implications; no network authorization, threat model, remote device, or failure/recovery test was performed. Do not reuse development Zen streaming as a public CDN design.
- No packaged client/server cook was run to prove server-content stripping, `WITH_SERVER_CODE`, `WITH_EDITORONLY_DATA`, soft-reference reachability, Asset Manager cook rules, shader sharing, encryption, chunk assignment, optional content, or IoStore output for an actual project.
- The 5.8.3 status was not changed by this skill: no 5.8.3 announcement was found in the pinned search context, which does not prove that no later private or unreleased packaging fix exists.

**Source/doc set checked:** all five repository files listed above, each read in full; installed UE 5.8.2 `Build.version`; `Engine/Source/Developer/DeveloperToolSettings/Classes/Settings/ProjectPackagingSettings.h`; `DeveloperToolSettings/Private/ProjectPackagingSettings.cpp`; `Engine/Source/Programs/AutomationTool/AutomationUtils/ProjectParams.cs`; `Engine/Source/Programs/AutomationTool/Scripts/BuildCookRun.Automation.cs`; `Engine/Source/Editor/UnrealEd/Private/CookOnTheFlyServer.cpp`; `Engine/Source/Runtime/Core/Internal/IO/IoStore.h`; `Engine/Source/Runtime/Experimental/IoStore/OnDemandCore/Public/IO/IoStoreOnDemand.h`; the UE 5.8 release-notes cache; the UE 5.8.1 hotfix material; the UE 5.8.2 hotfix cache; and the version-matched Epic Build Operations, Cooking/Chunking, Patching/DLC, Build Configurations, Sharing/Releasing, Zen cooked-output, Zen streaming, and Multi-Process Cooking documentation cited above. No marketplace/vendor/platform SDK project evidence was used.

---

## core/physics-and-chaos

**Working-tree reconciliation:** read the added decorative collision persistence section. UE 5.8.2 `Engine/Source/Runtime/Engine/Private/Components/StaticMeshComponent.cpp:2618–2622`, `UStaticMeshComponent::SetCollisionProfileName`, calls the parent setter then sets `bUseDefaultCollision=false`. That specific native behavior is verified and should be retained. The stated map-reopen and query outcomes are author-reported, not reproduced by this audit; the persistence check remains necessary.

**Status:** findings  
**Repository path:** `skills/core/physics-and-chaos/`  
**Files reviewed:** `SKILL.md`; `references/collision-channels-and-profiles.md`; `references/physics-simulation-and-constraints.md`; `references/traces-and-queries.md`.

### Verified recommendations

#### PHYS-01 — correct the contradictory overlap/block response rule

- **Priority:** P1 — collision debugging correctness; the main skill tells readers that both sides must request `ECR_Overlap`, then later says one overlap response is sufficient. The first rule can make a working trigger appear misconfigured.
- **Locations:** `skills/core/physics-and-chaos/SKILL.md:48-49` and `:209-211`; the consistent reference rule is `references/collision-channels-and-profiles.md:112-117`.
- **Finding:** UE 5.8.2 combines the two component responses with the minimum response value. `ECR_Block` on one side and `ECR_Overlap` on the other therefore produces an overlap, provided neither side ignores the other and both components have overlap generation enabled. `USceneComponent::GetCollisionResponseToComponent` documents and implements this at `SceneComponent.cpp:3082-3092`; `CanComponentsGenerateOverlap` additionally checks `GetGenerateOverlapEvents()` on both components.
- **Exact proposed replacement:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
-**Block** requires *both* sides to set `ECR_Block` for the other's object type. For **overlap**
-events, both sides need `ECR_Overlap` response *and* `bGenerateOverlapEvents = true`.
+**Block** is the result when both sides resolve to `ECR_Block`. For **overlap** events, at
+least one side must resolve to `ECR_Overlap`, neither side may resolve to `ECR_Ignore`, and
+both components must have `bGenerateOverlapEvents = true`. A common trigger setup is to set
+the trigger's response to `ECR_Overlap` and leave the other component's response at `ECR_Block`.
@@
- **Overlap never fires** — both components need `ECR_Overlap` response to each other's
-  object type *and* `bGenerateOverlapEvents = true` on both. One side being `ECR_Block` still
-  generates an overlap if the other is `ECR_Overlap`, but only one fires.
+- **Overlap never fires** — neither component may ignore the other's object type, at least one
+  side must resolve to `ECR_Overlap`, and `bGenerateOverlapEvents = true` must be enabled on
+  both. The engine combines responses with the minimum response; `ECR_Overlap` plus
+  `ECR_Block` therefore resolves to overlap.
```

- **Practical task benefit:** removes the internal contradiction and gives the smallest correct checklist for trigger/overlap failures.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/Components/SceneComponent.cpp:3070-3095` (`USceneComponent::GetCollisionResponseToComponent`, minimum of both responses); `.../Engine/Private/Components/PrimitiveComponent.cpp:223-231` (`CanComponentsGenerateOverlap`, both generate-overlap flags and resolved `ECR_Overlap`); `.../Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h:1768-1769` (`CreateMinContainer` comment and symbol). Epic UE 5.8 [Traces Overview](https://dev.epicgames.com/documentation/unreal-engine/traces-in-unreal-engine---overview?application_version=5.8) distinguishes trace channels and object types and describes multi-channel overlap/block results. No runtime trigger test was run.

#### PHYS-02 — replace the obsolete async-scene/version note with UE 5.8.2 async physics settings

- **Priority:** P1 — API and project-settings accuracy; `UPhysicsSettings::AsyncFixed` is not a UE 5.8.2 property, and `Use Async Scene`/“deterministic substeps” overstates what the current settings guarantee.
- **Locations:** `skills/core/physics-and-chaos/SKILL.md:228-233`; `references/physics-simulation-and-constraints.md:70-86`.
- **Finding:** UE 5.8.2 declares `bSubstepping`, `bSubsteppingAsync`, `bTickPhysicsAsync`, and `AsyncFixedTimeStepSize` in `UPhysicsSettings`; each async/substepping property is explicitly marked experimental in the source. `UActorComponent::AsyncPhysicsTickComponent` is a per-step callback, but the 5.8.2 header says these callbacks execute on the **game thread**, synchronize physics/game-thread data, and can halt the physics thread while running. The current reference calls it a physics-thread callback and “safe to call physics APIs from,” which is unsafe guidance.
- **Exact proposed replacement:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
 ## Version notes
 
 Chaos replaced PhysX as the default physics engine in UE5. The Chaos solver runs
-deterministic substeps controlled by `UPhysicsSettings::AsyncFixed` (Project Settings →
-Physics → Simulation → Use Async Scene). `FBodyInstance` is stable across UE5; solver
-internals differ from PhysX but the `UPrimitiveComponent` API is unchanged.
+substeps and can be configured through `UPhysicsSettings::bSubstepping`,
+`bSubsteppingAsync`, `bTickPhysicsAsync`, `AsyncFixedTimeStepSize`, `MaxSubstepDeltaTime`,
+and `MaxSubsteps`. UE 5.8.2 marks async physics and substepping as experimental; do not
+call the result universally deterministic or use the old `UPhysicsSettings::AsyncFixed`
+name. `FBodyInstance` and the common `UPrimitiveComponent` query/simulation APIs remain
+available, but solver and async-thread behavior still needs project validation.
```

```diff
--- a/skills/core/physics-and-chaos/references/physics-simulation-and-constraints.md
+++ b/skills/core/physics-and-chaos/references/physics-simulation-and-constraints.md
@@
-Configure in Project Settings →
-Physics → Simulation:
+Configure in Project Settings → Physics → Framerate/Simulation:
 
- - **Use Async Scene** — runs physics on a separate thread; reduces hitching but adds one
-  frame of latency to physics results.
- - **Max Physics Delta Time** — clamp the delta given to physics to avoid explosion during
-  hitching (default 0.1 s).
- - **Substepping** — subdivides large deltas into smaller steps for stability. Enable
-  `bSubstepping`, set `MaxSubstepDeltaTime` and `MaxSubsteps`.
+- **Tick Physics Async** (`bTickPhysicsAsync`) — ticks physics on an async thread. UE 5.8.2
+  marks this experimental; measure latency and thread interactions in the project.
+- **Async Fixed Time Step Size** (`AsyncFixedTimeStepSize`) — the step size when async
+  physics is enabled.
+- **Substepping** (`bSubstepping`) and async substepping (`bSubsteppingAsync`) — subdivide
+  simulation time; `MaxSubstepDeltaTime` and `MaxSubsteps` bound the synchronous substeps.
+- **Max Physics Delta Time** — clamps the physics delta during hitching.
@@
-For per-substep game code, override `UActorComponent::AsyncPhysicsTickComponent` (UE5+) —
-it runs on the physics thread each substep and is safe to call physics APIs from.
+For per-step component code, enable async physics ticking and override
+`UActorComponent::AsyncPhysicsTickComponent`. In UE 5.8.2 the callback executes on the game
+thread and forces a full physics/game-thread synchronization; it is not a free physics-thread
+callback. Keep the body of the callback short and thread assumptions explicit, then profile
+the project’s actual async configuration.
```

- **Practical task benefit:** prevents compile errors from a nonexistent property and prevents users from putting game-thread-only or expensive work into a callback described as physics-thread-safe.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsSettings.h:315-345` (`MaxPhysicsDeltaTime`, `bSubstepping`, `bSubsteppingAsync`, `bTickPhysicsAsync`, `AsyncFixedTimeStepSize`, `MaxSubstepDeltaTime`, `MaxSubsteps`), each async/substep comment stating experimental; `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Components/ActorComponent.h:402-407` (game-thread execution and synchronization warning), `:978-985` (`AsyncPhysicsTickComponent` contract), and `:1430-1435` (`SetAsyncPhysicsTickEnabled`); `.../Private/Components/ActorComponent.cpp:1842-1866` (registration). The UE 5.8.2 source contains no `UPhysicsSettings::AsyncFixed` declaration in the checked header. Epic UE 5.8 [Traces Overview](https://dev.epicgames.com/documentation/unreal-engine/traces-in-unreal-engine---overview?application_version=5.8) was available; the versioned bodies page returned 403 during this audit, so the async recommendation is source-grounded. No async physics runtime or determinism test was run.

#### PHYS-03 — mark `UPhysicalAnimationComponent` as experimental before recommending partial ragdolls

- **Priority:** P1 — production-risk classification; the skill presents physical animation as the normal partial-ragdoll path, but the UE 5.8.2 class declaration carries `UCLASS(..., Experimental, ...)`.
- **Locations:** `skills/core/physics-and-chaos/SKILL.md:163-166`; `references/physics-simulation-and-constraints.md:165-174`.
- **Finding:** `UPhysicalAnimationComponent` is available and its profile APIs match the examples, but the installed UE 5.8.2 `PhysicalAnimationComponent.h:66-100` marks the class Experimental. The recommendation can remain, but readers need an explicit stability boundary and a production fallback/validation instruction.
- **Exact proposed replacement:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
-// For blended / partial ragdoll, use UPhysicalAnimationComponent.
+// For blended / partial ragdoll, UPhysicalAnimationComponent is available but marked
+// Experimental in UE 5.8.2; validate the project’s target platforms and recovery path.
```

```diff
--- a/skills/core/physics-and-chaos/references/physics-simulation-and-constraints.md
+++ b/skills/core/physics-and-chaos/references/physics-simulation-and-constraints.md
@@
-For partial ragdolls, `SetAllBodiesBelowSimulatePhysics` simulates bones from the named
-bone down the hierarchy while the rest blend with animation.
+For partial ragdolls, `SetAllBodiesBelowSimulatePhysics` simulates bones from the named
+bone down the hierarchy while the rest blend with animation. `UPhysicalAnimationComponent`
+is marked **Experimental** by the UE 5.8.2 class declaration; test animation handoff,
+networking, save/load, and teardown behavior before using it as a production dependency.
```

- **Practical task benefit:** preserves the useful API path while preventing an experimental component from being mistaken for a stable guarantee.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicalAnimationComponent.h:66-100` (`UPhysicalAnimationComponent`, `SetSkeletalMeshComponent`, `ApplyPhysicalAnimationProfileBelow`); `PrimitiveComponent.h:1660-1663` (`SetAllBodiesBelowSimulatePhysics` in the checked source). No ragdoll, animation blend, platform, or network test was run.

#### PHYS-04 — require physical-material return data and null-check the weak pointer

- **Priority:** P1 — runtime safety and correctness; the main skill reads `Hit.PhysMaterial.Get()->SurfaceType` without enabling the query flag or checking that the weak pointer is valid.
- **Locations:** `skills/core/physics-and-chaos/SKILL.md:187-195`; the safer but incomplete reference example is `references/physics-simulation-and-constraints.md:176-195`.
- **Finding:** UE 5.8.2 `FHitResult::PhysMaterial` is a `TWeakObjectPtr<UPhysicalMaterial>`, and the header notes that `bReturnPhysicalMaterial` must be set on the component or query params for it to be populated. A trace may therefore have no physical material, and dereferencing `Get()` unconditionally can crash.
- **Exact proposed replacement:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
 Read `SurfaceType` from a hit to drive effects (footstep sounds, particle emitters):
-`Hit.PhysMaterial.Get()->SurfaceType`.
+set `FCollisionQueryParams::bReturnPhysicalMaterial = true` (or enable the component
+setting), then check the weak pointer before reading it:
+
+```cpp
+if (Hit.PhysMaterial.IsValid())
+{
+    const EPhysicalSurface Surface = Hit.PhysMaterial.Get()->SurfaceType;
+    // Select footstep/SFX behavior from Surface.
+}
+```
```

```diff
--- a/skills/core/physics-and-chaos/references/physics-simulation-and-constraints.md
+++ b/skills/core/physics-and-chaos/references/physics-simulation-and-constraints.md
@@
 if (Hit.PhysMaterial.IsValid())
 {
     EPhysicalSurface Surface = Hit.PhysMaterial.Get()->SurfaceType;
@@
 }
+Set `FCollisionQueryParams::bReturnPhysicalMaterial = true` (or the component’s
+`bReturnPhysicalMaterial` setting) on the query that produced `Hit`; otherwise a valid hit
+may carry no material. Keep the `IsValid()` check because the weak pointer can still be null.
```

- **Practical task benefit:** avoids a null dereference and explains why a valid trace can lack a surface type.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/HitResult.h:118-123` (`PhysMaterial` and `bReturnPhysicalMaterial` note); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/CollisionQueryParams.h:42-60` (`bReturnPhysicalMaterial`); `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/PhysicsCore/Public/PhysicalMaterials/PhysicalMaterial.h:177-181` (`SurfaceType`). Epic UE 5.8 [Physical Materials](https://dev.epicgames.com/documentation/unreal-engine/physical-materials-in-unreal-engine?application_version=5.8) confirms physical materials as the source of physical surface properties. No trace/material runtime test was run.

#### PHYS-05 — remove the unverified “expanded from 18 to 50 in 5.8” attribution

- **Priority:** P2 — documentation provenance; UE 5.8.2 source has 50 custom `ECC_GameTraceChannel` entries, but the checked UE 5.8 release notes and installed declarations do not establish that the expansion occurred specifically in 5.8.
- **Locations:** `skills/core/physics-and-chaos/SKILL.md:34-37`; `references/collision-channels-and-profiles.md:31-37`.
- **Finding:** the current capacity claim is verifiable for the pinned engine, while its historical “expanded from 18 to 50 in 5.8” attribution is not source-grounded by this audit. Keep the available range and remove the unsupported historical comparison.
- **Exact proposed replacement:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
-   Custom channels map to `ECC_GameTraceChannel1`–`ECC_GameTraceChannel50` at runtime
-   (expanded from 18 to 50 in 5.8).
+   In the pinned UE 5.8.2 source, custom channels map to `ECC_GameTraceChannel1`–
+   `ECC_GameTraceChannel50` at runtime. Use the project’s configured name/alias rather than
+   relying on an historical capacity claim.
```

```diff
--- a/skills/core/physics-and-chaos/references/collision-channels-and-profiles.md
+++ b/skills/core/physics-and-chaos/references/collision-channels-and-profiles.md
@@
-**Custom channels** occupy `ECC_GameTraceChannel1`–`ECC_GameTraceChannel50` (expanded from
-18 to 50 in 5.8). In Project
+**Custom channels** occupy `ECC_GameTraceChannel1`–`ECC_GameTraceChannel50` in the pinned
+UE 5.8.2 source. In Project
```

- **Practical task benefit:** preserves the actionable UE 5.8.2 range without teaching an unsupported release-history fact.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h:1094-1108` (object/trace metadata) and `:1119-1168` (`ECC_GameTraceChannel1` through `ECC_GameTraceChannel50`). Searches of the pinned UE 5.8 release-notes cache did not locate a matching 18-to-50 expansion entry; no older installed engine was used for a historical diff.

#### PHYS-06 — add the scoped UE 5.8 Geometry Collection runtime additions

- **Priority:** P2 — practical UE 5.8 feature coverage; the skill describes Chaos broadly but omits the new per-transform damping and current-transform queries that are useful when the project actually uses Geometry Collections.
- **Insertion point:** after `skills/core/physics-and-chaos/SKILL.md:185` (after the constraint deep-dive link and before `## Physical materials`).
- **Finding:** Epic’s UE 5.8 Chaos Destruction release section adds per-transform linear/angular damping and `GetCurrentTransforms`/`GetCurrentTransformsFromIndices`. UE 5.8.2 exposes these on `UGeometryCollectionComponent`; the APIs return component-space center-of-mass transforms, so the guidance must not present them as generic `UPrimitiveComponent` or world-space transforms.
- **Exact proposed addition:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
 See [references/physics-simulation-and-constraints.md](references/physics-simulation-and-constraints.md)
 for `FBodyInstance` details, damping, sub-stepping, and constraint drives.
+
+## UE 5.8 Geometry Collection additions
+
+If the project uses `UGeometryCollectionComponent` for Chaos Destruction, UE 5.8.2 exposes
+per-transform damping and current-transform queries:
+
+```cpp
+GeometryCollection->SetLinearDampingPerTransform(TransformIndices, LinearDamping);
+GeometryCollection->SetAngularDampingPerTransform(TransformIndices, AngularDamping);
+const TArray<FTransform> Current = GeometryCollection->GetCurrentTransforms();
+```
+
+`GetCurrentTransforms` and `GetCurrentTransformsFromIndices` return transforms in component
+space representing each piece's center of mass. This is a Geometry Collection API, not a
+replacement for `UPrimitiveComponent` rigid-body queries. Profile large arrays and validate
+the destruction/replication workflow before adding per-piece polling.
```

- **Practical task benefit:** gives destruction users a directly usable UE 5.8 capability without broadening ordinary rigid-body guidance or mislabeling transform space.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Experimental/GeometryCollectionEngine/Public/GeometryCollection/GeometryCollectionComponent.h:576-577` (`UGeometryCollectionComponent`), `:676-680` (`SetLinearDampingPerTransform`, `SetAngularDampingPerTransform`), and `:1347-1359` (`GetCurrentTransforms`, `GetCurrentTransformsFromIndices`); `.../Private/GeometryCollection/GeometryCollectionComponent.cpp:7124-7160` (component-space/current-transform implementation). Epic UE 5.8 release notes `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:2130-2165` document the Chaos Destruction additions and fixes. No Geometry Collection asset, cache, destruction, or performance test was run.

#### PHYS-07 — record the UE 5.8.2 Networked Physics hotfix boundary

- **Priority:** P2 — targeted hotfix awareness; projects using networked physics can otherwise attribute a fixed tick-offset issue to their collision or replication code.
- **Insertion point:** after `skills/core/physics-and-chaos/SKILL.md:233` in `## Version notes`.
- **Finding:** the pinned UE 5.8.2 hotfix notes report a Networked Physics fix so `TickOffset` is marshaled to the physics thread even when no replicated server state exists. The installed source exposes the corresponding internal and external tick-offset APIs. This is a hotfix note for networked physics users, not a claim that ordinary local Chaos simulation or arbitrary physics replication is deterministic.
- **Exact proposed addition:**

```diff
--- a/skills/core/physics-and-chaos/SKILL.md
+++ b/skills/core/physics-and-chaos/SKILL.md
@@
 internals differ from PhysX but the `UPrimitiveComponent` query/simulation API is unchanged.
+**UE 5.8.2 Networked Physics hotfix:** if using Networked Physics prediction/replication,
+use the 5.8.2 hotfix level; its release notes report a fix for marshaling the network
+physics tick offset to the physics thread when no server replicated state exists. This does
+not establish deterministic behavior for general Chaos simulation.
```

- **Practical task benefit:** gives networked-physics users a concrete engine-version check while keeping the fix scoped to the reported hotfix path.
- **Verified evidence:** UE 5.8.2 hotfix cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/forums.unrealengine.com-d1d8d96bf4.md:297-311` (Networked Physics `TickOffset` fix); installed `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/PhysicsReplicationInterface.h:55-69` (`IPhysicsReplicationAsync::GetNetworkPhysicsTickOffset_Internal`), `.../Public/PhysicsReplication.h:232-240`, and `.../Public/Physics/NetworkPhysicsComponent.h:77-92` (internal/external tick-offset APIs). No client/server networked-physics test was run.

### No-change checks

- The object/trace channel distinction, `ECR_Ignore`/`ECR_Overlap`/`ECR_Block` vocabulary, collision-enabled modes, profile application ordering, `UPrimitiveComponent` query APIs, `FHitResult` core fields, single/multi trace behavior, ByChannel/ByObjectType distinction, query-param flags, UV-from-hit prerequisites, simple-versus-complex collision distinction, force/impulse API names, mass override, physical-material fields, constraint-drive names, and full-ragdoll setup match the checked UE 5.8.2 declarations or versioned Epic documentation, subject to the corrections above.
- `ECC_GameTraceChannel1` through `ECC_GameTraceChannel50` and the listed built-in object/trace metadata exist in UE 5.8.2. `FCollisionResponseContainer` has 64 serialized response slots in the source; the report does not infer that all slots are user-configurable channels.
- The existing `FBodyInstance` damping, CCD, notify-hit, physical-material override, constraint, and `UGameplayStatics::FindCollisionUV` examples were not independently runtime-tested. No new general-purpose abstraction is justified by the 5.8.2 source check.
- The UE 5.8.1 hotfix material checked here did not yield a separate generic collision/query/constraint migration requirement. The UE 5.8.2 hotfix’s core-physics self-referencing-constraint and destruction fixes are engine fixes rather than API changes to the examples; the Networked Physics boundary is recorded above.

### Unresolved questions / verification gaps

- No project was compiled, loaded, simulated, or run under UE 5.8.2. No overlap/hit, trace/sweep, async-query, physical-material, rigid-body, constraint, ragdoll, Geometry Collection, or networked-physics behavior was runtime-validated.
- The installed source proves declarations and selected implementations, not editor profile configuration, generated Blueprint signatures, cooked physics assets, platform solver behavior, determinism, replication, or performance.
- The versioned Epic Collision Overview and Physics Bodies URLs returned 403 during extraction; Traces, Constraints, and Physical Materials pages were available. Collision/body workflow claims therefore remain partly source-grounded and partly documentation-limited.
- Async physics and substepping are explicitly marked experimental in UE 5.8.2 source. The report does not establish latency, ordering, thread-safety of project callbacks beyond the documented `AsyncPhysicsTickComponent` contract, or deterministic replay.
- `UPhysicalAnimationComponent` is marked Experimental, but no project-specific production fallback was authorized or inspected. Networked, saved, or teardown ragdoll behavior remains unresolved.
- The custom-channel historical expansion was not verified against an older installed engine or a dated Epic migration note; only the pinned 5.8.2 capacity is confirmed.
- Geometry Collection APIs were inspected at declaration/implementation level only. No asset, per-transform index validity, transform-space consumer, damage propagation, replication, or per-piece polling performance was tested.
- No marketplace/vendor project, platform SDK, Chaos Cloth/Flesh integration, or custom physics plugin was inspected.
- The pinned search context found no 5.8.3 announcement; this does not prove that no later private, unreleased, or distribution-specific physics fix exists.

**Source/doc set checked:** all four repository files listed above, each read in full; installed UE 5.8.2 `Build.version`; `Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h`; `Engine/Source/Runtime/Engine/Classes/Engine/HitResult.h`; `Engine/Source/Runtime/Engine/Classes/Components/PrimitiveComponent.h`; `Engine/Source/Runtime/Engine/Classes/Components/ActorComponent.h`; `Engine/Source/Runtime/Engine/Classes/Components/SceneComponent.h`; `Engine/Source/Runtime/Engine/Classes/PhysicsEngine/BodyInstance.h`; `Engine/Source/Runtime/Engine/Classes/PhysicsEngine/ConstraintInstance.h`; `Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsSettings.h`; `Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicalAnimationComponent.h`; `Engine/Source/Runtime/Engine/Private/Components/PrimitiveComponent.cpp`; `Engine/Source/Runtime/Engine/Private/Components/SceneComponent.cpp`; `Engine/Source/Runtime/Engine/Public/CollisionQueryParams.h`; `Engine/Source/Runtime/Engine/Public/Physics/PhysicsFiltering.h`; `Engine/Source/Runtime/PhysicsCore/Public/PhysicalMaterials/PhysicalMaterial.h`; `Engine/Source/Runtime/Experimental/GeometryCollectionEngine/Public/GeometryCollection/GeometryCollectionComponent.h`; `.../Private/GeometryCollection/GeometryCollectionComponent.cpp`; `Engine/Source/Runtime/Engine/Public/PhysicsReplicationInterface.h`; `.../Public/PhysicsReplication.h`; `.../Public/Physics/NetworkPhysicsComponent.h`; the UE 5.8 release-notes cache; the UE 5.8.1 hotfix material; the UE 5.8.2 hotfix cache; and the version-matched Epic Traces, Physics Constraints, Physical Materials, and the partially blocked Collision Overview/Physics Bodies documentation URLs cited above. No marketplace/vendor/platform SDK project evidence was used.

---

## core/plugins-and-modules

**Status:** findings
**Repository path:** `skills/core/plugins-and-modules/`
**Files reviewed:** `SKILL.md`; `references/uplugin-descriptor.md`; `references/plugin-structure-and-modules.md`; `references/plugin-dependencies-and-packaging.md`.

### Verified recommendations

#### PLUG-01 — distinguish BuildPlugin distribution filtering from cooked plugin-config staging

- **Priority:** P1 — distribution correctness; the current text sends users to duplicate plugin settings in the project, while the correct remedy depends on whether the user is building a distributable plugin or staging an enabled plugin in a cooked project.
- **Locations:** `skills/core/plugins-and-modules/SKILL.md:229-230`; `skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md:199-205`.
- **Finding:** UE 5.8.2 `BuildPlugin.PackagePlugin` applies `FilterPluginFiles`. Its default filter includes the descriptor, build products, `Binaries/ThirdParty`, `Resources`, `Content`, selected `Intermediate/Build`, `Shaders`, and `Source`, but not arbitrary `Config/*.ini`; it reads `Config/FilterPlugin.ini` for custom inclusion rules. This supports the distribution-package caution, but “copy them to the project's Config folder” is not the only or best fix. Separately, cooked target staging calls `StageTargetPlatform.GetPluginConfigFiles(PluginInfo)` and adds the returned files to the UFS staging list, so an enabled plugin's config is staged for a cooked project target without copying it into the project config directory.
- **Exact proposed replacement:**

```diff
--- a/skills/core/plugins-and-modules/SKILL.md
+++ b/skills/core/plugins-and-modules/SKILL.md
@@
-**Config files not packaged** — plugin config files are not automatically packaged; copy
-them to the project's `Config/` folder before distribution.
+**Plugin distribution vs cooked staging** — `BuildPlugin`'s default filter does not include
+arbitrary `Config/*.ini`. If a distributable plugin needs an ini, add an explicit rule in
+`Config/FilterPlugin.ini` (or make the setting project-owned). For an enabled plugin in a
+cooked project target, AutomationTool stages plugin config files through its plugin staging
+rules; do not copy them to the project `Config/` merely to make cooked output include them.
```

```diff
--- a/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
+++ b/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
@@
-|- `Config/` is **not** automatically packaged; copy ini files to the project's `Config/`
-  manually if needed.
+|- `Config/` is not in the default `BuildPlugin` include list. Add required distribution
+  files with rules in `Config/FilterPlugin.ini`, or document that the setting belongs to the
+  consuming project. This is distinct from cooked project staging: AutomationTool's cooked
+  target staging enumerates plugin config files and stages them as UFS for enabled plugins.
```

- **Practical task benefit:** prevents duplicated or divergent config and gives plugin authors a deterministic `FilterPlugin.ini` path for distribution while preserving the automatic cooked-target behavior.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Programs/AutomationTool/Scripts/BuildPluginCommand.Automation.cs:419-488` (`PackagePlugin`, `FilterPluginFiles`, `FilterPlugin.ini` rules); `.../AutomationTool/CookedEditor/CookedEditor.Automation.cs:672-690` (`GetPluginConfigFiles`, `StageFile(..., UFS)`). These are source-level checks; no plugin was built, packaged, or cooked.

#### PLUG-02 — use the serialized `Version` key and document GameFeature activation

- **Priority:** P1 — descriptor correctness; `RequestedVersion` is the C++ member name, not the JSON key parsed by UE 5.8.2, so the current example does not pin the dependency version. The omitted `Activate` key is relevant when a GameFeaturePlugin dependency must activate with its parent.
- **Locations:** `skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md:94-101` and `:121-130`; the omission also leaves `SKILL.md:82-84` without a version/activation example.
- **Finding:** `FPluginReferenceDescriptor::Read` reads `Optional`, then `Activate`, and reads the integer JSON field `Version` into `RequestedVersion`; it rejects a version field when `Enabled` is false. `FPluginReferenceDescriptor::bActivate` is explicitly documented as “also activate when the parent plugin is activated by the GameFeaturePlugin system.”
- **Exact proposed replacement:**

```diff
--- a/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
+++ b/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
@@
 ```json
-{ "Name": "SomeSDK", "Enabled": true, "RequestedVersion": 5 }
+{ "Name": "SomeSDK", "Enabled": true, "Version": 5 }
 ```
 
-`RequestedVersion`:74 (`TOptional<int32>`) pins to a specific integer `Version` from the
-dependency's `.uplugin`. Use this when your plugin relies on a specific API revision.
+`Version` is the serialized key for `RequestedVersion`:74 (`TOptional<int32>`); it pins to a
+specific integer `Version` from the dependency's `.uplugin`. It is valid only when
+`Enabled` is `true`. Use this when the plugin relies on a specific API revision. For a
+GameFeaturePlugin dependency that should activate with its parent, also use:
+
+```json
+{ "Name": "SomeGameFeature", "Enabled": true, "Activate": true }
+```
@@
 | `Optional` | `bOptional`:35 | If `true`, the plugin silently ignores the dependency being absent. |
 | `PlatformAllowList` | `PlatformAllowList`:50 | Enable on listed platforms only. |
 | `PlatformDenyList` | `PlatformDenyList`:53 | Disable on listed platforms. |
 | `TargetAllowList` | `TargetAllowList`:62 | Enable for listed `EBuildTargetType` values only. |
 | `TargetDenyList` | `TargetDenyList`:65 | Disable for listed target types. |
-| `RequestedVersion` | `RequestedVersion`:74 | Pin a specific plugin `Version` integer. |
+| `Version` | `RequestedVersion`:74 | Pin a specific plugin `Version` integer; serialized as `Version`, not `RequestedVersion`. |
+| `Activate` | `bActivate`:38 | For GameFeaturePlugin activation, also activate this dependency when the parent is activated. |
```

- **Practical task benefit:** stops silently ignored version pins and makes parent/child GameFeature activation intentional instead of relying on an incidental enabled state.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Projects/Private/PluginReferenceDescriptor.cpp:143-178` (`Read`, `Activate`, serialized `Version`, disabled-version validation) and `.../Public/PluginReferenceDescriptor.h:34-41,67-74` (`bOptional`, `bActivate`, `TargetsToExplicitlyLoad`, `RequestedVersion`). Epic UE 5.8 release notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:5670-5682` also records UE 5.8 GameFeature plugin config/activation-related changes; no GameFeature asset or activation flow was run.

#### PLUG-03 — describe `EngineVersion` as a compatibility gate, not an ABI guarantee

- **Priority:** P1 — upgrade and packaging reliability; the current sentence understates a real engine-version check while overstating an unspecified UBT module-identifier check.
- **Location:** `skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md:211-214`.
- **Finding:** UE 5.8.2 `FPluginManager::IsPluginCompatible` parses `FPluginDescriptor::EngineVersion` and compares it with `FEngineVersion::CompatibleWith()`, returning incompatible on a version comparison mismatch; the manager can then prompt to load the plugin anyway. `BuildPlugin.PackagePlugin` writes the current `Major.Minor.0` engine version unless `-Unversioned` is requested. This metadata gate is not an ABI proof: modules still need to be rebuilt and exercised against the target engine, and the separate `FModuleDescriptor::CheckModuleCompatibility`/`FModuleManager::IsModuleUpToDate` path checks module availability/path state rather than proving source or binary behavior.
- **Exact proposed replacement:**

```diff
--- a/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
+++ b/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
@@
 **Engine version compatibility:** plugin binaries compiled against one UE version are not
 ABI-compatible with other versions. Precompiled plugins must be recompiled for each engine
-version. The `EngineVersion` field in the descriptor is informational; UBT performs the actual
-compatibility check by comparing module identifiers.
+version. `FPluginManager::IsPluginCompatible` parses the descriptor's `EngineVersion` and
+compares it with `FEngineVersion::CompatibleWith()`; a mismatch can make the plugin
+incompatible and trigger a load prompt. This is a compatibility gate, not an ABI guarantee:
+rebuild and test every binary for the target engine. `BuildPlugin` embeds the current
+`Major.Minor.0` value unless `-Unversioned` is used.
```

- **Practical task benefit:** makes engine-version metadata useful for diagnosing load prompts without encouraging authors to treat it as permission to reuse an untested binary.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Projects/Private/PluginManager.cpp:2688-2714` (`IsPluginCompatible`, `PromptToLoadIncompatiblePlugin`); `.../Programs/AutomationTool/Scripts/BuildPluginCommand.Automation.cs:419-445` (`PackagePlugin` writes `EngineVersion`); `.../Runtime/Projects/Private/ModuleDescriptor.cpp:843-860` (`CheckModuleCompatibility`); `.../Runtime/Core/Private/Modules/ModuleManager.cpp:372-386` (`IsModuleUpToDate`). No cross-version binary or plugin load test was run.

#### PLUG-04 — give `UnmountExplicitlyLoadedPlugin` its required reason parameter and limitation

- **Priority:** P1 — compile/runtime correctness; the reference tells users to reverse a mount with an incomplete call and implies that compiled plugin code can be unloaded.
- **Location:** `skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md:110-126`, especially `:125-126`.
- **Finding:** UE 5.8.2 declares `MountExplicitlyLoadedPlugin(const FString&, ELoadingPhase::Type)` and `UnmountExplicitlyLoadedPlugin(const FString&, FText*)` (plus an overload with `bAllowUnloadCode`). The header documents that unmounting does not work on plugins with compiled modules. It also notes that localization data for an explicitly loaded plugin requires a separate `MountExplicitlyLoadedPluginLocalizationData` call when needed.
- **Exact proposed replacement:**

```diff
--- a/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
+++ b/skills/core/plugins-and-modules/references/plugin-dependencies-and-packaging.md
@@
 `MountExplicitlyLoadedPlugin` (`IPluginManager.h`:556) mounts content and loads modules up
-to the specified loading phase. Call `UnmountExplicitlyLoadedPlugin` to reverse this.
+to the specified loading phase. If the plugin has no compiled modules and its content may be
+unmounted, pass the required reason pointer:
+
+```cpp
+FText UnmountReason;
+const bool bUnmounted = IPluginManager::Get().UnmountExplicitlyLoadedPlugin(
+    TEXT("MyContentPlugin"), &UnmountReason);
+```
+
+The UE 5.8.2 contract says unmounting does not work on plugins with compiled modules; do not
+use this as a general code hot-unload mechanism. Localization for an explicitly loaded plugin
+is separately ref-counted and requires `MountExplicitlyLoadedPluginLocalizationData` when it
+is needed.
```

- **Practical task benefit:** avoids a copied-call compile error and prevents runtime systems from assuming that compiled plugin code can be safely unloaded during content teardown.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Projects/Public/Interfaces/IPluginManager.h:545-589` (`MountExplicitlyLoadedPlugin`, localization pair, `UnmountExplicitlyLoadedPlugin` overloads). No explicit-load plugin was mounted or unmounted in an editor/runtime session.

### No-change checks

- The plugin/project distinction, standard `Plugins/<Name>/` layout, `.uplugin` `FileVersion: 3`, top-level `Version`/`VersionName`, `CanContainContent`, `Modules`, `Plugins`, editor/runtime split, `_API` export guidance, `IModuleInterface` lifecycle, and the listed `IPluginManager` query methods match the checked UE 5.8.2 declarations.
- `DefaultPluginName.ini` is still the preferred plugin config layer in UE 5.8.2. `ConfigHierarchy.h:57-64` marks `BasePluginName.ini` and bare `PluginName.ini` layers deprecated; the existing `DefaultMyFeature.ini` examples do not need replacement. The UE 5.8 release note about allowing legacy names alongside defaults is therefore a compatibility/deprecation note, not a reason to change the preferred example.
- The nested-plugin warning matches the checked UBT scanner: `FileMetadataPrefetch.cs:171-187` scans plugin subdirectories, but when a directory contains a `.uplugin` it scans that plugin's `Source` and does not recurse into that plugin's child directories. No change is proposed.
- `EHostType::Developer` being deprecated, `UncookedOnly` being uncooked-only, the loading-phase enum, platform/target filters, optional dependency runtime guard, explicit-load distinction, and the need for both descriptor-level and `Build.cs` module dependencies match the UE 5.8.2 source reviewed.
- No general plugin/module migration was identified in the pinned UE 5.8.1 or UE 5.8.2 hotfix material that would justify changing the remaining examples. The hotfix notes contain plugin-specific fixes and known issues; those do not establish a universal plugin API change.

### Unresolved questions / verification gaps

- No repository plugin was built with UE 5.8.2 `BuildPlugin`, loaded in the editor, mounted at runtime, cooked, packaged, or tested on more than one target platform. The findings are source-grounded, not build or runtime validation.
- The `FilterPlugin.ini` recommendation was verified from `BuildPluginCommand.Automation.cs`, but no actual filter file was authored or run; wildcard precedence and a project’s custom filter rules remain project-specific.
- No GameFeaturePlugin was activated or deactivated, so `Activate`, explicit-load ordering, localization ref-counting, and parent/child feature lifecycle remain untested in an actual Game Features workflow.
- `EngineVersion` compatibility and module path checks were read from source, but no incompatible binary, OS loader failure, hot reload, or cross-engine ABI case was produced. Platform SDK, marketplace/vendor, and third-party plugin packaging behavior remains uninspected.
- No editor-only/server/client/cooked target matrix was built to validate every `EHostType`, platform list, target list, loading phase, or optional-dependency combination.
- The pinned search context found no 5.8.3 announcement; that does not prove that no later private, unreleased, or distribution-specific plugin/module fix exists.

**Source/doc set checked:** all four repository files listed above, each read in full; installed UE 5.8.2 `Build.version`; `Engine/Source/Runtime/Projects/Public/PluginDescriptor.h`; `Engine/Source/Runtime/Projects/Public/ModuleDescriptor.h`; `Engine/Source/Runtime/Projects/Public/PluginReferenceDescriptor.h`; `Engine/Source/Runtime/Projects/Public/Interfaces/IPluginManager.h`; `Engine/Source/Runtime/Projects/Private/PluginReferenceDescriptor.cpp`; `Engine/Source/Runtime/Projects/Private/PluginManager.cpp`; `Engine/Source/Runtime/Projects/Private/ModuleDescriptor.cpp`; `Engine/Source/Runtime/Core/Public/Modules/ModuleInterface.h`; `Engine/Source/Runtime/Core/Private/Modules/ModuleManager.cpp`; `Engine/Source/Runtime/Core/Public/Misc/ConfigHierarchy.h`; `Engine/Source/Programs/UnrealBuildTool/System/FileMetadataPrefetch.cs`; `Engine/Source/Programs/AutomationTool/Scripts/BuildPluginCommand.Automation.cs`; `Engine/Source/Programs/AutomationTool/CookedEditor/CookedEditor.Automation.cs`; the UE 5.8 release-notes cache; and the UE 5.8.1 hotfix material; and the UE 5.8.2 hotfix cache. No marketplace/vendor/platform SDK project evidence was used.

---

## core/project-structure

**Status:** findings
**Repository path:** `skills/core/project-structure/`
**Files reviewed:** `SKILL.md`; `references/uproject-and-modules.md`; `references/folder-layout-and-vcs.md`; `references/config-system.md`.

### Verified recommendations

#### PROJ-01 — correct serialized `.uproject` keys and document both external-directory lists

- **Priority:** P1 — project-open/build correctness; the current table presents C++ member names as JSON keys, and omits a supported editor-side root-directory list.
- **Locations:** `skills/core/project-structure/references/uproject-and-modules.md:15-29`; `skills/core/project-structure/SKILL.md:64-81` for the schema introduction and example.
- **Finding:** UE 5.8.2 `FProjectDescriptor::Read` reads `Enterprise` into `bIsEnterpriseProject` and `DisableEnginePluginsByDefault` into `bDisableEnginePluginsByDefault`, not JSON keys named `bIsEnterpriseProject` or `bDisableEnginePluginsByDefault`. It also reads `AdditionalPluginDirectories` and, in editor builds, `AdditionalRootDirectories`; the latter is absent from the repository table. `FileVersion` is required by the reader, with `ProjectFileVersion` accepted only as a compatibility fallback.
- **Exact proposed replacement:**

```diff
--- a/skills/core/project-structure/references/uproject-and-modules.md
+++ b/skills/core/project-structure/references/uproject-and-modules.md
@@
-A `.uproject` file is JSON that the engine deserialises into `FProjectDescriptor`
-(`Runtime/Projects/Public/ProjectDescriptor.h`). Every top-level JSON key maps to a
-field on the struct:
+A `.uproject` file is JSON that the engine deserialises into `FProjectDescriptor`
+(`Runtime/Projects/Public/ProjectDescriptor.h`). Use the serialized JSON names below;
+they are not always identical to the C++ member names:
@@
-| `bIsEnterpriseProject` | `bool bIsEnterpriseProject` | Enables enterprise features. |
-| `bDisableEnginePluginsByDefault` | `bool bDisableEnginePluginsByDefault` | Opt all engine plugins out by default. |
+| `Enterprise` | `bool bIsEnterpriseProject` | Enables enterprise features. |
+| `DisableEnginePluginsByDefault` | `bool bDisableEnginePluginsByDefault` | Opt all engine plugins out by default. |
 | `AdditionalPluginDirectories` | private `TArray<FString>` | Extra directories to scan for plugins. |
+| `AdditionalRootDirectories` | private `TArray<FString>` | Extra directories to scan for modules; read/written by editor builds. |
```

- **Practical task benefit:** prevents silently ineffective hand-edited project settings and exposes the supported external module-scan path when a project uses source outside its normal `Source/` tree.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Projects/Private/ProjectDescriptor.cpp:103-129,147-189` (`FProjectDescriptor::Read`) and `:269-318` (`Write`); `.../Public/ProjectDescriptor.h:90-106,138-199` (`TargetPlatforms`, flags, and additional directory fields). No `.uproject` was parsed or rewritten.

#### PROJ-02 — replace obsolete module target-list JSON names and expose UE 5.8.2 filters

- **Priority:** P1 — target-selection correctness; the current `IncludelistTargets` wording is not the key emitted or read by UE 5.8.2.
- **Location:** `skills/core/project-structure/references/uproject-and-modules.md:55-63`; related summary at `skills/core/project-structure/SKILL.md:100-112`.
- **Finding:** `FModuleDescriptor::Read` reads `TargetAllowList`/`TargetDenyList` with deprecated fallbacks `WhitelistTargets`/`BlacklistTargets`; it does not use `IncludelistTargets`. UE 5.8.2 also supports target-configuration, program, game-target, platform-architecture, and explicit-platform fields that are missing from the reference table. The writer emits the current names.
- **Exact proposed replacement:**

```diff
--- a/skills/core/project-structure/references/uproject-and-modules.md
+++ b/skills/core/project-structure/references/uproject-and-modules.md
@@
-| `TargetAllowList` / `TargetDenyList` | `TArray<EBuildTargetType>` | `"IncludelistTargets"` etc. | Game/Editor/Server/Client/Program. |
+| `TargetAllowList` / `TargetDenyList` | `TArray<EBuildTargetType>` | `"TargetAllowList"` / `"TargetDenyList"` | Game/Editor/Server/Client/Program; `WhitelistTargets`/`BlacklistTargets` are deprecated fallbacks. |
+| `TargetConfigurationAllowList` / `TargetConfigurationDenyList` | `TArray<EBuildConfiguration>` | matching JSON names | Restrict Development/Debug/Test/Shipping-style configurations. |
+| `ProgramAllowList` / `ProgramDenyList` | `TArray<FString>` | matching JSON names | Restrict named program targets. |
+| `GameTargetAllowList` / `GameTargetDenyList` | `TArray<FString>` | matching JSON names | Restrict named game targets. |
+| `PlatformArchitectureAllowList` / `PlatformArchitectureDenyList` | `TMap<FString,TArray<FString>>` | matching JSON names | Restrict platform/architecture pairs such as `Win64:x64`. |
+| `HasExplicitPlatforms` | `bool` | `"HasExplicitPlatforms"` | Treat an empty platform allow-list as no platforms when platform extensions add the explicit set. |
```

- **Practical task benefit:** makes per-target and per-architecture module gating copy-pasteable and avoids a descriptor that appears configured but is ignored because it uses a non-existent key.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Projects/Private/ModuleDescriptor.cpp:196-237` (`Read` for current/deprecated target, configuration, program, game-target, and architecture keys) and `:283-444` (`UpdateJson` emits current keys); `.../Public/ModuleDescriptor.h:165-205` (matching fields). No target matrix was built.

#### PROJ-03 — use the gameplay module implementation and remove the invalid plugin-reference `Type`

- **Priority:** P1 — startup/link and descriptor correctness; the primary module example uses the non-game default implementation, and the plugin-reference example adds a field that does not select a project plugin.
- **Locations:** `skills/core/project-structure/SKILL.md:123-137`; `skills/core/project-structure/references/uproject-and-modules.md:92-112`; invalid plugin example at `references/uproject-and-modules.md:135-149`.
- **Finding:** UE 5.8.2 defines `FDefaultGameModuleImpl` as the no-op module whose `IsGameModule()` returns true, while `FDefaultModuleImpl` is the general non-game module. The primary-game macro is intended for a gameplay module. `FPluginReferenceDescriptor` has no `Type` field: its reader consumes `Name`, `Enabled`, `Optional`, `Activate`, platform/target filters, `TargetsToExplicitlyLoad`, `SupportedTargetPlatforms`, and `Version`; plugin location/descriptor determines engine/project classification.
- **Exact proposed replacement:**

```diff
--- a/skills/core/project-structure/SKILL.md
+++ b/skills/core/project-structure/SKILL.md
@@
-IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultModuleImpl, MyGame, "MyGame");
+IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, MyGame, "MyGame");
@@
-- Use `FDefaultModuleImpl` unless you need `StartupModule`/`ShutdownModule` hooks.
+- Use `FDefaultGameModuleImpl` for an empty primary gameplay module; use a custom
+  `IModuleInterface` subclass when you need `StartupModule`/`ShutdownModule` hooks.
```

```diff
--- a/skills/core/project-structure/references/uproject-and-modules.md
+++ b/skills/core/project-structure/references/uproject-and-modules.md
@@
-IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultModuleImpl, MyGame, "MyGame");
+IMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, MyGame, "MyGame");
@@
-{ "Name": "MyProjectPlugin", "Enabled": true, "Type": "Project" }
+{ "Name": "MyProjectPlugin", "Enabled": true }
@@
-Under `"Plugins"`, each entry is an `FPluginReferenceDescriptor`
-(`Runtime/Projects/Public/PluginReferenceDescriptor.h`). The most-used fields:
+Under `"Plugins"`, each entry is an `FPluginReferenceDescriptor`
+(`Runtime/Projects/Public/PluginReferenceDescriptor.h`). The plugin's engine/project
+classification comes from discovery location; there is no `Type` selector in this
+reference object. The most-used fields are:
```

- **Practical task benefit:** preserves the primary module's gameplay identity and prevents authors from believing a `.uproject` plugin reference can relocate or classify a plugin with an unsupported `Type` key.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Modules/ModuleManager.h:884-904,974-985,1094-1136` (`FDefaultGameModuleImpl`, `IMPLEMENT_GAME_MODULE`, and `IMPLEMENT_PRIMARY_GAME_MODULE`); `.../Runtime/Projects/Private/PluginReferenceDescriptor.cpp:122-178` (recognized project plugin-reference fields) and `.../Public/PluginReferenceDescriptor.h:26-74` (`FPluginReferenceDescriptor`). No project module was compiled or loaded.

#### PROJ-04 — make the UE 5.8 config hierarchy and `SaveConfig` destination guidance precise

- **Priority:** P1 — configuration reproducibility; the current reference calls a partial list “canonical” and promises a `SaveConfig` destination that the API does not promise.
- **Locations:** `skills/core/project-structure/references/config-system.md:12-31` and `:134-144`; `:198-205` for the historical stability claim; `skills/core/project-structure/references/folder-layout-and-vcs.md:123-130` for the Saved/Config explanation.
- **Finding:** UE 5.8.2 `GConfigLayers[]` includes `ProjectGenerated`, `CustomConfig`, `ProjectPlatformGenerated`, and `CustomConfigPlatform` layers in addition to the common rows shown. Epic's version-matched configuration documentation also lists `Engine/Platforms/<PLATFORM>/Config` and `Project/Platforms/<PLATFORM>/Config` extension layers. `SaveConfig()` uses the class's resolved config filename unless a filename/context is supplied; explicit `TryUpdateDefaultConfigFile`, `UpdateGlobalUserConfigFile`, and `UpdateProjectUserConfigFile` APIs exist for named destinations. The source does not support the blanket “highest-priority non-read-only file (typically Default in dev or User in shipped builds)” rule.
- **Exact proposed replacement:**

```diff
--- a/skills/core/project-structure/references/config-system.md
+++ b/skills/core/project-structure/references/config-system.md
@@
-The canonical layer order, from `ConfigHierarchy.h` (`Engine/Source/Runtime/Core/Public/Misc/ConfigHierarchy.h`):
+The following is the common static sequence from `ConfigHierarchy.h`; UE 5.8 also has
+generated/custom layers and platform-extension expansions, so this abbreviated table is
+not an exhaustive list of every file that can participate:
@@
 `SaveConfig` is declared on `UObject`; it respects the class's config category and writes
-to the highest-priority non-read-only file in the hierarchy (typically `Default*.ini` in
-dev or `User*.ini` in shipped builds).
+to the class's resolved config filename unless the call supplies an explicit filename or
+save context. Use `TryUpdateDefaultConfigFile`, `UpdateGlobalUserConfigFile`, or
+`UpdateProjectUserConfigFile` when the intended config layer matters; do not infer the
+destination solely from whether the process is a development or shipped build.
@@
-For rendering cvars (`r.*`) the canonical section is
-`[/Script/Engine.RendererSettings]`; for streaming (`s.*`) use
-`[/Script/Engine.StreamingSettings]`.
+For most rendering cvars (`r.*`) use `[/Script/Engine.RendererSettings]`; for streaming
+(`s.*`) use `[/Script/Engine.StreamingSettings]`. UE 5.8's documented exceptions include
+`r.SupportAllShaderPermutations` in `[/Script/Engine.RendererOverrideSettings]`, `gc.*` in
+`[/Script/Engine.GarbageCollectionSettings]`, and `cook.*` in
+`[/Script/UnrealEd.CookerSettings]`.
@@
-  - The config layer ordering is stable across UE5. The `ConfigHierarchy.h` inline array
-  `GConfigLayers[]` is the canonical source of truth and has not changed since UE5.0.
+  - For UE 5.8, treat the installed `ConfigHierarchy.h`, its expansion rules, and the
+  version-matched Epic configuration documentation as the source of truth; do not assert
+  historical stability across engine branches without checking each branch.
```

```diff
--- a/skills/core/project-structure/references/folder-layout-and-vcs.md
+++ b/skills/core/project-structure/references/folder-layout-and-vcs.md
@@
-The editor writes project-settings changes to `Saved/Config/...` during editing sessions
-and then copies them to `Config/Default*.ini` on save. If you quit without saving,
-`Saved/Config/` may contain changes not in `Config/`.
+`Saved/Config/` is generated/runtime configuration state and can contain local overrides;
+the exact file written by a settings UI or `SaveConfig` depends on the setting class and
+save path. Persistent team settings belong in the appropriate `Config/Default*.ini` or
+platform/config-extension file, not in `Saved/Config/`. Treat unsaved editor changes as
+local state rather than assuming every editor setting follows one copy-to-default path.
```

- **Practical task benefit:** stops platform-extension, generated-layer, and runtime-user settings from being placed in the wrong file and makes config persistence deterministic for automation and teams.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Misc/ConfigHierarchy.h:9-45,90-145` (`GConfigLayers`, plugin/platform expansion); `.../Runtime/CoreUObject/Private/UObject/Obj.cpp:3678-3710,3958-3997` (`SaveConfig`, default/global-user/project-user filename APIs); `.../Runtime/CoreUObject/Private/UObject/Class.cpp:7144-7185` (`UClass::GetConfigName`); `.../Runtime/CoreUObject/Public/UObject/Object.h:1280-1316` (explicit save/update APIs); and Epic UE 5.8 configuration docs <https://dev.epicgames.com/documentation/unreal-engine/configuration-files-in-unreal-engine?application_version=5.8> (verified page version 5.8, hierarchy and CVar categories). No editor settings session or save operation was run.

#### PROJ-05 — add the UE 5.8 project plugin-override layer and external GameFeature path note

- **Priority:** P2 — practical UE 5.8 adoption; this is a scoped, stable config/project feature that lets a project override plugin settings without editing third-party plugin files.
- **Locations:** insertion after `skills/core/project-structure/references/config-system.md:169` (before `Saved/ vs Default*/`); insertion after `skills/core/project-structure/references/uproject-and-modules.md:28`.
- **Finding:** UE 5.8 release notes introduce `PluginOverride{TYPE}.ini` in the project `Config/` directory, with no per-platform version. UE 5.8.2 source adds it as dynamic priority `ProjectPluginOverrides = 49`, after project plugins (`30`) and before GameFeature (`50`) and hotfix (`80`) layers. The release notes also state that GameFeaturePlugins can now work from `AdditionalPluginDirectories`; the descriptor reader remaps additional plugin directories to `../RemappedPlugins/` for cooked builds.
- **Exact proposed addition:**

```diff
--- a/skills/core/project-structure/references/config-system.md
+++ b/skills/core/project-structure/references/config-system.md
@@
 Available typed getters on `FConfigCacheIni` (all in `ConfigCacheIni.h`):
 `GetBool`, `GetInt`, `GetInt64`, `GetFloat`, `GetDouble`, `GetString`, `GetText`,
 `GetArray`.
+
+### UE 5.8 project plugin overrides
+
+A project can override plugin config without modifying the plugin by placing files such as
+`Config/PluginOverrideEngine.ini` or `Config/PluginOverrideGame.ini` in the project. UE 5.8
+loads this dynamic project-plugin-override layer after engine/project plugin layers and before
+GameFeaturePlugin and hotfix layers. There is no per-platform `PluginOverride` file; use the
+category file that matches the branch being overridden.
```

```diff
--- a/skills/core/project-structure/references/uproject-and-modules.md
+++ b/skills/core/project-structure/references/uproject-and-modules.md
@@
 | `AdditionalPluginDirectories` | private `TArray<FString>` | Extra directories to scan for plugins. |
 | `AdditionalRootDirectories` | private `TArray<FString>` | Extra directories to scan for modules; read/written by editor builds. |
+
+UE 5.8 also permits GameFeaturePlugins to be discovered from `AdditionalPluginDirectories`.
+When cooked data is required, the engine remaps those external directories to its packaged
+`../RemappedPlugins/` location; validate the packaged layout rather than relying on an editor
+absolute path.
```

- **Practical task benefit:** gives teams a supported project-owned override for plugin settings and a concrete warning for external GameFeature plugin paths during cook/package work.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Misc/ConfigCacheIni.h:1101-1117` (`DynamicLayerPriority`) and `.../Runtime/Core/Private/Misc/ConfigContext.cpp:1226-1239` (`PluginOverride{TYPE}.ini` insertion); `.../Runtime/Projects/Private/ProjectDescriptor.cpp:147-172` (`AdditionalPluginDirectories` and cooked remap). Epic UE 5.8 release notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:5630-5634,5723-5726` documents PluginOverride and GameFeature external-directory support. No GameFeature or packaged-project test was run.

#### PROJ-06 — correct project Binaries ownership wording

- **Priority:** P2 — source-control hygiene; the folder reference attributes the editor executable to a project `Binaries/` directory even though the installed engine owns that executable.
- **Location:** `skills/core/project-structure/references/folder-layout-and-vcs.md:100-103`.
- **Finding:** Epic's UE 5.8 directory-structure documentation describes project `Binaries` generally as compiled output. On the verified installation, `UnrealEditor.exe` is at `Engine/Binaries/Win64/UnrealEditor.exe`; a project `Binaries` directory contains project/target products rather than the shared editor executable.
- **Exact proposed replacement:**

```diff
--- a/skills/core/project-structure/references/folder-layout-and-vcs.md
+++ b/skills/core/project-structure/references/folder-layout-and-vcs.md
@@
-Compiled output: game DLLs (`.dll`/`.so`) and the editor executable recompiled for hot
-reload. Fully regenerated by UBT; never commit.
+Compiled project/target output (`.dll`, `.so`, executables, and related products) generated
+by UBT. The shared `UnrealEditor` executable is engine-owned under `Engine/Binaries/`, not
+a project `Binaries/` product. Fully regenerated as needed; never commit generated output.
```

- **Practical task benefit:** keeps repository ownership and ignore rules accurate without implying that deleting a project directory removes the installed editor.
- **Verified evidence:** installed UE 5.8.2 file `C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe`; Epic UE 5.8 directory-structure documentation <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-directory-structure?application_version=5.8> (verified page version 5.8, project Binaries/Intermediate descriptions). No project build was run.

### No-change checks

- The project folder ownership split, virtual `/Game/`, `/Engine/`, and `/PluginName/` paths, `FPaths::ProjectContentDir`/`ProjectConfigDir`/`ProjectSavedDir`/`ProjectIntermediateDir` references, generated-directory ignore guidance, binary-asset/Git LFS caution, module `Public`/`Private` layout, `EngineAssociation` variants, `FileVersion: 3`, `TargetPlatforms`, `Plugins`, and `IMPLEMENT_MODULE` for additional modules match the inspected UE 5.8.2 source or version-matched Epic documentation, subject to the corrections above.
- The array operators (`+`, `.`, `-`, `!`), `UCLASS(config=...)` plus `UPROPERTY(Config)`, `/Script/Module.Class` section syntax, typed `GConfig` getters, `GetIni` command form, and command-line `-ini`/`-Def...Ini` concepts match the version-matched Epic configuration page. The page explicitly notes that command-line overrides do not work with arrays; this remains a useful caveat to preserve.
- `DefaultInput.ini` as the legacy input category and Enhanced Input bindings as assets remain correctly distinguished. No UE 5.8.2 change justifies removing that compatibility note.
- The `PlatformAllowList`/`PlatformDenyList` spelling and deprecated whitelist fallbacks, `EHostType`/`ELoadingPhase` values, primary macro's deprecated third argument, `TObjectPtr` version note, and project/plugin source-control conventions were not otherwise changed.
- The pinned UE 5.8 release notes' Raw Input deprecation, ZenServer defaults, editor-settings UI improvements, and plugin-specific entries do not require a project-structure edit beyond the PluginOverride and external GameFeature notes above. The checked UE 5.8.1 and UE 5.8.2 hotfix material yielded no additional general `.uproject` schema migration.

### Unresolved questions / verification gaps

- No repository project was opened, converted from Blueprint-only to C++, generated with `UnrealVersionSelector`, compiled, cooked, packaged, or run under UE 5.8.2. Descriptor and config findings are source/documentation checks, not editor/runtime validation.
- The `Enterprise` and `DisableEnginePluginsByDefault` key corrections were verified against parser/writer source, but no external consumer or launcher UI behavior was exercised.
- No target matrix was built for all host types, target configurations, program/game-target filters, platform architectures, additional plugin/root directories, or platform extension directories.
- `SaveConfig` destination behavior was read at API/source level only. Project-specific class flags, explicit filenames, read-only files, config cache state, packaged final paths, and settings UI save behavior remain untested.
- `PluginOverride` precedence and `AdditionalPluginDirectories` cooked remapping were source/release-note verified but not exercised with a real plugin, GameFeaturePlugin, external directory, or packaged output. No marketplace/vendor/platform plugin evidence was used.
- The installed binary check confirms the shared Windows editor path only; other platform binary layouts and custom source-built engine layouts were not inspected.
- The pinned search context found no 5.8.3 announcement; that does not prove that no later private, unreleased, or distribution-specific project/config fix exists.

**Source/doc set checked:** all four repository files listed above, each read in full; installed UE 5.8.2 `Build.version`; `Engine/Source/Runtime/Projects/Public/ProjectDescriptor.h`; `Engine/Source/Runtime/Projects/Public/ModuleDescriptor.h`; `Engine/Source/Runtime/Projects/Public/PluginReferenceDescriptor.h`; `Engine/Source/Runtime/Projects/Private/ProjectDescriptor.cpp`; `Engine/Source/Runtime/Projects/Private/ModuleDescriptor.cpp`; `Engine/Source/Runtime/Projects/Private/PluginReferenceDescriptor.cpp`; `Engine/Source/Runtime/Core/Public/Modules/ModuleManager.h`; `Engine/Source/Runtime/Core/Public/Misc/ConfigHierarchy.h`; `Engine/Source/Runtime/Core/Public/Misc/ConfigCacheIni.h`; `Engine/Source/Runtime/CoreUObject/Public/UObject/Object.h`; `Engine/Source/Runtime/CoreUObject/Private/UObject/Obj.cpp`; `Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp`; `Engine/Source/Runtime/Core/Public/Misc/Paths.h`; `Engine/Source/Runtime/Core/Private/Misc/ConfigContext.cpp`; the verified UE 5.8 Directory Structure and Configuration Files documentation pages; the UE 5.8 release-notes cache; the UE 5.8.1 hotfix material; and the UE 5.8.2 hotfix cache. No marketplace/vendor/platform SDK project evidence was used.

---

## core/profiling-and-optimization

**Status:** findings  
**Repository path:** `skills/core/profiling-and-optimization/`  
**Files reviewed:** `SKILL.md`; `references/instrumenting-cpp.md`; `references/memory-profiling.md`; `references/stat-commands.md`; `references/unreal-insights-and-trace.md`.

**Working-tree reconciliation:** also read the entire new `references/windows-pie-baselines.md` and its main-skill pointer. The inventory for this skill is now six files, not five.

### Verified recommendations

#### PROF-01 — remove the Trace prerequisite from `stat gpu`

- **Priority:** P1 — profiling correctness and iteration speed; the current table can make an agent start a trace merely to use the ordinary GPU stat overlay.
- **Location:** `skills/core/profiling-and-optimization/SKILL.md:41-54`, specifically the `stat gpu` row at `:46`.
- **Finding:** Epic's UE 5.8 Stat Commands page describes `stat GPU` as displaying GPU statistics for the frame. A Trace `gpu` channel is required for the Unreal Insights GPU track, not for the ordinary `stat gpu` console display. The row conflates the quick stat path with the trace path.
- **Exact proposed replacement:**

```diff
--- a/skills/core/profiling-and-optimization/SKILL.md
+++ b/skills/core/profiling-and-optimization/SKILL.md
@@
-| `stat gpu` | GPU pass costs (requires `-trace=gpu` or GPU channel) |
+| `stat gpu` | GPU statistics for the current frame (platform/RHI support applies); a separate `-trace=gpu`/`Gpu` channel is required for the Insights GPU track |
```

- **Practical task benefit:** preserves the low-friction `stat unit` → `stat gpu` triage loop and tells users exactly when a trace is needed.
- **Verified evidence:** Epic UE 5.8 [Stat Commands](https://dev.epicgames.com/documentation/unreal-engine/stat-commands-in-unreal-engine?application_version=5.8) (verified page title/version, `GPU` row: “Displays GPU statistics for the frame”); installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/ProfilingDebugging/TraceAuxiliary.h:142-152` (`FTraceAuxiliary::Start` separately enables trace channels). No in-game stat command was run.

#### PROF-02 — replace the nonexistent `DECLARE_STATS_GROUP_EXTERN` example

- **Priority:** P1 — compile correctness; the cross-file `stat-commands.md` example names a macro that is not declared by UE 5.8.2 `Stats.h`.
- **Locations:** `skills/core/profiling-and-optimization/references/stat-commands.md:88-97`; `skills/core/profiling-and-optimization/references/instrumenting-cpp.md:86-96`.
- **Finding:** UE 5.8.2 defines `DECLARE_STATS_GROUP`, but no `DECLARE_STATS_GROUP_EXTERN` or `DECLARE_STAT_GROUP_EXTERN`. The `stat-commands.md` cross-file snippet uses the nonexistent form; the `instrumenting-cpp.md` snippet already uses the correct type-only `DECLARE_STATS_GROUP` and only needs an explanatory note. The individual cross-file stat still uses `DECLARE_CYCLE_STAT_EXTERN` with `DEFINE_STAT` in one `.cpp`.
- **Exact proposed replacement:**

```diff
--- a/skills/core/profiling-and-optimization/references/stat-commands.md
+++ b/skills/core/profiling-and-optimization/references/stat-commands.md
@@
-DECLARE_STATS_GROUP_EXTERN(TEXT("My System"), STATGROUP_MySystem, STATCAT_Advanced, MYGAME_API);
+DECLARE_STATS_GROUP(TEXT("My System"), STATGROUP_MySystem, STATCAT_Advanced);
 DECLARE_CYCLE_STAT_EXTERN(TEXT("Step A"), STAT_MySystem_StepA, STATGROUP_MySystem, MYGAME_API);
```

```diff
--- a/skills/core/profiling-and-optimization/references/instrumenting-cpp.md
+++ b/skills/core/profiling-and-optimization/references/instrumenting-cpp.md
@@
 For stats shared across files (declare in header, define in one `.cpp`):
+`Stats.h` has no `DECLARE_STATS_GROUP_EXTERN`; keep the type-only `DECLARE_STATS_GROUP`
+in the header and use `DECLARE_CYCLE_STAT_EXTERN`/`DEFINE_STAT` for each cross-file stat.
```

- **Practical task benefit:** prevents a copied header from failing preprocessing and keeps the valid one-definition boundary on the stat itself.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/Stats/Stats.h:39-72` (`DECLARE_STAT_GROUP` implementation), `:120-132` (`DEFINE_STAT`/`DECLARE_CYCLE_STAT`), and `:171-176` (`DECLARE_CYCLE_STAT_EXTERN`). An exact search of the installed 5.8.2 `Stats.h` found no `DECLARE_STATS_GROUP_EXTERN` or `DECLARE_STAT_GROUP_EXTERN`. No custom translation units were compiled.

#### PROF-03 — make LLM, memory-trace, and CSV build claims conditional

- **Priority:** P1 — diagnostic correctness; the references promise data in builds where the relevant instrumentation may compile to no-ops, and omit several UE 5.8 deprecations.
- **Locations:** `skills/core/profiling-and-optimization/SKILL.md:83-90`, `:172-187`, and `:202-215`; `references/memory-profiling.md:11-17`, `:79-94`, and `:148-158`; `references/instrumenting-cpp.md:10-21` and `:138-143`.
- **Finding:** `MemoryTrace.h` defaults memory allocation tracing to non-Shipping only when the feature is available; `LowLevelMemTrackerDefines.h` derives `LLM_ENABLED_IN_CONFIG` from non-Shipping/Test policy and application type; `TagTrace.h` compiles memory-tag tracing only when its build define and `UE_TRACE_ENABLED` are present. `CsvProfiler.h` gates the category macros on `CSV_PROFILER` and timing macros on `CSV_PROFILER && !CSV_PROFILER_MINIMAL`. Therefore “Development+,” “memtag works in any build,” and unconditional Shipping/Test CSV wording are too broad. UE 5.8 also deprecates `LLM_ALLOW_ASSETS_TAGS`, `LLM_ALLOW_UOBJECTCLASSES_TAGS`, `LLM_ALLOW_STATS`, and `LLM_ENABLED_STAT_TAGS` rather than only the first of those.
- **Exact proposed replacement:**

```diff
--- a/skills/core/profiling-and-optimization/SKILL.md
+++ b/skills/core/profiling-and-optimization/SKILL.md
@@
-| `memalloc` | Every allocation + callstack (heavy — Development build only) |
+| `memalloc` | Every allocation + callstack (heavy; non-Shipping only when memory tracing is compiled; packaged capture should use a Development build) |
@@
-`CSV_SCOPED_TIMING_STAT` records per-frame timings to a CSV file, usable in Shipping and
-Test builds. Useful for automated performance regression tests.
+`CSV_SCOPED_TIMING_STAT` records per-frame timings to a CSV file when `CSV_PROFILER` is
+enabled and `CSV_PROFILER_MINIMAL` is false. A target may enable it outside the default
+configuration policy; verify the target before promising Shipping/Test output. It is useful
+for automated performance regression tests.
@@
-LLM instruments every allocation with a tag. Enable with `-llm` on the command line; view
-with `stat llm`, `stat llmfull`, or via Insights MemTag channel.
+When compiled in, LLM instruments allocations with tags. `-llm` enables the runtime tracker;
+it cannot add LLM support to a target where `ENABLE_LOW_LEVEL_MEM_TRACKER` or memory-tag
+tracing was compiled out. View with `stat llm`, `stat llmfull`, or the Insights MemTag channel.
```

```diff
--- a/skills/core/profiling-and-optimization/references/memory-profiling.md
+++ b/skills/core/profiling-and-optimization/references/memory-profiling.md
@@
-| `stat llm` / `stat llmfull` | Per-LLM-tag totals | Low (with `-llm`) | Development+ |
-| Insights MemTag | Per-tag per-frame graph | Low | Development+ |
-| Insights MemAlloc | Every alloc + callstack | High | Development only |
+| `stat llm` / `stat llmfull` | Per-LLM-tag totals | Low (with `-llm`) | Non-Shipping when LLM is compiled in |
+| Insights MemTag | Per-tag per-frame graph | Low | Target/config dependent; requires compiled LLM and memory-tag tracing |
+| Insights MemAlloc | Every alloc + callstack | High | Non-Shipping when memory tracing is compiled; packaged captures should use Development |
@@
-Development build only for `memalloc` (callstacks). `memtag` works in any build with
-`-llm`.
+`memalloc` requires a non-Shipping build with memory tracing compiled in; Epic's packaged
+Memory Insights workflow uses Development. `memtag` also requires compiled LLM/memory-tag
+tracing support; `-llm` enables the runtime tracker but does not change compile-time support.
@@
-`LLM_ALLOW_ASSETS_TAGS` is deprecated in 5.8 — per-asset tagging is always available
-  when `ENABLE_LOW_LEVEL_MEM_TRACKER` is 1.
+`LLM_ALLOW_ASSETS_TAGS`, `LLM_ALLOW_UOBJECTCLASSES_TAGS`, `LLM_ALLOW_STATS`, and
+`LLM_ENABLED_STAT_TAGS` are deprecated in 5.8; do not define them. The corresponding tag
+features are available when `ENABLE_LOW_LEVEL_MEM_TRACKER` is 1.
```

```diff
--- a/skills/core/profiling-and-optimization/references/instrumenting-cpp.md
+++ b/skills/core/profiling-and-optimization/references/instrumenting-cpp.md
@@
-| Per-frame CSV column for automation tests | `CSV_SCOPED_TIMING_STAT` | CSV file | Yes (Test) |
+| Per-frame CSV column for automation tests | `CSV_SCOPED_TIMING_STAT` | CSV file | When `CSV_PROFILER` is enabled (including any explicitly enabled Shipping/Test target) |
@@
-Available in Shipping and Test builds when `CSV_PROFILER` is enabled. Records per-frame
-timing columns to a `.csv` file; ideal for automated performance regression baselines.
+Available in any target where `CSV_PROFILER` is enabled and `CSV_PROFILER_MINIMAL` is false;
+do not assume a project's Shipping or Test target enables it. Records per-frame timing
+columns to a `.csv` file; ideal for automated performance regression baselines.
```

- **Practical task benefit:** agents will check target/build defines before prescribing a diagnostic, avoiding empty traces, missing LLM tags, and false Shipping instrumentation guarantees.
- **Verified evidence:** UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/ProfilingDebugging/MemoryTrace.h:17-27` (`UE_MEMORY_TRACE_ENABLED`), `.../Core/Public/HAL/LowLevelMemTrackerDefines.h:10-31` (`LLM_ENABLED_IN_CONFIG`), `.../Core/Public/HAL/LowLevelMemTracker.h:14-34` (derived `ENABLE_LOW_LEVEL_MEM_TRACKER` and 5.8 deprecations), `.../Core/Public/ProfilingDebugging/TagTrace.h:29-34` (`UE_MEMORY_TAGS_TRACE_ENABLED`), and `.../Core/Public/ProfilingDebugging/CsvProfiler.h:44-53,93-120` (`CSV_PROFILER`/`CSV_PROFILER_MINIMAL` gates). Epic UE 5.8 [Memory Insights](https://dev.epicgames.com/documentation/unreal-engine/memory-insights-in-unreal-engine?application_version=5.8) requires memory tracing from process start and a Development packaged workflow. No target build defines or packaged trace were exercised.

#### PROF-04 — add UE 5.8 automatic hitch snapshots

- **Priority:** P2 — practical hitch diagnosis; this turns a transient game/render hitch into a trace and screenshot pair without requiring an engineer to predict the frame.
- **Location:** insertion after `skills/core/profiling-and-optimization/SKILL.md:51` (`stat dumphitches`), or in the diagnostics subsection of `references/stat-commands.md` after its `dumphitches` row at `:70`.
- **Finding:** UE 5.8 release notes add `snapshothitches -start`/`-stop`. The installed 5.8.2 `TraceHitches.cpp` registers the command in non-Shipping builds with `STATS`, tests game/render frame time against `GHitchThresholdMS`, and writes a `.utrace` plus `.png` under the profiling `Hitches/<InstanceId>` directory. This is distinct from `stat dumphitches`, which logs a hitch.
- **Exact proposed addition:**

```diff
--- a/skills/core/profiling-and-optimization/SKILL.md
+++ b/skills/core/profiling-and-optimization/SKILL.md
@@
 | `stat dumphitches` | Log any hitch above `t.HitchFrameTimeThreshold` |
+| `snapshothitches -start` / `snapshothitches -stop` | Automatically save a trace snapshot and screenshot when a game/render hitch exceeds the hitch threshold (non-Shipping + `STATS` builds) |
```

```diff
--- a/skills/core/profiling-and-optimization/references/stat-commands.md
+++ b/skills/core/profiling-and-optimization/references/stat-commands.md
@@
 | `dumphitches` | Diagnostics | Log any frame exceeding `t.HitchFrameTimeThreshold` |
+| `snapshothitches -start` / `snapshothitches -stop` | Diagnostics | Start/stop automatic non-Shipping hitch snapshots; writes `.utrace` and `.png` files below `Saved/Profiling/Hitches/<InstanceId>/` |
```

- **Practical task benefit:** gives teams a built-in artifact for intermittent hitch reports while preserving `dumphitches` for low-overhead log-only detection.
- **Verified evidence:** UE 5.8 release notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:5942-5946` (`snapshot hitches`); installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/ProfilingDebugging/TraceHitches.cpp:15-30,45-71,73-103` (`FTraceHitches`, command registration, threshold check, `FTraceAuxiliary::WriteSnapshot`, and `FScreenshotRequest`). No hitch snapshot command was run.

#### PROF-05 — correct the UE 5.8.2 CPU macro line inventory

- **Priority:** P2 — citation and copy-paste accuracy; the source line reference currently says all CPU scope variants are at one line.
- **Locations:** `skills/core/profiling-and-optimization/SKILL.md:164-168`; `references/instrumenting-cpp.md:57-59`.
- **Finding:** UE 5.8.2 places the variants at distinct declarations: `_STR` at `408-409`, plain `SCOPE` at `453-454`, `_ON_CHANNEL` at `469-470`, and `_TEXT` at `489-490`. The current “all in `CpuProfilerTrace.h:453`” wording is not a reliable source locator.
- **Exact proposed replacement:**

```diff
--- a/skills/core/profiling-and-optimization/SKILL.md
+++ b/skills/core/profiling-and-optimization/SKILL.md
@@
-Scope variants (all in `CpuProfilerTrace.h:453`):
- `TRACE_CPUPROFILER_EVENT_SCOPE(Name)` — literal token, lowest overhead.
- `TRACE_CPUPROFILER_EVENT_SCOPE_STR(NameStr)` — const string pointer.
- `TRACE_CPUPROFILER_EVENT_SCOPE_TEXT(Name)` — dynamic `TCHAR*`/`FName`.
- `TRACE_CPUPROFILER_EVENT_SCOPE_ON_CHANNEL(Name, Channel)` — gated on a custom channel.
+Scope variants in UE 5.8.2 `CpuProfilerTrace.h`:
+- `TRACE_CPUPROFILER_EVENT_SCOPE(Name)` (`:453-454`) — literal token, lowest overhead.
+- `TRACE_CPUPROFILER_EVENT_SCOPE_STR(NameStr)` (`:408-409`) — const string pointer.
+- `TRACE_CPUPROFILER_EVENT_SCOPE_TEXT(Name)` (`:489-490`) — dynamic `TCHAR*`/`FName`.
+- `TRACE_CPUPROFILER_EVENT_SCOPE_ON_CHANNEL(Name, Channel)` (`:469-470`) — gated on a custom channel.
```

```diff
--- a/skills/core/profiling-and-optimization/references/instrumenting-cpp.md
+++ b/skills/core/profiling-and-optimization/references/instrumenting-cpp.md
@@
-Key `FEventScope` constructors are at `CpuProfilerTrace.h:188-233`; the
-`TRACE_CPUPROFILER_EVENT_SCOPE(Name)` macro is at line 453.
+Key `FEventScope` constructors are at `CpuProfilerTrace.h:188-233`; the plain
+`TRACE_CPUPROFILER_EVENT_SCOPE(Name)` macro is at `:453-454`, `_STR` at `:408-409`,
+`_ON_CHANNEL` at `:469-470`, and `_TEXT` at `:489-490` in UE 5.8.2.
```

- **Practical task benefit:** keeps source citations useful when an agent chooses between static, dynamic, and channel-gated instrumentation.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/ProfilingDebugging/CpuProfilerTrace.h:185-233,403-434,448-490`; the header comments explicitly distinguish static/constant from dynamic names and require both the CPU and custom channel for channel-gated events.

#### PROF-06 — document UE 5.8 shared Insights annotations

- **Priority:** P2 — team workflow; shared annotations make a trace review reproducible without modifying the capture.
- **Location:** insertion after `skills/core/profiling-and-optimization/references/unreal-insights-and-trace.md:100`, before the GPU-track subsection at `:102`.
- **Finding:** the UE 5.8 release notes add time, time-range, and event-based annotations in Unreal Insights and save annotation data in a sidecar `.ini` file. The repository reference documents the timing panels but not this shareable review artifact.
- **Exact proposed addition:**

```diff
--- a/skills/core/profiling-and-optimization/references/unreal-insights-and-trace.md
+++ b/skills/core/profiling-and-optimization/references/unreal-insights-and-trace.md
@@
4. Double-click the bar in the Timing panel to zoom into that scope.
+
+UE 5.8 Unreal Insights can add time, time-range, and event-based annotations to a trace.
+The annotation data is saved in a sidecar `.ini` file, so share the sidecar with the `.utrace`
+when handing a review to another engineer. The annotations do not replace the original trace
+or a measured before/after capture.
```

- **Practical task benefit:** lets teams exchange marked-up profiling findings while keeping the evidence-led before/after workflow intact.
- **Verified evidence:** UE 5.8 release notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:5918-5928` (Insights annotations and Go to Frame/Time); Epic UE 5.8 [Unreal Insights](https://dev.epicgames.com/documentation/unreal-engine/unreal-insights-in-unreal-engine?application_version=5.8) confirms `.utrace`/`.ucache` trace artifacts and the Timing Insights workflow. No trace was opened or annotated.

### No-change checks

- The measure-first workflow, `stat unit` interpretation, Trace Server/Unreal Insights component split, default Trace channels, late-connect behavior, symbol-path order, `TRACE_BOOKMARK`, `TRACE_CPUPROFILER_EVENT_SCOPE` naming pitfall, `DECLARE_CYCLE_STAT`/`DECLARE_CYCLE_STAT_EXTERN`, scoped timers, `ProfileGPU`, GPU Visualizer, and Memory Insights query concepts remain aligned with the installed UE 5.8.2 declarations and version-matched Epic documentation after the corrections above.
- `CSV_SCOPED_TIMING_STAT`, `CSV_CUSTOM_STAT`, `FScopedDurationTimer`, `FScopedDurationTimeLogger`, `stat startfile`/`stopfile`, and the LLM tag-scope examples name symbols that remain present in UE 5.8.2. The build-configuration caveat is retained rather than removing those workflows.
- UE 5.8 release notes add other Insights extensions (World Partition, Audio, Slate, Networking, Cooking, and Asset Loading Insights); those belong to the corresponding repository skills and are not duplicated here. The release-note Insights additions relevant to this skill are the hitch snapshots and shareable annotations above.
- The checked UE 5.8.1 and UE 5.8.2 hotfix notes contain no general migration that removes the core stat/Trace/LLM/CSV APIs used here. The 5.8.2 fixes that mention rendering, Niagara, physics, and logging are recorded in their scoped skills rather than treated as profiler API changes.

### Unresolved questions / verification gaps

- No custom target was compiled, so the project's actual `CSV_PROFILER`, `CSV_PROFILER_MINIMAL`, `LLM_ENABLED_IN_CONFIG`, `UE_MEMORY_TAGS_TRACE_ENABLED`, or `UE_TRACE_ENABLED` values remain unknown.
- No PIE, standalone, packaged Development, Test, Shipping, or platform-specific run captured `stat gpu`, Trace channels, LLM, CSV, Memory Insights, or `snapshothitches`; command availability and output are source/documentation verified, not runtime verified.
- GPU stat availability and exact pass detail depend on the platform/RHI; the Epic page was checked but no RHI capture was available.
- The Epic documentation states cross-release trace compatibility, but no 5.5/5.8 trace was opened in the installed 5.8.2 viewer. The report does not make a stronger compatibility guarantee.
- No profiler performance overhead measurement was made; “low” and “heavy” remain the source/documentation characterizations, not measurements on project hardware.

**Source/doc set checked:** the original five repository files plus the new Windows PIE reference were read in full; installed UE 5.8.2 `Build.version`; `Engine/Source/Runtime/Core/Public/Stats/Stats.h`; `Engine/Source/Runtime/Core/Public/ProfilingDebugging/CpuProfilerTrace.h`; `Engine/Source/Runtime/Core/Public/ProfilingDebugging/CsvProfiler.h`; `Engine/Source/Runtime/Core/Public/ProfilingDebugging/MemoryTrace.h`; `Engine/Source/Runtime/Core/Public/ProfilingDebugging/TagTrace.h`; `Engine/Source/Runtime/Core/Public/HAL/LowLevelMemTracker.h`; `Engine/Source/Runtime/Core/Public/HAL/LowLevelMemTrackerDefines.h`; `Engine/Source/Runtime/Core/Public/ProfilingDebugging/TraceAuxiliary.h`; `Engine/Source/Runtime/Engine/Private/ProfilingDebugging/TraceHitches.cpp`; the version-matched Epic Stat Commands, Unreal Insights, Trace, Timing Insights, and Memory Insights pages; the UE 5.8 release-notes cache; the UE 5.8.1 hotfix material; and the UE 5.8.2 hotfix cache. No custom project, trace, or runtime profile was used.

### Working-tree reference review — partially verified

`references/windows-pie-baselines.md:10–11`: UE 5.8.2 `Engine/Source/Runtime/Core/Private/ProfilingDebugging/CsvProfiler.cpp:3151–3154` emits `HasHeaderRowAtEnd=1`, and `:5098–5104` looks up and enables `r.GPUCsvStatsEnabled` for `csvGpuStats`. Retain the native CSV metadata/CVar guidance, separate measurement windows, explicit observer overhead and persistence readback. No new correction was established for those source-backed points.

The file's VibeUE/EditorToolset `StartPIE`, `warmupSeconds`, PerformanceService, window-size calibration and GPU-event readbacks are **author-reported integration observations**, not verified by this engine-source audit. Exact service version/schema, original traces and the reported two-pixel offset are unresolved. No adapter was invoked or another project entered. Keep these observations explicitly integration/machine-specific; do not promote them into universal Unreal API guarantees.

---

## core/save-and-load

**Status:** findings  
**Repository path:** `skills/core/save-and-load/`  
**Files reviewed:** `SKILL.md`; `references/savegame-objects-and-slots.md`; `references/serializing-actor-state.md`; `references/versioning-and-migration.md`.

### Verified recommendations

#### SAVE-01 — correct the slot pipeline: UE 5.8.2 does use the proxy archive

- **Priority:** P1 — copy-paste correctness; the current reference tells agents that the normal slot path does not use `FObjectAndNameAsStringProxyArchive`, while the installed implementation uses it to serialize object references and names. Following the wrong mental model can produce incompatible custom byte streams or unsafe raw-pointer assumptions.
- **Location:** `skills/core/save-and-load/references/savegame-objects-and-slots.md:11-15`.
- **Finding:** `UGameplayStatics::SaveGameToMemory` writes the save header and then constructs `FObjectAndNameAsStringProxyArchive` before calling `USaveGame::Serialize`. `SaveGameToSlot` delegates to that memory path and then calls `SaveDataToSlot`; it does not write raw UObject pointers. The existing “not used here” sentence is false for UE 5.8.2.
- **Exact proposed replacement:**

```diff
--- a/skills/core/save-and-load/references/savegame-objects-and-slots.md
+++ b/skills/core/save-and-load/references/savegame-objects-and-slots.md
@@
-1. `UGameplayStatics::SaveGameToSlot` (GameplayStatics.h:1167) serializes the `USaveGame` object
-   into a `TArray<uint8>` using tagged property serialization (FObjectAndNameAsStringProxyArchive
-   is **not** used here — all non-transient UPROPERTYs are written).
+1. `UGameplayStatics::SaveGameToSlot` (GameplayStatics.h:1167) delegates to
+   `SaveGameToMemory`, which writes the save header and serializes the `USaveGame` object into a
+   `TArray<uint8>` through `FObjectAndNameAsStringProxyArchive`. The proxy converts object
+   references and names to string forms; with the normal slot path the serializer writes all
+   non-transient `UPROPERTY`s, not only properties marked `SaveGame`.
```

- **Practical task benefit:** keeps normal SaveGame bytes and actor-state bytes conceptually distinct without claiming that the slot path stores process-local pointers; agents can safely use `SaveGameToMemory`/`LoadGameFromMemory` as the exact two-phase path.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/GameplayStatics.cpp:2371-2387` (`UGameplayStatics::SaveGameToMemory` constructs `FObjectAndNameAsStringProxyArchive`), `:2428-2436` (`SaveGameToSlot` delegates to `SaveGameToMemory` and `SaveDataToSlot`), and `:2457-2488` (`LoadGameFromMemory` reads the header and uses the proxy archive); `.../Engine/Classes/Kismet/GameplayStatics.h:1157-1167` documents that `SaveGameToSlot` writes all non-transient properties and does not check the `SaveGame` flag. UE 5.8.2 source.

#### SAVE-02 — document the actual completion result for `ULocalPlayerSaveGame` saves

- **Priority:** P1 — data-loss avoidance; callers can currently treat a `true` return from a local-player save as durable success even though the API documents it as request acceptance and reports the I/O result later.
- **Location:** precise insertion point after `skills/core/save-and-load/SKILL.md:178` (the `AsyncLoadOrCreateSaveGameForLocalPlayer` example), and in `references/versioning-and-migration.md` after the hook list at `:115`.
- **Finding:** `SaveGameToSlotForLocalPlayer()` and `AsyncSaveGameToSlotForLocalPlayer()` return `true` when the save was requested. The synchronous implementation calls `HandlePostSave(bSuccess)` before returning, and the async implementation calls it from the completion delegate. The generic `UGameplayStatics::AsyncSaveGameToSlot` delegate also carries the final `bool bSuccess`.
- **Exact proposed addition:**

```diff
--- a/skills/core/save-and-load/SKILL.md
+++ b/skills/core/save-and-load/SKILL.md
@@
 ULocalPlayerSaveGame::AsyncLoadOrCreateSaveGameForLocalPlayer(
     UMyPlayerSave::StaticClass(), PlayerController, TEXT("PlayerSlot"),
     FOnLocalPlayerSaveGameLoaded::CreateUObject(this, &AMyHUD::OnPlayerSaveLoaded));
 ```
+
+For saving a `ULocalPlayerSaveGame`, `SaveGameToSlotForLocalPlayer()` and
+`AsyncSaveGameToSlotForLocalPlayer()` return whether the request was accepted, not the final
+platform-write result. Override `HandlePostSave(bool bSuccess)` (or the Blueprint
+`OnPostSave` event), or inspect `WasLastSaveSuccessful()` after completion. The generic
+`AsyncSaveGameToSlot` delegate reports its final `bSuccess` value directly.
```

```diff
--- a/skills/core/save-and-load/references/versioning-and-migration.md
+++ b/skills/core/save-and-load/references/versioning-and-migration.md
@@
 - `HandlePreSave()` / `HandlePostSave(bool)` — hooks around the save operation.
+- `SaveGameToSlotForLocalPlayer()` / `AsyncSaveGameToSlotForLocalPlayer()` return request
+  acceptance; use `HandlePostSave(bool)`, `OnPostSave`, or `WasLastSaveSuccessful()` for the
+  final result.
```

- **Practical task benefit:** prevents UI, autosave, and checkpoint code from announcing or advancing progress before the platform save actually succeeds.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/GameFramework/SaveGame.h:83-95` documents request acceptance and post-save error handling; `.../Engine/Private/GameFramework/SaveGame.cpp:142-192` shows the sync/async request paths; `:195-210` calls `HandlePostSave(bSuccess)`; `.../Engine/Classes/Kismet/GameplayStatics.h:1145-1155` documents the generic async completion delegate. UE 5.8.2 source.

#### SAVE-03 — state that generic `LoadGameFromSlot` does not initialize local-player hooks

- **Priority:** P1 — migration correctness; the current `ULocalPlayerSaveGame` section can lead an agent to load through `UGameplayStatics` and assume `HandlePostLoad`/local-player association/version initialization ran automatically.
- **Locations:** `skills/core/save-and-load/SKILL.md:162-181`; `references/versioning-and-migration.md:71-116`.
- **Finding:** the local-player helper calls `ProcessLoadedSave`, which calls `InitializeSaveGame(LocalPlayer, SlotName, true)` and therefore `HandlePostLoad()`. Generic `UGameplayStatics::LoadGameFromSlot` only loads and returns a `USaveGame*`; it does not call `InitializeSaveGame`. The installed `SaveGame.h` comments explicitly say that generic loading requires manual initialization for this subclass.
- **Exact proposed replacement:**

```diff
--- a/skills/core/save-and-load/SKILL.md
+++ b/skills/core/save-and-load/SKILL.md
@@
-`ULocalPlayerSaveGame` (also in `SaveGame.h`) extends `USaveGame` with built-in versioning,
-`HandlePostLoad`/`HandlePreSave`/`HandlePostSave` hooks, and synchronous/async helpers tied to a
-specific `ULocalPlayer`. It is the recommended base for per-user saves when your game supports
-multiple local players or needs structured versioning:
+`ULocalPlayerSaveGame` (also in `SaveGame.h`) extends `USaveGame` with built-in versioning,
+`HandlePostLoad`/`HandlePreSave`/`HandlePostSave` hooks, and synchronous/async helpers tied to a
+specific `ULocalPlayer`. Use its `LoadOrCreateSaveGameForLocalPlayer` helpers when you want the
+association, initialization, reset, and migration hooks applied automatically. A generic
+`UGameplayStatics::LoadGameFromSlot` call only returns the deserialized object; it does not call
+`InitializeSaveGame` or `HandlePostLoad` for you.
```

```diff
--- a/skills/core/save-and-load/references/versioning-and-migration.md
+++ b/skills/core/save-and-load/references/versioning-and-migration.md
@@
-`ULocalPlayerSaveGame` provides a structured version hook pattern:
+`ULocalPlayerSaveGame` provides a structured version hook pattern when loaded through its
+`LoadOrCreateSaveGameForLocalPlayer` helpers. Those helpers call `InitializeSaveGame`, associate
+the local player and slot, and invoke `HandlePostLoad` only for an existing loaded save. If a
+subclass is loaded through generic `UGameplayStatics::LoadGameFromSlot`, call
+`InitializeSaveGame(LocalPlayer, SlotName, true)` before relying on these hooks, or use the
+local-player helper instead.
```

- **Practical task benefit:** makes per-user migration deterministic and prevents missing `SavedDataVersion`, `WasLoaded`, `OwningPlayer`, or post-load fixups when a code path uses the generic slot API.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/GameFramework/SaveGame.h:40-44` documents the generic-load caveat; `:152-168` declares `InitializeSaveGame` and `HandlePostLoad`; `.../Engine/Private/GameFramework/SaveGame.cpp:23-55,111-129` shows the helper calling `ProcessLoadedSave`/`InitializeSaveGame`, and `:300-314` invokes `HandlePostLoad` only when `bWasLoaded`; `.../Engine/Private/GameplayStatics.cpp:2536-2545` shows generic `LoadGameFromSlot` only reading bytes and calling `LoadGameFromMemory`. UE 5.8.2 source.

#### SAVE-04 — add the UE 5.8 experimental Level Streaming Persistence option, with its limits

- **Priority:** P2 — practical feature discovery; streamed-level state currently has to be designed as a bespoke actor-record system even though UE 5.8 ships a runtime plugin that can serialize configured streaming-level persistence into a SaveGame payload.
- **Location:** precise insertion point after `skills/core/save-and-load/SKILL.md:160`, before the `ULocalPlayerSaveGame` subsection.
- **Finding:** UE 5.8 release notes add Blueprint access to the Level Streaming Persistence Manager’s `SerializeTo` and `InitializeFrom` functions for SaveGames. In UE 5.8.2 the feature is a separate `LevelStreamingPersistence` runtime plugin, marked experimental and disabled by default; it is not a replacement for ordinary SaveGame schema/versioning and its restore timing/configuration rules matter.
- **Exact proposed addition:**

```diff
--- a/skills/core/save-and-load/SKILL.md
+++ b/skills/core/save-and-load/SKILL.md
@@
 See [references/serializing-actor-state.md](references/serializing-actor-state.md) for the
 full multi-actor pattern, spawn/restore loop, and gotchas.
 
+## UE 5.8 experimental: Level Streaming Persistence
+
+For a map whose state is tied to streamed levels, UE 5.8 includes the **experimental**,
+disabled-by-default `LevelStreamingPersistence` runtime plugin. Enable the plugin only after
+reviewing its behavior and add the `LevelStreamingPersistence` module dependency. Retrieve
+`ULevelStreamingPersistenceManager` from the world, call `SerializeTo` into a `TArray<uint8>`
+and store that payload in the `USaveGame`; on the same map, call `InitializeFrom` once during
+load. Prefer a native `UWorldSubsystem::Initialize` path early enough to restore before
+`BeginPlay`; a Blueprint-only post-`BeginPlay` restore overwrites already-started actors.
+
+`SerializeTo(..., true)` forces the latest visible-level snapshot. Persistent-level inclusion,
+runtime-actor respawn, destroyed map actors, and the individual properties to persist are
+configuration-dependent (`ULevelStreamingPersistenceSettings`). Keep a normal game schema
+version and validate the payload; this plugin is experimental and should not be presented as
+a general SaveGame or shipping-certification guarantee.
+
 ## Per-player saves — ULocalPlayerSaveGame (UE 5.3+)
```

- **Practical task benefit:** gives World Partition/streaming projects a native starting point for persisted streamed-level state while clearly preserving a fallback for projects that cannot accept an experimental plugin.
- **Verified evidence:** Epic UE 5.8 [release notes, API Change](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#apichange), fetched release-notes cache `C:/Users/Ronald Fraess/AppData/Local/hermes/profiles/game-tool-dev/cache/web/dev.epicgames.com-2bb37c474b.md:12854-12861`; installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Runtime/LevelStreamingPersistence/LevelStreamingPersistence.uplugin:4-22` (`IsExperimentalVersion=true`, `EnabledByDefault=false`, runtime module); `.../Source/LevelStreamingPersistence/Public/LevelStreamingPersistenceManager.h:164-198` (`ULevelStreamingPersistenceManager`, `SerializeTo`, `InitializeFrom`); `.../Public/LevelStreamingPersistenceSettings.h:39-83` (`ULevelStreamingPersistenceSettings`, persistent-level/runtime-actor/destruction settings). UE 5.8.2 source.

#### SAVE-05 — use CoreRedirects or retained fields for renames, and soften type-change wording

- **Priority:** P1 — migration reliability; the current reference presents a retained `_Deprecated` field as the only practical rename route and describes type changes as likely corruption, while UE 5.8.2’s tagged loader has an explicit property-redirect path for SaveGame archives.
- **Locations:** `skills/core/save-and-load/SKILL.md:183-203`; `references/versioning-and-migration.md:14-16`, `:57-68`.
- **Finding:** `UStruct::LoadTaggedPropertiesFromText` sets `bUseRedirects` when the archive is a SaveGame archive (including cooked data), calls `FProperty::FindRedirectedPropertyName`, and only then calls `FindPropertyByName`. A retained old `UPROPERTY` remains a valid fallback for value conversion, but a pure rename can use a tested `[CoreRedirects]` `PropertyRedirects` entry. A type change must be treated as migration-required and verified; “likely fail or corrupt” is too absolute for guidance.
- **Exact proposed replacement:**

```diff
--- a/skills/core/save-and-load/SKILL.md
+++ b/skills/core/save-and-load/SKILL.md
@@
 - For `ULocalPlayerSaveGame`, override `GetLatestDataVersion()` and do fixup in `HandlePostLoad`.
-- Always null-check the loaded object — a corrupt or mismatched save returns `nullptr`.
+- Always null-check the loaded object — missing, empty, unreadable, or unknown-class data can
+  return `nullptr`; a non-null object is not by itself a game-level integrity check.
```

```diff
--- a/skills/core/save-and-load/references/versioning-and-migration.md
+++ b/skills/core/save-and-load/references/versioning-and-migration.md
@@
-Schema **removals and renames** are not safe. The serializer matches by property name; if you
-rename `Health` to `MaxHealth`, old saves load it as 0 (the default). Without a version field
-you cannot detect and migrate old data.
+Schema **removals and renames** require an explicit compatibility decision. The tagged loader
+matches by property name, but UE 5.8.2 can apply a configured property redirect to a SaveGame
+archive. If `Health` becomes `MaxHealth`, either keep a temporary `UPROPERTY` carrying the old
+name for value conversion or add and test a project redirect such as:
+
+```ini
+[CoreRedirects]
++PropertyRedirects=(OldName="MySaveGame.Health",NewName="MySaveGame.MaxHealth")
+```
+
+Use a version migration when the value semantics change; a redirect alone only changes the
+property name mapping. Without a redirect or retained field, the old value is not found.
@@
-Keep the `_Deprecated` field in the class (marked `UPROPERTY` so it still deserializes from the
-old save) until no supported save version uses it, then remove it with a major version bump.
+Keep the `_Deprecated` field (marked `UPROPERTY`) until no supported save version needs a value
+conversion, **or** use a tested `PropertyRedirects` entry for a pure rename. Remove the old
+field/redirect only after the project's supported-save window no longer includes those files.
@@
-| Change a `UPROPERTY` type | No | Serialization will likely fail or corrupt; version-gate |
+| Change a `UPROPERTY` type | Migration required | The old tagged value may not be compatible with the new type; version-gate and test the actual old bytes |
```

- **Practical task benefit:** preserves old values across a pure property rename without unnecessary shadow fields, while still requiring explicit conversion for semantic/type changes.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/CoreUObject/Private/UObject/Class.cpp:1312-1318` (`bUseRedirects` includes `UnderlyingArchive.IsSaveGame()`), `:1342-1357` (`FProperty::FindRedirectedPropertyName` then `FindPropertyByName`); `.../Runtime/CoreUObject/Private/UObject/CoreRedirectsContext.cpp:69-77` maps `PropertyRedirects` to `Type_Property`; `.../Engine/Source/Programs/LiveLinkHub/Config/DefaultEngine.ini:71-73` contains a UE 5.8.2 `+PropertyRedirects=(OldName=...,NewName=...)` example. UE 5.8.2 source.

#### SAVE-06 — do not treat a non-null loaded object as proof that the payload is valid

- **Priority:** P1 — corrupted-save handling; the current null-check wording conflates platform read failure, unknown class, malformed payload, and application-level schema validity.
- **Locations:** `skills/core/save-and-load/SKILL.md:202-203`, `:225-227`; `references/versioning-and-migration.md:117-139`.
- **Finding:** `UGameplayStatics::LoadGameFromMemory` returns `nullptr` for an empty buffer and can fail to construct an unknown class, but after resolving a class it creates the object, calls `Serialize`, and returns the object without an application-level checksum/magic/schema validation result. `LoadGameFromSlot` likewise returns only the object pointer. `DoesSaveGameExistWithResult` is platform-dependent and not a substitute for validating the game payload.
- **Exact proposed replacement:**

```diff
--- a/skills/core/save-and-load/SKILL.md
+++ b/skills/core/save-and-load/SKILL.md
@@
-- Always null-check the loaded object — a corrupt or mismatched save returns `nullptr`.
+- Always null-check the loaded object — missing, empty, unreadable, or unknown-class data can
+  return `nullptr`. A non-null object means the engine constructed the class; validate your
+  `SaveVersion` and any game-level magic/checksum before applying high-value state.
@@
-- `DoesSaveGameExist` not checked **before** load — not strictly required (load returns null on
-  missing), but checking first lets you distinguish "no save" from "corrupt save".
+- `DoesSaveGameExist` not checked **before** load — not strictly required (load returns null on
+  missing), but it can avoid an expected read failure. Do not infer full payload integrity from
+  existence or from a non-null `USaveGame*`; use a game-level schema/integrity check when the
+  distinction matters.
```

```diff
--- a/skills/core/save-and-load/references/versioning-and-migration.md
+++ b/skills/core/save-and-load/references/versioning-and-migration.md
@@
 if (!Loaded)
 {
-    // Null: slot doesn't exist OR save is corrupt / class mismatch.
+    // Null: the slot was absent, the platform read failed, the data was empty, or the
+    // serialized class could not be resolved. Create a fresh save only after deciding how
+    // to preserve/report a possibly unreadable existing slot.
     // Create a fresh save:
@@
 }
 else if (Loaded->SaveVersion > CURRENT_VERSION)
 {
     // Save is from a newer build — handle gracefully (warn, reset, or error).
 }
+
+`LoadGameFromSlot` does not provide a game-level checksum or migration-success result. Treat a
+non-null object as engine-level construction only; validate a magic/version/checksum field before
+applying state that must not be silently lost.
```

- **Practical task benefit:** avoids overwriting a user’s only save after a partial/corrupt read and gives agents a concrete place to add integrity validation instead of relying on pointer nullability.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/GameplayStatics.cpp:2457-2488` (`LoadGameFromMemory` empty-buffer/class lookup/object construction/serialize/return path) and `:2536-2545` (`LoadGameFromSlot` result contract); `.../Engine/Public/SaveGameSystem.h:23-43` documents that `ESaveExistsResult` codes are not guaranteed on all platforms. UE 5.8.2 source.

#### SAVE-07 — make the Epic documentation citation version-matched and remove unverified historical provenance

- **Priority:** P2 — citation maintenance; the primary official link omits the pinned `application_version=5.8` selector, and the current “arrived in UE 5.3” statements were not verified as historical introduction claims by the installed 5.8.2 source or the checked 5.8 release/hotfix notes.
- **Locations:** `skills/core/save-and-load/SKILL.md:232-239`, `:266-269`; `references/savegame-objects-and-slots.md:3-7`, `:84`.
- **Finding:** the APIs named in those passages are present in UE 5.8.2, but the source establishes current availability, not when each API was introduced. Keep the versioned documentation link and state current-engine availability instead of presenting an unverified historical boundary.
- **Exact proposed replacement:**

```diff
--- a/skills/core/save-and-load/SKILL.md
+++ b/skills/core/save-and-load/SKILL.md
@@
-- `ULocalPlayerSaveGame` arrived in UE 5.3 (it lives in `SaveGame.h`, not its own header);
+- `ULocalPlayerSaveGame` is available in the pinned UE 5.8.2 engine (it lives in `SaveGame.h`,
+  not its own header);
   `UAsyncActionHandleSaveGame` is much older (UE 4.x). Earlier code uses only `USaveGame` +
   the `UGameplayStatics` free functions.
-- `SaveGameToMemory` / `LoadGameFromMemory` / `SaveDataToSlot` / `LoadDataFromSlot` are
-  available as of UE 5.3 for in-memory and two-phase save flows.
+- `SaveGameToMemory` / `LoadGameFromMemory` / `SaveDataToSlot` / `LoadDataFromSlot` are
+  present in the pinned UE 5.8.2 engine; verify historical availability against the
+  target branch before using this as a cross-version compatibility claim.
@@
 - Saving and Loading Your Game —
-  <https://dev.epicgames.com/documentation/unreal-engine/saving-and-loading-your-game-in-unreal-engine>
+  <https://dev.epicgames.com/documentation/unreal-engine/saving-and-loading-your-game-in-unreal-engine?application_version=5.8>
```

```diff
--- a/skills/core/save-and-load/references/savegame-objects-and-slots.md
+++ b/skills/core/save-and-load/references/savegame-objects-and-slots.md
@@
-Deep dive for [../SKILL.md](../SKILL.md). Covers how `UGameplayStatics` dispatches to
-`ISaveGameSystem`, file locations on each tier, the binary save helpers added in UE 5.3, slot
+Deep dive for [../SKILL.md](../SKILL.md). Covers how `UGameplayStatics` dispatches to
+`ISaveGameSystem`, file locations on each tier, the binary save helpers present in UE 5.8.2, slot
```

- **Practical task benefit:** agents will cite the pinned documentation version and will not turn a current-source check into an unsupported UE 5.3 compatibility promise.
- **Verified evidence:** Epic’s version-matched [Saving and Loading Your Game](https://dev.epicgames.com/documentation/unreal-engine/saving-and-loading-your-game-in-unreal-engine?application_version=5.8) page reports UE 5.8 and recommends `AsyncSaveGameToSlot` for gameplay saves; installed UE 5.8.2 `.../Engine/Classes/GameFramework/SaveGame.h:47-76` and `.../Engine/Classes/Kismet/GameplayStatics.h:1134-1211` verify current declarations. The checked UE 5.8 release notes and 5.8.1/5.8.2 hotfix notes yielded no SaveGame-specific introduction/deprecation that validates the old “as of 5.3” provenance.

### No-change checks

- The `USaveGame`/`UGameplayStatics` synchronous and asynchronous APIs, `FAsyncSaveGameToSlotDelegate`/`FAsyncLoadGameFromSlotDelegate` signatures, `ISaveGameSystem` platform adapter, `FGenericSaveGameSystem` PC path, `SaveGameToMemory`/`LoadGameFromMemory`, `SaveDataToSlot`/`LoadDataFromSlot`, `StripSaveGameHeader`, `CPF_SaveGame`, `ArIsSaveGame`, and `FObjectAndNameAsStringProxyArchive` names remain present in UE 5.8.2. The async thread-affinity claim is supported by `SaveGameSystem.h` and the `UGameplayStatics` callbacks’ `check(IsInGameThread())`.
- Plain `USaveGame` fields, `UPROPERTY(Transient)`, actor-state byte arrays, stable actor IDs, deferred spawn before `BeginPlay`, and the distinction between gameplay state and user/config settings remain valid conceptual guidance. The proxy archive’s path-based object-reference behavior is retained, with the slot-pipeline correction above.
- The UE 5.8 release notes’ Level Streaming Persistence entry is covered once above rather than duplicated in `levels-and-world-partition`; that skill remains responsible for streaming/world-authoring concerns, while this skill documents the SaveGame payload boundary.
- The release notes contain unrelated serialization changes (for example Iris, Control Rig, InstancedPropertyBag, and linker bounds); none was treated as a generic SaveGame API removal. The 5.8.1 and 5.8.2 hotfix material checked for exact `SaveGame` terms did not identify a SaveGame API deprecation or replacement. No claim is made that unrelated serialization fixes cannot affect a particular custom payload.

### Unresolved questions / verification gaps

- No custom project was compiled or run under UE 5.8.2. Slot I/O, corrupt-file recovery, async callback ordering, platform cloud conflict behavior, multi-user storage, and console-specific save systems remain untested.
- No old save corpus was migrated. The CoreRedirects rename recommendation is source/config verified, not validated against a real pre-rename SaveGame or a cooked build; value-semantic/type migrations still require fixture files and assertions.
- `LevelStreamingPersistence` was source- and plugin-descriptor checked only. No project enabled the plugin, configured properties, serialized a streamed map, restored before/after `BeginPlay`, or tested runtime actor/destroyed-actor behavior. It remains **experimental**, plugin-dependent, and disabled by default.
- `DoesSaveGameExistWithResult` is explicitly not guaranteed to return every result on every platform; no platform implementation was installed or exercised. Do not promise a universal corrupt-vs-missing distinction.
- The report does not claim the engine’s internal save header guarantees cross-UE-version compatibility. UE 5.8.2 `FSaveGameHeader` records package/engine/custom-version metadata, but game schema compatibility and old-file behavior still require project-owned tests.

## core/sequencer-and-cinematics

**Status:** findings  
**Repository path:** `skills/core/sequencer-and-cinematics/`  
**Files reviewed:** `SKILL.md`; `references/cameras-and-cuts.md`; `references/level-sequence-and-player.md`; `references/movie-render-queue.md`; `references/tracks-and-bindings.md`.

### Verified recommendations

#### SEQ-01 — fix the Movie Render Queue output-directory example

- **Priority:** P1 — copy-paste correctness; `/Game/Renders/` is an Unreal asset path, while MRQ’s `OutputDirectory` is consumed as a filesystem output path. Leaving the example unchanged can direct an agent to an invalid or unintended render location.
- **Location:** `skills/core/sequencer-and-cinematics/references/movie-render-queue.md:98-105`.
- **Finding:** the example assigns `OutSetting->OutputDirectory.Path = TEXT("/Game/Renders/")`. UE 5.8.2’s default basic config uses the format token `{project_dir}/Saved/MovieRenders/`, and the output implementations concatenate `OutputDirectory.Path` with the filename format before writing. Use the project-directory token (or an explicitly absolute filesystem path), not a `/Game` virtual path.
- **Exact proposed replacement:**

```diff
--- a/skills/core/sequencer-and-cinematics/references/movie-render-queue.md
+++ b/skills/core/sequencer-and-cinematics/references/movie-render-queue.md
@@
-OutSetting->OutputDirectory.Path = TEXT("/Game/Renders/");
+// OutputDirectory is a filesystem path. Use MRQ's project-dir token or an absolute path;
+// `/Game/...` is an asset path, not a render-output directory.
+OutSetting->OutputDirectory.Path = TEXT("{project_dir}/Saved/MovieRenders/");
```

- **Practical task benefit:** generated renders land in the intended project output directory and remain portable across machines.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/MovieScene/MovieRenderPipeline/Source/MovieRenderPipelineCore/Private/MoviePipelineBasicConfig.cpp:173-179` initializes `OutputDirectory.Path` to `{project_dir}/Saved/MovieRenders/`; `.../MoviePipelineVideoOutputBase.cpp:29-34,59-63` and `.../MoviePipelineCommandLineEncoder.cpp:97-107` consume that value as the output filesystem path. UE 5.8.2 source.

#### SEQ-02 — correct the runtime-plugin and packaged-build guidance

- **Priority:** P1 — build/runtime correctness; the current text names a module as a plugin and describes an executor-driven packaged workflow without identifying the actual project plugin/module boundary.
- **Locations:** `skills/core/sequencer-and-cinematics/SKILL.md:180-192`; `references/movie-render-queue.md:34-45,71-82,145-151`.
- **Finding:** UE 5.8.2 ships the plugin `MovieRenderPipeline` with runtime modules `MovieRenderPipelineCore` and `MovieRenderPipelineRenderPasses`, plus the editor-only `MovieRenderPipelineEditor` module. `MovieRenderPipelineRenderPasses` is not itself the plugin name. The editor queue subsystem must not be linked from a runtime module. For packaged runtime rendering, keep the runtime modules/plugin in the packaged target and use the runtime pipeline object/API; do not present `MoviePipelinePIEExecutor` or `MovieRenderPipelineEditor` as packaged-game dependencies.
- **Exact proposed replacement:**

```diff
--- a/skills/core/sequencer-and-cinematics/SKILL.md
+++ b/skills/core/sequencer-and-cinematics/SKILL.md
@@
-The queue is managed via editor subsystem (`MoviePipelineQueueSubsystem`) or Python/Blueprint
-scripting; runtime rendering in a packaged build uses `UMoviePipeline` directly.
+The queue is managed via the editor-only `MoviePipelineQueueSubsystem` or editor Python/Blueprint
+scripting. For packaged runtime rendering, enable the **MovieRenderPipeline** project plugin
+and package the runtime modules (`MovieRenderPipelineCore` and, when the selected passes require
+them, `MovieRenderPipelineRenderPasses`); do not link `MovieRenderPipelineEditor` or use the
+editor-only queue subsystem from a Runtime module. Treat packaged rendering as a separate
+runtime path and validate it in the target configuration.
```

```diff
--- a/skills/core/sequencer-and-cinematics/references/movie-render-queue.md
+++ b/skills/core/sequencer-and-cinematics/references/movie-render-queue.md
@@
-## Runtime builds (packaged game)
+## Runtime builds (packaged game)
@@
-1. Enable **Movie Render Queue Runtime** (`MovieRenderPipelineRenderPasses`) in the plugin
-   list with "Loaded by default" and "Enabled in packaged game".
-2. Use `UMoviePipelineInProcessExecutor` (not the editor executor).
-3. Create a `UMoviePipelineQueue` asset at runtime via `NewObject<UMoviePipelineQueue>`.
-4. Call `UMoviePipeline::Initialize` and drive it via the executor.
+1. Enable the **MovieRenderPipeline** project plugin. Its runtime modules are
+   `MovieRenderPipelineCore` and `MovieRenderPipelineRenderPasses`; the editor module is
+   `MovieRenderPipelineEditor` and must stay editor-only.
+2. Keep `MoviePipelineQueueSubsystem`, `MoviePipelinePIEExecutor`, and
+   `MovieRenderPipelineEditor` out of packaged-game code. Build a runtime path around the
+   `UMoviePipeline`/runtime queue APIs and the pass modules required by the chosen output.
+3. Package the plugin and selected render-pass classes in the target, then validate the exact
+   cooked target; plugin enablement alone does not prove every output format or pass is present.
@@
-Official doc: [Movie Render Queue in Runtime Builds](https://dev.epicgames.com/documentation/unreal-engine/movie-render-queue-in-runtime-in-unreal-engine).
+Official doc: [Movie Render Queue in Runtime Builds](https://dev.epicgames.com/documentation/unreal-engine/movie-render-queue-in-runtime-in-unreal-engine?application_version=5.8).
```

- **Practical task benefit:** prevents runtime targets from taking an editor-only dependency and gives agents the real `.uplugin`/module names needed to package MRQ deliberately.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/MovieScene/MovieRenderPipeline/MovieRenderPipeline.uplugin:1-80` declares the plugin and its `MovieRenderPipelineCore`, `MovieRenderPipelineRenderPasses`, and `MovieRenderPipelineEditor` modules with runtime/editor types; `.../Source/MovieRenderPipelineCore/Public/MoviePipelineQueueEngineSubsystem.h:47-104` marks `UMoviePipelineQueueEngineSubsystem` as an engine subsystem and exposes the runtime queue API; `.../Source/MovieRenderPipelineEditor/Public/MoviePipelineQueueSubsystem.h:18-29` is the editor queue subsystem. UE 5.8.2 source. The version-matched [Movie Render Queue in Runtime Builds](https://dev.epicgames.com/documentation/unreal-engine/movie-render-queue-in-runtime-in-unreal-engine?application_version=5.8) page is the matching Epic documentation reference.

#### SEQ-03 — promote Movie Render Graph to production-ready, graph-only feature guidance

- **Priority:** P2 — workflow accuracy; the existing wording calls MRG recommended but omits its UE 5.8 maturity and the fact that new major render features are graph-only.
- **Locations:** `skills/core/sequencer-and-cinematics/references/movie-render-queue.md:107-119`; precise insertion point in `SKILL.md` immediately after the MRQ paragraph at `:182-192`.
- **Finding:** UE 5.8 release notes state that Movie Render Graph enters **Production Ready**, that graph configurations support the major legacy-preset features, and that new features going forward are graph-only. Preserve legacy MRQ compatibility, but distinguish the stable production-ready graph workflow from experimental features that may be named by individual nodes.
- **Exact proposed replacement/addition:**

```diff
--- a/skills/core/sequencer-and-cinematics/references/movie-render-queue.md
+++ b/skills/core/sequencer-and-cinematics/references/movie-render-queue.md
@@
-UE 5.4 introduced **Movie Render Graph** as a node-graph successor to the linear MRQ config.
-In UE 5.8, MRG is the recommended path for new pipelines. MRQ configs still work and are
-auto-converted by the "Transitioning to MRG" workflow. See:
+UE 5.4 introduced **Movie Render Graph** as a node-graph successor to the linear MRQ config.
+In UE 5.8, MRG is **Production Ready** and is the recommended path for new pipelines. Graph
+configurations cover the major legacy-preset features; existing MRQ presets remain supported
+and can be transitioned, but new major render features may be graph-only. Check each named node
+for its own production/experimental status rather than treating the whole graph as experimental.
```

```diff
--- a/skills/core/sequencer-and-cinematics/SKILL.md
+++ b/skills/core/sequencer-and-cinematics/SKILL.md
@@
 Full MRQ setup and scripting: [references/movie-render-queue.md](references/movie-render-queue.md).
+
+In UE 5.8, Movie Render Graph is **Production Ready** and is the preferred authoring path for
+new render pipelines; legacy MRQ presets remain supported. New major render features may be
+graph-only, and individual graph nodes can have separate experimental status.
```

- **Practical task benefit:** agents choose the UE 5.8 production workflow without incorrectly deleting legacy presets or promoting an individual experimental node to stable status.
- **Verified evidence:** Epic [UE 5.8 Release Notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#movierendergraph) lines 1815-1825 state “Movie Render Graph (Production Ready),” major legacy-feature coverage, and graph-only new features. Installed UE 5.8.2 `.../MovieRenderPipelineCore/Public/Graph/MovieGraphConfig.h:20-112` verifies `UMovieGraphConfig` and graph configuration APIs. UE 5.8.2 source.

#### SEQ-04 — remove the unverified historical “custom binding” provenance and anchor dynamic binding claims

- **Priority:** P2 — citation precision; the current reference makes introduction/version claims that were not established by the installed 5.8.2 source, while the source does establish the current editor/runtime split.
- **Locations:** `skills/core/sequencer-and-cinematics/references/tracks-and-bindings.md:105-111,124-129`; `references/level-sequence-and-player.md:126-129`.
- **Finding:** `ULevelSequence::IterateDynamicBindings` is `#if WITH_EDITOR` in UE 5.8.2, while runtime binding resolution is handled through the sequence/player binding APIs. Keep dynamic binding as an editor-authored workflow and avoid claiming that the source alone proves a universal “replaces overrides for fresh code” or “introduced in 5.5” compatibility rule.
- **Exact proposed replacement:**

```diff
--- a/skills/core/sequencer-and-cinematics/references/tracks-and-bindings.md
+++ b/skills/core/sequencer-and-cinematics/references/tracks-and-bindings.md
@@
-## Dynamic Binding (UE 5.4+)
+## Dynamic Binding
@@
-Dynamic Binding (`dynamic-binding-in-sequencer` doc) is a newer mechanism that lets a
-Blueprint subclass of the Director decide *which* object to resolve for each binding,
-rather than using the override table. It replaces the old "Binding Overrides" pattern for
-fresh code. Under the hood it hooks `ULevelSequence::IterateDynamicBindings` (editor-only)
-and a `UClass`-derived resolver at runtime.
+Dynamic Binding lets a Blueprint-authored Director workflow decide which object to resolve for
+a binding rather than relying only on an actor binding-override table. Treat it as an
+editor-authored, project-versioned workflow: `ULevelSequence::IterateDynamicBindings` is
+editor-only in UE 5.8.2, while runtime resolution still goes through the sequence/player
+binding-resolution path. Use `ALevelSequenceActor::SetBinding*` overrides when code needs a
+direct, explicit runtime retargeting API, and verify the chosen workflow in the target build.
@@
- - Spawnables now use the **custom binding system** (`AllowsCustomBindings`) introduced in 5.5;
-  old `FMovieSceneSpawnable`-style data is automatically converted on load.
- - The `FGuid FindBindingFromObject(UObject*, UObject*)` API is deprecated since 5.5; prefer
-  the `SharedPlaybackState` variant or `FindNamedBinding` via tags.
+- `ULevelSequence::FindBindingFromObject(UObject*, UObject*)` is deprecated in UE 5.8.2;
+  prefer the overload taking `SharedPlaybackState` where that API is required, or use the
+  actor’s tag-based binding helpers for explicit runtime retargeting.
+- `AllowsCustomBindings` and the upgraded spawnable/binding data are present in UE 5.8.2;
+  do not turn the current declaration into an unsupported cross-version introduction claim.
```

```diff
--- a/skills/core/sequencer-and-cinematics/references/level-sequence-and-player.md
+++ b/skills/core/sequencer-and-cinematics/references/level-sequence-and-player.md
@@
- - Spawnables now use the **custom binding system** (`AllowsCustomBindings`) introduced in 5.5;
-  old `FMovieSceneSpawnable`-style data is automatically converted on load.
- - The `FGuid FindBindingFromObject(UObject*, UObject*)` API is deprecated since 5.5; prefer
-  the `SharedPlaybackState` variant or `FindNamedBinding` via tags.
+- `FindBindingFromObject(UObject*, UObject*)` is deprecated in the UE 5.8.2 declaration;
+  prefer the `SharedPlaybackState` overload or explicit tag-based binding helpers.
+- The custom-binding/spawnable conversion symbols are present in UE 5.8.2; this audit does not
+  use them as proof of the historical version in which the workflow was introduced.
```

- **Practical task benefit:** avoids editor-only API leakage and unsupported cross-version provenance while retaining both designer-authored dynamic binding and code-driven overrides.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/LevelSequence/Public/LevelSequence.h:45-47,101-110` marks the legacy overload deprecated and `IterateDynamicBindings` editor-only; `.../LevelSequenceActor.h:168-244` verifies `SetBinding`, `SetBindingByTag`, `AddBinding`, and tag lookup. UE 5.8.2 source. Matching Epic pages: [Dynamic Binding](https://dev.epicgames.com/documentation/unreal-engine/dynamic-binding-in-sequencer?application_version=5.8) and [Python Scripting in Sequencer](https://dev.epicgames.com/documentation/unreal-engine/python-scripting-in-sequencer-in-unreal-engine?application_version=5.8).

#### SEQ-05 — make the 5.8.2 Sequencer hotfix protection explicit without promising a workaround

- **Priority:** P2 — practical stability; users of actor-reference tracks should know that UE 5.8.2 contains a fix for off-game-thread binding resolution, while custom track code still needs its own thread-safety review.
- **Precise insertion point:** `skills/core/sequencer-and-cinematics/SKILL.md`, after the binding override section and before `## Cameras & camera cuts` (after current `:143`).
- **Finding:** the 5.8.2 hotfix notes list a fix for a crash caused by Sequencer resolving actor-reference track bindings off the game thread. The skill currently has no hotfix note and should not instruct agents to add an ad hoc thread hop as if that were the engine contract.
- **Exact proposed addition:**

```diff
--- a/skills/core/sequencer-and-cinematics/SKILL.md
+++ b/skills/core/sequencer-and-cinematics/SKILL.md
@@
 Full binding and track internals: [references/tracks-and-bindings.md](references/tracks-and-bindings.md).
+
+**UE 5.8.2 stability note:** the 5.8.2 hotfix includes a Sequencer fix for actor-reference track
+bindings being resolved off the game thread. Use the 5.8.2 engine when relying on that fix, and
+keep custom track/binding resolution on the thread required by the API; this note is not a
+general license to move arbitrary evaluation work between threads.
 
 ## Cameras & camera cuts
```

- **Practical task benefit:** directs teams to the hotfix containing the relevant crash fix and avoids fragile caller-side workarounds that could introduce new races.
- **Verified evidence:** Epic staff [5.8.2 Hotfix Released](https://forums.unrealengine.com/t/5-8-2-hotfix-released/2746335) lines 71-89 explicitly lists “Sequencer: Fixed a crash caused by Sequencer resolving actor reference track bindings off the game thread.” Installed UE 5.8.2 `.../LevelSequence/Public/LevelSequencePlayer.h:128-141` verifies the binding-resolution/evaluation virtuals in the pinned source. This is a hotfix-note-backed stability recommendation, not a runtime reproduction.

### No-change checks

- `ULevelSequence`, `ALevelSequenceActor`, `ULevelSequencePlayer`, `CreateLevelSequencePlayer`, `GetSequencePlayer`, `OnFinished`, `OnCameraCut`, `SetBindingByTag`, `FindNamedBinding`, `FMovieSceneSequencePlaybackSettings`, `PlayLooping`, `StopAtCurrentTime`, `SetPlaybackPosition`, completion-mode override, Cine Camera interpolation fields, and Director-instance concepts remain present in the installed UE 5.8.2 declarations. The normal runtime/editor distinction remains valid.
- The camera examples’ `SetCurrentFocalLength`, `SetCurrentAperture`, `SetFilmback`, and `FocusSettings` concepts match `CineCameraComponent.h`; the camera settings and cut delegate remain supported. No 5.8 release-note or hotfix item required a broad camera-cut API rewrite.
- The 5.8 release notes’ production-ready MRG and Sequencer editor improvements are covered above; animation-mixer/direct-mesh-control items are not promoted here because they are scoped to other skills or marked experimental in the release notes.

### Unresolved questions / verification gaps

- No Level Sequence or Cine Camera asset was opened, compiled, played in PIE, tested with missing/streamed/spawnable bindings, or rendered under UE 5.8.2. Binding precedence, camera restore behavior, Director event dispatch, network synchronization, and completion-state behavior remain source/documentation-level only.
- No packaged runtime MRQ build was cooked or executed. The runtime recommendation is plugin/source/documentation grounded; actual pass availability, codec support, output permissions, memory use, and target-platform behavior still require a project test.
- No custom Sequencer track, dynamic-binding Director Blueprint, Animation Mixer sequence, or graph render preset was authored. Individual MRG node maturity and vendor/codec availability remain project-dependent.
- The 5.8.1 hotfix material was checked for matching Sequencer/MRQ terms without identifying a separate API migration that supersedes the 5.8.2 items above. This does not prove the absence of unrelated fixes outside the searched terms.

## core/subsystems

**Status:** findings  
**Repository path:** `skills/core/subsystems/`  
**Files reviewed:** `SKILL.md`; `references/choosing-a-subsystem.md`; `references/lifecycle-and-access.md`; `references/subsystem-types.md`.

### Verified recommendations

#### SUB-01 — replace the removed streaming callback with the concrete 5.8.2 interface

- **Priority:** P1 — compile correctness; the references mention the old callback’s removal but do not show the include, inheritance, or method name an agent must use.
- **Locations:** `skills/core/subsystems/references/lifecycle-and-access.md:141-149`; `references/subsystem-types.md:191-198`; precise insertion point in `SKILL.md` after the `UWorldSubsystem` lifecycle/gotchas material.
- **Finding:** UE 5.8.2 has no `UWorldSubsystem::UpdateStreamingState` declaration in the inspected subsystem API. Streaming-aware world subsystems implement `IStreamingWorldSubsystemInterface` and override `OnUpdateStreamingState()` (and, if needed, `OnFlushStreaming()`). Turn the version note into a compile-oriented migration rather than leaving “use the interface” as an unresolved name.
- **Exact proposed replacement/addition:**

```diff
--- a/skills/core/subsystems/references/lifecycle-and-access.md
+++ b/skills/core/subsystems/references/lifecycle-and-access.md
@@
- - `UWorldSubsystem::UpdateStreamingState` was deprecated in UE 5.5 and removed in 5.8;
-  use `IStreamingWorldSubsystemInterface` for streaming callbacks.
+- `UWorldSubsystem::UpdateStreamingState` is not present in UE 5.8.2. For a world subsystem
+  that needs streaming notifications, include `Streaming/StreamingWorldSubsystemInterface.h`,
+  inherit `IStreamingWorldSubsystemInterface`, and override `OnUpdateStreamingState()` (and
+  `OnFlushStreaming()` when flush notifications are required):
+
+  ```cpp
+  #include "Streaming/StreamingWorldSubsystemInterface.h"
+
+  UCLASS()
+  class UMyWorldSubsystem final
+      : public UWorldSubsystem, public IStreamingWorldSubsystemInterface
+  {
+      GENERATED_BODY()
+      void OnUpdateStreamingState() override;
+  };
+  ```
@@
--- a/skills/core/subsystems/references/subsystem-types.md
+++ b/skills/core/subsystems/references/subsystem-types.md
@@
- - `UWorldSubsystem::UpdateStreamingState` was deprecated in UE 5.5 and removed in 5.8.
-  Implement `IStreamingWorldSubsystemInterface` instead if streaming state callbacks are needed.
+- `UWorldSubsystem::UpdateStreamingState` is absent in UE 5.8.2. Implement
+  `IStreamingWorldSubsystemInterface::OnUpdateStreamingState()` instead; the interface is
+  declared in `Engine/Public/Streaming/StreamingWorldSubsystemInterface.h`.
```

- **Practical task benefit:** removes an ambiguous deprecation note and gives agents a buildable UE 5.8.2 replacement for streaming notifications.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/Streaming/StreamingWorldSubsystemInterface.h:8-23` declares `IStreamingWorldSubsystemInterface::OnUpdateStreamingState` and `OnFlushStreaming`; `.../Engine/Public/Subsystems/WorldSubsystem.h:15-66` contains the current `UWorldSubsystem` API and no `UpdateStreamingState`. `ULevelInstanceSubsystem` and `UWorldPartitionSubsystem` implement the interface at `.../Engine/Public/LevelInstance/LevelInstanceSubsystem.h:55-75` and `.../Engine/Public/WorldPartition/WorldPartitionSubsystem.h:62-82`. UE 5.8.2 source.

#### SUB-02 — fix the server-only `ShouldCreateSubsystem` example

- **Priority:** P1 — behavior correctness; the example’s comment says “servers and standalone,” but `!IsRunningDedicatedServer()` returns true on ordinary clients, and the `IsServer(nullptr)` fallback is not a reliable world-context test.
- **Location:** `skills/core/subsystems/references/choosing-a-subsystem.md:112-126`.
- **Finding:** keep CDO-safe, cheap gating, but express the intended policy directly. If the subsystem is for non-dedicated processes, use only `!IsRunningDedicatedServer()`. If it is server-only, use a valid outer/world context or a clearly scoped dedicated-server predicate; do not imply that a null world context is a universal server check.
- **Exact proposed replacement:**

```diff
--- a/skills/core/subsystems/references/choosing-a-subsystem.md
+++ b/skills/core/subsystems/references/choosing-a-subsystem.md
@@
-bool UMySubsystem::ShouldCreateSubsystem(UObject* Outer) const
-{
-    // Only on servers and standalone:
-    if (!Super::ShouldCreateSubsystem(Outer)) { return false; }
-    return !IsRunningDedicatedServer() || UKismetSystemLibrary::IsServer(/*World*/nullptr);
-}
+bool UMySubsystem::ShouldCreateSubsystem(UObject* Outer) const
+{
+    if (!Super::ShouldCreateSubsystem(Outer)) { return false; }
+    // This policy means “not on a dedicated server”; it still creates on clients/listen servers.
+    return !IsRunningDedicatedServer();
+}
@@
-`ShouldCreateSubsystem` is called on the CDO with the **outer object** (the owning
-`UGameInstance`, `UWorld`, etc.) as the argument. You can inspect the outer to make decisions,
-but you cannot call `GetSubsystem` on it during this call — other subsystems may not yet be
-created.
+`ShouldCreateSubsystem` is called on the CDO with the **outer object** (the owning
+`UGameInstance`, `UWorld`, etc.) as the argument. You can inspect the outer to make decisions,
+but you cannot call `GetSubsystem` on it during this call — other subsystems may not yet be
+created. Keep the predicate cheap and make the server/client policy explicit; do not use a
+null world-context object as a substitute for a valid server check.
```

- **Practical task benefit:** prevents a subsystem intended to be server-only from silently being instantiated on clients and removes a misleading null-context helper call.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/Subsystems/Subsystem.h:49-62` documents that `ShouldCreateSubsystem` runs on the CDO before instances exist; `.../SubsystemCollection.h:31-45` limits dependency initialization to the same collection. UE 5.8.2 source. The recommendation is a correction to the example’s logic, not an engine API migration.

#### SUB-03 — do not promise automatic Blueprint/Python exposure for every subsystem member

- **Priority:** P2 — authoring clarity; the opening claim can lead agents to expect arbitrary methods or properties to appear in Blueprint/Python without reflection annotations.
- **Locations:** `skills/core/subsystems/SKILL.md:16-19`; `SKILL.md:153-158`; `references/lifecycle-and-access.md:112-129`.
- **Finding:** subsystem construction/lifetime is automatic, but member exposure still depends on Unreal reflection and the relevant host API. The later Blueprint section already says to use `UFUNCTION(BlueprintCallable)`; align the opening claim with that constraint.
- **Exact proposed replacement:**

```diff
--- a/skills/core/subsystems/SKILL.md
+++ b/skills/core/subsystems/SKILL.md
@@
-The engine creates it
-automatically when the owning object is created and destroys it when the owner is torn down —
-no manual instancing, no GC juggling, and Blueprint/Python exposure comes for free.
+The engine creates it
+automatically when the owning object is created and destroys it when the owner is torn down —
+no manual instancing and no manual GC ownership. Access to the subsystem is automatic, but
+Blueprint/Python exposure still requires the appropriate reflected class/function/property
+annotations and host-specific getter (for example, `UFUNCTION(BlueprintCallable)` for a
+Blueprint-callable operation).
```

- **Practical task benefit:** avoids non-reflected API examples that compile as C++ but are invisible to Blueprint or editor Python.
- **Verified evidence:** installed UE 5.8.2 `.../Engine/Public/Subsystems/Subsystem.h:12-29` documents auto-instanced subsystem lifetimes; `.../Engine/Public/Subsystems/SubsystemBlueprintLibrary.h:21-45` exposes typed Blueprint getter functions, while the reference’s own `lifecycle-and-access.md:112-129` correctly requires reflected functions for callable operations. UE 5.8.2 source.

### No-change checks

- `USubsystem`, `UDynamicSubsystem`, `UEngineSubsystem`, `UGameInstanceSubsystem`, `UWorldSubsystem`, `UTickableWorldSubsystem`, and `ULocalPlayerSubsystem` remain the applicable UE 5.8.2 base classes and lifetime choices. `Initialize`/`Deinitialize`, `ShouldCreateSubsystem`, `InitializeDependency`, `PostInitialize`, `OnWorldBeginPlay`, `PlayerControllerChanged`, and `GetStatId` guidance matches the inspected declarations.
- Same-collection dependency ordering, reverse deinitialization, null-safe accessors, `GetSubsystemChecked`, local-player split-screen scope, non-replication, and the distinction between a subsystem, manager actor, component, and replicated actor remain valid. No 5.8 release-note or 5.8.1/5.8.2 hotfix item justified a broad subsystem rewrite.
- `UEditorSubsystem` remains editor-only, and `MoviePipelineQueueSubsystem`/other editor subsystems are not treated as runtime classes. The 5.8 release notes and hotfix notes were checked for subsystem and streaming terms; the concrete streaming callback correction above is the only scoped compile-facing migration found.

### Unresolved questions / verification gaps

- No custom subsystem was compiled, instantiated, run through PIE, streamed across world travel, or tested in a dedicated server/listen-server/client matrix under UE 5.8.2. Lifetime timing, world-type filtering, plugin load/unload, and cross-scope coordination remain source-level checks.
- The report does not claim that every subsystem class is available in every target; module/plugin loading, target allow-lists, and `WITH_EDITOR` gates still require the project’s build configuration.
- The exact order of plugin module shutdown relative to dynamic subsystem deinitialization was not runtime-tested; keep cleanup idempotent and avoid relying on an unverified shutdown-order assumption.

## core/timers-and-async

**Status:** findings  
**Repository path:** `skills/core/timers-and-async/`  
**Files reviewed:** `SKILL.md`; `references/async-and-tasks.md`; `references/threads-and-runnables.md`; `references/tickers-and-latent.md`; `references/timer-manager.md`.

### Verified recommendations

#### TMR-01 — correct `SetTimerForNextTick` cancellation guidance

- **Priority:** P1 — API correctness; the current example says no handle is returned and the callback cannot be cancelled, but UE 5.8.2 returns an `FTimerHandle` for every `SetTimerForNextTick` overload.
- **Locations:** `skills/core/timers-and-async/SKILL.md:83-88`; precise insertion point in `SKILL.md` gotchas after the current `:392` statement; `references/timer-manager.md` should add the same distinction near `:28-49` or `:50-65`.
- **Finding:** object, delegate, and `TFunction` overloads all return the handle from `InternalSetTimerForNextTick`. Store it when cancellation or diagnostics matter, and clear it from the game thread before the next tick. A callback bound through a UObject delegate is also invalidated with the UObject; a raw-pointer lambda still needs lifetime-safe cleanup.
- **Exact proposed replacement/addition:**

```diff
--- a/skills/core/timers-and-async/SKILL.md
+++ b/skills/core/timers-and-async/SKILL.md
@@
-// Defer one frame — no handle returned; cannot be cancelled:
-GetWorldTimerManager().SetTimerForNextTick(this, &AMyActor::AfterSpawn);
+// Defer one frame. UE 5.8.2 returns a handle, so it can be cleared before it fires.
+FTimerHandle NextTickHandle =
+    GetWorldTimerManager().SetTimerForNextTick(this, &AMyActor::AfterSpawn);
+// Cancel from the game thread if the actor may be torn down first:
+GetWorldTimerManager().ClearTimer(NextTickHandle);
@@
-- **`SetTimerForNextTick` has no handle** — it cannot be cancelled; do not call it if the
-  actor might be destroyed before the next frame.
+- **`SetTimerForNextTick` still has a lifetime window** — UE 5.8.2 returns an
+  `FTimerHandle`, so clear that handle from the game thread when cancellation is needed.
+  UObject-bound delegates are invalidated with their object; raw-pointer lambdas still need
+  explicit lifetime-safe cleanup.
```

```diff
--- a/skills/core/timers-and-async/references/timer-manager.md
+++ b/skills/core/timers-and-async/references/timer-manager.md
@@
 ## SetTimer overloads
@@
 All `SetTimer` overloads resolve to `InternalSetTimer`, which accepts an
 `FTimerUnifiedDelegate`. The delegate is a `TVariant` over three forms (verified:
 `TimerManager.h` line 25):
+
+`SetTimerForNextTick` also returns an `FTimerHandle` in UE 5.8.2. Store and clear that handle
+when a one-frame deferral must be cancelled before execution.
```

- **Practical task benefit:** prevents one-frame callbacks from running after a state transition when the caller could have cancelled them, while preserving the UObject delegate’s automatic invalidation behavior.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Public/TimerManager.h:242-273` returns `FTimerHandle` from native, delegate, dynamic-delegate, and `TFunction` overloads; `:275-288` documents `ClearTimer` invalidating the handle. UE 5.8.2 source.

#### TMR-02 — distinguish world time dilation from actor custom time dilation and state overdue-fire behavior

- **Priority:** P1 — gameplay timing correctness; the current text promises per-actor dilation and says timers never fire more than once per frame, both of which can produce incorrect cooldown/regen behavior under hitching or custom actor dilation.
- **Locations:** `skills/core/timers-and-async/SKILL.md:120-126`; `references/timer-manager.md:67-80`; `SKILL.md:102-103` is otherwise correct for non-positive rates.
- **Finding:** the world timer manager advances from its `UWorld::Tick` delta, so global/world pause and dilation affect it. An actor’s `CustomTimeDilation` is applied in actor tick execution, not to the shared world timer manager. UE 5.8.2’s `FTimerManager::Tick` computes a looping timer’s `CallCount` from elapsed internal time and can invoke an overdue loop multiple times in one world tick unless `bMaxOncePerFrame` is set.
- **Exact proposed replacement:**

```diff
--- a/skills/core/timers-and-async/SKILL.md
+++ b/skills/core/timers-and-async/SKILL.md
@@
-Timers advance on **world time**, so they automatically respect `WorldSettings` time
-dilation, pausing (`SetPause`), and slow-motion. They do **not** fire more than once per
-game frame even if the accumulated delta exceeds the rate (modulo `bMaxOncePerFrame` on
-`FTimerData`). The game-thread-only note in the engine docs is accurate: `FTimerManager`
-is not thread-safe; never set or clear timers from a background thread.
+Timers advance from the world timer manager's tick delta, so global/world time dilation and
+world pausing affect them. An actor's `CustomTimeDilation` changes that actor's tick delta; it
+does not automatically change the shared world timer's cadence. A looping timer can fire more
+than once during one world tick when it is overdue; set `FTimerManagerTimerParameters::bMaxOncePerFrame`
+to `true` when catch-up calls are not wanted. `FTimerManager` is game-thread-only; never set or
+clear timers from a background thread.
```

```diff
--- a/skills/core/timers-and-async/references/timer-manager.md
+++ b/skills/core/timers-and-async/references/timer-manager.md
@@
-Because `UWorld::Tick` already applies time dilation when computing
-`DeltaTime`, timers automatically slow down / speed up with global or per-actor time
-dilation — no extra code needed.
+Because the timer manager consumes the world tick delta, timers follow global/world time
+dilation and world pause. Actor `CustomTimeDilation` is applied to the actor's tick and does
+not automatically rescale the shared world timer manager; model actor-specific timing in an
+actor tick or with an explicit rate if that is required.
@@
-`bMaxOncePerFrame` prevents the timer from firing multiple times in a single large frame
-(relevant for timers with very short rates under hitched frames).
+By default, an overdue looping timer can execute its delegate multiple times in one large
+world tick to catch up. `bMaxOncePerFrame` prevents those extra same-frame catch-up calls,
+which is relevant for short rates under hitched frames.
```

- **Practical task benefit:** avoids cooldowns silently catching up several times after a hitch and avoids assuming that a world timer honors an actor-specific time scale.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/TimerManager.cpp:1212-1237` computes looping `CallCount` from overdue internal time; `:1247-1309` executes the loop and breaks on `bMaxOncePerFrame`; `:1344-1349` reschedules by `CallCount * Rate`. `.../Engine/Classes/GameFramework/Actor.h:792-798` documents `CustomTimeDilation` as applying to that actor’s tick delta. UE 5.8.2 source.

#### TMR-03 — make the single-threaded FRunnable fallback honest

- **Priority:** P1 — platform correctness; the reference says `Init`, `Run`, and `Exit` will still be called on the game thread when multithreading is disabled, but the UE 5.8.2 runnable contract says a runnable without a `FSingleThreadRunnable` interface will not be ticked in that mode.
- **Location:** `skills/core/timers-and-async/references/threads-and-runnables.md:140-147`.
- **Finding:** `FRunnable::GetSingleThreadInterface()` returns `nullptr` by default and the declaration explicitly says the runnable will not be ticked when multithreading is unavailable. The reference should require an implemented single-thread interface for that fallback, or tell the caller to handle a null `FRunnableThread::Create` result itself; it should not promise a game-thread lifecycle automatically.
- **Exact proposed replacement:**

```diff
--- a/skills/core/timers-and-async/references/threads-and-runnables.md
+++ b/skills/core/timers-and-async/references/threads-and-runnables.md
@@
-On platforms where `FPlatformProcess::SupportsMultithreading()` returns `false` (some
-consoles, single-threaded cooking), `FRunnableThread::Create` returns `nullptr`. The engine
-will still call `Init`, `Run`, and `Exit` on the game thread when `FRunnableThread::Tick` is driven
-(via `FSingleThreadRunnable`). Override `GetSingleThreadInterface()` on your `FRunnable` if you
-need single-thread fallback behavior (verified: `Runnable.h`:69).
+On platforms where `FPlatformProcess::SupportsMultithreading()` returns `false`, do not assume
+that a null `FRunnableThread::Create` result runs the `FRunnable` lifecycle automatically.
+`FRunnable::GetSingleThreadInterface()` returns `nullptr` by default, and UE 5.8.2 states that
+such a runnable is not ticked in single-threaded mode. Implement and return a valid
+`FSingleThreadRunnable` when that fallback is required, or handle the null thread by running a
+separate synchronous path / skipping the service.
```

- **Practical task benefit:** prevents a platform build from silently dropping required worker work or assuming that a dedicated-thread loop became a safe synchronous loop.
- **Verified evidence:** installed UE 5.8.2 `C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Core/Public/HAL/Runnable.h:23-72` documents `Init`/`Run`/`Stop`/`Exit` and explicitly states that a null `GetSingleThreadInterface()` means the runnable will not be ticked without multithreading; `.../HAL/RunnableThread.h:36-50` documents `Create` returning `nullptr` on failure and `:76-89` documents graceful `Kill`. UE 5.8.2 source.

### No-change checks

- `FTimerManager`, `FTimerHandle`, timer parameter overloads, object-bound delegate invalidation, `ClearTimer`, `ClearAllTimersForObject`, `FTSTicker`, `FTSTickerObjectBase`, latent actions, `Async`, `AsyncTask`, `TFuture`, `FNonAbandonableTask`, `FAutoDeleteAsyncTask`, `FAsyncTask`, `UE::Tasks`, `FPipe`, `FTaskEvent`, `FRunnable`, `FRunnableThread`, and `UBlueprintAsyncActionBase` remain present in UE 5.8.2 with the documented module boundaries.
- Game-thread UObject access, weak-pointer revalidation after returning to the game thread, explicit task/thread shutdown, ticker removal, timer cleanup, and the preference for timers over per-frame work remain valid. The 5.8 release notes and 5.8.1/5.8.2 hotfix notes were checked for timer, ticker, async, task, and runnable terms; no separate scoped API migration was found beyond the corrections above.

### Unresolved questions / verification gaps

- No custom timer, ticker, latent node, task graph, Tasks System, or runnable was compiled or exercised in PIE, a cooked build, a single-threaded target, or a shutdown race under UE 5.8.2. Thread scheduling, cancellation timing, timer catch-up, and teardown behavior remain source-level checks.
- No runtime benchmark was run; the report does not claim that replacing `Tick` with a timer or task improves a particular workload.
- The exact historical version of Tasks busy-wait policy remains unresolved; only the current 5.8.2 declarations and absence of a matching searched release-note entry are verified.
- **TMR-04 withdrawn pending evidence (P2):** locations `SKILL.md:371–374` and `references/async-and-tasks.md:210–215`. Residual terminology or `ETaskFlags::DoNotRunInsideBusyWait` in `Engine/Source/Runtime/Core/Public/Tasks/TaskPrivate.h:88–92` does not demonstrate that a formerly public BusyWait API still exists. No replacement text is recommended on that basis. Verify the exact removed/deprecated symbols and their historical release notes before changing the migration statement; current declarations alone cannot establish introduction/removal dates.

## core/umg-and-slate

**Status:** findings; source/documentation verified, not compiled or runtime-tested.  
**Repository path:** `skills/core/umg-and-slate/`  
**Files reviewed:** `SKILL.md`; `references/architecture-and-authoring.md`; `references/common-widgets-and-layout.md`; `references/performance-and-best-practices.md`; `references/slate-layer.md`; `references/userwidget-and-binding.md`; `references/widget-component-and-input.md` (all read in full).

### Verified recommendations

#### UMG-01 — use the real controller input-mode API

**Priority:** P1. Fixes copy-paste compile failures and avoids assuming cursor/click configuration changes atomically with the input mode. **Locations:** `references/widget-component-and-input.md:105-121,151-152`; main skill `:235-236` should distinguish Blueprint library functions from controller methods.

```diff
--- a/skills/core/umg-and-slate/references/widget-component-and-input.md
+++ b/skills/core/umg-and-slate/references/widget-component-and-input.md
@@
-PlayerController->SetInputModeUIOnly(Mode);
+PlayerController->SetInputMode(Mode);
@@
-PlayerController->SetInputModeGameOnly();
+PlayerController->SetInputMode(FInputModeGameOnly{});
@@
-Avoid directly setting these booleans in production — prefer the `SetInputMode*` structs
-which manage them atomically.
+Set the input mode with `APlayerController::SetInputMode` and configure cursor visibility
+and actor/component click/hover events separately. Input-mode structs do not atomically
+configure those flags.
```

Replace the table's three Function cells with `SetInputMode(FInputModeUIOnly)`, `SetInputMode(FInputModeGameAndUI)`, and `SetInputMode(FInputModeGameOnly)`. Replace its Mouse cursor cells with `Configure separately; lock behavior is configurable`. Replace the main skill's two input-mode lines with: “For menus, call `APlayerController::SetInputMode` with an `FInputModeUIOnly`, `FInputModeGameAndUI`, or `FInputModeGameOnly` value; configure cursor visibility separately. Blueprint input-mode helpers belong to `UWidgetBlueprintLibrary`.”

**Evidence:** UE 5.8.2 `Engine/Source/Runtime/Engine/Classes/GameFramework/PlayerController.h:1648-1649`, `APlayerController::SetInputMode(const FInputModeDataBase&)`; `:525-527`, `bShowMouseCursor`/`SetShowMouseCursor`.

#### UMG-02 — repair the layout example and fictitious widget hierarchy

**Priority:** P1 for constructor; P2 for hierarchy. **Location:** `references/common-widgets-and-layout.md:10-17,91`. Enables compilable dynamic layouts and correct class navigation.

```diff
--- a/skills/core/umg-and-slate/references/common-widgets-and-layout.md
+++ b/skills/core/umg-and-slate/references/common-widgets-and-layout.md
@@
-    Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill, 1.f));
+    Slot->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); // default fill weight is 1
```

Replace the hierarchy block with this exact text:

```text
UVisual
  UWidget
    UPanelWidget
      UContentWidget — single-child panels such as Border and Button
    UTextLayoutWidget
    UImage, USlider, UProgressBar — direct UWidget subclasses
```

**Evidence:** UE 5.8.2 `Engine/Source/Runtime/UMG/Public/Components/SlateWrapperTypes.h:155-177`, `FSlateChildSize` has default and single-size-rule constructors, not the illustrated two-argument constructor; `Components/ContentWidget.h:12`, `UContentWidget : UPanelWidget`; `Components/Image.h:30`, `UImage : UWidget`; `Components/ProgressBar.h:21`, `UProgressBar : UWidget`. `ULeafWidget` is not the UMG counterpart of Slate's `SLeafWidget`.

#### UMG-03 — notify derived health when either input changes

**Priority:** P1. **Location:** `references/architecture-and-authoring.md:102`. Fixes stale health percentages when a max-health upgrade changes the denominator.

```diff
--- a/skills/core/umg-and-slate/references/architecture-and-authoring.md
+++ b/skills/core/umg-and-slate/references/architecture-and-authoring.md
@@
-    void SetMaxHealth(float Value) { UE_MVVM_SET_PROPERTY_VALUE(MaxHealth, Value); }
+    void SetMaxHealth(float Value)
+    {
+        if (UE_MVVM_SET_PROPERTY_VALUE(MaxHealth, Value))
+        {
+            UE_MVVM_BROADCAST_FIELD_VALUE_CHANGED(GetHealthPercent);
+        }
+    }
```

**Evidence:** UE 5.8.2 `Engine/Plugins/Runtime/ModelViewViewModel/Source/ModelViewViewModel/Public/MVVMViewModelBase.h:16-21,79-90`, macros and `SetPropertyValue` notify the specified field, not arbitrary derived functions. [UE 5.8 Viewmodel documentation](https://dev.epicgames.com/documentation/unreal-engine/umg-viewmodel-for-unreal-engine?application_version=5.8), “Use a FieldNotify Variable to Trigger Other FieldNotifies” and C++ manual broadcasts.

#### UMG-04 — correct lifecycle and GC absolutes, once rather than in duplicate

**Priority:** P1. **Locations:** `SKILL.md:48-50,191-192,324-325`; `references/userwidget-and-binding.md:23-31`. Avoids accidentally skipping runtime cosmetic initialization and misdiagnosing widget lifetime.

Replace the main lifecycle table's `NativePreConstruct` row with:

```text
| `NativePreConstruct()` | Before Slate construction in the designer and at runtime. | Cosmetic setup using locally owned data; use `IsDesignTime()` to distinguish preview behavior. |
```

Replace reference lifecycle steps 4–5 with:

```text
4. `NativePreConstruct()` runs for designer previews and at runtime. Restrict it to cosmetic
   setup using locally owned data; use `IsDesignTime()` rather than assuming editor-only execution.
5. `NativeConstruct()` follows construction of the underlying Slate widget, including nested
   widgets. It is not exclusively an AddToViewport event and can run again for the same UObject.
```

Replace the main skill's `NativeConstruct` table “When” cell with `After the underlying Slate widget is constructed; may repeat on the same UObject.` Replace `NativeDestruct`'s cell with `When the underlying Slate widget is torn down; not UObject destruction.` Replace the main skill's ownership bullet at 191–192 with:

```text
- Keep a `UPROPERTY()` reference when your UObject must retain a widget independently of its
  presentation. A live `SObjectWidget` also participates in GC; absence of your own property
  does not mean an attached widget is immediately collected. `RemoveFromParent` is not destruction.
```

Delete the duplicate “Widget not in a UPROPERTY” gotcha at 324–325. In the reference, replace step 7's “removed from the viewport” timing with “underlying Slate widget is torn down”.

**Evidence:** UE 5.8.2 `Engine/Source/Runtime/UMG/Public/Blueprint/UserWidget.h:510-530`, `PreConstruct`/`Construct` contract; `Private/UserWidget.cpp:1858-1882`, `NativePreConstruct` forwards `IsDesignTime()`; `Public/Slate/SObjectWidget.h:25-30,48-50`, `SObjectWidget : FGCObject`, `AddReferencedObjects`.

#### UMG-05 — replace boilerplate with relevant 5.8 native capabilities

**Priority:** P2. **Insertion points:** after the UTextBlock paragraph in `references/common-widgets-and-layout.md:47`; after CommonUI practical rules in `references/architecture-and-authoring.md:51`. Exact additions:

```text
UE 5.8 adds `UTextBlock::SetFontSize(float)` and `GetFontSize()`, expressed in the project's
Font Resolution DPI. Use them for size-only changes instead of copying and reapplying an
entire `FSlateFontInfo`.
```

```text
For Blueprint-authored CommonUI actions, UE 5.8 exposes `RegisterUIAction` and
`RegisterUIActionsFromMappingContext` on `UCommonUserWidget`, with `RemoveUIAction` and
`RemoveAllUIActionBinding` for cleanup. These helpers target UI Enhanced Input actions;
configure the required CommonUI mapping-context metadata rather than adding a custom C++
wrapper just to register an action.
```

**Evidence:** [UE 5.8 release notes, UI](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8#ui-2); matching source `Engine/Source/Runtime/UMG/Public/Components/TextBlock.h:218-230`, `SetFontSize`/`GetFontSize`; `Engine/Plugins/Runtime/CommonUI/Source/CommonUI/Public/CommonUserWidget.h:65-80`, named registration/removal functions. These improve routine UI authoring, not a mandate to migrate an existing simple HUD.

#### UMG-06 — preserve feature maturity and validate notifications, not just compilation

**Priority:** P2. **Locations:** `SKILL.md:352-354`; reference `architecture-and-authoring.md:126-128,193-198`. Replace the main version bullets with:

```text
- CommonUI becomes Production-Ready in UE 5.8; use it when activatable screens and
  multiplatform input routing justify it. A small push-updated UMG HUD need not adopt it.
- UMG Viewmodel remains Beta in UE 5.8; validate binding and lifecycle behavior before shipping.
  A one-way binding without FieldNotify now produces an informational notice rather than a
  compile error, so successful compilation alone does not establish that updates propagate.
- UMG ToolSet is Experimental in UE 5.8, not a default replacement for normal UMG authoring.
```

In `architecture-and-authoring.md`, replace the “solid”/“rough edges” sentence at 127–128 with `The plugin is Beta in UE 5.8; validate notifications and lifecycle in the target build before shipping.` Replace the “CommonUI activatable containers stable since 5.0” version bullet with `CommonUI is Production-Ready in UE 5.8. Lyra's layer-stack architecture is a sample pattern, not a prerequisite for a simple HUD.`

**Evidence:** UE 5.8 release notes UI New entries explicitly promote CommonUI, label UMG ToolSet Experimental, and change the FieldNotify compiler diagnostic. The version-matched [Viewmodel page](https://dev.epicgames.com/documentation/unreal-engine/umg-viewmodel-for-unreal-engine?application_version=5.8) explicitly labels it Beta. The 5.8.2 hotfix fixes a UMG Toolset rename crash; that does not promote its maturity.

#### UMG-07 — prune duplicated performance recipes and unsupported numerical promises

**Priority:** P2. **Locations:** `SKILL.md:213-230`; `references/performance-and-best-practices.md:172-173,251-252`. Keep the detailed constraints in the reference, with this exact replacement for the main summary bullets:

```text
- Push state changes through setters/delegates; use Tick/OnPaint only for work that actually
  needs frame updates. Pull initial state when binding.
- Prefer simple flow layouts; avoid nested Canvas Panels in repeated entries. Choose
  Hidden or Collapsed according to whether the layout must preserve the widget's space.
- For large lists, use native virtualized entries. Measure invalidation before adding
  retainer render targets; preserve pool cleanup and delegate-lifetime rules.
- Use the linked performance reference for layout, caching, animation, and profiling details.
```

Replace the `FText` timing bullet in the reference with `Format text when its value changes; measure text-formatting cost on the target build rather than relying on a universal per-call timing.` Replace its retainer version bullet with `Avoid deprecated direct retainer-property access. Use the exposed APIs; SetRenderingPhase changes phase scheduling at runtime, while mode initialization has its own construction-time contract.` Also replace `:66` with `Rendering modes have construction-time initialization constraints; phase scheduling can be changed with SetRenderingPhase.`

**Evidence:** [UE 5.8 optimization guidelines](https://dev.epicgames.com/documentation/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine?application_version=5.8) says use Tick/OnPaint sparingly, describes relative rather than universal measured CPU costs, and recommends event updates/simple layouts. UE 5.8.2 `Engine/Source/Runtime/UMG/Public/Components/RetainerBox.h:79-80`, `URetainerBox::SetRenderingPhase` is BlueprintCallable. Existing reference already owns the fuller layout constraints; repeating them in the main skill adds maintenance rather than capability.

### Unresolved questions / verification gaps

- No UMG example was compiled or tested in a live/cooked project. CommonUI integration, split-screen, focus transitions, animation handles, and widget-pool shutdown still need project-level execution tests.
- `references/widget-component-and-input.md:22` says Screen space both projects the widget and ignores its 3D position; that is internally inconsistent. Verify the screen-layer projection implementation before adopting either interpretation; do not use that sentence as authoritative placement guidance.
- Some other absolute claims (automatic native-tick opt-in, viewport persistence across travel, fixed list-size thresholds, and exact Slate animation invalidation cost) need narrower implementation/target checks. They are not endorsed by this report's no-change coverage.
- Checked the UE 5.8 UI release/upgrade/deprecation entries and the 5.8.2 SlateIM/UMG Toolset hotfix items. No reason was established to replace stable UMG with experimental SlateIM/Toolset; these additions are limited to the skill's existing UI authoring tasks.

## ultra-dynamic-sky/uds-cinematics-rendering

**Status:** findings; vendor 9.5 documentation verified, installed package integration partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-CIN-01 — P1, separate vendor compatibility mode from engine Path Tracer capability.** Locations: `skills/ultra-dynamic-sky/uds-cinematics-rendering/SKILL.md:24,106-120,180`. Replace the Path Tracer section body with this exact text:

```text
UDS 9.5 documents `Adjust for Path Tracer` and `Render Height Fog In Path Tracer Using Post
Process` as its compatibility/background-rendering path. Start from the vendor recipe for
that package version, but do not interpret it as an engine-wide lack of atmosphere or fog.
UE 5.8.2 has native Reference Atmosphere and volumetric fog/cloud path-tracing paths.
Compare a short MRQ render before replacing UDS's approximation: the vendor's sky material,
custom cloud material, and post-process fog may not produce the same result as native paths.
Avoid applying both treatments without checking for duplicate fog/lighting.
```

Replace the task-table Path Tracer cell with `Validate UDS 9.5 compatibility settings against the intended native/approximated fog path.` Replace the Path Tracer gotcha at 180 with `Missing distant fog: inspect both UDS's post-process approximation and native volumetric-fog settings; use an MRQ frame to identify which path is active.` This removes an obsolete engine limitation without claiming an untested native replacement for the vendor package.

**Evidence:** [UDS 9.5 §45](https://ultradynamicsky.com/Documentation/V9/9-5#section-45) still makes the legacy limitation claim; read directly in the browser. Epic's [Path Tracer page requested for 5.8](https://dev.epicgames.com/documentation/unreal-engine/path-tracer-in-unreal-engine?application_version=5.8) documents native fog and Reference Atmosphere, but its extracted internal links contain `application_version=5.5`—a documentation-version ambiguity, not clean patch-version proof. Matching UE 5.8.2 source resolves the engine capability: `Engine/Source/Runtime/Renderer/Private/PathTracing.cpp`, `CVarPathTracingEnableReferenceAtmosphere`, `PathTracing::UsesReferenceAtmosphere`, `CVarPathTracingCloudMultipleScatterMode`, and path-tracer volume flags.

**UDS-CIN-02 — P2, retain conditional language for the static-property workaround.** At `SKILL.md:92,178`, replace categorical “call every frame” guidance with: `For a non-dynamic property, UDS 9.5 suggests trying the relevant Static Properties function during animation. First confirm that function applies this property in the installed package; compare repeated playback and an MRQ render before adopting per-frame calls.` Vendor [§43](https://ultradynamicsky.com/Documentation/V9/9-5#section-43) says “could try”/“should work”, not a guarantee. This prevents expensive per-frame reapplication becoming an automatic recipe.

### No-change checks and unresolved questions

- Vendor §§43–46 and §125 match the deterministic Cloud Phase, loop, UDW ownership, manual-weather, and offline-render configuration recipes. Preserve those constraints and restoration gate; no generic Sequencer rewrite is needed.
- No installed UDS 9.5 assets were inspected and no movie was rendered. Package/UE 5.8.2 compatibility, exact runtime functions, and native-vs-approximate visual parity remain unverified. UE 5.8/hotfix rendering notes do not independently establish third-party compatibility.

## ultra-dynamic-sky/uds-clouds

**Status:** findings; vendor-documentation verified, UE/package integration partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-CLD-01 — P2, one owner for the cinematic cloud loop.** Replace `skills/ultra-dynamic-sky/uds-clouds/SKILL.md:128-147` (the full Seamless looping subsection) with:

```text
### Seamless looping (for film renders)
Use `uds-cinematics-rendering` for the complete Cloud Phase looping recipe and repeated
playback/render gate. A loop requires a full formation-texture UV cycle; arbitrary noise,
direction, and phase endpoints do not guarantee continuity.
```

**Why:** identical recipe already exists in the cinematic skill; preserve its non-obvious constraint while eliminating duplicate update sites. **Evidence:** [UDS 9.5 §46](https://ultradynamicsky.com/Documentation/V9/9-5#section-46), compared with both repository recipes. Vendor §§10–15,64,66 were read and support the core cloud-mode, phase, paint-save, and additive-card ray descriptions.

### Unresolved questions / verification gaps

- No installed vendor Blueprints/materials or runtime render checked. Engine release/upgrade notes do not prove that UDS's named rendering-mode options map identically to UE 5.8.2 cvars, nor that a performance ranking is universal. Retain workload-dependent mode/sample tuning rather than inventing a new preset.
- UE 5.8 fog scattering and renderer improvements do not automatically replace UDS's Niagara additive light-ray cards; they implement different effects. Do not silently substitute an experimental engine feature for this package workflow.

## ultra-dynamic-sky/uds-fog-and-atmosphere

**Status:** findings; package behavior partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-FOG-01 — P1, remove the repeated obsolete Path Tracer limitation.** Replace `skills/ultra-dynamic-sky/uds-fog-and-atmosphere/SKILL.md:66` with:

```text
UDS 9.5 offers `Render Height Fog In Path Tracer Using Post Process` as a distant-fog
approximation. UE 5.8.2 also supports native volumetric fog; use `uds-cinematics-rendering`
to choose and verify the intended path rather than assuming the engine has no fog support.
```

**Why/evidence:** same engine-vendor distinction as UDS-CIN-01; UE 5.8.2 `Engine/Source/Runtime/Renderer/Private/PathTracing.cpp`, volume flags and `PathTracing::UsesReferenceAtmosphere`; [vendor §45](https://ultradynamicsky.com/Documentation/V9/9-5#section-45). Keeps rendering configuration in its owner skill.

**UDS-FOG-02 — P2, don't assert an old engine bug unconditionally.** At `SKILL.md:162`, replace the flicker bullet with: `For black sky flicker, UDS 9.5 documents a camera-below-atmosphere-ground issue. Reproduce it on the installed UE version, inspect the component's ground-relative placement, and test moving that component below the camera range on a copy before applying the workaround.` [Vendor §158](https://ultradynamicsky.com/Documentation/V9/9-5#section-158) itself says “probably” and “in some circumstances”; no matching 5.8.2 bug reproduction was established. Avoids moving atmosphere geometry to treat an unrelated exposure/material failure.

### No-change checks and unresolved questions

- Read vendor §§32–35,37–38,157–159: density versus falloff, atmosphere-controlled color, distance-field ground fog, UDW ownership, and Shadow Quality routing match. Keep those boundaries.
- UE 5.8's Fog Screen Space Scattering is Experimental (5.8 release notes); it is not evidence that the vendor's global volumetric material, masks, or ground fog can be removed. No new package knob is invented for it.
- No installed UDS asset/Blueprint inspection, fog render, scalability sweep, or package-specific migration test. The runtime pseudo-function `CallStaticPropertiesVolumetricFog` is not a verified callable symbol; resolve the vendor Blueprint function before use.

## ultra-dynamic-sky/uds-lighting-and-shadows

**Status:** findings; engine mobility/source and vendor documentation checked, package execution partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-LGT-01 — P2, distinguish UDS time restrictions from engine light mobility.** At `skills/ultra-dynamic-sky/uds-lighting-and-shadows/SKILL.md:121`, replace the row with:

```text
| Preserve baked-lighting assumptions | Stationary lights can change direct-light brightness/color at runtime, but their baked indirect lighting does not update. Moving lights or changing baked contributions requires an appropriate rebuild. UDS 9.5 separately restricts runtime Time of Day when its sun is Static/Stationary. |
```

**Why:** prevents the vendor's broad warning becoming “any directional-light change invalidates lightmaps,” while keeping the real UDS workflow restriction. **Evidence:** [Epic UE 5.8 Stationary Light Mobility](https://dev.epicgames.com/documentation/unreal-engine/stationary-light-mobility-in-unreal-engine?application_version=5.8), direct brightness/color versus baked indirect; [UDS 9.5 §22](https://ultradynamicsky.com/Documentation/V9/9-5#section-22), package time/mobility rule.

### No-change checks and unresolved questions

- Read vendor §§17–22,48,50,63. Retain built-in component preference, custom-actor setup, sky-light mode ownership, exposure controls, and toggle-component hierarchy. UE 5.8.2 `Engine/Source/Runtime/Engine/Classes/Components/DirectionalLightComponent.h:240-241`, `CloudScatteredLuminanceScale`, remains BlueprintReadOnly; no native Blueprint setter was found in that header. Do not remove the manual custom-light fix-up merely because 5.8 is newer.
- MegaLights is Production-Ready in UE 5.8, but no source/vendor evidence establishes it as a substitute for these sun/moon/sky-light responsibilities. Leave general renderer adoption to `lighting-and-lumen` rather than add unrelated instructions here.
- No installed vendor package, baked-light rebuild, water-shadow render, or runtime lighting test. Platform-wide performance/support promises remain vendor claims, not independently measured guarantees.

## ultra-dynamic-sky/uds-modifiers-configs-state

**Status:** findings; documentation verified, installed asset/state persistence partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-STATE-01 — P2, remove a contradictory prerequisite.** Replace `skills/ultra-dynamic-sky/uds-modifiers-configs-state/SKILL.md:264` with:

```text
- `Set Modifier State` adds a modifier if absent. If its alpha is unexpectedly overwritten,
  check for time-of-day-specific control or competing Add/Remove/Set calls.
```

**Why/evidence:** current gotcha blames failure on the modifier not already being applied, immediately before saying it is added automatically. [UDS 9.5 §58](https://ultradynamicsky.com/Documentation/V9/9-5#section-58) explicitly guarantees add-if-absent and warns against mixing time-driven and manual control. The smaller correction avoids a redundant Add call and accidental fade.

### No-change checks and unresolved questions

- Read vendor §§57–62,65,67–69,74. Weather-before-sky configuration order, save-struct functions, startup-only overrides, modifier ownership, water-target refresh, UI client component, and child-Blueprint extension advice match. No scoped UE 5.8 release/upgrade/hotfix change justifies replacing these vendor contracts with custom persistence or networking.
- No installed package/source or save/reopen/multiplayer test. The supplied save struct is not proven to include every auxiliary system/asset introduced by a later package version. Child classes preserve owned code from file replacement but still need compatibility testing when parent APIs change.
- The `UDS Occlusion Portal` description is supported by vendor Sound Occlusion §109, checked later in this sequential pass under `udw-particles-lightning-wind-sounds`; installed component behavior remains untested. §62 alone was insufficient evidence.

## ultra-dynamic-sky/uds-performance-mobile-troubleshooting

**Status:** findings; vendor docs verified, performance/update execution partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-PERF-01 — P2, mobile renderer selection is not a platform-name rule.** Replace `skills/ultra-dynamic-sky/uds-performance-mobile-troubleshooting/SKILL.md:120` with:

```text
| 1 | Set UDS Feature Level to match the actual target renderer; most mobile projects use Mobile | Prevents unsupported feature activation; do not infer the renderer solely from the platform name. |
```

**Evidence/benefit:** [UDS 9.5 §72](https://ultradynamicsky.com/Documentation/V9/9-5#section-72) explicitly says “most mobile projects,” rather than all. Preserves viable renderer-specific configurations instead of forcing an unconditional downgrade.

**UDS-PERF-02 — P2, qualify cost and old bug claims.** Replace `SKILL.md:114` with `Static/stationary lighting can reduce dynamic-lighting work when the scene permits it, but compare the target renderer, overlap, shadow, and memory costs. Use uds-lighting-and-shadows for UDS mobility restrictions.` Replace the flicker table's Cause/Fix cell at `:264` with `See uds-fog-and-atmosphere for the version-qualified camera/atmosphere-ground diagnostic; reproduce before moving the component.`

**Evidence:** [UE 5.8 Stationary Light Mobility](https://dev.epicgames.com/documentation/unreal-engine/stationary-light-mobility-in-unreal-engine?application_version=5.8) documents expensive whole-scene shadow fallback after overlap limits; vendor [§158](https://ultradynamicsky.com/Documentation/V9/9-5#section-158) qualifies the historical flicker diagnosis. Avoids “always cheaper” and blanket engine-bug attribution without introducing a new optimization framework.

### No-change checks and unresolved questions

- Read vendor §§71–74,147–148,172,176. Retain cache reset versus static-property application, half-rate caveat, feature-level mapping, version-control backup, and relocated-content staging workflow. No UE 5.8 release/hotfix evidence proves those vendor workarounds universally obsolete.
- Do not remove `Recompileshaders All` solely on engine upgrade: the skill already limits it to missing rendering after a move. Conversely, this report did not reproduce the bug or justify running it unconditionally.
- No target-device profiling, actual launcher/Fab update, or installed package comparison. Launcher UI and asset-pack update restrictions are verified against vendor 9.5 documentation, not current launcher execution; inspect the actual package changelog before updating.

## ultra-dynamic-sky/uds-setup-and-modes

**Status:** findings; vendor 9.5 verified, exact installed package/UE compatibility partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-SET-01 — P1, pin package independently and make stack replacement reversible.** Insert before `skills/ultra-dynamic-sky/uds-setup-and-modes/SKILL.md:35`:

```text
Confirm the installed UDS package version separately from the Unreal version. This guidance
targets UDS 9.5; an engine-version tag is not proof of vendor compatibility. Read the package
change log when either version differs. Work on a copied map or a recoverable source-control
checkpoint. Identify which existing sky/light actors UDS replaces and preserve any external
light actors intentionally referenced by the UDS configuration before removing duplicates.
```

**Why/evidence:** vendor [§3](https://ultradynamicsky.com/Documentation/V9/9-5#section-3) replaces the sky stack, [§17](https://ultradynamicsky.com/Documentation/V9/9-5#section-17) explicitly permits custom external light actors, and [§73](https://ultradynamicsky.com/Documentation/V9/9-5#section-73) requires backup and package-change-log review. This adds the missing ownership/version gate, not a parallel engine setup workflow.

**UDS-SET-02 — P2, remove invented executable-looking enum/API syntax.** Replace the entire runtime code block at `SKILL.md:122-133` with:

```text
Get the UDS actor reference using the installed package's Blueprint API. Set Sky Mode,
Color Mode, Project Mode, and Feature Level using their actual exposed property/enum types.
The labels in this skill are UI names, not C++ enum declarations. UDW owns Cloud Coverage
and Fog when present; write the weather state there instead.
```

**Evidence:** vendor [§§4–8](https://ultradynamicsky.com/Documentation/V9/9-5#section-4) establishes property/display names, not `ESkyMode::VolumetricClouds` or `EColorMode::Simplified` C++ declarations. Removing unsupported syntax prevents agents from inventing imports/types. At `:140,151`, replace unconditional Mobile prescriptions with `Match UDS Feature Level to the actual target renderer; select Mobile when using the mobile renderer.` This follows §8/§72 rather than platform-name inference.

### No-change checks and unresolved questions

- Vendor §§3–8 support mode definitions, UDW-owned fields, ground placement, shader wait, and offline/game-mode separation. Preserve these and the daylight/night completion gate.
- No installed vendor assets, Blueprint schema, package release manifest, or setup execution checked. No Epic 5.8 release/hotfix entry can certify a proprietary package version by itself. Shared package-version caveat belongs here rather than duplicated across every UDS domain skill.

## ultra-dynamic-sky/uds-simulation

**Status:** findings; vendor accuracy claims verified as claims, installed algorithms partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-SIM-01 — P2, remove an invented accuracy cutoff and preserve attribution.** Replace `skills/ultra-dynamic-sky/uds-simulation/SKILL.md:106` with:

```text
- Astronomical mismatch: UDS 9.5 uses approximate algorithms. The vendor calibrates lunar
  position against 2017 and describes dates within several decades as generally accurate;
  it does not specify a 2050 cutoff or guarantee solar accuracy for every date. Validate the
  requested place/date against an authoritative ephemeris when numerical accuracy matters.
```

Replace the Sun table's accuracy/caveat cells at `:79` with `Vendor reports typical fractional-degree error and a little over one degree in its tested worst cases` and `Not a universal error bound; untested edge cases can be worse.`

**Evidence/benefit:** [UDS 9.5 §40](https://ultradynamicsky.com/Documentation/V9/9-5#section-40) explicitly qualifies its own tests. Prevents false precision in architectural sun studies while preserving game-sky usefulness. §41 confirms UTC plus selected offset, Simulation Speed, and DST ownership.

### Unresolved questions / verification gaps

- No installed simulation Blueprint, astronomical comparison, DST-boundary test, or runtime property application checked. The blanket statement at `:94` that toggles/location/date/DST are “mostly static” and `Static Properties - Simulation` immediately applies them is not established by §§40–41; verify the installed function and property flow before prescribing it.
- Epic's 5.8 release/upgrade/hotfix notes do not establish changes to the vendor's astronomical algorithms. No engine-native replacement is recommended without evidence that it preserves this package's time/state behavior.

## ultra-dynamic-sky/uds-sun-moon-stars

**Status:** partially verified; no evidence-led replacement recommended for the documented celestial-layer workflow.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified no-change checks

Read [UDS 9.5 §§27–30](https://ultradynamicsky.com/Documentation/V9/9-5#section-27), [§§52–55](https://ultradynamicsky.com/Documentation/V9/9-5#section-52), and [§160](https://ultradynamicsky.com/Documentation/V9/9-5#section-160). They confirm manual-target precedence, moon texture/normal pairing, star-map selection, separate aurora modes, glow direction, Space Roots and DBuffer-dependent compositing. These are package features, not Epic API declarations. Retain their constraints; UE 5.8 renderer additions do not establish a native replacement for the vendor's layered sky composition.

### Unresolved questions / verification gaps

- `skills/ultra-dynamic-sky/uds-sun-moon-stars/SKILL.md:158,177` identifies most appearance properties and Sun Scale as static; the inspected vendor sections do not enumerate those runtime classifications. Confirm actual Blueprint application paths rather than inferring them from the category name.
- No installed asset/Blueprint source, material compilation, target-platform decal test, or visual animation test. No scoped change in Epic 5.8 release/upgrade/hotfix guidance could certify those vendor internals; “no replacement recommended” is not a blanket UE 5.8.2 compatibility approval.

## ultra-dynamic-sky/uds-time

**Status:** findings; vendor time/event contract verified, scalar conversion and native bindings partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDS-TIM-01 — P1, use documented Blueprint dispatchers rather than invented native signatures.** Replace `skills/ultra-dynamic-sky/uds-time/SKILL.md:84–90` with:

```text
In Blueprint, obtain and validate the actor with `Get Ultra Dynamic Sky`, then use
`Bind to Sunrise` / `Bind to Sunset` and matching custom events. Inspect the installed
Blueprint's dispatcher signatures before writing native bindings; display names do not
establish a C++ `OnSunrise` member or `GetUltraDynamicSky()` function.
```

**Evidence/benefit:** [UDS 9.5 §49](https://ultradynamicsky.com/Documentation/V9/9-5#section-49) documents this Blueprint path, not the skill's C++-looking pseudocode. Prevents agents generating uncompilable vendor calls.

**UDS-TIM-02 — P2, qualify event counts and avoid unverified HHMM conversion.** Replace `:112` with:

```text
If time changes instantly from 14:00 to 18:00, the documented distinction is:
```

Replace `:121–129` with:

```text
Populate `Custom Time Dispatchers` with verified UDS scalar Time of Day values. To derive
one for a clock time such as 06:30, use the documented time-string or Time Code setter in
a disposable test, then read `Get Time of Day`. Do not assume the float encodes HHMM.
Bind `Custom Time` and switch on its emitted array index to choose the scheduled action.
```

**Evidence/benefit:** [§24](https://ultradynamicsky.com/Documentation/V9/9-5#section-24), [§25](https://ultradynamicsky.com/Documentation/V9/9-5#section-25), §49. The docs distinguish an **instant** change, not a fast transition that may be sampled more than once. They specify 0–2400 but do not establish that 630 means 06:30. This replacement removes a silently wrong scheduling assumption without inventing a conversion formula.

### Unresolved questions / verification gaps

- No installed conversion Blueprint, dispatcher binding, or replicated time jump tested. Numeric conversion remains unresolved, not proven HHMM or decimal-hour here.
- Read vendor replication §176; retain local client advancement and periodic synchronization. Epic 5.8 migration notes do not establish different behavior for this proprietary implementation. Refer to UDS-LIT-01 rather than duplicating its mobility wording correction at this skill's `:164`.

## ultra-dynamic-weather/udw-material-and-screen-effects

**Status:** findings; vendor documentation and selected renderer contracts verified, asset/runtime integration partially verified.  
**Files reviewed:** `SKILL.md`, `references/placed-and-water-effects.md` (entire files).

### Verified recommendations

**UDW-MAT-01 — P1, disambiguate override volumes from occlusion data.** Replace `skills/ultra-dynamic-weather/udw-material-and-screen-effects/SKILL.md:261` with:

```text
| **Sample UDW Material State** | Material snow coverage, dust coverage, and wetness after Weather Override Volumes and Weather Mask effects. Weather Override Volumes are not the distance-field Weather Occlusion Volume. |
```

Replace `:345` with `- **Custom material ignores spatial weather masking** — use Sample UDW Material State for Weather Override Volume and Weather Mask effects; raw MPC reads are not a replacement for those spatial operations.`

**Evidence/benefit:** [UDW 9.5 §105](https://ultradynamicsky.com/Documentation/V9/9-5#section-105) versus [§140](https://ultradynamicsky.com/Documentation/V9/9-5#section-140). Prevents agents conflating two very different systems because of “WOV.” Vendor §105 says `Sample UDW Seasons` while §86 says `Sample UDW Season`; do not rename the skill's node label until the installed asset resolves this documentation inconsistency.

**UDW-MAT-02 — P1, make Rigid shadow caching a measured tradeoff, not a universal fix.** Replace `:178` and shorten the duplicate at `:338` to link here:

```text
The vendor suggests Rigid Shadow Cache Invalidation Behavior for DLWE landscapes to
reduce repeated WPO/PDO invalidation. Rigid suppresses material-driven shadow refreshes;
compare changing snow/trails and their shadows before accepting the tradeoff. Keep Auto
when changing displacement needs accurate shadows. In UE 5.8, also profile the narrower
Nanite tessellation shadow switches `r.Shadow.Virtual.Nanite.AllowTessellationDirectional`
and `r.Shadow.Virtual.Nanite.AllowTessellationLocal`; disabling one reduces tessellated
shadow detail for that light class, not DLWE's visible surface displacement.
```

**Evidence/benefit:** vendor [§101](https://ultradynamicsky.com/Documentation/V9/9-5#section-101); UE 5.8.2 `Engine/Source/Runtime/Engine/Public/SceneTypes.h:220–229` (`EShadowCacheInvalidationBehavior::Rigid`); `Engine/Source/Runtime/Renderer/Private/VirtualShadowMaps/VirtualShadowMapArray.cpp:200–215` (both CVars, default 1); UE 5.8 release notes, Nanite rendering changes. Adds new native cost controls and preserves the correctness ceiling of the older workaround. [Epic VSM documentation](https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine?application_version=5.8) requested at 5.8 contains older internal links; source is authoritative here.

**UDW-MAT-03 — P2, fix a reference's invented dry-puddle condition.** Replace `references/placed-and-water-effects.md:88–89` with:

```text
- **Puddle visible while dry** — the vendor keeps dry meshes visible in the editor for
  placement and hides them at runtime. Check runtime state and the installed actor logic;
  placing the dry level below ground is a placement recommendation, not a documented
  prerequisite for its visibility toggle.
```

**Evidence/benefit:** [UDW 9.5 §127](https://ultradynamicsky.com/Documentation/V9/9-5#section-127). Avoids diagnosing a state/visibility problem solely by moving the actor.

### Unresolved questions / verification gaps

- Read vendor §§99–105, 127–134 and 136–140 against both files. Retain material-attribute routing, local-space rotation handling, control-point range, physical-material filters, and local weather-state ownership.
- No installed material graphs, Niagara systems, DLWE interaction test, rendered shadow comparison, target-platform build, or measured performance. Nanite tessellation support in the package is documented; this is not proof that every project's material/rendering configuration works.
- Epic's 5.8 Nanite overview was retrieved, but its internal links include older versions and it does not establish a universal production-readiness label for every DLWE tessellation path. No automatic migration to new Nanite foliage/wind systems is proposed.

## ultra-dynamic-weather/udw-particles-lightning-wind-sounds

**Status:** findings; vendor contracts verified, renderer/platform limitations partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDW-FX-01 — P2, retain a conditional VR workaround without declaring a universal engine limitation.** Replace `skills/ultra-dynamic-weather/udw-particles-lightning-wind-sounds/SKILL.md:64` with:

```text
| Splashes render only in one eye | UDW 9.5 documents this symptom with its GPU-sprite deferred-decal splash setup and Instanced Stereo; verify on the target UE/RHI/HMD | If reproduced, try Splash Particles Rendering Mode = Translucent; check both eyes and accept its different lighting behavior before keeping the workaround. |
```

Use the same conditional wording at `:336` rather than applying the fallback preemptively.

**Evidence/benefit:** [UDW 9.5 §167](https://ultradynamicsky.com/Documentation/V9/9-5#section-167) says “doesn't seem to support” and “one thing you can try,” not guaranteed cross-version incompatibility. UE 5.8 release notes did not establish a fix for this exact material/system combination. Preserves actionable failure guidance without forcing a lower-quality renderer path in unaffected projects.

**UDW-FX-02 — P2, label pseudo-native examples and keep the actual node contract.** Replace `:156–160` with:

```text
Call the Blueprint function `Flash Lightning` on the UDW actor. Enable its custom-location
input when needed; the location is the bolt root at cloud height. A nonzero Custom Target
Location selects the endpoint. Inspect the installed node pins (including enable/seed
inputs); this display name does not establish a two-argument native C++ signature.
```

Replace `:248–251` with `Call the Blueprint function Set Enable Weather Sound Effects to toggle all weather sounds, or set the documented per-sound Volume variables for individual sounds.` Replace `:329–332` with `Call the Blueprint function Change Environment Sound with an environment sound asset to start/change it, or with no asset selected to stop it.`

**Evidence/benefit:** [vendor §97](https://ultradynamicsky.com/Documentation/V9/9-5#section-97), [§108](https://ultradynamicsky.com/Documentation/V9/9-5#section-108), [§110](https://ultradynamicsky.com/Documentation/V9/9-5#section-110). Prevents agents treating illustrative member syntax as a compiled API and omitting the custom-location enable pin.

### Unresolved questions / verification gaps

- Read vendor §§92–97, 108–110, 118–123, 162–167. Keep collision query/channel requirements, distance-field/scalability coupling, single active kill sphere, audio-bus channel mapping, occlusion portal behavior, and cloth/physics/material wind distinctions. Do not replace proprietary weather wind with a newer engine wind system without tracing each consumer.
- Vendor §109 resolves the portal-documentation gap previously noted under `uds-modifiers-configs-state`: it explicitly documents `UDS Occlusion Portal`; installed component behavior still requires validation.
- No installed Niagara/MetaSound/Blueprint assets, two-eye HMD capture, cloth consumer test, audio audition, or networking probe. No Epic 5.8 migration note establishes that these package-specific workarounds can be removed wholesale.

## ultra-dynamic-weather/udw-random-seasons-temperature

**Status:** findings; vendor behavior verified, exact node identifiers and runtime execution partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDW-RND-01 — P2, remove pseudo-native duplication while retaining useful behavior.** Replace `skills/ultra-dynamic-weather/udw-random-seasons-temperature/SKILL.md:76–78` with `Call the Blueprint function Change to Random Weather Variation on the UDW actor.` Replace `:121–125` with:

```text
Call the Blueprint function `Get Current Temperature` and choose Fahrenheit or Celsius
and the required Sample Location. Global excludes location-based effects; inspect the
installed node's actual choices/pins rather than treating this as a C++ signature.
```

Delete the redundant Runtime / Blueprint scripting summary at `:157–166`; the owner sections already cover these functions and cross-link the weather state skill. In the Season Mode table at `:99`, replace `set yourself via SetSeason(value)` with `set through the Blueprint function Set Season`.

**Evidence/benefit:** [UDW 9.5 §85](https://ultradynamicsky.com/Documentation/V9/9-5#section-85), [§86](https://ultradynamicsky.com/Documentation/V9/9-5#section-86), [§113](https://ultradynamicsky.com/Documentation/V9/9-5#section-113). Reduces duplicated API-looking surface and preserves the important temperature-is-an-output invariant, date/manual season ownership, and local-vs-global sampling behavior.

### Unresolved questions / verification gaps

- Vendor §86 uses `Sample UDW Season`; §105 uses `Sample UDW Seasons`. Installed material asset title is needed before normalizing either skill. Do not “repair” identifiers from inconsistent documentation.
- No installed random-selection Blueprint, probability boundary tests, date rollover, temperature sampling, or config round-trip. Climate data is the vendor's claim, not independently assessed meteorology. Epic UE 5.8 release/upgrade notes do not certify these vendor calculations; no native replacement is established.

## ultra-dynamic-weather/udw-setup-and-state

**Status:** findings; vendor contracts verified, installed assets and network behavior partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDW-SET-01 — P1, fix reversed troubleshooting advice.** Replace `skills/ultra-dynamic-weather/udw-setup-and-state/SKILL.md:240` with:

```text
- **Weather does not stay at the manually selected preset** — Change Weather is documented
  to switch from random variation to a static preset. Check for another caller, local
  volume/storm, or manual value override before changing modes. Call Change to Random
  Weather Variation only when intentionally handing control back to random variation.
```

**Evidence/benefit:** [UDW 9.5 §84](https://ultradynamicsky.com/Documentation/V9/9-5#section-84), [§85](https://ultradynamicsky.com/Documentation/V9/9-5#section-85), [§87](https://ultradynamicsky.com/Documentation/V9/9-5#section-87). The existing remedy could re-enable the exact controller the caller wants to stop.

**UDW-SET-02 — P1, replace invented native dispatcher binding.** Replace `:172–178` with:

```text
From a valid UDW actor reference in Blueprint, bind a matching custom event to the
documented `Started Raining` dispatcher (or another listed dispatcher). Inspect its
installed signature before connecting parameters. `OnStartedRaining.AddDynamic(...)`
is not a verified native member API for this Blueprint asset.
```

Replace the generic member-call block at `:131–133` with `Call the Blueprint function Change Weather on the UDW reference with the target preset and transition duration; leaving the preset input empty selects Manual Weather State.` Replace `:207–211` with `For a one-off sample, call the Blueprint function Test Actor for Weather Exposure on UDW with the actor reference. Its rain, wind, snow, and dust floats combine intensity and exposure; 1 means fully exposed at maximum intensity.`

**Evidence/benefit:** vendor [§115](https://ultradynamicsky.com/Documentation/V9/9-5#section-115), [§116](https://ultradynamicsky.com/Documentation/V9/9-5#section-116), §§84/87. Agents keep the supported Blueprint route rather than inventing C++ symbols.

**UDW-SET-03 — P2, identify the actual driver of freezing breath.** Replace `:70` with:

```text
| Snow | float | Drives snow particles and can drive screen frost; freezing breath uses calculated temperature or Actor Weather Status temperature, not Snow directly. |
```

**Evidence/benefit:** [vendor §137](https://ultradynamicsky.com/Documentation/V9/9-5#section-137), §116. Prevents treating precipitation as a prerequisite for cold breath.

### Unresolved questions / verification gaps

- Read vendor §§78–79, 81–84, 87, 112, 115–116, 135 and 183. Retain preset/manual/local distinction, parent Custom Weather Behavior call, material-state lag, and replication of state sources with per-client local sampling.
- No installed package, dispatcher signatures, actor exposure, configuration persistence, multiplayer run, or render tested. Use the shared version gate proposed under `uds-setup-and-modes`; Epic 5.8 release/migration evidence does not establish compatibility of a particular UDW asset build.

## ultra-dynamic-weather/udw-spatial-weather

**Status:** findings; vendor spatial behavior verified, exact Blueprint signatures and persisted masks partially verified.  
**Files reviewed:** `SKILL.md` (no supporting files).

### Verified recommendations

**UDW-SPA-01 — P2, distinguish visible surface state from distant storm rendering.** Replace `skills/ultra-dynamic-weather/udw-spatial-weather/SKILL.md:20` with:

```text
| **Weather Override Volume** | Arbitrary spline | Material state can be visible from outside; it does not create Radial Storm's distant clouds/fog/lightning | Region-specific weather state with arbitrary shape |
```

Replace `:32` with `- Keeping snow from accumulating inside a building, or wetness off the floor under a roof.`

**Evidence/benefit:** [UDW 9.5 §88](https://ultradynamicsky.com/Documentation/V9/9-5#section-88), [§89](https://ultradynamicsky.com/Documentation/V9/9-5#section-89). Resolves the overview's contradiction with its own material-state section and corrects the reversed task description.

**UDW-SPA-02 — P2, remove inferred child-class and abbreviated signature contracts.** Replace `:215` with:

```text
- **WOV custom behavior not running** — override the documented Custom Volume Behavior
  function in a Weather Override Volume child and verify that UDW samples that volume.
  Do not infer an equivalent Radial Storm override; inspect the installed storm Blueprint.
```

Replace `:120–125` with:

```text
In Blueprint, spawn the installed Radial Storm actor class, call Fade In Storm, then Move
Storm Over Time. The vendor example fades in over 30 seconds, moves over 200 seconds,
and fades out during its final 30 seconds. Configure the actual node's movement/fade
inputs explicitly; the documentation excerpt does not establish a three-argument C++ API.
```

Replace `:198–204` with `Call the Blueprint function Fade Mask Over Time on the Weather Mask Brush or Weather Mask Projection Box component. Inspect its pins for target/fade controls; Weather Mask Update Period controls sampling, documented as 20 updates per second by default.`

**Evidence/benefit:** [vendor §88](https://ultradynamicsky.com/Documentation/V9/9-5#section-88), §89 and [§106](https://ultradynamicsky.com/Documentation/V9/9-5#section-106). Keeps the useful native Blueprint workflow without inventing a storm hook or losing explicit fade inputs.

### Unresolved questions / verification gaps

- Read all four cited vendor sections. Retain control-point ownership, spatial transition width, limited distant-storm rendering, vertical mask projection, render-target range/resolution, explicit painter Save and `UDS_LevelData` persistence location.
- No installed volume/storm assets, exact node signatures, overlap-priority experiment, material-mask render, save/reopen check, or packaged execution. Epic UE 5.8 release/upgrade guidance does not establish a package-level migration or eliminate these constraints. No new experimental engine system is recommended as a drop-in replacement.

## Final validation and approval boundary

| Check | Actual result |
| --- | --- |
| Repository inventory versus report sections | PASS: 62 skills, 62 unique matching sections; no missing or duplicate sections |
| Supporting-file reconciliation | PASS: all 156 supporting paths represented in their owning sections; 218 total skill-directory files |
| Per-skill status | PASS: every section has a disposition; 59 findings, 1 no changes, 2 partially verified |
| Markdown fence check | PASS: balanced fenced blocks; no skill heading swallowed by a code fence |
| Core citation-path recheck | Exit 0: 203 Markdown files scanned, 584 unique engine citations, all paths exist |
| Validation runtime | Node v26.7.0 was available, not prescribed Node 22; citation run is supplemental evidence, not the repository's prescribed CI pass |
| Existing working-tree work | Seven modified skills and the new Windows PIE reference preserved; audit edits are confined to this report |
| Runtime/compile/package verification | Not performed; source/documentation audit only |

The retained diffs are review excerpts, not an apply-ready patch: some old-side excerpts summarize or normalize source whitespace, and line numbers can drift with the preserved working-tree edits. Apply approved replacements against the actual named passages and rerun the relevant Node 22 checks; compile or exercise changed API examples before claiming their operational acceptance.

**Proposed skill edits require separate approval.** No skill implementation, commit, push, package migration, engine update, vendor update, or production-project mutation has been performed. Unresolved items—especially proprietary asset contracts, historical API introduction/removal claims, platform rendering, and integration-specific observations—remain separate from the evidence-backed recommendations.
