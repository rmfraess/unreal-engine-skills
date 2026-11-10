# Volumetric Cloud materials (UE 5.8)

Sky layers and clouds pinned to terrain (mountain cap clouds, banks over a range, cumulus sharing one base with them) on
the native `VolumetricCloud` actor. One cloud component renders per scene, so the sky and any local cloud share one
material.

## Choose the route

| Need | Route |
|---|---|
| Fair-weather or overcast sky | A material instance of Epic's `/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst`, parameters only. It reuses compiled shaders. |
| Cloud tied to world features | Copy the base `m_SimpleVolumetricCloud` and add one Custom-node term (procedure below). |
| Low cumulus sharing one flat base with terrain cloud | Generate them in the same Custom term (cumulus recipe below); keep Epic's types only for the high thin sky with `Layout_CloudType` = (0, 0, 1, 0). |

Don't try to do these with the engine's own parameters:
- **Pinning km-scale cloud:** `Layout_GlobalCloudMask` is added after the height profile and noise, so masked cloud renders as flat-sided boxes. Cloud fed into `Layout_CloudGlobalPattern` goes through the engine's several-km 3D noise, which erases km-scale shapes or turns boosted ones into full-height columns, even with a custom height profile.
- **Lowering the puffy sky to a shared low base:** the visible puffs are the mid-level (G) type, whose base sits near 0.42–0.45 of the layer. Lowering the layer barely moves them, boosting the low (R) type gives grey overcast, and squeezing the layer erases them.

An unowned sky product (for example Ultra Dynamic Sky) can be a design reference, but its docs don't show its shader. Keep the custom term self-contained so a later swap replaces one actor and material.

## Procedure (crash-safe)

Recompiling a cloud material while a live cloud uses it has crashed UE 5.8. Keep every compile off live components.

1. **Make a recovery point.** Commit the map and leave nothing dirty. Read the log's `LogRHI: Texture pool` line and any over-budget warnings for VRAM headroom.
2. **Prototype in PIE.** Changes there are transient. Edit the PIE copy of the cloud (`get_game_world()`), or spawn one with `PIEActorService.spawn_actor`. Give it `unreal.MaterialLibrary.create_dynamic_material_instance(world, saved_mi)` and change parameters live. Parameter sweeps on that MID never touch the saved instance.
3. **Copy the base material.** Use `EditorAssetLibrary.duplicate_asset(base, '/Game/.../M_X')`. Before the first save, assert `used_with_volumetric_cloud` and `MD_VOLUME`.
4. **Wire the two hook points.** Find them by property, not position, using `get_material_expressions`, `get_inputs_for_material_expression`, `get_material_expression_input_names` and `get_input_node_output_name_for_material_expression`:
   - **Density:** connect the Custom node's output to input `A` of the `Add` whose `desc` is "Add additive mask". It replaces the engine mask term and inherits the engine's density, lighting and outputs.
   - **Conservative density:** insert a `Max` between the `MakeFloat4` X input that feeds `VolumetricAdvancedMaterialOutput.ConservativeDensity` and its current source. Take the second input from a Custom-node additional output that is 1 wherever your cloud can exist. The renderer skips every sample whose conservative density x is ≤ 0 (`Engine/Shaders/Private/VolumetricCloud.usf`), so without this the added cloud never draws.
5. **Expose tuning as scalar parameters:** base and top height, noise size, erosion, edge hardness, density, coverage amounts, wind speed and direction. PIE tuning through a dynamic instance then needs no recompile.
6. **Detach, then import and compile.**
   - Assert PIE is stopped, swap every cloud component to the engine instance, and only then reimport any texture the material samples. A compression change recompiles the materials that use the texture.
   - Call `MaterialEditingLibrary.recompile_material`, then `get_statistics`, which blocks until the shader map is complete. `num_pixel_shader_instructions > 0` only flags a total failure: the count stays the same when the Custom code changes, so it is not the cloud shader's count. Also grep the log for `Failed to compile Material` and judge the result in PIE.
7. **Build the instance.** Copy the shipped instance's four texture overrides (height profile, cloud pattern, cloud mask, 3D noise); the base material's defaults are black placeholders, so without them the sky disappears. Set the wind, `Layout_CloudType` and your parameters.
8. **Re-parent safely.** Re-parent your instance while the component still holds the engine instance and confirm it with `get_statistics(mi)`. Then reassign it, set the component's View Sample Count Scale and Tracing Max Distance (see Verification), and save the level explicitly.
9. **Verify in PIE** (below) and measure the cost.

