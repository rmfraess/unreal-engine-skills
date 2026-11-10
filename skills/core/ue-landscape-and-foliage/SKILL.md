---
name: ue-landscape-and-foliage
description: >-
  Build Unreal landscape terrain, instanced vegetation, and procedural environments in C++ —
  ALandscape / ALandscapeProxy / ULandscapeComponent (heightmap grid, material layers, edit
  layers, splines, Nanite landscape), UFoliageType / AInstancedFoliageActor /
  UHierarchicalInstancedStaticMeshComponent (HISM-backed instanced foliage, procedural foliage
  volumes), and the PCG framework (UPCGComponent / UPCGGraph, point data, landscape sampling,
  runtime generation). Use when creating or sculpting terrain, painting weight layers or foliage,
  adding landscape splines, batching vegetation with HISM, authoring PCG graphs, querying
  landscape data from C++, or debugging instancing and PCG generation issues.
metadata:
  engine-version: "5.8"
  category: world-building
---

# Landscape & foliage

For automatic terrain shading, use `ue-auto-landscape-materials`. For runtime virtual textures and material-driven grass, use `ue-landscape-rvt-and-grass`.

Three complementary systems cover terrain and environment population:

| System | Actor / Component | Purpose |
|---|---|---|
| Landscape | `ALandscape` → `ULandscapeComponent` | Heightmap terrain with painted weight layers and splines |
| Foliage / HISM | `AInstancedFoliageActor` → HISM | Hand-painted instanced vegetation at low draw-call cost |
| PCG | `UPCGComponent` + `UPCGGraph` | Rule-based graph pipeline for procedural placement |

## When to use this skill

- Creating, sculpting, or importing a heightmap landscape; tuning component/section sizes.
- Authoring landscape materials with `Layer Blend` nodes and `ULandscapeLayerInfoObject`s.
- Painting foliage (`UFoliageType_InstancedStaticMesh`) onto terrain or meshes; tuning
  density, culling, collision, and scalability.
- Adding landscape splines (`ALandscapeSplineActor`) for roads/rivers/paths.
- Enabling Nanite on a landscape (`bEnableNanite`).
- Authoring or extending a PCG graph from C++ — subclassing `UPCGSettings`, querying
  `UPCGData`, calling `Generate()`/`Cleanup()` from code.
- Debugging foliage not rendering, PCG not generating, landscape layer info missing.

## Landscape

### Class hierarchy

`ALandscape` extends `ALandscapeProxy` (which itself extends `APartitionActor`). The proxy
holds the component grid, material, and dimension metadata. `ALandscape` is the authoritative
root; large landscapes in World Partition spawn `ALandscapeStreamingProxy` instances to load
per-region.

```
ALandscape : ALandscapeProxy : APartitionActor
                  └── TArray<ULandscapeComponent*> LandscapeComponents  (LandscapeProxy.h:682)
                  └── UMaterialInterface* LandscapeMaterial             (LandscapeProxy.h:604)
                  └── int32 ComponentSizeQuads                          (LandscapeProxy.h:924)
                  └── int32 SubsectionSizeQuads                         (LandscapeProxy.h:927)
                  └── int32 NumSubsections                              (LandscapeProxy.h:930)
                  └── bool  bEnableNanite                               (LandscapeProxy.h:491)
```

`ULandscapeComponent` (`LandscapeComponent.h`:431) extends `UPrimitiveComponent` — it is
the renderable, collidable unit of terrain.

### Heightmap dimensions

Landscape dimensions are not arbitrary. Each component contains `NumSubsections × NumSubsections`
sections, each `SubsectionSizeQuads` quads wide. Total landscape quads in one axis is
`NumComponents × ComponentSizeQuads`. The corresponding heightmap vertex count is
`(NumComponents × ComponentSizeQuads) + 1`. Common valid size: 8129 × 8129 vertices
(32 × 32 components, 4 sections/component, 63 quads/section). Heights are stored as 16-bit
values, `h_cm = (v − 32768) × ZScale / 128`: ±256 m at default Z scale 100, ±2,048 m at 800.
Raising terrain past that range needs a new Z scale, which re-encodes every height. On
terrain with protected or accepted areas, keep new relief inside the existing range.

