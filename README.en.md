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

Records stay in your own local vault. You can report before capturing: facts
already visible in the current conversation can provide temporary evidence when
the project, group, and work date are known. Reporting does not save those facts
to long-term memory or read other conversations. Git-only reports remain
`limited`, with explicit gaps instead of invented intent or outcomes.

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

Weekly resolves goal sources within each group, then explains actual change,
variance, and next commitments without a fixed headline count. The brief keeps
information that changes management judgment; its appendix preserves full
commitments, work coverage, and evidence.

Scope uses your explicit choice, then the configured default, then the current
project’s group. If none is known, the report stays in the conversation as a
`local` view of the current project. Unassigned projects cannot enter `work` or
`personal`; run `/tracework:cold-start-interview` to assign a group. Capture Day
stops before reading sessions when scope is unresolved.

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

When explicitly asked for a `weekly PPT`, Tracework produces a standalone
PPT-ready Markdown Deck with only the necessary pages. Unusual length triggers
compression review rather than a fixed page limit. By default, it serves a
same-department weekly meeting: work goals, this week's results or final choices,
the shortest necessary rationale and evidence boundary, then next-week plans.
Sources are reopened only for selected claims; the public appendix keeps a
compact evidence map. The Markdown is readable on its own; a rendered `.pptx`
is a separate visual translation.

Decision replay is a trust mechanism, not a daily operation. A reader can drill
from a report claim to raw entries, rejected alternatives, risks, and direct
evidence. When the record is insufficient, Tracework should expose the gap
instead of inventing history.

Tracework is not a meeting-notes tool, approval workflow, performance-packaging
layer, employee-monitoring surface, or generic office suite. Activity counts,
commit counts, and lines of code describe coverage; they do not prove outcomes.

## Updating Reports and Correcting Records

Daily updates protect existing content by date and group; hand edits or
concurrent changes return a draft while preserving the file. For a mistaken
stored fact, ask Capture to correct the record and provide the original record
and the correct fact. Corrections preserve original records and apply in the
original work period; an explicit historical knowledge cutoff (as-of) uses only
what was known then. Daily, Weekly, Monthly, Recall, Query, and Roadmap share
that corrected view. Existing reports change only when you request a refresh;
once corrections exist, do not downgrade to readers that ignore them.

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
