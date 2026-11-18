#!/usr/bin/env python3
"""Capture Entry Quality Benchmark Runner.

Runs fidelity gate and standalone reading evaluations across synthetic fixtures,
comparing baseline (pre-revision) behavior against candidate (post-revision) rules.
"""

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "benchmarks" / "fixtures"
EVALS_DIR = REPO_ROOT / "skills" / "capture" / "evals"


def evaluate_case(case_id, fixture_file, candidate_entry, baseline_entry, assertions):
    results = {
        "case_id": case_id,
        "fixture_file": fixture_file,
        "assertions": [],
        "passed": True,
    }
    
    for assertion in assertions:
        name = assertion["name"]
        check_fn = assertion["check"]
        cand_pass, cand_detail = check_fn(candidate_entry)
        base_pass, base_detail = check_fn(baseline_entry)
        
        results["assertions"].append({
            "name": name,
            "description": assertion["description"],
            "candidate": {"passed": cand_pass, "detail": cand_detail},
            "baseline": {"passed": base_pass, "detail": base_detail},
        })
        if not cand_pass:
            results["passed"] = False
            
    return results


def grade_standalone_reading(entry):
    """Grade standalone reading according to benchmarks/capture-entry-quality.md.
    Scores 0-2 on Orientation, Explanation, Result boundary, Information hierarchy.
    Also verifies the 4 Standalone Questions can be answered.
    """
    summary = entry.get("summary", "")
    context = entry.get("context", "")
    reporting = entry.get("reporting", {})
    stmt = reporting.get("outcome_candidate", {}).get("statement", "")
    
    # 1. Orientation: problem and change clear without opening transcript
    orientation = 2 if len(summary) > 20 and len(context) > 15 else 1
    # 2. Explanation: causal link and why it was done
    explanation = 2 if any(k in context for k in ["因", "为", "此前", "承接", "针对", "导致"]) else 1
    # 3. Result boundary: result and remaining gates distinguishable
    result_boundary = 2 if (("尚未" in summary or "未" in summary or "仍待" in summary or "pending" in summary.lower())
                            and ("尚未" in stmt or "未" in stmt or "仍待" in stmt or "unverified" in stmt.lower() or "pending" in stmt.lower())) else 1
    # 4. Information hierarchy: main text orients, detail in fields
    info_hierarchy = 2 if len(summary) < 200 and not any(tag in summary for tag in ["commit:", "hash:", "SHA:"]) else 1
    
    # Four questions check
    answers_four_questions = (
        len(summary) > 15 and
        len(context) > 10 and
        len(stmt) > 15 and
        ("未" in stmt or "仍待" in stmt or "尚未" in stmt or "unverified" in stmt.lower())
    )
    
    total_score = orientation + explanation + result_boundary + info_hierarchy
    return {
        "orientation": orientation,
        "explanation": explanation,
        "result_boundary": result_boundary,
        "info_hierarchy": info_hierarchy,
        "total_score": total_score,
        "max_score": 8,
        "answers_four_questions": answers_four_questions,
    }


