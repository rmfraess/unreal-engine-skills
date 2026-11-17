---
name: ue-metahuman-creator
description: >-
  MetaHuman Creator character authoring and assembly in UE 5.8 (in-editor since 5.6). Use for C++/Python UMetaHumanCharacter creation/editing via UMetaHumanCharacterEditorSubsystem; face/body sculpting and skin/eyes/makeup/teeth settings; mesh, DNA or Identity conforming; wardrobe grooms/clothing and palette instances; cloud auto-rigging, texture sources, Blueprint build/quality/LODs or preview actors; legacy Quixel Bridge migration; and unrigged-character, missing-texture, optional-content or cloud-login failures.
metadata:
  engine-version: "5.8"
  category: metahuman
---

# MetaHuman Creator (in-editor)

Since UE 5.6 MetaHuman Creator runs inside the editor as the **MetaHuman Creator** plugin
(`Engine/Plugins/MetaHuman/MetaHumanCharacter`, plugin name `MetaHumanCharacter`, beta).
A character is a `UMetaHumanCharacter` asset holding parametric face/body state plus look
settings; every edit goes through `UMetaHumanCharacterEditorSubsystem`; the result is
*assembled* by a pipeline into a `BP_<Name>` actor Blueprint with face and body skeletal
meshes, grooms and clothing. Two steps still call Epic's cloud service: face auto-rigging
and high-resolution texture download.

## When to use this skill

- Creating a `UMetaHumanCharacter` from code, sculpting body/face, setting skin, eyes,
  makeup, eyelashes and teeth, then building the playable Blueprint without the UI.
- Conforming a scanned or sculpted head/body mesh, a `.dna` file, or a MetaHuman Identity
  into a MetaHuman (mesh import / "Conform" tools).
- Dressing a character: adding `UMetaHumanWardrobeItem` grooms and outfits to slots and
  tweaking instance parameters (hair melanin, shirt colour).
- Understanding build output, pipeline types and quality levels, LODs, and what the face
  rig state means for MetaHuman Animator and Live Link.
- Migrating legacy Quixel Bridge MetaHumans, or diagnosing failures caused by missing
  "MetaHuman Creator Core Data" or a missing Epic account login.

## Mental model

| Concept | Type | Role |
|---|---|---|
| Character asset | `UMetaHumanCharacter` | Pure data: face/body state (bulk data), optional face/body DNA, `SkinSettings`, `EyesSettings`, `MakeupSettings`, `HeadModelSettings`, synthesized texture bulk data, an *internal* `UMetaHumanCollection`. |
| Edit session | `UMetaHumanCharacterEditorSubsystem` | Owns runtime identity models (`FMetaHumanCharacterIdentity::FState`, `FMetaHumanCharacterBodyIdentity::FState`), the live preview meshes and materials. All edits are its UFUNCTIONs. |
| Palette / collection | `UMetaHumanCollection : UMetaHumanCharacterPalette` | Items (`FMetaHumanCharacterPaletteItem`, keyed by `FMetaHumanPaletteItemKey`) per slot (`Hair`, `Eyebrows`, `Outfits`, ...) plus a `Pipeline` and a `DefaultInstance`. |
| Instance | `UMetaHumanInstance` | A selection per slot (`FMetaHumanPipelineSlotSelection`) + instance-parameter overrides; `Assemble()` produces the assembly output struct. |
| Wardrobe item | `UMetaHumanWardrobeItem` | A principal asset (groom binding, outfit, skeletal mesh) + its `UMetaHumanItemPipeline`. |
| Pipeline | `UMetaHumanCollectionPipeline` / `UMetaHumanCollectionEditorPipeline` | Runtime side assembles an instance; editor side builds assets and writes the actor Blueprint. Defaults: `UMetaHumanDefaultPipeline` (current), `...Legacy`, `...UEFN`. |

Three rules drive almost every gotcha:

1. **Nothing edits without a session.** Call `TryAddObjectToEdit(Character)` first; most
   subsystem functions require it and `BuildMetaHuman` fails without it. Call
   `RemoveObjectToEdit` when done.
2. **Apply vs Commit.** `Apply*` (native, const) only updates the preview; `Commit*` writes
   into the asset (and marks it dirty, transactable). Scripts use `Commit*`.
3. **Rig and textures gate the build.** `CanBuildMetaHuman` requires: added for edit, no
   pending cloud request, `EMetaHumanCharacterRigState::Rigged` (face DNA present), and
   `HasHighResolutionTextures()` (texture sources downloaded).

## Plan a character before authoring

Settle these with the user before creating the asset; get facts (plugin tools, LFS rules,
engine enums) yourself and put only the decisions to them.

