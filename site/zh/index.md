---
layout: home

hero:
  name: Tracework
  text: 把 Agent 工作，收口成有证据的进展报告。
  tagline: 日常说“收工”留下关键事实；需要时生成日报、周报、月报。被追问时，再回看当时为什么这么选。
  actions:
    - theme: brand
      text: 快速开始
      link: /zh/quick-start
    - theme: alt
      text: 查看工作流
      link: /zh/workflow

features:
  - title: 先出报告
    details: 安装后可先试写日报或周报（可对话输出）。尚未收工也能使用当前对话中范围明确的事实；只有 git 记录时标明 limited 边界。
  - title: 收口今天与本周
    details: 讲清改变了什么、为什么重要、还差哪一道门；默认管理简报，明确要求时再出汇报大纲。
  - title: 说“收工”留下依据
    details: 关键 session 结束时保存取舍、风险和下一步，让后续报告更有依据。
  - title: 被追问时再下钻
    details: 需要时回看当时为什么这么选，或接着上次继续；不必当成每天的操作。
---

<section class="tw-command-panel">

```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

<p>公开 namespace 是 <code>tracework</code>。记录留在你自己的本地 vault；也可以先试用，再配置持久保存。</p>

</section>

## 怎么用

```text
安装 -> 先试：写周报 / 写日报
      -> 需要跨天累计时再配置 vault 与项目分组
      -> 关键活结束说“收工”
      -> 被追问或续作时再 query / recall
```

项目可声明 `work`、`personal` 等 reporting group。报告先分区，再选择 headline，个人
项目不会挤占或泄漏进公司汇报；私人 `all` 视图会把各组放在独立叙事中。

## 边界

Tracework 不是会议纪要、审批流、绩效包装、泛办公室套件或员工监控。活动数量只能
说明覆盖度，不能证明成果。记录不足时暴露缺口，不编造历史。
