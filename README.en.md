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

Tracework is a local reporting and memory plugin for **Codex** and **Claude Code**.

Say **“wrap up” (收工)** during day-to-day development to checkpoint durable facts, architectural tradeoffs, and key decisions. When it is time to update your team or management, generate **daily, weekly, and monthly progress reports with direct evidence backing**.

- **Evidence-Backed**: Every claim in a report can be traced back to raw entries, rejected alternatives, code changes, and identified risks. If records are missing, Tracework flags the coverage gap instead of hallucinating outcomes.
- **Local Sovereignty**: All facts and reports stay in your own local vault. No external telemetry, no background conversation leakage, and total data privacy.
- **Zero-Friction Preview**: Generate reports immediately in the active session without configuring a vault. When ready for durable storage, initialize with a single command.

> [!NOTE]
> **Product Boundary Notice**  
> Tracework is not a meeting-notes tool, approval workflow, performance-packaging layer, employee-monitoring surface, or generic office suite. Activity counts, commit counts, and lines of code describe coverage; they do not prove outcomes.

---

## Quickstart

### 1. Install Plugin

#### Codex
```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

#### Claude Code
```bash
claude plugin marketplace add KKenny0/Tracework
claude plugin install tracework@tracework
```

### 2. Try It Immediately (Zero Config)

After installing, try it directly in any project session with recent work:

```text
write the weekly report
# or
/tracework:weekly
```

Or close today's work first: `write the daily report` / `/tracework:daily`.

You do not need to configure a vault beforehand—Tracework renders an immediate preview right inside the conversation. When only Git history is available, Tracework generates a `limited` report that explicitly identifies evidence gaps.

### 3. Initialize Storage & Project Scopes (Optional)

When you are ready to accumulate work over time, write reports to local Markdown files, and strictly separate workplace from personal projects, run:

```text
/tracework:cold-start-interview
```

This interactive setup configures your local vault path, project identity, and reporting scopes.

---

## Core Loop & Skills

The daily workflow is simple: **Capture durable facts during development, then close progress at review milestones**.

```text
Agent Work
  ├─> Wrap up / /tracework:capture (Evidence multiplier: checkpoint facts & decisions)
  └─> Write Daily / Weekly / Monthly (Management-facing progress closure)
```

| Frequency / Role | What you say / Command | Purpose & Output |
| :--- | :--- | :--- |
| **High Frequency** | `write daily` / `weekly` / `monthly`<br>`/tracework:daily` · `:weekly` · `:monthly` | Management-facing progress closure: what changed, why it matters, and the next gate. |
| **Evidence Multiplier** | `wrap up` / `checkpoint`<br>`/tracework:capture` | Checkpoints session facts and architectural decisions, dynamically routed to `lite`, `standard`, or `deep`. |
| **Optional Recovery** | `capture today`<br>`/tracework:capture day [date] [scope]` | Scans locally indexed session metadata after scope resolution to backfill evidence (transcripts never enter the vault). |
| **Initial Setup** | `configure Tracework`<br>`/tracework:cold-start-interview` | One-time setup: configures local vault directory, project identity, and reporting scopes. |

### Skills Overview

- **`/tracework:daily`**: What changed today, why it matters, and the next gate. Protects manual edits and returns safe drafts on conflict.
- **`/tracework:weekly`**: Weekly management judgment. Outputs an executive brief by default, a quick summary on “what did we do this week”, or a PPT-ready Markdown Deck on explicit request.
- **`/tracework:monthly`**: Raw-first phase outcomes, recurring systemic risks, and next-month closure targets. Reads directly from raw facts without requiring prior daily reports.
- **`/tracework:capture`**: An adaptive session raw record (`lite`, `standard`, or `deep`).
- **`/tracework:capture day [date] [scope]`**: Incrementally recovers evidence from indexed sessions after scope partitioning.
- **`/tracework:cold-start-interview`**: Vault directory, project identity, and reporting group configuration.

---

## Key Capabilities & Principles

### 1. Strict Workplace vs. Personal Partitioning

Each project declares a reporting group in its config ([Configuration Guide](docs/configuration.md)):

```yaml
profile:
  project_name: My Project
  reporting_group: work   # Options: work, personal, open-source, consulting
