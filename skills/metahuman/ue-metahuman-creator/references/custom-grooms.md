# Own hair and brow grooms for a Creator character (UE 5.9)

Use when no library style matches the reference and the user rules out paid grooms or wants own
tools. "No library style matches" is the user's verdict on the whole library, not yours on a
sample: see the hair and brows planning note in SKILL.md before starting. Creator accepts a groom you generate: it selects, assembles, saves and reloads like a library
item. The technical route below is proven; the look is a draft until the user has judged it in the
Editor beside the reference.

## How Creator carries a groom

A groom wardrobe item is a `MetaHumanWardrobeItem` whose `principal_asset` is a `GroomBindingAsset`
with source and target both `/MetaHumanCharacter/Optional/Grooms/GroomMesh/SKM_Groom_Head_Legacy01`
(the "groom head"). At assembly the pipeline duplicates the binding and carries the strands to the
character's face mesh by UV. The groom head shares the face's UV layout (same skin triangles), so:

- **Author on the character, export on the groom head.** Work in the character's own space so
  previews and measurements are against the real head, then map every strand to the groom head.
- **Brows (short, on the skin):** per strand point, closest skin point on the character -> its UV
  -> the same UV on the groom head, plus the point's height off the skin along the groom head's
  normal, scaled by the local size ratio of the two heads.
- **Head hair (long):** a smooth warp fitted to skin points the two heads share by UV (thin-plate,
  ~1,000 points; ~0.5 mm error on held-out points), then snap each root to the groom head's skin by
  UV. Per-vertex UVs are meaningless on triangles that straddle a UV seam (back of the head) and a
  few mouth/seam vertices find no match: leave those out of the fit and let the warp alone place
  those roots.

## Procedure

1. **Dump both heads once**: positions, triangles, material IDs and per-vertex UVs of the
   character's preview face mesh and of the groom head (`copy_mesh_from_skeletal_mesh`, render
   LOD0; skin is material 0).
2. **Generate strands** (numpy/scipy outside the Editor), recipes below.
3. **Preview offline before every import**: flat-shaded head triangles plus strands as lines,
   sorted back to front, four views beside the reference. It takes seconds against a 5-7 minute
   bind and shows silhouette, coverage, hairline and bare scalp; it does not show shading or
   colour. Iterate here freely; only Editor rounds count against the per-method attempt cap.
4. **Export Alembic from Blender**: one legacy curve object, one poly spline per strand, point
   radius = half the width. Blender writes Y-up `(x, z, -y)` and Unreal reads it raw, so put a
   point at `(X, -Z, Y)` in Blender to get `(X, Y, Z)` cm in Unreal with no import conversion.
   60-90k strands of 18 points export in seconds (20-30 MB).