- **One asset, many builds.** Game vs cinematic is not two models: the character asset is
  authored once and assembled any number of times (`NameOverride` / `AbsoluteBuildPath` keep
  builds apart). Pick the pipeline at build time; table in
  [references/palette-pipeline-assembly.md](references/palette-pipeline-assembly.md#choosing-a-build-target).
- **Two choices live on the character, not the build:** face rig type (`JointsAndBlendShapes`
  when close-ups matter: the LOD0 blendshapes carry expression and correctives) and texture
  source resolution (re-downloadable). Ask about them up front.
- **Story-point variants** (older, more muscular): duplicate the character and change only the
  body, so the face stays identical; each copy needs its own rig and build. Never pick a fixed
  `set_body_type` for a character that will get variants — it locks the body sliders.
- **Body method:** overall sliders first (masc/fem, fat, muscle, height), then named
  measurements (`Across Shoulder`, `Chest`, `Waist`, `Hip`, `Neck`, `Knee`, `Thigh`, `Calf`, ...
  `Height` in cm) fitted *numerically* to front + side references scaled by the stated height —
  never approved by eye. Present an outline overlay and a per-level % table, and name the
  regions the reference hides (shorts, hair, arms in A-pose). Procedure and pitfalls:
  [references/body-fitting-to-reference.md](references/body-fitting-to-reference.md). Conform to a mesh when a real scan/sculpt exists, **or when the user has looked at a generated
  3D head and approved it as the character**. Their by-eye approval makes that head the shape
  target, whatever a landmark score against the flat references says (that metric cannot see
  form). So when the user brings or mentions a generated head, ask for that verdict first, before
  listing the mesh's defects: a conform can only lose detail, so the raw head must already read as
  the character. An approved head supplies proportions and the body's height supplies absolute
  size; a mesh that is not life-size needs a resize, which is never an objection to the route.
  Without that approval, do not propose an image-to-3D head (Meshy) for face shape: unreviewed
  generations drifted to a generic, older face and a gap measured only against one pointed the
  wrong way; use one as a skull/ear cross-check and sculpt against a hairless (buzz-cut) edit of
  the reference set (image-prompt-engineer, "Hairless sculpt set"). Planning notes under
  "User-approved generated head as the conform target" and the scoring recipe under "Generated 3D
  reference head", both in the face-fitting reference.
- **Face fit:** front-view MediaPipe landmark fitting with a long-lens piloted camera, then depth
  from the profiles; procedure, projection math and its ceiling in
  [references/face-fitting-to-reference.md](references/face-fitting-to-reference.md), along with
  the face-shape levers table (use it to answer "how much control do we have?"), the
  coefficient-mix recipe for swapping the base after a fit, and hand sculpt passes for jaw,
  cheeks, eyes and ears (ears need `bAllowEars`). When the user says a feature is "off",
  do not sculpt that feature yet: run a full deficiency review (pupil-aligned side-by-side sheets
  per view under reference-matched light, IPD-normalised eye and mouth/chin crops, the profile pair) and present a numbered table: area,
  reference vs ours **with a measured number**, proposed fix, how likely the lever lands it. Every
  row needs a measurement (IPD-normalised landmark distance, or nasion-aligned profile depth in cm)
  before it goes to the user: impressions from comparison sheets get the direction wrong (a mouth
  that "looks wider" measured narrower; a nose that "projects further" matched within 0.1 cm once
  profiles were aligned at the nasion). Re-measure an approved item before sculpting it, and drop
  or resize it when the number disagrees, telling the user. Recipes in
  [references/face-fitting-to-reference.md](references/face-fitting-to-reference.md#measuring-a-deficiency).
  Sculpt only the items the user approves, broad shapes first. A flagged feature often reads wrong because of a neighbour (an
  over-projecting nose makes the chin look weak in profile), and the user's "weak" may mean a
  shape detail (a chin cleft, squareness) rather than projection. Show the user the %
  error trend and a side-by-side with the reference each round. The user wants parity in
  front, three-quarter *and* profile before any texture work. Matched feature numbers are not a
  matched feature either: a nose within 0.1 cm on length, projection and width still looked "very
  different" (round tip, flared wings, nostril show); after two brush tries on such a form, move to
  a preset feature transplant (face-fitting reference). A converged front number is not
  parity, so run the multi-view fit, measure the references' own consistency floor, and show
  pupil-aligned side-by-side sheets per view. Never show a warped 50/50 photo-over-render blend as
  evidence: the similarity warp absorbs feature errors and the high-contrast photo dominates the
  blend, so it reads as parity while the user plainly sees chin, nose, jaw and eyes off. Never call
  matched landmarks "parity" either; say "positions match, form does not". Surface form between sculpt points (jaw line into the neck,
  cheek hollows) is beyond landmark passes: first rule out lighting and skin texture with
  throwaway renders, then edit the whole surface on a test copy via the head template round-trip
  (export preview face mesh -> edit -> skin-only static mesh -> `import_from_template`).
  Copy the character `.uasset` (hash-check the copy) before every template import: restoring the
  pre-import face coefficients leaves the head ~0.1 cm mean / ~0.9 cm max off, so the file copy is
  the only undo. Restore it with the character's edit session ended (or the Editor closed), or the
  in-memory copy is saved back over it. If the Editor turns out to have been closed mid-trial,
  hash the character file against the committed one before relaunching: a close with Save writes
  the unapproved trial to disk. Copy both versions aside, tell the user, and leave it uncommitted
  until they give a verdict. Judge
  every pass by eye in before/after sheets, not only by the landmark number, which saturates at
  the reference floor while the face still looks unchanged. Template imports keep face-surface
    brushes almost whole (0.17-0.6 cm moves at 1.1-2.4 cm radius landed 94-98%; a 0.2 cm chin cleft
    landed 100%; a continuous brow-ridge band landed 99%; a smooth forehead displacement field driven
    by the profile gap landed 95%) but strip the face/neck border: a throat
    bump (Adam's apple) landed ~15% and under-jaw / jaw-angle brushes 23-46% across passes. Plan
    throat, under-jaw and jaw-angle anatomy as a post-build mesh edit; after one failed try there,
    stop and tell the user.
    Count each method's attempts per feature and stop at two, offering a different method rather
    than a third strength. Passes that measure correctly can still look unchanged: say so with the
    sheet. Neck width is the body `Neck` constraint, not the face, and measure it (neck width over
    cheekbone width, front view) before proposing a change: a neck that read "too thick" by eye
    measured 17% narrower than the reference's. Hair does not
    gate face *sculpting* (no "freeze the face" step), but it gates the likeness verdict: with hair
    and brows unlike the reference's the user cannot see the similarities, so once they accept the
    bald shape "for now", move on to hair and brows instead of proposing more shape passes. When no
    library style fits, custom hair and brows are a user decision between an own generated groom
    (free; [references/custom-grooms.md](references/custom-grooms.md)), a hand-groomed or paid
    one, and a stand-in; take the generated route when the user rules out spending. **Put the
    whole library in front of the user before calling it exhausted.** A few styles rejected from
    captures is not a verdict on the rest: the user judges a stock style in seconds, and a custom
    groom costs a build and a review per pass. List the styles on disk (`find
    <engine>/Plugins/MetaHuman/MetaHumanCharacter/Content/Optional/Grooms/Bindings/Hair -name
    'WI_*.uasset'`: 38 hair styles in 5.9, with `Eyebrows`, `Beards`, `Mustaches`, `Eyelashes` and
    `Peachfuzz` folders beside it), say which were already tried, and offer the user the browse
    themselves: open the character asset, **Hair & Clothing**, then **Wardrobe**, then the Hair
    slot (labels read from the 5.9 editor source; say so if you have not seen the screen). Tell
    them to close without saving so the trial does not replace the saved selection, that a newly
    chosen groom can take minutes to appear on a conformed head, and to judge the cut, not the
    default colour. Hand the Editor over while they browse and ask for the style names they like.
- **Canon beats generated reference** on traits the source states (eye colour, hair colour,
  height); the reference images govern only what canon leaves open (face, cut). Point out the
  conflict rather than matching the image.
- **Proportion questions get measurements.** When the user asks whether something is the right
  size (head for the body, neck, shoulders), measure it against each reference separately and
  against human norms, say where the references disagree with each other or with a stated
  height, then give a recommendation. Recipe: "Is the head the right size?" in the body-fitting
  reference.
- **Review hand-off:** same-camera sheet beside the target or reference, a measured table, what
  still differs by eye, every setting chosen by eye named as such, then numbered decisions for
  the user. A close-up crop of one feature goes out together with a whole-face sheet beside the haired
  reference (front and three-quarter, hair and brows on) **in every trial report, every round**:
  the user judges a cleft, cheek or nose root in the context of the face and asks for the full
  face each time they get only the crop, which costs a round per change. A verdict given on that
  full-face sheet ("keep this") covers every unsaved trial visible in it: save them all, then list
  what was saved and how to revert each, and say plainly that the keep was read as covering all
  of them so the user can object. "Looks better" is progress, not a keep. When the user asks how
  to see the model better in the Editor, give the viewport steps first (view-mode menu,
  Exposure, untick Game Settings, lower EV100 to the captures' value) and offer a multi-light
  lighting map second; a front-only booth map leaves the sides of the nose in shadow. The two-pass
  limit is on your own retries; a further pass the user asks for is theirs to spend. Before sending, zoom every capture at the head/body join (neck, collarbones, back of
  the shoulders): the user spots a seam you skimmed past. A defect that is gone on the next
  capture is unexplained, not fixed: repeat the edit that preceded the bad capture to reproduce
  it (a body commit leaves the preview head offset; body-fitting reference). Skin, eyes and build are judged against the character's life (a farm worker is tanned
  and defined), so ask or infer that before the first look-dev pass.
- **Captures must show what the Editor shows.** A whole head from a long-lens distance puts the
  face on only ~550 px of a viewport-sized capture, and a comparison sheet shrinks it again, so
  freckles, pores and small blemishes vanish and the skin reads smooth and shiny. Render at 2x the
  viewport size or more (same camera, same perspective) before judging skin, freckles, shine or
  tone, and never report a skin difference from a small capture. When the user sees something in
  the Editor that your pictures lack, the pictures are wrong: test the cause (shoot close, force
  the LOD, `r.TextureStreaming 0`, compare a fine-detail number) before naming one; a guessed
  "engine drops detail with distance" had to be retracted a turn later.
- **Profile gaps without landmarks.** Once the nose root has been filled or hair covers the
  forehead, nasion-anchored profile alignment has nothing to hold. Trace the picture's front edge
  (figure mask, first figure pixel per row, face span from under the fringe to where the chin
  turns back), then fit our midline side-view line to it by size, turn and shift with a trimmed
  closest-point fit (drop the worst sixth so one real gap does not drag the rest; seed the scale
  from several sizes with the nose tips together; self-test on a turned, resized copy of our own
  line). Report the gap per height in mm, run every profile picture available and state how far
  they disagree with each other (2-4 mm at brow and tip is normal); move towards their average,
  not one picture. Even the gap over a few mm of height before turning it into a move: a
  correction that is narrow in height raises a ridge.
- **Local fills beside a feature** (hollow next to a nose wing): a tight, strong fill makes a
  round lump in the clay preview; spread it wider and lower before raising the amount, and expect
  part of a dark band to be colour in the skin map, not depth.
- **A nose that reads "pinched" near the tip** is the groove between the ball of the tip and each
  wing, just above the nostril, not the overall width (landmark widths stay within noise). Find it
  in horizontal cross-sections (forward position by distance from the midline, every 2 mm of
  height): the depth under a straight line from tip side to wing is the pinch. Rounding the tip
  deepens it, so check after any tip swell. Fill it with one push direction for the whole patch
  (~1.5 mm over ~0.8 cm radius to start) and print the normal at the patch centre first: a centre
  on the facet above the nostril rim faces downward and pushes the wrong way, so move the centre
  2 mm up until the normal points out and forward. Go past ~2.5 mm only after viewing the nostrils
  from below.
- **A speck, bump or "pimple" the user points at: locate it before blaming the sculpt.** Ray-cast
  the pixel from the capture camera onto the exported face mesh to get its position and UV; check
  how far each nearby vertex sits off its neighbours in every saved head version (a smooth result
  clears the shape edits); then look at that UV in the colour map and in the preview material's
  `Normal` and `Cavity` textures (`MID_MI_Skin_Head_*` on the face component). Those are
  transient: `export_texture2d` writes an empty file, so draw the texture to a render target with
  a canvas and `export_render_target`. An outlier well above the face's 99.9th percentile at that
  UV, absent on the mirrored side, is a blemish in the synthesized skin sample
  (`FaceTextureIndex`, skin U/V). Offer the user the choice between healing those pixels through
  texture overrides and picking another skin texture (which changes pores and freckles
  everywhere and needs any painted map redone).
- **Healing a blemish through overrides.** Copy only the fine detail of a clean patch 2-3 radii
  away (patch minus its ~9 px median) onto the spot's own median, faded over the outer third of
  the radius: a plain clone, even level-matched at the rim, shows as a patch because shading
  differs a few mm away. Use the same patch offset for colour, `Normal` and `Cavity` so bump,
  pores and colour stay in step. Import the healed maps (`normal` kind for Normal, `mask` for
  Cavity) and add them to `texture_material_overrides.texture_overrides.face` under
  `FaceTextureType.NORMAL` / `CAVITY`, starting from the existing dict: assigning a one-entry dict
  drops the other overrides. Prove the round-trip left the rest alone (fine-detail rms and mean
  colour away from the spot, before against after, same camera). Tell the user the override pins
  those maps at the exported preview size (1024), whatever the build would otherwise use.
- **Freckles are a live material layer, not part of the synthesised colour map.** Changing
  `skin_settings.freckles` and `commit_skin_settings` updates the face at once even with a
  colour-map override on (`FrecklesDensity` etc. on the skin material); the exported synthesised
  map is byte-identical before and after, so no re-export or repaint is needed. Faint freckles
  in the map itself belong to the skin sample.
- **Groom colour is read and set on the preview collection.** `character.internal_collection
  .default_instance.get_instance_parameters(item_path=...)` returns an empty list; use
  `subsystem.get_preview_collection(character).default_instance` with
  `MetaHumanPaletteItemPath(item_key=<slot selection's selected_item>)`, `set_float` on `Melanin`
  / `Redness`, then `assemble_for_preview` and the groom wait. That shows the colour but does
  **not** store it: a save keeps the character's old values. Before saving, read
  `character.internal_collection.default_instance.get_instance_parameter_overrides(path)` and, if
  it still holds the old numbers, write them on the character (a project service such as
  `set_wardrobe_item_parameters`, or the same `set_float` on the character's own instance once
  its parameters are listed), then re-read the overrides. Read the hair's values first when
  brows should match it, and change a painted brow underlay to the same hue in the same pass or
  the dark paint shows through. Before recolouring, sample the reference's brow and hair colour
  and tell the user when the request moves away from it (reference brows are often darker than
  the hair); a lighter brow colour also reads thinner.
- **A verdict on a close-up covers that item only.** When other trials share the unsaved
  character, save what can be saved alone (textures, grooms), leave the character unsaved, and
  say that the kept item is locked in on the character only once the open trials are decided.
- **Judge neck and shoulders out of the A-pose.** The A-pose lifts the shoulder muscles towards
  the jaw, so the neck reads short and the build bulky. Hold the preview in a standing idle frame
  before proposing any neck or muscle change: on the preview body component
  `set_update_animation_in_editor(True)` and `override_animation_data(anim, True, True, 0.5, 1.0)`
  (`play_animation` alone did not move it), then `face.set_leader_pose_component(body, True)` or
  the head stays behind (4 cm gap at `neck_01`). Idle clips ship under
  `/MetaHumanCharacter/Optional/Animation/TemplateAnimations/Technical_Loops/Idle/`. Preview only;
  switching the animation off again does not restore the A-pose, so destroy the preview actor and
  reassemble. Captures taken posed do not line up with A-pose ones.
- **Proportions against survey men, when the user distrusts the body pictures.** Fit each
  ANSUR II male measure (`https://tools.openlab.psu.edu/publicData/ANSUR_II_MALE_Public.csv`;
  lengths in mm, weight in 0.1 kg, pupil distance in 0.1 mm) on stature and weight, predict at the
  character's height and weight, and report ours in residual spreads (under 1 is noise; few very
  tall men in the sample). Mesh volume (body plus head skin, signed tetrahedra) times 1.03-1.07
  checks the stated weight. The survey has no chin height: build it from `sittingheight -
  eyeheightsitting` plus `mentonsellionlength`. Take the top of the breastbone from the mesh (the
  midline point where the neck's front is furthest back), not from the `clavicle_l` joint, which
  sat 5 cm lower and reversed the finding. When the user says "head too short" or "neck too
  long", check skull breadth against head height and whether the hairline was lowered before
  touching neck length.
- **Likeness:** for adaptations, confirm the face is an original design, not a real person,
  screen actor or published cover art, before sculpting.
- **Starting preset:** pick it from bald front captures of scratch copies under the `Studio`
  lighting map, not thumbnails; recipe in [references/python-scripting.md](references/python-scripting.md#comparing-presets-or-look-dev-states-with-front-captures).
  Rank presets on what fitting cannot change: **3D form** (cheek fullness, cheekbone and jaw
  definition, soft tissue under the jaw; judge in three-quarter and profile captures, not front
  only), age and skin detail texture, ears. Front-view landmark fitting only moves feature
  positions, so a heavy preset stays heavy after a converged fit.
  Delete the scratch copies (with the user's OK) once the real asset exists.
- **Skin and eyes before body/face approval:** offer them early — a preset's tan and colouring
  make a correct body read wrong. Present 2–3 tone options as face close-ups beside the
  reference. State limits up front: skin tone is **one tone for the whole body** (regional sun
  only via face `Accents`; tanned forearms or a paler torso need a custom body texture), and a
  "gray" iris needs `GlobalSaturation` near 0.1 — a cool hue alone still renders blue. A light
  gray iris still reads blue beside tanned skin and red hair even when its pixels are neutral:
  sample the iris ring's RGB before retuning and tell the user whether the blue is in the pixels
  or in the contrast. Values:
  [references/character-asset-and-settings.md](references/character-asset-and-settings.md#look-dev-recipes).
  Keep fitting and scouting previews bald: strip and re-verify grooms in the same call as every
  spawn (earlier groom clears do not survive a save/reload, and landmark moves refuse with grooms
  on). The strip writes the wardrobe selection on the character itself, so a later save persists
  the bald state: record the stripped slots (with full asset paths) when stripping, reselect them
  before any save of that character, and check `get_summary(...)['wardrobe_selections']` after
  every save. `select_wardrobe_item` needs the full object path; summaries list only short item
  names, so map them through `get_wardrobe(...)['items']`. When hair/brows are judged, use a test copy or an unsaved trial on the
  real character (discard recipe in that section), `assemble_for_preview`, and wait 4-7 min per
  groom change (check a hair pixel) before capturing; see "Groom preview timing" in
  [references/face-fitting-to-reference.md](references/face-fitting-to-reference.md).
- **Repository:** before the first save, check `.gitattributes` covers the character and
  build folders with LFS; a Cine build is 1–2 GB and would bloat plain Git permanently. Keep
  review-only comparison builds uncommitted.

## Core workflow

1. **Create** the asset with `UMetaHumanCharacterFactoryNew` through Asset Tools
   (`IAssetTools::CreateAsset` / `AssetTools.create_asset`). The factory initializes a
   valid default face/body state; never `NewObject<UMetaHumanCharacter>` directly.
2. **Open for edit**: `TryAddObjectToEdit` (returns false if already registered, for
   example open in an asset editor; then edit via that session instead).
3. **Body**: `GetBodyConstraints` → set `bIsActive` / `TargetMeasurement` on the
   `FMetaHumanCharacterBodyConstraint`s you care about (`Height` in cm; others are
   measurements between `MinMeasurement`..`MaxMeasurement`) → `SetBodyConstraints` →
   `CommitBodyState`. Or conform: `ConformBodyToTarget`, `ImportBodyWholeRig`,
   `ImportFromBodyTemplate`.
4. **Face**: sculpt via `GetFaceLandmarks` / `TranslateFaceLandmarks` or
   `GetFaceModelCoefficients` / `SetFaceModelCoefficients`, or conform via
   `ImportFromTemplate`, `ImportFromFaceDna`, `ImportFromIdentity`,
   `FitStateToTargetVertices`; finish with `CommitFaceState`.
5. **Look**: fill `FMetaHumanCharacterSkinSettings`, `FMetaHumanCharacterEyesSettings`,
   `FMetaHumanCharacterMakeupSettings`, `FMetaHumanCharacterHeadModelSettings` and call the
   matching `CommitSkinSettings` / `CommitEyesSettings` / `CommitMakeupSettings` /
   `CommitHeadModelSettings`.
6. **Wardrobe**: `Character->GetMutableInternalCollection()->TryAddItemFromWardrobeItem(Slot, Item, OutKey)`,
   then `GetMutableDefaultInstance()->TryAddSlotSelection(FMetaHumanPipelineSlotSelection(Slot, Key))`;
   `RunCharacterEditorPipelineForPreview` (Python `assemble_for_preview`) exposes instance
   parameters.
7. **Cloud**: `RequestAutoRigging` (`FMetaHumanCharacterAutoRiggingRequestParams`, pick
   `EMetaHumanRigType::JointsOnly` or `JointsAndBlendShapes`) then `RequestTextureSources`
   (`FMetaHumanCharacterTextureRequestParams`). Set `bBlocking = true` in scripts.
8. **Build**: `CanBuildMetaHuman` → `BuildMetaHuman(Character, FMetaHumanCharacterEditorBuildParameters)`.
   Output lands in `AbsoluteBuildPath/<Name>/BP_<Name>` with shared assets in
   `CommonFolderPath` (defaults `/Game/MetaHumans`, `/Game/MetaHumans/Common`).
9. **Save** the character asset, `RemoveObjectToEdit`. For a level preview while editing,
   `SpawnMetaHumanActor`; for gameplay, place the built `BP_<Name>`.

## Subsystem API map (BlueprintCallable, so also Python)

| Area | Functions |
|---|---|
| Session | `TryAddObjectToEdit`, `IsObjectAddedForEditing`, `RemoveObjectToEdit`, `GetPreviewCollection`, `OnEditPreviewCollection`, `RunCharacterEditorPipelineForPreview` (ScriptName `AssembleForPreview`) |
| Body | `GetBodyConstraints(Character, bScaleMeasurementRangesWithHeight=false)`, `SetBodyConstraints`, `CommitBodyState`, `ConformBodyToTarget`, `SetBodyMesh`, `SetBodyJoints`, `ImportBodyWholeRig`, `GetMeshForBodyConformingFromTemplate/FromDNA`, `GetJointsForBodyConformingFromTemplate/FromDNA` |
| Face | `GetFaceLandmarks`, `TranslateFaceLandmarks`, `GetFaceModelCoefficients`, `SetFaceModelCoefficients`, `CommitFaceState`, `FitStateToTargetVertices`, `ImportFromTemplate`, `ImportFromFaceDna`, `ImportFromIdentity`, `FitFaceStateFromBodyWithEyesTeethDNA/Template`, `ConformToTargetMeshes`, `AlignToTargetMeshes`, `CommitPosedStateAsAPose` |
| Look | `CommitSkinSettings`, `CommitEyesSettings`, `CommitMakeupSettings`, `CommitHeadModelSettings` |
| Cloud | `RequestAutoRigging`, `RemoveFaceRig`, `RequestTextureSources` |
| Build | `CanBuildMetaHuman(Character, bInLogError)`, `BuildMetaHuman`, `SpawnMetaHumanActor(Character, bKeepTransient)` |
| Testing | `CompareFaceState`, `CompareBodyState`, `CompareFaceTextures` |

Native-only (C++): `GetRiggingState`, `IsFixedBodyType`, `SetMetaHumanBodyType`,
`IsTextureSynthesisEnabled`, `GetFaceState`/`GetBodyState`, `ApplyFaceDNA`, `CommitFaceDNA`,
`CommitBodyDNA`, `ResetParametricBody`. Full signatures and line numbers:
[references/editor-subsystem-api.md](references/editor-subsystem-api.md).

## C++ pattern (editor module)

Module deps: `MetaHumanCharacter`, `MetaHumanCharacterEditor`, `MetaHumanCharacterPalette`,
`MetaHumanDefaultPipeline`, `MetaHumanCoreTechLib`, `MetaHumanSDKRuntime` (for
`EMetaHumanQualityLevel`), plus `AssetTools`, `UnrealEd`. Editor-only (`Type: Editor`).

```cpp
#include "MetaHumanCharacter.h"
#include "MetaHumanCharacterEditorSubsystem.h"
#include "MetaHumanCharacterFactoryNew.h"
#include "Subsystem/MetaHumanCharacterBuild.h"     // FMetaHumanCharacterEditorBuildParameters
#include "MetaHumanCharacterBodyIdentity.h"        // FMetaHumanCharacterBodyConstraint
#include "IAssetTools.h"

static void BuildPilot()
{
    UMetaHumanCharacter* Character = Cast<UMetaHumanCharacter>(IAssetTools::Get().CreateAsset(
        TEXT("MH_Pilot"), TEXT("/Game/Characters/MetaHumans"),
        UMetaHumanCharacter::StaticClass(), NewObject<UMetaHumanCharacterFactoryNew>()));
    if (!Character) { return; }

    UMetaHumanCharacterEditorSubsystem* MH = UMetaHumanCharacterEditorSubsystem::Get();
    if (!MH->TryAddObjectToEdit(Character)) { return; }   // not registered: do not Remove

    // Body: parametric constraints (names match the UI, e.g. "Height", "Muscularity")
    TArray<FMetaHumanCharacterBodyConstraint> Constraints = MH->GetBodyConstraints(Character);
    for (FMetaHumanCharacterBodyConstraint& C : Constraints)
    {
        if (C.Name == TEXT("Height")) { C.bIsActive = true; C.TargetMeasurement = 185.f; }
    }
    MH->SetBodyConstraints(Character, Constraints);
    MH->CommitBodyState(Character);

    // Skin: U = lightness (0 light .. 1 dark), V = redness; copy, edit, commit
    FMetaHumanCharacterSkinSettings Skin = Character->SkinSettings;
    Skin.Skin.U = 0.35f;
    Skin.Skin.V = 0.60f;
    Skin.Freckles.Mask = EMetaHumanCharacterFrecklesMask::Type1;
    MH->CommitSkinSettings(Character, Skin);

    // Cloud: blocking so a script can continue when the service answers
    FMetaHumanCharacterAutoRiggingRequestParams Rig;
    Rig.RigType = EMetaHumanRigType::JointsOnly;
    Rig.bBlocking = true;
    Rig.bReportProgress = false;
    MH->RequestAutoRigging(Character, Rig);

    FMetaHumanCharacterTextureRequestParams Tex;
    Tex.bBlocking = true;
    Tex.bReportProgress = false;
    MH->RequestTextureSources(Character, Tex);

    if (MH->CanBuildMetaHuman(Character, /*bInLogError*/ true))
    {
        FMetaHumanCharacterEditorBuildParameters Build;
        Build.PipelineType = EMetaHumanDefaultPipelineType::Optimized;   // Cinematic | Optimized | UEFN
        Build.PipelineQuality = EMetaHumanQualityLevel::High;            // Low..Cinematic; Optimized/UEFN only
        Build.AbsoluteBuildPath = TEXT("/Game/MetaHumans");
        Build.CommonFolderPath = TEXT("/Game/MetaHumans/Common");
        MH->BuildMetaHuman(Character, Build);                            // writes BP_MH_Pilot
    }
    MH->RemoveObjectToEdit(Character);
}
```

`Character->SkinSettings` / `EyesSettings` / `MakeupSettings` / `HeadModelSettings` are the
committed values; read them, mutate a copy, commit. Do not write the UPROPERTYs directly
(the preview meshes and materials would not update; `PostEditChangeProperty` only covers a
subset).

## Python worked example (Epic's exposed surface only)

Every call below is a `BlueprintCallable` UFUNCTION or a `BlueprintReadWrite` /
`BlueprintType` struct verified in the 5.8 headers; parameter names follow the Python
convention (`InCharacter` → `character`, `bInLogError` → `log_error`).

```python
import unreal

PKG, NAME = "/Game/Characters/MetaHumans", "MH_Pilot"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
character = asset_tools.create_asset(
    asset_name=NAME, package_path=PKG,
    asset_class=unreal.MetaHumanCharacter,
    factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
if character is None:
    raise RuntimeError("MetaHumanCharacter creation failed")

mh = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
if not mh.try_add_object_to_edit(character):
    raise RuntimeError("Could not open for edit (already open in an asset editor?)")

try:
    # ---- body: parametric constraints -------------------------------------------
    constraints = mh.get_body_constraints(character)            # TArray<FMetaHumanCharacterBodyConstraint>
    by_name = {str(c.name): c for c in constraints}             # "Height", "Fat", "Muscularity", "Masculine/Feminine", ...
    by_name["Height"].is_active = True
    by_name["Height"].target_measurement = 185.0                # cm
    musc = by_name["Muscularity"]
    musc.is_active = True
    musc.target_measurement = unreal.MathLibrary.lerp(musc.min_measurement, musc.max_measurement, 0.7)
    mh.set_body_constraints(character, list(by_name.values()))
    mh.commit_body_state(character)

    # ---- skin ----------------------------------------------------------------------
    skin = character.skin_settings                              # struct copy of the committed value
    skin.skin.u = 0.35                                          # lightness 0..1 (0 = light)
    skin.skin.v = 0.60                                          # redness 0..1
    skin.freckles.mask = unreal.MetaHumanCharacterFrecklesMask.TYPE1
    skin.freckles.density = 0.3
    mh.commit_skin_settings(character, skin)

    # ---- eyes ----------------------------------------------------------------------
    iris = unreal.MetaHumanCharacterEyeIrisProperties()
    iris.pattern = unreal.MetaHumanCharacterEyesIrisPattern.IRIS003   # ScriptName "Pattern"
    iris.primary_color_u, iris.primary_color_v = 0.2, 0.8             # cool .. warm, dark .. light
    eyes = character.eyes_settings
    eyes.eye_left.iris = iris
    eyes.eye_right.iris = iris
    mh.commit_eyes_settings(character, eyes)

    # ---- eyelashes / teeth (head model) ----------------------------------------------
    head = character.head_model_settings
    head.eyelashes.type = unreal.MetaHumanCharacterEyelashesType.LONG_CURL
    head.teeth.tooth_length = 0.2
    mh.commit_head_model_settings(character, head)

    # ---- face sculpt: scale all landmarks 5% ---------------------------------------
    landmarks = mh.get_face_landmarks(character)
    deltas = [unreal.MathLibrary.subtract_vector_vector(v.multiply_float(1.05), v) for v in landmarks]
    mh.translate_face_landmarks(character, list(range(len(deltas))), deltas)
    mh.commit_face_state(character)

    # ---- cloud: auto-rig, then texture sources (both need an Epic login) ------------
    rig = unreal.MetaHumanCharacterAutoRiggingRequestParams()
    rig.rig_type = unreal.MetaHumanRigType.JOINTS_ONLY           # or JOINTS_AND_BLEND_SHAPES
    rig.blocking = True                                          # required in scripts
    rig.report_progress = False
    mh.request_auto_rigging(character, rig)

    tex = unreal.MetaHumanCharacterTextureRequestParams()
    tex.blocking = True
    tex.report_progress = False
    mh.request_texture_sources(character, tex)

    # ---- build the Blueprint ------------------------------------------------------------
    if not mh.can_build_meta_human(character, log_error=True):
        raise RuntimeError("Not buildable: rig or texture request did not complete")

    build = unreal.MetaHumanCharacterEditorBuildParameters()
    build.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
    build.pipeline_quality = unreal.MetaHumanQualityLevel.HIGH
    build.absolute_build_path = "/Game/MetaHumans"
    build.common_folder_path = "/Game/MetaHumans/Common"
    build.enable_wardrobe_item_validation = True
    mh.build_meta_human(character=character, params=build)      # -> /Game/MetaHumans/MH_Pilot/BP_MH_Pilot

    unreal.EditorAssetLibrary.save_loaded_asset(character)

    # ---- optional: live preview actor in the open level -------------------------------
    actor = mh.spawn_meta_human_actor(character=character, keep_transient=True)
    unreal.log(f"preview actor {actor.get_name()} mirrors edits until the session ends")
finally:
    if mh.is_object_added_for_editing(character):
        mh.remove_object_to_edit(character)
```

Grooms/clothing, conforming, export and the `MetaHumanGenerator` toolset wrapper are in
[references/python-scripting.md](references/python-scripting.md).

## Cloud dependencies and offline behaviour

- `RequestAutoRigging` and `RequestTextureSources` create `UE::MetaHuman::FAutoRigServiceRequest`
  / `FFaceTextureSynthesisServiceRequest` / `FBodyTextureSynthesisServiceRequest`
  (`MetaHumanSDKEditor`, `Cloud/`). They need an Epic Games account login (EOS auth;
  `ServiceAuthentication::CheckHasLoggedInUserAsync`, `LoginToAuthEnvironment`) and an
  accepted EULA. Failure codes: `EMetaHumanServiceRequestResult` (`Unauthorized`,
  `EulaNotAccepted`, `LoginFailed`, `Busy`, `Timeout`, `GatewayError`, ...).
- Offline or logged out: the request fails with a notification ("Auto-Rigging of Face failed
  with code ..."; textures: "User not logged in, please autorig before downloading source
  face textures"), the rig state stays `Unrigged`/`RigPending`, and `CanBuildMetaHuman`
  returns false ("Character is not rigged" / "The Character is missing textures").
- A failed request logs only a result code. To read the service's reason, set the console variable
  `http.UrlPatternsToInspect <part of the service host>` before the request: the JSON error body
  then appears in the log as `LogHttp: Warning`. Clear it afterwards.
- 'Invalid Arguments' (HTTP 400) on a conformed face usually means stacked vertices: the service
  refuses any triangle with two vertices at one place, in its own triangulation, so separate every
  coincident pair, not only those your triangle list shows as flat. `ImportFromTemplate` with UV
  matching creates such stacks when the template is copied from the render mesh, whose UVs are
  rounded (lip corners, tear ducts). Copy the template from `GeometryScriptLODType.SOURCE_MODEL`:
  same triangles in the same order, exact UVs.
- Auto-rigging rebuilds the face mesh with a different render-vertex order (same positions): exports
  indexed by render vertex taken before the rig no longer line up with the mesh after it.
- `synthesized_face_textures` stream in: drawn to a render target straight away they export as a
  blurred low mip. Set `r.TextureStreaming 0`, wait, export, restore. The animated maps (CM1-3,
  WM1-3) are near-white and mid-grey modifiers on top of the base maps, not full maps.
- The Optimized pipeline at High bakes the head colour to 2K (normal and roughness stay 4K) and
  builds a joints-only face mesh with no morph targets, whatever rig type was requested.
- Everything else (sculpting, skin preview via local texture synthesis, body solve,
  conforming, wardrobe, preview assembly) is local. Local texture synthesis needs the
  optional content below (`IsTextureSynthesisEnabled()`).
- The subsystem keeps one `FMetaHumanCharacterEditorCloudRequests` per character; a second
  request while one is active is rejected (`HasActiveRequest()`).

## Optional content ("MetaHuman Creator Core Data")

`FMetaHumanCharacterEditorModule::IsOptionalMetaHumanContentInstalled()` checks the plugin's
`Content/Optional/` folder for `TextureSynthesis/` (with `*.ar` model files) and
`BodyTextures/`. It is installed from the Epic Games Launcher next to the engine, not with the
plugin. Without it the editor logs "MetaHuman Optional Content folder not found ... limited
features" and disables: local texture synthesis (skin tone preview becomes flat), presets
library and blend tool (`Optional/Presets`), body textures, the built-in wardrobe grooms and
clothing (`Optional/Grooms/...`, `Optional/Clothing/WI_DefaultGarment`), the legacy fixed body
types (`Optional/Body`), migration (`Optional/Migration/MigrationDatabase`) and DCC export
templates (`Optional/DCC`). Silence the warning with `mh.Character.SuppressContentWarnings`.

Plugin content that *does* ship with the engine (`Content/`): `Face/` (`SKM_Face`,
`SKM_Face_DNA`, `Face_Archetype_Skeleton`, `ABP_Face`, `ABP_Face_PostProcess`, `PHYS_Face`,
`Face_LODSettings[_Low|_Medium|_High]`, `IdentityTemplate/` model data, `ARKit/` mapping
assets), `Body/` (`ABP_Body_PostProcess`, `IdentityTemplate/` with `SKM_Body`, `SKM_Body_DNA`,
`body_model.dna`, `PHYS_Body`, `Body_LODSettings*`), `Female/Medium/NormalWeight/Body/metahuman_base_skel`,
`BuildPipeline/` (`BP_DefaultPipeline`, `BP_DefaultLegacyPipeline[_Low|_Medium|_High]`,
`BP_DefaultUEFNPipeline_*`, `BP_MetaHuman*`, `DefaultWardobePipeline/`), `Animation/`
(`ABP_MH_LiveLink`, `ABP_AnimationPreview`, `Retargeting/IK_MH_IKRig`, `RTG_MH_IKRig`),
`Clothing/` (translucent clothing material), `Common/MetaHuman_ControlRig`, `Controls/` (face
board), `LightingEnvironments/` (`Studio`, `Split`, `Fireside`, `Moonlight`, `Tungsten`,
`Portrait`, `RedLantern`, `TextureBooth` maps), `Materials/`, `TextureGraphs/`, `Textures/`,
`Tools/EyePresets/`, `Python/examples/`.

## Gotchas & edge cases

- **Texture synthesis status is lazy.** In UE 5.8.4, `IsTextureSynthesisEnabled()` only tests `FaceTextureSynthesizer.IsValid()`; `TryAddObjectToEdit` initializes it asynchronously. A false VibeMetaHumans `texture_synthesis_enabled` before any character edit session does not prove missing Core Data or a broken installation. Check optional-content status separately and verify synthesis after opening an authorized character before diagnosing failure.
- **Reloading a character from disk.** Call `end_edit` (Python service) / `RemoveObjectToEdit`
  before `EditorLoadingAndSavingUtils.reload_packages` on a `UMetaHumanCharacter`; reloading while
  its edit session and preview actor are live can access-violate the editor's Python and leave it
  unstable for later calls. After such a crash, stop Editor work, verify the saved `.uasset` from
  outside (hash, exported verts), and have the user restart the Editor without saving.
- **"Unable to edit asset"** — `TryAddObjectToEdit` returns false when the character is
  already registered (asset editor open). Either use that session (it is the same subsystem)
  or close the editor. Never call `RemoveObjectToEdit` after a false return.
- **Commit, not raw property writes.** Writing `Character->EyesSettings` directly leaves the
  preview and the identity state out of sync. Use `Commit*`. In Python, properties like
  `skin_settings` are `BlueprintReadOnly`: read, modify the copy, commit.
- **Rig state.** `EMetaHumanCharacterRigState { Unrigged, RigPending, Rigged }`. Any face
  sculpt or conform after rigging invalidates the DNA (back to `Unrigged`); re-run
  `RequestAutoRigging`. `RemoveFaceRig` reverts to the archetype DNA. A rigged face is what
  gives the built `SKM_Face` its RigLogic DNA and the 200+ facial controls that MetaHuman
  Animator, Live Link Face (`ABP_MH_LiveLink`, `Face/ARKit/` mapping) and Control Rig drive.
  `JointsOnly` is lighter; `JointsAndBlendShapes` adds blendshapes (`HasFaceDNABlendshapes()`)
  for the Cinematic look.
- **Textures gate the build** even when materials will be overridden: assembly needs the
  animated maps that arrive with the texture download. Desired resolutions live in
  `SkinSettings.DesiredTextureSourcesResolutions` (`ERequestTextureResolution` 2k/4k/8k);
  `NeedsToDownloadTextureSources()` tells you when a re-download is needed.
- **Fixed body types.** `bFixedBodyType` is set when a whole body rig is imported from DNA
  (`FImportFromDNAParams::bImportWholeRig`, `ImportBodyWholeRig`) or a legacy compatibility
  body (`EMetaHumanBodyType::f_med_nrw`...) is chosen: the body constraints then do nothing
  until `ResetParametricBody`.
- **Pipeline quality only matters for Optimized/UEFN.** `Cinematic` ignores
  `PipelineQuality`. Legacy pipelines come from `UMetaHumanCharacterPaletteProjectSettings::DefaultCharacterLegacyPipelines`
  keyed by `EMetaHumanQualityLevel`; `BP_DefaultPipeline` is the current default.
- **LODs.** Face/body LOD settings come from `Face_LODSettings*` / `Body_LODSettings*`;
  `FMetaHumanLODProperties` in the default editor pipeline overrides them and strips LODs
  (`FMetaHumanCharacterEditorBuild::StripLODsFromMesh`). Preview LOD is `EMetaHumanCharacterLOD`
  (`LOD0..LOD7`, `Auto`). Rendering-quality profiles (Epic/High/Medium) are viewport-only.
- **Preview actor is not your gameplay actor.** `SpawnMetaHumanActor` spawns an
  `AMetaHumanCharacterEditorActor` (Transient, NotPlaceable) that mirrors the live session;
  it is destroyed when the session ends. Ship the built `BP_<Name>` instead.
- **Build path.** Output folder is `AbsoluteBuildPath/<NameOverride or asset name>/`;
  leaving `AbsoluteBuildPath` empty uses the collection's unpack settings
  (`UMetaHumanCollection::UnpackPathMode`). Wardrobe validation can be skipped with
  `bEnableWardrobeItemValidation = false` (also a project setting).
- **Legacy Bridge MetaHumans.** The `MetaHumanCharacterMigrationEditor` module hooks
  `FMetaHumanImport` (Bridge / Fab import) and, when the source has `MigrationInfo.json`,
  offers Import / Migrate / Import and Migrate (`UMetaHumanCharacterEditorSettings::MigrationAction`,
  `MigratedPackagePath`, name prefix/suffix). Migration recreates skin, makeup, eyes and
  grooms through the subsystem using `Optional/Migration/MigrationDatabase`; it cannot run
  without the optional content.
- **UAF (experimental).** `Engine/Plugins/Experimental/MetaHuman/MetaHumanCharacterUAF`
  registers an extra animation system option
  (`AnimationSystemName = "Unreal Animation Framework (UAF) - Experimental"`) and per-quality
  actor Blueprints (`UMetaHumanCharacterUAFProjectSettings::Blueprints`). Default is
  `FMetaHumanCharacterAssemblySettings::AnimationSystemNameAnimBP` (`"AnimBP"`). Keep AnimBP
  unless the project already runs UAF.
- **Virtual textures.** `UMetaHumanCharacterEditorSettings::bUseVirtualTextures` is ignored
  when VT is off or `r.AllowStaticLighting` is on (MetaHuman VT materials fail to compile
  with static lighting).

## Version notes

- 5.6: MetaHuman Creator moved into the editor as this plugin; Quixel Bridge import became a
  migration path.
- 5.7: `AutoRigFace` deprecated in favour of `RequestAutoRigging` + params struct.
- 5.8: `RemoveFaceRig` exposed to Blueprint/Python; `FOnPaletteBuilt` → `FOnCollectionBuilt`;
  `IMetaHumanCharacterActorInterface::SetCharacterInstance` → `SetMetaHumanInstance`;
  `ConformBody`/`GetMeshForBodyConforming`/`GetJointsForBodyConforming` (FVector overloads)
  deprecated for the `*ToTarget` / `*FromTemplate` / `*FromDNA` FVector3f versions;
  `FMetaHumanCharacterSkinSettings::bEnableTextureOverrides`/`TextureOverrides` deprecated for
  `TextureMaterialOverrides`.

---

## References & source material

Engine source (UE 5.8 — all paths under `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/`):
- `MetaHumanCharacter/Public/MetaHumanCharacter.h`:29 — `EMetaHumanCharacterRigState`.
- `MetaHumanCharacter/Public/MetaHumanCharacter.h`:162 — `FMetaHumanCharacterHeadModelSettings`.
- `MetaHumanCharacter/Public/MetaHumanCharacter.h`:206 — `UMetaHumanCharacter`.
- `MetaHumanCharacter/Public/MetaHumanCharacterSkin.h`:340 — `FMetaHumanCharacterSkinSettings`.
- `MetaHumanCharacter/Public/MetaHumanCharacterEyes.h`:241 — `FMetaHumanCharacterEyesSettings`.
- `MetaHumanCharacter/Public/MetaHumanCharacterMakeup.h`:196 — `FMetaHumanCharacterMakeupSettings`.
- `MetaHumanCharacter/Public/MetaHumanCharacterTeeth.h`:28 — `FMetaHumanCharacterTeethProperties`.
- `MetaHumanCharacter/Public/MetaHumanCharacterAssemblySettings.h`:14 — `EMetaHumanDefaultPipelineType`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:131 — `EMetaHumanRigType`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:138 — `FMetaHumanCharacterTextureRequestParams`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:152 — `FMetaHumanCharacterAutoRiggingRequestParams`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:491 — `UMetaHumanCharacterEditorSubsystem`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:529 — `TryAddObjectToEdit`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:777 — `CanBuildMetaHuman`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:788 — `BuildMetaHuman`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1356 — `RequestAutoRigging`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1927 — `GetBodyConstraints`.
- `MetaHumanCharacterEditor/Public/Subsystem/MetaHumanCharacterBuild.h`:25 — `FMetaHumanCharacterEditorBuildParameters`.
- `MetaHumanCharacterEditor/Public/Subsystem/MetaHumanCharacterService.h`:20 — `FMetaHumanCharacterEditorCloudRequests`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorModule.h`:15 — `IsOptionalMetaHumanContentInstalled`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSettings.h`:36 — `UMetaHumanCharacterEditorSettings`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterFactoryNew.h`:10 — `UMetaHumanCharacterFactoryNew`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterExportBlueprintLibrary.h`:184 — `UMetaHumanCharacterExportBlueprintLibrary`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorActor.h`:22 — `AMetaHumanCharacterEditorActor`.
- `MetaHumanCharacterPalette/Public/MetaHumanCollection.h`:70 — `UMetaHumanCollection`.
- `MetaHumanCharacterPalette/Public/MetaHumanInstance.h`:133 — `UMetaHumanInstance`.
- `MetaHumanCharacterPalette/Public/MetaHumanWardrobeItem.h`:14 — `UMetaHumanWardrobeItem`.
- `MetaHumanCharacterPalette/Public/MetaHumanPaletteItemKey.h`:15 — `FMetaHumanPaletteItemKey`.
- `MetaHumanCharacterPalette/Public/MetaHumanCollectionBlueprintLibrary.h`:250 — `UMetaHumanCollectionBlueprintLibrary`.
- `MetaHumanDefaultPipeline/Public/MetaHumanDefaultPipeline.h`:20 — `UMetaHumanDefaultPipeline`.
- `MetaHumanDefaultEditorPipeline/Public/MetaHumanDefaultEditorPipeline.h`:13 — `UMetaHumanDefaultEditorPipeline`.
- `MetaHumanCharacterMigrationEditor/Private/MetaHumanCharacterMigrationEditorModule.h`:17 — `FMetaHumanCharacterMigrationEditorModule`.

Related plugins (UE 5.8, under `Engine/Plugins/`):
- `MetaHuman/MetaHumanCoreTechLib/Source/MetaHumanCoreTechLib/Public/MetaHumanCharacterBodyIdentity.h`:89 — `FMetaHumanCharacterBodyConstraint`.
- `MetaHuman/MetaHumanCoreTechLib/Source/MetaHumanCoreTechLib/Public/MetaHumanCharacterIdentity.h`:41 — `EAlignmentOptions`, `FFitToTargetOptions`.
- `MetaHuman/MetaHumanSDK/Source/MetaHumanSDKRuntime/Public/MetaHumanTypes.h`:53 — `EMetaHumanQualityLevel`.
- `MetaHuman/MetaHumanSDK/Source/MetaHumanSDKRuntime/Public/MetaHumanBodyType.h`:10 — `EMetaHumanBodyType`.
- `MetaHuman/MetaHumanSDK/Source/MetaHumanSDKEditor/Public/Cloud/MetaHumanServiceRequest.h`:20 — `EMetaHumanServiceRequestResult`, `ServiceAuthentication`.
- `MetaHuman/MetaHumanSDK/Source/MetaHumanSDKEditor/Public/Cloud/MetaHumanARServiceRequest.h`:86 — `FAutoRigServiceRequest`.
- `Experimental/MetaHuman/MetaHumanCharacterUAF/Source/MetaHumanCharacterUAFEditor/Private/MetaHumanCharacterUAFProjectSettings.h`:12 — `UMetaHumanCharacterUAFProjectSettings`.

Epic Python examples (UE 5.8): `Engine/Plugins/MetaHuman/MetaHumanCharacter/Content/Python/examples/`
(`example_create_asset.py`, `example_auto_rig.py`, `example_assembly.py`, `example_modify_skin.py`,
`example_sculpt_body.py`, `example_live_edit.py`, `example_add_grooms.py`, `example_add_clothing.py`,
`example_conform_head.py`, `example_conform_body_from_template.py`, `example_download_textures.py`,
`example_export_tools.py`, `example_spawn_metahuman_actor.py`) and
`Engine/Plugins/Experimental/Toolsets/MetaHumanGenerator/Content/Python/metahuman_toolset/metahuman.py`.

Deep-dive references in this skill:
- [references/character-asset-and-settings.md](references/character-asset-and-settings.md) —
  `UMetaHumanCharacter` data model, every settings struct and enum, textures, body types.
- [references/editor-subsystem-api.md](references/editor-subsystem-api.md) — the subsystem
  UFUNCTIONs with signatures, param structs, import error codes, cloud flow, build checks.
- [references/palette-pipeline-assembly.md](references/palette-pipeline-assembly.md) —
  collection/instance/wardrobe model, pipelines, assembly output, Blueprint libraries,
  project settings, build output layout.
- [references/python-scripting.md](references/python-scripting.md) — Python naming rules,
  grooms/clothing, conforming, export, spawn, batch patterns, MetaHumanGenerator toolset.
- [references/body-fitting-to-reference.md](references/body-fitting-to-reference.md) and
  [references/face-fitting-to-reference.md](references/face-fitting-to-reference.md) — measured
  body and face fitting to reference pictures.
- [references/custom-grooms.md](references/custom-grooms.md) — generating own hair and brow
  grooms, mapping them to the groom head, import and wardrobe-item wiring, offline preview.

Related skills: `ue-control-rig-and-ik`, `ue-animation-system`.
