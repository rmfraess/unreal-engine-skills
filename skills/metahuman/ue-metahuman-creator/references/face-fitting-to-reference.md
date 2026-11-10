# Fitting a MetaHuman face to a front reference picture

Front-view landmark fitting (MediaPipe on the reference and on a render, then
`move_face_landmarks`) converges in about three rounds, but it only moves **feature positions as
seen from the front**. It does not change cheek fullness, cheekbone or jaw definition, soft tissue
under the jaw, or apparent age. Those come from the starting preset and the skin texture, so the
preset must be chosen for 3D form (see SKILL.md). Tell the user this ceiling before the first round.

## Procedure (VibeMetaHumans `MetaHumanCharacterService`)

1. **Preconditions.** Grooms cleared (move refuses with grooms on), face unrigged, preview spawned
   at the origin with zero rotation. Then `get_face_landmarks` positions are world centimetres
   (+Y toward the face, +Z up); confirm against the `FACIAL_L_Eye` / `FACIAL_R_Eye` sockets
   (about ±3 cm in X).
2. **Long-lens front camera.** Spawn a transient `CameraActor` at `(0, 160, eye_z - 2)`, yaw -90,
   `field_of_view` 15, `constrain_aspect_ratio` False, and `LevelEditorSubsystem.pilot_level_actor`
   it; capture with `SceneCaptureToolset.CaptureEditorViewport` (it returns the viewport's own size). A long lens keeps perspective
   close to a portrait photo's, and a known camera makes the sculpt points projectable.
3. **Project the sculpt landmarks** with the camera *as actually piloted*: read the camera actor's
   location, yaw and FOV in the same call that dumps the landmarks, never a constant (an orbit
   helper that places the camera relative to the head silently moves it by centimetres). General
   level camera: `fwd = (cos yaw, sin yaw, 0)`, `right = (-sin yaw, cos yaw, 0)`, `up = +Z`;
   `depth = (P-loc)·fwd`, `px = W/2 + f*((P-loc)·right)/depth`, `py = H/2 - f*((P-loc)·up)/depth`,
   `f = (W/2)/tan(fov/2)`; cm per pixel = `depth/f`. Draw them on the render once and check they
   land on eye corners, nostrils, lip corners, jaw.
4. **MediaPipe** (Tasks API; current releases have no `mp.solutions`):
   `uv run --no-project --python 3.12 --with mediapipe --with pillow --with numpy python ...`,
   `vision.FaceLandmarker` with the `face_landmarker.task` model from
   `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`.
   478 points on both the reference and a bald render.
5. **Align and measure.** 2D similarity (Umeyama) from reference points onto render points, using
   every point except the forehead/oval-top ones (hair hides them). Report the mean point distance
   as a % of the iris-to-iris distance; that is the convergence number to show the user.
6. **Targets.** For each sculpt landmark that is front-facing (`y > 3`), below brow + 2 cm, inside
   the MediaPipe bounds, and not in `likely_ears` / `likely_neck` / `likely_skull`: inverse-distance
   weight the displacement of its 8 nearest MediaPipe points, convert to cm (X, Z only), average
   with its mirror twin (x -> -x) so asymmetric photo noise cancels, zero X on the midline, gain 0.8.
   Send as deltas: `move_face_landmarks(c, targets, 'auto', 0.06, 12, 2.5, False, False)`.
7. **Recapture, re-dump landmarks, repeat.** Stop when the error stops falling meaningfully;
   then save the asset (the last commit is the rollback point) and compare side by side with the
   reference before claiming progress.

A low front error is not parity: the user judges three-quarter and profile too. Once the front
converges, switch to the multi-view fit below rather than reporting the front number as done.

## Multi-view fit (front + both three-quarters: adds depth)

1. **Match each reference's head angle.** Request `output_facial_transformation_matrixes=True` from
   the FaceLandmarker and read yaw on the reference and on a render at a known orbit angle; MediaPipe
   under-reads yaw (a 35 deg render read ~29 deg), so scale the reference yaw by that ratio to get the
   camera angle, then confirm the new render's yaw is within ~1 deg of the reference. Redo this
   whenever the reference set changes (e.g. haired -> buzz-cut edits): each generated view has its
   own head turn, and a stale camera angle makes the far cheek and brow read as a wrong shape.
2. **Per view:** dump landmarks + actual camera, capture, similarity-align reference points onto
   the render, read the 2D displacement at each projected sculpt landmark (8 nearest MediaPipe
   points, inverse-distance weighted) and express it in cm along that camera's right and up axes.
   Skip landmarks turned away from the camera (normal from a point inside the head · -fwd < ~0.25).
3. **Solve per landmark** for the 3D delta that best explains every view that sees it
   (least squares, weak ridge ~0.05 so unobserved directions stay 0), mirror-average twins, gain 0.7,
   apply, recapture all views. Keep the camera angles fixed across rounds or the numbers stop being
   comparable.
4. **Measure the reference's own consistency floor** before chasing numbers: reference three-quarter
   left vs the horizontally mirrored three-quarter right, and the front vs its mirror, with the same
   error metric (overall and per feature: eyes, brows, nose, lips, jaw/cheek outline, cheeks via
   `FaceLandmarksConnections`). A symmetric face cannot beat that floor; generated reference sets
   typically disagree by ~2.5% in three-quarter and ~4% on the jaw outline. Once a view is at or
   under its floor, more landmark fitting only trades one view against the other.
5. **Show the user side-by-side sheets, not just numbers:** per view, rotate/scale/translate each
   image so the two irises (468/473) land on the same pixels (pupils only, no shape fit), put
   reference | render (| after) next to each other, and draw the reference's horizontal guide lines
   (pupils, nose base, mouth, chin) across every panel. Do not warp the reference with a
   multi-point similarity fit or show a 50/50 blend: the fit spreads each feature's error over the
   face and the photo's contrast dominates the blend, so the sheet suggests parity that is not there.

## Levers for face shape (explain before the user picks a route)

| Lever | Controls | Limit |
|---|---|---|
| Starting preset | Everything not explicitly changed: form between sculpt points, ears, skin detail | Only a start |
| Sculpt landmarks (`move_face_landmarks`) | ~80-125 points in 3D; the solver keeps the face plausible | Surface *between* points follows the base face, so fleshy cheeks survive a converged fit; depth (Y) and cheek hollows need hand moves |
| Face coefficients (`get/set_face_coefficients`, ~1.4k values) | Whole-face mixes of presets or saved states | Not per-feature; for one feature use a preset feature transplant through the template import (see "Feature transplant from a preset") |
| Mesh conform (`import_from_custom_mesh`, `import_from_template`) | Any sculpted head | Custom mesh must be a full MetaHuman-frame body (feet z=0, facing +Y, A-pose, bald) or head + body pair. Template import needs MetaHuman topology but a **head-only** static mesh is enough (body constraints survive); the preview's own face mesh is a ready template, see "Head template round-trip" |
| Skin texture / accents / custom textures | Apparent age, pores, wrinkles | Much of an "older" read is the texture, not the shape |

A generated image-to-3D head (e.g. Meshy) is **neither a conform base nor a face-shape target**:
it uploads the references to a third-party service (needs the user's explicit OK), costs credits,
its hair is solid mesh, and it rebuilds a generic face that scores worse than a fitted MetaHuman.
Do not propose it for face shape; if the user asks for it anyway, score it first (step 6 below)
and use it only as a cross-check where it agrees with the flat references. The shape reference is
a hairless buzz-cut edit of the user's reference set.

## Generated 3D reference head (Meshy, measured in Blender)

1. **Generate** with `meshy_multi_image_to_3d` from the front plus one profile of a hairless
   (1-2 mm buzz-cut) reference set (image-prompt-engineer, multi-angle references), `ai_model
   latest`, `geometry_resolution 2k`, textured, `image_enhancement false`, `target_formats ["glb"]`
   (35 credits). Adding generated three-quarters fuses views that disagree with each other; hair in
   the inputs becomes a solid shell over skull, temples and ears. A shaved set reads older and
   heavier-browed and Meshy exaggerates that, so prefer the buzz cut. Save under the project's
   ignored `Saved/` folder. Portrait references come back as a bust (shoulders, clothing, solid
   hair, ~2.5 M triangles) with arbitrary scale and a few degrees of roll.
2. **Export the MetaHuman head** from the preview (`copy_mesh_from_skeletal_mesh`, render LOD0) to
   OBJ with one group per material ID; eyeball slots are `eyeLeft`/`eyeRight` (IDs 3/4), and the
   front-most vertex of each is the pupil. Convert Unreal cm to Blender m as
   `(x, -y, z) * 0.01` and **keep the face winding as exported**: Unreal's left-handed winding plus
   the y flip already gives outward normals in Blender (reversing it inverts every normal, which
   silently breaks normal-based filters and ray offsets). Left/right stay correct and the face
   points -Y (Blender Front view).
3. **Anchor and align:** scale = MetaHuman pupil distance / Meshy pupil distance (MediaPipe iris on a
   textured front ortho render of the Meshy head; iris points on an untextured clay render are
   ~6% off, so use the eyeball meshes on the MetaHuman side); level the roll from the two irises;
   put the pupil midpoints together in X/Z. **Set depth by the median midline-profile offset**
   (front ray hits per mm from the pupils to the chin), not by the pupils: pupil depth on the AI
   mesh put the whole face 1.35 cm forward.
4. **Deliver** a `.blend` with each head in its own collection, units in cm, textures packed, plus
   a profile table (forward depth per height, both heads) and a ref | MetaHuman | 50/50 overlay
   for front and profile.
5. **State the limits with the result:** every size is relative to the chosen anchor (one real
   number such as the pupil distance), not true cm; the hair shell makes skull, temple and
   silhouette widths useless (a silhouette width scan counts hair and ears; measure face widths by
   hand); and where the generated head disagrees with a flat reference (it projected the nose
   0.35-0.6 cm more than the matched profile image), the reference image the user chose stays the
   authority.
6. **Score it before trusting any of its shape.** Render the raw GLB in Blender (85 mm lens, head
   filling the frame, yaws 0, ±15-40 and 90) and run the same per-feature landmark metric against
   the original references, best yaw per three-quarter. If it scores worse than the MetaHuman on a
   view, it is no target there. Image-to-3D rebuilds a plausible generic face, not the specific
   likeness: three generations (with hair, buzz-cut, shaved inputs) all scored worse than the
   fitted MetaHuman on every view, and the user judged them off too. Compare models only within one
   render pipeline: changing the framing alone moved scores by up to 0.6.
7. **Never sculpt a gap seen only against the generated head.** A signed surface-distance heatmap
   (MetaHuman skin to nearest generated surface, hair masked by texture colour) showed a 1 cm
   "too-full cheek" that the real references did not support. Confirm direction against the flat
   references (signed outline offsets per view and side; consistent sign across views) before
   proposing a pass, and present any proxy finding to the user as a hypothesis.
8. **Use it as a cross-check, not a second target.** Sculpt a gap only where the flat-reference
   measurement and the 3D head agree on direction (brow mass did; the nose did not). Before calling
   a same-row depth difference a gap, compare the feature's *own* relief (crease depth below the lip
   and chin pad, brow over nasion): a feature sitting at a different height shows a large same-row
   difference with identical depth (a lower-lip crease 0.5 cm lower read as "0.4 cm deeper").

## Changing the base face after fitting

1. Save every state's coefficients to a JSON file first (`get_face_coefficients`): this is the
   rollback for an uncommitted fit, since `set_face_coefficients` restores it exactly (not across an
   `import_from_template`: see the round-trip).
2. Scout candidate bases in **three-quarter** view with the same long-lens camera: orbit it around
   the face at ~35 deg, z from the preview's `FACIAL_C_FacialRoot` socket (preset heights differ).
   Front captures hide the cheek and jaw form that decides the pick. To scout many presets in one
   Python call, render through a `SceneCapture2D` (`capture_scene()` then
   `RenderingLibrary.export_render_target`, `SCS_FINAL_TONE_CURVE_HDR`, fov 15, same pose as the
   piloted camera): it matches the viewport capture and renders synchronously, so create -> spawn ->
   shoot -> `end_edit` loops over a dozen presets in ~2 min. For a single feature (nose), compare
   IPD-normalised close-up crops of reference | current | presets and let the user pick by eye.
   When brushes can't reshape a feature (bulbous nose tip), transplant it from the chosen preset: same
   topology, so similarity-align the donor on a skin ring around the region and blend
   `base + w*(donor - base)` with a smoothstep fade (~0.7 cm), then template-import (~90% lands).
   Use the donor's shape as is; forcing it to the old measured length/projection rebuilt the round tip.
3. Mixing is linear: `blend = sum(w_i * coeffs_i) / sum(w_i)` lands between the inputs on the
   front-error measure. A face copied onto another character's body differs ~1% (the head adapts
   to the neck and body), so measure on the target character, not the scout.
