# Skill Authoring Guide

House style for writing Unreal Engine skills in this repo. Read this before adding or
editing a skill. It layers repo-specific conventions on top of the official
[Agent Skills specification](https://agentskills.io/specification).

## 1. The spec, in brief

A skill is a directory containing at minimum a `SKILL.md` with YAML frontmatter + Markdown body.

Frontmatter fields:

| Field | Required | Rule |
|---|---|---|
| `name` | yes | ≤64 chars; `a-z`, `0-9`, `-` only; no leading/trailing/consecutive hyphens; **must equal the folder name** |
| `description` | yes | ≤1024 chars; starts with a complete `Use when ...` trigger inside Hermes' first 57 displayed characters |
| `license` | no | short license name or file reference; use `UNLICENSED` only to record that no grant exists |
| `compatibility` | no | ≤500 chars; environment requirements |
| `metadata` | no | Agent Skills metadata plus the accepted nested `metadata.hermes` routing extension |
| `allowed-tools` | no | space-separated, experimental |

Progressive disclosure budget:
- **name + description** (~100 tokens) — always loaded, for *discovery*.
- **SKILL.md body** (< ~5000 tokens / 500 lines) — loaded on *activation*.
- **`references/`, `scripts/`, `assets/`** — loaded *on demand*.

Keep one reference hop from `SKILL.md` (don't chain references deeply).

## 2. Writing the `description` (most important field)

The description is how an agent decides whether to activate the skill. Hermes includes only
the first 57 characters in its compact skill index, so the first sentence must be a complete,
package-qualified trigger. Pattern:

> `Use when <specific trigger>. Covers <major branches>.`

Good:
```yaml
description: >-
  Use when structuring Unreal gameplay classes. Covers GameInstance, GameMode,
  GameState, controllers, pawns, characters, PlayerState, HUD, and login flow.
license: UNLICENSED
metadata:
  engine-version: "5.8"
  category: framework
  hermes:
    tags: [unreal-engine, ue5, gameplay-framework]
    related_skills: [actors-and-components]
```
Poor:
```yaml
description: Helps with gameplay.
```

Include the words an agent's task would contain (class names, system names, error phrases).
Marketplace triggers must name the package and say `confirmed` in the first sentence; generic
cloud, weather, lighting, material, audio, or time prompts belong to native Unreal skills.

## 3. Body structure (recommended sections)

Order skills roughly like this. Omit sections that don't apply.

1. **When to use this skill** — 2-4 bullet triggers (mirror/expand the description).
2. **Mental model** — the few concepts the agent must hold to not make mistakes.
3. **Core workflow / steps** — numbered, imperative, copy-pasteable.
4. **C++ patterns** — minimal correct snippets that compile against 5.8.
5. **Worked example** — a realistic example tying the patterns together (when it helps).
6. **Gotchas & edge cases** — the mistakes this skill exists to prevent.
7. **References & source material** *(required)* — real `Engine/Source/...` paths and verified
   official UE 5.8 doc URLs, plus links to any `references/*.md`.

## 4. Repo-specific rules

- **Target UE 5.8.** Snippets must be valid against 5.8. When an API differs across 5.x,
  add a short *Version note*.
- **Ground in real source, and always reference it.** Resolve the local engine root, then cite
  verified paths relative to `<UE_ENGINE_ROOT>/Engine/Source/`. Prefer naming the header and class
  (e.g. `GameFramework/Actor.h` → `AActor`) over vague references. If unsure of a signature,
  read the header before asserting it. **Every core skill must include a "References & source
  material" section** with at least one verified engine-source path (and official UE 5.8 doc
  URLs where confirmed — never guess a URL). Marketplace skills instead cite the installed
  product version or vendor documentation and never treat a zero-citation engine check as proof.
- **Keep domain skills tool-neutral.** Do **not**
  describe how to drive the editor, MCP, or any specific tool — the consuming agent handles
  that and has its own tooling skills. Describe *what* is correct in Unreal, not *which tool*
  performs it. A meta skill may name exact Hermes read-only operations when the operation is
  itself the workflow, as `navigating-engine-source` does.
- **Preserve Agent Skills compatibility.** Do not add unsupported top-level fields such as
  `version` or `author`; record Hermes-only routing under `metadata.hermes` and validate with
  both `skills-ref` and `check-hermes-compatibility.mjs`.
- **Show the macro specifiers that matter.** `UPROPERTY`/`UFUNCTION`/`UCLASS` specifiers are
  where agents go wrong — show the exact specifiers (`EditAnywhere`, `BlueprintReadWrite`,
  `BlueprintCallable`, `Replicated`, `meta=(...)`) and why.
- **Prefer modern APIs.** `TObjectPtr<>` for member UPROPERTYs, Enhanced Input over legacy
  input, MetaSounds over SoundCues, World Partition where applicable. Note legacy where the
  agent will still encounter it.
- **Keep code minimal and correct.** Snippets illustrate one idea; no incidental boilerplate.

## 5. Naming

- Skill folder = `name`. Use the action/domain, lowercase-hyphenated:
  `gameplay-framework`, `enhanced-input`, `networking-and-replication`.
- Reference files: `references/REFERENCE.md` for the main deep-dive, or topic files like
  `references/replication-conditions.md`.
- Scripts: name by what they do, e.g. `scripts/create_widget_blueprint.py`.

## 6. Checklist before committing a skill

- [ ] Folder name == `name` frontmatter; passes naming rules.
- [ ] `description` starts with a complete trigger inside 57 chars; ≤1024 chars.
- [ ] Marketplace descriptions require confirmed package context.
- [ ] `metadata.hermes.tags` and `metadata.hermes.related_skills` are present and resolve.
- [ ] Body ≤ ~500 lines; deep material moved to `references/`.
- [ ] Every cited source path exists in the 5.8 tree.
- [ ] C++ snippets compile against 5.8 (correct includes, macros, module deps).
- [ ] Has verified engine-source references, or versioned vendor evidence for marketplace skills.
- [ ] Domain guidance has no editor-transport instructions; meta tooling uses real Hermes names.
- [ ] The checks required by [`docs/agents/validation.md`](agents/validation.md) pass for the
  changed scope.
