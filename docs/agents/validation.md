# Repository Validation

Use the smallest validation scope that covers the change. Run commands from the repository root.

## Prerequisites

- Node.js 22, matching `.github/workflows/validate-skills.yml`.
- No dependency installation is required; repository scripts use Node built-ins.
- `npx` downloads the pinned `skills-ref@0.1.5` validator.
- Citation checks require `UE_ENGINE_ROOT` to name the directory containing `Engine/`.

## One Skill

For every changed skill:

```bash
node scripts/check-hermes-compatibility.mjs
npx --yes skills-ref@0.1.5 validate ./skills/<category>/<skill-name>
```

For a core skill, also verify its UE 5.8 source citations:

```bash
UE_ENGINE_ROOT='<actual-engine-root>' node scripts/check-citations.mjs <category>/<skill-name>
```

## Full Tree

Hermes compatibility:

```bash
node scripts/check-hermes-compatibility.mjs
```

Agent Skills compatibility, equivalent to CI:

```bash
failures=0
for skill_file in skills/*/*/SKILL.md; do
  skill_dir="$(dirname "$skill_file")"
  if ! npx --yes skills-ref@0.1.5 validate "$skill_dir"; then
    failures=$((failures + 1))
  fi
done
test "$failures" -eq 0
```

All UE source citations:

```bash
UE_ENGINE_ROOT='<actual-engine-root>' node scripts/check-citations.mjs
```

## Routing and Evals

- After changing descriptions or exposed categories, run the positive and negative cases in [`evals/hermes-routing.md`](../../evals/hermes-routing.md) from fresh sessions.
- For golden-task changes, follow [`evals/README.md`](../../evals/README.md), including UE 5.8 scratch-project compilation where applicable.

## Failure Semantics

- `check-hermes-compatibility.mjs` validates frontmatter, 57-character triggers, Hermes metadata, related-skill targets, local resource links, and source-navigation tool names across all skills.
- `check-citations.mjs` fails when the engine root is unavailable, a cited path is missing, or the selected scope contains zero recognized engine citations.
- Do not use the citation checker for Ultra Dynamic Sky or Ultra Dynamic Weather. Validate marketplace guidance against the installed product version and vendor documentation.