### Rebuilding the Custom node when its pins change

Python can't rewire a `CustomInput` list. If the script owns every source of the node, rebuild it in place:
1. Find the node by its description.
2. Reconnect the conservative-density `Max`'s input A source directly to the `MakeFloat4` X pin.
3. Delete every expression from `get_inputs_for_material_expression(m, custom)` except shared engine nodes such as `Noise_Texture3D`, then delete the `Max` and the node.
4. Re-add the node.

Compare the existing code and pin names (`get_editor_property('input_name')`) first, and skip the rebuild when both match, so unchanged runs leave the package untouched in Git.

## Engine material facts

- **Layout:** the textures sample at UV = world km / `Layout_CloudGlobalScale` (256 km) + 0.5, so the world origin sits at the texture centre, and they wrap.
- **Types:** RGBA = stratocumulus, altostratus, cirrostratus, nimbostratus. `Layout_CloudType` weights them (default 1, 1, 1, 2).
- **Height profile:** sampled at UV = (normalised altitude in the layer, pattern value). Each value is decoded as value − 0.5, and the max over the four types is taken.
- **Layer clipping:** an `If` node zeros the bottom and top 2% of the layer (120 m of a 6 km layer). Set the layer bottom below the lowest base you need.
- **Wind:** horizontal `Layout_WindControls` slides the whole layout across the world. Zero x/y for clouds that must stay put. For a standing cloud such as a cap, advect only your term's noise; air moving through a stationary cloud looks right.
- **Altitude:** with SkyAtmosphere `PLANET_TOP_AT_ABSOLUTE_WORLD_ORIGIN` and terrain at Z = 0, `WorldPosition.z / 100` is metres above the terrain datum. A base taken from world Z stays flat; layer altitudes follow planet curvature, which drops about 15 m at 14 km from the origin.
- **Terrain intersection:** `r.VolumetricRenderTarget.Mode` 0 and 1 composite clouds against opaque terrain; mode 2 cannot (see the cvar text in `VolumetricRenderTarget.cpp`). Check the live value before blaming the material for clouds drawn over mountains.
- **Isolating your term:** `Cloud_GlobalCoverage` −1 clears the engine sky.
- **Epic's shape recipe:** `Noise1_Coordinates` tiles the breakup noise at ~4.2 km, and `Noise_Strength` weights the three noise octaves 0.8 / 0.08 / 0.03. Its soft look comes from that large noise and modest density, not from detail; copy those proportions in a custom term.
- **Parameter meanings:** the exported graph's parameter `Desc` strings describe each one. Use them when the online docs are unavailable. Older example cloud materials ship in the disabled `Engine/Plugins/Experimental/Volumetrics` plugin; read them as reference rather than enabling the plugin for production.

## Custom-node notes

- **Textures:** a texture-object input `X` gets sampler `XSampler`. The engine's `Noise_Texture3D` parameter node can feed your Custom node as well as its existing consumers; sample it with `Texture3DSampleLevel`.
- **Additional outputs** are assigned by name inside the code (`Conservative = ...;`).

### Shared-base cumulus and cap recipe

