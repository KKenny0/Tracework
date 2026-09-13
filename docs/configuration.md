# Configuration

[Back to README](../README.md)

Reports can be tried in the current conversation without configuration. Durable
storage needs a vault path and project reporting identity.

## Minimum Config

Global `~/.tracework/config.yaml`:

```yaml
knowledge_vault: /path/to/your/knowledge-vault

profile:
  default_reporting_group: work
```

Project `{project}/.tracework/config.yaml`:

```yaml
project_slug: my-project

profile:
  project_name: My Project
  reporting_group: work
```

Resolution order:

1. `{project}/.tracework/config.yaml`
2. `~/.tracework/config.yaml`

## Reporting Groups

`profile.reporting_group` partitions projects before Daily, Weekly, or Monthly
selects headlines. Recommended values are `work` and `personal`; other stable
values such as `open-source` or `consulting` are valid.

Scope resolves identically for reports and Capture Day: explicit user choice,
then `profile.default_reporting_group`, then the current project's group
(project config before matching registry). No assigned group means a
conversation-only `local` report; Capture Day stops before reading transcripts.
No helper silently defaults to `work`. Exact groups exclude unassigned
projects, including when selected by configuration. Explicit `all` produces
a private combined view with separate group sections.

The project registry mirrors the group:

```json
{
  "name": "My Project",
  "slug": "my-project",
  "path": "/absolute/path/to/project",
  "reporting_group": "work"
}
```

### Unassigned Projects

Project configs and registry rows without a reporting group are treated as
`unassigned`. Scoped reports exclude them rather
than guessing that they are safe for work or personal output. Run
`/tracework:cold-start-interview` in each existing project or add
`profile.reporting_group` and the registry field manually.

## Optional Fields

```yaml
profile:
  report_language: mixed     # zh | en | mixed; otherwise inferred
  weekly_mode: report        # report | tech; brief remains the default format
  team_context: solo         # solo | team | mixed

artifact_index:
  enabled: true              # default true

session_scan:
  enabled: false             # default false; metadata-only Stop hook
  retention_days: 30         # local session manifests, not transcript copies
```

Output paths remain optional under `daily_note`, `weekly_outline`, and
`monthly_review`.

## First Run

Run `/tracework:cold-start-interview`. It asks only for missing vault, project
identity, reporting group, and—when multiple groups exist—the default scope.

Capture Day is an optional enhancement, not a required setup step. When
global `session_scan.enabled: true`, the plugin's Stop hook indexes session metadata
under `~/.tracework/session-index/`; it does not read or copy transcript
content. Run `/tracework:capture day [YYYY-MM-DD] [scope]` explicitly to recover
report-ready facts. Manual `收工` and `/tracework:capture` always remain valid.

Codex requires users to review and trust plugin command hooks. Host or
organization policy may disable hooks; when that happens, Capture Day reports
the missing index and normal manual capture continues to work.

## Doctor

The maintenance CLI checks config, vault access, and plugin install state:

```bash
tracework doctor
```

Public installation uses the native marketplace commands documented in the
README. The CLI is not a legacy installer.