4. Any mix or base swap discards most of the fit: rerun the front fit afterwards (~2-3 rounds back
   to the previous error). A mix keeps only part of the lean base's form; a 40% share of a fleshy
   face still dominates the lower face, so expect a hand pass on jaw angle and cheek hollows.

## Measuring a deficiency

Put a number on every item of a deficiency table before proposing a fix, and re-measure it before
sculpting. Sheets mislead on size and even direction.

- **Front, in IPD units** (MediaPipe iris 468-473), reference vs bald render: mouth `61-291`,
  cupid's bow `37-267`, upper lip `0-13`, lower lip `14-17`, nose wings `64-294`, tip `129-358`,
  bridge between the eyes `193-417` / `122-351`, inner canthi `133-362`, eye opening `159-145` /
  `386-374`, chin contour widths `148-377`, `176-400`, `149-378`, `150-379`, `136-365`, `172-397` and
  each pair's rise above `152` (the rise shows a V vs a flat chin). Vertical chain: nasion `168` ->
  `2` -> stomion (`13`+`14`)/2 -> `152`.
- **Pupil-aligned, not fitted.** Normalise both images by the two irises only (pupils at fixed
  pixels, IPD = 100%) and read widths, heights and contour offsets directly. A multi-point
  similarity fit hides a misplaced feature by sharing its error with the rest of the face.