The structure is Horizon's: coverage sets a threshold on the noise, so the noise draws the outlines. The shape numbers follow Epic's own cloud material: one large breakup noise, fine detail almost off, soft edges and modest density. That gives soft, translucent fair-weather cumulus at 5–20 km (base 1,150 m) with grain matching Epic's sky. Don't add fine detail to get definition: dense, hard-edged clouds with ~400 m erosion read as opaque cotton balls, and their edges sparkle as they drift (PIE grain 0.6–1.1 against Epic's 0.16–0.56; this recipe 0.16–0.44).

1. **Coverage.**
   - **Cap:** `saturate(capTex * Gain)`, with a fade for positions outside the coverage texture. A clamped texture otherwise streaks its edge texels to the horizon.
   - **Puffs:** `saturate((w - t) / (1 - t))`, where `w` samples a tiling puff field drifted downwind and `t = 1 - lerp(Lowland, Crest, region)`.
   - **Combined:** `cov = max(cap, puff)`.
2. **Height envelope** with `h = (z - Base) / (Top - Base)`:
   - `dome = max(lerp(0.3, 1, puff), cap * CapTop)`, so puff towers rise out of a lower cap bank.
   - `env = cov * saturate(h / 0.06) * saturate((dome - h) / (0.35 * dome))`.
   - Conservative output is 1 where `cov > 0.01` and h is in [0, 1].
   - Keep the dome varying: a saturated cap with a constant dome gives a flat-topped slab.
3. **Outline:** use `n = 0.75 * noise.r(q) + 0.25 * noise.g(q * 2.7)` at a ~4.2 km tile (Epic's breakup scale), then `b = saturate((n - (1 - env)) / max(env, 0.02)) * env`. Thresholding `env - (1 - n) * E` instead makes round cotton balls, because the dome contour dominates and the noise only nudges it. A 1.6 km tile gave many small, lumpy puffs.
4. **Detail:** keep an erosion term as a tuning parameter, `e = lerp(nd, 1 - nd, saturate(h * 3)) * Erosion` with `nd = noise.g(q * 4)`, but start at Erosion 0. Fine erosion is sub-step detail at 10–20 km, so it renders as crawling dots; 0.15 was grainy, 0.25 tore the puffs, and a ~220 m octave speckled.
5. **Density:** `saturate((b - e) / (1 - e) * Edge) * Density`, with Edge 1 and Density 1 (applied before the engine's `Cloud_GlobalDensity`). Edge 2+ and Density 4 gave opaque, sparkling cotton balls.
6. **Puff depth:** give the biggest puffs ~800 m (fair-weather cumulus are 0.3–1 km deep). At 500 m they barely self-shadow, so their bases stay white.

### Coverage inputs

- **Cap from the final terrain heights,** not from a separate band authored elsewhere:
  - Summit envelope: `gaussian(maximum_filter(h, 1.2 km), 0.5 km)` passed through a smoothstep.
  - Lee spill: also sample the envelope 0.6, 1.2 and 1.8 km upwind (away from the viewer), weighted 0.9, 0.7 and 0.45.
  - Apply gap noise only to the spill, so the tallest peaks are always capped.
  - Count the peaks above the base that end up with full coverage after the gain.
- **Region mask:** a smoothstep of the heights blurred ~2.5 km. Tune it to the mountain zone's share of the map.
- **Puff field:** a tiling texture (for example 30 km, not a multiple of the noise tile) of domes. Each puff is a main dome plus 2–4 side bubbles with radii of 350–2,200 m, mostly small, and random peak heights, so lowering `t` adds puffs and grows them.
  - Print an offline table of area coverage against the amount, and pick a starting amount for 1–3 oktas over the lowlands and 4–6 over the range.
  - The outline remap roughly halves the visible area, so raise the amounts from the table and confirm in PIE.
  - Sample the field at twice its tile size (for example 60 km for a 30 km texture) for fewer, larger clouds like Epic's sky. That empties parts of the sky, so check coverage at several yaws and tell the user about the trade.
- **Wind direction:** derive downwind from the world layout: compare the coverage centroid with the review camera's yaw. Don't assume +X is east; a wrong axis drifts the cap's air along the crest instead of off it.

## Verification

- **Judge clouds only in PIE or game captures**, and wait at least 4 s after each camera move; volumetric clouds accumulate over frames.
  - One-shot Editor scene captures and `AutomationLibrary.take_high_res_screenshot` re-render without that history: the first smear the clouds, the second adds grain.
  - Grab real frames with the `Shot` console command (then move the newest file out of `Saved/Screenshots/WindowsEditor`) or with `SceneCaptureToolset.CaptureGameViewport`.
- **Grain ("fizzy" dots that crawl as clouds drift) and flicker are view-ray undersampling,** not the cloud's shape. The renderer spreads a view-sample budget (scaled by View Sample Count Scale) over the traced ray, from the layer entry out to the component's Tracing Max Distance (default 50 km); read the exact step-count formula and cvars in `VolumetricCloud.usf` and `VolumetricCloudRendering.cpp` rather than assuming it. Long grazing rays then step ~170 m even at 3×, coarser than cumulus detail, so backlit edges break into dots. It is worst near or inside the cloud slab and facing the sun. Fix in this order:
  1. **Tracing Max Distance 20 km** (`set_tracing_max_distance` in PIE, `tracing_max_distance` on the saved component): ~70 m steps at unchanged GPU cost. Afterwards check from the ground, in several directions, that horizon cloud and terrain-pinned cloud survive; with a 1 km layer bottom they did.
  2. **View Sample Count Scale 3** (`set_view_sample_count_scale` / `view_sample_count_scale`): frame-to-frame sky change 0.3 at 2×, 0.18 at 3× and 4×; +1.2 ms GPU over 2×, 4× +3.5 ms, 6× +5.7 ms.
- **Levers that measured worse or flat** (don't spend a session on them):
  - `r.VolumetricRenderTarget.Mode 1` (half-res tracing): it flickers about twice as much as mode 0 (less temporal accumulation) and costs more. Mode 3 (cinematic, full res) is smooth but costs ~60 ms.
  - A thinner cloud layer: barely changes flicker.
  - Half density, or a density floor to drop faint fragments: still fizzy; the floor also splits clouds into more fragments.
  - Softer or harder edges: no gain; harder edges are grainier.
- **When the user prefers an earlier or engine look, A/B it in the same PIE run before tuning anything.** Recreate it on the PIE MID (Epic's puffy sky: `Layout_CloudType` (1, 1, 1, 2) with your coverage amounts at 0), capture the same views with the same method, and measure grain on both. Then read the reference's parameter defaults (below) and copy its recipe. Sample-count, density-floor and edge levers don't close a gap that comes from the shape recipe.
- **Reproduce the user's view before measuring.** Read their camera with `UnrealEditorSubsystem.get_level_viewport_camera_info()` (they may be in the Editor viewport at cloud altitude) and put the PIE pawn there. Also review facing the sun, where forward scattering lights the edges, not only away from it. Clean metrics at your own review cameras are no evidence against a reported artifact.
- **Measure, then confirm by eye.** Freeze the cloud wind on the PIE MID (`Cloud_Wind_mps` 0) so every config sees the same sky, then grab consecutive `Shot` frames per config. *Grain* = mean |frame − 2 px Gaussian blur| on one frame; *flicker* = (Σ|Δframe| − |last − first|) / (N − 1), which ignores steady drift. Repeat the baseline in the same run (noise about ±0.1). Whole-frame means dilute a small artifact, so always compare same-region native crops side by side; for motion, pan the yaw about 4°/s through `set_control_rotation` and grab mid-turn. [scripts/pie_cloud_flicker.py](../scripts/pie_cloud_flicker.py) does all of this.
- **Check cap placement from above** (about 3 km up, pitched down toward the range). From a ground view, a bank behind the crest and one on the summits look alike.
- **Moving the PIE view:** set the PIE pawn's location and call `PlayerController.set_control_rotation`. Capture a view set with a slate post-tick state machine (see `ue-editor-scripting-and-python`, "Multi-frame work"); run cumulative variants on the MID and assemble a labelled grid.
- **Cost:** in PIE, toggle the cloud component's visibility (or `set_actor_hidden_in_game`) and compare `PerformanceService.frame_timing()` taken by the tick state machine after a settle. Measure each sample-count setting the same way. One reading: the cloud cost 1.7 ms GPU at 1×, 2.8 ms at 2× and 6.5 ms at 4× (shadows at 2×). GPU readings drift 1–3 ms between runs, so compare configs within one run. Report it as a PIE reading, not a packaged-build cost.

## Reading engine material graphs

- **Export:** `MaterialNodeService.export_material_graph` needs the full object path (`/Engine/.../M.M`); the package path returns nothing.
- **Export JSON shape:** a dict with `expressions` (each with `id`, `class`, `parameter_name`, `pos_x`/`pos_y` and `properties`, which holds `DefaultValue`, `Desc` and node settings), `connections` (`source_id`, `target_id`, `target_input`, `source_output_name`) and `output_connections`. Index expressions by `id` and build up/down adjacency from `connections` to trace a parameter to the output.
- **Named reroutes:** the export omits declaration-to-usage links, so ancestry traced through it misses them. Read real wiring with `MaterialEditingLibrary.get_inputs_for_material_expression`.
