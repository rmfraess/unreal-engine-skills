# Data Interfaces and performance — full reference

Deep dive for [../SKILL.md](../SKILL.md). Covers the Data Interface catalog, CPU/GPU simulation
details, scalability settings, and the Niagara Debugger. Grounded in UE 5.8
(`Engine/Plugins/FX/Niagara/Source/Niagara/Classes/NiagaraDataInterface.h`,
`Classes/NiagaraDataInterfaceSkeletalMesh.h`, `Public/NiagaraFunctionLibrary.h`) and the
official [Debugging and Optimization in Niagara](https://dev.epicgames.com/documentation/unreal-engine/debugging-and-optimization-in-niagara-effects-for-unreal-engine)
and [Collisions in Niagara](https://dev.epicgames.com/documentation/unreal-engine/collisions-in-niagara-for-unreal-engine)
docs.

## Data Interface base class

`UNiagaraDataInterface` (`NiagaraDataInterface.h`) is the abstract base. All concrete DIs
derive from it and register functions that HLSL modules can call. On the CPU path those
functions are bound to C++ `VectorVM` external functions; on the GPU path they generate HLSL
that is compiled into the emitter's compute shader.

A DI is an **asset reference** carried by a User Parameter of type `Data Interface`. You bind a
concrete object (e.g. a `USkeletalMeshComponent`) at runtime either via a User Parameter or via
a `UNiagaraFunctionLibrary` helper.

## Data Interface catalog (UE 5.8)

### Geometry

| DI | Source class | Key capabilities |
|---|---|---|
| Skeletal Mesh | `UNiagaraDataInterfaceSkeletalMesh` | Sample triangles, bones, sockets; read bone transforms; emit from skin surface |
| Static Mesh | `UNiagaraDataInterfaceStaticMesh` | Sample static mesh triangles; volume or surface distribution |
| Spline | `UNiagaraDataInterfaceSpline` | Distribute along `USplineComponent`; sample position/tangent/up by distance or fraction |
| Physics Asset | `UNiagaraDataInterfacePhysicsAsset` | Sample physics bodies from a `UPhysicsAsset` (ragdolls, cloth) |

### Rendering / texture

| DI | Key capabilities |
|---|---|
| Texture 2D | Sample a `UTexture2D` by UV; use as a spawn mask, velocity field, or color ramp |
| Texture 2D Array | Flip-book arrays; animated decals |
| Volume Texture | 3D density/velocity fields; smoke advection |
| Render Target 2D | Read/write a `UTextureRenderTarget2D`; feedback loops, trails-to-texture |

### Collision

| DI | CPU/GPU | Mechanism |
|---|---|---|
| Collision Query | CPU and GPU paths | CPU VM geometry queries; GPU shader path uses the scene data required by the DI |
| Async Gpu Trace | GPU only | Latent GPU scene traces; the provider can require a ray-tracing scene |
| GPU Collision (Distance Field/Depth Buffer) | GPU | Distance-field or screen-space depth collision; view/platform dependent |
| HWRT Collision | GPU, Experimental | Hardware ray-tracing collision; requires a supported DXR configuration |

### Utility

| DI | Key capabilities |
|---|---|
| Curve Float/Vector/Color | Sample UCurveFloat/UCurveVector/UCurveLinearColor by time or parameter |
| Audio | Sample FFT/envelope from a `USoundWave`; react to music or dialog |
| Actor Component | Reference a `USceneComponent`; read its world transform |
| Camera | Access the active camera transform and FOV |
| Neighbor Grid 3D | Voxel spatial hash; neighbor queries for flocking, fluid |
| Grid 2D/3D Collection | General 2D/3D array storage on the GPU; fluid simulations |
| Niagara Data Channel | Cross-system particle communication (see below) |

## Binding DIs from C++

```cpp
// Bind a skeletal mesh component to a DI User Parameter named "CharacterMesh":
UNiagaraFunctionLibrary::OverrideSystemUserVariableSkeletalMeshComponent(
    FX,                   // UNiagaraComponent*
    TEXT("CharacterMesh"),
    GetMesh());           // USkeletalMeshComponent*

// Bind a static mesh component to a DI User Parameter named "Surface":
UNiagaraFunctionLibrary::OverrideSystemUserVariableStaticMeshComponent(
    FX, TEXT("Surface"), GroundMesh);

// Bind a texture:
UNiagaraFunctionLibrary::SetTextureObject(
    FX, TEXT("MaskTex"), MyTexture2D);
```

These helpers write to the component's override parameter store; the DI is updated on the next
tick. The DI name must match the User Parameter name exactly.

## Niagara Data Channels (5.3+)

Data Channels (`NiagaraDataChannel.h`) allow multiple Niagara Systems to share data without
direct component coupling. One system writes particle data to a named channel; another system
reads from it in the same or next frame.

```cpp
// Access a Data Channel from C++ with the UE 5.8 access-context API:
#include "NiagaraDataChannelFunctionLibrary.h"
#include "NiagaraDataChannelAccessContext.h"

FNDCAccessContextInst AccessContext;
AccessContext.Init(TNDCAccessContextType(FNDCAccessContext::StaticStruct()));
FNDCAccessContext& Context = AccessContext.GetChecked<FNDCAccessContext>();
Context.Location = GetActorLocation(); // world-space location in this AActor example
Context.bOverrideLocation = true;

// Begin a write of one element to a channel asset; fill fields via the returned writer:
UNiagaraDataChannelWriter* Writer =
    UNiagaraDataChannelLibrary::WriteToNiagaraDataChannel_WithContext(
        this,
        ExplosionsChannel,                  // UNiagaraDataChannelAsset*
        AccessContext,
        /*Count*/ 1,
        /*bVisibleToBlueprint*/ true,
        /*bVisibleToNiagaraCPU*/ true,
        /*bVisibleToNiagaraGPU*/ true,
        TEXT("MyGame"));
```

Data Channels facilitate communication between game code and Niagara, or between Niagara
systems, and can combine work into a shared simulation. They are not a blanket replacement for
Data Interfaces: use a DI when a system samples an external object/source, and use a Data Channel
when decoupled publishers/readers need shared data. Prefer the access-context API above for new
UE 5.8 code; the SearchParameters overload is retained for legacy compatibility.

## CPU vs GPU: detailed trade-offs

### CPU emitter

- Simulates on the game thread via the VectorVM (vectorized CPU runtime).
- Per-particle data is accessible to gameplay: you can read `Particle.Position`,
  listen for Niagara events, trigger Blueprint callbacks.
- Collision uses `UWorld::LineTrace*`, which respects full physics (complex collision,
  procedural meshes, destructibles).
- There is no engine-wide particle-count cutoff; measure the selected modules, data interfaces,
  collision path, and target frame budget with `stat Niagara`/the Niagara Debugger.
- Use `stat Niagara` → `NiagaraGameThread_*` counters to measure.

### GPU emitter

- Simulates on the render thread as a compute shader via the `FNiagaraGpuComputeDispatchInterface`.
- Game thread has no direct access to per-GPU-particle data; there is no per-particle event
  callback from GPU emitters to gameplay.
- Can use GPU-supported distance-field/depth-buffer paths or the separate async GPU trace path;
  do not promise CPU-style complex-mesh traces or gameplay callbacks from GPU particles.
- Can support very large particle counts on suitable hardware, but dispatch, render-thread/GPU,
  memory, and renderer costs still apply; do not treat GPU simulation as zero total cost.
- Use `stat Niagara` → `NiagaraRenderThread_*` and Unreal Insights GPU track.

### Mixed systems

A single `UNiagaraSystem` can contain both CPU and GPU emitters. Emitters do not share particle
data across the CPU/GPU boundary directly. Use Data Channels or User Parameters to pass
information from CPU emitters to GPU emitters (e.g. passing the player position as a User
Parameter so GPU particles can repel from the player).

## Scalability and culling

Niagara integrates with the scalability system via `UNiagaraEffectType` assets assigned to each
`UNiagaraSystem`. The effect type defines:

- **Visibility culling** — cull if occluded for N ms.
- **Distance culling** — cull beyond a world-space radius.
- **Instance count limiting** — cap the number of concurrent instances.
- **Quality levels** — reduce particle counts or disable emitters at lower scalability tiers.

The `UNiagaraComponent::SetAllowScalability(false)` call exempts a specific component from
culling (e.g. first-person effects or locally important player VFX).

`SpawnSystemAtLocation`/`SpawnSystemAttached` with `bPreCullCheck = true` apply the system's
effect type rules **before** allocating the component; they return `nullptr` if the effect would
be immediately culled. This avoids the cost of spawning an effect that the engine would cull
on the first tick.

## The Niagara Debugger

The Niagara Debugger (editor: Window → Niagara Debugger, or `showdebug niagara` in-game)
provides:

- Live particle count and simulation time per system instance.
- Parameter store inspection — read active User Parameter values.
- Emitter enable/disable toggles for isolating behaviors.
- GPU dispatch counts and timing.
- Scalability state for each active component.

`stat Niagara` in the console gives aggregate timing. For deeper profiling, Unreal Insights
(CPU track: `NiagaraGameThread`, GPU track: compute dispatches) shows the full call chain.

## Common performance mistakes

- **CPU emitter with a measured budget overrun** — VectorVM and data-interface work scale with
  the selected workload. Profile with `stat Niagara`/the Niagara Debugger and move work to GPU
  only when the target platform and feature set support that trade-off; there is no universal
  `~10k` switch point.
- **Many distinct system instances** — each instance has per-tick overhead independent of
  particle count. Pool small-burst effects with `ENCPoolMethod::AutoRelease`.
- **Unbound skeletal mesh DI** — if the DI's mesh reference is null, the emitter may spawn
  zero particles or assert. Always ensure the DI binding is set before `Activate()`.
- **GPU emitter requesting gameplay collision** — distance-field only; no complex-collision
  support on GPU. Use CPU if you need exact collision response.
- **Unlimited instances** — without an `UNiagaraEffectType`, there is no instance cap.
  Assign an effect type to all systems that may be spawned repeatedly.
