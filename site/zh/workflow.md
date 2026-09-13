# 工作流

## 主循环

```text
安装
  -> 先试：写周报 / 写日报
  -> 需要跨天累计时：配置 vault 与项目分组
  -> 关键 session 说“收工”
  -> 写日报 / 写周报 / 写月报
  -> 被追问或续作时再下钻
```

1. 安装 `tracework@tracework`。
2. 先直接运行 `/tracework:weekly` 或 `/tracework:daily` 试用；无 vault 时在对话中输出。
3. 需要持久保存与严格分区时，再运行 `/tracework:cold-start-interview`。
4. 关键工作结束时说“收工”，保存动机、风险、取舍和证据边界。
5. 用 `/tracework:daily`、`/tracework:weekly`、`/tracework:monthly` 完成高频收口。
6. 可选启用元数据级 session scan，在每天结束时运行一次
   `/tracework:capture day`，补回遗漏 session。
7. 只有在工作被追问、继续或长周期复盘时，才使用 Query、Recall、Roadmap。

## 用户动作，而不是命令表

| 你怎么说 | 背后能力 |
| :--- | :--- |
| 收工 | capture |
| 写日报 / 写周报 / 写月报 | daily / weekly / monthly |
| 为什么当时这么选 / 接着上次 | query / recall |

完整命令表见 [Skills](./skills)。

## 先分区，再选择主线

```text
work     -> 只包含公司项目
personal -> 只包含个人项目
all      -> 私人视图中按组分别叙事
```

Weekly 会在每个组内先恢复目标来源，再解释实际变化、偏差和下周承诺，不固定
headline 数量。Brief 正文只保留会改变判断、行动或置信度的信息，完整核算、覆盖与
证据进入附录。

## 复用地图

```text
Capture -> raw/weeks/{week}/{slug}.json
Capture Day -> scoped session index + 本地 transcript -> raw entries
Daily   <- raw entries + limited git fallback
Weekly  <- raw entries + limited git fallback
Monthly <- raw entries + Daily/Weekly 人类判断
Query   <- derived decisions + raw entries
Recall  <- raw entries + artifact/decision navigation
Roadmap <- decision evidence pack
```

Raw entries 是语义真相。报告本地证据编号只属于附录，不进入 raw schema 或口头主叙事。

Daily、Weekly、Monthly 也能使用当前对话中范围明确的事实，不会因此自动 Capture
或扫描其他 session。已保存的记录先经过共享更正视图再参与报告；更正在原工作期间
生效，明确指定 as-of 时保留当时的知悉边界。已有报告需要明确请求才会刷新。
