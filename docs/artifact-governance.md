# Artifact Governance

[Back to README](../README.md)

Tracework keeps durable project artifacts close to the code. The vault stores
indexes and synthesized outputs, not full copies of every project document.

## Rule

Preserve enough provenance for direct report value first:

```text
/tracework:daily or /tracework:weekly -> limited when only git exists
/tracework:capture -> stronger report evidence
```

Daily, weekly, and monthly reports can reuse the same evidence later.
They should not require users to maintain a parallel report-specific document
catalog.

## Artifact Dossier

`{vault}/raw/artifacts/{slug}.json` stores durable artifact dossiers. A dossier
is more than a path index and less than a source document backup. It should
identify:

- where the durable artifact lives
- which topics, decision threads, risks, or open questions it covers
- whether it is active, superseded, obsolete, or missing
- when a later skill should read or mention it
- what the artifact governs and does not govern
- which key claims, decisions, and open questions are worth preserving
- when the source was last seen and whether it still exists

The dossier should be independently readable after the source moves or is
deleted, but it is not independently authoritative. Treat its claims as
navigation or recorded context unless they carry direct evidence. The dossier
must not duplicate the full artifact. Full content stays in the project repo
unless the artifact is itself a vault wiki output.

Weekly raw entries remain authoritative. If the record does not support a
report claim, the report should expose that gap. Add new information as new raw
entries rather than rewriting historical records.
