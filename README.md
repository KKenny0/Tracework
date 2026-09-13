<p align="center">
  <img src="assets/mark.svg" alt="Tracework" width="132" />
</p>

<h1 align="center">Tracework</h1>

<p align="center"><strong>把 Agent 工作，收口成有证据的进展报告。</strong></p>

<p align="center">
  <img src="assets/tracework-reporting-hero.webp" alt="Tracework 把 Agent 工作收口成有证据的进展报告" width="1086" />
</p>

<p align="center">
  <a href="https://kkenny0.github.io/projects/tracework/"><strong>项目页</strong></a> · <a href="https://kkenny0.github.io/Tracework/"><strong>文档</strong></a> · <a href="README.en.md">English</a>
</p>

日常说“收工”留下关键事实；需要时生成日报、周报、月报。
被追问时，再回看当时为什么这么选。

记录留在你自己的本地 vault。没有累计记录时，报告仍可用 git 生成 `limited`
版本，并明确标出证据边界，而不是编造动机或成果。

## 最短试用

安装后，在任意有工作记录的项目里直接试：

```text
写周报
# 或
/tracework:weekly
```

也可以先写今天的收口：`写日报` / `/tracework:daily`。

不配置 vault 也能先在对话里看到结果。若要跨天累计、写入文件，以及严格区分公司 /
个人项目，再运行 `/tracework:cold-start-interview`。

## 安装

### Codex

```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

### Claude Code

```bash
claude plugin marketplace add KKenny0/Tracework
claude plugin install tracework@tracework
```

## 核心循环

```text
Agent 工作
  -> 收工，留下关键事实
  -> 写日报 / 写周报 / 写月报
  -> 需要时：为什么当时这么选 / 接着上次
```

| 频次 | 你怎么说 | 作用 |
| :--- | :--- | :--- |
| 高频 | 写日报 / 写周报 / 写月报 | 给人看的进展收口 |
| 高频增强 | 收工 | 让后续报告更有依据 |
| 低频 | 为什么当时这么选 / 接着上次 | 被追问或续作时下钻 |

## 公司与个人项目分区

每个项目可以声明报告分组：

```yaml
profile:
  project_name: My Project
  reporting_group: work   # 也可以是 personal、open-source、consulting
```

Daily、Weekly、Monthly 必须先分区，再选择主线：

- `work`：只包含公司项目，任何个人内容都不得进入正文或证据附录。
- `personal`：只包含个人项目。
- `all`：私人全景视图，各组分别拥有自己的判断和 headline。

Weekly 会在每个分组内先恢复目标来源，再解释实际变化、偏差和下周承诺，不固定
headline 数量。Brief 正文只保留会改变管理判断的信息，完整承诺、工作组合与证据
进入附录；其余有意义的工作不会因为没有进入正文而消失。

从 0.2 升级时，尚未配置 `reporting_group` 的项目会成为 `unassigned`，并出于安全
原因被 scoped report 排除。请在每个项目中运行一次
`/tracework:cold-start-interview`，或手动补上该字段。

## Skills

| Command | 频次 | 输出 |
| :--- | :--- | :--- |
| `/tracework:daily` | 高频 | 今天改变了什么、为什么重要、下一道门是什么 |
| `/tracework:weekly` | 高频 | 周级管理判断；默认 brief，「这周做了啥」为 quick，明确 PPT 时才出 PPT-ready Markdown Deck |
| `/tracework:monthly` | 高频 | Raw-first 的阶段成果、反复风险和下月收口目标 |
| `/tracework:capture` | 高频增强 | 动态选择 lite/standard/deep 的 session raw record |
| `/tracework:capture day [date] [scope]` | 可选补录 | 按分组扫描已索引 session，增量补回当天证据 |
| `/tracework:query` | 低频 | 用引用回答当时为什么这么选 |
| `/tracework:recall` | 低频 | 继续旧工作时恢复有边界的上下文 |
| `/tracework:roadmap` | 低频进阶 | 长周期决策线程叙事 |
| `/tracework:cold-start-interview` | 一次性增强 | Vault、项目身份和报告分组 |

明确请求 `weekly PPT` 时，Tracework 会生成只保留必要页面的 PPT-ready Markdown
Deck；异常长度触发压缩检查，而不是数字上限。没有显式受众时，默认服务同部门周会：
从工作目标进入本周结果或最终选择、最短必要理由和证据边界，并以下周计划收口。
系统只为入选结果回溯 source，完整 source packet 留在内部，公开附录只保留紧凑证据
映射。Markdown 本身可以独立阅读，PPT 只是它的视觉转译。

Decision replay 是可信机制，而不是需要每天使用的操作。读者可以从报告主张向下追到
raw entry、被拒方案、风险和直接证据。记录不足时，Tracework 应该明确暴露缺口，而
不是编造历史。

Tracework 不是会议纪要、审批流、绩效包装、员工监控或泛办公室套件。活动数、提交数
和代码行数只能描述覆盖度，不能证明成果。

## Storage

- 配置：`~/.tracework/config.yaml` 或 `{project}/.tracework/config.yaml`
- Raw entries：`{vault}/raw/weeks/{week}/{slug}.json`
- Artifact dossiers：`{vault}/raw/artifacts/{slug}.json`
- Decision indexes：`{vault}/raw/decisions/{slug}.json`
- 可读输出：`{vault}/Daily Note.md` 和 `{vault}/Work Diary/`

Raw entries 是语义真相；decision index 是可重建的查询视图；Artifact dossier 保存导航
和已记录边界，不复制完整源文档。

可选的 Capture Day 默认关闭。设置 `session_scan.enabled: true` 后，插件 Hook 只在
`~/.tracework/session-index/` 保存 session 指针和分组所需元数据；只有显式运行
`/tracework:capture day` 才会在分区后读取当天会话，且不会把 transcript 复制进 vault。

## 开发

`copy-skills` 按固定映射同步 canonical → skill-local → bundle；`check-skills` 只检查，不修复。CI 会拒绝未提交的生成物差异。

```bash
npm --prefix cli run build
npm --prefix cli run copy-skills
npm --prefix cli run check-skills
npm --prefix cli run test
npm --prefix site run build
```

核心文档：[配置](docs/configuration.md)、[数据模型](docs/data-model.md)、
[Artifact governance](docs/artifact-governance.md)。

## 支持

如果 Tracework 帮你把 Agent 工作收口成了更清晰的进展报告，同时保留了重要决策背后的
证据，你可以在这里支持项目继续维护：

<https://kkenny0.github.io/support/>

你的支持将用于持续维护报告质量、跨运行时插件打包、存储契约和文档。

## License

MIT
