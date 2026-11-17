# Fitting a MetaHuman body to reference images

Measure; don't eyeball. Side-by-side vision judgements of body proportions get the *direction*
wrong (thin legs called "fuller"), and a user who sees a gap expects a measured pass, not another
opinion. Use the stated height as the scale and fit every visible measurement numerically.

## Procedure

1. **Captures.** Spawn the preview (grooms and `Outfits` cleared), `Studio` lighting map, viewport
   camera at the same distance for every capture: front `(0, 330, 100)` yaw -90, side
   `(330, 0, 100)` yaw 180, then `SceneCaptureToolset.CaptureEditorViewport`. Same camera for every iteration,
   so captures are comparable.
2. **Scale by height, calibrate by method.** Align reference and render at neck row and sole row
   (excludes hair and floor). Measure both images *the same way*, then
   `target_cm = MetaHuman_reported_cm x (reference_estimate / render_estimate)`. The ratio cancels
   most method error: where MetaHuman places its tape, the ellipse approximation, lens.
3. **Circumferences from two views.** MetaHuman measurements (`Neck`, `Chest`, `Waist`, `Thigh`,
   `Knee`, `Calf`) are girths: front width x side depth -> ellipse perimeter (Ramanujan).
   `Across Shoulder` is a straight front width (deltoid-to-deltoid max just below the neck).
4. **Levels** as fractions of neck-to-sole length L below the neck: neck 0.0, shoulders max in
   0.02-0.10, chest (see below), waist = min torso width in 0.25-0.34, knee/above-knee ~0.60-0.68,
   calf = max leg width in 0.72-0.82.
5. **Apply, respawn the preview actor, recapture, re-measure** (a capture taken on the old
   preview after a body commit shows the head offset at the neck; see Pitfalls) until every
   visible level is within ~1-2%; then show the user
   an overlay (reference outline red, render outline cyan, aligned at neck and sole) plus a
   per-level % table.
6. `set_body_constraints` takes normalized 0..1 values: convert cm with `(target-min)/(max-min)`
   from `get_body_constraints`, and re-send the other active constraints' current normalized
   values so they hold.

## Pitfalls

- **Draw a debug image of every measurement span** on all four images before trusting a number;
  each bug below was invisible in the numbers and obvious in the debug image.
- **Neck on front views:** the narrowest row under the head is the chin tip, not the neck. Take the
  neck row from the side view (front/side pairs share framing: assert the sole rows agree).
- **Chest on front views:** in A-pose the arms touch the torso at nipple height, so the run
  includes the arms. Use the first row below the armpits where the central width drops under 0.8x
  the shoulder span; side depth at nipple level.
- **Arms are not comparable:** MetaHuman's A-pose angle differs from a photo's, so equal levels hit
  different anatomy (forearm level lands on the wrist). Leave `Bicep`/`Forearm` unmeasured.
- **Hidden regions stay hidden:** don't scale `Thigh` (upper thigh) or `Hip` from the visible lower
  thigh under shorts; it produced bulky thighs and pulled the hips up. Fit the visible part with
  the matching constraint (`Knee`) and report the hidden ones as unmeasurable.
- **Don't override the reference with an adjective** of your own ("lean" -> shrinking the waist
  below the preset). The reference image wins over your interpretive words. The user's direction
  after seeing the fit ("more definition", "he works outdoors") wins over the reference: apply it
  with the overall sliders, keep the fitted girths pinned, and re-measure them afterwards.
- **Masks:** reference photo background estimated per row from the image edges; fill holes only
  above the knees (legs + floor shadow enclose the leg gap); find the sole from skin-coloured
  pixels (R-B > 15) to skip floor shadow; use the skin mask for leg levels (the Studio floor disc
  pollutes the plain mask). MetaHuman's grey briefs match the studio background and cut the waist
  outline: drop rows whose width collapses below 0.6x the band median.
- Viewport captures are perspective; at 330 cm from a ~2 m figure expect a few % width error. A
  show-only orthographic SceneCapture2D export was not verified working; the ratio method makes it
  unnecessary.
- Skin tone and the unfitted preset head dominate how a body reads; offer to set skin before
  asking for body approval.

## Orthographic route (no viewport captures)

Export the preview's body and head meshes (positions and triangles, as in the face-fitting
reference), render white-on-transparent silhouettes in headless Blender with an orthographic
camera, and measure those against the reference picture. This removes the perspective error, the
floor disc and the briefs-match-the-background problem above. For the side view drop the arms by
deleting body triangles beyond a half-width (~24 cm) and fill the holes that leaves.

- **No outline measure of shoulder width held up.** The widest row below the neck measures the
  arms; the sharpest bend of the outline and joints found along the upper-arm axis each broke on
  one figure. Set `Across Shoulder` by overlay, and say it was by eye.