### Material layers and `ULandscapeLayerInfoObject`

Each paintable weight layer requires a `ULandscapeLayerInfoObject` data asset
(`LandscapeLayerInfoObject.h`:59) paired with a `LandscapeLayerBlend` node in the landscape
material. Layer weights are stored per-component in weightmap textures.

```cpp
// Reading landscape layer weight at runtime (C++ — editor or runtime with proper setup):
// ULandscapeInfo::GetLayerWeightAtLocation is the key query path.
// ULandscapeLayerInfoObject holds PhysicalMaterial and layer blend settings.
```

**Edit Layers** (`LandscapeEditLayer.h`) allow non-destructive stacking of sculpt/paint
operations — each edit layer renders additively/subtractively into the final heightmap.

Before a whole-Landscape paint-identity replacement, reconcile the native component map, LandscapeInfo proxy inventory and live world actors in both directions; inspect matching World Partition descriptors too. Fail before a transaction if any affected proxy or component is unavailable or unregistered: an unloaded proxy can remain resident, so descriptor `IsLoaded()` and the engine's unloaded-component query alone can falsely report completeness. Check effective blend method and group, physical material and collision threshold before replacement; preserve edit, rendered, mobile, collision, allowlist and edit-layer blend metadata identities. Preserve the existing target's reimport filename across native `ULandscapeInfo::ReplaceLayer`: it recreates target settings with an empty path. Snapshot the filename before replacement and restore it inside the transaction through `UpdateTargetLayer` with property change notification so inherited proxy settings are synchronized. Preflight metadata conflicts and snapshot affected edit-layer UObjects before the public native blend-status mover: it can overwrite a destination entry and its internal `Modify()` occurs after mutation. When opting into custom layers, snapshot each custom layer before native replacement or stale-cache blend repair, because the engine dispatches blend-move virtuals to every edit layer; do not promise Undo for a plugin's transient state or mutations to other objects. Verify sampled data and references after save/reload. Audit compatibility before choosing a custom-layer guard: an exact-class allowlist also rejects subclasses and Epic Landscape Patch layers, even height-only ones. Do not allow the Epic patch layer solely by class: custom patch components can retain LayerInfo references the layer scan misses. Treat registered patches and the World Partition `AffectsLandscape` tag as discovery hints, not complete inventories: unloaded actors, unresolved Landscape pointers and multiple components overwriting a single tag can hide targets. A same-world resident scan also misses World Composition tiles, dormant child-actor templates and cross-world bindings; treat uninspected actors or nested containers as unknown rather than safe. Exercise both real built-in height/paint patches and a reference-holding custom component before widening support. Distinguish an installed plugin from an affected Landscape that actually contains its layer, and identify the specific operation blocked rather than implying the plugin or all Landscape tools stop working. Do not assert how many users are affected without evidence. A standard layer can host Blueprint brushes and a Landscape Patch layer can host custom patch components; direct UObject reference scans may miss their soft, indirect or external references, so neither an edit-layer class allowlist nor the native picker proves complete reference repair. Inspect every edit layer's serialized `FLandscapeLayer::Brushes` via `ALandscape::ForEachLayerConst` before replacement; default to rejecting nonempty brush lists before mutation unless reference handling is proven safe. When an explicit risk-acceptance path is authorized, identify the affected brush and custom layers in the caller-visible result, obtain the user's informed approval before opting in, and retain the uncertainty after success rather than claiming unknown references were repaired. Keep inventory, incompatible-data and conflicting-reference failures non-overridable and report their actual reason, so approval is never presented as a remedy for a hard failure. Native replacement can succeed while a custom brush retains the old LayerInfo, and an edit-layer UObject scan does not inspect the sibling brush list. This inventory covers attached brushes, not detached actors or arbitrary external references; do not claim global reference safety. Balance useful support for real workflows against data safety: explain unknown reference risks and retain safe defaults while allowing an explicitly authorized risk-acceptance path where appropriate. Test that path in a disposable project; do not claim full plugin compatibility or reference repair without evidence. Distinguish existing API regressions from restrictions on a new operation. See the Landscape fixtures reference linked from `gd-tdd` for resident- and partially-loaded-proxy regressions and loaded controls.

