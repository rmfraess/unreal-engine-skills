---
name: ue-lighting-and-lumen
description: >-
  Configure Unreal lighting in C++: UDirectionalLightComponent,
  UPointLightComponent, USpotLightComponent, URectLightComponent,
  USkyLightComponent; Static/Stationary/Movable mobility and GI, baking,
  and runtime cost; Lumen GI/reflections, quality settings, software/hardware
  ray tracing; Virtual Shadow Maps; USkyAtmosphereComponent and
  UExponentialHeightFogComponent; Post Process Volumes for exposure/auto-exposure
  and Lumen overrides; reflection captures. Use when creating/configuring lights,
  choosing mobility, enabling/troubleshooting Lumen, setting up sky/fog/atmosphere,
  tuning exposure/color grading, placing reflection captures, or choosing baked
  Lightmass vs dynamic lighting.
metadata:
  engine-version: "5.8"
  category: world-building
---

# Lighting & Lumen

UE5's default lighting pipeline is **fully dynamic**: Lumen provides global illumination
(GI) and reflections without a bake. Understanding the light component hierarchy,
mobility rules, and the Lumen/post-process stack lets you get correct and performant
results quickly.

## When to use this skill

- Creating or modifying a light component in C++ (type selection, intensity/color/units,
  attenuation, IES profiles, light functions).
- Choosing the right mobility for a light and understanding the GI/shadow consequences.
- Enabling, tuning, or debugging Lumen GI and Lumen Reflections.
- Setting up sky atmosphere, sky light, volumetric clouds, and exponential height fog.
- Configuring post process volumes for exposure, auto-exposure, bloom, color grading,
  or per-area Lumen overrides.
- Placing reflection captures for areas Lumen cannot reach (legacy or spec-heavy interiors).
- Deciding when to use baked Lightmass vs Lumen.

## Light component hierarchy

All light components derive from `USceneComponent` through the following chain:

```
USceneComponent
└─ ULightComponentBase        (LightComponentBase.h:15) — Intensity, LightColor, CastShadows
   ├─ ULightComponent         (LightComponent.h:48)     — Temperature, ShadowBias, IES, LightFunction
   │  ├─ ULocalLightComponent (LocalLightComponent.h:18) — AttenuationRadius, IntensityUnits
   │  │  ├─ UPointLightComponent (PointLightComponent.h:19) — SourceRadius, SourceLength
   │  │  │  └─ USpotLightComponent (SpotLightComponent.h:17) — InnerConeAngle, OuterConeAngle
   │  │  └─ URectLightComponent  (RectLightComponent.h:24) — SourceWidth, SourceHeight, BarnDoorAngle
   │  └─ UDirectionalLightComponent (DirectionalLightComponent.h:18) — DynamicShadowCascades, bAtmosphereSunLight
   └─ USkyLightComponent      (SkyLightComponent.h:101)  — bRealTimeCapture, SourceType, Cubemap
```

See [references/light-components-and-mobility.md](references/light-components-and-mobility.md)
for C++ patterns and per-type properties.

## Light types at a glance

| Component | Shape | Use for |
|---|---|---|
| `UDirectionalLightComponent` | infinite parallel rays | sun, moon, any directional source |
| `UPointLightComponent` | sphere/capsule omnidirectional | light bulbs, candles, explosions |
| `USpotLightComponent` : Point | cone | torches, headlights, stage spots |
| `URectLightComponent` | planar rectangle | TVs, windows, fluorescent strips |
| `USkyLightComponent` | cubemap capture | ambient IBL, sky bounce |

## Mobility and its lighting consequences

Mobility is set on the component via `SetMobility(EComponentMobility::Movable)`.

| Mobility | Direct light | Indirect light | Shadows | Runtime change |
|---|---|---|---|---|
| **Static** | baked into lightmaps | baked | baked | none |
| **Stationary** | dynamic direct, baked indirect | baked (Lightmass) | mixed (baked static, dynamic movable) | color/intensity only |
| **Movable** | fully dynamic | Lumen GI (no bake) | Virtual Shadow Maps | all properties |

