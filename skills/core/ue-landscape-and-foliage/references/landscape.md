# Landscape — deep reference

Deep dive for [../SKILL.md](../SKILL.md). Covers component/section dimension math, material
layer setup, edit layers, landscape splines, Nanite landscape, and runtime C++ queries.
Grounded in UE 5.8 (`Engine/Source/Runtime/Landscape/Classes/`) and the official
[Landscape Outdoor Terrain](https://dev.epicgames.com/documentation/unreal-engine/landscape-outdoor-terrain-in-unreal-engine)
and [Landscape Technical Guide](https://dev.epicgames.com/documentation/unreal-engine/landscape-technical-guide-in-unreal-engine)
docs.

## Component / section / quad math

The landscape is a uniform grid of `ULandscapeComponent`s. Each component contains
`NumSubsections × NumSubsections` sections, each `SubsectionSizeQuads` quads on a side.

```
ComponentSizeQuads = NumSubsections × SubsectionSizeQuads
Total landscape quads (one axis) = NumComponentsX × ComponentSizeQuads
Heightmap vertex count (one axis) = Total quads + 1
```

Common recommended setup (32 × 32 components, 4 sections/component, 63 quads/section):
- `ComponentSizeQuads` = 2 × 63 = 126
- Total quads = 32 × 126 = 4032
- Heightmap size = **4033 × 4033 vertices**

Key rule: each section must be a power-of-two number of quads (63 = 64 − 1 for 2×2
subsections; 127 = 128 − 1 for single-section components) so LOD mipmaps fit cleanly.
The engine targets ≤ 1024 components for performance (one render-thread CPU cost per
component, one draw call per section).

Height precision: 16-bit values, `h_cm = (v − 32768) × ZScale / 128`, so ±256 m at
`Z Scale = 100` and ±2,048 m at 800. Exceeding the range means changing Z scale and re-encoding
every height. Import formats: 16-bit
grayscale PNG, `.r8`, `.r16`, or `.raw` with companion JSON (width/height/bpp).

## Class architecture

```
ALandscape : ALandscapeProxy : APartitionActor
```

`ALandscapeProxy` (abstract, `LandscapeProxy.h`:450) is the runtime class. All streaming
landscape cells are `ALandscapeStreamingProxy` instances pointing back to their parent
`ALandscape` via `LandscapeGuid`. The proxy holds:

- `LandscapeComponents` — `TArray<ULandscapeComponent*>` (index into the component grid).
- `LandscapeMaterial` — the `UMaterialInterface` applied to all components.
- `ComponentSizeQuads`, `SubsectionSizeQuads`, `NumSubsections` — dimension metadata.
- `bEnableNanite`, `NaniteLODIndex`, `bNaniteSkirtEnabled` — Nanite generation settings.
- `bUseDynamicMaterialInstance` — creates per-component `UMaterialInstanceDynamic` at
  runtime; required if you modify landscape material parameters from code.
- `bUsedForNavigation` — opt out for distant/background landscapes to avoid navmesh cost.

`ULandscapeComponent` (`LandscapeComponent.h`:431) extends `UPrimitiveComponent`. It owns
the heightmap texture and weightmap textures for its tile of terrain, drives the LOD
selection per-component, and contributes to the landscape's collision.

## Material layers and `ULandscapeLayerInfoObject`

A landscape material uses one or more `LandscapeLayerBlend` material nodes, each referencing
a named layer. For each such layer:

1. Create a `ULandscapeLayerInfoObject` data asset (`LandscapeLayerInfoObject.h`:59).
   - Assign a `UPhysicalMaterial` (optional) for surface-type queries at runtime.
   - `Hardness` influences paint blending; `bNoWeightBlend` forces binary 0/1 weight.
2. Open the landscape's **Target Layers** panel and assign the created asset to the matching
   layer name.
3. The weightmap (a texture stored per component) records the blended weights at runtime.

Without the `ULandscapeLayerInfoObject` asset, the layer entry appears in the editor UI but
painting is disabled and the material blend node receives zero weight for that layer.

**Whole-Landscape replacement preflight (UE 5.8):** Check the target engine's replacement path and require coverage of every affected proxy before mutating persistent target-layer bindings. Native `FLandscapeEditDataInterface::ReplaceLayer` visits `ULandscapeInfo::XYtoComponentMap`; `ForEachLandscapeProxy` and `AreAllComponentsRegistered` only inspect registered/known proxies, so neither proves that unloaded or wholly unregistered proxies were covered. Compare descriptor-backed proxies, live world actors and the LandscapeInfo mutation set in both directions, including descriptor-less unsaved proxies; require a fully initialized partition, validate component mapping in both directions, and handle unloaded streaming levels explicitly. A proxy removed from the level can remain registered in LandscapeInfo, so validating only live actors against that set misses objects the operation may still mutate. Do not treat `HasUnloadedComponentsInRegion` or descriptor `IsLoaded()` as proof of registration: after a region unload, `FindObject` can rediscover a still-resident proxy even though it was removed from the level and LandscapeInfo. `HasUnloadedComponentsInRegion` also only checks partitioned persistent-level landscapes. Inspect engine export visibility before calling internal helpers across modules; a public declaration need not be linkable. Test actually unloaded states separately, including a resident-but-unregistered proxy, before crediting the guard.

Compare collision behavior as well as pointer identities: collision heightfield material handles are cached, and `MinimumCollisionRelevanceWeight` affects dominant-layer selection. When replacement changes either physical material or collision relevance, verify the engine's rebuild and Undo/Redo path with settled physical queries, or reject the change until that behavior is supported.

**Landscape grass types:** `ULandscapeGrassType` assets referenced from the landscape
material cause the engine to spawn grass HISM instances procedurally as the camera moves.
Grass uses `UHierarchicalInstancedStaticMeshComponent` under `ALandscapeProxy`
(see `LandscapeProxy.h` — `UHierarchicalInstancedStaticMeshComponent` is forward-declared
at line 30). Runtime grass generation is controlled by `bDisableRuntimeGrassMapGeneration`.

## Edit layers

Edit Layers (`LandscapeEditLayer.h`) are non-destructive sculpt/paint stacks authored in
the editor. Each layer is either a **Height** layer, a **Weight** layer, or a **Blueprint
Brush** layer (`ALandscapeBlueprintBrushBase`). The engine merges them in order at bake
time into the final heightmap and weightmap textures. At runtime, only the baked result
is used — there is no runtime merge cost.

Blueprint brushes provide a C++/Blueprint hook (`AddBrushToLayer`, `RemoveBrush` on
`ALandscape`) for tools that generate heightmap edits procedurally at edit time.

## Procedural relief: finding and fixing sharp points

Code that writes a height delta (noise ridges, bumps, pits) into a landscape layer is sampled
only at vertices. A feature narrower than one quad survives as a single raised vertex and
renders as a pyramid tip; noise-space widths (e.g. `smoothstep(0, k, |noise|)`) shrink in
world space wherever the noise gradient is steep, so the tips cluster in patches.

1. **Scan the real vertex heights, all of them.** Sample on the vertex lattice
   (`origin_min + i·quad_size`) through the landscape's own collision, so rocks and trees cannot
   block it: for each `LandscapeHeightfieldCollisionComponent` (bounds via
   `SystemLibrary.get_component_bounds(c)`), `c.line_trace_component(top, bottom, True, False, False)`
   returns `(location, normal, bone, HitResult)` or `None` on a miss. **Offset each ray ~1 cm off
   the vertex** — rays exactly on a heightfield edge miss, which silently drops whole columns and
   every neighbour test next to them — and assert the sample count equals the grid count before
   trusting any statistic. Collision matches render heights at `collision_mip_level` 0.
2. **Measure two things, against a baseline.** Tips: a vertex higher than all 8 neighbours whose
   height minus the 4-neighbour mean exceeds ~40 cm. Creases: convex curvature
   `k = 2·(h − (h₊+h₋)/2)/s²` along x, y and both diagonals; the triangle-to-triangle bend is
   ≈ `quad·k`, and > ~20° reads as a knife edge, especially on silhouettes. A tip-only check misses
   ridge lines entirely. Report counts beside the same counts for the hand-sculpted ground with all
   generated detail off, and check one flagged spot sits where the user's camera looks
   (`get_level_viewport_camera_info()`, then trace its forward vector).
3. **Attribute by toggling terms**: zero one term (or chance, e.g. windthrow), regenerate, dump,
   restore. Terms add, so differences of dumps give each term at every vertex. Typical split: point
   features (windthrow mounds: 60 cm high, 2.6 m radius ≈ 1 quad) make the big tips; noise crests
   and banks make the creases; small lumps add many moderate bends.
4. **Simulate before a C++ rebuild.** Blur a term's difference grid in Python (offsets = quad size
   hit neighbour vertices exactly, so it matches what C++ will write) and rerun tips, bends and
   slope stats (median, p90). For point features simulate the analytic shape at 16 sub-cell offsets:
   blurring a narrow mound flattens it (60 → ~18 cm), while doubling its radii keeps ~56 cm with
   worst tip ~22 cm and bend ~15°.
5. **Implement once, opt-in**: a pure `GridSmooth(P, Step, Taps, F)` binomial helper applied at the
   relief composition (lumps 1 tap, ridges 2 taps) plus widened *drawn* pit/mound radii, all behind
   one setting holding the grid spacing (0 = legacy). Keep site choice and tree clearing on the old
   footprint. Tests: a plane survives the smoothing; the smoothed term's worst tip on the grid is
   bounded; legacy vs widened mound tips swept over 16 sub-cell offsets — one offset can land the
   peak between vertices and under-report.
6. **Verify**: full-grid rescan (tips and bends vs before and vs sculpted baseline), regenerate
   twice and diff the dumps (0 cm = deterministic), capture the user's views and the worst
   remaining spot, and state the trade-off: steep, short banks cannot exist on a 2 m grid, so
   steepest-10% slopes drop a few degrees. A finer detail landscape is the only way to keep both.

## Landscape splines

`ALandscapeSplineActor` (`LandscapeSplineActor.h`:14) owns a `ULandscapeSplinesComponent`
(forward-declared in `LandscapeProxy.h`:38 as `SplineComponent`). Splines consist of:

- `ULandscapeSplineControlPoint` — a positioned point with tangent handles.
- `ULandscapeSplineSegment` — connects two control points; stores the painted falloff shape.

At cook/build time, the spline deforms terrain beneath it (raise terrain to spline height
within the falloff) and optionally stamps static mesh instances along the segment
(`ControlPointMeshActor.h`, `LandscapeSplineMeshesActor.h`).

World Partition landscapes partition splines into `ALandscapeSplineActor` actors per region;
the `ShouldPartitionSpline()` method on the spline actor controls this.

## Nanite landscape

Enable with `bEnableNanite = true` on the proxy. The engine:
1. Generates a `ULandscapeNaniteComponent` (`LandscapeNaniteComponent.h`) at the LOD
   specified by `NaniteLODIndex` (usually 0 for highest detail).
2. Renders the landscape as a Nanite virtualized mesh on supported hardware.
3. Falls back to standard LOD rendering on non-Nanite hardware.

Caveats:
- Per-LOD material overrides (`PerLODOverrideMaterials`) do not apply to the Nanite mesh.
- A skirt (`bNaniteSkirtEnabled`, `NaniteSkirtDepth`) hides gaps at landscape edges.
- Nanite meshes are regenerated when the heightmap changes; rebuild is an editor operation.
- See [Using Nanite with Landscapes](https://dev.epicgames.com/documentation/unreal-engine/using-nanite-with-landscapes-in-unreal-engine)
  for platform support and known constraints.

### Material displacement on a Nanite landscape (ground depth instead of POM)

Prefer this over POM for a floor seen at player height: it moves real geometry (silhouettes, shadows, contact), while POM flattens at grazing angles and costs samples per blended layer.

1. **Height source.** Confirm a height map exists. Megascans Medium tier ships only colour/normal/ORM; the High tier adds a 4K single-channel `_H` (re-import via Fab, see `unreal-asset-sourcing`).
2. **Material.** Sample the height with `SAMPLERTYPE_ALPHA`, mix it per layer with the same masks the colour uses, and return `lerp(Center, height, mask)` so unmasked areas (road, snow, field) sit at the centre value and do not move. Python's `MaterialProperty` enum has no Displacement entry: wire it with `MaterialNodeService.connect_expression_to_output(mat, expr_id, "", "Displacement")`. Set `enable_tessellation=True` and `displacement_scaling` (`magnitude`, `center`). Runtime tessellation (`r.Nanite.Tessellation`) is on by default.
3. **Scale.** Landscape displacement is multiplied by the actor's Z scale (100 on a default landscape), so set `magnitude = cm / ZScale`; a magnitude of 8 is 8 m. A first trial that changes nothing visible or explodes is usually this.
4. **Amplitude and softness — start low.** Scanned height maps at full resolution have near-vertical steps at every pebble and leaf edge. Displaced, each step becomes a wall the UV-mapped albedo is smeared down (vertical streaks, "choppy" ground). The user rejected 15 cm at mip 0 for exactly this. Start at ~4 cm and read the height at a fixed coarse mip: set `mip_value_mode = TMVM_MIP_LEVEL` and `const_mip_value` (4 ≈ 256 px over a ~2.5 m tile) on the height `TextureSample`; no extra node needed. Raise one notch at a time only if the user asks for more depth. Expose cm, centre and mip as script constants so a retune is one rebuild.
5. **Centre vs flat collision.** Collision stays on the undisplaced heightfield, and clutter rests on collision. A centre of ~0.7 keeps at most ~30% of the range above collision (≈1.2 cm at 4 cm), so litter is rarely buried and the rest reads as gaps between stones.
6. **Enable Nanite** on the target proxy only (`enable_nanite=True`), then save the map: the `LandscapeNaniteComponent` is built on save. Without it the Displacement output is ignored.
7. **Judge close, not just standing.** Check a very low camera (~20–60 cm above ground, the user's viewport via `get_level_viewport_camera_info()`) as 1:1 brightened crops of the same patch per setting, looking for stretched texture on stone/leaf edges; then a low sunlit view (~0.9 m eye) and a standing view. Standing views hide the artifact (15 cm looked merely "subtle" there), and downscaled sheets hide both artifact and relief. Present a labelled ladder (0 cm, current, 2–3 softer settings) and let the user pick; if the softest readable one still looks odd, recommend turning displacement and Nanite landscape off rather than further tuning.
8. **Cost A/B without recompiles:** `r.Nanite.Tessellation 0/1` toggles displacement and `landscape.RenderNanite 0/1` falls back to the legacy landscape, both live in one session. Measured on a dense forest view: Nanite landscape +0.24 ms, 15 cm displacement +0.43 ms. Restore both cvars afterwards.
9. Changing the material's centre/magnitude/mip needs a recompile (~30 s of shader work); transient compile errors in the log during that window are not the final state, so recompile once more and read the log after it.

## Runtime C++ queries

Direct landscape data access from gameplay code uses `ULandscapeInfo`, retrieved via
`ALandscapeProxy::GetLandscapeInfo()` or the `ULandscapeInfoMap` subsystem.

```cpp
// Querying landscape height and layer weight at a world location (editor/runtime):
if (ALandscapeProxy* Proxy = Cast<ALandscapeProxy>(LandscapeActor))
{
    ULandscapeInfo* Info = Proxy->GetLandscapeInfo();
    if (Info)
    {
        // Height query requires landscape coord conversion:
        FVector LandscapePos = Proxy->LandscapeActorToWorld().InverseTransformPosition(WorldLoc);
        // Layer weight sampling requires ULandscapeInfo::GetLayerWeightAtLocation
        // (available in editor; limited at runtime without cook-time bake).
        float Weight = Info->GetLayerWeightAtLocation(WorldLoc, LayerInfoObj);
    }
}
```

For pure runtime slope/height queries (without editor-only APIs), trace against the
landscape's collision (a `ULandscapeHeightfieldCollisionComponent`) using
`GetWorld()->LineTraceSingleByChannel`.

## Key source paths (UE 5.8)

All under `Engine/Source/Runtime/Landscape/Classes/`:
- `Landscape.h` — `ALandscape`:276
- `LandscapeProxy.h` — `ALandscapeProxy`:450; key fields at lines 491, 604, 682, 924–930
- `LandscapeComponent.h` — `ULandscapeComponent`:431
- `LandscapeLayerInfoObject.h` — `ULandscapeLayerInfoObject`:59
- `LandscapeSplineActor.h` — `ALandscapeSplineActor`:14
- `LandscapeInfo.h` — `ULandscapeInfo`
- `LandscapeGrassType.h` — `ULandscapeGrassType`
- `LandscapeNaniteComponent.h` — `ULandscapeNaniteComponent`
