# Putting a built MetaHuman on a playable Character

## Copying the MetaHuman Blueprint's components (C++)

- Copy the MetaHuman Blueprint's components onto the Character **under their Blueprint
  variable names**. `LODSyncComponent` and `UMetaHumanComponentUE` find parts by name; without
  LOD Sync the grooms pick their own LOD and the hair disappears beyond about 2 m.
- Put the Body mesh on the Character's own Mesh. `UMetaHumanComponentBase::GetBodySkelMeshComponent`
  falls back to the Face's attach parent when nothing is named `Body`, so body correctives
  still run on the Character Mesh beside the locomotion Anim Class.
- Inside a Blueprint's component tree, `USCS_Node::ParentComponentOrVariableName` is empty for
  ordinary children; track the parent while walking `GetChildNodes()`. `GetAllNodes()` is not
  exported from the Engine module.
- When construction re-runs, rename old copies (`Rename(nullptr, nullptr, REN_DontCreateRedirectors
  | REN_DoNotDirty | REN_NonTransactional)`) before `DestroyComponent`, so their names are free.

## Template locomotion on a MetaHuman body

A batch-retargeted UE5 template AnimBP keeps its foot-IK Control Rig node, which needs
`ik_foot_*` bones the MetaHuman body lacks; legs stay planted while arms animate. Duplicate the
rig and repoint its `ik_foot_*` reads at `foot_*` (`ue-control-rig-and-ik`), keep Alpha 1, then
check foot bones move in actor space while running (`ue-pie-python`, "Sampling over time") and
that both feet plant on a tilted test ramp spawned in PIE. The template rig only moves feet up
and down; it never tilts them to the slope, so toes dip a few cm into steep ground.

## Close-inspection camera

A mouse-wheel zoom that only shortens the spring arm frames the waist (the arm pivots on the
capsule centre). Raise the arm's relative Z toward the head as the length drops below the
default (`FMath::GetMappedRangeValueClamped`), and bind a 1D `IA_Zoom` to `MouseWheelAxis` in
the mapping context; set the action on the Blueprint defaults and recompile it.

Scale motion blur with the same mapping: the camera's `PostProcessSettings.MotionBlurAmount`
(with `bOverride_MotionBlurAmount`) from about 0.1 at the closest zoom up to the engine default
0.5 at the default distance. Close up, swinging limbs cross much of the screen and smear at
the default amount; wide shots stay as before.

## Isolating a neck/shoulder seam line

The face mesh continues down the neck onto the upper back; a hard line there is the face/body
mesh boundary. Isolate before changing anything:

1. Spawn the source MetaHuman Blueprint beside the player under the same light and camera. Same
   line on both: it comes from the build, not your Character setup.
2. Confirm which side is which with a live dynamic instance on the face **skin** slot (look it
   up by name, `face.get_material_index('head_LOD<n>_shader_shader')`; slot 0 is the teeth) and
   push `Basecolor Global Value Post-Bake` down: everything above the line darkens.
3. Then compare textures (sample both UV sides at the shared boundary vertices) and vertex
   normals/tangents (GeometryScript `copy_mesh_from_skeletal_mesh` source LOD 0,
   `get_interpolated_triangle_normal_tangents`; convert lists with
   `GeometryScript_List.convert_*_list_to_array`) before editing materials. Matching textures
   plus differing normals points at shading, not at the bake. A low back-light shows it most.
4. Any fix to the built face mesh or materials is overwritten by a Creator rebuild: keep it as a
   re-runnable script, and test it on a scratch copy first.
