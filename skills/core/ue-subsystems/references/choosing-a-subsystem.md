# Choosing a subsystem — decision guide

Deep dive for [../SKILL.md](../SKILL.md). Covers when to use each subsystem type vs
alternatives, networking constraints, and plugin patterns. Grounded in UE 5.8 subsystem
framework and related systems (`ue-gameplay-framework`, `ue-networking-and-replication`).

## The core question: what is the lifetime of the data?

Before picking a subsystem type, answer these two questions:

1. **When does this data become invalid / should it reset?**
   - Reset every level load → `UWorldSubsystem`
   - Persist across level loads, reset per game session → `UGameInstanceSubsystem`
   - Persist for the entire process → `UEngineSubsystem`
   - Belongs to one player → `ULocalPlayerSubsystem`

2. **Does this data need to be replicated to other machines?**
   - Yes → put it on `AGameState`, `APlayerState`, or a replicated actor; subsystems are local-only.

## Decision table

| Scenario | Recommended |
|---|---|
| Save data, cross-level progression, match-session state | `UGameInstanceSubsystem` |
| Per-level AI, event coordination, physics callbacks | `UWorldSubsystem` |
| Per-level periodic logic, frame-time budget tracking | `UTickableWorldSubsystem` |
| Per-player input profiles, per-player UI state | `ULocalPlayerSubsystem` |
| Plugin-provided process-wide service, cross-PIE-session state | `UEngineSubsystem` |
| Editor tooling, asset pipeline | `UEditorSubsystem` |
| Replicated game rules, authoritative score | `AGameState` / `APlayerState` |
| Behavior tied to a specific placed world object | Manager actor (placed in level) |
| Reusable per-actor behavior | `UActorComponent` on the actor |
| Stateless helpers | Free functions or `UBlueprintFunctionLibrary` |

## Subsystem vs GameInstance override

Overriding `UGameInstance` gives you the same lifetime as `UGameInstanceSubsystem`, but with
drawbacks:
- A project can override `UGameInstance` once; plugins cannot supply their own `UGameInstance`
  subclass. A `UGameInstanceSubsystem` from a plugin simply works without conflict.
- Each feature in a `UGameInstance` subclass adds to an already large class surface area,
  making it harder to maintain.

The subsystem pattern is the preferred replacement for "put everything in `UGameInstance`."

## Subsystem vs manager actor

A manager actor placed in the level has some advantages subsystems lack:
- It can be configured per-level from the editor (properties set in the level).
- It participates in actor replication.
- It receives `Tick` automatically without inheriting `UTickableWorldSubsystem`.

A subsystem is better when:
- The service is always needed (a placed actor can be accidentally deleted).
- You want guaranteed initialization order (subsystem dependencies).
- The service must not be visible in Outliner / selectable by designers.
- The service needs to survive level streaming without being placed in a persistent level.

Practical rule: **prefer subsystems for invisible infrastructure; prefer actors for content
that designers configure per level**.

## Subsystem vs component

An `UActorComponent` is the right abstraction for per-actor behavior. A subsystem is the right
abstraction for a service that many actors query. If multiple actors would each hold the same
component just to call `GetSubsystem<T>()` indirectly, eliminate the component and have them
call the subsystem directly.

## Networking constraints

Subsystems are local. They run on the machine that owns the outer object:
- `UGameInstanceSubsystem` exists on both server and client (each creates its own instance).
- `UWorldSubsystem` exists on server and client separately.
- `ULocalPlayerSubsystem` only exists on the client (or listen server for the hosting player).

There is no built-in RPC mechanism for subsystems. To drive server-side behavior, use RPCs on
an actor or `AGameMode` / `AGameState`. Call the subsystem on the server side from those RPCs.

Pattern:
```
Client UMyGameInstanceSubsystem::RequestAction()
    → calls RPC on PlayerController
    → server PlayerController calls server-side UMyGameInstanceSubsystem::ExecuteAction()
```

## Plugin patterns

### Using a UEngineSubsystem for plugin initialization