### Landscape splines

`ALandscapeSplineActor` (`LandscapeSplineActor.h`:14) owns a `ULandscapeSplinesComponent`
containing control points and segments. Splines deform terrain beneath them (raise/lower)
and optionally spawn static meshes along their length as decoration or road surfaces.

When repairing a null control-point slot, do not create an Undo transaction that snapshots the invalid slot: UE 5.8 `ULandscapeSplinesComponent::PostEditUndo` calls `CheckSplinesValid`, which removes null entries and emits an ensure. Remove the slot as a non-Undo sanitation, mark the owning package dirty, and test that Undo/Redo still reaches the preceding valid edit. Scope-guard test-injected nulls so fixture cleanup also works when the assertion fails; engine component cleanup can otherwise dereference the null.

When a shared Landscape identifier lookup rejects ambiguous or inactive targets, propagate the specific reason into each structured caller's error result and make legacy caller logs non-contradictory. Test refusal without mutation, genuine missing targets and a unique active positive control; an accurate internal warning alone may not reach an MCP client.

### Nanite landscape

Set `bEnableNanite = true` on the `ALandscapeProxy` to render the landscape as a Nanite
mesh on supported platforms. The engine generates and maintains a `ULandscapeNaniteComponent`
alongside the traditional LOD components. LOD settings under `NaniteLODIndex` control the
source LOD used for Nanite mesh generation (default 0). See `ue-nanite-and-rendering`.

## Foliage (instanced placement)

### Class hierarchy

```
UFoliageType (abstract, UObject)              — FoliageType.h:105
  └── UFoliageType_InstancedStaticMesh        — FoliageType_InstancedStaticMesh.h:13
  └── UFoliageType_Actor                      — FoliageType_Actor.h
AInstancedFoliageActor : AISMPartitionActor   — InstancedFoliageActor.h:28
UHierarchicalInstancedStaticMeshComponent     — HierarchicalInstancedStaticMeshComponent.h:135
  (extends UInstancedStaticMeshComponent)
```

`AInstancedFoliageActor` stores a `TMap<UFoliageType*, FFoliageInfo>` and manages the
underlying HISM instances. One `AInstancedFoliageActor` per world-partition cell holds all
foliage painted in that cell.

### UFoliageType key properties (FoliageType.h)

| Property | Purpose |
|---|---|
| `Density` | Instances per 1000 × 1000 UU area |
| `Radius` | Minimum spacing between instances |
| `Scaling` / `ScaleX/Y/Z` | Random scale ranges per axis |
| `AlignToNormal` | Tilt instance to match surface normal |
| `GroundSlopeAngle` | Valid placement slope range |
| `LandscapeLayers` | Restrict painting to named weight layers |
| `CullDistance` | Per-instance screen-size cull |

### HISM internals

`UHierarchicalInstancedStaticMeshComponent` builds a BVH cluster tree over its instances
(`ClusterTreePtr`, `FClusterNode`). Rendering culls entire clusters with a single check.
Adding/removing instances invalidates the tree; `BuildTreeIfOutdated(bool Async, bool Force)`
triggers a rebuild (synchronous or async).

Key API (HierarchicalInstancedStaticMeshComponent.h):
- `AddInstance(Transform, bWorldSpace)`:303 — add one instance; returns index.
- `AddInstances(Transforms, bReturnIndices, bWorldSpace)`:304 — batch add.
- `RemoveInstance(Index)`:305 / `RemoveInstances(Indices)`:306 — remove by index.
- `UpdateInstanceTransform(Index, NewTransform, bWorldSpace, bMarkDirty, bTeleport)`:308.
- `BuildTreeIfOutdated(Async, ForceUpdate)`:330 — explicit rebuild trigger.

