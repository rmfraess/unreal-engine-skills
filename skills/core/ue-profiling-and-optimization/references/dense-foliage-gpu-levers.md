# Dense foliage scenes: attributing and cutting GPU cost (UE 5.8)

These levers were measured in PIE on a Nanite forest: about 100k Nanite floor instances, about 5k Megaplants
skinned pines (Nanite Voxelize), Lumen with hardware ray tracing, VSM and volumetric fog. Use the table to
choose what to A/B first. Re-measure in your own scene, because the savings depend on the scene.

## Procedure

1. **Measure in PIE or standalone, not the Editor viewport.**
   - The viewport adds hit-proxy and Editor work, so it can report a render-thread bound that turns out GPU-bound in PIE.
   - Teleport the PIE player each tick with `BugItGo x y z pitch yaw 0` so every config uses the same view.
   - Use [../scripts/pie_ab_timing.py](../scripts/pie_ab_timing.py); it does the teleport, per-config cvars/hides/props on PIE-world components, medians and restore.
   - `PerformanceService.frame_timing()` reports `render_thread_ms` as 0 during PIE, so count samples on `gpu_ms`. A sampler gated on render-thread samples never finishes.
   - Disable Editor background throttling first, or PIE (and automation tests) run at about 3 fps.
2. **Attribute the cost by content category.**
   - Hide one category's instanced components in the PIE world only and record median GPU over 45–60 frames.
   - Repeat the baseline at the end. Single runs carry about ±0.7 ms of noise.
3. **Attribute the cost by pass.**
   - Run `r.ProfileGPU.ShowUI 0`, then `ProfileGPU` once with the category shown and once with it hidden.
   - The pass tree is written to the log as `LogRHI: Display:` lines, with `┃`-separated columns: inclusive ms in column 2, indented name in column 3, 3 spaces per depth level.
   - Parse both dumps and compare passes at depths 4–6. The usual movers are `RenderVirtualShadowMaps(Nanite)` and `LumenScreenProbeGather`.
4. **Bisect the lever cvars one at a time** in the same PIE run (see the table). Restore every cvar afterwards.
5. **Check quality before adopting a lever.**
   - Capture a close-up and a mid view, *including a sunlit view*. Shaded views hide shadow-resolution changes.
   - To find sunlit floor under a canopy, don't line-trace toward the sun: foliage usually has no collision, so nearly every point traces clear. Instead capture 3–4 views with the camera yaw equal to the light's yaw (sun behind the camera, pitch about −30, eye 1.5 m), pick the ones with sun patches, then A/B those at full resolution.
   - Crop full resolution for vision.
   - Present each lever with its GPU saving and its quality risk, and adopt only those with no visible close-range loss.

## Levers measured (GPU ms saved, about 19.5 ms baseline)

| Lever | Saved | Close-range quality risk |
|---|---|---|
| `r.Lumen.HardwareRayTracing 0` | 2.9 | Foliage GI and reflections usually worse; avoid |
| `r.Shadow.Virtual.ResolutionLodBiasDirectional` −1.5 → −1.0 (Epic → High) | 2.2 | **Rejected for close-up work:** in direct sun it visibly softens grass-blade shadows on the floor at about 1.5 m (identical in shade) |
| `r.Lumen.ScreenProbeGather.DownsampleFactor 32` | 1.7 | Noisier indirect light |
| `r.RayTracing.Culling.Radius` 300 m → 100 m | 1.1 | None seen at close or mid range; adopted. It is not a Project Settings property, so set it under `[SystemSettings]` in `DefaultEngine.ini` |
| Mature skinned pines `cast_shadow` off (diagnostic only) | 2.3 | Unacceptable; shows tall-tree shadows are the main shadow cost |
| `r.Nanite.MaxPixelsPerEdge 2` globally (diagnostic only) | 0.8 | Coarser geometry everywhere; shows triangle count is not the bottleneck, so cutting needle triangles on one asset is not worth its close-up loss |
| `r.VolumetricFog 0` | 0.7 | Loses volumetric fog look |
| `r.Shadow.Virtual.Clipmap.LastLevel 20` | about 0.5 | Far shadows lost |

These gave **no gain** in this scene:
- freezing skinned wind (`r.Skinning.TransformProviders 0`)
- `r.Shadow.Virtual.Cache.DeformableMeshesInvalidate 0`
- per-component `ShadowCacheInvalidationBehavior = Rigid`
- `AnimationMinScreenSize 0.3`
- `bAffectDynamicIndirectLighting = false` on clutter
- shorter ISM cull distances
- turning clutter shadows off, including small skinned saplings (all, or only the smallest)
- `r.Nanite.ShadowRaster.TimeBudgetMs 1` with `r.Nanite.ShadowRaster.PixelsPerEdgeScaling` 50 or 33 (shadow-only dynamic coarsening; no measurable effect)

So for Nanite skinned trees, the cost is shadow-depth and Lumen work on their geometry, not animation. A code reading may suggest per-frame VSM invalidation from skinned proxies (`bHasDeformableMesh`), but this measurement did not show it. Measure before acting on it.

## Fog and mist as an optimization

- Height and volumetric fog do not cull anything. Fog has no role in the Nanite, instance-culling, shadow-setup or VSM code; `FogCutoffDistance` is only a shader parameter.
- Volumetric fog *costs* GPU: a froxel grid controlled by `r.VolumetricFog.GridPixelSize` and `GridSizeZ`, plus the component's view distance.
- Mist only pays off when you pair it with distance cuts it hides:
  - `InstanceEndCullDistance`
  - max draw distance (`r.Nanite.Culling.DrawDistance 1`)
  - VSM last clipmap level
  - ray-tracing culling radius
  - Lumen view and trace distance
  - HLOD
- With Nanite, distant geometry is already cheap, and these cuts were worth only about 0.5–1.1 ms. Check the art direction before proposing mist for performance.