Key rule for Lumen: **only Movable lights feed Lumen GI**. Static lights are entirely
stored in lightmaps and their contribution is disabled when Lumen is enabled.
Stationary lights contribute baked indirect; their direct pass is dynamic.

Stationary limit: a single primitive can overlap at most **four** Stationary lights
before the fifth reverts to fully dynamic (expensive). The editor shows this with a red
channel-limit indicator.

## Lumen (dynamic GI + reflections)

Lumen is the default GI system for new UE5 projects. It computes diffuse interreflection
and specular reflections in real time, across scales from millimeters to kilometers.

**Enabling:** Project Settings → Rendering → Dynamic Global Illumination: **Lumen**;
Reflection Method: **Lumen**. Enabling Lumen automatically enables Generate Mesh
Distance Fields (required for software ray tracing) and disables precomputed lightmaps.

**Two tracing modes:**
- **Software Ray Tracing** — traces against Signed Distance Fields; works on all
  DX11+ hardware; requires `Generate Mesh Distance Fields` in project settings.
- **Hardware Ray Tracing (HRT)** — uses the GPU BVH; higher quality reflections and
  hit-lighting; enabled in Project Settings → Rendering → Hardware Ray Tracing.

Quality is tuned per-camera in a `APostProcessVolume` via `FPostProcessSettings`
fields (all in `Engine/Classes/Engine/Scene.h`):

| `FPostProcessSettings` field | Purpose |
|---|---|
| `LumenSceneLightingQuality` (line 1783) | fidelity of the Lumen scene cache |
| `LumenFinalGatherQuality` (line 1799) | noise vs cost of the final gather pass |
| `LumenMaxTraceDistance` (line 1811) | max ray length; too small leaks GI into caves |
| `LumenReflectionQuality` (line 1846) | reflection ray quality |

See [references/lumen-gi-and-reflections.md](references/lumen-gi-and-reflections.md)
for the full Lumen settings table, emissive GI, and hardware ray tracing notes.

## Virtual Shadow Maps (VSMs)

VSMs are the default shadow technology for Movable and Stationary lights when Lumen
is active. They render into a virtualized (sparse) 16k×16k shadow atlas, support
Nanite geometry natively, and require no per-light manual distance tuning.

Enable via Project Settings → Rendering → Shadows → Shadow Map Method: **Virtual
Shadow Maps**. The CVars `r.Shadow.Virtual.*` control quality and cache behaviour.

Key shadow properties on `ULightComponent` (`LightComponent.h`):
- `ShadowBias` (line 113) / `ShadowSlopeBias` (line 123) — self-shadow acne
- `ContactShadowLength` (line 131) — screen-space contact shadow ray length
- `CastShadows` / `CastDynamicShadows` / `CastStaticShadows` — per-channel toggle

For `UDirectionalLightComponent`, cascaded shadow maps are set with
`DynamicShadowCascades` (line 73) and `DynamicShadowDistanceMovableLight` (line 59).

See [references/shadows-and-postprocess.md](references/shadows-and-postprocess.md).

## Sky, atmosphere, and fog

A complete outdoor sky in C++ uses three cooperating actors/components:

1. `UDirectionalLightComponent` with `bAtmosphereSunLight = true` — drives the sky color.
2. `USkyAtmosphereComponent` (`Components/SkyAtmosphereComponent.h`) — physically-based
   atmosphere scattering.
3. `USkyLightComponent` with `bRealTimeCapture = true` — recaptures the rendered sky
   every tick for ambient/IBL.

Fog depth and god rays come from `UExponentialHeightFogComponent`
(`Components/ExponentialHeightFogComponent.h`). Enable volumetric fog on it for
`VolumetricFogScatteringDistribution` and `VolumetricFogAlbedo` to feed Lumen GI.

## Post Process Volume and exposure

`APostProcessVolume` (`Engine/PostProcessVolume.h`) hosts `FPostProcessSettings`
(`Engine/Scene.h:711`). Set `bUnbound = true` for a global volume; bounded volumes
blend by distance (Priority and BlendRadius fields).

