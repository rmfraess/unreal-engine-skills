# CharacterMovementComponent to Mover migration

Use this mapping only after selecting Mover and its backend. Mover does not expose mutable velocity or a single movement-mode enum; translate CMC concepts into shared settings, named modes, effects, layered moves, and replicated data collections.

| CMC | Mover |
|-----|-------|
| `MaxWalkSpeed` | `UCommonLegacyMovementSettings::MaxSpeed` |
| `JumpZVelocity` | `UCommonLegacyMovementSettings::JumpUpwardsSpeed` |
| `SetMovementMode(MOVE_Flying)` | `QueueNextMode("Flying")` or input `SuggestedMovementMode` |
| `PhysCustom` + `CustomMovementMode` | custom `UBaseMovementMode` registered under its own name |
| `LaunchCharacter` | `FApplyVelocityEffect` / `FLayeredMove_LinearVelocity` |
| `SetActorLocation` / teleport | `FTeleportEffect` |
| Root motion montage | `FLayeredMove_AnimRootMotion` |
| `FSavedMove_Character` custom flags | custom `FMoverDataStructBase` in the input command collection |
| `bOrientRotationToMovement` | author `OrientationIntent` in `ProduceInput` |
| `IsMovingOnGround()` | `IsOnGround()` / `Mover_IsOnGround` tag |
| `GetCharacterMovement()->Velocity = V` | queue an instant effect or layered move; direct mutation is unsupported |

## Migration check

Verify each translated feature under the selected backend, including authority/prediction behavior, rollback-sensitive state, mode transitions, root motion, and external teleports. A compile-only migration is incomplete.

## UE 5.8 source grounding

Paths are under `Engine/Plugins/Experimental/Mover/Source/Mover/Public/` unless noted:

- `MoverComponent.h` — `QueueLayeredMove:314`, `QueueInstantMovementEffect:394`,
  `QueueNextMode:414`, `GetVelocity:526`, `IsOnGround`/state query support.
- `MoverTypes.h` — `FMoverDataStructBase:203` and movement-state data collections.
- `DefaultMovementSet/Settings/CommonLegacyMovementSettings.h` — shared speed and jump settings.
- `DefaultMovementSet/LayeredMoves/BasicLayeredMoves.h` — velocity and root-motion layered moves.
- `DefaultMovementSet/InstantMovementEffects/BasicInstantMovementEffects.h` — teleport and
  velocity instant effects.
- [Comparing Mover and Character Movement Component](https://dev.epicgames.com/documentation/unreal-engine/comparing-mover-and-character-movement-component-in-unreal-engine).