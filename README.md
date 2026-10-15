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

Tracework 是面向 **Codex** 和 **Claude Code** 的本地报告与记忆插件。

日常研发中对 Agent 说一句“**收工**”，沉淀架构权衡、技术决策与代码演进背后的关键事实；需要同步进展时，一键生成**有直接证据支撑的日报、周报与月度回顾**。

- **证据闭环（Evidence-backed）**：报告中的每一项结论均可向下穿透至原始记录（Raw Entry）、决策理由与已知风险。记录不足时明确标出缺口，绝不凭空编造成果。
- **本地主权（Local-First）**：全部记录保存在你自己的本地 Vault，零外部数据上报，不泄露任何对话与业务机密。
- **零门槛即时可用（Zero-friction）**：未配置 Vault 也能在当前会话中即时出报预览；按需一键初始化，实现跨天累计与项目严格隔离。

> [!NOTE]
> **产品边界声明**  
> Tracework 不是会议纪要整理、OA 审批流、绩效词藻包装工具，更不是员工监控软件。提交频次、活动点数与代码行数仅用于衡量追踪覆盖度，不能作为成果证明。

---

## 快速上手

### 1. 安装插件

#### Codex
```bash
codex plugin marketplace add KKenny0/Tracework
codex plugin add tracework@tracework
```

#### Claude Code
```bash
claude plugin marketplace add KKenny0/Tracework
claude plugin install tracework@tracework
```

### 2. 即刻体验（无需配置）

安装后，在任意有工作记录的项目会话中直接尝试：

```text
写周报
# 或
/tracework:weekly
```

也可以先生成今日收口：`写日报` / `/tracework:daily`。

无需预先配置 Vault，Tracework 会在当前对话中即时输出预览。当仅有 Git 记录时，将自动生成标注缺口的 `limited` 版本报告，明确指出事实盲区。

### 3. 初始化持久化与项目治理（可选进阶）

当你需要跨天累计工作证据、将报告写入本地 Markdown 文件，以及严格隔离公司与个人项目时，运行：

```text
/tracework:cold-start-interview
```

即可通过交互式引导，完成本地知识库（Vault）绑定与项目身份配置。

---

## 核心循环与技能

日常心流非常简单：**平时让 Capture 沉淀事实，周期节点直接调取 Reporting 输出**。

```text
Agent 工作
  ├─> 收工 / /tracework:capture（留下关键事实，作为证据倍增器）
  └─> 写日报 / 写周报 / 写月报（收口为面向团队与管理的进展汇报）
```

| 频次 / 角色 | 你怎么说 / 命令 | 核心产出与作用 |
| :--- | :--- | :--- |
| **高频汇报** | `写日报` / `写周报` / `写月报`<br>`/tracework:daily` · `:weekly` · `:monthly` | 面向团队与管理者的进展收口，解释改变了什么、为什么重要与下阶段门槛 |
| **证据倍增器** | `收工` / `checkpoint`<br>`/tracework:capture` | 自动捕获当前会话的架构决策与关键事实，动态适配 `lite` / `standard` / `deep` 深度 |
| **按需回溯** | `补录今天` / `扫描今天会话`<br>`/tracework:capture day [date] [scope]` | 仅在指定范围后，扫描已索引的本地会话元数据增量补全当天证据（Transcript 不入库） |
| **首次配置** | `配置 Tracework`<br>`/tracework:cold-start-interview` | 一次性初始化设置：配置本地 Vault 存储路径、项目身份与报告分组 |

### 技能矩阵概览

- **`/tracework:daily`**：今天改变了什么、为什么重要、下一道推进门槛是什么。
- **`/tracework:weekly`**：周级管理判断。默认生成管理 brief；输入“这周做了啥”生成 quick 简版；明确请求 PPT 时生成 PPT-ready Markdown Deck。
- **`/tracework:monthly`**：Raw-first 的阶段成果、反复出现的系统风险与下月收口目标。直接基于原始记录，无需先写齐全部日报。
- **`/tracework:capture`**：自适应深度的会话原始事实记录（Raw record）。
- **`/tracework:capture day [date] [scope]`**：按分组扫描已索引 session，安全补回证据。
- **`/tracework:cold-start-interview`**：配置存储、项目标识与报告分组。

---

## 核心机制与设计原则

### 1. 公司与个人项目严格分区

