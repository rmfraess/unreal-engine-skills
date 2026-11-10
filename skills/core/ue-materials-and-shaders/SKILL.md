---
name: ue-materials-and-shaders
description: >-
  Author and drive Unreal materials — UMaterial (the node graph asset), material
  instances (UMaterialInstanceConstant for editor-authored variants, UMaterialInstanceDynamic
  for runtime parameter changes), material domain (Surface/Deferred Decal/Light Function/Post
  Process/UI/Volume), shading models (Default Lit/Unlit/Subsurface/Clear Coat/Hair/Cloth/Eye),
  blend modes (Opaque/Masked/Translucent/Additive), scalar/vector/texture parameters,
  material functions, material parameter collections (global values), and
  the material C++ API (CreateDynamicMaterialInstance, Set*ParameterValue, UKismetMaterialLibrary). Use when
  creating materials, making parameterized variants, changing material parameters at runtime,
  setting global weather or world-state parameters, fixing material shader permutation count
  or translucency overdraw, cross-referencing the UMaterial/instance hierarchy, or diagnosing
  default-material fallback from a missing usage flag. Also for Volumetric Cloud materials.
metadata:
  engine-version: "5.8"
  category: content-assets
---

# Materials & shaders

For graph-specific effects, use `ue-material-graph-effects`. For reusable PBR graph structure and texture contracts, use `ue-master-material-authoring`. For terrain shading, use `ue-auto-landscape-materials` or `ue-landscape-rvt-and-grass` as appropriate.

For generated tissue or other large organic surfaces, see
[organic surface projection and seam diagnosis](../ue-importing-content/references/organic-surfaces-and-material-sections.md).
Distinguish UV seams, image-border wrapping and split mesh normals before changing
the shader; retain approved lighting and material appearance on unaffected assets.

UE materials are node graphs that compile to HLSL shaders. The central
workflow idea is **parameters + instances**: one parameterized base material,
cheap asset variants (constant instances), and runtime-tweakable copies
(dynamic instances). Understanding where to put logic — parameter vs. static
switch vs. separate material — determines both quality and compile cost.

## When to use this skill

- Creating a material or family of material variants from a shared base.
- Changing material parameters at runtime (damage tint, team color, wetness,
  dissolve amount).
- Choosing domain, shading model, or blend mode for a material.
- Fixing shader permutation counts or translucency overdraw performance issues.
- Setting world-wide values through a material parameter collection.
- Cross-referencing `UMaterial`, `UMaterialInstance`, `UMaterialInstanceDynamic`,
  or `UMaterialParameterCollection` in C++.

## The material class hierarchy

```
UObject
└── UMaterialInterface          (abstract base; common API for all material types)
    ├── UMaterial               (the base node-graph asset — "the shader")
    └── UMaterialInstance       (abstract; instance overriding a parent)
        ├── UMaterialInstanceConstant  (MIC — editor-authored static variants)
        └── UMaterialInstanceDynamic   (MID — runtime-writable copy)
```

Store and pass materials as `UMaterialInterface*` so any concrete type fits.

Source locations (UE 5.8 `Engine/Source/Runtime/Engine/Public/Materials/`):
- `MaterialInterface.h` — `UMaterialInterface`:351 (common interface, `GetMaterial`,
  `GetRenderProxy`, property getters).
- `Material.h` — `UMaterial`:448 (`MaterialDomain`:482, `BlendMode`:486,
  `ShadingModel`:511, `bUsedWithSkeletalMesh`:703, `GetDefaultMaterial`:1455).
- `MaterialInstance.h` — `UMaterialInstance`:626 (shared parameter storage and
  hierarchy traversal).
- `MaterialInstanceConstant.h` — `UMaterialInstanceConstant`:20 (editor-only setters;
  read-only at runtime).
- `MaterialInstanceDynamic.h` — `UMaterialInstanceDynamic`:14, `Create`:176,
  `SetScalarParameterValue`:24, `SetVectorParameterValue`:109,
  `SetTextureParameterValue`:65.
- `MaterialParameterCollection.h` — `UMaterialParameterCollection`:78.

See [references/material-instances-and-parameters.md](references/material-instances-and-parameters.md)
for a full parameter-type breakdown and a worked C++ example.

## Key material settings (UMaterial properties)

### Material domain (`EMaterialDomain`, `MaterialDomain.h`:12)

