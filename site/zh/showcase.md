---
title: 效果展示
description: Tracework 的输出形态、前后对比与证据边界。
---

# 效果展示

这个页面会刻意保守：先给你一份能感觉到差别的样本，再说明证据边界。
**下面的前后对比是 fixture**（按 weekly brief 合同构造，主题取自公开产品能力：
周报三档、首日 local 试用、capture 回执）。它不是私有 vault 导出，也不假装成
已验证的客户成功案例。

## 前后对比

### Before：纯 git / 随手周报

```text
本周工作：
- 改了 weekly skill
- 更新 README 和文档站
- 修了 cold-start 文案
- capture 回执调整
- 跑了测试

下周继续优化。
```

读感：像活动清单。看不出本周真正改变了什么、还差哪道门、哪些话站得住。

### After：Tracework weekly brief（fixture）

```markdown
# 2026-W30 工作汇报

**日期：** 2026-07-20 ~ 2026-07-22
**范围：** work

## 本周判断

周初产品入口仍偏“系统说明”，未配置时也容易在默认 work 范围下空报。本周把定位
收成“有证据的进展报告”，并补齐周报三档、首日 local 试用和 capture 回执前瞻。
当前文档与 skill 合同已对齐；还差真实宿主会话冒烟和 showcase 样本门槛。

## 结果弧线

### 对外主句与试用路径对齐

- **周初约束：** 新用户先看到完整系统，cold-start 像门票
- **关键转折：** 主句改为“收口成有证据的进展报告”，quick-start 改为先试写周报
- **周末状态：** README / 文档站 / 插件描述使用同一主句；安装后可先出报告
- **管理意义：** 降低理解成本，把价值点前移到第一次成功
- **剩余门槛：** 插件市场文案随版本发布后的实际展示仍待核对
- **证据边界：** recorded（文档与插件清单已改）；宿主市场页未在本 fixture 中复核

### 周报拆成 quick / brief / slides

- **周初约束：** 普通周报也背负 PPT 逻辑图与实施叙事重规则
- **关键转折：** 路由为三档；重规则仅 slides
- **周末状态：** 「这周做了啥」对话快览；默认 brief；明确 PPT 才出大纲
- **管理意义：** 日常收口变轻，汇报场景仍可加深
- **剩余门槛：** agent 选档依赖 skill 合同，尚无自动化回归断言
- **证据边界：** recorded（skill 与站点 skills 页已同步）

### 未配置项目可 local 试用且不串 work

- **周初约束：** 默认 work 会排除 unassigned，裸仓库第一次常为空
- **关键转折：** 区分 explicit / configured / implicit；implicit 走 local
- **周末状态：** 无 vault 可对话输出；显式 work 仍排除未分组并提示修复
- **管理意义：** 先试用、后配置；公司分区安全保留
- **剩余门槛：** 需在真实无配置环境再冒烟一次
- **证据边界：** recorded（skill + narrative contract）；runtime 冒烟未计入 verified

## 工作组合状态

| 工作主线 | 状态 | 本周形成的变化 | 与主线关系 | 需要关注 |
|----------|------|----------------|------------|----------|
| Capture 回执前瞻句 | done | 收工后提示可进入本周报告候选 | supporting | 无 |
| 站点 quick-start / workflow | done | 与 try-first 叙事一致 | supporting | 无 |
| 版本号 bump | done | 插件清单已升到 0.6.0 | supporting | 发布时再推市场安装 |

## 下周收口目标

1. **Showcase 门槛：** 公开样本必须标 fixture 或脱敏真实 run
2. **宿主冒烟：** 无 vault「写周报」与「这周做了啥」各跑通一次
3. **发版同步：** 需要用户可见发布时再统一 bump 版本

## 证据边界（摘要）

- raw / skill 合同改动：recorded
- git-only 维护项：limited，不升格为成果
- 未做的宿主安装冒烟：显式列为剩余门槛，不编造成已验证
```

### 怎么读这份 After

| 读点 | 说明 |
| :--- | :--- |
| 比 Before 强在哪 | 有**本周判断**、状态变化主线、下一道门，不是 commit 罗列 |
| `recorded` | 本地记录了决策/改动，但还没有独立验证物证明“线上已生效” |
| `limited` | 主要来自 git 覆盖或信号不足；不能编动机、不能当已验证成果 |
| 记录中的理由 | 例如“为什么 brief 不要求逻辑图”“为什么 unassigned 不能进 work” |
| 没有编造的部分 | 宿主冒烟、市场页展示等未完成项保留在门槛里，而不是写成已完成 |

30 秒对照：Before 回答“忙了什么”；After 回答“局面怎么变了、依据到哪、下一步卡什么”。

## 输出形态

| Surface | 应该展示什么 | 证据边界 |
| :--- | :--- | :--- |
| Capture | 路由深度、目标、决策、放弃路径、风险、证据、下一步；vault 回执含报告前瞻句 | 捕获记录本身不是独立 proof |
| Weekly | quick / brief / slides 三档；默认 brief | PPT 重规则只在 slides；git-only 保持 limited |
| Monthly | Raw-first 阶段叙事、反复风险、下月收口目标 | 计数留在 coverage，不升格成 outcome |

## 示例 Claim Chain

```text
O1 成果或进展
  W1 支撑它的工作主线
    D1 决策或取舍
      E1 raw entry 或 evidence reference
```

这条 chain 只在报告内部成立。它帮助读者从 brief 向下回到证据，但不会改写 raw
data。

## 真实输出门槛

继续往这个页面加 case 时，仍须确认：

- 来源是真实 Tracework run，或**明确标注为 fixture**
- 私有路径和专有细节已经移除
- `source_entry_refs` 被描述为 provenance，而不是自动 verification
- 每个 outcome claim 都有独立证据，或者有明确可见的限制
- 核心机制页覆盖主路径、关键分支或回退、输出与不变量，不把图的结构当作效果证据
- 普通维护工作保留在 portfolio coverage 中，不生成装饰性架构图
- 证据不足的报告主张会标明 evidence gap

## Commands

| Command | 用途 |
| :--- | :--- |
| `/tracework:capture` | 捕获 session 记录；vault 模式带回执前瞻 |
| `/tracework:daily` | 日报收口；可无 vault 试用 |
| `/tracework:weekly` | 默认 brief；`这周做了啥` 为 quick；明确 PPT 为 slides |
| `/tracework:monthly` | 月度 review |
| `/tracework:cold-start-interview` | 配置 vault、项目身份与报告分组 |
