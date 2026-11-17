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

collection = character.internal_collection                      # UMetaHumanCollection (BlueprintReadOnly)
r = collection.try_add_item_from_wardrobe_item("Hair", hair_item)   # 5.8 headers: (bool, key); UE 5.9 returned the key alone
if isinstance(r, tuple) and not r[0]:
    raise RuntimeError("item not compatible with slot Hair")
item_key = r[1] if isinstance(r, tuple) else r   # never write `ok, key = ...`: the unpack raises after the item was added

selection = unreal.MetaHumanPipelineSlotSelection(slot_name="Hair", selected_item=item_key)
collection.default_instance.try_add_slot_selection(selection)   # or set_single_slot_selection("Hair", item_key)

with MetaHumanEditSession(character) as mh:
    mh.assemble_for_preview(character=character)                 # parameters exist only after an assembly
    item_path = unreal.MetaHumanPaletteItemPath(item_key=item_key)
    params = collection.default_instance.get_instance_parameters(item_path=item_path)  # UMetaHumanCharacterInstanceBlueprintLibrary ScriptMethod
    melanin = next((p for p in params if p.name == "Melanin"), None)
    if melanin:
        melanin.set_float(value=0.5)                              # UMetaHumanCharacterInstanceParameterBlueprintLibrary ScriptMethod
```

Epic's `example_add_grooms.py` and `example_add_clothing.py` are this flow; the clothing one
sets `PrimaryColorShirt` with `set_color(value=unreal.LinearColor.GREEN)`. Note that Epic
calls `try_add_item_from_wardrobe_item` *before* opening the edit session; adding to the
internal collection does not need a session, but `assemble_for_preview` does.

Listing what is in a palette: `unreal.MetaHumanCollectionBlueprintLibrary.get_slot_names(collection)`,
`get_item_keys_for_slot(collection, "Hair")`, `get_item_display_name(collection, key)`;
`unreal.MetaHumanCharacterInstanceBlueprintLibrary.get_allowed_item_keys_for_slot(instance, "Hair")`.

The library's styles can be listed without the Editor: `WI_*.uasset` files under
`<Engine>/Plugins/MetaHuman/MetaHumanCharacter/Content/Optional/Grooms/Bindings/<Slot>/`
(UE 5.9: 38 `Hair`, 18 `Eyebrows`, 16 `Beards`, 16 `Mustaches`, 6 `Eyelashes`, 1 `Peachfuzz`).
When the user wants to browse them by hand, point them at the character's own editor window
(double-click the character asset; the source names the section `Hair & Clothing` and its tools
`Wardrobe` and `Costume`) and tell them to close it without saving, or to browse on a copy: a
saved pick replaces the character's hair.

### Trying library grooms on a character without saving

The code for "A groom trial needs no test copy if nothing is saved" ("Groom preview timing" in
[face-fitting-to-reference.md](face-fitting-to-reference.md)). It uses Epic's collection API
only, so it also works when the project's MetaHuman service has no wardrobe helpers
(`add_wardrobe_item`, `select_wardrobe_item`, `get_wardrobe`).

```python
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
lib = unreal.MetaHumanCollectionBlueprintLibrary
col = character.internal_collection
assert not sub.is_object_added_for_editing(character)             # select before the session opens
for slot, path in (("Hair", HAIR_WI_PATH), ("Eyebrows", BROWS_WI_PATH)):
    name = path.rsplit("/", 1)[-1].replace("WI_", "")            # display names look like Hair_S_SweptUp_Binding
    keys = {str(lib.get_item_display_name(col, k)): k for k in lib.get_item_keys_for_slot(col, slot)}
    key = next((k for n, k in keys.items() if name in n), None)
    if key is None:                                               # add once: an earlier failed call may already have added it
        r = col.try_add_item_from_wardrobe_item(slot, unreal.load_asset(path))
        key = r[1] if isinstance(r, tuple) else r
    col.default_instance.set_single_slot_selection(slot, key)
# then: try_add_object_to_edit, spawn the preview, sub.assemble_for_preview(character=character),
# set the colours (parameters exist only after an assembly), assemble again, wait for the bind, capture.

# discard
for actor in preview_actors: actor.destroy_actor()
sub.remove_object_to_edit(character)                              # before the reload, or the Editor can crash
unreal.EditorLoadingAndSavingUtils.reload_packages(
    [character.get_outermost()], unreal.ReloadPackagesInteractionMode.ASSUME_POSITIVE)
