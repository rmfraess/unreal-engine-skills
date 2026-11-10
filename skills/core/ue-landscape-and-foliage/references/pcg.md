# PCG (Procedural Content Generation) — deep reference

Deep dive for [../SKILL.md](../SKILL.md). Covers PCG graph authoring, custom node
implementation, landscape data queries, runtime generation, and partitioned generation.
Grounded in UE 5.8 (`Engine/Plugins/PCG/Source/PCG/Public/`) and the official
[PCG Framework](https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-framework-in-unreal-engine)
and [PCG Overview](https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview)
docs.

## Architecture overview

PCG is a shipped plugin (`Engine/Plugins/PCG/`). The data flow:

```
Actor + UPCGComponent ──▶ UPCGGraph (nodes/edges) ──▶ UPCGData outputs
                                                        └── ISM components / Actors (resources)
```

Each node in the graph is a `UPCGNode` with a `UPCGSettings` object that defines the node's
type, properties, and I/O pin types. At execution time, a `UPCGElement` subclass processes
an `FPCGContext` (containing input `UPCGData` collections) and produces outputs.

## Core types

| Type | Path | Notes |
|---|---|---|
| `UPCGComponent` | `PCGComponent.h`:112 | Runs a graph; attached to any actor |
| `UPCGGraph` | `PCGGraph.h`:332 | Editable graph asset (nodes + edges) |
| `UPCGGraphInterface` | `PCGGraph.h`:159 | Abstract; `UPCGGraph` and `UPCGGraphInstance` both implement |
| `UPCGGraphInstance` | `PCGGraph.h`:879 | Graph + local parameter overrides |
| `UPCGNode` | `PCGNode.h` | A node in the graph; has a `UPCGSettings` |
| `UPCGSettings` | `PCGSettings.h` | Defines node type, properties, pin descriptors |
| `UPCGElement` | `PCGElement.h` | Stateless executor; `Execute(FPCGContext*)` produces outputs |
| `UPCGData` | `PCGData.h` | Base for all data flowing through the graph |
| `UPCGPointData` | `Data/PCGPointData.h` | Point cloud — primary per-instance data |
| `UPCGLandscapeData` | `Data/PCGLandscapeData.h` | Landscape surface + layer weights |
| `UPCGManagedResource` | `PCGManagedResource.h` | Wrapper around a generated resource (ISM, actor) |
| `UPCGSubsystem` | (not in Public/) | World subsystem that dispatches graph execution |

## `UPCGComponent` generation lifecycle

```
UPCGComponent::Generate(bForce)       — schedules graph execution (replicated, netmulticast)
UPCGComponent::GenerateLocal(bForce)  — local-only, delayed, not replicated (Blueprint-callable)
UPCGComponent::Cleanup(bRemoveComponents) — destroys all managed resources
UPCGComponent::CleanupLocal(...)          — local-only cleanup
UPCGComponent::CancelGeneration()         — abort in-progress generation
```

**Delegates for completion:**
```cpp
// Registered before calling Generate():
PCGComp->OnPCGGraphGeneratedExternal.AddDynamic(this, &AMyActor::OnPCGGenerated);
PCGComp->OnPCGGraphCleanedExternal.AddDynamic(this, &AMyActor::OnPCGCleaned);
```

**Generation trigger** (`EPCGComponentGenerationTrigger`, `PCGComponent.h`:77):

| Enum | When generation runs |
|---|---|
| `GenerateOnLoad` | Once when the component loads; standard for static content |
| `GenerateOnDemand` | Only when `Generate()` is called explicitly from code/Blueprint |
| `GenerateAtRuntime` | Scheduled by `UPCGSubsystem` runtime scheduler as the player moves |