5. **Import and wire** (one Python call):
   - `AssetImportTask` with `automated`, `replace_existing`, `options = GroomImportOptions()`.
   - Copy `hair_groups_materials` and `hair_groups_rendering` from a library groom of the same
     kind; set `HairWidth` in the rendering group's geometry settings (it overrides file widths).
   - **Copy `enable_global_interpolation` and `hair_groups_lod` from that library groom too.**
     Library hair has global interpolation on (strands are warped onto the character's head),
     library brows have it off (each strand only follows its root), and a fresh import has it off.
     Hair left off comes out at the groom head's size (13% small in one case), tight to the skull.
   - `GroomLibrary.create_new_groom_binding_asset_with_path(path, groom, head, 100, head, 0)`.
   - Duplicate a library `WI_*` item of the same slot and point its `principal_asset` at the
     binding: `ref.import_text('(Asset="<path>",AssetIdentifier="<path>")')`.
   - Re-importing over the groom keeps the binding and the item; the next assembly picks it up.
6. **Select it like a library item**, set colour with `set_wardrobe_item_parameters`,
   `assemble_for_preview`, wait for the re-bind and check a hair pixel before judging (see "Groom
   preview timing" in the face-fitting reference). Change hair and brows in one call to share the
   wait.
7. **Save** the groom, binding and item assets, then the character; reload the character package
   and confirm the selections and colour parameters survived. Check the grooms folder is under LFS
   first (a 90k-strand groom is ~17 MB).

## Brow recipe

- Take placement from the target's painted brows: threshold dark pixels in the band above the
  eyes on a textured front ortho render, fit a centre line and half-thickness per side, and map
  head space to that render with an affine fit over shared vertices.
- **The mask misses the sparse hairs at the nose end.** Start the brow several millimetres inside
  the mask's inner edge and fade the density in, or the gap between the brows reads wide.
- **Brow hairs rise as they grow.** Treat each sampled point as the hair's middle and walk back
  half a length along the flow for the root, or the brow sits 1-3 mm high.
- Flow: fanned upward at the nose end, then lying outward, upper hairs angled down and lower hairs
  up so they meet on the centre line; turn down along the tail. 6-9 mm long, 7 points.
- Density and weight trade off: 1,800 strands per brow at width 0.010 read dark and bold but
  hard-edged and stuck-on; 1,500 with the edges thinning over the outer half read natural but
  lighter than a bold reference. Show the user both rather than tuning blind. `Melanin` 0.9 /
  `Redness` 0.5 read dark brown at that density (library brows never did).
- Measure the result by hiding the brow groom and diffing two captures; compare the band with the
  reference's in a pupil-aligned frame.
- **A brow at full density to its edge reads as a bar.** Keep a dense core and let density fall
  steadily to the upper and lower edges (to ~20% at the mask edge), over the first third at the
  nose end and the last half of the tail; make edge and tail hairs ~30% shorter and ~40% finer
  (file widths, `hair_width_override = False`). ~1,200 hairs a brow kept a bold brow's weight;
  900 with a narrow core read thin. Fade the paint underneath the same way.
- **Brow hair alone reads thin and short at the nose end: paint the brows into the face colour
  map under it.** Bold purchased heads do this (a library brow groom over a painted map). Splat
  the target's brow darkness into the character's UV space through the same head-to-render map
  and blend towards a dark brown at ~0.8. Allow paint where either side's mirrored mask has brow,
  since one side's mask often misses its nose-end hairs.
  - Apply it with `skin_settings.texture_material_overrides`: `enable_texture_overrides = True`,
    `texture_overrides.face = {unreal.FaceTextureType.BASECOLOR: texture}`, then
    `commit_skin_settings`. The override replaces the synthesised map: skin tone and freckle
    controls stop showing until the map is exported and painted again.
  - **Never run an asset export on `synthesized_face_textures`.** They are transient with no
    source data; `UTextureExporterGeneric` asserts and takes the Editor down. Draw the texture to
    an `RTF_RGBA8_SRGB` render target (`begin_draw_canvas_to_render_target`,
    `Canvas.draw_texture`) and `export_render_target`. That PNG is sRGB-encoded twice: decode it
    once before painting, then check a skin patch in a capture against one taken before (they
    matched within 2 of 255).
  - A changed map restarts the groom bind: wait before capturing, like any groom change.
- **When the brow groom changes, repaint the map from the groom itself.** Paint made from the
  conform target's brows stays as a thin arc under a different groom, with bare skin showing
  through the new hairs. Recipe (offline, seconds):
  1. Start from the exported map with no brows on it (look at it first), with any earlier fixes
     to that map applied again. Keep such fixes in one shared function so both painters use it,
     and prove a refactor by regenerating the old output byte for byte.
  2. Dump the head the groom is bound from (the binding's `source_skeletal_mesh`) with UVs. Every
     library groom head shares the face's UV layout, so no character mesh is needed: a hair
     point's texel is the UV of the closest skin point on that head. Confirm the layout once
     (nearest-UV distance between the head's and the face's skin vertices is ~0).
  3. Sample ~8 places per hair segment, closest skin point -> barycentric UV, count samples per
     texel, blur ~1.2 texels (1024 map), and blend towards the brow brown by
     `0.8 * clip(density / high percentile, 0, 1)`.
  4. Assert hairs are within ~1 cm of the skin and no hair's UV jumps: either failing means the
     wrong head.
  - **Grade the paint by density; do not saturate it.** Full strength from the 75th percentile
    up fills the whole hair band flat (the bar again, three times the old paint's height); the
    97th leaves a dark core fading into the hair tips. The percentile is a by-eye setting: say so.
  - Two dumps of different library heads have the same triangle count but not the same triangle
    order or vertex count: carry anything between heads by UV, never by index. Test an assumed
    correspondence against a shuffled control before using it.
  - Prove the new map is live with a per-pixel diff of same-camera captures before and after: at
    review size the two look alike. The diff also answers "was that dark patch the old paint?"
    (no change there means it was not).
  - Send the user a before/now sheet of full-resolution brow crops, front and three-quarter, and
    leave the trial unsaved until they answer; back up the character and texture packages first.
- **Slimming or reshaping a brow groom ("too tall", "too spread"): squeeze, do not trim.** Per
  side, fit the brow's middle line (cubic of height against distance from the midline, through
  the closest skin points), scale each skin point's height about that line (0.75 read as "a
  bit"), project back onto the binding head and add each point's original offset from the skin.
  Hairs keep their length, lift and count, so the brow gets denser as it gets slimmer; stray
  hairs above the edge are squeezed, not removed: say both beside the sheet.
  - **Moving a brow up or down uses the same projection**: subtract a drop from each skin
    point's height before projecting back, the drop interpolated over distance from the midline
    (inner end, pupil, outer third) so the brow can tilt as it moves. Amounts measured on the
    character are not the groom head's: fit an affine map over skin vertices shared by UV
    around the brows and divide by its height scale (1.14 in one case), and carry the pupil's
    position across with its width scale. Re-measure the brow edges on a capture afterwards.
  - **Sliding a brow sideways needs the step held while it is put back on the skin.** The
    nearest skin point pulls a sideways step back where the brow curves round to the temple, and
    down under the ridge: tails moved a third of the asked distance and drooped towards the eye
    corner. Set the wanted x and height, project, restore x and height, and repeat (8 rounds)
    before the final projection. Then drop hairs whose longest segment more than doubled: a few
    slid to the edge of the eye socket land half on the lid, and the paint step's UV-jump check
    fails on them. Check height by quarter of the brow, inner to outer, before and after.
  - **Narrowing the cleared gap between the brows does not bring them visibly closer.** A library
    brow is sparse at its nose end (a hundred hairs a side in the first half centimetre), so
    letting those back in changes the start by a millimetre; the dense body starts further out.
  - Prove the edit path first: with the factor at 1 the output must equal the current strands
    file exactly. Print the band height before and after at one station (5-95% of point heights
    3-4 cm from the midline).
  - Before re-importing over the groom, read `hair_width_override` and `hair_width` from the
    existing asset and pass the same width: the import helper's default is not what a library
    copy was made with, and a silent width change reads as a density change.
  - Repaint the colour map from the new strands in the same trial and change groom and map in
    one call, so they share one re-bind wait. Three packages are then dirty (character, map,
    groom): save all three on approval, and read back wardrobe selections after the reload.
  - `trimesh` closest-point queries need `rtree` in the environment (`--with trimesh --with rtree`).

## Head hair recipe (short tousled cut)

- **Hairline** as a table of (degrees round the head from the front, height above the pupils),
  read off a buzz-cut reference, with the ear as its own limit (distance to ear vertices) and the
  density thinning over the last ~7 mm.
- **Locks**: 400-500 guides grown from a crown whorl outward, each with its own heading (tousle),
  length by region (top, fringe, sides, back, nape) and its own target height off the skin.
  Steer every step towards that height plus gravity: without it hair leaves along the normal and
  never lies down, and with one shared height the mass is a hollow shell.
- **Near the whorl, comb the locks across it.** Straight outward flow bares the scalp at the
  crown.
- **Wave** as an S in the scalp plane growing from the root, little of it off the scalp; a helix
  with strong tip curls reads as tight ringlets.
- **Strands**: structure decides the look. A purchased groom that reads well showed the pattern
  in its group info alone: ~160 strands per authored guide, plus a separate group of very short
  hairs for the hairline. So: ~360 locks for a whole scalp, strands parallel to their lock from a
  root patch that covers the scalp, drawing in late to a pointed tip (root offset x (1 - c t^1.8),
  c 0.82-0.97), ~12% running between the two nearest locks to hide gaps, very little frizz, 2%
  following no lock. Drawing in early (t^0.6) renders as ropes; weak drawing-in (c under 0.6) with
  half the strands between locks renders as fine frizz with no locks. The cost of the pointed
  locks is regularity: they can read as tiles, so vary lock length and heading.
- **Develop and judge strands in Blender, not in the engine.** A Cycles render of the same strands
  on the exported head (hair curves + Principled Hair BSDF, 48 samples, 800 px) takes ~4 s a view
  and gives the same verdict as the engine capture; an engine look costs a 5-8 minute re-bind.
  Import only what already looks right in Blender. Put the painted colour map on the head when
  judging brows, so paint and hair are seen together.
  - Blender 5.3 geometry-node modifier inputs are `mod.properties.inputs[identifier]['value']`
    (also `'type'`, `'attribute_name'`); `mod[identifier] = v` raises "id properties not supported".
  - One-UV-per-vertex head exports have triangles spanning the UV seam; anything in Blender that
    looks hair up by UV needs a fresh non-overlapping map (Smart UV Project).
- **Formula-placed guides do not make a hairstyle.** Random headings per lock give evenly sized
  leaf-shaped locks laid like roof tiles, whatever the strand settings. Design the flow and let
  Blender's hair nodes make the strands (this replaced the hand-rolled strand recipe above and
  read as natural hair on its first screens):
  - **Guides**: ~90, roots by farthest-point sampling of the scalp vertices, each grown along one
    smooth flow field (away from the crown whorl, plus a fringe sweep and a forward lean at the
    temples), with its own length, height off the skull, turn (about +-35 degrees) and tip flick.
    Stand it up at the root, hold it at its own height, pull it back in above that height (a
    rounded mass, not spikes), let fringe tips drop to the forehead.
  - **Set region weights at the root, not at the current point.** A fringe lock leaves the scalp;
    weights read off the forehead under it are zero, and it hangs straight as a bowl edge. The
    front hairline is not "top of the head" either: give the fringe its own weight.
  - **Stack**: Interpolate Hair Curves (2 guides) -> three lock levels (3.5 cm, 1.8 cm, 0.5 cm) ->
    Hair Curves Noise (2 mm, scale 20) -> Frizz (0.3 mm) -> keep-off-skin -> Set Hair Curve Profile.
  - **Read the cut off the reference at full size before tuning anything**, one view at a time,
    and write it down per region: lock shape (arc, wave or curl), where tips end against the ear
    and brow, what stands off the head and what lies close, what the ears and forehead show.
    Judging from downscaled contact sheets produced "a mop": right silhouette, no haircut.
  - **Short layered cuts are arcs with flicked tips, not waves.** Keep the per-lock bend's
    wavelength well above the hair length (11 mm at 13 cm, 7 mm at 10 cm on 6-7 cm hair) so each
    lock is one C; S-waves all over read as a perm or a mop. Give most tips an outward flick
    (lift 0.1-0.5 over the last 30%): the visible pointed tips are the layers.
  - **Lengths make the structure**: top ~7 cm, fringe ~8.5, above the ears ~3-4, back ~6, nape
    ~3-4.5 and shorter towards its sides, with almost no gravity term; long hair with gravity
    hangs to the jaw and hides the cut.
  - **Side hair tucks in at its tips** (stand-off falling to a quarter over the outer half, no
    flick) and is shorter and closer in front of the ear, or it hides the ears from the front.
  - **Fringe as commas**: weaken the base flow by the sweep, keep the root lifted longer, rotate
    the heading about the normal by up to ~110 degrees x s^2 towards down, add gravity only at
    the tip, and let the tip's stand-off drop. A straight sweep gives hanging blades.
  - **Nape**: add a pull towards the centre line low on the back so it draws in to a point.
  - **"Match the style, not the strands" means: outline, fringe line, and wavy lock masses.**
    Read the reference per view as a few large lock masses beside the render at double size in
    the same frame. What carried a wavy reference's style here:
    - **Cut the fringe to a line read off the reference's front outline** (a table of height
      against position across the forehead, applied to each guide point by where it is), not to
      one level: a level cut is a curtain.
    - **Wave whole lock masses** (the 3-4 cm group level: about 9 mm every 6 cm, each group its
      own phase), not single strands and not every fine lock. Its clumping can stay off where
      it irons guide waves; the group wave still applies.
    - **Make a lock's wave swing along the head's surface**: across the strand and across the
      line from the head centre (`cross(tangent, position - centre)`), not in a random plane.
      Random planes at that size put tufts and wings outside the silhouette, which is what
      reads as bed head; along the surface the same waves read as styled.
  - Generated reference views can disagree on overall width as well as on details (front and
    back by over 1 cm here). Follow the view the user judges first and record the other.
  - **Also compare the whole head, reference over render, two views a sheet.** Hair-only
    crops hide the nape, the hair below the ears and the overall silhouette (a cap stepping in
    over a narrower nape, dome shoulders too flat).
  - **Read the direction ticks per view before guessing at a view's weak number.** A whole
    region running the wrong way (side hair hanging down where the reference runs back over
    the ear) shows as one red block; fixing it moved more than any strand setting. Re-test an
    idea that was only ever tried while a sign or term was wrong.
  - **Flared tips are locks that end at their widest point, not locks that are too wide.**
    Measure the guides' tips against the reference half-width first; if they are inside it,
    turn the tips in instead of pulling the lock in.
  - **Pull-in and push-out limits must use the same stand-off.** A point-wise reduction applied
    to only one of them is cancelled by the other.
  - **Lock-mass wave phase**: every mass on its own phase reads as braided ladders where
    strands run across the view (front, top); nearly in step (a smooth function of position
    plus about a third of a cycle of jitter) reads as curved locks. In step down the back the
    crests line up in level ripples, so keep the back mostly random. Calm lock waves near the
    whorl, where strands diverge.
  - Patch scripts that assert on a matched string: match code, never a comment you only wrote
    in an earlier patch script. A failed assert writes nothing, and the build that follows is
    the old state: read the first line of the output before judging the render.
  - **Check the comparison tool before chasing its numbers.** Confirm scale with a landmark the
    hair cannot move (pupils in the front frame; ear to ear between front and back). A hair
    mask traces solid hair only: it runs above thin lock ends, so read a fringe line off the
    image itself, never off the mask outline. Know where the frame crops (the nape).
  - **A haircut is cut lines.** Where the reference shows ears, cut side hair at the ear top and
    the sideburn at mid-ear (a test on each guide point's position, with about 1 cm of stagger)
    and let stand-off shrink with height towards the ears. Matching width by pushing lower hair
    out to meet an overhanging cap is the wrong direction: check the reference's width at two
    heights, not only its widest.
  - **Strands end short of their guides** (random trim; about 1.5 cm here). If an edge will not
    come down, measure guide tips against the cut line before moving the line: the hair may
    simply be too short to reach it.
  - **When a lock's path is wrong and two guesses failed, print one guide's integration** (per
    step: position, flow direction, lift, limits) from the build script, then remove the print.
    Terms stack: a flow that already points down, plus a turn-down, plus weight, gave a vertical
    drop that no single one of them explained.
  - **Post-process rotations change meaning with length.** An end hook over the last 45% of a
    short lock is a curl; on a longer diagonal lock it is a vertical drop. Keep end details to
    the last fifth.
  - **Measure an edge as numbers on both sides before moving it.** Per 1 cm column across the
    view, print the lowest strand points (a low percentile of the evaluated curves) and read
    the reference's edge at the same columns. Reading a reference edge by eye once ("reaches
    the brow") overshot by 1-2 cm; the table showed it in one run.
  - **Anything applied after a cut can undo the cut.** An end hook or tip turn applied to a
    guide already cut to a line hangs below it; shorten the turned end so the tip keeps its
    cut height, then re-space the points evenly (uneven steps trip minimum-segment checks).
  - **A cut-line table is live everywhere it is defined.** An entry at hairline height meant to
    say "no hair here" chops every lock that crosses that column into a stub. Keep the line
    under the locks that cross.
  - **Locks outside the silhouette come from the lock levels' random shift**, not only from
    guides. Remove the shift's outward component (subtract `n * max(dot(shift, n), 0)` with
    `n` the direction from the head centre): locks still separate along and into the head,
    and tufts and wings outside the outline go. Check guide tips against the reference width
    first; if they are inside it, the modifiers are the cause.
  - **Width seen from the front belongs to hair in front of the ear line.** Front and back views
    of a reference can then both be met: keep the front width there and reduce stand-off
    behind the head's middle.
  - More stand-off at the root is carried down the whole lock: raising the top that way
    enlarges the whole head. After each pass compare all four direction numbers with the
    last kept state and back out a change that costs one view without a visible gain.
  - **"Looks like bed head, not a hairstyle" is a guide-flow fault, not a strand or clump one.**
    When the outline already matches, these change the read very little: less per-lock
    randomness, looser clumping, blending strands between guides, neater strand ends. Test
    them on overrides without a rebuild, then spend the effort on where the locks go: lift
    at the hairline, sweep, volume on top, how the ends finish.
  - **A limit that brings hair back in must follow the point, not the root.** Stand-off set at
    the root lets top-rooted locks keep the top's height all the way down the side: a wing.
    Shrink the limit by the region the point is in. Check which term pulls in and which only
    pushes out before editing; a fix on the push-out term does nothing.
  - **Validate a new image metric before trusting it.** It must respond to the change it is
    meant to guide and not to lighting or to skin inside the mask. One that separates
    reference from render but ignores every hair setting is measuring the render, not the
    hair: delete it.
  - **Strands read as separate when hairs are gathered into fine bundles, not when they are
    loosened.** At preview resolution a hair is sub-pixel, so parallel hairs in a lock render
    as one glossy sheet. A firm clump level at about 5 mm (factor 0.8) with a little tip
    spread gives visible strand bundles and keeps the locks. Looser locks give brush tips,
    more per-strand noise gives fur, thinner or rougher strands give fuzz, and shifting or
    waving each bundle gives spikes or crinkle.
  - **Try clump and shader values on one zoom before a rebuild.** A scratch script that edits
    the constant inside the built node group and renders one close-up takes a quarter of a
    full build; change the builder only for the setting that wins.
  - **A fringe cannot both reach far forward in profile and run diagonally from the front.**
    Stand-off in its far half moves its travel towards the camera, and from the front it then
    hangs vertically. Generated reference views can ask for both; pick the view the user
    judges first and record the other as a known gap.
  - **A strong swirl round the whorl lays the upper back level across the hair below as a
    ledge.** Keep the tangential term near the radial one (about 1:1), not double it.
  - Parse a builder edit before writing it to disk; a comment spliced into the middle of a
    line fails only when Blender runs it.
  - **Shape a fringe edge by where the lock is, not by how far along it is.** Sweep and fall
    weighted by distance along the strand give a diagonal edge whatever the lengths. For an
    arch-shaped opening, let the lock go across while it is over the opening and fall once
    past its edge (a smoothstep on the point's position), and cap how low a fringe guide may
    go (cut and re-space the points); strands end a few centimetres short of their guide.
  - **Check the whorl's side and sense against the reference's back view.** The direction
    ticks show it at once: a whorl turning the wrong way puts the whole mid-back 60 degrees
    or more off while each lock still looks plausible.
  - **A dark knot is usually a guide seen end-on or a clump level across diverging guides.**
    Switch stages off first; if it survives interpolate-only, list guides by chord/arc (a
    folded guide scores low) and fix the flow at that root.
  - Write down the axis sign next to every directional constant. A `FORWARD` multiplier that
    was really "towards +y" got its sign flipped and sent side hair the wrong way for rounds.
  - **A clump level wider than the guide spacing irons guide waves flat.** Over a wavy front it
    turns wavy guides into straight blades; without it, short layered hair on the back and
    sides is rows of single pointed tufts (scales). Fade the clump factor by region (a clamped
    ramp on each strand's mean position, multiplied into Clump's Factor) instead of choosing
    one or the other for the whole head.
  - **Waves a reference shows as flowing S-curves belong in the guides, shared by neighbours**
    (phase within about a third of a cycle, 5-7 cm long, under 1 cm deep). Giving every fine
    lock its own short wave reads as a perm all over, and as a crinkled top with a frayed
    fringe when limited to the front.
  - **A tall roll beside a part is root lift, not wave.** Hair on the long side that stands
    straight up before sweeping over reads as a quiff from the front: lean it over from the
    root near the part and reduce its stand-off there.
  - For one view that stays wrong, put reference and render side by side at double size in the
    same frame, hair only; whole-head rows hide lock character.
  - **Measure the direction the hair lies in, as well as the outline.** A structure tensor on
    each reference view and on the render (grey image, gradients, tensor smoothed with a
    Gaussian, angle = half atan2 plus 90 degrees) gives an orientation per pixel; draw both as
    ticks and print the median angle between them per view (random is 45). It showed in one
    run what many rounds by eye had missed: the reference's hair lay round the head (top
    straight across, side back along the head, upper back spreading sideways) where the build
    hung down it.
    - Smooth the tensor over more than a quarter of the lock wavelength (1.5 cm for a 5-7 cm
      wave). At 0.65 cm the wave swings the reading 45 degrees either way and every number sits
      at random.
    - It is an orientation: it cannot tell root from tip. Decide the sense from where the roots
      must be and from flicked tips on the outline, and test a guess on the other views: a rule
      that fixes one view and worsens two is the wrong sense or the wrong region.
    - Self-check it on stripes drawn at a known angle.
    - The number says the hair lies the right way, not that it looks right: matching direction
      made the hair read combed and smooth where the reference was tousled. Keep looking.
  - A wave added in each step's (normal, flow) frame jumps where that frame jumps (hair crossing
    an ear). Smooth the offsets along the guide before adding them, and make the
    degenerate-segment assert name the guide, the step and its root so the cause can be read.
  - **Make the guide wave a loose spiral, not a sideways sine.** A sine along `normal x flow`
    is invisible wherever that direction points at the camera (the top in profile, the sides
    from the front): that hair renders straight and slick. Add 0.6 of the amplitude along the
    normal a quarter turn later (zero mean, or the whole head grows), and give hair from 4.5 cm
    the full amplitude.
  - **A region weight that reaches further than its name is a silent length bug.** A `fringe`
    weight built from "front" covered the whole front of the top, so the short side of a part
    got fringe length and ran to the ear as a slick band. Print root, tip minus root and arc
    length for the guides in a region that looks wrong before changing its rules.
  - **Mess is a dial; ask where the user wants it before matching a tousled reference.** Tidy
    and structured: neighbouring guides wave nearly in step (phase from position plus a small
    random part), one wave per lock (9 mm at 5.5 cm), headings within about 12 degrees either
    way, 5% loose hairs, noise 1 mm. Tousled: random phase, 22 degrees, 15% loose hairs.
  - **Do not stack `Curl Hair Curves` on guides that already wave.** It crinkles every lock and
    makes a ladder along a part. Find such a culprit by switching the stack off one stage at a
    time on a zoom, before changing any guide rule.
  - Generated reference views can disagree with each other. When the overlay matches in one
    view and not in another at the same edge, compare the reference's own views there before
    sculpting; follow one view and say which.
  - **If the reference shows separate strands and the render shows fur, the strands are
    sub-pixel.** At 1 px = 0.4 mm, strands of real width (0.1 mm) average into a matte mass
    whatever the clumping. For the preview draw them about 0.2 mm wide and glossier (roughness
    0.3): the highlight along each strand is what draws it. Say so beside the sheet, and carry
    the real width to the engine. Cutting surface reflection (Huang model, Reflection 0.3)
    removes white frosting and the strand definition with it.
  - **Put the tousle in the guides, not the lock levels.** A lock-level wave longer than the
    hair is a random heading per lock: it turned the fringe into a blade pointing sideways.
    Double the guides (about 2 cm apart, one ribbon each), give each its own wave (7-10 mm at a
    4 cm wavelength, random phase), and add the wave after the guide smoothing, which otherwise
    halves it. Keep the phase in step in the fringe and beside the part, or the part reads as a
    braid.
  - **A swept fringe that still reaches the far brow**: from the part to the middle of the
    forehead it stays up, short, and goes across; only towards the far temple does it get its
    length and weight and end on the skin. All of it falling is a curtain in profile.
  - **Read positions off the aligned overlay, not off side-by-side crops.** The crops sit at
    different heights; a fringe that looked 3 cm too low beside the reference was level with it
    in the overlay, and three passes went to a difference that was not there.
  - When a change does not move the thing it was aimed at, undo it before trying the next one.
  - **Sculpt the shape against a traced outline, not by eye.** Mask the reference's hair by
    colour per view, shift it onto the render by face landmarks (pupils, nose tip, ear), and
    draw both outlines on the render, with top / left / right / area per view printed after
    every build. It shows in centimetres where the mass is too big or small; side-by-side
    judging had stalled on "closer" for several rounds. The landmark shift is the weak point:
    state its uncertainty and do not chase differences smaller than it.
  - Once the outline matches, the remaining difference is lock character inside it; the outline
    tool says nothing about that, so keep the same-scale side-by-side for it.
  - **One guide row at a part, on the short side only.** A row on each side made a ladder of
    identical locks arcing over the part, which reads as a braid from the front.
  - Giving every lock in the fringe its own heading (about 40 degrees either way) broke it into
    spiky blades and bared the forehead; keep the fringe coherent and vary the top instead.
  - **Render hair previews without the denoiser** (about 190 samples at 1024 px). At 48 samples
    denoised, strands smear into painted blobs and every tuning judgement about lock definition
    is made on the smear. Expect to retune clumping once it is off: what looked soft was fur.
  - **Lock definition after that**: lock level 0.8 with 3 mm tip spread, sub-locks 0.3, frizz
    0.6 mm, curl factor 0.2-0.3. Looser (0.6 / 0.6) read as fur; curl around the 3.5 cm chunks read
    as a perm; curl `Random Offset` 1.0 read as wool.
  - **A fringe that covers the forehead is a mass standing off it, not long strands.** Give
    fringe roots a mostly forward flow with a lean (a quarter of the top's sweep), about 10 cm of
    length, stand-off 1.3x the usual falling to 40% at the tips, and tip gravity. Long strands
    sent sideways first bare the middle of the forehead and bunch at the temple; too much
    stand-off (1.9x) pushes the mass forward instead of letting it come down.
  - Compare each view at the same scale beside its reference, two views to an image; a
    four-across contact sheet hides whether the forehead is covered.
  - **Light the preview the way the reference is lit.** A reference sheet is lit from the viewer
    in every view: parent the lights to the camera. A fixed key made bright blades and dark
    hollows in the side and back views that read as hair faults and were not.
  - **Flat blade locks become loose waves with `Curl Hair Curves` at half strength**: radius
    15 mm, frequency 1.5, factor 0.5, curl start 0.3, own guide map at the lock distance, placed
    after the lock level. At factor 1 every radius tried (3-20 mm) gave ringlets. Curl resamples
    the strands, so nothing downstream may assume the guide's point count.
  - **Let one strand in ten join no lock**: multiply the Clump `Factor` by a per-curve random
    test (Index evaluated on the curve domain -> Random Value -> less-than), same seed at every
    level. It fills between locks and gives the silhouette its loose hairs.
  - **Crown: a coherent swirl, not random headings.** Random headings cover the whorl's centre but
    open a parting wherever two neighbours diverge. Strengthen and widen the tangential term
    instead (2.0 x exp(-distance / 0.45)) and keep the per-guide turn small there.
  - **Scalp under hair: hair-dark and no specular** (map the growth mask to specular level 0),
    or light from the viewer shows white through every gap. Check a pale patch three ways
    before fixing it: hair hidden (is it scalp?), colour-by-intercept (roots or tips?), and the
    guide printout.
  - **When a tuft keeps rendering grey, measure the guides before changing rules.** Print each
    guide's tip and mid direction dotted with the camera direction and its root position; the
    end-on ones name the rule at fault. Two rule changes aimed at the wrong region did nothing;
    the printout showed hair above the ear running level and forward (a temple-lean term), and
    turning that flow down fixed it.
  - **A part that runs to the crown reads as a quiff in profile.** Let it rule the fringe and the
    front of the top only; behind it the hair goes outward from the crown.
  - **Sweep the fringe across; do not rotate it far towards 'down' about the surface normal.** On
    top of the head that rotation points forward: 100 degrees gave a visor in profile, 45-60 with
    extra tip gravity gave a fringe that crosses and then drops.
  - **Trim strands to uneven lengths** (`Trim Hair Curves`, `Replace Length` off, `Random Offset`
    ~2 cm) straight after Interpolate. With one interpolation guide every strand of a lock has the
    same length and the lock ends in a blunt brush.
  - Softer, fuller hair came from looser clumping (0.6 at 3.5 cm, 0.75 at 1.8 cm, tip spread
    3 mm), not from more stand-off.
  - **A part is a cut in the growth surface, not a flip in the flow.** Flipping the sweep across a
    line is not enough: strands near it follow guides from both sides and average into short
    crumpled tufts. Grow the hair from a scalp-only mesh cut along the part (duplicate the
    vertices on one side), turn on Interpolate's `Part by Mesh Islands`, and feed each Clump a
    `Create Guide Index Map` whose `Group ID` is the same side test, so locks never span it. End
    the cut before the crown and make the cut-off piece one front quarter; a cut right over the
    head opens a seam down the back. Add a row of guides close to each side of the part.
  - **The long side of the part comes forward and across, then down**: add a forward component
    that grows over the forehead, rotate the heading towards down by ~100 degrees x s^1.5, and
    make that side 1.5-3 cm longer. **The short side goes straight down the temple**: damp the
    base flow there. Left to a forward flow it heads for the camera in the front views; combed
    back it is a slick roll in profile.
  - **Hair seen end-on, and sparse lock tips, render pale grey** in Cycles (only the white
    surface reflection is left). Treat a grey band as a direction problem first. Lowering the
    hair BSDF `IOR` to 1.33 removes most of the frosting in a preview.
  - **To shade end-on hair dark in a preview, test |Geometry > Tangent . Incoming|** (about 0.85
    to 0.98) and mix to a dark diffuse. `Hair Info > Tangent Normal` is a normal facing the
    viewer, not the tangent: a test built on it never finds end-on strands and dims all the hair
    instead. Prove any such mask by setting its range to an extreme (0 to 0.01) and looking at
    what goes dark.
  - **Find what a pale patch is by measuring, and draw the measuring box on the render first.**
    Project the evaluated strand points into the view, take the frontmost layer inside the
    patch, and print where along the strand they are and |tangent . view|. A box read off a
    downscaled image sat 3 cm from the patch and blamed the wrong guides; world light,
    roughness, IOR and clump shape were all changed for nothing before the measurement.
  - **To find what a band or tuft is made of, colour by position along the strand** (Curves Info
    `Intercept` -> ramp -> emission) and render the same zoom; and switch modifiers off one at a
    time (`show_render`) to find which stage makes it. Both are seconds per try and beat
    reasoning about it.
  - Smooth each guide after stepping it (5 passes of 1/4-1/2-1/4, ends fixed): step rules meet
    at corners that show as a fold across a whole lock.
  - `Interpolation Guides` 1 gives choppier, more separate locks than 2; strands are then exact
    translated copies of the nearest guide. `Follow Surface Normal` put 8% of points inside the
    head with script-made guides, which carry no `surface_uv_coordinate`; whether attaching the
    guides fixes it is untested.
  - Clamp the length formula (a sum of region terms went negative at the sideburn and tripped the
    guide check).
  - **A lock level is Clump plus a per-lock move and bend, or the hair reads as one fuzzy cap.**
    Noise is smooth in space, so neighbouring locks move together and never separate. Wrap the
    Clump group in your own node group and use its `Guide Index` output as the ID of Random Value
    nodes: offset = random vector x shift x factor^1.5, plus normalize(tangent x random vector) x
    bend x sin(2 pi (length / wavelength + random phase)) x factor^0.7.
  - **Size from the reference in pupil distances** (hair height above the pupils, hair width),
    then set the stand-off per region. Width lives at the temples; hair below mid-skull hugs.
  - **The fringe needs a soft side part**: one sweep direction for roots on one side of a line, the
    opposite beyond it. Per-lock random sweep opens an inverted V on the forehead.
  - **Crown whorl**: every direction leads away from it, so scalp shows. A spiral is not enough;
    give locks rooted there any heading (turn range up to +-180 degrees) so they fall across it.
  - **Shade the scalp hair-dark under the hair** (mix the skin colour towards the hair colour by
    the growth mask); pink skin between locks reads as thinning. The engine character needs the
    same in its face colour map.
  - Define the hairline where the hair is built, as a soft 0..1 vertex mask used as density. A
    wrap-time "ear region" was far larger than the ear and left a bare block above it; the real
    limit is the top of the pinna (vertices that stick out past the skull side).
  - Vary guide lengths widely (0.7-1.25x); even lengths put tips in a row that reads as a shelf.
  - **Interpolation Guides 2, not 4.** Four average each guide's turn and height into a smooth
    cap; two keep them as chunks, which is the tousle.
  - **Clump: set `Existing Guide Map` off.** Interpolate leaves one guide index on every strand,
    and Clump then draws the whole head into a single lock (hair on one patch, hanging straight).
  - **Noise and Frizz: set `Cumulative Offset` off.** On (the default), the offset adds up along
    the strand and the tips fly out as spikes.
  - Noise after the clumps waves whole locks; before them it mostly vanishes.
  - The surface mesh needs a `rest_position` point attribute or Interpolate warns and misplaces.
  - No stock node keeps hair out of the head, and strong clumping pulls 2-3% of points inside.
    Build a small node group: Geometry Proximity and Sample Nearest Surface (normal) on the head,
    height = dot(point - nearest, normal), offset = normal x max(margin - height, 0), scaled in
    over the first sixth of the strand so roots stay. It took 3.2% inside to 0.0%.
  - Self-check every build: guide step lengths are hair-sized, roots span the scalp, under 0.5%
    of sampled points inside the head. On failure print the farthest point after each modifier.
  - Where bare skin shows beside the hair, zoom a render before changing lengths: a hairline set
    by a generous ear region sat 1.6 cm above the ear; longer side hair falling over it covered it.
- **With a 3D model of the wanted hair, trace guides from it instead of styling by formula.** Even
  a generated mesh of fused tubes agrees with itself from every angle, which pictures do not, and
  it can be measured in 3D.
  - **Fit the model to the character by the face, from the character's side.** Take a fixed set of
    the character's face points, match each to the nearest point on the model's head, solve scale,
    turn and move, trim to the best 80%, and try several starting scales. Fitting the model's
    points onto the character lets the scale run away: a small patch of a too-large face fits a
    cheek well.
  - **Read the direction from the normals.** Round a tube the surface normals fan out and none
    points along it, so the hair's direction is the smallest eigenvector of the summed
    normal-times-normal over a few millimetres. Average directions as tensors, since they have no
    sense. How far to smooth decides how much of the model is copied (see "Decide how much of the
    model to copy" below).
  - **Keep a reach table**: per direction from the skull's middle, how far out the hair goes and
    whether there is any. Close single empty bins, or thin lock ends act as cut lines.
  - **Trace from roots on the character's own growth area**: lift off the skin over the first
    centimetre, then follow the field. Carry the sense in the heading, not in the step taken (the
    lift is at right angles to the hair and flips it). Where skin or reach holds a guide back,
    remove that part of the heading so it slides. Stop a guide that returns to where it was.
  - **Do not push guides out to a set depth.** The field carries hair outwards where the model's
    hair goes outwards; a forced depth made guides ride on top, three times further off the
    model's direction, and miss the fringe.
  - **Only for a lock-by-lock copy: switch off formula waves in the clump levels and gather each
    guide's strands into its own lock** (clumping grouped by the strand's guide; check the
    guide-index attribute holds distinct values first, and write one from the nearest guide root
    if not). Traced guides then carry the model's waves, and a clump wave doubles the direction
    error. Do this only when the user wants the model's locks themselves; a general-flow trace
    keeps the hand-styled lock levels as they are.
  - Measure the direction error after each modifier in turn to find which stage undoes the guides.
  - **Cap length with a designed length.** A lock's end inside the hair cannot be read from a
    direction field. Compare path length over straight-line distance with the model's: past the
    right cap the extra length is wandering.
  - **Decide how much of the model to copy before tracing; the default is its general flow and
    outline, not its locks.** Smoothed over 2 mm the guides copy each of the model's locks, and a
    generated model's locks are thick ropes: with each guide's strands gathered into its own lock
    the result reads as matted patches. Smoothed over about 8 mm they take the general flow and
    outline, and the strand look comes from the clump levels: only fine 5 mm bundles on that flow
    read combed and sleek; the hand-styled chunk, lock and sub-lock levels on it read tousled.
    - Tell guides from clump settings on overrides before rebuilding: halve the per-guide lock's
      strength on the built file. If the patches barely change, the tracing is the cause.
    - Show the candidates as labelled rows on one sheet (as sent, flow only, flow plus lock
      levels) and let the user pick the direction before fixing details in any of them.
  - **A direction field has no tip end; break ties with a rule, not by accident.** Where a guide
    meets the flow side-on the sign is arbitrary, and hair then runs against its neighbours (a
    patch out of line, a hollow where a part should be, strands pressed flat across the forehead).
    Add a constant bias to the sign choice: downhill, or the sweep direction for the swept side.
    End a guide where the skin beneath it starts to rise: a smoothed field has no lock ends, so
    its lines U-turn where two flows meet.
  - **Print the share of guide points with a neighbouring guide within 1 cm running the opposite
    way.** It finds against-the-grain patches before a render does.
  - **Expect calmer hair and a shorter fringe after fixing the sense.** Part of a traced build's
    tousle and reach was wrong-way hair; re-measure the fringe edge and report what got worse.
  - **When the user marks a spot on a render, find the hair there before changing a rule.** Draw a
    pixel grid on that render, map the marked pixel back through its camera to head coordinates,
    and list the guides passing within about 1 cm (root, tip, direction at the spot) beside the
    model's direction there. Strands can lie wrong where no guide does: count the faulty strands
    after each modifier, then print the paths of the guides nearest their roots.
  - **Editing a library groom instead of building one**: the engine has no groom exporter, so read the strands in C++ from `UGroomAsset::GetHairDescription()` (editor only; module `HairStrandsCore`, plugin `HairStrands` enabled in the project). Three things to check before using them:
- The description holds the authored guide curves as well as the hairs. Compare its strand count with `hair_groups_info` (`num_curves` + `num_guides`) and drop the guides before re-importing as strands, or they render as extra hairs.
- Read which head the strands sit on from the library binding's `source_skeletal_mesh`. Library heads differ (two in one install were 12 cm apart in height); binding to the wrong one misplaces the groom.
- `FHairDescription` cannot remove strands. Moving points (write positions back, `CommitHairDescription`, `CacheDerivedDatas`) on a duplicate keeps groups, guides, widths and settings; removing hairs means re-importing the kept ones.

To move a hairline, turn the points round the ear-to-ear line through the skull middle and keep each point's height above the skin (ray-cast the binding head); fade the turn to nothing at the sideburns and behind the crown.

**Known limit**: guides converge on the strongest flow, so locks that peel off and hang free
    (fringe ends, wisps) get none.
  - **Render the model through the hair file's own camera** for comparisons; no alignment by eye.
- **Generated pictures and generated models exaggerate hair** (rope-thick locks, fringes that
  could not hang that way). Treat one as a hint of style and outline, never as the target for
  strand character. When the user calls the result unrealistic, or before spending many passes on
  lock character, offer a pick sheet of real photographs of the style and build towards the picks
  (search recipe: the `research` skill's `references/photo-references.md`, "People and
  hairstyles").
- **Hairline hairs**: a few thousand, 0.4-1.4 cm, across the last 5 mm, lying the way the nearest
  lock starts. They need the file's own widths (`hair_width_override = False`) at under half the
  main width: 7,000 at full width rendered as a band of stubble on the forehead.
- Learn from a third-party groom by looking at renders and at the settings the Editor shows. The
  Fab licence forbids deriving data from content, so do not extract its strand curves.
- Give neighbouring locks a shared wave phase (a function of root position) so they bend
  together; amplitude above ~0.5 cm on pointed locks reads as ringlets.
- **Fringe**: vary lock length there and sweep it sideways, or it renders as a bowl's edge.
- Push every point out to a small clearance above the skin so nothing runs under it.
- Scale: library hair is ~105k strands at width 0.011; 90k at that width covered the scalp.

## Colour on an own groom

- The same `Melanin`/`Redness` reads darker on a denser groom: values matched on a library style
  came out ~10% darker on a 90k-strand groom.
- Judge colour in the key-lit views (profile, three-quarter), not only a front patch sample: a
  step lighter that matched the front sample read strawberry blond where the key hit.
- Change one parameter per round; every change costs a full re-bind.