Exposure settings in `FPostProcessSettings`:
- `AutoExposureMethod` (line 1491) — `AEM_Histogram` (default) or `AEM_Basic`
- `AutoExposureBias` (line 1933) — EV100 offset for all metering modes
- `AutoExposureMinBrightness` / `AutoExposureMaxBrightness` (lines 1994, 2002) —
  clamp the auto-exposure range (in EV100 or cd/m² depending on project setting)

For predictable results, prefer **manual exposure** over auto: set
`AutoExposureMethod` to `AEM_Manual` and fix the EV100 directly with `AutoExposureBias`.
Auto-exposure "breathes" as the camera pans, which reads as incorrect to players.

Color grading and tone curve live alongside exposure in the same struct; see
[references/shadows-and-postprocess.md](references/shadows-and-postprocess.md).

## Reflection captures (legacy / spec fill)

`UReflectionCaptureComponent` (`Components/ReflectionCaptureComponent.h:30`) and its
concrete subclasses (`USphereReflectionCaptureComponent`,
`UBoxReflectionCaptureComponent`) provide cubemap IBL for surfaces with low roughness
in areas where Lumen reflections have insufficient quality (e.g., enclosed interiors or
mobile targets). They are **not** updated at runtime by default; call
`MarkDirtyForRecaptureOrUpload()` to force a refresh.

With Lumen enabled, reflection captures are mostly replaced by Lumen Reflections for
Movable surfaces. They remain relevant for Static/Stationary geometry and as a fallback
for hardware that does not meet Lumen's requirements.

## C++ snippet — creating and configuring a light

```cpp
// In actor constructor:
#include "Components/PointLightComponent.h"

UPROPERTY(VisibleAnywhere)
TObjectPtr<UPointLightComponent> FillLight;

// Constructor body:
FillLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("FillLight"));
FillLight->SetupAttachment(RootComponent);
FillLight->SetIntensity(2000.f);           // lumens (with inverse-sq falloff)
FillLight->SetLightColor(FLinearColor(1.f, 0.95f, 0.8f));
FillLight->SetAttenuationRadius(600.f);
FillLight->CastShadows = true;
```

```cpp
// Runtime: change intensity and disable shadow casting
FillLight->SetIntensity(500.f);
FillLight->SetCastShadows(false);
```

Key APIs on `ULightComponent` (all `BlueprintCallable`):
- `SetIntensity(float)` — total output in the component's intensity units
- `SetLightColor(FLinearColor, bool bSRGB)` — filter tint
- `SetTemperature(float)` / `SetUseTemperature(bool)` — color temperature (Kelvin)
- `SetShadowBias(float)` / `SetShadowSlopeBias(float)` — self-shadow tuning
- `SetLightFunctionMaterial(UMaterialInterface*)` — project a material as a cookie

On `ULocalLightComponent`:
- `SetAttenuationRadius(float)` — bounding radius; affects tile-culling cost
- `SetIntensityUnits(ELightUnits)` — `Candelas`, `Lumens`, or `EV100`

## Gotchas

- **Static lights ignored by Lumen** — Lumen disables lightmap contributions; only
  Movable (and partially Stationary) lights drive dynamic GI.
- **Mesh distance fields off** — Lumen's software path silently degrades or produces
  black GI; enable in Project Settings → Rendering → Generate Mesh Distance Fields.
- **More than four overlapping Stationary lights** — fifth light degrades to Movable
  shadow cost; keep count per-area ≤ 4.
- **Auto-exposure surprise** — scenes look inconsistent as the camera moves; use
  manual exposure for cinematic or stylized work.