| Enum value | Use |
|---|---|
| `MD_Surface` | geometry surfaces — the default for meshes |
| `MD_DeferredDecal` | decal projectors on surfaces |
| `MD_LightFunction` | modifies a light's intensity/color pattern |
| `MD_PostProcess` | custom post-process pass |
| `MD_UI` | UMG/Slate widgets |
| `MD_Volume` | volumetric materials: Volumetric Cloud (with `used_with_volumetric_cloud`; see [volumetric cloud materials](references/volumetric-cloud-materials.md)), Heterogeneous Volumes |

### Blend mode (`EBlendMode`, `Engine/Classes/Engine/EngineTypes.h`:245)

| Enum value | Cost | Notes |
|---|---|---|
| `BLEND_Opaque` | cheapest | depth-writes; no sorting needed |
| `BLEND_Masked` | low | alpha-test cutout; no overdraw; uses clip instruction |
| `BLEND_Translucent` | expensive | no depth-write by default; sorting required |
| `BLEND_Additive` | moderate | adds to scene; good for glow/sparks |
| `BLEND_Modulate` | rare | multiplies into scene |

Prefer `BLEND_Masked` over `BLEND_Translucent` for foliage and fences. Use
translucency only where physically required.

### Shading model (`EMaterialShadingModel`, `EngineTypes.h`:707)

`MSM_DefaultLit`, `MSM_Unlit`, `MSM_Subsurface`, `MSM_SubsurfaceProfile`,
`MSM_ClearCoat`, `MSM_TwoSidedFoliage`, `MSM_Hair`, `MSM_Cloth`, `MSM_Eye`,
`MSM_SingleLayerWater`, `MSM_ThinTranslucent`.

Each shading model enables different material inputs; not all inputs are
meaningful for every model.

## Master material → instances — the authoring pattern

1. Author one `UMaterial` with **parameter nodes** (Scalar Parameter, Vector
   Parameter, Texture Parameter) for everything that varies across surfaces.
2. Create `UMaterialInstanceConstant` assets (child instances) in the Content
   Browser for art variants. Scalar/vector/texture overrides reuse the parent shader;
   static parameters and qualifying base-property overrides can require separate shader permutations.
3. At runtime, call `CreateDynamicMaterialInstance` on a component to get a
   `UMaterialInstanceDynamic` when a value must change during play.

This limits shader permutations versus authoring many separate materials.

See [references/material-graph-and-domains.md](references/material-graph-and-domains.md)
for material graph authoring concepts: PBR inputs, material functions, material
attributes, static switches, and custom HLSL nodes.

## Runtime parameters (MID) in C++

```cpp
// PrimitiveComponent.h:1629 — creates a MID from SourceMaterial and assigns it
// to slot ElementIndex; returns the new MID.
UMaterialInstanceDynamic* MID =
    MeshComp->CreateDynamicMaterialInstance(0, BaseMaterial);

// MaterialInstanceDynamic.h — three core setters (call on the game thread)
MID->SetScalarParameterValue(TEXT("DamageAmount"), 0.75f);
MID->SetVectorParameterValue(TEXT("TeamColor"), FLinearColor(0.f, 0.f, 1.f, 1.f));
MID->SetTextureParameterValue(TEXT("DetailTex"), MyTexture);
```

`CreateDynamicMaterialInstance` creates the MID **and** assigns it to the slot
in one call. Parameter names must match the Parameter nodes in the base material
exactly (case-sensitive `FName` comparison). Typos silently no-op.

To create a standalone MID without assigning it to a slot:

```cpp
UMaterialInstanceDynamic* MID =
    UMaterialInstanceDynamic::Create(BaseMaterial, this);
// Assign later with SetMaterial / CreateDynamicMaterialInstance
MeshComp->SetMaterial(0, MID);
```

High-frequency calls on the same MID can use the index-cache API
(`InitializeScalarParameterAndGetIndex` + `SetScalarParameterByIndex`) to
avoid repeated name lookups.

## Material parameter collections (global parameters)

`UMaterialParameterCollection` is a data asset holding up to 1024 scalar and
1024 vector parameters readable by **any** material in the project. One write
propagates to every referencing material in the same frame — useful for
world-state values (wetness, time-of-day tint, wind strength).