```cpp
// In your plugin module:
void FMyPlugin::StartupModule()
{
    // No manual subsystem setup needed — it is created by the engine after StartupModule returns.
}

// In the subsystem:
void UMyPluginSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    // Register asset type actions, start background threads, etc.
}
void UMyPluginSubsystem::Deinitialize()
{
    // Unregister, shut down threads.
    Super::Deinitialize();
}
```

This eliminates the pattern of `StartupModule` manually managing service lifetime.

### Conditional creation and server work in a world subsystem

Make the owner explicit: this `UWorldSubsystem` supports only Game/PIE worlds and accepts
standalone, listen-server, and dedicated-server net modes. It excludes editor/preview worlds
and worlds currently reporting client mode. The creation check uses `Outer`, not the CDO's
`GetWorld()` or a process-level server flag; each PIE world has its own network role.

```cpp
// MySubsystem.h
#pragma once
#include "Subsystems/WorldSubsystem.h"
#include "Engine/World.h"
#include "MySubsystem.generated.h"

UCLASS()
class MYGAME_API UMySubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override
    {
        const UWorld* World = Cast<UWorld>(Outer);
        return World && Super::ShouldCreateSubsystem(Outer)
            && World->GetNetMode() < NM_Client;
    }

    virtual void OnWorldBeginPlay(UWorld& InWorld) override
    {
        Super::OnWorldBeginPlay(InWorld);
        if (InWorld.GetNetMode() < NM_Client)
        {
            // Start authoritative gameplay work here; client worlds do no server work.
        }
    }

protected:
    virtual bool DoesSupportWorldType(const EWorldType::Type WorldType) const override
    {
        return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
    }
};
```

`ENetMode` orders the three server-capable modes before `NM_Client`, so the comparison includes
standalone play. Creation observes the world's **current** net mode; network setup or later
changes can affect that mode. Recheck before starting authoritative work and guard later
server-only entry points too. Keep cleanup safe when no work was started.

If a workflow cannot establish the intended network role at creation, use world-type-only
creation and defer the authority gate to gameplay readiness instead. This example is not a
guarantee that an early-created instance cannot remain after its world changes to client mode.

`ShouldCreateSubsystem` is called on the CDO with the **outer object** (the owning
`UGameInstance`, `UWorld`, etc.) as the argument. You can inspect the outer to make decisions,
but you cannot call `GetSubsystem` on it during this call — other subsystems may not yet be
created.

Source evidence:
- `Engine/Source/Runtime/Engine/Public/Subsystems/WorldSubsystem.h` — callback and filter signatures.
- `Engine/Source/Runtime/Engine/Private/Subsystems/WorldSubsystem.cpp` —
  `ShouldCreateSubsystem` forwards the outer world's type to `DoesSupportWorldType`;
  the base `OnWorldBeginPlay` maintains lifecycle state.
- `Engine/Source/Runtime/Engine/Classes/Engine/EngineBaseTypes.h` — `ENetMode` ordering.
- `Engine/Source/Runtime/Engine/Classes/Engine/EngineTypes.h` — `EWorldType` values.
- `Engine/Source/Runtime/Engine/Classes/Engine/World.h` and
  `Engine/Source/Runtime/Engine/Private/World.cpp` — per-world net mode and begin-play dispatch.

The replaced null-context predicate was not a world-authority filter:
`Engine/Source/Runtime/Engine/Private/KismetSystemLibrary.cpp` implements
`UKismetSystemLibrary::IsServer`; `Engine/Source/Runtime/Engine/Private/UnrealEngine.cpp`
handles null world contexts in `UEngine::GetWorldFromContextObject`.

## Version notes

- World subsystem `DoesSupportWorldType` (added alongside `UWorldSubsystem`) is the cleanest
  way to exclude a subsystem from editor preview worlds — prefer it over `ShouldCreateSubsystem`
  for world-type gating. `ShouldCreateSubsystem` is evaluated on the CDO for each candidate
  owner, and the world-subsystem base calls `DoesSupportWorldType` for that world.
- Dynamic subsystems (`UEngineSubsystem`, `UEditorSubsystem`) support late module loading; if
  your plugin is loaded after engine init, the subsystem is still created correctly.
