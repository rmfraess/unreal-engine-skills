# StateTree for AI — deep dive

Deep dive for [../SKILL.md](../SKILL.md): C++ tasks, schema,
`UStateTreeAIComponent`, events, and the BT-vs-StateTree decision guide.
Grounded in UE 5.8 (`Engine/Plugins/Runtime/StateTree/` and
`Engine/Plugins/Runtime/GameplayStateTree/`).

## StateTree for AI

StateTree (`Plugins/Runtime/StateTree`, `Plugins/Runtime/GameplayStateTree`) is a
hierarchical state machine where states contain tasks and transitions, and selector states
mirror BT composites. It is data-oriented: task state lives in typed structs, not UObjects.

### Concepts

| Concept | Analog in BT | Notes |
|---|---|---|
| **State** | Branch/composite | Can contain tasks and sub-states |
| **Selector State** | Selector/Sequence composite | Iterates child states; enters the first whose conditions pass |
| **Task** | Task node | C++ struct implementing `FStateTreeTaskBase` |
| **Evaluator** | Service | Runs periodically on the active branch to supply data |
| **Condition** | Decorator | Guards state transitions |
| **Transition** | Decorator abort | Explicit when/event-based state change |

### UStateTreeAIComponent

Declared at
`Plugins/Runtime/GameplayStateTree/Source/GameplayStateTreeModule/Public/Components/StateTreeAIComponent.h`:16.
Subclasses `UStateTreeComponent`, which is a `UBrainComponent` — the same interface that
`UBehaviorTreeComponent` implements. Adding it to an `AAIController` replaces the BT brain
with a StateTree brain.

Setup in `AMyAIController` constructor:
```cpp
StateTreeComp = CreateDefaultSubobject<UStateTreeAIComponent>(TEXT("StateTreeComp"));
```

Assign a `UStateTree` asset:
```cpp
UPROPERTY(EditDefaultsOnly, Category="AI")
TObjectPtr<UStateTree> StateTreeAsset;

// In OnPossess:
StateTreeComp->SetStateTree(StateTreeAsset);
StateTreeComp->StartLogic();   // UBrainComponent::StartLogic — StateTreeComponent.h:54
```

### Authoring C++ StateTree tasks

StateTree tasks are plain C++ structs that implement `FStateTreeTaskBase` from
`StateTreeModule/Public/StateTreeTaskBase.h` (or `FStateTreeAITask` from the GameplayStateTree
module for tasks needing AI-specific context):

```cpp
USTRUCT()
struct FMyChaseTask : public FStateTreeTaskBase
{
    GENERATED_BODY()

    // Instance data (bound to the StateTree's schema-provided context):
    UPROPERTY(EditAnywhere, Category=Parameter)
    float AcceptanceRadius = 50.f;

    EStateTreeRunStatus EnterState(FStateTreeExecutionContext& Context,
        const FStateTreeTransitionResult& Transition) const;

    EStateTreeRunStatus Tick(FStateTreeExecutionContext& Context,
        const float DeltaTime) const;
};
```

`EStateTreeRunStatus` mirrors BT's `EBTNodeResult`: return `Running` (continue ticking),
`Succeeded`, or `Failed`. No `NodeMemory` pointer — instance data lives in the struct fields
(each state instance gets its own copy).

### Schema

A `UStateTree` asset has a **schema** that defines what external objects are accessible in
tasks and evaluators (e.g. the `AAIController`, `APawn`, `UBlackboardComponent`). The schema
validates that a task's context bindings are satisfied at edit time.

`UStateTreeAIComponentSchema` (declared in
`Plugins/Runtime/GameplayStateTree/Source/GameplayStateTreeModule/Public/Components/StateTreeAIComponentSchema.h`)
provides
`AAIController` and owned `APawn` to tasks automatically.

### Sending events to StateTree

StateTree transitions can be triggered by gameplay events:
```cpp
FStateTreeEvent Event;
Event.Tag = FGameplayTag::RequestGameplayTag(TEXT("AI.Event.TargetLost"));
StateTreeComp->SendStateTreeEvent(Event); // UStateTreeComponent API
```

### BT vs StateTree — decision guide

| Situation | Prefer |
|---|---|
| Existing large BT codebase | Keep BT; migrate incrementally |
| New project targeting UE 5.4+ | StateTree |
| Shared logic between AI and non-AI objects (e.g. doors, pickups) | StateTree (general schema) |
| Many simple AI with shared tree assets | BT (non-instanced nodes; memory-efficient) |
| Complex explicit state transitions with events | StateTree |
| Tight integration with Mass Entity (city-scale AI) | StateTree + MassEntity |

The two systems can coexist: some controllers use BT, others use StateTree. There is no
engine-level restriction.

## Version notes

- `UStateTreeAIComponent` was finalized in UE 5.4. In UE 5.3, use `UStateTreeComponent`
  with a manually-set `UStateTreeAIComponentSchema`.
- StateTree task structs do not need `UCLASS` — they use `USTRUCT`. This is intentional:
  the struct-based model avoids UObject overhead for large agent counts.