- **Nose length: trust the profile, not the front.** The front nasion point `168` moves with brow
  and bridge shading (on a bald render it sat below the pupil line, on the reference above it), so
  front nasion-subnasale "too short" contradicted a profile tip already 0.2 cm too low. Use pupil ->
  subnasale `2` for the front and nasion-aligned tip height/projection from the profile.
- **Three-quarter contour offsets measure face wraparound.** Pupil-align a three-quarter pair and
  compare the far-side oval points (`127, 234, 93, 132, 58, 172` or their mirrors): render points
  outside the reference mean the lateral face (outer brow, cheekbone) sits too far forward, a flat
  face that shows as a brow shelf and bulging far cheek. Convert to depth with `/ sin(yaw)`. Front
  widths can match exactly while this is off. The two generated three-quarters disagree with each
  other, so act only on offsets with the same sign in both views or confirmed by eye in both.
- **Neck:** narrowest silhouette row 0.25-0.6 eye-to-chin heights below the chin (skin chroma
  `R - B > 25` mask, not background difference), divided by cheekbone width `234-454`, reference vs
  render. Measure before calling a neck thick or thin; the by-eye read has been backwards.
- **Before removing a small feature (chin dimple, crease), check it in every reference set** on a
  landmark-centred zoom crop (e.g. around `17`-`152`, haired and hairless side by side). A faint
  dimple is invisible on a full-face sheet, and calling it absent from one view nearly removed a
  user-requested cleft both sets actually show.