```cpp
// Kismet/KismetMaterialLibrary.h:30
// Set a scalar parameter on a collection from C++ game-thread code:
UKismetMaterialLibrary::SetScalarParameterValue(
    this, WetnessCollection, TEXT("GlobalWetness"), 0.8f);

UKismetMaterialLibrary::SetVectorParameterValue(
    this, TODCollection, TEXT("SunColor"),
    FLinearColor(1.f, 0.85f, 0.6f, 1.f));
```

A material can reference at most **two** collections. Adding parameters to a
collection re-triggers a recompile of all referencing materials; add parameters
in bulk in an empty map to avoid repeated hitching.

See [references/material-cpp-and-collections.md](references/material-cpp-and-collections.md)
for the `UKismetMaterialLibrary` API, `CopyScalarAndVectorParameters`, and
index-cache optimization.

## Usage flags

Each unique `UMaterial` must have its **"Used with ..."** flags enabled for every
content type it will be applied to (`bUsedWithSkeletalMesh`, `bUsedWithNiagaraSprites`,
`bUsedWithInstancedStaticMeshes`, etc.). Missing flags cause the engine to use a
default material instead. Each enabled flag adds one or more shader permutations.

Enable only what the content actually uses; extra usages silently grow compile time.

## Performance guidance

- **Prefer instances**: fewer base materials = fewer shader permutations = less
  compile time and PSO count.
- **Static Switch parameters**: feature toggles compiled per MIC — zero runtime
  branch cost. Minimize the total number of static switch combinations in use.
- **Instruction count**: visible in the material stats panel; keep pixel shaders
  well under a few hundred instructions for mobile.
- **Texture samplers**: each material stage has a hard platform limit (typically
  16 per shader stage). Shared sampler nodes help.
- **Translucent overdraw**: large overlapping translucent surfaces stall the GPU.
  Consider `BLEND_Masked` for cutouts and dithered LOD transitions.
- Use the **Material Analyzer** (Windows → Material Analyzer) to find redundant
  materials and duplicate parameter overrides.

## Verifying a visual material change in the Editor

1. **Prove the edit drives the intended region first.** Inspect the actual component slot, effective instance and graph bindings. When a mask or injection point is uncertain and the mutation scope permits it, temporarily output a diagnostic colour such as `lerp(Prev, float3(1,0,0), mask)`, capture once, then restore the real code. Reuse already-conclusive binding evidence instead of adding a diagnostic edit to protected materials.
2. **Separate dependency readiness, shader compilation and capture.** Load all referenced textures/materials first and return to the Editor for async resource work before a cold check. Retain exact GPU dimensions and formats; registry source sizes alone do not exclude placeholder resources. Call `unreal.MaterialEditingLibrary.get_statistics(material)` after `recompile_material` to finish its current-platform shader map; zero pixel instructions flags failure, but a positive count does not prove ready textures, correct wiring or runtime cost. Verify effective usage flags on the actual A/B instances before their first assignment. Then queue one `take_high_res_screenshot` per real frame and wait for fresh output before switching variants. For temporally accumulated effects such as clouds, use settled PIE frames instead of history-free high-resolution rerenders (see the cloud reference).
3. **Frame the surface you changed.** Pick cameras where that surface fills the lower frame; road or boulders in the frame hide a floor change. Compare same-camera crops side by side, A/B/C variants included.
4. **Don't judge albedo by frame brightness under auto exposure.** Eye adaptation cancels brightness changes of a surface that dominates the frame, so a 30% albedo cut can measure identical. Compare hue (for example R−B) and texture detail. To make a surface read darker, reduce its contrast relative to its neighbours, or fix the exposure. Fixed exposure is a scene-wide lighting decision, so ask the user before changing it.
5. **Choose the correct comparison.** For an effect OFF/ON test, hold the PBR maps, non-target shading terms, lighting, exposure and cameras identical; updating an old imported finish only on the ON side confounds the claimed effect. When the user prefers an earlier version or engine default, compare that look separately in the same session before changing it, then inspect its effective textures and parameter recipe. Judge the requested visible cue, not merely changed pixels or higher shader complexity.

## Gotchas

