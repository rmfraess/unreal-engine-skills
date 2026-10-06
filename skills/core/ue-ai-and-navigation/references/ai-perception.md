# AI Perception — deep dive

Deep dive for [../SKILL.md](../SKILL.md): senses, forget behavior,
`UAIPerceptionStimuliSourceComponent`, affiliation, queries, and debugging.
Grounded in UE 5.8 (`Engine/Source/Runtime/AIModule/Classes/Perception/`).

## AI Perception — all senses

The perception system uses **sense configs** (subclasses of `UAISenseConfig`) to define what
the AI can detect and with what parameters. Each config maps to a `UAISense` implementation.

### Sight (`UAISenseConfig_Sight`)

Declared at `Perception/AISenseConfig_Sight.h`:18. Key properties:

| Property | Effect |
|---|---|
| `SightRadius` | Max distance to detect a target not yet seen. |
| `LoseSightRadius` | Max distance before a previously-seen target is lost. Must be ≥ `SightRadius`. |
| `PeripheralVisionAngleDegrees` | Half-angle of the vision cone from the forward vector. |
| `DetectionByAffiliation` | Which affiliations (enemies, neutrals, friendlies) trigger sight. |
| `AutoSuccessRangeFromLastSeenLocation` | If > 0, targets already seen are auto-succeeded within this range of their last seen position. |
| `PointOfViewBackwardOffset` | Moves the cone origin backward — adds close-range peripheral awareness. |
| `NearClippingRadius` | Blind spot at the pawn's very feet (use with backward offset). |

`PeripheralVisionAngleDegrees` can be changed at runtime:
```cpp
UAISenseConfig_Sight* Cfg = Cast<UAISenseConfig_Sight>(
    PerceptionComp->GetSenseConfig(UAISense_Sight::StaticClass()));
if (Cfg) { Cfg->PeripheralVisionAngleDegrees = 90.f;
           PerceptionComp->RequestStimuliListenerUpdate(); } // line 326
```

For targets to be seen, they (or their owning actor) must have `UAIPerceptionStimuliSourceComponent`
registered for `UAISense_Sight`, OR they implement `IAISightTargetInterface`
(`Perception/AISightTargetInterface.h`) to provide a custom can-be-seen test.

### Hearing (`UAISenseConfig_Hearing`)

Senses `UAISense_Hearing` (`Perception/AISense_Hearing.h`). Hearing stimuli are generated
by calling `UAISense_Hearing::ReportNoiseEvent` (static) or `UAISenseBlueprintListener`:
```cpp
UAISense_Hearing::ReportNoiseEvent(
    GetWorld(), SoundLocation, /*Loudness*/ 1.0f, NoiseInstigator,
    /*MaxRange*/ 0.f,         // 0 = use hearing config's range
    /*Tag*/ NAME_None);
```

`MaxAge` on the config controls how long the stimulus is remembered before it is forgotten.

### Damage (`UAISenseConfig_Damage`)

Automatically receives stimuli when `UAISense_Damage::ReportDamageEvent` is called — or when
`AISense_Damage` intercepts UE's standard damage flow (configurable). Useful for AI that
reacts to being hit even when the attacker is outside sight range.

### Prediction, Team, Touch

- **Prediction** (`UAISenseConfig_Prediction`) — requests a predicted future location for a
  target. Used for lead-aim or interception logic.
- **Team** (`UAISenseConfig_Team`) — notifies the AI when a teammate is within a configurable
  radius broadcast by gameplay code.
- **Touch** (`UAISenseConfig_Touch`) — senses physical contact (pawn bumps into something or
  vice versa).

## Forget behavior

Stimuli age over time. When a stimulus exceeds `MaxAge` on its sense config without being
refreshed, it is forgotten. Set `MaxAge = 0` to never forget.

To reset all known percepts immediately:
```cpp
PerceptionComp->ForgetAll(); // AIPerceptionComponent.h:346
```

To forget a specific actor:
```cpp
PerceptionComp->ForgetActor(Actor);
```

Enable automatic forget in Project Settings → Engine → AI System: set **Forget Stale Actors**
to true. The system then purges actors whose last stimulus is older than the configured age.

## Querying currently perceived actors

```cpp
TArray<AActor*> VisibleActors;
PerceptionComp->GetCurrentlyPerceivedActors(
    UAISense_Sight::StaticClass(), VisibleActors);   // AIPerceptionComponent.h:372

TArray<AActor*> KnownActors;
PerceptionComp->GetKnownPerceivedActors(nullptr, KnownActors); // all senses
```

`GetCurrentlyPerceivedActors` returns only actors with an *active* (not expired) stimulus.
`GetKnownPerceivedActors` returns everything still in memory (not yet forgotten).

## UAIPerceptionStimuliSourceComponent

Add this component to actors the AI should be able to sense:
```cpp
// In the target actor's constructor:
StimuliSource = CreateDefaultSubobject<UAIPerceptionStimuliSourceComponent>(
    TEXT("StimuliSource"));
StimuliSource->bAutoRegisterAsSource = true;
StimuliSource->RegisterForSense(TSubclassOf<UAISense>(UAISense_Sight::StaticClass()));
```

Declared at `Perception/AIPerceptionStimuliSourceComponent.h`. Without this (or an
`IAISightTargetInterface` implementation), a `UAISense_Sight` will never detect the actor.

## Affiliation (team-based sensing)

Affiliation (enemy / neutral / friendly) maps through `IGenericTeamAgentInterface`
(`GenericTeamAgentInterface.h`). Implement on both the AI controller and the target actor.
The sense config's `DetectionByAffiliation` flags gate which team relationships trigger the
sense. In Blueprint-only projects (where C++ team assignment is impractical), set
`DetectNeutrals = true` and filter by tag in the perception callback.

## Debugging AI Perception

In PIE, press `'` (apostrophe) to open the AI Debugger, then press **Numpad 4** to show
Perception. Each active sense is drawn as a sphere or cone around the AI. The overlay shows
age and source for each known stimulus.

Use `VisLog` integration: `UAIPerceptionComponent` writes stimuli events to the Visual Logger
(`Gameplay Debugger` skill) if `ENABLE_VISUAL_LOG` is defined.

## Version notes

- `OnTargetPerceptionInfoUpdated` (richer `FActorPerceptionUpdateInfo` struct) was added in
  UE 5.1. Prefer it over `OnTargetPerceptionUpdated` for new code.