- **Never use point `10` (forehead top) for face-length ratios when the reference has a fringe**:
  MediaPipe guesses it under the hair, which turned a 2% short lower face into "3% long". Use the
  nasion chain above.
- **Profile:** align both face lines at the nasion (most backward point above the tip) and scale by
  nasion-to-chin height, then list the depth difference per 0.5 cm below the nasion, plus tip
  projection in front of the nasion and the bridge hump (max bulge over the nasion-tip chord).
  Aligning at the tip, or scaling by tip-to-chin, hides the nose itself. Automatic anchors
  (most-forward row = tip) pick the hair on a reference with a fringe or a full head of hair: set the
  tip and chin search bands by hand per reference image and draw the anchors on the overlay.
  For forehead work extend the rows to ~6 cm above the nasion and trust them only up to the
  reference's hairline (on a buzz-cut reference the stubble adds 0.1-0.3 cm above it; on a haired
  one the fringe adds centimetres).
- **Mesh coordinates for brushes:** read them from the exported vertices, not from guesses. Plot the
  midline (`|x| < 0.12`) as y-vs-z with a 1 cm grid to locate nasion, tip, subnasale, lips, groove,
  chin and menton, and snap each brush centre to the surface (`max y` of vertices near the target
  x/z).

## Hand sculpt passes (form the front fit cannot reach)