- **Milky mid-distance haze** — with volumetric fog enabled, `VolumetricFogExtinctionScale` usually drives the washed-out middle distance more than `FogDensity` does. Lowering density alone barely changes the view. Change one at a time and compare same-camera captures. For crisp air, drop extinction first (for example 0.6 → 0.2), then density.
- **Sun direction is the light's travel direction** — a `DirectionalLight`'s forward vector points where the light goes, so the sun sits at `-forward`. Map that to the project's world compass (which axis is north or east) before placing a sun by bearing, and print the forward vector to confirm.
- **Auto exposure normalises frame brightness** — with default auto exposure, neither scaling the sun nor darkening the albedo of a surface that fills much of the frame changes image brightness much, because metering re-targets the frame mean. Light trials change the sun-to-sky ratio, the colour and the shadow length; albedo trials change hue and contrast. Only exposure (bias, or a manual/clamped range) moves overall brightness. If a region stays too bright under every light and material trial, go to exposure.
- **Prove what a measured region contains** — before blaming a material for a region's brightness or colour, confirm that material actually covers the region: temporarily return a flat colour (e.g. red) from the suspect node and capture. A lower-frame crop of a road-side view is often mostly road, not the surface being tuned.
- **Default exposure bias is 1.0, not 0** — `FPostProcessSettings::AutoExposureBias` defaults to 1.0 in UE5 (`unreal.PostProcessSettings().auto_exposure_bias`). Overriding it to 0 is already −1 EV; quote trials relative to 1.0.
- **Exposure trial procedure** — add one unbound `PostProcessVolume` with only `override_auto_exposure_bias` set (read `settings`, set fields, assign the struct back). Capture the same fixed views and report, per view, full-frame mean luma, lower-frame mean luma and clipped-pixel % against the reference frames. Sunlit and shaded views respond differently (sky in frame drags a shaded view darker), so one bias is a trade-off: show both groups. To check whether short-settle captures had converged, run once with `auto_exposure_speed_up/down` overridden high, then remove those overrides before showing the real result. Present before/after and keep the volume unsaved until the user accepts.
- **A low sun turns golden** — at low elevation `SkyAtmosphere` transmittance warms the direct light. For a pale or cold low sun, enable `bUseTemperature` and raise `Temperature` (about 8,000–8,500 K) to offset it.
- **Systems that read the sun** — procedural placement that samples the directional light (shade or slope-aspect bias) goes stale when the sun moves. Regenerate it and re-measure after a sun change.
- **Volumetric clouds: stock material for the sky, trial in PIE** — configure sky clouds through a material instance of `m_SimpleVolumetricCloud_Inst` (parameter changes never recompile under the renderer), zero the x/y of `Layout_WindControls` because horizontal wind slides the whole layout, and judge only PIE or game captures, since one-shot Editor captures smear clouds. The stock material cannot shape summit-sized clouds: its world mask is added after the profile and noise (flat-sided boxes), and km-scale pattern features are erased or turn into columns, so a crest cap is custom-material work. A custom cloud material needs the Volume domain and `used_with_volumetric_cloud` set before it is ever assigned. Toggling that flag or recompiling while it is on a live cloud component crashed the renderer. Trial every cloud change on transient PIE actors first. Setup, mechanisms, graph reading and the PIE/cost recipe: [references/volumetric-clouds.md](references/volumetric-clouds.md).
- **Sky Light not recapturing** — with `bRealTimeCapture = false`, the sky light bakes
  once; call `RecaptureSky()` or set `bRealTimeCapture = true` when the sky changes.
- **VSM invalidation cost** — moving or spawning many Movable meshes near shadowed
  lights forces cache invalidation; pool or batch spawn off-screen when possible.
- **Rect lights and light functions** — `URectLightComponent` does not support
  `LightFunctionMaterial` (only Directional/Point/Spot do).
- **Lightmap UVs for baked lighting** — if you fall back to Lightmass, meshes must
  have a valid lightmap UV channel or shadows bake black.

## Version notes

- Lumen is the default GI system for new UE5 projects; existing UE4 projects converted
  to UE5 do not automatically enable it (avoids breaking baked workflows).
- MegaLights (`bAllowMegaLights` on `ULightComponent`, line 171) is a UE5.5+ feature
  for stochastic many-light rendering; present in 5.8 but still experimental.
- VSMs replaced the legacy Cascaded Shadow Map default for PC/console in UE5; mobile
  platforms still use traditional shadow maps.

