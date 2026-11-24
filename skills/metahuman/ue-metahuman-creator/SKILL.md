---
name: ue-metahuman-creator
description: Use when scripting MetaHuman Creator characters or builds.
metadata:
  aliases: "MetaHuman, MetaHuman Creator, digital human, character creator, groom, wardrobe"
  engine-version: "5.9"
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
   `RunCharacterEditorPipelineForPreview` (Python `assemble_for_preview`) builds only the edit
   session's preview collection, so query instance parameters on `GetPreviewCollection(Character)`.
   Project grooms/clothing (`WardrobePaths`, item pipelines, template-head grooms,
   the preview-collection trap): [references/custom-wardrobe-content.md](references/custom-wardrobe-content.md).
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

- **"Unable to edit asset"** — `TryAddObjectToEdit` returns false when the character is
  already registered (asset editor open). Either use that session (it is the same subsystem)
  or close the editor. Never call `RemoveObjectToEdit` after a false return.
- **Commit, not raw property writes.** Writing `Character->EyesSettings` directly leaves the
  preview and the identity state out of sync. Use `Commit*`. In Python, properties like
  `skin_settings` are `BlueprintReadOnly`: read, modify the copy, commit.
- **Rig state.** `EMetaHumanCharacterRigState { Unrigged, RigPending, Rigged }`.
  `GetRiggingState` is just `HasFaceDNA()`, and a face conform or template import plus
  `CommitFaceState` does **not** clear the DNA. The character stays `Rigged` and
  `can_build_meta_human` stays True, so a build pairs the old rig with the new face. After
  any face shape change on a rigged character, call `remove_face_rig`, then
  `request_auto_rigging` (blocking, same rig type as before; about a minute), then export the
  preview head and confirm it still matches the target before building. `RemoveFaceRig`
  reverts to the archetype DNA. A rigged face is what
  gives the built `SKM_Face` its RigLogic DNA and the 200+ facial controls that MetaHuman
  Animator, Live Link Face (`ABP_MH_LiveLink`, `Face/ARKit/` mapping) and Control Rig drive.
  `JointsOnly` is lighter; `JointsAndBlendShapes` adds blendshapes (`HasFaceDNABlendshapes()`)
  for the Cinematic look.
- **Textures gate the build** even when materials will be overridden: assembly needs the
  animated maps that arrive with the texture download. Desired resolutions live in
  `SkinSettings.DesiredTextureSourcesResolutions` (`ERequestTextureResolution` 2k/4k/8k);
  `NeedsToDownloadTextureSources()` tells you when a re-download is needed.
