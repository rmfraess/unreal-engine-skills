# Material graph, domains, and authoring concepts — full reference

Deep dive for [../SKILL.md](../SKILL.md). Covers the material graph structure,
PBR input slots, material functions, static switches, material attributes, the
Custom (HLSL) node, layered materials, and a note on Substrate. Grounded in UE 5.8
(`Engine/Source/Runtime/Engine/Public/Materials/Material.h`,
`MaterialFunctionInterface.h`, `MaterialDomain.h`) and the official
[Material Properties](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-material-properties)
and [Material Functions](https://dev.epicgames.com/documentation/unreal-engine/material-functions-in-unreal-engine)
docs.

## The material result node (PBR inputs)

Every `UMaterial` has a single root **Material Result** node with input pins.
The set of active pins depends on the chosen domain, shading model, and blend
mode. The primary PBR inputs for `MD_Surface` + `MSM_DefaultLit`:

| Input pin | Data type | Purpose |
|---|---|---|
| Base Color | float3 (RGB) | albedo / diffuse reflectance |
| Metallic | float (0–1) | dielectric (0) to conductor (1) |
| Specular | float (0–1) | non-metal specular adjustment (default 0.5) |
| Roughness | float (0–1) | micro-surface roughness |
| Emissive Color | float3 (HDR) | self-illumination; drives bloom |
| Normal | float3 (tangent-space) | per-pixel normal perturbation |
| World Position Offset | float3 | vertex displacement in world space |
| Opacity / Opacity Mask | float (0–1) | translucency or alpha-cut weight |
| Ambient Occlusion | float (0–1) | static AO baked into mesh or textures |
| Refraction | float | IOR for `BLEND_Translucent` |
| Custom Data 0 / 1 | float | shading-model-specific extra data |

Only `MSM_Unlit` removes lighting calculations entirely (only Base Color and
Emissive are meaningful). Subsurface/SkinProfile models add scatter radius
inputs. Hair and Eye models expose strand/limbus-specific inputs.

## Material domains in depth

`EMaterialDomain` (defined in `Public/MaterialDomain.h`:12) controls what the
material is evaluated for:

- **`MD_Surface`** — the default. Evaluated per-pixel on meshes via the G-buffer
  (deferred) or directly (forward). All PBR inputs apply.
- **`MD_DeferredDecal`** — projected onto surfaces. Blend mode is controlled by
  `DecalBlendMode` (`Material.h`:489), not `BlendMode`. Decals can write to
  specific G-buffer channels.
- **`MD_LightFunction`** — multiplied into a light's output. Only `Emissive Color`
  is used. Attach to a `ULightComponent` as a light function.
- **`MD_PostProcess`** — used by `FPostProcessSettings::AddBlendable`. Reads the
  scene color via `SceneTexture` expressions. Domain must be Post Process.
- **`MD_UI`** — evaluated in screen-space for UMG/Slate widgets. No lighting.
  Only Base Color / Emissive / Opacity are meaningful.
- **`MD_Volume`** — evaluated inside a volume primitive for heterogeneous effects
  (smoke, fire). Pairs with `USparseVolumeTexture` sampling.

Changing domain changes which G-buffer writes and render passes the material
participates in.

## Material functions (`UMaterialFunctionInterface`)

A **Material Function** (`Public/Materials/MaterialFunctionInterface.h`:58) is a
saved subgraph that appears as a single node in any material graph. Use them to:
- Share complex node networks (e.g. a triplanar projection, a Fresnel calculation,
  a PBR blend) across many materials.
- Reduce per-material maintenance — a bug fix in the function propagates to all
  materials using it.
- Abstract advanced HLSL or multi-step math behind a named interface.

Functions expose **FunctionInput** and **FunctionOutput** pins. They are stored as
`.uasset` files and referenced via `Material Functions → Add Function Call` in the
graph. The engine ships with a large library of built-in functions (Blends,
Gradients, Math, Texturing, World Position Offset, etc.).

Source: `Public/Materials/MaterialFunctionInterface.h` — `UMaterialFunctionInterface`:58
(stores the function graph; `GetInputs`, `GetOutputs`).

## View-dependent UV relief

Use this sequence for a bounded surface-depth experiment, not as proof that a whole asset is realistic.

1. Inspect the saved broad-face UVs and every shared material user, including backing and reveals. Derive physical distance per UV unit on each axis; a plank face and a square test plane rarely share the same mapping. Record approximations where clipped widths or secondary projections differ.
2. Prepare a bounded scalar height input sampled in linear space from its declared channel. Keep authored height distinct from measured scan data or an inferred normal-to-height reconstruction. Preserve repeat boundaries and neutral seam margins; verify that the chosen offset cannot sample unintended neighbouring regions.
3. Probe native pins before creating package assets. In UE 5.8, create expressions on a transient `unreal.Material()` and call `MaterialEditingLibrary.get_material_expression_input_names(expression)` with one argument. `MaterialExpressionBumpOffset` exposes `Coordinate`, `Height`, `HeightRatioInput`; the native Texture Sample coordinate pin is `UVs`. Verify the installed names instead of wiring an editor display label by guess.
4. Start with the native BumpOffset node when a simple parallax test answers the question. Sample height at unshifted UV0, feed R into `Height`, and use one scalar ratio with zero as the OFF control. Its reference plane defaults to 0.5. In UE 5.8 the node adds tangent-camera XY multiplied by `(height - reference) * ratio`; it does not divide by view Z. Treat the ratio as an artistic UV control, not calibrated centimetres or raymarched POM.
5. Correct anisotropy on the **offset**, not the original mapping. If one U unit spans `L_u` metres and one V unit spans `L_v`, use `UV_final = UV0 + (UV_bump - UV0) * float2(1, L_u / L_v)`. Sample the same BaseColor, Normal and Roughness through `UV_final` on both controls. This nominal correction remains approximate where a shared slot has different UV metrics.
6. Finish instance usage/shader/resource readiness using the main skill's verification sequence. Compare matched player-height, detail and oblique views under existing lighting. Texture displacement between stills proves neither convincing cupping nor the absence of motion swimming; test camera motion separately when that claim matters.

A technically working BumpOffset test may yield little visible benefit. Report that negative result without promoting it or concluding all PBR relief is impossible. POM, displaced self-shadowing, silhouettes and collision are separate mechanisms and acceptance claims; choose a further experiment only under the next agreed scope.

Installed-source entry points: `Runtime/Engine/Public/Materials/MaterialExpressionBumpOffset.h`, `Runtime/Engine/Private/Materials/MaterialExpressions.cpp`, and `Editor/MaterialEditor/Public/MaterialEditingLibrary.h`.

## Static Switch parameters

A `StaticSwitchParameter` node chooses between two input paths at **compile
time**. The chosen branch is inlined into the shader; the other is eliminated
entirely — zero runtime branch cost.

```
[If TRUE path]  →|
                  StaticSwitch → downstream
[If FALSE path] →|
```

Each unique combination of static parameter values across all child MICs produces
a separate compiled shader variant (permutation). With N independent static
switches you can have up to 2^N permutations. Keep the set of actually-used
combinations small — even a dozen unused permutations waste compile time and disk.

**Static Component Mask Parameter** is a similar node that selects which RGBA
channel(s) to pass through, also resolved at compile time.

## Material attributes — layer-friendly wiring

The `MakeMatAttributes` and `BreakMatAttributes` nodes pack/unpack all surface
input slots into a single `FMaterialAttributes` struct pin. Benefits:
- Pass a full attribute set between material functions in a single wire.
- Use `BlendMaterialAttributes` to lerp between two attribute sets (e.g. dry
  and wet surfaces).
- Required by layered materials (Material Layers) when building layer functions.

Material attributes do not change the compiled output — they are a graph-topology
convenience.

## Custom (HLSL) node

The **Custom** expression node lets you write inline HLSL. Use it for:
- Algorithms with no built-in node equivalents.
- Optimized math that collapses many nodes into fewer instructions.
- Interfacing with custom shader includes (`.ush` files in a plugin's Shaders/
  directory).

Each Custom node input is a named HLSL parameter. The return type matches the
node's output. The code runs inside the pixel shader's generated function and
has access to standard HLSL types but not to global state outside what UE passes
in.

Custom node code is not validated by the material compiler until it is compiled.
Syntax errors produce a compile failure at shader compile time, not at save.

Avoid using Custom nodes for trivial math — node-graph equivalents are better
optimized by the material translator.

## Layered materials and Substrate (UE 5.8)

**Material Layers** (non-Substrate path) allow stacking multiple material
functions, each providing a full attribute set, blended by a Layer Blend function.
This is the predecessor to Substrate.

**Substrate** (opt-in project setting in UE 5.8) replaces the shading model and
blend mode selectors with a physically-based **slab** model. Each slab node
describes one material layer with its own scattering and transmittance properties.
Slabs are combined with operators (over, add, mix). The C++ runtime parameter
API (`UMaterialInstanceDynamic::Set*ParameterValue`) is identical — Substrate
only changes the graph-authoring model, not the instance API.

When Substrate is enabled:
- `EMaterialShadingModel::MSM_Strata` (hidden in non-Substrate mode) becomes
  the active shading model.
- `BLEND_TranslucentColoredTransmittance` and related Substrate-only blend modes
  are exposed.
- Existing non-Substrate materials can be migrated using the provided conversion
  utilities.

For most C++ gameplay code that only calls `Set*ParameterValue`, Substrate is
transparent — the same calls work on either path.

## Shader compilation overview

The material graph is translated to HLSL by the Material Compiler
(`Public/MaterialCompiler.h`). Compilation:
1. The graph is traversed; each expression node emits HLSL code fragments.
2. The translator assembles per-shader-frequency (vertex/pixel/compute) programs.
3. The HLSL is compiled per render backend (D3D12, Vulkan, Metal, etc.) by
   `FShaderCompilerWorker` (offline, asynchronous).
4. Compiled bytecode is stored in the Derived Data Cache (DDC) and on disk in
   the shader cache.

Each unique combination of (base material × static parameter values × enabled
usage flags × target platform) is one shader permutation. The permutation count
multiplies across all dimensions — the biggest practical source of long compile
times.

The **PSO Precache** system (UE 5.4+, present in 5.8) precompiles Pipeline State
Objects at load time instead of on first draw, eliminating in-game hitches.
Materials can opt into precaching via `PSOPrecacheMaterial.h`.