```

- **Hash the character `.uasset` before the trial and compare after the discard.** Collection
  edits and wardrobe colour changes did not mark the package dirty, so an empty dirty list proves
  neither that nothing changed nor that the discard worked. Also read the selections back: they
  must name the items the character had before.
- **Colour the trial grooms with the character's own hair and brow values**, not the style's
  defaults, so the user judges the cut and not a colour change.
- **Frame hair wider and higher than a face shot**: aim about 3 cm above eye height with a
  field about 40 cm tall (14 degrees at 160 cm), or a swept-up style is cut off at the top. Add
  a brow close-up (5 degrees at 160 cm, front and three-quarter) when brows are being judged.
  Take one front shot first and look at it before the full set.
- **Say what is still underneath.** Brows painted into the face colour map stay under a trial
  brow groom; check the close-ups for a double edge and tell the user either way.
- When the trial comes from a purchased head, show the listing's own picture beside the result
  and name the stock items, so the user sees which part of its look the grooms carry.
- After a context compaction, read the scripting tool's schema again before the first call. A
  guessed argument name or shape spends the two-attempt limit on the call format, and the
  question the user asked stays unanswered.

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

Any of these leave the face **unrigged**; run auto-rigging afterwards.

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

### Comparing presets or look-dev states with front captures

Use this to pick a starting preset or to review a sculpt against a reference image. Content
Browser preset thumbnails (`EditorAssetLibrary.sync_browser_to_objects(paths)` + a window
capture) are only good for a first cut (skin tone, apparent age); they are ~80 px, too small to
judge faces. Epic's `EditorAppToolset.CaptureAssetImage` rejects `MetaHumanCharacter` assets
("Asset type does not support image capture"), so faces need a spawned preview.

1. Shortlist from the thumbnails, then for each candidate create a **scratch copy** in a
   throwaway folder (VibeMetaHumans: `create_character("/Game/.../_Scout", "Scout_<Preset>",
   "/MetaHumanCharacter/Optional/Presets/<Preset>")`). Never edit or preview the plugin preset itself.
2. Clear every groom slot (`Hair`, `Eyebrows`, `Beard`, `Mustache`, `Eyelashes`, `Peachfuzz`)
   **in the same call that spawns**, and assert the remaining selections are only `Character`
   and `Outfits`: a preview that wears grooms can hang the editor for minutes, and a clear made
   in an earlier edit session does not survive a save/reload (a scratch copy saved during an
   editor restart came back wearing its preset grooms).
3. Light neutrally: if nothing is dirty, `LevelEditorSubsystem.load_level("/MetaHumanCharacter/LightingEnvironments/Studio")`
   (key/fill/bounce aimed at the origin, grey backdrop). It brings `L_BaseEnvironment` along as a
   sublevel, so `unreal.PythonTools.get_resident_maps()` lists it; that is the open world, not a leak.
   Review one candidate at a time at the origin: `end_edit` the previous one (destroys its
   preview), then spawn the next transient (`spawn_in_level(c, origin, rot, True)`). In a game
   map instead, spawn far above the level (z=30000) so foliage never occludes; either way
   `get_dirty_map_packages()` must stay empty.
4. Frame from the head socket, not a fixed height (presets differ by >10 cm). The transient
   preview is invisible to `EditorActorSubsystem.get_all_level_actors()`; find it with
   `GameplayStatics.get_all_actors_of_class(world, unreal.Actor)` filtered on a class name
   containing `MetaHuman`, take the `SkeletalMeshComponent` with socket `head`, and put the
   viewport camera at `(head.x, head.y + 75, head.z + 3)`, yaw -90 (previews face **+Y**) via
   `UnrealEditorSubsystem.set_level_viewport_camera_info`; `select_nothing()` hides gizmos;
   capture the editor viewport. Keep these helpers in one small module under
   `Saved/` and `importlib.reload` it per call rather than re-sending the code.
5. `execute_python` saves nothing by itself: never save while a scratch character is dirty, and
   check `unreal.PythonTools.get_dirty_packages()` before any save.
6. Present the candidates as one labelled contact sheet (crop each capture to the head, paste
   side by side with Pillow via `uv run --no-project --with pillow`) plus a one-line fit verdict
   each and a recommendation.
7. Clean up: `end_edit` each scratch character; scratch packages stay dirty and unsaved. If they were
   saved anyway, they are untracked task-owned scratch: delete them (with the user's go-ahead) once
   the real character exists.
8. **Editor restart during look-dev:** first `end_edit`, save every task-owned asset you want to
   keep (test copies, template static meshes), delete approved scratch, and confirm
   `get_dirty_content_packages()` is empty; only the `Studio` map (transient previews/cameras) may
   stay dirty. Relaunch with VibeUE `BuildAndLaunchGame.ps1 -SkipBuild -Map /MetaHumanCharacter/LightingEnvironments/Studio`.
   The script force-quits the old Editor, so the next launch opens a modal **Restore Packages**
   dialog: the health heartbeat's `gameThreadStallSeconds` keeps climbing, `mcpListening` stays
   false and the log stops after font loading. Confirm it by listing the Editor PID's visible
   window titles (Win32 `EnumWindows` from a PowerShell script file), then ask the user to click
   **Skip Restore**: restoring can put an older autosave over saved work. After the restart,
   recreate transient fit cameras and call `assemble_for_preview` before judging grooms.
   An Editor the user closed normally opens no restore prompt: the last log ends with
   `LogExit: Exiting.` and `Saved/Autosaves/PackageRestoreData.json` says `RestoreEnabled` false.
   Check both before a launch to know whether to expect the dialog. Compare the newest plugin
   source file with the plugin binaries too: when the source is newer through a checkout that is
   not yours, `-SkipBuild` starts the session on the binaries that last ran instead of compiling
   someone else's change, and the report must say the plugin was not rebuilt.

Creating a character from a preset can take ~15–60 s; a call can report `timed_out` with full
output and a dirtied package. Read the output and the dirty list before retrying, or you create
a duplicate.

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
muscularity=0.70, height_cm=168`.