```cpp
// Batch-adding foliage instances from C++ (illustrative):
UHierarchicalInstancedStaticMeshComponent* HISM = NewObject<UHierarchicalInstancedStaticMeshComponent>(this);
HISM->SetStaticMesh(TreeMesh);
HISM->RegisterComponent();

TArray<FTransform> Transforms;
for (const FVector& Pos : SpawnPositions)
{
    FTransform T(FRotator(0, FMath::RandRange(0.f, 360.f), 0),
                 Pos,
                 FVector(FMath::RandRange(0.8f, 1.2f)));
    Transforms.Add(T);
}
HISM->AddInstances(Transforms, /*bShouldReturnIndices=*/false, /*bWorldSpace=*/true);
// Tree rebuilds async after the next tick; forcing sync:
HISM->BuildTreeIfOutdated(/*Async=*/false, /*ForceUpdate=*/true);
```

### Procedural foliage volumes

`UProceduralFoliageComponent` (`ProceduralFoliageComponent.h`:42) is placed on a volume
actor and references a `UProceduralFoliageSpawner`. The spawner holds an array of
`UFoliageType` entries with competition rules (spread radius, priority). Simulation runs
at cook/editor time and bakes instances into `AInstancedFoliageActor`s.

## PCG (Procedural Content Generation)

PCG is a shipped plugin at `Engine/Plugins/PCG/`. Enable it in `.uproject` if not present.

### Core types

| Type | Header | Role |
|---|---|---|
| `UPCGComponent` | `PCGComponent.h`:112 | Runs a graph on its actor; entry point for generate/cleanup |
| `UPCGGraph` | `PCGGraph.h`:332 | Asset containing nodes and edges |
| `UPCGGraphInterface` | `PCGGraph.h`:159 | Abstract base for graphs and graph instances |
| `UPCGData` | `PCGData.h` | Base for all spatial/attribute data flowing through the graph |
| `UPCGPointData` | `Data/PCGPointData.h` | Point cloud — the primary per-instance data type |
| `UPCGLandscapeData` | `Data/PCGLandscapeData.h` | Samples landscape height/normals/layers |

### `UPCGComponent` lifecycle

```
Generate()      — schedules an async graph execution, result baked as managed resources
Cleanup()       — removes all managed resources (ISM components, spawned actors)
GenerateLocal() — local-only generate (not replicated); use in editor automation
CleanupLocal()  — local-only cleanup
NotifyPropertiesChangedFromBlueprint() — dirty + re-generate from Blueprint
```

`GenerationTrigger` (`EPCGComponentGenerationTrigger`: `GenerateOnLoad`, `GenerateOnDemand`,
`GenerateAtRuntime`) controls when the graph runs automatically. Set `bIsComponentPartitioned`
to distribute generation across World Partition cells via `UPCGSubsystem`.

### Working with PCG from C++

To extend PCG, subclass `UPCGSettings` (defines node inputs/outputs/properties) and pair it
with a `UPCGElement` subclass (`Execute(FPCGContext*)`). For runtime queries:

```cpp
// Triggering PCG generation from gameplay code:
UPROPERTY(VisibleAnywhere)
TObjectPtr<UPCGComponent> PCGComp;

void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    if (PCGComp)
    {
        // Force a fresh generation regardless of trigger type:
        PCGComp->Generate(/*bForce=*/true);
    }
}

// Listening to generation completion:
PCGComp->OnPCGGraphGeneratedExternal.AddDynamic(this, &AMyActor::OnPCGDone);
```

PCG landscape data (`UPCGLandscapeData`) exposes layer weights as point attributes when
`bGetLayerWeights = true` (`PCGLandscapeData.h`). Filter points by attribute value in the
graph to, for example, restrict scatter to slope ranges below a threshold.

## Performance

- **Draw calls:** foliage HISM merges thousands of instances into one draw call per cluster.
  Actor foliage (`UFoliageType_Actor`) costs one draw call per instance — avoid at scale.