Use after the front fit has converged, when the user names a feature ("jaw is heavy", "eyes are
off", "ears") or the three-quarter view still differs.

1. **Diagnose before moving anything.** Crop the feature from the reference and the render at the
   same scale (normalise by MediaPipe iris distance 468-473), stack them, and compute ratios on both:
   eye width `|33-133| / IPD`, opening `|159-145| / |33-133|`, corner tilt. For ears, compare the
   profile (`03`/`05`) against a side render: lobe height vs nose base, top vs brow, distance back
   from the eye. Name each concrete difference to the user before sculpting.
2. **Snapshot coefficients** (`get_face_coefficients` -> JSON) before every pass; it is the exact
   rollback for an uncommitted state.
3. **Move symmetric deltas.** Define moves on the +X side only and give the mirror twin (nearest
   landmark to (-x, y, z), gap < 0.6 cm) the X-negated delta, so the face stays symmetric. Find
   indices by dumping landmarks near the feature (front-facing `y > 3`, by Z band) rather than
   trusting a remembered index list.
4. **Step sizes that register:** eye-corner moves under ~0.2 cm do not change the measured eye
   width; ~0.4 cm does. Lift lids in small steps (~0.1 cm): an overshoot in eye opening did not
   come back with a small reverse move. Jaw/cheek depth moves of 0.2-0.4 cm (Y back) are visible in
   three-quarter view.
5. **Re-measure all views after every pass.** If the front rises, the reference does not want that
   change from the front (e.g. narrowing a jaw the photo shows wide): run one front-fit round, which
   restores the front widths while keeping the depth moves. If the multi-view errors rise or the
   change is barely visible, restore the snapshot rather than stacking more moves.

**When the user still sees no parity but every metric sits at the reference floor, stop
measuring-driven passes.** Landmarks see feature positions, not volume, ear shape, nose-wing shape
or lid shape, so the user's eye is the better instrument there. Ask for a marked-up comparison
sheet (pupil-aligned ref | render side by side per view, hairless references if available): each mark with a
direction ("wings narrower", "ears stick out less"). Turn each mark into one measured brush on the
test copy. Also rule out presentation gaps first (bald vs hair, studio light, skin age); see the
confound checks below.

Markup sheet contents: (1) per front/three-quarter view, reference | render side by side at equal
pupil distance with reference guide lines (see multi-view step 5); (2) a profile panel: reference | render | render with the reference outline.
Build the profile panel from the profile metric's anchor rows (nasion, tip, chin on both images):
scale the render by the ratio of nasion-to-chin heights, shift it so both nasions share a row, and
set each crop's left edge from the first non-background pixel on the tip row so both noses share a
column; crop around the face, never the image centre (a centred crop cuts a profile face that sits
off-centre). Re-score the landmark metric against the new reference set and call it a new
baseline, not comparable with scores against the old set. In the message, list measured profile
gaps (cm, with sign meaning) separately from by-eye observations, and name any presentation gap
(missing brows) the user should ignore while marking.

**Surface form is beyond sculpt points.** Jaw-line crispness into the neck, cheek hollows under the
cheekbone, nostril/tip roundness and brow-ridge mass live *between* landmarks: hand passes on them
barely register and push the measured error up. When overlays show those gaps with the landmark
error already at the reference floor, stop landmark work and (a) rule out the confounds first —
render once with a key light matched to the references (flat Studio light hides hollows a
directional key carves) and once with a younger skin texture as a throwaway A/B (preset textures
carry nasolabial and age detail that reads as fleshy form) — then (b) move to a mesh conform of an
edited copy of the current head ("Head template round-trip" below), which fits the whole surface
and uploads nothing. Neck-to-jaw separation in the front view is mostly the **body** neck (the
face conform cannot move the neck below the seam): test a smaller `Neck` body constraint for that,
on the test copy first: `set_body_constraints(c, '{"Neck": 37}', False, False)` takes raw cm and
returns before/after for every measurement; report the coupled moves (3 cm off the neck also took
~3.7 cm off Neck Base and ~1 cm off shoulder height).

### Confound checks (throwaway, restore exactly)

- Lighting: on the `Studio` map, save `KeyLight`/`FillLight`/`AmbientLight` location, rotation,
  intensity and `source_radius` to JSON (once; a second match must not overwrite the originals),
  then place the key from the reference's side at about 20 deg azimuth and 15 deg elevation, 300 cm
  from the head, aimed with `MathLibrary.find_look_at_rotation(light_loc, head)`, `source_radius`
  ~40 for soft portrait shadows, fill ~0.45x the key. Studio's default key (~35 deg up, hard)
  carves brow, nose and chin shadows the soft generated references lack. Keep the matched light for
  every later comparison capture so before/after sheets share it; restore from JSON and assert the
  deltas are ~0 when done. View-only: never save the map.
- Texture: read the candidate presets' `get_settings(c,'skin')['settings']['skin']['faceTextureIndex']`
  and set it on the character with `set_settings(c,'skin', {'skin': {'faceTextureIndex': n}})`;
  capture each under the matched light, then set the original index back and save.

### Head template round-trip (edit the whole face surface)

Run it on a **test copy** (`create_character(dir, name, source)`) and `end_edit` the original
before spawning the copy (one preview at a time). Shortcut: when the real character's file on disk
is byte-identical to a hash-checked backup (rollback = copy the backup back with the Editor closed),
import straight into the real character and skip steps 6-7; still export its positions first and
confirm they equal the base the brushes were made from. Importing the same written template into
the test copy afterwards syncs its face for groom tests.

1. **Export the preview face mesh.** Find the preview's `SkeletalMeshComponent` that has socket
   `FACIAL_C_FacialRoot`, assert it sits at the origin unrotated, then
   `GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(asset, DynamicMesh(), opts, lod)` with
   `lod_type=RENDER_DATA, lod_index=0`, and `GeometryScript_MeshQueries.get_all_vertex_positions`
   (Python returns `(mesh, list, has_gaps)`; assert no gaps). Dump positions to a float32 file.
2. **Edit positions outside the Editor** (numpy), keeping vertex order.
3. **Write the template.** Fresh copy of the same mesh -> `GeometryScript_MeshEdits.set_all_mesh_vertex_positions`
   -> **delete every triangle whose material ID is not 0 (skin)** -> `copy_mesh_to_static_mesh` into a
   static mesh asset (seed it once by FBX-exporting the face mesh and importing it as a static mesh).
   Eyes, lashes, eye-edge and teeth share UV space with the skin and the template import matches by
   UV, so leaving them in drags single skin vertices onto them (13 cm spikes).
4. **Conform:** `import_from_template(test_copy, static_mesh, '', '', '')`, re-export the fitted
   positions and measure what landed per brush (projection of achieved onto intended move over the
   vertices each brush moved >= 50% of its peak; face brushes landed 94-98%) and the drift where
   nothing was wanted (mean ~0.01 cm). An identity round-trip first proves the path.
5. Capture all views, run the per-feature metric, build ref | before | after sheets, judge by eye.
6. **Before applying to the real character, copy its `.uasset` (or commit it)** and hash-check the
   copy. A template import changes face state beyond the ~1.4k coefficients: restoring the
   pre-import coefficients left the head ~0.14 cm mean / ~0.9 cm max off its original shape, so
   coefficient snapshots are no rollback here. Explain this to the user when proposing the copy-over.
7. **Apply to the real character:** `end_edit` the test copy, spawn the real one, export its current
   positions and confirm they match the base the edit was made from (mean < ~0.02 cm), import the
   same written template, re-export and confirm it equals the test copy's fitted result, re-apply
   any body constraint tested on the copy (`Neck`), recapture all views, then save.
8. **Discard a rejected import on the real character** without touching the backup: `end_edit`,
   `EditorLoadingAndSavingUtils.reload_packages(<the character and template packages>,
   ReloadPackagesInteractionMode.ASSUME_POSITIVE)`, respawn, re-export and confirm max difference 0
   against the saved base. Never save between a trial import and its verdict.

### Feature transplant from a preset (nose, philtrum: form brushes cannot reach)

When the user says a feature looks wrong while its measured numbers match (nose length, tip
projection and alar width within ~0.1 cm, yet the tip is a round ball, wings flare and nostrils show),
the gap is the base face's feature form. Spot brushes on the tip do not change it (two tip passes
left no visible change). Every preset shares the character's topology, so take the feature from a
preset instead:

