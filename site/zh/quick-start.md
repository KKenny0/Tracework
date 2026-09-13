# 快速开始

## 1. 安装

```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

Claude Code：

```bash
claude plugin marketplace add KKenny0/Tracework
claude plugin install tracework@tracework
```

## 2. 先试一份报告

在任意有近期工作的项目里直接说：

```text
写周报
```

或：

```text
/tracework:weekly
```

也可以先写今天：`写日报` / `/tracework:daily`。

不配置 vault 也能先在对话里看到结果。当前项目尚未分组时，隐式试用会按 `local`
出当前仓库报告，而不会假装成安全的 `work` 汇报；显式或默认配置选择 `work` 时会排除
未分组项目并提示修复。尚未 Capture 时，也可以使用当前对话里项目、分组和工作日期明确的事实；
这些临时依据不会自动存入长期记忆，也不会触发其他对话读取。只有 git 活动时标成
`limited`，不会补造动机、决策或已验证影响。

## 3. 需要时再开启持久保存

若要跨天累计、写入本地文件，以及严格区分公司 / 个人项目，再运行：

```text
/tracework:cold-start-interview
```

它会设置本地 vault、项目身份，以及 `work` 或 `personal` 等 reporting group。

为需要纳入分组报告的每个项目配置分组。未分组项目不会被猜进公司或个人汇报。

常用收口：

```text
/tracework:daily work
/tracework:weekly work
/tracework:monthly work
```

个人项目使用 `personal`；私人全景使用 `all`，各组会分别叙事。Weekly 有三档：说
`这周做了啥` / `周报简版` 得到对话里的 quick 回顾；默认 `写周报` 生成 Markdown
brief；明确说 `weekly PPT` / `周报 PPT` 时，才生成面向部门内部汇报、以 IC 为讲述
者的 PPT-ready Markdown Deck。没有显式受众时，默认是同部门周会，不虚构时长；
内容从工作目标进入本周结果或最终选择、最短必要理由和证据边界，最后给出下周计划。
Markdown 本身可独立阅读，PPT 只是视觉转译。

## 4. 用“收工”让报告更有依据

关键工作结束时说“收工”或运行 `/tracework:capture`。Capture 会从 session 信号选择
lite、standard 或 deep，只保存值得跨 session 复用的事实。

如果更适合每天结束时集中补录，可以显式启用：

```yaml
session_scan:
  enabled: true
  retention_days: 30
```

然后运行 `/tracework:capture day [YYYY-MM-DD] [work|personal|all]`。插件 Hook 只索引
元数据；Capture Day 会先完成 reporting group 分区，再读取会话内容。

## 5. 被追问或续作时再下钻

- `/tracework:query why did we choose ...?`
- 继续旧工作时运行 `/tracework:recall`
- 长周期决策复盘时运行 `/tracework:roadmap`

这些是低频能力，不需要培养成每日操作。

## 6. 更新报告或更正记录

日报更新会保护手改内容；文件在读取后发生变化时返回草稿。已保存事实有误时，
对 Capture 说“更正这条记录”，提供原记录、正确事实和原因。原始记录保留，六个
读取入口在原工作期间使用更正后的事实。已有报告只在请求刷新时更新；写入更正后，
保留支持更正的插件，不要降级到旧读取器。历史知悉时点和状态处理见 [Skills](./skills)。
