# Hermes Agent integration

This downstream keeps the Unreal domain material portable while making discovery and the
source-navigation workflow predictable in Hermes Agent.

## What the downstream changes

- Every description starts with a complete `Use when ...` trigger sentence within Hermes'
  57-character skill-index preview.
- Ultra Dynamic Sky and Ultra Dynamic Weather triggers are package-qualified to avoid
  capturing native Unreal sky, weather, audio, Niagara, material, or time-of-day work.
- `metadata.hermes.tags` and `metadata.hermes.related_skills` improve routing and related-skill
  discovery without duplicating the domain guidance in every body.
- `navigating-engine-source` uses Hermes `search_files` and `read_file` operations and resolves
  the local engine root instead of inheriting another developer's drive layout.
- `scripts/check-hermes-compatibility.mjs` enforces these invariants across the full library.

The remaining skills intentionally describe Unreal concepts and contracts rather than editor
transport. Load a separate editor-control skill when the task requires Unreal MCP, VibeUE,
GameIQ, or another live-editor bridge.

## Install from a checkout

Hermes can discover skills from one or more external directories. See the authoritative
[Hermes Skills System documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
for current discovery and precedence behavior. First inspect the existing list:

```text
hermes config get skills.external_dirs
```

Open the configuration through Hermes, preserve every existing list item, and append this
checkout's `skills/` directory:

```text
hermes config edit
```

```yaml
skills:
  external_dirs:
    - C:/Users/<user>/.agents/skills
    - D:/Dev/Personal/unreal-engine-skills/skills
```

`hermes config set skills.external_dirs` currently stores an array-shaped argument as one string;
do not use it for this list. For a narrower trigger surface, append a category directory instead:

```yaml
skills:
  external_dirs:
    - D:/Dev/Personal/unreal-engine-skills/skills/core
```

After changing the list, start a fresh Hermes session. Confirm discovery with
an exact skill lookup rather than relying only on a truncated table row.

## Precedence and update safety

- A same-named profile-local skill can shadow an external copy. Remove duplicates only after
  the external skill loads successfully.
- Pin production use to a reviewed commit or tag. Pulling a moving branch changes the agent's
  behavior on the next skill reload.
- Treat the checkout as source. Make adaptations on a branch, validate, review the diff, and
  merge rather than editing loaded copies ad hoc.
- External skill directories may be writable. Use repository permissions or Hermes write
  approval settings when the checkout should remain read-only during normal agent work.

## Validation

Use [`docs/agents/validation.md`](agents/validation.md) for exact commands, change scopes,
routing checks, and marketplace-validation boundaries.

## Provenance and licensing

- Upstream: <https://github.com/kevinpbuckley/unreal-engine-skills>
- Downstream: <https://github.com/rmfraess/unreal-engine-skills>
- Hermes adaptation base: `5704060a01f8e7c0d31b003586f98186bef9c8a4`
- Engine target: UE 5.8; re-run source validation for every engine patch or upgrade.

The upstream repository does not currently declare a repository license. `license: UNLICENSED`
in skill frontmatter records that absence; it does not create a permission grant. Preserve
attribution and resolve licensing or redistribution permission before treating this fork as a
redistributable package. Ultra Dynamic Sky and Ultra Dynamic Weather skills also do not install,
license, or replace the marketplace products themselves.
