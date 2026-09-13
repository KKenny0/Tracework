# Skills

Full command reference. For first use, prefer [Quick Start](./quick-start): try a weekly or daily report before configuring a vault.

## High-Frequency Reporting

### Daily

`/tracework:daily [work|personal|all]` writes one daily judgment per reporting
group, necessary progress, and the next gate in short prose. One supported
change is enough. Protected per-date/per-group updates preserve user edits;
a conflict returns a draft instead of overwriting the file.

### Weekly

Three modes:

- **quick**: `这周做了啥` / `quick weekly` — 1–7 conversation bullets plus
  carried-forward items; no file write.
- **brief** (default): `/tracework:weekly` / write the weekly report —
  objective-anchored management brief covering actual change, variance, and
  next commitments. Its body is decision-complete; its appendix preserves
  accountability, work coverage, and provenance.
- **slides**: explicit `weekly PPT` / slides wording — a standalone PPT-ready
  Markdown Deck with only necessary main-deck pages; unusual length triggers
  compression review, and zero admitted pages return an empty state.

Without explicit framing, Slides serves same-department colleagues at a weekly
meeting, assumes they know the project background but not this week's changes,
and ends with next-week closure. It starts from why the work exists, selects the
weekly result or final choice, reopens sources only for selected claims, and
uses cognitive roles only when a complex merge/split decision needs them.
Public output contains claim-led slide content and a compact Evidence Appendix;
it contains no production guidelines or page-level source packets.

Design rationale and mechanism split only when they use different grounded
content, serve the same Deck Thesis, and the mechanism depends on the design
premise. Complementary proof objects may share a page when each has a clear
evidence responsibility for one claim.

### Monthly

`/tracework:monthly [work|personal|all]` uses raw entries as semantic truth and
Daily/Weekly as prior human judgments. It produces phase arcs, recurring risks,
and next-month closure targets.

Reports can use current visible conversation facts when project, group and work
date are known. They deduplicate these with raw/git and preserve conflicts.
This does not capture facts into long-term memory or scan other conversations.

Stored factual mistakes can be corrected through Capture. All six readers then
use the corrected fact in its original work period; explicit as-of preserves
the knowledge boundary. Accepted risks and unresolved conflicts stay visible.
Existing reports change only when you request a refresh. Targeted recovery
reads only the project/date you select and leaves temporary reads unsaved.

## Evidence Foundation

### Capture

`/tracework:capture`, checkpoint wording, or `收工` stores adaptive-depth raw
facts. It does not pre-write separate Daily, Weekly, and Monthly prose.

`/tracework:capture day [YYYY-MM-DD] [scope]` incrementally recovers durable
facts from opt-in local session manifests. Scope partition happens before
transcript reading, and transcript bodies are never copied into the vault.

## Lower-Frequency Trust and Recovery

### Query

Answers a specific why, alternative, revisit, or impact question from cited
local evidence. Unsupported questions return an evidence gap.

### Recall

Restores bounded project context when older work is resumed.

### Roadmap

Builds a long-range narrative over decision threads. It is an advanced review,
not a required reporting step.

### Cold Start

Configures the vault, project identity, and reporting group with the minimum
required questions. Metadata-only session scanning remains an explicit opt-in.
