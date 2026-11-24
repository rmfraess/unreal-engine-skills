# Python scripting for MetaHuman Creator — deep reference

Deep dive for [../SKILL.md](../SKILL.md). Covers the Python-visible surface of the
`MetaHumanCharacter` plugin (everything `BlueprintCallable` / `BlueprintType`), naming rules,
Epic's shipped example scripts, and recipes for wardrobe, conforming, export, spawning and
batch runs. Grounded in UE 5.8: the headers under `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source`
and Epic's own scripts in `Content/Python/examples/` plus the `MetaHumanGenerator` toolset.

---

## Naming rules (how the C++ names appear in `unreal`)

- Classes drop the prefix: `UMetaHumanCharacter` → `unreal.MetaHumanCharacter`,
  `FMetaHumanCharacterSkinSettings` → `unreal.MetaHumanCharacterSkinSettings`,
  `EMetaHumanRigType` → `unreal.MetaHumanRigType` (values upper snake: `JOINTS_ONLY`,
  `JOINTS_AND_BLEND_SHAPES`). `ScriptName` metadata wins: `EAlignmentOptions` is
  `unreal.MetaHumanAlignmentOptions`; `RunCharacterEditorPipelineForPreview` is
  `assemble_for_preview`.
- Functions and properties are snake_case with Hungarian prefixes removed:
  `TryAddObjectToEdit(InCharacter)` → `try_add_object_to_edit(character)`,
  `bInMatchVerticesByUVs` → `match_vertices_by_u_vs`, `bInLogError` → `log_error`,
  `bKeepTransient` → `keep_transient`, `bBlocking` → `blocking`, `bReportProgress` → `report_progress`.
- `UPROPERTY(... ScriptName="Pattern")` on `IrisPattern` → `iris.pattern`; `IrisRotation` → `iris.rotation`.
- Out-parameters become return tuples: `get_mesh_for_body_conforming_from_template(...)`
  returns `(result, vertices)`; `get_joints_for_body_conforming_from_template(mesh)` returns
  `(result, translations, rotations)`; `get_face_landmarks(character)` returns the array.
- Struct-typed UPROPERTY reads (`character.skin_settings`) hand back a struct you can modify;
  the asset only changes when you pass it to the matching `commit_*`. `BlueprintReadOnly`
  properties (`skin_settings`, `head_model_settings`, `face_evaluation_settings`) are
  readable but must be written through the subsystem.
- Subsystem access: `unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)`.

Everything in this file was checked against the 5.8 headers: a function is listed only if it
carries `UFUNCTION(BlueprintCallable...)` and a struct only if it is `USTRUCT(BlueprintType)`
with `BlueprintReadWrite`/`BlueprintReadOnly` members.

---

## Session helpers (from Epic's `metahuman_character_test_utils.py`)

```python
import unreal

class MetaHumanEditSession:
    """try_add_object_to_edit on enter, remove_object_to_edit on exit."""
    def __init__(self, character):
        self.character = character
        self.mh = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    def __enter__(self):
        if not self.mh.try_add_object_to_edit(self.character):
            raise RuntimeError(f"{self.character.get_name()} is already open for edit")
        return self.mh
    def __exit__(self, *exc):
        if self.mh.is_object_added_for_editing(self.character):
            self.mh.remove_object_to_edit(self.character)
        return False

def create_character(package_path: str, name: str) -> unreal.MetaHumanCharacter:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    _, unique = tools.create_unique_asset_name(base_package_name=f"{package_path}/{name}", suffix="")
    asset = tools.create_asset(asset_name=unreal.Paths.get_base_filename(unique),
                               package_path=package_path,
                               asset_class=unreal.MetaHumanCharacter,
                               factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
    if asset is None:
        raise RuntimeError("create_asset failed")
    return asset
```

If the character is open in the asset editor, `try_add_object_to_edit` returns False but the
subsystem already holds a session — call the edit functions anyway (Epic's
`example_live_edit.py` does exactly this after `AssetEditorSubsystem.open_editor_for_assets`).

---

## Grooms and clothing (wardrobe items)

Slot names: `Hair`, `Eyebrows`, `Beard`, `Mustache`, `Eyelashes`, `Peachfuzz`, `Outfits`
(plus top/bottom garment and skeletal-mesh slots). Wardrobe item assets live in the optional
content, e.g. `/MetaHumanCharacter/Optional/Grooms/Bindings/Hair/WI_Hair_L_StraightBangs`
and `/MetaHumanCharacter/Optional/Clothing/WI_DefaultGarment`, or in your own project
(`UMetaHumanWardrobeItem` assets whose Principal Asset is a groom binding / outfit).