- **Pass the edited constraint objects back.** Iterating the array from
  `get_body_constraints` yields copies: edit them, collect them into a list, and pass that list
  to `set_body_constraints` (as Epic's `example_sculpt_body.py` does). Passing the original
  array back applies nothing and raises nothing. Re-read the constraints to confirm.
- **Try body/face changes on a scratch copy with a live preview.** `duplicate_asset` the
  character, `try_add_object_to_edit`, `spawn_meta_human_actor(character, keep_transient=True)`
  (spawns at the world origin; move it where the light is right), then `set_body_constraints`:
  the preview actor updates without a commit. Capture each variant from fixed cameras with
  `unreal.ViewportService.capture_with_view` (front, 3/4 low, side) and compare side by side.
  Then `remove_object_to_edit` and delete the scratch asset; the real character is untouched.
  Creator's preview draws a thin line at the face/body boundary that the build does not.
- **Diagnose a body-shape complaint (lumps, ledges, odd neck) on the posed in-game mesh
  first, before any sculpt.** Rest-pose exports and Creator previews can be smooth while the
  game pose shows a ring or ledge from skinning/correctives where face and body meshes meet;
  sculpting the rest pose then changes nothing the user sees. Steps, cheapest first:
  1. **Split geometry from shading first, before any mesh work**, in PIE at the user's camera
     and view (front close-ups included), time frozen and shot repeatability checked (recipe:
     `ue-pie-python`, Captures). Set every face and body slot to
     `/Engine/BasicShapes/BasicShapeMaterial`: if the lumps vanish, they are drawn by the skin
     material, and no mesh edit can fix them. Then bisect cumulatively with the skin material's
     own scalars on the head MIDs (`M_skin_unified_baked`), one capture per step: animated
     wrinkle weights (`head_wm*_normal_*`, e.g. `neckStretch_L/R`) → `Fake AO Strength`,
     `Material AO Power` → `Micro Skin Normal Strength`, `Intensity Neck` → `Normal Flatten` 1 +
     `Normal Global Strength Post-Bake` 0 → `Specular Global Multiply Post-Bake` 0; what is left
     after that is painted into the colour map. Horizontal neck folds in a character's baked
     face normal map, raked by a low sun, read as lumps from the front and side.
     `Clay Basecolor Blend` exists on the head material only, so it leaves the body skin
     textured. Only when the defect survives the plain material is it geometry; continue below.
     When it is the maps, retouch the maps rather than the mesh (recipe:
     [references/python-scripting.md](references/python-scripting.md#retouching-the-face-skin-maps)).
  2. Capture the posed meshes from PIE (recipe:
     [references/python-scripting.md](references/python-scripting.md#capturing-the-posed-in-game-mesh))
     and check the arms are down (not the rest pose).
  3. Render posed and rest meshes as clay through the same script, side by side, with a key
     light from the camera side, ~40 deg up. An overhead sun buries the neck in the head's
     cast shadow and hides the shape.
  4. If only the posed clay shows it, run a stock MetaHuman preset (own head and body) through
     the same pose and renders before touching the character (recipe:
     [references/python-scripting.md](references/python-scripting.md#stock-preset-in-the-same-pose)).
     Judge the size of the difference the way the user sees it: a faint line on the preset
     against obvious lumps on the character means the character's own geometry is the cause.
     Never write that off as template behaviour because the preset shows a trace of it.
     Isolate one factor per control, and prove it:
     - A body solve starts from the current body, so the character's constraints on another
       preset give a different neck base (seam ring up to ~1 cm off in shape, ~2.5 cm higher).
       Measure the seam ring (the skin's full open boundary) between the two before crediting
       the result to the head or the body (vertex matching and ring detection:
       [references/python-scripting.md](references/python-scripting.md#moving-vertices-between-two-characters-heads)).
     - A stock head mesh swapped onto the custom body in PIE does not reach the seam and
       looks falsely clean.
     - Rig vs shape: write the character's head positions into a stock-rigged exported head
       and pose it on the same body (recipe:
       [references/python-scripting.md](references/python-scripting.md#rig-vs-shape-test)).
       Still lumpy means the shape, not weights, correctives or the auto-rig.
     - Shape: profile the head's neck radius against the stock head on the same body per
       2 cm height and per angle (back, side, front). A custom neck a few mm to ~1 cm thinner
       than stock above the seam correlated with the posed roll; treat it as a lead, not a
       proven cause.
     Blending the stock neck into the custom head is not a fix: it cleared the roll in clay
     back views but put a fold across the throat where the blend met the jaw, visible only in
     textured front close-ups. Re-solving the neck with Epic's fitter (`adapt_neck`) is not
     one either: on an already conformed head it moved the neck under 6 mm and changed
     nothing visible. `import_from_template` already sets
     `bAdaptNeck = !isolate_head_from_body`, so a default conform has had the neck solve;
     only a vertex-exact edit (`isolate_head_from_body=True`) skips it. If both posed and rest show the defect, sculpt. If a shape fix the user
     reviewed did not change what they see, do not try another variant: go back to step 2,
     because the fix was aimed at the wrong state.
  5. Before any new shape attempt after a rejected one, have the user mark the defect on a
     current screenshot (which region, which view). Several scripted neck variants in a row
     each fixed a measured proxy while the user's complaint was elsewhere.
  Never slim a neck to fix posed lumps: a thinner column over the same base pinches harder.
  Measure against the stock head on the same body, not only against girth norms (lean adult
  man about 38-40 cm girth, neck about 0.8x jaw width, wider than deep). Single-vertex slope
  reads are noisy: profile at 1 cm steps before calling something a corner. Adding muscle
  ridges to a thick neck read lumpier.
- **Accept a head or neck shape change only from textured in-game close-ups.** Before
  applying it to the real character or committing, pose a scratch export in PIE with the
  character's real materials (re-applied by slot name after the mesh swap), animation frozen,
  at the gameplay camera's closest zoom, from the front (slightly below the chin), front-side,
  side and back, next to the unchanged character in the same frames (recipe: `ue-pie-python`,
  Captures). Untextured clay renders from the back and sides at a distance passed a change
  the user then called grotesque from the front. A geometry check that the build equals the
  target proves only that the build is faithful, not that the shape is right. Treat any
  warning from your own script (many triangles turned > 30 deg in a blend band, flips) as a
  blocker until you have looked at that region close up.
- Before using a saved per-vertex mask for fitting **or measuring** a bust transfer, verify its vertex order against the current export. Matching counts or skin index sets do not prove a jaw or occlusion label still belongs to the same point. If correspondence is unknown, select the region from current geometry, inspect it, then measure face-to-surface distances at fixed scale. Exclude the shoulder shelf as well as the seam from equal-height matches: a radial ray there can hit a different anatomical surface. Check changed triangle turns against the original before exporting the target.
- **The face owns the upper neck, the body owns its base.** A head conform pins everything
  below the chin to the body seam, so the lower neck's size is the body's seam ring, set by
  the body constraints (`Neck`, `Neck Base`, `Muscularity`). A head-only edit (vertex-exact
  recipe: [references/python-scripting.md](references/python-scripting.md#editing-an-existing-head-vertex-exact))
  reshapes the column from just above the seam ring up to the jaw; it cannot move the ring
  itself. Body constraints barely reach the base either: `Muscularity` 1.5 -> 0.8 with
  `Neck`/`Neck Base` cut 4-5 cm shrank chest and shoulders slightly but left the trapezius
  mound and neck base essentially as they were. Render a scratch-copy body before promising a
  body fix, and tell the user which half each option reaches before applying either.
- **Undo a head edit from version control, not by re-editing.** If the character and its
  built output were committed before the edit, stop PIE, close the Editor
  (`CloseMainWindow`, then confirm the process is gone), `git revert --no-edit <newest> <older>`
  for committed edits (keeps history), or `git checkout <previous> -- <every Content path the
  edit changed>` for uncommitted ones. Confirm `git diff --stat <good> HEAD -- Content` is
  empty, relaunch and export the head to confirm it matches the pre-edit export. The committed rig and build come
  back with it, so no re-rig or rebuild is needed.
- **Fixed body types.** `bFixedBodyType` is set when a whole body rig is imported from DNA
  (`FImportFromDNAParams::bImportWholeRig`, `ImportBodyWholeRig`) or a legacy compatibility
  body (`EMetaHumanBodyType::f_med_nrw`...) is chosen: the body constraints then do nothing
  until `ResetParametricBody`.
- **Pipeline quality only matters for Optimized/UEFN.** `Cinematic` ignores
  `PipelineQuality`. A Cinematic build into an existing Optimized folder: face LOD0 went from
  18.6k verts and 588 bones to 33.8k and 737, with 8 face LODs on 4 body LODs and 8K face
  normal/SRMF. It also copies about 170 shared assets into `CommonFolderPath`. Python may raise
  a logged control-rig error ("Cannot break link ... Face_ControlBoard_CtrlRig") although
  assembly succeeded: check the log and the saved output. Saving is yours: the build leaves its
  packages dirty.
- **Cinematic face colour is baked at 2K.** `BP_DefaultLegacyPipeline`'s editor pipeline
  (`editor_pipeline` property, not a method) has
  `material_baking_options.face_baking_options.texture_resolutions_overrides['T_Head_BC']` =
  2048, even when the source maps are 4K. Raise it on the class default before
  `build_meta_human` and restore it after; never save the engine asset. The value is an
  `unreal.MetaHumanBuildTextureResolution` entry: map a size with
  `getattr(unreal.MetaHumanBuildTextureResolution, f'RES{size}')`.
- **Restart the Editor after a rebuild, before PIE.** Blueprints that reference the rebuilt
  BP can keep a transient `BP_<Name>_TEMP_..._C` class in memory. A character copying from it
  gets groom components with no assets, so the character appears bald.
- **Scripted rebuild of an existing character:** refuse to start with unsaved packages; open
  for edit, apply any temporary pipeline override (above) in `try/finally`; build; accept the
  known control-rig error only; assert every dirtied package is under the build or common
  folder, then save them; verify output (texture sizes, LOD counts); re-run every post-build
  fix script (seam, materials, grooms); restart the Editor. Keep it as one project script so
  a rebuild never drops a fix. For pose-only edits on an assembled face, use the [corrective promotion recipe](references/python-scripting.md#promoting-a-pose-corrective-to-an-assembled-face) rather than re-conforming the neutral head.
- **Legacy pipelines** come from `UMetaHumanCharacterPaletteProjectSettings::DefaultCharacterLegacyPipelines`
  keyed by `EMetaHumanQualityLevel`; Cinematic uses `BP_DefaultLegacyPipeline`.
  `BP_DefaultPipeline` is the current default.
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

Engine source (UE 5.9 — all paths under `Engine/Plugins/MetaHuman/MetaHumanCharacter/Source/`):
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
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:496 — `UMetaHumanCharacterEditorSubsystem`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:534 — `TryAddObjectToEdit`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:782 — `CanBuildMetaHuman`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:793 — `BuildMetaHuman`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1361 — `RequestAutoRigging`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSubsystem.h`:1932 — `GetBodyConstraints`.
- `MetaHumanCharacterEditor/Public/Subsystem/MetaHumanCharacterBuild.h`:25 — `FMetaHumanCharacterEditorBuildParameters`.
- `MetaHumanCharacterEditor/Public/Subsystem/MetaHumanCharacterService.h`:20 — `FMetaHumanCharacterEditorCloudRequests`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorModule.h`:15 — `IsOptionalMetaHumanContentInstalled`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorSettings.h`:36 — `UMetaHumanCharacterEditorSettings`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterFactoryNew.h`:10 — `UMetaHumanCharacterFactoryNew`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterExportBlueprintLibrary.h`:184 — `UMetaHumanCharacterExportBlueprintLibrary`.
- `MetaHumanCharacterEditor/Public/MetaHumanCharacterEditorActor.h`:22 — `AMetaHumanCharacterEditorActor`.
- `MetaHumanCharacterPalette/Public/MetaHumanCollection.h`:71 — `UMetaHumanCollection`.
- `MetaHumanCharacterPalette/Public/MetaHumanInstance.h`:133 — `UMetaHumanInstance`.
- `MetaHumanCharacterPalette/Public/MetaHumanWardrobeItem.h`:14 — `UMetaHumanWardrobeItem`.
- `MetaHumanCharacterPalette/Public/MetaHumanPaletteItemKey.h`:15 — `FMetaHumanPaletteItemKey`.
- `MetaHumanCharacterPalette/Public/MetaHumanCollectionBlueprintLibrary.h`:372 — `UMetaHumanCollectionBlueprintLibrary`.
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
- [references/custom-wardrobe-content.md](references/custom-wardrobe-content.md) — project
  wardrobe items: `WardrobePaths`, slot classes, item pipelines and validation, custom grooms
  on `SKM_Groom_Head_Legacy02`, preview collection, groom parameters, Chaos outfit refit.

After the build (packaged and web targets, face AnimBP, groom LOD holes, cook size, wardrobe for
close-ups): `ue-metahuman-runtime`.

Related skills: `ue-control-rig-and-ik`, `ue-animation-system`, `ue-hair-and-grooms` (groom
authoring, Alembic import, bindings, custom grooms as Creator hair).