- Matching every measurable girth can still read soft and pear-shaped: tightening `Waist` while
  `Hip` and `Thigh` stay free leaves wide hips, and the reference's shorts hide them. After the
  measured fit, do one by-eye pass on `Fat` / `Muscularity`, then `Hip` / `Thigh`, compare
  captures, and report those as by eye. Pin `Neck` and `Neck Length` first so they hold.
- **More definition on request:** raise `Muscularity` in ~0.5 steps with `Chest`, `Waist`, `Hip`,
  `Thigh`, `Knee` and `Calf` held active. The muscle goes to shoulders, arms and chest relief
  (`Bicep` +2 cm) while the fitted girths stay within ~1%. Raising `Across Shoulder` with `Chest`
  pinned (+1.7 cm) reshaped the shoulders but left the outline width unchanged: report "more
  shape, not more width" and ask whether broader was meant.
- **A little leaner on request:** lower `Fat` by ~0.4 and take ~2 cm off `Waist` and `Hip`, with
  chest, shoulders and muscle held. The torso came out 2-3% narrower from the front and 2-5%
  shallower from the side, and the arms slimmed with it. Say that the waist now sits under the
  reference's on purpose.
- Compare captures by pixel row widths, not by a downscaled sheet: a 7% hip change was invisible
  at sheet size. Show body changes as a before | now pair from the same camera.
- **Body edits move a conformed head.** Each commit shifts it rigidly (a few mm) and changes its
  shape slightly (about 0.5 mm on the face, 1 mm on skull and ears after six edits). Re-measure
  the head against its target with a fresh rigid alignment afterwards; a stale alignment reports
  the shift as a shape error. Guard a re-import on the neck seam, not on the whole head.
- **Check limb and torso lengths against survey data, not a generated picture.** AI body
  references are drawn with average-height proportions whatever height was asked for. Regress
  each ANSUR II male measure on stature (public CSV, 4,082 men) and compare at the character's
  height: `crotchheight` vs the lowest mesh point exactly on the midline (`|x| < 0.05`; at 1 cm the
  inner thighs count and the crotch reads 10 cm low), `trochanterionheight` vs the `thigh_l`
  joint, `lateralfemoralepicondyleheight` vs `calf_l`, `acromialheight` vs the skin above
  `upperarm_l`, `suprasternaleheight` vs `clavicle_l`. Joints vs skin landmarks are good to 1-2 cm.
- A default 198 cm masculine body had hip joints and shoulders at the expected heights but the
  crotch 5 cm low, which reads as a long torso. `Inseam` +4 cm (Height held) raised the crotch
  3.5 cm and the hip joints 2.5 cm: it cannot lift the crotch alone.
- **After `commit_body_state`, destroy and respawn the preview actor before any capture** (UE 5.9).
  The head component gets the new bind pose but keeps posing on the old joints, so it renders
  offset from the body by the joint movement: a step, ledge or grey gap at the neck seam, while
  the exported mesh rims coincide exactly. Detect it by comparing `get_socket_location('neck_01')`
  on the face and body components; saving the character or a fresh preview clears it.
- **The body solve is path-dependent**: setting a constraint back does not restore the earlier body
  (up to 5 mm off). Go back by releasing the character and reloading its package, not by re-entering
  values. Body render-data vertex order also reshuffles between rebuilds, so compare body exports
  as point sets, not index by index.
- With the head conformed and chest/waist fitted, the free `Neck` already sat within 1.3% of the
  target's girth: measure before touching it.
- **"Is the head the right size?" gets measurements, one per reference, not an opinion:**
  1. Heads tall = stature / chin-to-crown. Take the chin from the landmark ray hit used for the
     wrap scale; midline-profile heuristics on the head mesh pick the neck base, because the head
     mesh runs down to the chest.
  2. Skull breadth, brow-to-occiput length and pupil distance against adult male norms
     (ISO 16976-2 means, 5th-95th: breadth 153, 144-163 mm; length 197, 185-210; pupil distance
     64.5, 59-71; at stature 1754). A tall figure should sit a few % over these while its body is
     further over, so it comes out at more heads than an average man.
  3. Head against shoulders versus a bust target: silhouettes of both from one orthographic
     camera, aligned at the neck row, outline width every 2 cm below it.
  4. Versus the body picture: crown-to-neck over neck-to-sole, and head width over chest width.
  Generated body pictures tend to be drawn at average-height proportions, so a very tall stated
  height and the picture disagree on head size: name the conflict and which one the build
  follows. A bald head reads smaller than it will with hair, so recommend judging again with
  hair on before reaching for `FaceEvaluationSettings.HeadScale` (0.8-1.3; check it keeps a
  conformed shape before offering it as done).
- **The preview stays grey topology after `commit_skin_settings`.** Set the asset's
  `preview_material_type` to `MetaHumanCharacterSkinPreviewMaterial.EDITABLE`, `save_deferred`
  (ends the session), then reopen: the new preview uses the skin material. `SceneCapture2D` with
  `SCS_FINAL_COLOR_LDR` into an `RTF_RGBA8_SRGB` target then gives well-lit captures in `Studio`.