```python
character = unreal.load_asset("/Game/Characters/MetaHumans/MH_Pilot.MH_Pilot")
hair_item = unreal.load_asset("/MetaHumanCharacter/Optional/Grooms/Bindings/Hair/WI_Hair_L_StraightBangs.WI_Hair_L_StraightBangs")

with MetaHumanEditSession(character) as mh:
    collection = mh.get_preview_collection(character)              # the session's built collection
    ok, item_key = collection.try_add_item_from_wardrobe_item("Hair", hair_item)   # -> (bool, FMetaHumanPaletteItemKey)
    if not ok:
        raise RuntimeError("item not compatible with slot Hair")
    collection.default_instance.set_single_slot_selection("Hair", item_key)   # or try_add_slot_selection(...)
    mh.on_edit_preview_collection(character)                       # preview -> character asset

    mh.assemble_for_preview(character=character)                   # builds the preview collection only
    item_path = unreal.MetaHumanPaletteItemPath(item_key=item_key)
    params = collection.default_instance.get_instance_parameters(item_path=item_path)  # UMetaHumanCharacterInstanceBlueprintLibrary ScriptMethod
    melanin = next((p for p in params if p.name == "Melanin"), None)
    if melanin:
        melanin.set_float(value=0.5)                               # UMetaHumanCharacterInstanceParameterBlueprintLibrary ScriptMethod
    mh.on_edit_preview_collection(character)
```

