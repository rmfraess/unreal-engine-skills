# Hermes routing matrix

Use this matrix after changing skill descriptions or exposing a new category through
`skills.external_dirs`. Start each prompt in a fresh session so prior package context does not
leak into routing.

## Acceptance rule

- Positive cases load the expected package skill and no unrelated package skill.
- Negative twins do not load any `uds-*` or `udw-*` skill.
- Multi-skill activation is acceptable only when the prompt explicitly spans both domains.
- The package-qualified trigger confirms package context and remains complete within the first
  57 description characters.

## Ultra Dynamic Sky

| Prompt | Expected |
|---|---|
| "This project uses Ultra Dynamic Sky. Tune volumetric cloud coverage and wisps." | `uds-clouds` |
| "Tune the native VolumetricCloud component coverage and material." | No `uds-*` skill; use native rendering/material guidance |
| "In Ultra Dynamic Sky, keyframe time of day for a Movie Render Queue shot." | `uds-cinematics-rendering`; `uds-time` only if runtime time behavior is also requested |
| "Build a native Unreal day-night clock." | No `uds-*` skill |
| "Ultra Dynamic Sky is installed and mobile clouds are too expensive." | `uds-performance-mobile-troubleshooting` |
| "Our native Unreal mobile scene is GPU-bound." | No `uds-*` skill |
| "Set Ultra Dynamic Sky latitude, date, and time zone for astronomical sun position." | `uds-simulation` |
| "Rotate a Directional Light from latitude and date without marketplace plugins." | No `uds-*` skill |

## Native Unreal lighting

| Prompt | Expected |
|---|---|
| "Configure Stationary lights and baked Lightmass for this interior." | `lighting-and-lumen`; no marketplace skill |
| "Choose light mobility and reflection captures without Lumen." | `lighting-and-lumen`; no marketplace skill |

## Ultra Dynamic Weather

| Prompt | Expected |
|---|---|
| "Ultra Dynamic Weather is installed. Add random seasonal temperature variation." | `udw-random-seasons-temperature` |
| "Add seasons and temperature to our custom gameplay system." | No `udw-*` skill |
| "Localize an Ultra Dynamic Weather storm with an override volume." | `udw-spatial-weather` |
| "Spawn a local Niagara rain volume." | No `udw-*` skill; use Niagara/native weather guidance |
| "Configure Ultra Dynamic Weather rain, wind, lightning, and environment sounds." | `udw-particles-lightning-wind-sounds` |
| "Add rain audio and lightning to a native Unreal level." | No `udw-*` skill |
| "Make Ultra Dynamic Weather wetness drive glass drips and puddles." | `udw-material-and-screen-effects` |
| "Author a generic wet material and post-process droplets." | No `udw-*` skill; use material/post-process guidance |

## Cross-package cases

| Prompt | Expected |
|---|---|
| "The project uses UDS and UDW. Save sky time plus active weather and restore both." | `uds-modifiers-configs-state` + `udw-setup-and-state` |
| "Set up Ultra Dynamic Sky and Ultra Dynamic Weather from a clean level." | `uds-setup-and-modes` + `udw-setup-and-state` |
| "Build clouds, rain, and a day-night cycle using only native Unreal systems." | No marketplace skills |
