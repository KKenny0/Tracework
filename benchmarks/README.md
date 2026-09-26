# Benchmarks

This directory publishes benchmark protocols and quality bars for Tracework skills.

Local fixtures, transcripts, grader outputs, and workspace snapshots are intentionally
not committed. Keep them under ignored `skills/*/evals/` or `*-workspace/`
directories when running private evaluations.

## Run Records

For each local benchmark run, record:

- Date and model
- Repository commit SHA
- Skill version or local diff summary
- Scenario name
- Pass/fail for each assertion
- Short failure reason and output excerpt for failed assertions

## Public Protocols

- `weekly-outline.md` documents the quality bar for scoped weekly management briefs.
- `reporting-narrative.md` defines executable contract checks plus real-output evaluation.
- `report-contract.mjs` validates scope, headline budgets, portfolio coverage, and audience safety.
- `regression-fixtures.json` lists public, synthetic regression scenarios for behavior that should not regress.
- `run-regression.mjs` executes fixture-backed checks. It currently runs
  report contracts, monthly raw loading, unsafe-slug rejection for raw writes
  and report reads, and capture-helper gates end to end.
  Agent-authored prose quality remains a documented real-output protocol.
- `test_tracework_sessions.py` generates temporary synthetic Codex and Claude
  transcripts to verify metadata-only indexing, scope-before-read filtering,
  incremental watermarks, and fail-closed host parsing. It never reads or
  commits a user's real session data.

Skill evaluations should keep local fixtures under ignored `skills/*/evals/`
directories. Public benchmark writeups should describe the behavioral contract
only: evidence preservation, reporting quality, scope safety, and correction
handling.

`test_evidence_flow.py` exercises historical capture through raw-only monthly
loading, concurrent appends and registration, atomic-write failure preservation,
and both supported Daily date formats. It uses temporary synthetic data only.

`test_report_reader.py` exercises the shared installed entry for all three reports:
config precedence, scope-before-body-read isolation, Daily-only repo restrictions,
ambiguous ownership, partial failures, correction preservation and monthly draft
write protection. All fixtures use temporary project and vault directories.
