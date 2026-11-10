# Likeness measurement limits (face fitting to AI references)

Lessons from fitting a MetaHuman to a six-view AI-generated head turnaround.

- **Landmark error can't see volume.** IPD-normalised MediaPipe landmark error measures only where features sit. Cheek mass, jaw definition, brow mass, ear shape and nose form (tip roundness, wing flare, nostril show) never register, and neither do nasion-aligned profile numbers for those, so a "metric at floor" or "nose within 0.1 cm" result can coexist with a user who clearly sees no likeness. When the user disagrees with the numbers, stop sculpting from numbers: ask for a markup with directions, or for a single feature show donor-preset crops and let the user pick.
- **Check the references against each other first.** Compare 3/4-left against a mirrored 3/4-right. AI turnaround views were each edited independently, so they disagree by about as much as a good fit differs from them. Pick hero views (front + one profile) instead of chasing parity with all of them.
- **Meshy is not a shape target for a specific face.** Multi-image Meshy heads scored worse than the template-fitted MetaHuman against the same references:
  - first run with hair, front 2.3 vs Rand 1.0;
  - hairless inputs, `image_enhancement:false`, front + profile only: front 1.9.
  
  A Meshy-vs-MetaHuman surface heatmap reported a "1 cm cheek gap" that the real references did not confirm. Use Meshy for skull, ear and hair outline at most, and validate any Meshy-derived gap against the reference images before brushing.
- **Render framing alone moves scores by up to 0.6.** Use one camera rig for every candidate, or the score differences are noise.
- **Hairless reference sets:** use a minimal-edit prompt (`replace only his hair... everything else pixel-identical... do not make him older/harder`) on each existing haired view, not new angles from a bald front.
  - A 1-2 mm buzz cut drifts less: about 0.6 front, about 1.0 at the 3/4 views.
  - Fully shaved reads harsher and older and drifts to 1.2-1.7.
  
  Score each edit against its haired original with the landmark tool.
  Once the user accepts a buzz set, it is the sculpt reference for forehead, temples, ears and skull; judge overall likeness and hair against the haired set.
- **Showing a generated 3D head to the user:** one sheet per candidate, rows = the input images, the textured render, and a flat grey clay render (geometry only), columns = front / both 3/4 / profile at the same yaws as the references. Clay exposes solid-mesh hair and shape drift that the texture hides. Post the sheets directly when asked to see results, then restate the open decisions.
