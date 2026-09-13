<p align="center">
  <img src="assets/mark.svg" alt="Tracework" width="132" />
</p>

<h1 align="center">Tracework</h1>

<p align="center"><strong>Turn agent work into evidence-backed progress reports.</strong></p>

<p align="center">
  <img src="assets/tracework-reporting-hero.webp" alt="Tracework turns agent work into evidence-backed progress reports" width="1086" />
</p>

<p align="center">
  <a href="https://kkenny0.github.io/projects/tracework/"><strong>Project page</strong></a> · <a href="https://kkenny0.github.io/Tracework/"><strong>Documentation</strong></a> · <a href="README.md">中文</a>
</p>

The Chinese README is the canonical product reference; this page mirrors its
current product scope and command surface in English.

Say “wrap up” to keep the durable facts. Generate daily, weekly, and monthly
reports when you need them. When the work is questioned later, replay why a
choice was made.

Records stay in your own local vault. Without accumulated entries, reports can
still use git for `limited` coverage and mark the evidence boundary instead of
inventing intent or outcomes.

## Try It First

After install, try it in any project with recent work:

```text
write the weekly report
# or
/tracework:weekly
```

Or close today first: `write the daily report` / `/tracework:daily`.

You can see a result in the conversation without configuring a vault. Run
`/tracework:cold-start-interview` when you want durable storage, file writes,
and strict work/personal partitioning.

## Install

### Codex

```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

### Claude Code

```bash
claude plugin marketplace add KKenny0/Tracework
claude plugin install tracework@tracework
```

## Core Loop

```text
agent work
  -> wrap up and keep the durable facts
  -> write daily / weekly / monthly reports
  -> when needed: why that choice / resume where you left off
```

| Frequency | What you say | What it does |
| :--- | :--- | :--- |
| High | write daily / weekly / monthly | Management-facing progress closure |
| High multiplier | wrap up / capture | Makes later reports better grounded |
| Low | why did we choose this / continue last time | Drill-down when questioned or resuming |

## Reporting Scopes

Each project can declare a reporting group:

```yaml
profile:
  project_name: My Project
  reporting_group: work   # or personal, open-source, consulting
```

Daily, Weekly, and Monthly partition scope before selecting the main story:

- `work`: workplace projects only. Personal material must not appear in the
  report body or evidence appendix.
- `personal`: personal projects only.
- `all`: a private combined view, with a separate judgment and headline set for
  each group.

The default three-headline budget applies per reporting group, not across the
whole vault. Other meaningful work remains visible in portfolio status instead
of disappearing because it was not selected as a headline.

When upgrading from 0.2, projects without `reporting_group` become
`unassigned` and are excluded from scoped reports for safety. Run
`/tracework:cold-start-interview` once in each project or add the field
manually.

## Skills

| Command | Frequency | Output |
| :--- | :--- | :--- |
| `/tracework:daily` | High | What changed today, why it matters, and the next gate |
| `/tracework:weekly` | High | Weekly management judgment; brief by default, quick review on “what did we do this week”, PPT outline only when requested |
| `/tracework:monthly` | High | Raw-first phase outcomes, recurring risks, and next-month closure targets |
| `/tracework:capture` | High multiplier | An adaptive lite/standard/deep session raw record |
| `/tracework:capture day [date] [scope]` | Optional recovery | Incrementally recovered evidence from indexed sessions after scope partitioning |
| `/tracework:query` | Low | A cited answer to why a path was chosen |
| `/tracework:recall` | Low | Bounded context for resuming older work |
| `/tracework:roadmap` | Low / advanced | A long-range decision-thread narrative |
| `/tracework:cold-start-interview` | One-time upgrade | Vault, project identity, and reporting group |

When explicitly asked for a `weekly PPT`, Tracework produces a 6-10 slide
outline for an individual contributor reporting within a department. Core
technical results follow three questions: why it changed, how the new mechanism
works, and whether it is effective. Before/After establishes the state change;
solution logic and implementation narrative explain the main path, branches,
fallbacks, and invariants; data, tests, or a visible measurement gap establish
the evidence boundary. The main deck keeps at most two or three logic diagrams,
does not manufacture architecture diagrams for routine maintenance, and leaves
raw evidence mappings in the appendix. The command produces an outline, not a
rendered `.pptx` file.

Decision replay is a trust mechanism, not a daily operation. A reader can drill
from a report claim to raw entries, rejected alternatives, risks, and direct
evidence. When the record is insufficient, Tracework should expose the gap
instead of inventing history.

Tracework is not a meeting-notes tool, approval workflow, performance-packaging
layer, employee-monitoring surface, or generic office suite. Activity counts,
commit counts, and lines of code describe coverage; they do not prove outcomes.

## Storage

- Configuration: `~/.tracework/config.yaml` or `{project}/.tracework/config.yaml`
- Raw entries: `{vault}/raw/weeks/{week}/{slug}.json`
- Artifact dossiers: `{vault}/raw/artifacts/{slug}.json`
- Decision indexes: `{vault}/raw/decisions/{slug}.json`
- Human-readable outputs: `{vault}/Daily Note.md` and `{vault}/Work Diary/`

Raw entries remain semantic truth. Decision indexes are rebuildable query views.
Artifact dossiers preserve navigation and recorded boundaries without copying
complete source documents.

Capture Day is optional and disabled by default. When `session_scan.enabled: true`
is set, the plugin hook stores only session pointers and the metadata needed for
reporting groups under `~/.tracework/session-index/`. Only an explicit
`/tracework:capture day` invocation reads that day's sessions after scope
partitioning, and transcript content is never copied into the vault.

## Development

`copy-skills` synchronizes canonical → skill-local → bundle using one static map.
`check-skills` is read-only; CI rejects uncommitted generated differences.

```bash
npm --prefix cli run build
npm --prefix cli run copy-skills
npm --prefix cli run check-skills
npm --prefix cli run test
npm --prefix site run build
```

Core documentation: [Configuration](docs/configuration.md),
[Data model](docs/data-model.md), and
[Artifact governance](docs/artifact-governance.md).

## Support

If Tracework helps you turn agent work into clearer progress reports while
preserving the evidence behind important decisions, you can support continued
maintenance here:

<https://kkenny0.github.io/support/>

Your support helps maintain reporting quality, cross-runtime plugin packaging,
storage contracts, and documentation.

## License

MIT
