# Placed and water-linked weather effects

Read this reference only when the task uses placed helper actors/components, UDS water-level integration, or the built-in weather display widget. Material graph and camera effects remain in the parent skill.

## Puddle Fluid Volume

Renders a puddle as an actual water surface that moves up/down as the puddle fills/empties with weather. Use when there's a real geometric recess for water to fill.

In `Blueprints/Weather_Effects/`.

Optional **Puddle Fluid Interactions** renders the puddle as a dense grid mesh simulating natural ripples from DLWE Interaction components contacting the surface. Cost scales significantly with size — keep small.

Placement notes:

| Detail | Reason |
| --- | --- |
| Editor preview state comes from currently selected weather on UDW | Override via **Level Editor Preview State** |
| Place so the puddle is fully hidden under ground when dry | Mesh visible in editor when dry (helps placement); hidden at runtime when dry |
| Scale via `Puddle Area` or actor scaling; only Z-axis rotation supported | Geometry constraint |
| Translucent water surface by default | Enable **High Quality Translucency Reflections** in project settings for good Lumen reflections |

Categories: **Puddle State** (when/how filled/emptied), **Fluid Interactions** (DLWE interaction behavior toggles).

## Dripping Mesh Particles

Niagara systems that make a mesh spawn drip particles on its surface in response to rain / material wetness. In `Particles/Standalone/`.

| Mesh type | System | Setup |
| --- | --- | --- |
| Static mesh | **Dripping Static Mesh** | Add Niagara component as a child of the static mesh component |
| Skeletal mesh | **Dripping Skeletal Mesh** | Same with skeletal mesh component |

User parameters scale lifetime, max spawn rate, and the spawn rate fraction used when raining/wet/independent.

Drip appearance (sprite size, color, alpha) comes from UDW's rain particle settings.

If the actor has an **Actor Weather Status** component, the actor's local status drives the drip amount instead of global weather state. See `udw-setup-and-state`.

## Freezing Breath

Niagara system for visible character breath in cold air. Asset: **Freezing Breath** at `Particles/Standalone/`.

```
1. Add a Niagara component using Freezing Breath to your actor
2. Position + parent it in front of the mouth
3. Rotate so X axis points in direction of exhale
```

| State | Behavior |
| --- | --- |
| Default | Visible in freezing temperatures (UDW's calculated local temperature) |
| With Actor Weather Status component | Uses actor-local temperature instead |

## Rain Drip Spline and icicles

Actor in `Blueprints/Weather_Effects/` for spawning rain droplets along a line/curve — e.g. dripping from a building roof edge.

Drag in → small straight line. Edit the spline (move/rotate points; right-click to add) for length/shape.

Particle collision/appearance use UDW's rain particle settings.

**Optional icicle meshes** hanging from the spline render in cold weather.

## Weather Occlusion Volume

Volume texture caching how occluded each point around the camera is from weather/wind. Built by sampling the global distance field — requires distance fields enabled and supported.

Used by **Post Process Wind Fog** to mask intensity in spaces blocked by scenery.

## Water Level effects (UDW side)

The **Use UDS Water Level** option in UDW's **Water Level** category enables UDS water level for several UDW features. Actual water level config is on UDS — see `uds-modifiers-configs-state`.

What UDS water level affects on UDW:

- Weather particles kept out of below-water space
- Sound Occlusion fully occludes when camera goes below water
- Screen Droplets auto-off underwater; screen wet effect on resurface
- Rainbow masked beneath water level (when its option is on)
- Surface Weather Effects + DLWE functions have inputs to mask coverage below water

## Current Weather Display widget

**UDW_Current_Weather_Display** widget (widget designer → Ultra Dynamic Sky Widgets). Represents current weather as an icon by default, sourced via `Get Display Name for Current Weather`. Exposed settings switch to text display or read the current weather preset asset.

## Troubleshooting

- **Puddle mesh visible at runtime while dry** — the dry mesh is hidden automatically only when
  the puddle is fully below ground. Place the volume lower.
- **Puddle Fluid Interactions cost is excessive** — simulation cost scales with puddle area;
  restrict fluid interaction to small puddles.
- **Freezing Breath stays visible** — an Actor Weather Status component is supplying its local
  temperature. Tune or remove that local override rather than changing global weather.
- **Dripping Mesh Particles ignore global weather** — Actor Weather Status intentionally makes
  the drip system use actor-local state. Remove it when the effect should follow global state.

## Completion check

The selected effect is complete only when its weather driver, placement or material dependency, local-vs-global state source, and relevant cost or masking constraint are all accounted for. Vendor sources and asset paths are indexed in the parent skill's **References & source material** section.
