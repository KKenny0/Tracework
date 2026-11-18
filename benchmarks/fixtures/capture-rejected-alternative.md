# Synthetic capture fixture: explicit rejected alternative and chosen design

This is a synthetic session. It contains no real project or user data.

Source line 1, user, 2026-10-21T10:00:00Z:
我们需要优化本地缓存 `cache/lru.go` 在高并发下的锁竞争。请评估环形缓冲区与分段锁两种方案，并在 `DESIGN.md` 记录最终设计。

Source line 2, assistant, 2026-10-21T10:35:00Z:
对比了两种方案：
1. 评估了无锁环形缓冲区方案（Ring Buffer）：但在 10 万条缓存项规模下，随机 Key 驱逐必须做全量扫描，退化为 O(N) 复杂度，无法满足微秒级淘汰延迟要求，因此明确放弃该方案。
2. 选用了 16 分段锁方案（16-shard Striped Mutex）：保留双向链表哈希结构，按 Key 哈希分摊锁竞争。
已在 `DESIGN.md` 中记录该分段锁架构规范。本地微基准测试显示在 32 并发协程下吞吐量提升 3.2 倍。
尚未进行集群分布式同步测试与端到端故障转移演练。
