# Fitting a MetaHuman body to reference images

Measure; don't eyeball. Side-by-side vision judgements of body proportions get the *direction*
wrong (thin legs called "fuller"), and a user who sees a gap expects a measured pass, not another
opinion. Use the stated height as the scale and fit every visible measurement numerically.

## Procedure

1. **Captures.** Spawn the preview (grooms and `Outfits` cleared), `Studio` lighting map, viewport
   camera at the same distance for every capture: front `(0, 330, 100)` yaw -90, side
   `(330, 0, 100)` yaw 180, then `capture_image source=editor`. Same camera for every iteration,
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
5. **Apply, recapture, re-measure** until every visible level is within ~1-2%; then show the user
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
- **Don't override the reference with an adjective** ("lean" -> shrinking the waist below the
  preset). The reference image wins over interpretive words.
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