Query and set instance parameters on the **preview collection**
(`get_preview_collection(character).default_instance`), not on `character.internal_collection`.
`assemble_for_preview` (`RunCharacterEditorPipelineForPreview`) builds and assembles only the
preview collection; the internal collection's built data is cleared whenever an item is added
and on every copy-back (`UMetaHumanCollection::CopyContentsFrom` calls `ClearBuiltData`), so
`get_instance_parameters` on it fails with "Collection is not built". Epic's
`example_add_grooms.py` adds the item to and queries `internal_collection`; by the 5.8 and
5.9 source that query has no built data to read. The internal collection is also overwritten from
the preview on the next `on_edit_preview_collection` while a session is open. Details, the
Creator-open case and the full groom parameter list:
[custom-wardrobe-content.md](custom-wardrobe-content.md#scripting-a-character-that-is-open-in-the-creator).

**5.9: standalone Collection and Instance assets are session-only for scripts.** On a
`UMetaHumanCollection` or `UMetaHumanInstance` that is an asset in its own right (or an editing
session's staged copy), `try_add_item_from_wardrobe_item` and setting an instance parameter (`set_float`, ...)
raise a script error ("... is an asset, which scripts edit only through an editing
session"). Use `unreal.get_editor_subsystem(unreal.MetaHumanCollectionEditingSubsystem)
.open_collection_session(collection, "my-script")`, then on the handle `add_wardrobe_item(slot,
item)`, `build_preview()` then `get_instance_parameters(...)` for parameters (or
`open_instance_session` for an Instance asset), and `apply_changes()` (which closes the handle). A
character's internal collection and the Creator's preview collection are sub-objects, not
assets, so the flow above is unaffected (`MetaHumanScriptEditPolicy.cpp`,
`MetaHumanCollectionSessionHandle.h`; read in 5.9 source, not run).

Epic's `example_add_clothing.py` sets `PrimaryColorShirt` with
`set_color(value=unreal.LinearColor.GREEN)`.

Listing what is in a palette: `unreal.MetaHumanCollectionBlueprintLibrary.get_slot_names(collection)`,
`get_item_keys_for_slot(collection, "Hair")`, `get_item_display_name(collection, key)`;
`unreal.MetaHumanCharacterInstanceBlueprintLibrary.get_allowed_item_keys_for_slot(instance, "Hair")`.

---

## Conforming a head

From a `.dna` file (whole-rig import makes a fixed, non-editable body; `import_whole_rig=False`
uses the head DNA only for neck alignment):

```python
params = unreal.ImportFromDNAParams()
params.import_whole_rig = False
params.alignment_options = unreal.MetaHumanAlignmentOptions.SCALING_ROTATION_TRANSLATION
result = mh.import_from_face_dna(character=character, dna_file_path="D:/scans/head.dna", import_params=params)
if result != unreal.ImportErrorCode.SUCCESS:
    raise RuntimeError(result)
```

From a template skeletal/static mesh in MetaHuman topology (eyes/teeth optional):

```python
params = unreal.ImportFromTemplateParams()
params.use_eye_meshes = True
params.use_teeth_mesh = True
params.match_vertices_by_u_vs = True
params.alignment_options = unreal.MetaHumanAlignmentOptions.SCALING_ROTATION_TRANSLATION
result = mh.import_from_template(character, head_mesh, left_eye_mesh, right_eye_mesh, teeth_mesh, params)
```

From raw vertices (any source that gives you MetaHuman-ordered head vertices):

```python
fit = unreal.MetaHumanCharacterFitToVerticesParams()
fit.options.alignment_options = unreal.MetaHumanAlignmentOptions.SCALING_ROTATION_TRANSLATION
fit.options.adapt_neck = True
fit.options.disable_high_frequency_delta = True
fit.head_vertices = head_vertices            # list[unreal.Vector]; eyes/teeth lists optional
mh.fit_state_to_target_vertices(character=character, params=fit)
mh.commit_face_state(character)
```

From a MetaHuman Animator Identity: `mh.import_from_identity(character, identity_asset, unreal.ImportFromIdentityParams())`.
Arbitrary-topology meshes go through `conform_to_target_meshes(character, target_mesh_key, conform_params)`
with keypoints (`commit_target_mesh_keypoints`) — the Mesh Import tool's headless path.

`import_from_template` passes `adapt_neck = not params.isolate_head_from_body`
(`ImportFromTemplate` in `MetaHumanCharacterEditorSubsystem.cpp`), so the default import
already re-solves the neck against the body; isolating the head is what keeps an edit
vertex-exact. Re-importing a conformed head with the neck solve on moved only the neck base
and middle (under 6 mm) and left the face at 0.00 mm.

None of these clears an existing face rig (the rig state is just "has face DNA"): on a rigged
character call `remove_face_rig` then `request_auto_rigging` afterwards, or the build pairs the
old rig with the new face.

## Editing an existing head, vertex-exact

For small shape edits (a neck, a cheek) on a character that already sits on its body:

1. Read the preview Face mesh LOD0 (`GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh`)
   and write the target positions per vertex. Two edit shapes:
   - **Add form** (a muscle, a cheek): displace skin vertices along their normals with smooth
     falloffs. Model a muscle as distance to a continuous polyline on the surface, not to
     sampled points (sparse samples give blotches).
   - **Slim or widen a column** (a neck): scale skin x/y about the column's axis to a target
     width x depth measured at one height (centre from the front/back midline points), with
     weight = inside an enlarged ellipse of that ring (keeps jaw and shoulders out) x a fade
     toward the jaw x a fade toward the seam. Print girth/width/depth per height before and
     after: near the seam the column cannot change, so check where the change actually lands.
   For both: fade every move to zero 1-3 cm from the skin's open border (the body seam) and
   assert the border vertices did not move; reject any flipped triangle. Before writing any
   target, confirm the defect exists in the rest pose at all (posed vs rest:
   [Capturing the posed in-game mesh](#capturing-the-posed-in-game-mesh)); do not slim a neck to
   fix a posed-only roll: a thinner column over the same base pinches harder (SKILL.md,
   body-shape diagnosis). Render before/after with the body attached and show the user before
   importing, then pass the textured in-game close-up gate (SKILL.md) before touching the real
   character; rig and rebuild cost about 15 minutes per try.
2. Build one static mesh per material section (skin, each eyeball, teeth) from the **source**
   model with the target positions. Map source vertices to render vertices **by position**,
   not by triangle order: the two can list triangles differently after rigging. Assert every
   source vertex found a render vertex within 1e-4.
3. `import_from_template(character, head, eye_l, eye_r, teeth, params)`, then
   `commit_face_state`. Measure the result per material section against the target: skin and
   the seam should match to 0.00 mm. Eyelash cards are re-placed from the lids by the engine,
   so they always differ; any other section that moved means the import options re-solved or
   re-aligned the head; fix the options rather than accepting the drift.
4. Re-rig the scratch character, export the head, and compare it with the target. Keep the tested template meshes through the textured PIE review. Selecting a variant for review is not approval to replace production.
5. On explicit promotion, compare the current production head to the pre-trial export; stop if it drifted. Import the **same tested** head, eyes and teeth with alignment `NONE` and `isolate_head_from_body=True` for an already aligned target. Check skin error and seam alignment before and after re-rigging. Save and run the project's existing rebuild, including its post-build fixes.
6. After Editor restart, compare saved skin positions with the approved target. Query Asset Registry hard and soft package dependencies of the character and generated packages for scratch paths: local PIE can resolve a dependency that won't ship. Verify the ordinary pawn uses the production mesh and expected grooms without a mesh swap. Leave scratch cleanup separate until authorized.

## Promoting a pose corrective to an assembled face

1. Preserve the saved production face and its exact morph-name set. Promote only the approved shape; replacing the face with the scratch duplicate can carry comparison morphs and scratch references into production.
2. Store each tested LOD's sparse vertex IDs, indexed rest positions and displacements as project-owned authoring data. Before writing **any** LOD, use `GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh` with `GeometryScriptLODType.SOURCE_MODEL` to check every target LOD's vertex count, ordered triangles, triangle material IDs and affected rest positions against the tested mesh. Stop on a mismatch rather than applying offsets by stale index.
3. Write `rest + displacement` to the dynamic mesh: `copy_morph_target_to_skeletal_mesh` takes absolute morphed positions, not displacement vectors. Pass the matching `GeometryScriptMeshWriteLOD`, check `SUCCESS` on each call, and save only the target asset. Invoke this same guarded writer from the character's post-assembly step so regeneration reapplies it or explicitly rejects a changed mesh.
4. Cold-load the face. Require the original morph-name set plus exactly the approved target; check hard and soft package dependencies for scratch references. Verify activation separately on the possessed production pawn: replay the calibration motion and **observe**, never set, the driver weight. Compare posed vertices with the approved result at the same pose and LOD. A saved morph and a compiled driver establish persistence and compilation, not in-game activation.

## Capturing the posed in-game mesh

What the player sees is the skinned pose (bones, correctives, post-process AnimBP), not the
rest-pose source model. To inspect it as geometry, read the components of the running PIE pawn
with native GeometryScript; for a skeletal mesh component it returns the current pose:

```python
GS, Q, Ls = unreal.GeometryScript_SceneUtils, unreal.GeometryScript_MeshQueries, unreal.GeometryScript_List
pick = lambda r, T: r if isinstance(r, T) else [x for x in r if isinstance(x, T)][0]   # return tuples vary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0); xf = pawn.get_actor_transform()
for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent):       # body + Face
    dm = pick(GS.copy_mesh_from_component(c, unreal.DynamicMesh(),
              unreal.GeometryScriptCopyMeshFromComponentOptions(), True), unreal.DynamicMesh)
    pos = Ls.convert_vector_list_to_array(pick(Q.get_all_vertex_positions(dm, False), unreal.GeometryScriptVectorList))
    tris = Ls.convert_triangle_list_to_array(pick(Q.get_all_triangle_indices(dm, False), unreal.GeometryScriptTriangleList))
    mids = Ls.convert_index_list_to_array(pick(unreal.GeometryScript_Materials.get_all_triangle_material_i_ds(dm), unreal.GeometryScriptIndexList))
    local = [xf.inverse_transform_location(v) for v in pos]               # actor space; write OBJ, keep face material 0 = skin
```

- Confirm it is posed: arms-down hands sit ~35 cm from the centre line, rest-pose arms far more.
- Take every capture in one script without an `await` in between: PIE components can go stale
  across awaits ("ObjectInstance is null"), and a half-written capture pairs mismatched files.
- Check the posed seam: distance from the face skin's open border to the body surface (0 mm
  means the defect is not a crack).
- Clay-render the OBJs in Blender: weld (`remove_doubles`) and `recalc_face_normals` after
  import, and key-light from the camera side about 40 deg up, not straight overhead, or the
  head's shadow hides the neck.
- Render the rest pose through the same script for the posed-vs-rest verdict: read it with
  `GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh` (asset space: faces +Y, origin at
  the feet), rotate to actor axes (actor x = asset y, actor y = -asset x) and drop it by the
  capsule half-height so the same cameras frame both. Different renderers or lights make the
  comparison worthless.
- Calibrate `copy_mesh_from_component` before interpreting a zero delta. In UE 5.9, with a held pose and `options.requested_lod` set to a known authored `SOURCE_MODEL` LOD, an explicit component morph produced measurable off/on displacement and exact off-again restoration. Repeat on the LOD actually rendered: the same weight can produce no displacement there if that tier lacks deltas. This control tests the named morph, not every facial animation curve.
- Cause-isolation toggles (`disable_post_process_blueprint`, `disable_morph_target`, anim
  mode): set `global_anim_rate_scale = 0` on both components first so idle drift does not
  swamp the toggle, then take two captures with no toggle as the noise floor (body 0 mm, face
  a few mm), then toggle. Switching the face to custom anim mode leaves its last pose in place
  rather than resetting to bind. Re-fetch the pawn and components after every `await`.
- Per-vertex distances between two exports are valid only when their triangle index lists are
  identical (compare the files first); a Creator body solve can reorder vertices, which turns
  per-vertex deltas into nonsense such as a 25 cm move.  Use renders or slice profiles then.

## Stock preset in the same pose

A reference for "is this deformation the template's or the character's?", without a build
or a texture download:

1. `duplicate_asset('/MetaHumanCharacter/Optional/Presets/<Name>', '<scratch>/MH_<Name>')`.
   Presets ship unrigged; `request_auto_rigging` (blocking, same rig type as the character,
   about 25 s). `can_build_meta_human` stays False until a texture download, so skip the build.
2. `MetaHumanGeometryExportParams` with `project_path=<scratch folder>`,
   `head_skeletal_mesh=True`, `body_skeletal_mesh=True` → `export_geometry` (character open
   for edit). The head and body skeletal meshes carry DNA and the same bone counts as a built
   character; they reference the plugin's skeleton copies, which the built character's
   AnimBPs still drive.
3. In PIE, `set_skeletal_mesh_asset` the exported body on the pawn's body component and the
   head on `Face`, wait a second or two, check the hands are down and both anim instances
   exist, then capture as above. Nothing is saved; PIE drops the swap.
4. Delete the scratch character and export folder after checking they have no referencers
   outside scratch.

For any export-based trial of an edited character, export the **unchanged** character the
same way and pose it too: that control separates defects of the edit from defects of the
export route (an unchanged export closes the posed seam to 0 mm).

## Moving vertices between two characters' heads

- Render-vertex order differs between characters (and after rigging): match vertices by
  material section plus **nearest** UV (cKDTree per section, accept < 5e-4), the shared
  MetaHuman layout the face import also matches by. Exact UV keys fail: an unrigged or freshly
  solved character's render UVs are rounded differently (seen up to 3.4e-4), and only ~1% of
  vertices matched. Assert every skin vertex found a partner; an odd teeth vertex may not, so
  leave unmatched non-skin vertices as they are.
- The head/body seam is the skin's whole open boundary below the face, welded by position:
  a ring about 6-8 cm high around the neck base, not the lowest-z vertices. Pinning only the
  lowest points moves most of the ring and opens a posed gap of 1 cm or more.
- Before blending part of one head into another, shift the donor by the mean seam-ring
  offset, report the remaining ring difference, keep the receiver's ring exact, fade the
  donor in over 2-3 cm above it, and assert the ring did not move and no triangle flipped.
- Where the donor fades into the receiver, the two shapes disagree and the band creases.
  Under the chin that crease reads as a fold across the throat even with zero flipped
  triangles. Count triangles turned > 30 deg per region and look at that region textured,
  close up, from the front before going further; a whole-neck donor blend has not produced an
  acceptable neck.
- Then fit (`import_from_template` route above), re-rig, export the geometry of the edited
  scratch character and pose it next to an export of the unchanged character.

## Rig vs shape test

To tell a bad face rig from a bad head shape without re-rigging: take the stock preset's
exported head (see [Stock preset in the same pose](#stock-preset-in-the-same-pose)),
`duplicate_asset` it, read both heads with `ModelingService.load_mesh_from_skeletal_mesh`
(positions, per-vertex UVs, triangles, material IDs), match vertices by material + nearest UV,
then `set_vertex_positions` the custom shape onto the copy and
`save_mesh_to_skeletal_mesh_lod(handle, path, 0, False)`. Check the copy's seam ring equals the
stock one (it should, when the body is the same solve), then pose it in PIE on the stock
exported body. Its weights, correctives and joints are the stock rig's, so a defect that
remains belongs to the shape.

## Retouching the face skin maps

For a defect the material bisect (SKILL.md, body-shape diagnosis, step 1) traced to the skin
maps, such as fold lines in the neck normal map. The mesh stays as it is.

1. **Find the live maps.** The character's `skin_settings.texture_material_overrides`
   (`export_text()` lists them) names any face `Basecolor` / `Normal` / `Cavity` override
   textures. Export each one's source to PNG instead of guessing which file on disk made it:
   `AssetExportTask` with `object=<texture>`, `exporter=unreal.TextureExporterPNG()`,
   `automated=True`, `prompt=False`, then `unreal.Exporter.run_asset_export_task(task)`. Diff
   the result against candidate working files to pick the right source. Without an override,
   the synthesised maps are transient: draw them to a render target and export that.
2. **Map the region in texture space.** Export the head (positions + per-vertex UVs +
   triangles + material IDs, same render vertex order) and rasterise a per-vertex weight
   over skin triangles into a mask (smoothstep on height or another 3D test, Gaussian
   softened). Print height and forward depth per UV row along the layout's centre column
   first: in the MetaHuman face layout the strongest neck fold arcs sit on the underside of the
   chin and the upper throat (about rows 0.70-0.85 of the map), not only on the lower neck. A
   mask that stops below the chin leaves them in. Overlay the mask on the map and look at it.
3. **Filter only what the defect is made of.** For fold lines, remove the band between a fine
   and a coarse Gaussian (`c - mask * (G(c, 3 px) - G(c, 40 px))` at 4K): pores and the overall
   shading stay. Run the same mask on the normal and colour maps. For a normal map, rebuild
   blue from red and green inside the mask. Assert every pixel outside the mask is unchanged
   and print the band energy inside the mask before and after.
4. **Preview in PIE before touching the character.** Import the original and edited PNGs the
   same way (`unreal.MetaHumanCharacterService.import_texture(png, folder, name, kind)` with
   `kind` `normal` or `color`), set `virtual_texture_streaming=True` on each, then set
   `Normal Baked VT` and `Basecolor Baked VT` on the head-slot MIDs. Compare original-vs-edited
   (not live-vs-edited) in frozen-time close-ups. This shortcut skips the build's face-to-body
   blend at the seam, so both previews show a pale band on the chest: judge only above the
   seam.
5. **Apply** with the face override slots (`NORMAL`, `BASECOLOR`) through
   `texture_material_overrides` + `commit_skin_settings`, keeping the other slots, then run the
   project's Cinematic rebuild (it re-bakes the 8K maps from the overrides) and compare the
   built character in the same frames.

## Conforming a body from a template

```python
res, verts = mh.get_mesh_for_body_conforming_from_template(character, body_mesh, face_mesh, match_vertices_by_u_vs=False)
res2, joint_t, joint_r = mh.get_joints_for_body_conforming_from_template(body_mesh)
if res != unreal.ImportErrorCode.SUCCESS or res2 != unreal.ImportErrorCode.SUCCESS:
    raise RuntimeError("template not in MetaHuman body topology")
mh.conform_body_to_target(character, verts, joint_r, target_is_in_a_pose=True, estimate_joints_from_mesh=False)
# alternatives: mh.set_body_mesh(character, verts, reposition_helper_joints=True)
#               mh.set_body_joints(character, joint_t, joint_r, import_helper_joints=True)
#               mh.import_body_whole_rig(character, "D:/body.dna", "D:/head.dna")   # fixed body
```

---

## Export (`UMetaHumanCharacterExportBlueprintLibrary`, editor module)

All static, take the character plus a params struct; the character must be open for edit,
rigged, and (for DCC/materials) have high-resolution textures.

```python
lib = unreal.MetaHumanCharacterExportBlueprintLibrary

dcc = unreal.MetaHumanDCCExportParams(); dcc.external_path = "D:/Export/MH_Pilot"; dcc.bake_make_up = True
dcc.compress_in_zip_file = True; dcc.archive_name = "MH_Pilot"
lib.export_dcc(character, dcc)                                   # Maya/DCC package (needs Optional/DCC content)

dna = unreal.MetaHumanDNAExportParams(); dna.project_path = "/Game/MetaHumans"; dna.external_path = "D:/Export/DNA"
dna.dna_head = True; dna.dna_body = True; dna.overwrite_existing_assets = True
lib.export_dna(character, dna)                                   # UDNA assets and/or .dna files

geo = unreal.MetaHumanGeometryExportParams(); geo.project_path = "/Game/MetaHumans"
geo.head_skeletal_mesh = True; geo.body_skeletal_mesh = True; geo.full_body_skeletal_mesh = True
lib.export_geometry(character, geo)                              # standalone skeletal meshes

mat = unreal.MetaHumanMaterialsExportParams(); mat.project_path = "/Game/MetaHumans"; mat.apply_as_overrides = True
lib.export_materials(character, mat)                             # persistent MICs, optionally set as overrides

posed = unreal.MetaHumanPosedDNAExportParams(); posed.project_path = "/Game/MetaHumans"; posed.target_mesh_key = key
lib.export_posed_dna(character, posed)                           # after conform_to_target_meshes
```

---

## Spawning in a level

```python
asset_editor = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
asset_editor.open_editor_for_assets(assets=[character])          # opens the MetaHuman editor (registers the session)
mh = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
actor = mh.spawn_meta_human_actor(character=character)           # AMetaHumanCharacterEditorActor in the current level
```

The actor mirrors live edits and is owned by the subsystem; it is destroyed when the editor
window closes (Epic's `example_spawn_metahuman_actor.py`). `keep_transient=True` keeps the
`RF_Transient` flag so it can never be saved into the map. For a persistent actor, build the
character and spawn the generated Blueprint:

```python
bp = unreal.load_asset("/Game/MetaHumans/MH_Pilot/BP_MH_Pilot.BP_MH_Pilot")
cls = bp.generated_class()
unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(cls, unreal.Vector(0, 0, 100))
```

---

## Batch / headless notes

- Cloud calls must be `blocking = True`, `report_progress = False` (Epic: "Required for
  running in batch"). The blocking path pumps the auth client
  (`ServiceAuthentication::TickAuthClient`) and HTTP until the service answers or fails; a
  failure is a notification plus a log line, not an exception — check
  `can_build_meta_human(character, log_error=True)` afterwards.
- A logged-in Epic account is required in the editor session running the script. There is no
  Python API to log in; `test_cloud_requests.py` simply assumes it.
- Texture synthesis (skin preview) and the presets/wardrobe library need the optional
  content; `FMetaHumanCharacterEditorModule::IsOptionalMetaHumanContentInstalled` is not
  exposed to Python — check for the folder
  `<Engine>/Plugins/MetaHuman/MetaHumanCharacter/Content/Optional/TextureSynthesis` yourself.
- `build_meta_human` is synchronous from Python's point of view and writes many packages;
  save with `unreal.EditorAssetLibrary.save_directory("/Game/MetaHumans")` or
  `save_loaded_asset(character)`.
- `remove_face_rig(character)` returns the face to the archetype DNA; `has_face_dna` and the
  rig state are native-only, so track rig success through `can_build_meta_human`.
- Face sculpt data: `get_face_model_coefficients(character)` → `list[float]`,
  `set_face_model_coefficients(character, coeffs)`; landmarks via `get_face_landmarks` /
  `translate_face_landmarks(character, indices, deltas)`; then `commit_face_state`.
- Testing helpers: `compare_face_state(a, b, tolerance)`, `compare_body_state`,
  `compare_face_textures(a, b, pixel_tolerance)`.

---

## Epic's `MetaHumanGenerator` toolset (experimental)

`Engine/Plugins/Experimental/Toolsets/MetaHumanGenerator/Content/Python/metahuman_toolset/metahuman.py`
wraps the same subsystem for AI agents: `begin_edit(object_path)` / `end_edit(session)`
(a session that registers the character and `finalize()`s), `create(asset_path)` (AssetTools
+ `MetaHumanCharacterFactoryNew`), `get_body_shape` / `set_body_shape` (maps 0..1
`masculine_feminine`, `fat`, `muscularity` onto the `Masculine/Feminine`, `Fat`,
`Muscularity` constraints via `lerp(min_measurement, max_measurement, v)`, `height_cm`
directly; then `set_body_constraints` + `commit_body_state` and a native
`MetaHumanGeneratorSubsystemWrapper.reset_neck_to_body`), `get_skin_tone` / `set_skin_tone`
(`skin.u` = lightness, `skin.v` = redness → `commit_skin_settings`), `get_eye_color` /
`set_eye_color` (`iris.primary_color_u/v` and `secondary_color_u/v` on both eyes →
`commit_eyes_settings`). Its docstrings carry useful calibration examples: pale skin
`[0.10, 0.45]`, medium neutral `[0.50, 0.45]`, very dark warm `[0.93, 0.75]`; light blue eyes
`(0.1, 0.9)`, dark brown `(0.9, 0.1)`; athletic woman `masculine_feminine=0.80, fat=0.25,
muscularity=0.70, height_cm=169`.

---

## Source references (UE 5.9)

Under `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/`:
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:534 — `TryAddObjectToEdit`; 538 — `IsObjectAddedForEditing`; 546 — `RemoveObjectToEdit`; 577 — `RunCharacterEditorPipelineForPreview` (`ScriptName="AssembleForPreview"`).
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:690 — `SpawnMetaHumanActor`; 782 — `CanBuildMetaHuman`; 793 — `BuildMetaHuman`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1361 — `RequestAutoRigging`; 1370 — `RemoveFaceRig`; 922 — `RequestTextureSources`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1420 — `FitStateToTargetVertices`; 1442 — `ImportFromIdentity`; 1460 — `ImportFromFaceDna`; 1479 — `ImportFromTemplate`; 1816 — `ConformToTargetMeshes`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1690 — `GetMeshForBodyConformingFromTemplate`; 1728 — `GetJointsForBodyConformingFromTemplate`; 1898 — `ConformBodyToTarget`; 1902 — `SetBodyJoints`; 1906 — `SetBodyMesh`; 1913 — `ImportBodyWholeRig`; 1932 — `GetBodyConstraints`; 1943 — `SetBodyConstraints`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterExportBlueprintLibrary.h`:14 — `FMetaHumanDCCExportParams`; 37 — `FMetaHumanDNAExportParams`; 76 — `FMetaHumanGeometryExportParams`; 108 — `FMetaHumanPosedDNAExportParams`; 157 — `FMetaHumanMaterialsExportParams`; 184 — `UMetaHumanCharacterExportBlueprintLibrary`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterFactoryNew.h`:10 — `UMetaHumanCharacterFactoryNew`.
- `MetaHumanCharacterEditor/Public/Subsystem/MetaHumanCharacterBuild.h`:25 — `FMetaHumanCharacterEditorBuildParameters` (`BlueprintReadWrite` members only are Python-visible).
- `MetaHumanCharacterPalette/Public/MetaHumanCharacterPalette.h`:93 — `TryAddItemFromWardrobeItem`.
- `MetaHumanCharacterPalette/Public/MetaHumanInstance.h`:243 — `SetSingleSlotSelection`; 263 — `TryAddSlotSelection`.
- `MetaHumanCharacterPalette/Public/MetaHumanCollection.h`:379 — `DefaultInstance` (`BlueprintReadOnly`).
- `MetaHumanCharacterPalette/Public/MetaHumanCollectionBlueprintLibrary.h`:255 — instance-parameter ScriptMethods; 346 — `MakeSlotSelection`; 456 — `GetInstanceParametersForItem` (`ScriptMethod="GetInstanceParameters"`).
- `MetaHumanCharacter/Public/MetaHumanCharacter.h`:386–399 — `FaceEvaluationSettings`, `HeadModelSettings`, `SkinSettings`, `EyesSettings`, `MakeupSettings`; 515 — `InternalCollection` (`BlueprintReadOnly`).
- `MetaHumanCharacter/Public/MetaHumanCharacterEyes.h`:39 — `IrisPattern` (`ScriptName="Pattern"`); 43 — `IrisRotation` (`ScriptName="Rotation"`).

Under `Engine/Plugins/MetaHuman/MetaHumanCoreTechLib/Source/MetaHumanCoreTechLib/Public/`:
- `MetaHumanCharacterIdentity.h`:40 — `EAlignmentOptions` (`ScriptName="MetaHumanAlignmentOptions"`); 52 — `FFitToTargetOptions`.
- `MetaHumanCharacterBodyIdentity.h`:89 — `FMetaHumanCharacterBodyConstraint`.

5.9 script edit policy for Collection and Instance assets:
- `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/MetaHumanCharacterPalette/Private/MetaHumanScriptEditPolicy.cpp`:14 — `CanScriptDirectlyEdit`.
- `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/MetaHumanCharacterPalette/Public/MetaHumanCharacterPalette.h`:104 — `K2_TryAddItemFromWardrobeItem` (script name `TryAddItemFromWardrobeItem`).
- `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/MetaHumanCharacterPaletteEditor/Public/MetaHumanCollectionEditingSubsystem.h`:38 — `OpenCollectionSession`; 42 — `OpenInstanceSession`.
- `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/MetaHumanCharacterPaletteEditor/Public/MetaHumanCollectionSessionHandle.h`:41 — `AddWardrobeItem`; `ApplyChanges`, `BuildPreview`.
- `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/MetaHumanCharacterPaletteEditor/Public/MetaHumanSessionHandleBase.h`:122 — `GetInstanceParameters`.

Epic scripts (UE 5.8, `Engine/Plugins/MetaHuman/MetaHumanCharacter/Content/Python/`):
`examples/example_create_asset.py`, `examples/example_auto_rig.py`, `examples/example_assembly.py`,
`examples/example_modify_skin.py`, `examples/example_sculpt_body.py`, `examples/example_sculpt_face.py`,
`examples/example_live_edit.py`, `examples/example_add_grooms.py`, `examples/example_add_clothing.py`,
`examples/example_conform_head.py`, `examples/example_conform_body_from_template.py`,
`examples/example_download_textures.py`, `examples/example_export_tools.py`,
`examples/example_spawn_metahuman_actor.py`, `metahuman_character_test_utils.py`,
`test_cloud_requests.py`; and `Engine/Plugins/Experimental/Toolsets/MetaHumanGenerator/Content/Python/metahuman_toolset/metahuman.py`.