**Partitioned generation** (`bIsComponentPartitioned = true`): the component is split into
a grid of local PCG components dispatched per World Partition cell. The grid size is set
on the `APCGWorldActor` (or by the graph's Hierarchical Generation setting). Partitioned
generation enables async streaming of generated content alongside the world.

## Landscape data in PCG

`UPCGLandscapeData` (`Data/PCGLandscapeData.h`) is populated by the graph's `Landscape`
input pin when `EPCGComponentInput::Landscape` is set, or via an explicit `Get Landscape
Data` node. It exposes:

- **Height** — Z position at each sample point.
- **Normal / Tangent** — surface normal (controlled by `bGetHeightOnly`; disable to get
  normals, enable for height-only speed optimization).
- **Layer weights** — per-landscape-layer float attributes on each point; enabled by
  `bGetLayerWeights = true` (`FPCGLandscapeDataProps`).
- **Physical material** — surface material per point (`bGetPhysicalMaterial`).
- **GPU sampling** — `bSampleVirtualTextures` uses virtual textures for faster GPU-side
  landscape sampling (requires virtual textures to be baked on the landscape).

Typical pattern — filter scatter points to slope and grass-layer weight:

```
[Landscape Surface Sampler] → [Attribute Filter: Normal.Z > 0.85] →
[Attribute Filter: GrassLayer > 0.5] → [Static Mesh Spawner: Tree mesh]
```

From C++, access landscape data on the component:

```cpp
UPCGData* LandscapeData = PCGComp->GetLandscapePCGData();     // sampled as surface
UPCGData* HeightData    = PCGComp->GetLandscapeHeightPCGData(); // height-only variant
```

## Authoring a custom PCG node (C++)

1. **Settings class** — subclass `UPCGSettings`. Override `GetInputPinProperties`,
   `GetOutputPinProperties`, and `CreateElement()`. Properties on the settings class appear
   in the graph node's Details panel.

2. **Element class** — subclass `UPCGElement`. Implement `Execute(FPCGContext* Context)`.
   The context provides input collections; produce outputs via `Context->OutputData`.

```cpp
// Minimal custom PCG element skeleton (illustrative):
class MYGAME_API UMyScatterSettings : public UPCGSettings
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category = Settings)
    float MinSlope = 0.f;

    UPROPERTY(EditAnywhere, Category = Settings)
    float MaxSlope = 30.f;

protected:
    virtual TArray<FPCGPinProperties> InputPinProperties() const override;
    virtual TArray<FPCGPinProperties> OutputPinProperties() const override;
    virtual FPCGElementPtr CreateElement() const override;
};

class FMyScatterElement : public FSimplePCGElement
{
protected:
    virtual bool ExecuteInternal(FPCGContext* Context) const override;
};
```

`FSimplePCGElement` provides default loop boilerplate for single-input → single-output
nodes. For multi-input/complex graphs, implement `UPCGElement` directly.

## Runtime generation pattern

For environments that stream at runtime (open world), use `GenerateAtRuntime` with a
partitioned PCG component on a persistent actor. The `UPCGSubsystem` scheduler handles
loading/unloading cells as the player moves.

```cpp
// Setting up a runtime-generating PCG component in C++:
UPROPERTY(VisibleAnywhere)
TObjectPtr<UPCGComponent> PCGComp;

AMyWorldManager::AMyWorldManager()
{
    PCGComp = CreateDefaultSubobject<UPCGComponent>(TEXT("PCGComponent"));
    PCGComp->GenerationTrigger = EPCGComponentGenerationTrigger::GenerateAtRuntime;
    PCGComp->bIsComponentPartitioned = true;
}

void AMyWorldManager::BeginPlay()
{
    Super::BeginPlay();
    if (PCGComp && PCGComp->GetGraph())
    {
        // Runtime scheduler handles generation automatically;
        // manual trigger only needed for on-demand changes:
        PCGComp->NotifyPropertiesChangedFromBlueprint(); // dirty → regenerate
    }
}
```

## Managed resources

PCG tracks every ISM component and spawned actor it creates as a `UPCGManagedResource`
(subclasses: `UPCGManagedComponent`, `UPCGManagedActors`). On `Cleanup()`, all managed
resources are destroyed. If you want to detach generated content from the PCG component
(so `Cleanup` no longer affects it), call `ClearPCGLink(TemplateActorClass)` which moves
managed resources to a new standalone actor.

## Per-point material overrides

To give one Static Mesh Spawner different materials per mesh (for example, project-local instances over shared vendor meshes), write a `FSoftObjectPath` (or `FString`) attribute per point in the producing node. Then on the spawner's `PCGMeshSelectorByAttribute` set `bUseAttributeMaterialOverrides = true` and `MaterialOverrideAttributes = ["<AttrName>"]` (one name per material slot).

- When a data set lacks the attribute, PCG logs only a Warning (`Attribute '<X>' for material overrides is not present`) and spawns with mesh defaults. Treat that warning as "the override never reached this data" and check the producer, because the Generate still completes.
- A point with an empty path gets a null override, and a null override falls back to the mesh's own material. Unrelated items on the same pin (logs next to rocks) can therefore leave the attribute empty.
- Verify the result by reading `ISMComponent.get_material(0)` per mesh after Generate. The settings readback alone proves nothing.

## Exclusion zones and attached dressing

- **Test the whole footprint, not the pivot.** A pivot-only test against a road or other exclusion lets wide meshes (boulders, logs, root plates) overlap it. The *visible* road mesh can also be wider than the spline width plus margin. Sample the mesh bounds 3x3 at the final placement transform, and cache bounds per asset. Exempt small floor litter that should bank against the edge.
- **Verify against what the player sees.** Trace or overlap only the visible, colliding road components. Hidden placeholder splines give false hits. Run a control count of samples that should hit, so you know a zero result isn't a broken check.
- **Attached base dressing (root flares, collars):** emit the companion point in the same accept pass as its parent, on a separate pin. Put it at ground Z rather than the parent's sunk pivot, and use the parent's yaw only, so a leaning trunk keeps its flare flat. Scale it by the parent scale × (measured trunk radius / authored radius).
- **Shrink before dropping.** When a companion fails the exclusion test, retry at a smaller spread (for example 1.0 → 0.7 → 0.45 in XY only) before skipping it, since a short flare reads better than a bare trunk.
- **Measure source meshes before sizing companions.** Read vertices with `GeometryScript_MeshQueries.get_all_vertex_positions`, then `GeometryScript_List.convert_vector_list_to_array`, and take a near-ground Z band. On low-poly trunks with one sparse ring per band, use the band's XY extent / 4; a median distance from the centre is meaningless with that few vertices.
- **Prove determinism.** Run Cleanup and Generate twice at fixed settings and compare an instance digest (mesh + rounded transforms). Equal digests mean later before/after comparisons are trustworthy.

## Isolating a graph in its own test level

To iterate a PCG graph in a smaller dedicated level (a forest-only bench copied from a busier test map):

1. **Inventory what the graph reads from the world before deleting anything.** List every node's actor selector (`actor_selection`, tag, `select_multiple`) and read custom elements' source for `TActorIterator` lookups by tag **or by actor name/label** (e.g. `GetActorNameOrLabel() == Settings->SomeLandscape`), ground-mesh tags, clearing/exclusion tags and hard-coded asset loads. Keep exactly those actors plus lighting; everything else can go.
2. **Copy by Save As, then relaunch on the copy** (see `ue-editor-scripting-and-python` → map copy): `save_map(world, NewPath)`, quit with nothing dirty, relaunch with `-Map NewPath`, then delete the unused actors and save.
3. **Record the source's saved output first:** ISM instance totals per mesh and `InstancedSkinnedMeshComponent` instance totals (skinned spawner output is not in the ISM count).
4. **Generate in the copy with `auto_save=false`,** wait, and compare per-mesh totals. Read the custom nodes' own log lines (accepted/removed counts) to find which node lost input; a mesh family dropping to 0 with no PCG error means an input lookup silently found nothing.
5. **Check side effects before saving:** list dirty content packages after Generate. Custom nodes can write shared assets (masks, textures, landscape relief); save only the level package and restore any shared asset the copy wrote.
6. **Judge the look after a cold load,** not right after Generate: freshly generated masked foliage can render as opaque squares until streaming settles.

## Common pitfalls

- **Verify a graph by running Generate, not by comparing saved output.** Generated resources persist in the map, so a rename or input change that breaks the graph is invisible until someone regenerates. After any rename/move/input change, regenerate (in a copy or with `auto_save=false`) and compare per-mesh totals.
- **Name-based actor lookups in node settings break on label renames.** A setting holding an actor label string (`RoadLandscape`, `ReliefLandscape`) is not a reference, so redirectors and reference fix-ups miss it and the lookup silently returns null. Prefer tags; when a name field exists, include node settings in the rename's text sweep.

- **Large-volume synchronous generation** — calling `Generate()` on a 1 km² PCG volume at
  runtime blocks the game thread; use async paths and `GenerateAtRuntime` with the scheduler.
- **Graph parameter type mismatch** — overriding a graph parameter with the wrong type in a
  `UPCGGraphInstance` is silently ignored; verify types match in the graph's parameter
  definitions.
- **Landscape tracking** — if your graph samples a landscape, the component automatically
  tracks landscape changes and regenerates. Disable with `bIgnoreLandscapeTracking` if you
  want to control regeneration manually.
- **No cleanup before re-generate** — calling `Generate()` when the graph is already
  generated appends more resources instead of replacing them; call `Cleanup()` first or
  set `bForce = true`.
- **PCG in packaged builds** — confirm the PCG plugin is added to `.uproject` with
  `"Enabled": true`; it is a shipped plugin but not enabled by default in all templates.

## Key source paths (UE 5.8)

All under `Engine/Plugins/PCG/Source/PCG/Public/`:
- `PCGComponent.h`:112 — `UPCGComponent`; `Generate`:253, `Cleanup`:257,
  `GenerateLocal`:221, `CleanupLocal`:232, `NotifyPropertiesChangedFromBlueprint`:264,
  `GenerationTrigger`:327, `bIsComponentPartitioned`:324,
  `OnPCGGraphGeneratedExternal`:393, `OnPCGGraphCleanedExternal`:396.
- `PCGGraph.h`:332 — `UPCGGraph`; `:159` — `UPCGGraphInterface`; `:879` — `UPCGGraphInstance`.
- `PCGSettings.h` — `UPCGSettings` (node settings base).
- `PCGElement.h` — `UPCGElement`, `FSimplePCGElement`.
- `PCGContext.h` — `FPCGContext` (input/output data collections).
- `Data/PCGLandscapeData.h` — `UPCGLandscapeData`, `FPCGLandscapeDataProps`
  (bGetHeightOnly, bGetLayerWeights, bGetPhysicalMaterial, bSampleVirtualTextures).
- `Data/PCGPointData.h` — `UPCGPointData`.
- `PCGManagedResource.h` — `UPCGManagedResource`.
- `Elements/Landscape/PCGWaitLandscapeReady.h` — utility element for landscape readiness.
