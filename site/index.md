---
layout: home

hero:
  name: Tracework
  text: Turn agent work into evidence-backed progress reports.
  tagline: Say “wrap up” to keep the durable facts. Generate daily, weekly, and monthly reports when you need them. When the work is questioned later, replay why a choice was made.
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
  - title: Drill down when asked
    details: Replay why a choice was made, or resume older work, only when you need it — not as a daily habit.
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
        -> query / recall only when questioned or resuming
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