每个项目可通过配置文件声明报告分组（[查看配置指南](docs/configuration.md)）：

```yaml
profile:
  project_name: My Project
  reporting_group: work   # 选项: work, personal, open-source, consulting
```

Daily、Weekly、Monthly 严格执行**先划分范围、再组织叙事**：

- **`work`**：仅包含公司项目，任何个人内容与证据绝不进入正文或附录。
- **`personal`**：仅聚合个人项目。
- **`all`**：私人全景综合视图，各分组分别拥有独立的判断与 Headline 叙事线。

> **范围判定优先级**：明确指定的参数 ➔ 配置的默认分组 ➔ 当前项目所在分组。都未确定时，仅在对话中生成当前项目的 `local` 报告；未分组项目绝不会意外混入 `work` 或 `personal`。Capture Day 在范围未确定时主动停止读取会话。

### 2. 目标溯源与证据链

Weekly 会在每个分组内先溯源对齐既定目标，再解释实际变化、偏差分析与具有时间依据的后续安排，不固定 headline 数量。

Brief 正文只保留足以改变管理判断的关键信息，完整承诺、工作组合与证据移入附录；其余有意义的工作不会因未进入正文而丢失。读者可从报告主张一路向下追溯到 Raw entry、被拒方案、技术风险与直接证据。

### 3. 会议就绪型演示大纲（Weekly PPT）

明确请求 `weekly PPT`（或“周报 PPT”、“演示大纲”）时，Tracework 会生成一份可独立阅读的 **PPT-ready Markdown Deck**：

- **内容组织**：默认服务同部门周会——从工作目标切入，呈现最终选择、最短必要理由与证据边界，最后以下周交付计划收口。
- **篇幅审查**：若长度异常，触发内容压缩审查，而非机械死卡幻灯片页数。
- **证据映射**：系统仅为入选结果回溯 source，公开附录保留紧凑证据映射，Markdown 文本自成一体（PPT 仅是其视觉转译）。

### 4. 报告保护与事实纠错

- **手写保护**：Daily 报告按日期和分组管理写入块。如果检测到人工手改或并发冲突，绝不强行覆盖，而是保留原文并将新草稿返回对话中。部分项目读取失败时同样返回注明缺口的草稿，仅在显式确认时写入文件。
- **事实更正**：若已存事实有误，可对 Capture 说“**更正这条记录**”，提供原记录与正确事实。更正操作保留原始记录并在原工作期间生效；支持指定历史知悉时点（as-of），确保日、周、月报共享一致的修正视图。写入更正后，自动防止降级到忽略更正的旧读取器。

---

## 本地存储与隐私

Tracework 严格践行本地优先（Local-First）与数据主权原则（详见 [数据模型](docs/data-model.md) 与 [产物治理规范](docs/artifact-governance.md)）：

- **配置文件**：`~/.tracework/config.yaml` 或 `{project}/.tracework/config.yaml`
- **原始事实记录（Raw entries）**：`{vault}/raw/weeks/{week}/{slug}.json`（语义真相源）
- **持久产物索引（Artifact dossiers）**：`{vault}/raw/artifacts/{slug}.json`（保存导航与记录边界，不复制完整源文档）
- **人类可读输出**：`{vault}/Daily Note.md` 与 `{vault}/Work Diary/`

可选的 **Capture Day** 机制默认关闭。开启 `session_scan.enabled: true` 后，插件 Hook 仅在 `~/.tracework/session-index/` 保存指针和分组元数据；只有显式执行 `/tracework:capture day` 才会进行本地会话解析，且**绝不将完整对话（Transcript）复制到 Vault 中**。

---

## 本地开发

本项目使用固定映射同步 `canonical → skill-local → bundle`；`check-skills` 只执行只读校验。

```bash
npm --prefix cli run build
npm --prefix cli run copy-skills
npm --prefix cli run check-skills
npm --prefix cli run test
npm --prefix site run build
```

核心文档：[配置指南](docs/configuration.md) · [数据模型](docs/data-model.md) · [产物治理规范](docs/artifact-governance.md)。

---

## 支持项目

如果 Tracework 帮助你把 Agent 工作收口成了更清晰、有证据支撑的进展报告，欢迎支持本项目持续维护：

👉 <https://kkenny0.github.io/support/>

你的支持将用于持续打磨报告质量、维护跨运行时插件体系、演进存储契约与更新文档。

---

## License

MIT
