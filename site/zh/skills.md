# Skills

完整命令参考。第一次上手优先看 [快速开始](./quick-start)：先试写周报或日报，再配置 vault。

## 高频报告

### Daily

`/tracework:daily [work|personal|all]` 为每个 reporting group 生成今日判断、必要进展和
下一道门的短正文。一条有依据的变化也足够。更新按日期、分组保护用户手改；出现
冲突时保留原文，返回草稿。

### Weekly

三档：

- **quick**：`这周做了啥` / `周报简版` — 对话内 1–7 条 + 结转，不写文件。
- **brief**（默认）：`/tracework:weekly` / `写周报` — management brief。
- **slides**：明确 `weekly PPT` / `周报 PPT` 时 — 面向部门内部汇报、以 IC 为讲述者的
  PPT-ready Markdown Deck；只保留必要页面，异常长度触发压缩检查而不是数字上限。

没有显式受众时，Slides 默认服务同部门周会：同事知道项目背景，但不了解本周最新
实现与验证；正文从“为什么做”进入本周结果或最终选择，给出最短必要理由，并以下周
计划收口。系统只为入选结果回溯 source；认知任务仅在复杂拆合页时使用。完整 source
packet 不公开，PPT 制作者只做视觉转译。

### Monthly

`/tracework:monthly [work|personal|all]` 以 raw entries 为语义真相，Daily/Weekly 只
作为已有的人类判断，输出阶段弧线、反复风险和下月收口目标。

报告可以直接使用当前对话中已可见、能确定项目、分组和工作日期的事实，与 raw/git
去重并保留冲突。这不会自动保存长期记忆，也不会扫描其他对话。

可以通过 Capture 更正已经保存的错误事实。六个读取入口会在原工作期间采用更正后
的事实，明确指定 as-of 时按当时已知材料回放；已接受风险与未解决冲突分别保留。
已有报告只在请求更新时改写。补证据限定为你选定的项目和日期，临时查看不会落库。

## 证据基础

### Capture

`/tracework:capture`、checkpoint 或“收工”保存动态深度的 raw facts，不提前写三份
Daily、Weekly、Monthly 文案。

`/tracework:capture day [YYYY-MM-DD] [scope]` 从显式启用的本地 session manifest
增量补回持久事实。分区发生在 transcript 读取之前，正文不会被复制进 vault。

## 低频可信度与恢复

### Query

从有引用的本地证据回答具体的 why、alternatives、revisit 或 impact 问题。证据不足
时明确返回缺口。

### Recall

继续旧工作时恢复有边界的项目上下文。

### Roadmap

对决策线程生成长周期叙事，是高级复盘，不是报告必经步骤。

### Cold Start

用最少问题配置 vault、项目身份和 reporting group。元数据级 session scan 保持显式
opt-in。
