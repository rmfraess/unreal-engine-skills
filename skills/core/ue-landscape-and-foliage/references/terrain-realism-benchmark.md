# Terrain realism benchmark against a real DEM

Deep dive for [../SKILL.md](../SKILL.md). Use it to judge whether game mountains or hills read as real, or to plan a landform pass toward a real-world reference ("like the Rockies", "like the Alps"). It turns "looks fake" into measured gaps and keeps the work off the Editor until a change is authorized.

## Procedure

1. **Get game heights offline first.** Rerun the repo's offline terrain generator into the scratch directory, or use an exported heightmap. This needs no Editor ownership and cannot dirty the map. Check that the regenerated min/max matches the saved evidence, and list any later saved edits it omits (for example road corridors). Decode 16-bit heights as `h_cm = (v - 32768) * ZScale / 128`.
2. **Fix the raster orientation before any directional metric.** Generators often write rows along +Y and columns along +X. With +X north and +Y east, `north_up = h.T[::-1, :]`, giving row = (Xmax - x)/step and col = (y - Ymin)/step. Skylines and hillshades come out mirrored or rotated if you skip this step.
3. **Fetch a real DEM of the analogous structure** at a similar cell size: a crest, its foothills and the plains it drains toward. For quick analysis, AWS Terrain Tiles (terrarium, no auth) work:
   ```python
   url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
   elev_m = R*256 + G + B/256 - 32768            # RGB as float64
   x = int((lon + 180) / 360 * 2**z)
   y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**z)
   cell_m = 156543.03392 * math.cos(math.radians(lat)) / 2**z   # z12 ≈ 29 m at 40°N
   ```
   Cache the tiles in scratch. Tile mosaics carry attribution terms, so for heights that ship in the game use a public-domain source and get acquisition/licence approval. For USGS 3DEP, one `exportImage` call returns a projected, cropped float raster:
   ```python
   base = 'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage'
   q = {'bbox': f'{xmin},{ymin},{xmax},{ymax}', 'bboxSR': 26913, 'imageSR': 26913,   # UTM 13N metres
        'size': f'{(xmax-xmin)//30},{(ymax-ymin)//30}', 'format': 'tiff', 'pixelType': 'F32',
        'interpolation': 'RSP_BilinearInterpolation', 'f': 'json'}         # -> {'href', 'extent', 'width', 'height'}
   dem = np.array(Image.open(downloaded_tif), dtype=np.float64)          # Pillow mode 'F', row 0 = north
   ```
   Give the bbox in the projected system: a lat/lon bbox with a fixed `size` is stretched to that aspect. Keep the returned `extent` (it can differ slightly from the request), the request URL and the file's sha256 beside the raster. Verify the georeference before use by reading the DEM at a few known summits and a town; a wrong formula or axis shows up as hundreds of metres of error. Max image is 8000 px per side.
4. **Compute metrics over comparable masks.** In the game, use the mountain layer weight > 0.5. In the real DEM, use cells more than ~500 m above the plains, plus the alpine zone. Report:
   - relief (p2 → p99.9)
   - slope p50/p90/p99/max
   - % of cells < 10° (valley floors, benches, cirque floors)
   - % of cells > 30°, > 40° and > 50°
   - residual std against a ~2 km and a ~250 m box mean

   Use numpy (`np.gradient` for slope, and a cumsum box filter for the means).
5. **Measure skylines from the story viewpoints.** For each azimuth in 0.25° steps, take the maximum elevation angle with the curvature drop `r²/(2R)·0.87` subtracted. Report the median and max angle, and peaks per 10° of azimuth (a peak must stand ≥ 0.1° above both sides within ±2°). Compare against the real range seen from an analogous town at an analogous distance. This shows whether the problem is size or shape.
6. **Make a same-scale hillshade side by side.** Resample the real DEM to the game cell size, crop equal kilometres, and use identical sun azimuth/altitude for both:
   ```python
   gy, gx = np.gradient(h, step); slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
   shade = cos(zen)*cos(slope) + sin(zen)*sin(slope)*cos(az - aspect)
   ```
   This one image shows the user the gap better than any table.