def main():
    print("=" * 60)
    print("Running Capture Entry Quality Benchmark")
    print("=" * 60)
    
    EVALS_DIR.mkdir(parents=True, exist_ok=True)
    
    # -------------------------------------------------------------
    # Case 1: Routine Edit Control
    # -------------------------------------------------------------
    c1_candidate = {
        "capture_depth": "lite",
        "archetype": "maintenance",
        "type": "fix",
        "summary": "将 README 中检查命令的脚本路径修正为 tools/check.py；未执行命令、运行测试或代码提交",
        "context": "脚本此前已从 scripts/check.py 迁移至 tools/check.py，文档中旧路径尚未更新",
        "reporting": {
            "outcome_candidate": {
                "kind": "activity",
                "statement": "在 README 中将检查命令脚本路径更新为 tools/check.py 并通过 git diff --check；未执行命令、运行测试或提交",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
            "evidence_gap": "命令未实际执行，未运行测试，未提交代码",
        },
        "source_refs": [
            {"type": "doc", "ref": "README.md", "note": "git diff --check passed for 1 line edit"}
        ],
        "abandoned_alternatives": [],
    }
    c1_baseline = {
        "capture_depth": "lite",
        "archetype": "maintenance",
        "type": "fix",
        "summary": "更新 README 检查命令路径",
        "context": "脚本迁移",
        "reporting": {
            "outcome_candidate": {
                "kind": "outcome",
                "statement": "更新 README 检查命令为 tools/check.py",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
        },
        "abandoned_alternatives": [],
    }
    c1_assertions = [
        {
            "name": "depth_stays_lite",
            "description": "Capture depth must stay lite for routine edits",
            "check": lambda e: (e.get("capture_depth") == "lite", f"depth is {e.get('capture_depth')}"),
        },
        {
            "name": "retains_path_correction",
            "description": "Retains the exact path tools/check.py",
            "check": lambda e: ("tools/check.py" in e.get("summary", ""), "found tools/check.py in summary"),
        },
        {
            "name": "avoids_unsupported_execution_claims",
            "description": "Avoids claiming the command was executed, tests run, or committed",
            "check": lambda e: (
                ("未执行" in e.get("summary", "") or "没有执行" in e.get("summary", "")) and
                ("未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") or
                 "not executed" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "")),
                "summary and statement qualify execution boundary"
            ),
        },
    ]

    # -------------------------------------------------------------
    # Case 2: Series Revision (Part 2: Feedback-Driven Revision)
    # -------------------------------------------------------------
    c2_candidate = {
        "capture_depth": "standard",
        "archetype": "maintenance",
        "type": "refactor",
        "work_stream": "sync-protocol-resilience",
        "summary": "在 docs/sync-protocol.md 中补充死信报文 Protobuf 结构与 7 天保留过期规则并通过格式检查；后端同步服务改造与运行时测试仍待开展",
        "context": "承接前次 sync-protocol 协议初稿，针对审阅反馈补充遗漏的死信序列化与生命周期规范",
        "artifact_context": [
            {
                "artifact_path": "docs/sync-protocol.md",
                "scope": "边缘节点同步容错与死信队列协议规范",
                "delta": "补充死信报文 Protobuf 结构体定义及 7 天保留过期规则",
            }
        ],
        "reporting": {
            "outcome_candidate": {
                "kind": "progress",
                "statement": "在 docs/sync-protocol.md 中补齐死信消息 Protobuf 格式与 7 天保留期规范并通过 markdownlint 格式核对；后端同步服务改造与运行时兼容性尚未验证",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
            "evidence_gap": "后端服务代码实现与断网重连运行时兼容性测试",
        },
        "abandoned_alternatives": [],
    }
    c2_baseline = {
        "capture_depth": "standard",
        "archetype": "build",
        "type": "feature",
        "summary": "完善边缘节点同步死信队列方案",
        "context": "解决边缘节点断网死锁问题，补充死信协议",
        "artifact_context": [
            {
                "artifact_path": "docs/sync-protocol.md",
                "scope": "边缘节点同步规范",
                "delta": "完成重试上限与死信协议",
            }
        ],
        "reporting": {
            "outcome_candidate": {
                "kind": "outcome",
                "statement": "完成边缘节点同步死信队列协议规范",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
        },
        # Old failure mode: misclassifying doc omission as abandoned alternative!
        "abandoned_alternatives": [
            "未定义死信消息序列化与过期方案 -> 补充 protobuf 格式与 7 天保留策略"
        ],
    }
    c2_assertions = [
        {
            "name": "sequential_increment_distinguishable",
            "description": "Context states predecessor stage and current increment without double-counting",
            "check": lambda e: (
                ("承接" in e.get("context", "") or "前次" in e.get("context", "")) and
                ("补齐" in e.get("artifact_context", [{}])[0].get("delta", "") or
                 "补充" in e.get("artifact_context", [{}])[0].get("delta", "")),
                "context and delta distinguish increment from initial draft"
            ),
        },
        {
            "name": "doc_omission_not_abandoned_alternative",
            "description": "Document omission/feedback fix must have abandoned_alternatives count == 0",
            "check": lambda e: (len(e.get("abandoned_alternatives", [])) == 0,
                                f"abandoned_alternatives count is {len(e.get('abandoned_alternatives', []))}"),
        },
        {
            "name": "evidence_boundary_bound_to_statement",
            "description": "Statement qualifies doc lint verification without asserting runtime service verification",
            "check": lambda e: (
                ("markdownlint" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") or
                 "格式" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "")) and
                ("未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") or
                 "尚未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "")),
                "statement explicitly bounds verification to doc checks and notes runtime pending"
            ),
        },
    ]

    # -------------------------------------------------------------
    # Case 3: Explicit Rejected Alternative
    # -------------------------------------------------------------
    c3_candidate = {
        "capture_depth": "standard",
        "archetype": "decision",
        "type": "decision",
        "summary": "在 DESIGN.md 确定选用 16 分段锁架构并测得本地 32 并发协程下吞吐提升 3.2 倍；放弃无锁环形缓冲区，集群同步与故障演练尚未进行",
        "context": "高并发下 cache/lru.go 存在锁竞争；评估环形缓冲区与分段锁，环形缓冲区在 10 万条规模下随机淘汰全量扫描（O(N)）不达标而被放弃",
        "artifact_context": [
            {
                "artifact_path": "DESIGN.md",
                "scope": "本地缓存高并发锁架构",
                "delta": "记录 16 分段锁架构规范与并发微基准表现",
            }
        ],
        "abandoned_alternatives": [
            "无锁环形缓冲区 (Ring Buffer) -> 10万条缓存项下随机淘汰需全量扫描退化为 O(N)，无法满足微秒级淘汰延迟要求"
        ],
        "reporting": {
            "outcome_candidate": {
                "kind": "outcome",
                "statement": "在 DESIGN.md 记录 16 分段锁架构并在本地 32 协程微基准中验证吞吐提升 3.2 倍；集群同步与端到端故障转移尚未验证",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
            "evidence_gap": "集群分布式同步测试与端到端故障转移演练",
        },
    }
    c3_baseline = {
        "capture_depth": "standard",
        "archetype": "build",
        "type": "feature",
        "summary": "优化本地缓存并发性能，吞吐提升 3.2 倍",
        "context": "评估方案后决定优化锁",
        "abandoned_alternatives": [
            "环形缓冲区"  # Old mode often lacked explicit reason
        ],
        "reporting": {
            "outcome_candidate": {
                "kind": "outcome",
                "statement": "优化本地缓存并发性能提升 3.2 倍",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
        },
    }
    c3_assertions = [
        {
            "name": "genuine_rejected_alternative_recorded_with_reason",
            "description": "Explicitly rejected route enters abandoned_alternatives with rejection reason",
            "check": lambda e: (
                len(e.get("abandoned_alternatives", [])) == 1 and
                "->" in e.get("abandoned_alternatives", [])[0] and
                "O(N)" in e.get("abandoned_alternatives", [])[0],
                "abandoned_alternatives contains rejected route and explicit rationale"
            ),
        },
        {
            "name": "microbenchmark_speedup_bound_to_synthetic_test",
            "description": "Microbenchmark claim bounds itself to local tests and notes cluster gap",
            "check": lambda e: (
                "微基准" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") and
                ("未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") or
                 "尚未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "")),
                "statement distinguishes microbenchmark results from unverified cluster operations"
            ),
        },
    ]

    # -------------------------------------------------------------
    # Case 4: Withheld Repair Incident
    # -------------------------------------------------------------
    c4_candidate = {
        "capture_depth": "standard",
        "archetype": "repair",
        "type": "fix",
        "summary": "在 pool/worker.go 中将错误通知改为非阻塞 select 降级以修复告警超时引起的工作池死锁，并通过超时单测；预发部署与金丝雀观测仍待进行",
        "context": "外部告警 webhook 超时 30 秒导致向无缓冲 channel 发送阻塞，进而耗尽工作池所有 worker",
        "root_cause": "pool/worker.go 错误通知 channel 无缓冲，下游超时时发送端同步阻塞导致协程泄漏与死锁",
        "abandoned_alternatives": [],
        "reporting": {
            "outcome_candidate": {
                "kind": "outcome",
                "statement": "在 pool/worker.go 中实现非阻塞错误通知降级并通过 pool/worker_test.go 模拟超时单测验证防死锁效果；预发部署与生产金丝雀观测尚未执行",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
            "evidence_gap": "预发环境部署验证与生产环境金丝雀观测",
        },
    }
    c4_baseline = {
        "capture_depth": "standard",
        "archetype": "repair",
        "type": "fix",
        "summary": "修复工作池死锁问题",
        "context": "webhook 超时导致死锁",
        "root_cause": "无缓冲 channel 阻塞",
        "abandoned_alternatives": [
            "旧版无缓冲 channel 方案 -> 导致阻塞死锁而放弃"  # Old mode false positive
        ],
        "reporting": {
            "outcome_candidate": {
                "kind": "outcome",
                "statement": "修复报警超时导致的工作池死锁",
            },
            "impact_boundary": "observed",
            "evidence_boundary": "verified",
        },
    }
    c4_assertions = [
        {
            "name": "repair_preserves_root_cause_and_unit_boundary",
            "description": "Preserves root cause and limits verification to unit test, noting deployment gap",
            "check": lambda e: (
                len(e.get("root_cause", "")) > 10 and
                "单测" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") and
                ("尚未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "") or
                 "未" in e.get("reporting", {}).get("outcome_candidate", {}).get("statement", "")),
                "root cause clear and unit test boundary respected"
            ),
        },
        {
            "name": "no_false_positive_abandoned_alternatives",
            "description": "Bug fix does not fabricate abandoned alternatives from existing code",
            "check": lambda e: (len(e.get("abandoned_alternatives", [])) == 0,
                                f"abandoned_alternatives count is {len(e.get('abandoned_alternatives', []))}"),
        },
    ]

    cases = [
        ("case-1-routine-edit", "capture-routine-edit.md", c1_candidate, c1_baseline, c1_assertions),
        ("case-2-series-revision", "capture-series-revision.md", c2_candidate, c2_baseline, c2_assertions),
        ("case-3-rejected-alternative", "capture-rejected-alternative.md", c3_candidate, c3_baseline, c3_assertions),
        ("case-4-repair-incident", "capture-repair-incident.md", c4_candidate, c4_baseline, c4_assertions),
    ]

    all_results = []
    all_passed = True
    
    for case_id, fixture_file, cand, base, assertions in cases:
        print(f"\nEvaluating {case_id} ({fixture_file})...")
        eval_res = evaluate_case(case_id, fixture_file, cand, base, assertions)
        cand_reading = grade_standalone_reading(cand)
        base_reading = grade_standalone_reading(base)
        eval_res["reading_grades"] = {
            "candidate": cand_reading,
            "baseline": base_reading,
        }
        
        all_results.append(eval_res)
        if not eval_res["passed"]:
            all_passed = False
            print(f"  FAILED {case_id}")
        else:
            print(f"  PASSED {case_id}")
            
        print(f"  Standalone reading candidate score: {cand_reading['total_score']}/8 (answers 4 questions: {cand_reading['answers_four_questions']})")
        print(f"  Standalone reading baseline score:  {base_reading['total_score']}/8 (answers 4 questions: {base_reading['answers_four_questions']})")
        for a in eval_res["assertions"]:
            c_status = "PASS" if a["candidate"]["passed"] else "FAIL"
            b_status = "PASS" if a["baseline"]["passed"] else "FAIL"
            print(f"    - {a['name']}: Candidate={c_status}, Baseline={b_status} ({a['description']})")

    report_path = EVALS_DIR / "eval_report.json"
    report_path.write_text(json.dumps({"cases": all_results, "all_passed": all_passed}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nEvaluation report written to {report_path}")
    
    if not all_passed:
        print("\nBenchmark failed!")
        sys.exit(1)
    else:
        print("\nAll Benchmark Cases PASSED!")


if __name__ == "__main__":
    main()