- **Cull distance:** set `CullDistance` (start + end) on each `UFoliageType`; far instances
  fade with `PerInstanceFadeAmount` in the material.
- **HISM tree rebuild:** batching `AddInstances` is far cheaper than repeated `AddInstance`;
  prefer a single batch call then one `BuildTreeIfOutdated`.
- **Nanite foliage/rocks:** Nanite eliminates LOD transitions on dense geometry; enable it on
  high-poly rocks and detailed meshes (see `ue-nanite-and-rendering`).
- **PCG generate cost:** graph execution is async but can still spike on large volumes;
  trigger on load / pre-bake where possible; prefer `GenerateOnLoad` over `GenerateAtRuntime`
  for static content.
- **Landscape component count:** aim for ≤ 1024 components; each has a render-thread CPU
  cost. Prefer fewer, larger components over many small ones.
- **World Partition streaming:** landscape proxies stream by region; foliage uses a separate
  256 m grid (configurable in Project Settings → Instanced Foliage Grid Size).

## Gotchas

- **Invalid heightmap dimensions** — landscape widths/heights must follow
  `(N × ComponentQuads) + 1`; arbitrary resolutions will be rejected or silently resized.
  Use the recommended size table (Landscape Technical Guide).
- **Missing layer info objects** — painting a weight layer requires a `ULandscapeLayerInfoObject`
  asset assigned to the layer in the landscape material; without it the layer appears in the
  UI but cannot be painted.
- **Actor foliage at density** — `UFoliageType_Actor` instances spawn one actor per instance,
  not an HISM; high density is a performance cliff. Use `UFoliageType_InstancedStaticMesh`
  unless you need per-instance Blueprint logic.
- **HISM tree stale after edit** — `AddInstance` marks the tree dirty; until the async
  rebuild completes, the BVH is inconsistent; call `BuildTreeIfOutdated(false, true)` after
  bulk edits if you need it immediately.
- **Collision on all foliage** — enabling complex collision on dense grass/foliage is
  extremely expensive; disable collision or use simple sphere/capsule only for interactive
  foliage.
- **PCG generate at runtime carelessly** — calling `Generate()` mid-frame on a large volume
  can hitch; use the async path (`GenerateLocal`) and observe the delegate for completion.
- **Foliage in World Partition** — foliage instances live in `AInstancedFoliageActor`s that
  load per cell; painting across cell boundaries splits instances. Keep foliage within cells
  or use PCG for cross-cell content.