- **Verify instance details against Unreal's effective values before relying on a material-info wrapper.** A wrapper can faithfully serialize a legacy reader's wrong blend mode, defaults, or override flags. Check the installed implementation and test a real instance with a local override and a nested parent override; see [instance inspection](references/material-instances-and-parameters.md#inspecting-effective-instance-values). Report rounded values and omitted parameter types or layer identities as limits, not complete material diagnostics.
- **Detach nested editor structs before editing or comparison.** Use `.copy()` on a material instance's `base_property_overrides` and its nested `DisplacementScaling`, enable the intended override, assign the edited copies back, then verify the actual magnitude/centre before saving and after clean reload. Do not normalize a live readback struct merely to compare it: local-looking edits can affect its owner or preserve an inherited value unexpectedly.
- **Keep shallow displacement and grain shading coherent.** A depth-only magnitude change holds the authored normal map fixed and may barely change face lighting. For a stronger tactile candidate, derive or tune the normal for the chosen height amplitude and UV metric; record approximate mapping on clipped/reveal faces. If both depth and normal change, label the comparison a coupled appearance pass, not a displacement-only A/B, and preserve the prior finish.
- **Parameter name typos** in `Set*ParameterValue` silently no-op — verify names
  match the parameter nodes exactly.
- **Changing a `UMaterial` directly at runtime** (e.g. swapping its texture
  references) triggers a recompile and hitches. Create a MID instead.
- **Editing a `UMaterialInstanceConstant` at runtime** — MICs are editor assets;
  only `Set*EditorOnly` functions exist. Use MID for any runtime mutation.
- **Missing usage flag** — the mesh shows the default material with no error in
  the log by default. Enable the flag and re-save the material.
- **Declare Nanite usage before an instance A/B test.** In UE 5.8, first assignment can automatically add a Nanite usage override to a material instance and leave it dirty. Set `MaterialEditingLibrary.set_base_material_usage(parent, MaterialUsage.MATUSAGE_NANITE, True)` before creating the instances; verify `has_material_usage` on both. If an owned test instance already gained an automatic override, reconcile it with `set_material_usage_override(instance, usage, False)` and save only the verified owned assets. Keep both controls on the same effective usage flags.
- **Treat cold placeholder resources as a readiness diagnosis.** Use the dependency-load/frame-separated checks above; keep source metadata distinct from the eventual exact GPU readback rather than redefining the expected dimensions or format.
- **An inspector can omit a real hidden output.** Some loaded bridge versions serialize the common material outputs but omit Displacement even though their writer connected it. `EMaterialProperty::MP_Displacement` is hidden in UE 5.8, so its Python enum member can be absent and passing its integer ordinal can fail conversion. Do not drop output verification or rebuild unrelated plugin work just to inspect it. Export the owned material through `AssetExportTask` + `ObjectExporterT3D` to a task-local `.copy`, verify its native `Displacement=(Expression=...)` entry, then inspect that expression's defaults, connected height/strength nodes and sampler settings. Release the export task's object afterward, retain the actual exported text/hash and recheck dirty packages.
- **A copy of an engine base material loses its shipped instance's look.** Engine content often ships a base material whose texture parameters default to placeholders, plus an `*_Inst` that sets the real textures. A copy of the base renders blank until your instance copies the shipped instance's `texture_parameter_values` (and any scalar or vector overrides).
- **Two-collection limit**: a single material graph can reference at most two
  `UMaterialParameterCollection` assets.
- **Static switch combinations**: each unique combination is a separate compiled
  shader. With N static switches you can have 2^N permutations.
- **MID lifetime**: retain GC-visible strong ownership. A strong `UPROPERTY()` member
  is appropriate for independent retention; assignment to a reachable mesh component's
  material slot also retains the MID.

## Version notes — Substrate materials

UE 5.8 ships with the **Substrate** material framework (opt-in project setting).
Substrate replaces the single shading model and blend mode selectors with a layered
slab-based authoring model. The C++ instance API (`UMaterialInstanceDynamic`,
`Set*ParameterValue`) is unchanged. Some `EMaterialShadingModel` enum values
are Substrate-only (`MSM_Strata`, hidden from the non-Substrate editor). The
`BLEND_TranslucentColoredTransmittance` and `BLEND_ColoredTransmittanceOnly`
blend modes are also Substrate-only. Non-Substrate projects should ignore these.

See [references/material-graph-and-domains.md](references/material-graph-and-domains.md)
for a Substrate overview.

## Cross-references

- `ue-meshes-static-and-skeletal` — assigning materials to mesh components and
  slots; `UStaticMeshComponent::SetMaterial`, skeletal mesh material slots.
- `ue-actors-and-components` — component lifecycle; when to call
  `CreateDynamicMaterialInstance` (after component is registered / in `BeginPlay`).

## References & source material

Engine source (UE 5.8, `Engine/Source/Runtime/Engine/`):
- `Public/Materials/MaterialInterface.h` — `UMaterialInterface`:351.
- `Public/Materials/Material.h` — `UMaterial`:448; `MaterialDomain`:482;
  `BlendMode`:486; `ShadingModel`:511; usage flags from :703.
- `Public/Materials/MaterialInstance.h` — `UMaterialInstance`:626.
- `Public/Materials/MaterialInstanceConstant.h` — `UMaterialInstanceConstant`:20.
- `Public/Materials/MaterialInstanceDynamic.h` — `UMaterialInstanceDynamic`:14;
  `Create`:176; `SetScalarParameterValue`:24; `SetVectorParameterValue`:109;
  `SetTextureParameterValue`:65.
- `Public/Materials/MaterialParameterCollection.h` — `UMaterialParameterCollection`:78.
- `Public/MaterialDomain.h` — `EMaterialDomain`:12 (all domain enum values).
- `Classes/Engine/EngineTypes.h` — `EBlendMode`:245; `EMaterialShadingModel`:707.
- `Classes/Kismet/KismetMaterialLibrary.h` — `UKismetMaterialLibrary`:22;
  `SetScalarParameterValue`:30; `SetVectorParameterValue`:34.
- `Classes/Components/PrimitiveComponent.h` — `SetMaterial`:1600;
  `CreateDynamicMaterialInstance`:1629.
- `Private/Materials/MaterialInstance.cpp` — static permutation creation and game-thread parameter updates.
- `Classes/Components/MeshComponent.h` — GC-visible `OverrideMaterials` references.
- `Private/Components/PrimitiveComponent.cpp` — `CreateDynamicMaterialInstance` creation/reuse behavior.

Official docs (UE 5.8):
- Materials overview —
  <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-materials>
- Material Properties (domain, blend mode, shading model) —
  <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-material-properties>
- Instanced Materials (MIC / MID concepts) —
  <https://dev.epicgames.com/documentation/unreal-engine/instanced-materials-in-unreal-engine>
- Material Parameter Collections —
  <https://dev.epicgames.com/documentation/unreal-engine/using-material-parameter-collections-in-unreal-engine>
- Material Functions —
  <https://dev.epicgames.com/documentation/unreal-engine/material-functions-in-unreal-engine>
- Substrate Materials —
  <https://dev.epicgames.com/documentation/unreal-engine/substrate-materials-in-unreal-engine>
- Designing Visuals, Rendering, and Graphics —
  <https://dev.epicgames.com/documentation/unreal-engine/designing-visuals-rendering-and-graphics-with-unreal-engine>

Deep-dive references in this skill:
- [references/material-instances-and-parameters.md](references/material-instances-and-parameters.md) —
  parameter types, MIC vs MID in detail, C++ worked example, index-cache API.
- [references/material-graph-and-domains.md](references/material-graph-and-domains.md) —
  PBR inputs, material functions, static switches, material attributes, custom HLSL,
  Substrate overview.
- [references/material-cpp-and-collections.md](references/material-cpp-and-collections.md) —
  full C++ API reference: `UKismetMaterialLibrary`, `CopyScalarAndVectorParameters`,
  MID gotchas, collection constraints.
- [references/volumetric-cloud-materials.md](references/volumetric-cloud-materials.md) —
  sky vs terrain-pinned clouds, crash-safe custom cloud material procedure (detach before
  compiles and texture reimports), conservative density, shared-base cumulus and summit-cap
  recipe matched to Epic's soft look, engine cloud-material facts (incl. Epic's noise proportions),
  A/B against a preferred reference look, grain/flicker fixes (Tracing Max Distance 20 km, then 3×
  samples) and the levers that measured worse, reproducing the user's view, PIE verification and cost.
- [scripts/pie_cloud_flicker.py](scripts/pie_cloud_flicker.py) — PIE probe that grabs frame
  bursts per config (cvars, sample scale, MID parameters, component setters; still, slow or panning
  camera) and reports grain, flicker and GPU ms. Copy it onto the Editor's Python path.
