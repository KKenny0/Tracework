---
title: Showcase
description: Tracework output shapes, before/after sample, and proof boundaries.
---

# Showcase

This page stays conservative: one sample you can feel in 30 seconds, then the
evidence rules. **The before/after below is a fixture** built from the weekly
brief contract and public product capabilities (weekly modes, first-run local
trial, capture receipt). It is not a private vault export and not a customer
success claim.

## Before / After

### Before: plain git / hand-written weekly

```text
This week:
- updated the weekly skill
- refreshed README and docs site
- adjusted cold-start copy
- tweaked capture receipts
- ran tests

Continue optimizing next week.
```

Reads like an activity list. It does not say what state changed, what remains
gated, or which claims are actually supported.

### After: Tracework weekly brief (fixture)

```markdown
# 2026-W30 Weekly Brief

**Dates:** 2026-07-20 ~ 2026-07-22
**Scope:** work

## Weekly judgment

At the start of the week the product still looked like a system manual, and an
unconfigured first run could return empty under default work scope. This week
the positioning became “evidence-backed progress reports,” with weekly mode
split, local first-run trial, and capture receipts that point forward to
reports. Docs and skill contracts are aligned; host-session smoke and the
public sample gate remain open.

## Result arcs

### Public line and try-first path aligned

- **Starting constraint:** New users saw the full system; cold-start felt like a ticket
- **Decisive move:** Lead with “evidence-backed progress reports”; quick-start tries weekly first
- **End state:** README, docs site, and plugin copy share one line; reports can be tried after install
- **Why it matters:** Moves value to the first success instead of setup ceremony
- **Remaining gate:** Marketplace rendering after publish still needs a check
- **Evidence boundary:** recorded (docs/plugin manifests changed); marketplace UI not verified in this fixture

### Weekly split into quick / brief / slides

- **Starting constraint:** Ordinary weekly reports carried PPT diagram and narrative gates
- **Decisive move:** Three-mode routing; heavy rules only for slides
- **End state:** “What did we do this week” is a conversation quick view; default brief; PPT only when explicit
- **Why it matters:** Daily closure stays light; presentation depth remains available
- **Remaining gate:** Mode choice is contract-driven; no automated router assertion yet
- **Evidence boundary:** recorded (skill + skills pages synced)

### Unconfigured projects can try as local without leaking into work

- **Starting constraint:** Default work excluded unassigned repos, so first tries often looked empty
- **Decisive move:** Distinguish explicit / configured / implicit; implicit unassigned uses local
- **End state:** No vault still returns conversation output; explicit work still excludes unassigned with repair hints
- **Why it matters:** Try first, configure later, without breaking audience safety
- **Remaining gate:** One real no-config host smoke is still due
- **Evidence boundary:** recorded (skill + narrative contract); runtime smoke not claimed as verified

## Portfolio

| Stream | Status | What changed | Relation | Watch |
|--------|--------|--------------|----------|-------|
| Capture receipt forward line | done | Wrap-up now points at weekly/daily candidates | supporting | none |
| Quick-start / workflow docs | done | Match try-first narrative | supporting | none |
| Version bump | done | Plugin manifests at 0.6.0 | supporting | publish to marketplaces separately |

## Next-week closure targets

1. **Showcase gate:** public samples must be fixtures or desensitized real runs
2. **Host smoke:** no-vault weekly and quick review once each
3. **Release sync:** bump versions only when shipping a user-visible release

## Evidence boundary (summary)

- skill/contract edits: recorded
- git-only maintenance: limited, not promoted to outcomes
- unrun host install smoke: left as open gates, not invented as verified
```

### How to read the After

| Read point | Meaning |
| :--- | :--- |
| Stronger than Before | Has a **weekly judgment**, state-change arcs, and next gates—not a commit dump |
| `recorded` | Locally recorded decision/change; not independently proven in production |
| `limited` | Thin or git-only signal; no invented motive or verified impact |
| Recorded rationale | e.g. why brief skips logic diagrams; why unassigned cannot enter work |
| What was not invented | Missing host smoke and marketplace checks stay as gates, not completed claims |

In 30 seconds: Before answers “what kept us busy”; After answers “what changed, how strong the evidence is, and what blocks next.”

## Output Shapes

| Surface | What it should show | Proof boundary |
| :--- | :--- | :--- |
| Capture | Routed depth, goal, decision, rejected path, risk, evidence, next step; vault receipt points at later reports | A capture record is not independent proof |
| Weekly | quick / brief / slides; brief by default | Heavy PPT rules only in slides; git-only stays limited |
| Monthly | Raw-first phase narrative, recurring risks, next-month targets | Counts stay in coverage, not outcomes |

## Example Claim Chain

```text
O1 outcome or progress
  W1 supporting work stream
    D1 decision or tradeoff
      E1 raw entry or evidence reference
```

The chain is report-local. It helps readers move from a brief back to evidence,
but it does not mutate raw data.

## Real-Output Gate

Before adding another public case here, confirm:

- the source is a real Tracework run or a **clearly labeled fixture**
- private paths and proprietary details are removed
- `source_entry_refs` are described as provenance, not automatic verification
- every outcome claim has either independent evidence or a visible limitation
- a core mechanism slide covers its main path, key branch or fallback, output,
  and invariant without treating diagram structure as effect evidence
- routine maintenance stays in portfolio coverage without receiving a
  decorative architecture diagram
- unsupported report claims carry an explicit evidence gap

## Commands

| Command | Use |
| :--- | :--- |
| `/tracework:capture` | Capture the session; vault mode includes a forward-looking receipt |
| `/tracework:daily` | Daily closure; works without a vault |
| `/tracework:weekly` | Brief by default; quick review on “what did we do this week”; slides only for explicit PPT |
| `/tracework:monthly` | Monthly review |
| `/tracework:cold-start-interview` | Configure vault, project identity, and reporting group |