- **PCG verified from saved output** — generated resources persist in the map, so a broken input (a renamed label in a node's name-lookup setting, a deleted tagged actor) stays invisible until someone presses Generate. Verify graph changes, renames and test-level copies by regenerating and comparing per-mesh totals; isolating a graph in its own level: `references/pcg.md` → "Isolating a graph in its own test level".
- **Pivot-only exclusion tests** — wide scattered meshes overlap roads or paths whose visible mesh is wider than the spline. Test the whole mesh footprint against visible colliding geometry. See `references/pcg.md` → "Exclusion zones and attached dressing".
- **Procedural relief finer than ~2 landscape quads renders as pyramid tips and knife-edge crests** — the grid draws flat triangles between vertices, so a crest or bump curving over less than ~2 quads bends 20–40° from one triangle to the next. A 3×3 blur is not enough for crest/bank terms: low-pass noise detail at the grid spacing (lumps 3×3, ridges/banks 5×5 binomial, offsets = quad size), but **widen** point features such as pit/mound bumps (radius ≥ ~2.5 quads) instead of blurring them, because a blur flattens a narrow mound to a third of its height. Put it behind an opt-in setting when the generator is shared, and verify with a full-grid scan of tips **and** crease bends, not by eye: see `references/landscape.md` → "Procedural relief: finding and fixing sharp points".
- **Mountains judged by eye or by height alone.** Gaussian-blob-plus-noise ranges can match a real range's apparent height and still read fake: slopes are uniformly steep, and there are no valley floors, cliffs or drainage. Before proposing more height, benchmark them against a real DEM: slope distribution, flat fraction, max slope, skyline angle from story viewpoints, and a same-scale hillshade. Before warping a real DEM into the range at a uniform scale, check that the real relief within `band width / scale` of its crest gives the height you need: broad ranges gain most of their relief across wide foothills, so they fall short in a narrow game band. Then use separate along/across/vertical scales; never restore height by matching the old placeholder's peak envelope, because it lifts smooth shoulders that hide the real crest. Judge every variant by skyline peaks per 10° as well as angle. See `references/terrain-realism-benchmark.md`.
- **Mountain detail finer than the Landscape grid:** before placing asset-pack peak meshes, bake a detail normal and surface masks from a finer real DEM through the terrain's own warp. Pack meshes read as a patchwork against grid terrain. See `references/terrain-realism-benchmark.md` → "Sub-grid detail from a finer real DEM".
- **Landscape displacement is scaled by the actor's Z scale** — material `DisplacementScaling.magnitude` is multiplied by the landscape Z scale (100 by default), so give it centimetres / Z scale. Full recipe (height source, centre vs flat collision, cvar cost A/B): `references/landscape.md` → "Material displacement on a Nanite landscape".
- **Full-resolution scanned height maps displace into choppy cliffs** — sharp pebble/leaf edges become walls with the albedo stretched down them. Start at a few cm with the height sampled at a fixed coarse mip (`TMVM_MIP_LEVEL`, mip ~4), and judge from a very low camera at 1:1, not only a standing view.
- **Moving or renaming a map with a Nanite landscape fails to save** ("Illegal reference to private object … LandscapeNaniteMesh … belongs to an external map"): the generated Nanite mesh lives inside the map package and still points at the old one. Turn `bEnableNanite` off and save before the move; turn it on and save afterwards, because `ALandscapeProxy::PreSave` rebuilds the mesh in the new package.
- **Nanite landscape + LOD materials** — per-LOD material overrides (`PerLODOverrideMaterials`
  on `ALandscapeProxy`) do not apply to the Nanite mesh; use a single material that works
  at all distances.

## Version notes

- `UFoliageType_InstancedStaticMesh.NaniteOverrideMaterials` was added in UE5 for Nanite
  foliage support.
- `CleanupLocal(bool bRemoveComponents, bool bSave)` was deprecated in 5.6; use the
  `bRemoveComponents`-only overload (`PCGComponent.h`:232).
- `UPCGComponent.GenerationTrigger = GenerateAtRuntime` enables the runtime generation
  scheduler (new in 5.3+; scheduler policy expanded in 5.6/5.7).
- Landscape Edit Layers are stable since UE5; the underlying renderer classes
  (`ULandscapeEditLayerBase`) are Engine/Editor-only and should not be referenced from
  runtime game code.

## References & source material

Engine source (UE 5.8):
- `Runtime/Landscape/Classes/Landscape.h` — `ALandscape`:276 (extends `ALandscapeProxy`).
- `Runtime/Landscape/Classes/LandscapeProxy.h` — `ALandscapeProxy`:450,
  `LandscapeComponents`:682, `LandscapeMaterial`:604, `ComponentSizeQuads`:924,
  `SubsectionSizeQuads`:927, `NumSubsections`:930, `bEnableNanite`:491.
- `Runtime/Landscape/Classes/LandscapeComponent.h` — `ULandscapeComponent`:431.
- `Runtime/Landscape/Classes/LandscapeLayerInfoObject.h` — `ULandscapeLayerInfoObject`:59.
- `Runtime/Landscape/Classes/LandscapeSplineActor.h` — `ALandscapeSplineActor`:14.
- `Runtime/Foliage/Public/FoliageType.h` — `UFoliageType`:105.
- `Runtime/Foliage/Public/FoliageType_InstancedStaticMesh.h` — `UFoliageType_InstancedStaticMesh`:13.
- `Runtime/Foliage/Public/InstancedFoliageActor.h` — `AInstancedFoliageActor`:28.
- `Runtime/Foliage/Public/ProceduralFoliageComponent.h` — `UProceduralFoliageComponent`:42.
- `Runtime/Engine/Classes/Components/HierarchicalInstancedStaticMeshComponent.h` —
  `UHierarchicalInstancedStaticMeshComponent`:135, `AddInstance`:303, `AddInstances`:304,
  `RemoveInstance`:305, `UpdateInstanceTransform`:308, `BuildTreeIfOutdated`:330.
- `Plugins/PCG/Source/PCG/Public/PCGComponent.h` — `UPCGComponent`:112,
  `Generate()`:253, `Cleanup()`:257, `GenerateLocal()`:221, `GenerationTrigger`:327.
- `Plugins/PCG/Source/PCG/Public/PCGGraph.h` — `UPCGGraph`:332, `UPCGGraphInterface`:159.
- `Plugins/PCG/Source/PCG/Public/Data/PCGLandscapeData.h` — `UPCGLandscapeData`,
  `FPCGLandscapeDataProps` (layer weights, height-only mode, GPU sampling).
- `Plugins/PCG/Source/PCG/Public/Data/PCGPointData.h` — `UPCGPointData`.

Official docs (UE 5.8):
- Landscape Outdoor Terrain — <https://dev.epicgames.com/documentation/unreal-engine/landscape-outdoor-terrain-in-unreal-engine>
- Landscape Technical Guide — <https://dev.epicgames.com/documentation/unreal-engine/landscape-technical-guide-in-unreal-engine>
- Landscape Materials — <https://dev.epicgames.com/documentation/unreal-engine/landscape-materials-in-unreal-engine>
- Landscape Edit Layers — <https://dev.epicgames.com/documentation/unreal-engine/landscape-edit-layers-in-unreal-engine>
- Using Nanite with Landscapes — <https://dev.epicgames.com/documentation/unreal-engine/using-nanite-with-landscapes-in-unreal-engine>
- Open World Tools (Foliage) — <https://dev.epicgames.com/documentation/unreal-engine/open-world-tools-in-unreal-engine>
- Foliage Mode — <https://dev.epicgames.com/documentation/unreal-engine/foliage-mode-in-unreal-engine>
- Procedural Foliage Tool — <https://dev.epicgames.com/documentation/unreal-engine/procedural-foliage-tool-in-unreal-engine>
- PCG Framework — <https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-framework-in-unreal-engine>
- PCG Overview — <https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview>

Deep-dive references in this skill:
- [references/landscape.md](references/landscape.md) — component/section math, material layer
  setup, edit layers, splines, Nanite landscape, runtime queries.
- [references/foliage-and-hism.md](references/foliage-and-hism.md) — HISM internals, foliage
  type hierarchy, procedural foliage volumes, scalability, World Partition foliage.
- [references/terrain-realism-benchmark.md](references/terrain-realism-benchmark.md) — realism gap
  analysis of terrain/mountains against a real DEM: offline height decode and orientation, terrain-tile
  fetch, slope/flat/cliff metrics, skyline angles, same-scale hillshade, on-screen size of a grid cell
  per view (the by-scale split), USGS 3DEP projected-crop fetch, fitting a real range's profile into the
  game band, an offline real-DEM warp onto a crest arc (separate along/across/vertical scales, valley
  floor, protected blend, sightline buffer check), surface rules under vertical exaggeration, the
  the heightmap import round-trip check, crest cloud caps (volumetric first, cards as stopgap), placed peak
  meshes from asset packs (summit picking, sinking the flat tile base, patchwork/snow/cloud-cap integration), sub-grid detail
  normal and surface masks baked from a finer real DEM through the same warp, physical causes
  cloud caps and treeline, and turning the gaps into a plan.
- [references/pcg.md](references/pcg.md) — PCG graph authoring, element/settings subclassing,
  landscape data queries, runtime generation, partitioned generation, per-point material overrides,
  exclusion-zone footprint tests, attached base dressing (root flares), determinism digests.

Related skills: `ue-meshes-static-and-skeletal`, `ue-levels-and-world-partition`, `ue-nanite-and-rendering`.