1. **Scout donors** with the SceneCapture batch (see "Changing the base face" step 2): for each
   preset `show` -> `headmesh.export('scout_<Name>')` -> front + three-quarter shot -> `end_edit`.
   Build IPD-normalised nose crops (reference | current | presets, front and three-quarter rows),
   ignore skin colour, and let the user pick; female presets are valid donors for one feature.
2. **Region mask on the base mesh:** front-facing skin (`y > ~7.5` for the nose) inside a
   half-width-by-height table from the nostril base/philtrum up to the nasion, wide enough to
   include the alar-facial grooves (a mask stopping at the wings keeps the base's deep grooves),
   with a ~0.7 cm smoothstep fade outside it; assert nothing outside the fade moves.
3. **Align the donor** with a similarity fit (Umeyama: rotation, uniform scale, translation) on a
   ring of skin 0.7-1.9 cm outside the region, then `new = base + w * (aligned_donor - base)`.
4. **Keep the donor's own proportions.** Remapping its heights and tip projection to the base's
   measured nose length made the tip bigger and rounder; the as-is donor read closest to it.
5. Template-import on the test copy (landed ~90%, skin drift elsewhere <= 0.06 cm, no seam), shoot
   all four angles, show reference | current | transplant | donor crops plus a full-face sheet. Two
   variants of the transplant count as the method's two attempts; a donor's own tip shape is the
   ceiling of this lever.

Sculpting the chin, jaw and throat this way (radial brushes on the exported positions, below):

- **Diagnose chin strength across the whole profile chain before moving the chin.** Compare nose
  projection and tip, lip projection, the groove under the lower lip, and chin point on a profile
  pair, plus chin width/squareness and any cleft in front crops. A chin sitting behind the lower lip
  can be the nose and lips over-projecting, not the chin receding; pushing the chin forward then
  over-pronounces it (users rejected ~0.5-1 cm pushes). Fix the dominant neighbour first, and treat
  a cleft as a small local feature (see below).
- **Set the seam guard from the mesh, not a guess:** find the exported head mesh's lowest Z (the
  body seam; ~158 cm on a 198 cm body) and pin only a 2 cm band above it. A guard several cm higher
  silently blocks throat work.