7. **Size each landform scale on screen from the acceptance views.** A grid cell spans `cell_m / (dist_m × radians(hfov) / width_px)` pixels. Compute it at the p0/p10/p50/p90 distance from each view camera to the mountain mask, and also report the height headroom (Z scale) and the distance from the range to the Landscape edge. Features smaller than about 3 cells (cliff bands, gullies, rock ribs) cannot be heights on that grid where a cell spans several pixels. They need material detail or placed meshes there, while broad forms stay in the Landscape. A range that runs into the Landscape edge needs ranges behind it, either from extra terrain or from backdrop meshes. This sets the by-scale split before you choose any mechanism.
8. **Fit the real range's profile into the game band before choosing a source range or scale.** Measure the game band from radial height profiles around the core (every 5° of azimuth): foot (mountain weight 0.1) → crest distance, crest → Landscape edge distance, and the foot and crest heights. Then measure the real range's elevation against distance from its crest. At uniform scale k, the band shows only the real relief found within `band_km / k` of the crest, times k. Broad ranges gain most of their relief across wide foothills: the Colorado Front Range drops only ~800 m in the first ~7 km east of the divide, so at 0.4× a 3 km band gets ~300 m of relief, not the ~1,000 m the whole range would give. A narrow band needs a range that rises steeply from a basin, a smaller relief target, or a wider band. Vertical exaggeration or radial compression brings back the uniformly steep slopes the realism pass exists to remove. Run this check with the offline warp prototype before you offer scale numbers, and report a misfit as a conflict between agreed constraints.

## Reading the numbers

| Signature | Gaussian-blob + noise terrain | Eroded real range |
|---|---|---|
| Median slope | Uniformly steep (~27°) | Gentler overall (~17°) with a steep alpine core (~25°) |
| Flat < 10° | ~7% | ~25% |
| Max slope | ~60° (smooth Gaussian flanks) | ~80° (headwalls, cliffs) |
| Plan view | Bead chain of domes; no valleys reach the foothills | Dendritic valleys draining off the crest, arêtes, cirques |

- **Similar angular height plus a different slope distribution means the fix is landform, not scale.** Do not raise peaks to fix a shape problem: the range then dominates views that an approved direction may want restrained.
- **Do not keep apparent size by matching the old peak envelope with a smooth offset.** A >3 km offset lifts the broad front shoulders, which then hide the real crest: the Front Range warp at 0.4x fell from 2.5 to 0.6 skyline peaks per 10° (as smooth as the placeholder blobs) while angular height rose. Re-run the skyline peak count after every height adjustment.
- **Compare skylines at real distances, not uniform-scale-equivalent ones.** A game viewpoint 8 km from the crest at 0.4x equals 20 km real, which is inside the real foothills. From real plains towns (Niwot, Longmont, Lafayette at 31–44 km), the Front Range crest stands only 2.5–2.9° high and 0.6–1.1° above the foothills, but shows ~5–6.5 peaks per 10° with 7.5–11.6% skyline roughness (std after a 3° moving average, as % of crest-over-foothill relief). A range "not high or jagged enough" usually lacks peak density, not angle. Fix it with separate scales (warp recipe below): pack more real crest along the arc (along k ~0.25), squeeze the real mountain front across into the band (across k ≈ band width / real front width, ~0.18), and set the vertical scale for the agreed height (~0.9). That gave ~4 peaks/10° at a slightly taller crest. Cost: much steeper slopes than real (median ~36°). Present it as a change to any agreed uniform-scale decision.
- **Check what stands in front of the crest along each key sightline.** Sample height and layer weights every 1 km along rays from the main viewpoints. A protection buffer (for example "≥ 3.6 km from every road edit") can keep smooth placeholder hills right in front of the new crest, and those read as domes hiding the peaks. Size buffers by what they protect (detail tiles and the village wide, distant road edits narrower), and report any narrowing as a change to an agreed rule. To explain a buffer, render a north-up top-down hillshade showing the protected features, each buffer outline, the changed area and the area each choice frees (with km² and the nearest-change distance); a map answers it faster than prose.
- **Noise added on top of blobs raises the residual std without creating drainage.** Residual alone never proves realism; judge by flat fraction, max slope and the hillshade.
- **A "far ridge" offset a short distance behind the near ridge merges into one massif** when the saddle is only tens of metres lower. Depth needs separate receding ranges. When the range sits near the Landscape edge, also check for an exposed world edge on the horizon.

