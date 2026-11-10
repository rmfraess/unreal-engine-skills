# Volumetric clouds (UE 5.8)

Deep dive for [../SKILL.md](../SKILL.md): real sky clouds from the stock material, what that material cannot place and why, and how to trial cloud changes without risking the map.

User preference: distant cloud banks must be real volumetric clouds. Translucent cloud cards read as flat images even when well lit, so use them only as a stopgap. When clouds sit on a crest, the open sky should carry real clouds too, so the crest bank reads as the lower layer of one cloud system.

## Order of work

1. **Prove the stock cloud first, in PIE** (recipe below). Spawn `/Script/Engine.VolumetricCloud`; its component already uses `/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst`. The defaults (layer bottom 5 km, height 10 km) read as a natural fair-weather sky. A base at summit height with a 6 km layer (1.1 km over 1.0-1.4 km peaks) also reads natural and puts cumulus bases at summit level; a thin layer (about 1.5 km) squashes the sky.
2. **Configure through a `MaterialInstanceConstant` of the stock instance**, saved before any cloud component uses it. Parameter changes reuse the parent's compiled shaders, so nothing recompiles under the renderer. Start from `clear_all_material_instance_parameters` so a builder never carries stale overrides.
3. **Zero the horizontal wind:** set `Layout_WindControls` to `(0, 0, 0.5, 0.333)` (the default with x/y zeroed). Horizontal wind slides the whole cloud layout across the world, so anything placed in it drifts away; vertical wind only evolves the shapes in place.
4. **Judge clouds only in PIE or game captures**, after about 4 s of settling at each view. One-shot Editor scene captures lack the cloud's temporal history and show smeared, streaked clouds that are not what the game shows.
5. **Persist the actor only after the PIE trial looks right from every review view**, then measure its cost with the in-PIE A/B below.
6. **Write a custom cloud material only for what the stock parameters cannot do** (next section). Set the Volume domain and `used_with_volumetric_cloud` before the first save and before it is assigned to any cloud component. Compile it unassigned and wait for shaders, then assign it in PIE. Never toggle that flag or recompile while the material is on a live cloud component: that path crashed the renderer. Without the flag it renders nothing and SceneCapture shots give no hint; only the viewport prints the warning.

## What the stock material cannot place: summit-sized clouds

A cloud cap on a mountain crest could not be made from the stock material's parameters; treat it as custom-material work (that path is not yet proven). The mechanisms, so the same routes are not retried:

- **`Layout_GlobalCloudMask` makes boxes.** Its density (strength `Layout_CloudTypeMask`, RGB per type, alpha overall) is added after the height profile and noise erosion (the graph's "Add additive mask" node), so masked cloud is uniform through the layer: flat-sided boxes at any strength or layer thickness. Its UV is world km / `Layout_CloudGlobalScale` (256) + 0.5.
- **Pattern-placed features below the noise scale fail.** `Layout_CloudGlobalPattern` (RGBA = stratocumulus, altostratus, cirrostratus, nimbostratus; UV = world km / 256 x `Layout_CloudPerTypeScale`, wrapping) picks a row of `Layout_CloudHeightProfile` (UV = normalised altitude in layer, pattern value; decoded as value - 0.5 after a weighted max over the types, weights `Layout_CloudType`). The 3D noise works at several km, so km-scale patches are erased at weight 1 and become full-height columns when boosted; a custom profile texture gave faint streaky curtains.
- **Diagnose one type at a time** with `Layout_CloudType` (for example `(1,0,0,0)`); `Cloud_GlobalCoverage` -1 clears the sky, and raising it above the default -0.2 quickly turns a low layer overcast.

## Reading the stock graph

- Stop PIE first: `MaterialNodeService` returns empty graphs and lists while PIE runs. Pass the full object path, `export_material_graph('/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud.m_SimpleVolumetricCloud')`; the package path alone returns nothing.
- The export omits parameter names and named-reroute links (usage nodes do not record their declaration). Identify parameter nodes by their `Desc` text, and trace through reroutes by elimination: list every `TextureSample` with its UV chain and follow node positions.
- Engine HDR textures export with `AssetExportTask` to `.exr` (`T_CloudPattern` is 1024² float RGBA, `T_Profile_08` 256²); read them offline with `uv run --no-project --with OpenEXR --with numpy`.

## PIE trial recipe for risky rendering features

PIE actors are transient, so a renderer crash leaves no dirty map and no Restore Packages dialog on relaunch.

1. Confirm the Editor map has no dirty packages, then `vibeue.exec_tool('EditorToolset.EditorAppToolset', 'StartPIE')`.
2. `r = json.loads(unreal.PIEActorService.spawn_actor('server', '/Script/Engine.VolumetricCloud', unreal.Transform(), 'AlwaysSpawn', False, 'TEST_Cloud'))`, then `unreal.find_object(None, r['actor_path'])`. Trial materials: `unreal.MaterialLibrary.create_dynamic_material_instance(game_world, parent)` and `component.set_material(mid)`. A saved cloud actor appears in PIE too, so trial its parameters on a dynamic instance of its material.
3. Move the view directly: `pawn.set_actor_location(loc, False, True)` and `pc.set_control_rotation(unreal.Rotator(roll=0, pitch=p, yaw=y))`, using the player controller from `GameplayStatics.get_player_controller(game_world, 0)`.
4. For a parameter sweep or a fixed view set, drive one call's worth of work with a post-tick state machine (set parameters or view, wait about 4 s, `unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, path)`, next) and write a done-marker file; see the multi-frame rule in `ue-editor-scripting-and-python`. For a single look, the MCP `capture_image` tool with `source='game'` works, but any Editor drawer overlapping the PIE window lands in the image.
5. **Cost A/B in one PIE session:** from the state machine, sample `PerformanceService.frame_timing()` every 0.5 s for about 6 s with the cloud visible, then `set_actor_hidden_in_game(True)` and repeat. Compare medians and min-max ranges; claim a cost only when the ranges separate. The stock sky cost about 0.8 ms GPU in one 1600x900 outdoor view.
6. `PIEActorService.destroy_all()`, `StopPIE`, then verify there are no dirty packages and no new actor in the Editor map.
