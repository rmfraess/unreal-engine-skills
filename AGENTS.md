# unreal-engine-skills

This repository contains Agent Skills for Unreal Engine 5.8. It is Markdown-first, not an Unreal project or editor-automation plugin.

## Working on skills

- Skills live in `skills/<category>/ue-*/SKILL.md`; deep dives live beside them in `references/`.
- When adding or editing a skill, read `docs/skill-authoring-guide.md` for frontmatter, naming, source citations, and the marketplace-pack exception.
- When evaluating a skill, read `evals/README.md` for the manual baseline-versus-skill workflow and UE compile check.

## Validation

- Set `UE_ENGINE_ROOT` to the UE 5.8 installation directory containing `Engine/`. From the repo root, run `node scripts/check-citations.mjs` for all skills or `node scripts/check-citations.mjs core/ue-gameplay-tags` for one. This checks cited file existence, not API signatures or compilation.
- For optional Agent Skills spec validation, see the `skills-ref validate` command in `README.md`.

## Repository boundary

- This repository may have fork and upstream remotes. Check `git rev-parse --show-toplevel` and `git remote -v` before changing files or publishing; use the routed checkout.