## Physical basis for mountain features

Cite the cause with the look, so surface rules come from physics rather than taste:

- **Glacial versus fluvial shape:** ice carves cirques, aretes and U-shaped valleys above the former ice limit, and streams cut V-shaped valleys below it ([NPS Rocky Mountain geology](https://home.nps.gov/romo/learn/nature/geologicactivity.htm), [USGS](https://www.usgs.gov/geology-and-ecology-of-national-parks/rocky-mountain-national-park)).
- **Snow follows the wind:** prevailing winds scour crests and windward faces and load the lee slopes and hollows ([Niwot Ridge, Front Range](https://www.tandfonline.com/doi/full/10.1080/00040851.1987.12002600)). Work out which side the story viewpoint faces before placing the snow.
- **Cloud caps:** orographic lift forms cloud on the windward side, and seen from the lee it sits on the crest as a cap or wall that thins downwind ([WMO Cloud Atlas](https://cloudatlas.wmo.int/orographic-influences-on-the-windward-side.html)). Persistent crest cloud is therefore compatible with clear lowland light.
- **Treeline:** it follows a growing-season mean of about 6–7 °C ([Körner & Paulsen 2004](https://doi.org/10.1111/j.1365-2699.2003.01043.x)), with closed conifer forest below, wind-stunted krummholz at the limit, and tundra, rock and snow above ([NPS subalpine](https://www.nps.gov/romo/learn/nature/subalpine_ecosystem.htm)). Express it as a fraction of the crest relief when the game range is lower than the real one.

## From gaps to a plan

- **Order the work:** landform (erosion/drainage), then surface (rock/scree/snow/treeline from slope, altitude, aspect and flow), then atmosphere/clouds (aerial-perspective value layers), then vegetation representation, then horizon closure. Bake surface masks from the final heights; masks or material tuned on placeholder landforms must be redone after reshaping.
- **Real-DEM landforms are the cheapest source of authentic erosion.** Warping a real patch along the approved crest line, so valleys drain toward the lowlands, beats writing an erosion simulator or adding an external terrain tool. Label the result as visual interpretation, not canon. A warp recipe that runs offline in seconds (numpy, scipy, Pillow):
  - Game axis: order the crest anchors along the arc, extend both ends by a few km, resample every grid step and Gaussian-smooth (~1.5 km) so nearest-point projection does not fold on the concave side. Project zone cells onto the line for arc length `s` and signed offset `d` (positive `d` away from the core): find the nearest vertex with `cKDTree(line).query(workers=-1)`, then project onto its two adjacent segments and keep the closer foot. Nearest-vertex alone snaps `s` to the resample step; on steeply warped terrain that misplaces heights by ~7 m RMS (p99 ~28 m), which reads as bumpy relief. Use the same projection wherever the warp is sampled (heights, detail maps, masks).
  - Real axis: per DEM row, take the argmax of a 2 km-smoothed DEM inside an easting window around the crest, then smooth that line along northing (~8 km). Map `N = N0 ∓ s/k_along`, `E = E_axis(N) ∓ d/k_across`, and sample with `map_coordinates(order=1)`. Choose the travel direction so the real lowland side lands on the game's inner side; this avoids mirroring. Pick `N0` so a named summit lands on the main viewpoint's sightline. Fetch the DEM crop wide enough for `arc length / k_along` and assert that no sample falls outside it.
  - Heights: `game = k_up*real + C`. Fit C from the cells at the zone's foot. Stretched valleys then drop below the lowland, so floor them: below the foot level `f` (p25 of the old foot heights), keep only ~15% of the depth, `f + (core - f)*0.15`. Report the remaining foot step, crest heights, skyline angles and peaks per 10° against the agreed size tolerance.
  - Blend: `new = old*(1-m) + warped*m`, with `m = smoothstep(0.1, 0.5, old mountain weight)`. Cells with `m == 0` stay byte-identical, which the protection diff checks.
- **Protect accepted terrain.** Keep new relief inside the Landscape's current Z-scale range (see SKILL.md). Write it only inside a mask (a dedicated edit layer keeps it reversible), and diff every height outside the mask, expecting zero changes. In the Editor, export the live heightmap as the recovery point and check it equals the last committed shape, import the new heights, export again, and require a byte-identical match with the generated PNG before capturing or saving.
- **Surface rules under vertical exaggeration.** Drive snowline, treeline, aspect and the forest belt from real elevation and the real slope (`np.gradient(h * k_across / k_up, step)`), but let snow shed and rock show by the slope players see (`np.gradient(h, step)`). Otherwise every stretched face reads as real-gentle and stays white. Starting thresholds: snow sheds above ~60° visible, rock above treeline from ~50°, cliffs anywhere from ~66°. Sweep 3–4 threshold sets offline, report snow/rock % above treeline, and pick against the reference photos and any agreed snow cover in a side-by-side render before touching the Editor.
- **Crest cloud cap: real volumetric cloud first.** This user judged well-lit cloud cards "odd": they read as flat images. Build the cap as the lower layer of a real sky cloud system: the stock `VolumetricCloud` material instance with the crest coverage (`cloud_cover`-style mask) in `Layout_GlobalCloudMask`, trialled on transient PIE actors. Mapping, layer thickness and the PIE recipe are in `ue-lighting-and-lumen` `references/volumetric-clouds.md`. Keep the sky lighter than the crest bank so the cap still reads as the mountains' own cloud. The cards below are a stopgap only.
- **Stopgap crest cap: layered cloud cards.** Place 2–4 world-anchored translucent planes per crest segment at three depths (~−150 m, ~1.5 km and ~4 km behind the crest), bases 0–300 m below the crest, about 80% of the arc capped with real gaps, facing the mean of the review viewpoints. Use a procedural RGBA atlas (a few cloud variants stacked in rows) and one lit translucent two-sided material that reads row, opacity and mirror from custom primitive data, with a DepthFade where the cards meet terrain. Pitfalls:
  - Fade the atlas alpha to zero over the outer ~5% of each strip; otherwise the cloud is cut vertically at the card edge.
  - A flat, ridge-streaked cap style (low smooth top, ellipses stretched ~3× along the strip) reads more like an orographic cap than billowed cumulus from the review views.
  - Orient the engine plane (local XY, normal +Z, UV = (xy + 50)/100) with `MathLibrary.make_rot_from_zx(face, across)` where `across = (face.y, -face.x, 0)`, so texture-up is world-up; scale by width/100 and height/100.
  - Cards only hold from the side they face: from an off-axis viewpoint (~50° and beyond) back faces render dark and the bank looks detached. Check one off-axis capture before adoption; ranges seen from several sides need per-side card sets or volumetric cloud.
  - Editor-viewport cost of 25 cards was within noise; measure in PIE before scaling up.
- **Placed peak meshes (asset-pack mountain tiles) over the Landscape.** They add sub-grid detail (eroded ridges, rock faces, snow in gullies) at negligible cost: 22 Nanite peaks stayed within PIE noise (±0.5 ms GPU). This user rejected them in a side-by-side, because they read as a patchwork against the grid terrain and brought their own snow and rock colour. When the terrain is a warped real DEM, try the detail maps in the next item first: they come from the same landform, so they cannot mismatch it. If you trial a pack anyway, plan it offline from the heightmap, then judge it in PIE:
  - Pick summits as local maxima above the treeline. A wide spacing (~1.5 km) finds only the tallest, cloud-capped tops; ~0.9 km also picks up the lower peaks that stay visible below the cloud base.
  - Pack peaks are square terrain tiles with a flat base, pivot at the bottom centre. With the base set at the treeline, the base sticks out over lower foothills as a flat dark apron. Instead, scale each tile until its base sits ~20 m under the lowest ground in its rotated footprint (radius ≈ 0.71 × width). That forces ~2.5–3.5× scale, so the meshes cover most of the range rather than just the tops.
  - Detailed meshes beside smooth grid terrain read as a patchwork, most of all from altitude. Cover the whole visible crest or none of it.
  - Pack peaks bring their own baked snow, down to their foot, and near-black shadowed cliffs. Match them to the terrain's snowline and rock value through a project material instance before judging the look.
  - Peaks that rise into a volumetric cap read as ghostly snow ridges. Any cap mask derived from terrain heights must be regenerated from the new tops.
- **Sub-grid detail from a finer real DEM (detail normal + masks).** A 25 m Landscape grid cannot carry gullies, rock ribs or snow in hollows, but the same real area exists at finer resolution. USGS 3DEP has 10 m nationally and 1 m lidar in many places, with ~12× the fine relief of an upscale. Bake it into textures through the exact warp the heights use:
  1. Refactor the generator so one warp function serves both the heights and the detail script. Prove the refactor changed nothing by rerunning it and requiring byte-identical height outputs.
  2. Size the texel to the zone: 4 m texels over a 32 × 16 km zone fit 8192 × 4096, and 10 m source data is enough at that size. Compute the real area the warp samples first: separate along/across scales enlarge it (32 × 16 km in game was 69 × 133 km real).
  3. Fetch 10 × 10 km blocks at 1000 × 1000 px from the `exportImage` service above, with 4 threads, into `.npy` files plus a provenance JSON (request, extent, sha256 per TIFF). Commit the fetcher and the provenance, not the blocks (~450 MB). Retry a 5xx block once; if it still fails, fill it from the coarser DEM and record which block.
  4. Detail normal: take the fine-DEM gradient minus the gradient the Landscape grid already shades, and encode it tangent-space in RG, with a cavity term in B (0.5 = flat). Masks in RGBA are snow, cliff, scree and conifer, from the surface rules above. Chain the exclusive shares so each class takes its share of what is left, `cliff = c*(1-snow)`, `scree = r*(1-snow-cliff)`, `trees = t*(1-snow-cliff-scree)`, and assert the sum ≤ 1.
  5. Preview offline before import: a hillshade-style crop around the top summit. Look for grid or stair artefacts.
  6. Import as linear (sRGB off), BC7, World-group mips, clamp addressing. In the material use LinearColor-sampler texture objects with the zone rectangle as world-space UV bounds. Add a Normal output only after confirming nothing in the material reads the pixel normal. Extend the material through a separate Custom node (see `gd-implement` on wired Custom nodes). Add an LFS rule for the textures before committing.
  7. Verify in PIE from the same views before and after, with GPU timings and a still-camera flicker check. Measured cost: +80 PS instructions, GPU within noise, ~90 MB for two 8192 × 4096 BC7 textures with mips.

  State the limits up front. The detail maps change neither the silhouette, which still comes from the Landscape grid, nor the slope steepness the warp scales create; those are landform decisions.
- **Surface the conflicts before planning around them:**
  - a real-range reference against an approved restrained scale
  - reshaping terrain that was already accepted
  - canon traits missing from the scene (for example permanent cloud caps)
  - atmosphere used to hide unfinished landforms
