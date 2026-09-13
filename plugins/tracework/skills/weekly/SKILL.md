---
name: weekly
description: >
  Generate a workplace-facing weekly report from Tracework raw entries, using
  git only as limited fallback coverage. Supports work, personal, and private
  all-project scopes. Three modes: quick conversation review ("这周做了啥",
  "周报简版", "quick weekly", "本周概要"), default Markdown brief ("写周报",
  "周报", "/tracework:weekly", "weekly brief", "本周总结", "weekly report"),
  and PPT-ready Markdown Deck only when weekly PPT is explicit ("weekly PPT", "周报 PPT",
  "weekly slides", "演示大纲"). Do not use for daily notes, generic slide
  decks, or single-commit analysis.
---

# Tracework Weekly

Explain the week’s actual change, variance, judgment and next commitment.
Never invent goals from activity or a previous report’s proposals.

## Mode and Required Reads

Resolve mode first. Conflicting explicit cues: slides > quick > brief.

| Mode | Request | Read after this entry and shared contract | Output |
| --- | --- | --- | --- |
| quick | 这周做了啥, 周报简版, quick weekly, 本周概要 | Nothing else by default | Conversation only |
| brief | 写周报, 周报, /tracework:weekly, weekly brief, 本周总结, weekly report | `references/weekly-analysis-contract.md`, `references/weekly-brief-template.md` | Markdown brief |
| slides | weekly PPT, 周报 PPT, weekly slides, 演示大纲 | `references/weekly-analysis-contract.md`, `references/weekly-slides-contract.md`, `references/slide-template.md` | PPT-ready Markdown Deck |

Always read `references/reporting-narrative-contract.md`. Default paths: Quick must not load analysis or templates;
brief must not load slides rules or the slide template; slides does not load the
brief template. Bare PPT/slides selects this mode only within a weekly request.

## Resolve Range, Scope, and Target

- Default period: current Monday through today.
- Resolve project then global config with
  `python <this-skill>/scripts/tracework_raw.py resolve-scope --cwd <project-root> --purpose report`.
  Add `--scope` only for explicit user choice; use scope, scope_source, reason.
- Apply the shared contract's scope-before-selection rules to every input and
  appendix. Explain excluded/empty scope without leaking titles or refs.
  Implicit-local is current-project-only, conversation-only and unassigned;
  never work. Keep all groups separate. A group does not imply a common goal.
- Default brief/slides file: `{vault}/Work Diary/Weekly/{YYYY-WNN}.md`, unless
  user/config overrides it. Only normal scoped vault runs write files. Quick,
  no-vault and implicit-local runs always stay in conversation.
- Ask before overwriting an existing file unless update/rewrite/overwrite is
  already requested. Missing setup never blocks; optional cold-start hint once.

## Evidence Workflow

1. Read effective facts and period-end states through the shared contract’s
   `tracework_state.py` route for each authorized project.
2. Apply the shared conversation admission rules.
3. For brief/slides, read available previous Weekly commitments as editorial
   context and explicit goal sources only as needed. Preserve confirmed versus
   proposed. Artifact dossiers are optional navigation and recorded scope.
4. Check uncovered git activity under the shared evidence boundary.
5. No usable signal: return the coverage gap without padding or empty files.

## Quick

Write one to seven concise bullets grounded in recorded changes, plus at most
three carried-forward lines for material risks or unresolved decisions. One
valid change is enough. No goal clarification question, slide candidates,
diagrams, implementation narratives, or vault write. Include claim boundaries
and a short coverage note when material; no need for report-local IDs.

## Brief and Slides

Follow the analysis contract for goal resolution, prior commitment accounting,
work-stream merging, variance, portfolio coverage and evidence. Unknown goals
stay unknown; ask at most once only when ambiguity changes selection or judgment.
Do not claim an unknown goal advanced. Keep unrelated goal lanes separate.

Brief applies Brief Projection and its template: one judgment per group, only
body blocks that change judgment/action/confidence, complete coverage and
provenance in the appendix. Slides branches before manager-oriented ranking:
apply Result Selection and selected-source recovery from the slides contract,
then the slide template. Do not produce a Brief before the deck.

## Shared Gate

Account for every prior commitment and replan; proposals remain proposals.
Return paths and coverage, or clearly conversation-only output.