---

## Source references (UE 5.8)

Under `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/`:
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:529 — `TryAddObjectToEdit`; 533 — `IsObjectAddedForEditing`; 541 — `RemoveObjectToEdit`; 572 — `RunCharacterEditorPipelineForPreview` (`ScriptName="AssembleForPreview"`).
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:685 — `SpawnMetaHumanActor`; 777 — `CanBuildMetaHuman`; 788 — `BuildMetaHuman`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1356 — `RequestAutoRigging`; 1365 — `RemoveFaceRig`; 917 — `RequestTextureSources`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1415 — `FitStateToTargetVertices`; 1437 — `ImportFromIdentity`; 1455 — `ImportFromFaceDna`; 1474 — `ImportFromTemplate`; 1811 — `ConformToTargetMeshes`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1685 — `GetMeshForBodyConformingFromTemplate`; 1723 — `GetJointsForBodyConformingFromTemplate`; 1893 — `ConformBodyToTarget`; 1897 — `SetBodyJoints`; 1901 — `SetBodyMesh`; 1908 — `ImportBodyWholeRig`; 1927 — `GetBodyConstraints`; 1938 — `SetBodyConstraints`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterExportBlueprintLibrary.h`:14 — `FMetaHumanDCCExportParams`; 37 — `FMetaHumanDNAExportParams`; 76 — `FMetaHumanGeometryExportParams`; 108 — `FMetaHumanPosedDNAExportParams`; 157 — `FMetaHumanMaterialsExportParams`; 184 — `UMetaHumanCharacterExportBlueprintLibrary`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterFactoryNew.h`:10 — `UMetaHumanCharacterFactoryNew`.
- `MetaHumanCharacterEditor/Public/Subsystem/MetaHumanCharacterBuild.h`:25 — `FMetaHumanCharacterEditorBuildParameters` (`BlueprintReadWrite` members only are Python-visible).
- `MetaHumanCharacterPalette/Public/MetaHumanCharacterPalette.h`:94 — `TryAddItemFromWardrobeItem`.
- `MetaHumanCharacterPalette/Public/MetaHumanInstance.h`:220 — `SetSingleSlotSelection`; 225 — `TryAddSlotSelection`.
- `MetaHumanCharacterPalette/Public/MetaHumanCollection.h`:303 — `DefaultInstance` (`BlueprintReadOnly`).
- `MetaHumanCharacterPalette/Public/MetaHumanCollectionBlueprintLibrary.h`:141 — instance-parameter ScriptMethods; 232 — `MakeSlotSelection`; 334 — `GetInstanceParametersForItem` (`ScriptMethod="GetInstanceParameters"`).
- `MetaHumanCharacter/Public/MetaHumanCharacter.h`:386–399 — `FaceEvaluationSettings`, `HeadModelSettings`, `SkinSettings`, `EyesSettings`, `MakeupSettings`; 515 — `InternalCollection` (`BlueprintReadOnly`).
- `MetaHumanCharacter/Public/MetaHumanCharacterEyes.h`:39 — `IrisPattern` (`ScriptName="Pattern"`); 43 — `IrisRotation` (`ScriptName="Rotation"`).

Under `Engine/Plugins/MetaHuman/MetaHumanCoreTechLib/Source/MetaHumanCoreTechLib/Public/`:
- `MetaHumanCharacterIdentity.h`:40 — `EAlignmentOptions` (`ScriptName="MetaHumanAlignmentOptions"`); 52 — `FFitToTargetOptions`.
- `MetaHumanCharacterBodyIdentity.h`:89 — `FMetaHumanCharacterBodyConstraint`.

Epic scripts (UE 5.8, `Engine/Plugins/MetaHuman/MetaHumanCharacter/Content/Python/`):
`examples/example_create_asset.py`, `examples/example_auto_rig.py`, `examples/example_assembly.py`,
`examples/example_modify_skin.py`, `examples/example_sculpt_body.py`, `examples/example_sculpt_face.py`,
`examples/example_live_edit.py`, `examples/example_add_grooms.py`, `examples/example_add_clothing.py`,
`examples/example_conform_head.py`, `examples/example_conform_body_from_template.py`,
`examples/example_download_textures.py`, `examples/example_export_tools.py`,
`examples/example_spawn_metahuman_actor.py`, `metahuman_character_test_utils.py`,
`test_cloud_requests.py`; and `Engine/Plugins/Experimental/Toolsets/MetaHumanGenerator/Content/Python/metahuman_toolset/metahuman.py`.
