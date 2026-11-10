---
name: ue-master-material-authoring
description: Design reusable Unreal Engine 5.8 master materials and material instances. Use for PBR texture controls, material functions, UV options, static switches, channel-packed masks, or maintaining a family of related materials.
metadata:
  engine-version: "5.8"
  category: content-assets
---

# Master material authoring

Use `ue-materials-and-shaders` for the underlying material and instance APIs. Build a master only when several assets share the same shading model and meaningful controls. A material instance should expose useful artistic variation without turning every graph branch into a parameter. Use project textures or procedural values; no specific texture set, packing convention, or source application is required.

## Structure and parameters

Start with the common PBR inputs, then group related controls in small material functions when the same logic recurs. Give parameters names and groups that reveal what the instance artist changes: base color tint, UV scale, normal intensity, roughness range, and optional mask sources are examples. Keep defaults visually valid when a texture is absent. Distinguish global UV controls from per-texture scale or offset; forcing every texture to share one UV transform can break packed masks or detail normals.

Use scalar, vector, and texture parameters for values that change among instances. Use a Static Switch Parameter only for a feature whose compiled shader path should differ, such as enabling an optional normal-map branch. Every independent switch can multiply shader permutations; avoid a switch for each minor artistic adjustment. Evaluate instruction count and compilation cost across the combinations actually used.

## Texture data contracts

- Treat base color as color data, while roughness, metalness, ambient occlusion, height, and packed masks are linear data. Verify texture import, sRGB, compression, and sample type rather than correcting a bad input with arbitrary graph math.
- Normal maps need normal-map compression and sampling compatible with the chosen texture. Blend or adjust normals using normal-aware functions; naïvely scaling RGB can destroy a valid normal.
- For channel-packed textures, write down the channel mapping at the sample: for example, which channel supplies AO, roughness, or metalness. Use Component Mask to route scalar channels and do not assume every pack follows the same convention. Packing reduces texture fetch and memory overhead only when it matches actual asset use.
- Expose roughness and metalness ranges where useful. Leave Specular near the physically based default unless the material calls for a deliberate dielectric adjustment; avoid using it as a substitute for roughness.

Diagnose the missing visual cue before adding depth features: fine grain and surface response need suitable base-colour/normal/roughness data, recesses may benefit from height shading, and an incorrect outline or missing bundle volume needs geometry. POM cannot recover detail absent from a soft or mis-scaled source texture. Preserve already accepted materials while trialing corrections to the rejected surface.

Displacement needs a specific geometry and platform plan. World Position Offset moves existing vertices and needs sufficient geometry and bounds; other displacement or tessellation paths vary with project renderer and UE version. Choose the supported path for the target rather than treating a height texture as automatic geometric detail.

**Surface depth (POM vs Nanite displacement), UE 5.8:**
1. First confirm every blended layer has a real height texture. Scanned surfaces often ship colour/normal/ORM only (e.g. Megascans Medium tier); a height map then needs a higher-tier re-import, which is an import needing approval. Faking height from AO is a cavity proxy, not a height map.
2. Compare POM with geometry-supported displacement at the actual viewing angles. POM changes apparent depth within a surface, not its geometric outline or collision, and can step or flatten at grazing angles while adding work per blended layer. Use real geometry for visible cut edges or bundle volume; treat small wall/decal relief as a POM candidate rather than a blanket requirement. Verify Pixel Depth Offset, contact-shadow, Lumen and VSM behavior in the target renderer instead of claiming either universal shadow support or none. Neither POM nor shader displacement by itself proves updated collision or correct prop seating.
3. Nanite displacement in 5.8 is a material feature (`Material.h`: `bEnableTessellation`, `DisplacementScaling`, Displacement Fade) with runtime tessellation on by default (`r.Nanite.Tessellation`, `NaniteCullRaster.cpp`). Landscapes need Nanite enabled on the proxy and can drop displacement per distant cluster (`r.Landscape.AllowNanitePerClusterDisplacementDisable`, `LandscapeRender.cpp`). Verify the target landscape's Nanite state live before planning; cite engine source, not memory.
4. Trial on an Evaluation-local material copy, A/B on fixed review cameras, and measure GPU ms against a same-session baseline; displacement cost is scene-specific.

## Data-driven masks and scripted masters

- Measure a texture before gating a mask on its colour. A surface named "mossy" or "grassy" may be brown overall, so a green-dominance test passes almost no pixels. Export the texture with `unreal.AssetExportTask` to TGA. Then compute channel percentiles and ratios in linear space with numpy (decode sRGB first) and set the thresholds from that data.
- To see whether a mask fires and where, temporarily set its tint to an extreme colour, such as linear (20,0,0), on the live instances and capture the view. Faint uniform coverage means the gate is too weak; no change means the branch is not wired. Restore the values afterwards.
- A scripted master can be rebuilt whole (`delete_all_material_expressions`, then recreate), and instances keep their overrides by parameter name. Because overrides persist, a changed default never shows on an instance that already overrides it. Call `clear_all_material_instance_parameters` in the instance script before setting that instance's own values.
- After a master rebuild, judge parameter state from a render capture. The instance getter may still report the old default.
- To dress shared vendor meshes, prefer a project-local master that takes each mesh's own colour/normal/ORM as texture parameters, with one instance per mesh. Apply the instances as overrides so vendor assets stay untouched.

## Review

Create a few representative instances from the master: one with only defaults, one with all intended optional features, and one with the most different texture set. Check shader compilation, visual output, texture streaming, and whether the instance interface makes invalid combinations too easy. Split a master when unrelated feature families make it hard to understand or expensive to compile.

## References & source material

- UE 5.8 source: `Engine/Source/Runtime/Engine/Public/Materials/Material.h` (`UMaterial`).
- UE 5.8 source: `Engine/Source/Runtime/Engine/Public/Materials/MaterialInstance.h` (`UMaterialInstance`).
- UE 5.8 source: `Engine/Source/Runtime/Engine/Public/Materials/MaterialFunction.h` (`UMaterialFunction`).
- UE 5.8 source: `Engine/Source/Runtime/Engine/Public/Materials/MaterialExpressionStaticSwitchParameter.h` (`UMaterialExpressionStaticSwitchParameter`).
- UE 5.8 source: `Engine/Source/Runtime/Engine/Public/Materials/MaterialExpressionComponentMask.h` (`UMaterialExpressionComponentMask`).