## References & source material

Engine source (UE 5.8, under `Engine/Source/Runtime/Engine/Classes/`):
- `Components/LightComponentBase.h` — `ULightComponentBase`:15; `Intensity`:37,
  `LightColor`:44, `CastShadows`:58, `IndirectLightingIntensity`:116,
  `SetCastShadows()`:146, `GetLightColor()`:150.
- `Components/LightComponent.h` — `ULightComponent`:48; `Temperature`:57,
  `ShadowBias`:113, `ShadowSlopeBias`:123, `ContactShadowLength`:131,
  `bAllowMegaLights`:171, `LightFunctionMaterial`:205, `IESTexture`:219,
  `SetIntensity()`:286, `SetLightColor()`:296, `SetTemperature()`:303.
- `Components/LocalLightComponent.h` — `ULocalLightComponent`:18;
  `IntensityUnits`:28, `AttenuationRadius`:46, `SetAttenuationRadius()`:53.
- `Components/PointLightComponent.h` — `UPointLightComponent`:19;
  `SourceRadius`:45, `SourceLength`:59, `SetSourceRadius()`:71.
- `Components/SpotLightComponent.h` — `USpotLightComponent`:17;
  `InnerConeAngle`:23, `OuterConeAngle`:27.
- `Components/RectLightComponent.h` — `URectLightComponent`:24;
  `SourceWidth`:33, `SourceHeight`:40, `BarnDoorAngle`:46, `BarnDoorLength`:52.
- `Components/SkyLightComponent.h` — `USkyLightComponent`:101;
  `bRealTimeCapture`:108, `SourceType`:112, `RecaptureSky()`:304.
- `Components/DirectionalLightComponent.h` — `UDirectionalLightComponent`:18;
  `DynamicShadowDistanceMovableLight`:59, `DynamicShadowCascades`:73,
  `bAtmosphereSunLight`:164.
- `Components/ReflectionCaptureComponent.h` — `UReflectionCaptureComponent`:30.
- `Engine/PostProcessVolume.h` — `APostProcessVolume`:22; `bUnbound`:51.
- `Engine/Scene.h` — `FPostProcessSettings`:711; `AutoExposureMethod`:1491,
  `AutoExposureBias`:1933, `AutoExposureMinBrightness`:1994,
  `AutoExposureMaxBrightness`:2002, `LumenSceneLightingQuality`:1783,
  `LumenFinalGatherQuality`:1799, `LumenMaxTraceDistance`:1811,
  `LumenReflectionQuality`:1846.

Official docs (UE 5.8):
- Light Types and Their Mobility —
  <https://dev.epicgames.com/documentation/unreal-engine/light-types-and-their-mobility-in-unreal-engine>
- Lumen Global Illumination and Reflections —
  <https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine>
- Shadowing —
  <https://dev.epicgames.com/documentation/unreal-engine/shadowing-in-unreal-engine>
- Virtual Shadow Maps —
  <https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine>
- Post Process Effects —
  <https://dev.epicgames.com/documentation/unreal-engine/post-process-effects-in-unreal-engine>

Deep-dive references in this skill:
- [references/light-components-and-mobility.md](references/light-components-and-mobility.md) —
  per-type component properties, C++ authoring patterns, mobility decision guide.
- [references/lumen-gi-and-reflections.md](references/lumen-gi-and-reflections.md) —
  Lumen architecture, settings table, hardware vs software RT, emissive GI, sky integration.
- [references/shadows-and-postprocess.md](references/shadows-and-postprocess.md) —
  VSMs, CSMs, shadow bias, post process volume exposure, color grading, Lumen PPV overrides.
- [references/volumetric-clouds.md](references/volumetric-clouds.md) — stock sky cloud setup (layer,
  wind, judging captures), what the stock material cannot place and why, reading its graph, custom
  cloud material order, PIE trial and in-PIE cost A/B recipe.

Related skills: `ue-nanite-and-rendering`, `ue-materials-and-shaders`.
