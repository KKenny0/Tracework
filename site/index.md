---
layout: home

hero:
  name: Tracework
  text: Turn agent work into evidence-backed progress reports.
  tagline: Say “wrap up” to keep the durable facts. Generate daily, weekly, and monthly reports when you need them.
  actions:
    - theme: brand
      text: Install
      link: /quick-start
    - theme: alt
      text: See the Loop
      link: /workflow

features:
  - title: Report first
    details: Try a daily or weekly report right after install, even in conversation only. Use scoped facts already visible in the conversation before capturing; git-only coverage stays limited.
  - title: Close the day and week
    details: Explain what changed, why it matters, and the next gate. Markdown brief by default; a presentation outline only when you ask.
  - title: Wrap up to keep the why
    details: End key sessions by saving trade-offs, risks, and next steps so later reports stay grounded.
  - title: Trace progress to evidence
    details: Follow report claims to raw facts, trade-offs, and verification evidence. Missing evidence stays visible.
---

<section class="tw-command-panel">

```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

<p>Public namespace: <code>tracework</code>. Records stay in your own local vault. You can try reports first, then set up durable storage.</p>

</section>

## How to use it

```text
install -> try: write weekly / write daily
        -> configure vault and project groups when you want multi-day memory
        -> wrap up after key sessions
        -> generate daily / weekly / monthly reports when needed
```

Projects can declare a reporting group such as `work` or `personal`. Reports
filter scope before selecting headlines, so personal projects never displace or
leak into workplace output. A private `all` view keeps each group in a separate
lane.

## Boundary

Tracework is not a meeting-notes tool, approval workflow, performance packaging
layer, generic office suite, or employee-monitoring surface. Activity volume is
coverage, not proof of outcomes. When the record is thin, Tracework exposes the
gap instead of inventing history.

Tracework is a local reporting plugin for Codex and Claude Code with five skills:
`capture` keeps key facts; `daily`, `weekly`, and `monthly` produce progress
reports; `cold-start-interview` configures storage and project groups.

Reports select projects before reading effective records, keeping work and
personal groups separate. Monthly reviews use raw records and current risk
states; Daily and Weekly reports provide prior judgments, so a complete Daily
archive is optional. If some projects cannot be read, Tracework returns a
conversation draft with coverage gaps and saves it only on explicit request.
