# Finding APIs in the engine source

Deep-dive companion to [../SKILL.md](../SKILL.md). Grounded in UE 5.8 source under
the verified `<UE_ENGINE_ROOT>/Engine/Source`.

A repeatable, step-by-step playbook for locating any class, function, or type
without guessing. Examples use Hermes `search_files` and `read_file`.

---

## Workflow 1 — You know the class name

**Goal:** find `FGameplayTag`'s header, module, and real signature.

1. **Search for the header** — most UE types have a header named after them:
   ```
   search_files(target="files", pattern="*GameplayTagContainer.h",
                path="<UE_ENGINE_ROOT>/Engine/Source")
   ```
   Result: `Runtime\GameplayTags\Classes\GameplayTagContainer.h`.

2. **Search for the declaration** without reading the full file:
   ```
   search_files(target="content", pattern="struct FGameplayTag\b",
                path="<resolved GameplayTagContainer.h>")
   → line 41: struct FGameplayTag
   ```

3. **Identify the module** — the file lives under `Runtime\GameplayTags\`, so the
   module name is `GameplayTags`. Confirm: `Runtime\GameplayTags\GameplayTags.Build.cs`.

4. **Determine the `#include`** — the header is under `Classes\` (a public root), so:
   ```cpp
   #include "GameplayTagContainer.h"
   ```

5. **Add to Build.cs**:
   ```
   PrivateDependencyModuleNames.AddRange(new string[] { "GameplayTags" });
   ```

---

## Workflow 2 — You know a function name, not the file

**Goal:** find `SpawnActor` signature on `UWorld`.

1. **Search for the symbol** in the narrowest known source root:
   ```
   search_files(target="content", pattern="SpawnActor",
                path="<UE_ENGINE_ROOT>/Engine/Source/Runtime/Engine/Classes/Engine/World.h")
   ```
   Scan the output for the templated overload signature.

2. **Read a focused range** around the match using `read_file` with `offset`/`limit`. Do
   not read the full `World.h` (it exceeds 5,000 lines).

3. Note line numbers as approximate — they drift across patch releases. Cite the
   path + approximate line; reconfirm if the number matters.

---

## Workflow 3 — You know a specifier but not where it is used

**Goal:** find all uses of `ReplicatedUsing` in `Actor.h`.

```
search_files(target="content", pattern="ReplicatedUsing",
             path="<resolved GameFramework/Actor.h>")
→ line 351, …  (UPROPERTY lines with ReplicatedUsing=OnRep_*)
```

Read a 5–10 line window around each hit to see the full UPROPERTY + member
declaration. Pattern: the UPROPERTY line immediately precedes the C++ member
declaration.

---

## Workflow 4 — You need the module for an `*_API` symbol

The export macro directly encodes the module name. Rules:

| Macro | Module |
|---|---|
| `ENGINE_API` | `Engine` |
| `CORE_API` | `Core` |
| `COREUOBJECT_API` | `CoreUObject` |
| `GAMEPLAYABILITIES_API` | `GameplayAbilities` |
| `GAMEPLAYTAGS_API` | `GameplayTags` |
| `AIMODULE_API` | `AIModule` |
| `UMG_API` | `UMG` |
| `SLATECORE_API` | `SlateCore` |

Pattern: `<MODULENAME_ALLCAPS>_API`. Strip `_API`, lowercase the result — that is
the `Build.cs` module name. Confirm by locating `<ModuleName>.Build.cs` under
the corresponding source folder.

---

## Workflow 5 — You need a plugin API

Plugin APIs live under `Engine\Plugins\` and follow the same pattern. Example:
`GAMEPLAYABILITIES_API UAbilitySystemComponent` is declared in
`Engine\Plugins\Runtime\GameplayAbilities\Source\GameplayAbilities\Public\AbilitySystemComponent.h`.

Steps:
1. Use `search_files(target="files")` for the header under `Engine\Plugins\`.
2. Confirm the module via `<Module>.Build.cs` in the plugin's `Source\<Module>\`.
3. Confirm the plugin is enabled in the `.uproject`'s `Plugins` array.
4. Add the module name to `Build.cs` dependencies.

---

## Workflow 6 — Comparing a signature across engine versions

Resolve each installed or source-built engine root independently. Search the same symbol
in each tree, then diff the focused declaration windows. When an API changed
between versions, document the version it changed in the skill or code you produce.

---

## Reading headers efficiently

| Situation | Strategy |
|---|---|
| Looking for a class | `search_files(target="content")` for `"class AMyClass\b"` |
| Looking for a method | Search the header, then `read_file` a ±10-line window |
| Looking for a UPROPERTY | Search for the member; the UPROPERTY line is usually 1–2 lines above |
| Looking for specifiers on a known member | `read_file` a 15-line window starting 2 lines before the member |
| Navigating a 2,000+ line header | Search first; never read the whole file |

### Reading trick: focused `read_file`

When the search shows a hit at line 351 in `Actor.h`, read a focused context window:
```
read_file(path="<resolved Actor.h>", offset=347, limit=20)
```
This avoids loading the entire file. For `Actor.h` (~4,500 lines) this is
critical.

---

## Reflection anatomy of a UE C++ declaration

Every UCLASS/USTRUCT/UFUNCTION/UPROPERTY header follows this pattern:

```
[Header includes CoreMinimal.h, own *.generated.h last]

UCLASS(BlueprintType, Blueprintable, config=Engine, MinimalAPI)
class MYMODULE_API AMyActor : public AActor
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="MyGame")
    void MyFunction();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category="MyGame")
    float MyValue;
};
```

Key reading points:
- `UCLASS(...)` line — tells you whether it's `BlueprintType`, `Abstract`,
  `MinimalAPI`, `config=...`, etc.
- `MYMODULE_API` — tells you the module (see Workflow 4).
- `GENERATED_BODY()` — must be first in the class body; do not remove or move it.
- `UFUNCTION(...)` on the line immediately before a function — specifiers apply
  only to that one declaration.
- `UPROPERTY(...)` on the line immediately before a member — same rule.
- The `*.generated.h` include at the bottom of the includes block is UHT output;
  never edit it.
- `meta=(...)` clauses inside specifiers carry editor / Blueprint behavior;
  replicate them faithfully when you implement similar APIs.

---

## Common mistakes

- **Searching the Private folder first** — most public APIs are in `Public/` or
  `Classes/`; start there.
- **Reading the full header** — always search first, then read a focused range.
- **Trusting a memorized line number** — line numbers drift across patch releases.
  Search fresh each session for precision.
- **Forgetting the `*.generated.h` include** — UHT generates it; if your header
  uses reflection macros and omits the `#include "MyClass.generated.h"` (last
  include), compilation fails with an obscure macro-not-found error.
- **Using an Editor header in Runtime code** — if the found header is under
  `Source\Editor\`, it is only available when `WITH_EDITOR` is defined. Wrapping
  it in `#if WITH_EDITOR` or moving your code to an Editor module is required.

See [source-conventions.md](source-conventions.md) for the full naming prefix
and folder convention reference.