- **What survives the import:** face-surface brushes land almost whole (~95% of a 0.6 cm chin push
  at 2.4 cm radius; 94-98% of 0.17-0.35 cm nose, brow and chin-pad brushes at 1.1-1.8 cm radius;
  100% of a 0.2 cm deep chin cleft from stacked r 0.65 cm midline brushes, so a cleft goes through
  the import), but a throat bump (Adam's apple, r 1.1-1.8 cm, 0.45-1 cm high) landed only ~0.15 cm, even at
  double strength. Under-jaw and jaw-angle brushes at the face/neck border also landed only
  23-46% (0.36 cm jaw-angle move landed 0.08 cm; the lower-border band 46%), while nose, bridge
  and chin-corner brushes in the same pass landed 99-100%. Upper-lid brushes land ~72-75%, but a straight-down lid move lets the cornea bulge poke
  through the lid (dark notch above the iris at 0.05 cm, scalloped lid line at 0.11 cm): give lid
  moves a forward (+Y) component and check a zoomed eye crop before saving. Measure landed vs wanted per brush; when a local feature is stripped, it belongs
  to a post-build mesh or normal-map edit, so stop after one rescaled retry and tell the user.
- **Order the post-build edit last.** It needs a rigged, assembled character, and any later sculpt
  or conform resets the rig to `Unrigged` (rigging is a cloud step), so a post-build trial before
  the face is final means rigging and building twice. Sequence: finish template-import passes ->
  rig -> assemble -> scripted, re-runnable post-build edit (jaw border, throat, lids). Check
  `rig_state` in the import result before proposing it.
- **Hair work does not gate or freeze the face.** Groom roots sit on the scalp above the hairline,
  which face passes do not move, and groom bindings rebuild after every import. Do not propose
  "freeze the face before hair": hair and face iteration run in parallel; only sculpt-before-rig is a
  real ordering rule.

What this lever does and does not buy:

- Driving it with the multi-view MediaPipe displacements (RBF field over ~1 cm-spaced face centres,
  skull/ears/neck pinned, mirrored constraints) pushes every view under the reference floor, but
  moves are ~0.1 cm and the result is visually unchanged: landmark error cannot see form.
- **Ridge features (brow ridge, jaw line) need one continuous band, not a few spot brushes.** Two
  or three separate brushes along the brow read as lumps and a frown between the brows from the
  front. Instead place brushes every ~0.35 cm along the ridge (r ~1.3, mirrored, surface-snapped),
  taper the amplitude toward the ends (`a = k * (1 - 0.55 * (x / x_end)^2)`), and calibrate `k` in
  vertex space before importing: run the brush script, read the peak displacement at the centre,
  rescale `k` to the measured gap, repeat until it matches (two iterations). A 0.20 cm brow band
  landed 99% and closed most of the profile gap with no crease.
- **Broad planes (forehead, cheek fronts) take a displacement field, not brushes.** Move every
  front-facing skin vertex (`y > ~2`, so the back of the skull stays put) along +Y by
  `np.interp(height_above_nasion, H, D)` where `H/D` is the profile metric's ref-minus-ours table,
  times a lateral weight (1 to |x| 2.5 cm, cosine to 0 by the temples at ~6 cm). Find the nasion on
  the mesh the way the profile metric does (most backward midline point 0.9-4.2 cm above the tip),
  hold the last trusted value a little past the measured range and fade to 0 over ~2.5 cm so no
  step forms. Self-check the script on its own output (100%) before writing the template. A 0.7 cm
  peak forehead field landed 95% (drift elsewhere <= 0.07 cm) and brought the profile within
  0.03 cm of the reference with a smooth surface.
- Scripted radial brushes are not a sculptor: broad ~0.2-0.5 cm brushes land but can be invisible,
  and ~1.4 cm overlapping brushes leave creases and silhouette notches. Small detail brushes
  (r 0.4-0.8 cm: lip crease, philtrum columns, tip sides) were invisible at 0.08-0.16 cm and read
  cleanly at 1.5-2x that (~0.15-0.3 cm); judge each on a zoomed ref | before | after crop. Do not escalate brush strength; take
  the remaining form to a person sculpting smoothly (Blender on the exported head) or accept it,
  and say which the user wants.
- GeometryScript Python quirks: `get_num_triangle_i_ds` is the max ID (gaps included), not a
  count; `get_all_triangle_material_i_ds` returns `(mesh, list, ...)` and lists need
  `GeometryScript_List.convert_index_list_to_array`.

**Ears.** `move_face_landmarks` refuses the whole batch if any target is in `likely_ears` unless
`bAllowEars` is True (ear moves have crumpled ears before). Send ear moves in their own call with
the override, ≤0.6 cm per step, snapshot first, and check front *and* side captures for crumpling.
There are only two ear points per side (upper, lower), so protrusion and lobe height move a
little; overall ear size and helix shape are beyond this lever. Say so rather than forcing it.

**Eyes without eyebrows.** On a bald render MediaPipe's brow points land on the brow ridge, so
brow-to-lid ratios are not comparable with a reference that has thick brows; judge eye openness
again once eyebrows are on. Put brows/hair on the **test copy** for that judgement, see "Groom
preview timing" below. Library brows read much thinner than thick generated-reference brows.

### Groom preview timing (hair/brows on a Creator preview)

1. Set slot items and colour (`add_wardrobe_item`, `set_wardrobe_item_parameters` with
   `Melanin`/`Redness`), then call `assemble_for_preview(c)`. A preview spawned after an Editor
   restart has **no groom components at all** until this runs, even though `get_summary` lists the
   selections.
2. Every groom add or colour change hides the grooms until their binding rebuilds: **2-3 minutes**,
   with nothing in the log. Wait >= 3 min (check the health heartbeat meanwhile), then capture.
   A bald capture before that is not a failure; do not clear/re-select slots or recolour to "fix" it,
   each change restarts the wait. Brows can bind minutes before the hair (hair took ~5 min), so
   judge each groom only once its own strands render. Change hair and brows in the same call so
   both candidates share one wait. A `import_from_template` also restarts the wait: front captures
   taken right after a sculpt import show a bare brow ridge (it reads as a shelf), so recapture the
   front after the brows rebind before the user's verdict or a commit, and label early shots.
3. Verify wiring read-only if still bald: the preview actor's `GroomComponent`s should have
   `groom_asset` and a transient `binding_asset`, attached to `Face`. If they are wired and still
   bald well past 3 min (log stuck at `Waiting for groom bindings to be ready 0/1`), restart the
   Editor, then step 1 again. If brows are still bald after two such routes, stop re-selecting
   (two-attempt rule): shape work does not need brows, so capture anyway, label the sheet
   "brows not rendering", and discount brow landmark scores until the brows show again.
4. Canon-dark auburn-brown hair: `Melanin` ~0.72, `Redness` ~0.62 (0.55/0.5 reads golden-brown).
5. **Pick styles from the full list against the cut in every reference view.** Describe the
   reference cut from front, three-quarter *and* profile (length at sides/nape, ear coverage,
   volume on top, wave, fringe) before naming a candidate, then read `list_wardrobe_items('Hair')`
   and shortlist by those traits; names like `M_`/`S_` say length, not shape. If no library style
   matches, say so early and offer a custom groom as a user decision instead of cycling styles at
   ~3 min each.
6. **Custom hair is an artist task, not a generator.** A rule-based Blender generator (strands grown
   from the scalp inside a generated head's hair shell, clumped and curled) and the free Fab head
   grooms were both judged visibly bad by the user. Do not offer more generator passes or another
   free-listing sweep as the route; present the options as hand-placed guide curves (a person in
   Blender), a paid groom the user picks, or pausing hair, and keep face work going meanwhile.

## Pitfalls

- `EditorActorSubsystem.get_all_level_actors()` does not return transient actors; find the fitting
  camera again with `GameplayStatics.get_all_actors_of_class(world, unreal.CameraActor)`.
- Prefer a `SceneCapture2D` helper that shoots all four angles inside one Python call (pose it like
  the piloted camera, `capture_scene()`, `export_render_target`): it matches the viewport capture and
  cannot skip a view. With the viewport capture tool, capture strictly as aim -> capture -> aim ->
  capture; two aim calls before a capture silently drop a view (the viewport keeps only the last
  angle), a slip that recurs even when known, and the gap shows only when the sheet is built.
- Before a test-copy pass, sync the copy to the real character by writing the real character's
  exported positions into the template and importing it into the copy, then confirm mean < ~0.02
  cm; strip the copy's hair (its saved wardrobe may carry hair the real character does not), and do
  not save either asset before the user's verdict.
- Spawning even a transient actor marks the open map dirty; on the engine `Studio` lighting map
  never save it.
- Profile silhouettes: the hair fringe can stick out as far as the nose, so "most forward point of
  the face line" picks the fringe as the nose tip. Use hand-set row bands (see "Measuring a
  deficiency") and draw the chosen anchor rows on the mask before using any profile-derived depth.
- Head and body references from one generated set can disagree (a slimmer neck in the head
  shots than the body shot); ask which governs instead of silently matching one.