```

Daily, Weekly, and Monthly reports enforce **partitioning before narrative synthesis**:

- **`work`**: Workplace projects only. Personal material must never enter the report body or evidence appendix.
- **`personal`**: Personal projects only.
- **`all`**: A private combined view, maintaining an independent judgment and headline lane for each group.

> **Scope Precedence**: Explicit parameter ➔ Configured default group ➔ Current project group. If none is resolved, Tracework falls back to a `local` conversation report of the current project. Unassigned projects never enter `work` or `personal`. Capture Day halts before reading sessions if scope is unresolved.

### 2. Goal Alignment & Evidence Chains

Weekly reports resolve and align with original goals within each group before analyzing actual progress, variance, and time-grounded next steps, avoiding arbitrary headline quotas.

The brief body preserves information that shifts management judgment; full commitments and supporting citations move to the appendix. If underlying facts are missing, Tracework exposes the gap rather than inventing history.

### 3. Presentation-Ready Decks (Weekly PPT)

When explicitly requested (`weekly PPT`, `周报 PPT`, or `presentation outline`), Tracework generates a standalone **PPT-ready Markdown Deck**:

- **Audience Focus**: Tailored for same-department weekly meetings—linking original goals to this week's final choices, shortest necessary rationale, evidence boundaries, and next week's plan.
- **Compression Review**: Excessive length triggers editorial compression review instead of an arbitrary slide count limit.
- **Compact Appendix**: Sources are reopened only for selected claims, with a compact evidence map in the appendix. The Markdown file remains fully self-contained.

### 4. Update Protection & Fact Correction

- **Edit Protection**: Daily reports manage content blocks by date and group. If manual edits or concurrent changes are detected, Tracework preserves the file and returns a draft in the conversation. Partial project read failures also return annotated drafts, saved only on explicit request.
- **Fact Correction**: If a stored fact is inaccurate, tell Capture to “**correct this record**” and provide the original claim alongside the verified fact. Corrections preserve the original record, apply to the target period, and support historical knowledge cutoffs (`as-of`). Daily, Weekly, and Monthly reports share this unified corrected view.

---

## Storage & Privacy

Tracework adheres strictly to **Local-First** principles ([Data Model](docs/data-model.md) and [Artifact Governance](docs/artifact-governance.md)):

- **Configuration**: `~/.tracework/config.yaml` or `{project}/.tracework/config.yaml`
- **Raw Entries**: `{vault}/raw/weeks/{week}/{slug}.json` (Semantic source of truth)
- **Artifact Dossiers**: `{vault}/raw/artifacts/{slug}.json` (Tracks navigation and boundary metadata without duplicating source documents)
- **Human-Readable Outputs**: `{vault}/Daily Note.md` and `{vault}/Work Diary/`

**Capture Day** is disabled by default. When `session_scan.enabled: true` is set, the plugin hook records only session pointers and grouping metadata under `~/.tracework/session-index/`. Local transcript parsing occurs only when explicitly invoking `/tracework:capture day`, and **transcript contents are never copied into the vault**.

---

## Development

Canonical files are synced via a static map (`canonical → skill-local → bundle`), and `check-skills` performs read-only validation.

```bash
npm --prefix cli run build
npm --prefix cli run copy-skills
npm --prefix cli run check-skills
npm --prefix cli run test
npm --prefix site run build
```

Core documentation: [Configuration](docs/configuration.md) · [Data Model](docs/data-model.md) · [Artifact Governance](docs/artifact-governance.md).

---

## Support

If Tracework helps turn your agent work into clearer, evidence-backed progress reports, support continued maintenance here:

👉 <https://kkenny0.github.io/support/>

Your support maintains reporting quality, cross-runtime packaging, storage contracts, and documentation.

---

## License

MIT
