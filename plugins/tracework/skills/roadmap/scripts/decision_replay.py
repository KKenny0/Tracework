#!/usr/bin/env python3
"""Build a Decision Replay Index from Tracework raw entries.

The index is derived from weekly raw entries only. Artifact metadata may help
connect entries, but it must not create decision facts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

from tracework_raw import write_json_atomic

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


SCHEMA_VERSION = "tracework.decision_replay.v1"
QUERY_SCHEMA_VERSION = "tracework.decision_query.v1"
ROADMAP_SCHEMA_VERSION = "tracework.decision_roadmap.v1"
INDEX_BUILDER_VERSION = 3
SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
EXPLICIT_FIELDS = (
    "motivation",
    "exploration_paths",
    "abandoned_alternatives",
    "open_questions",
)
STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "before",
    "between",
    "build",
    "built",
    "changed",
    "changes",
    "choose",
    "context",
    "decision",
    "did",
    "during",
    "entry",
    "for",
    "from",
    "have",
    "how",
    "into",
    "needed",
    "project",
    "rather",
    "replaced",
    "session",
    "should",
    "source",
    "that",
    "the",
    "their",
    "there",
    "these",
    "this",
    "through",
    "using",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "why",
    "with",
    "without",
}
CJK_QUERY_BOILERPLATE_RE = re.compile(
    r"为什么|为何|怎么|什么|是否|当时|我们|这个|那个|请问"
)
CJK_RUN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


def load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError(f"config is not a mapping: {path}")
        return data
    return parse_simple_yaml(raw)


def parse_simple_yaml(raw: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if not value or value in {"|", ">"}:
            continue
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        result[key.strip()] = value
    return result


def find_project_config(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for directory in (current, *current.parents):
        candidate = directory / ".tracework" / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def merge_configs(global_cfg: dict[str, Any], project_cfg: dict[str, Any]) -> dict[str, Any]:
    merged = dict(global_cfg)
    for key, value in project_cfg.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def resolve_config(cwd: Path) -> tuple[dict[str, Any], list[str]]:
    sources: list[str] = []
    global_path = Path.home() / ".tracework" / "config.yaml"
    project_path = find_project_config(cwd)

    global_cfg = load_yaml_config(global_path)
    if global_cfg:
        sources.append(str(global_path))

    project_cfg: dict[str, Any] = {}
    if project_path is not None:
        project_cfg = load_yaml_config(project_path)
        sources.append(str(project_path))

    cfg = merge_configs(global_cfg, project_cfg)

    if cfg.get("knowledge_vault"):
        cfg["knowledge_vault"] = str(Path(cfg["knowledge_vault"]).expanduser().resolve())
    sources = dedupe(sources)
    return cfg, sources


def slugify(value: str) -> str:
    slug = re.sub(r"[\s_]+", "-", value.strip().lower())
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "project"


def validate_project_slug(slug: str) -> str:
    if not SAFE_SLUG_RE.fullmatch(slug):
        raise ValueError(
            "project slug must be a filename-safe value using letters, numbers, dots, underscores, or hyphens"
        )
    return slug


def same_path(left: str, right: Path) -> bool:
    left_path = Path(left).expanduser()
    right_path = right.expanduser()
    try:
        return left_path.resolve() == right_path.resolve()
    except OSError:
        return left_path.absolute() == right_path.absolute()


def project_slug(cwd: Path, vault: Path, configured: Any = None) -> str:
    if isinstance(configured, str) and configured.strip():
        return validate_project_slug(configured.strip())

    projects_file = vault / "raw" / "projects.json"
    if projects_file.exists():
        try:
            projects = json.loads(projects_file.read_text(encoding="utf-8"))
            if isinstance(projects, list):
                for project in projects:
                    if not isinstance(project, dict):
                        continue
                    path_value = project.get("path")
                    slug_value = project.get("slug")
                    if isinstance(path_value, str) and isinstance(slug_value, str):
                        if same_path(path_value, cwd):
                            return validate_project_slug(slug_value)
        except json.JSONDecodeError:
            pass

    return validate_project_slug(slugify(cwd.resolve().name))


def load_json_array(path: Path) -> list[Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"expected JSON array or object: {path}")


def load_raw_entries(vault: Path, slug: str) -> tuple[list[dict[str, Any]], list[str]]:
    root = vault / "raw" / "weeks"
    if not root.exists():
        return [], []

    entries: list[dict[str, Any]] = []
    source_paths: list[str] = []
    for path in sorted(root.glob(f"*/{slug}.json")):
        raw_entries = load_json_array(path)
        source_paths.append(str(path))
        week = path.parent.name
        for index, entry in enumerate(raw_entries):
            if not isinstance(entry, dict):
                continue
            item = dict(entry)
            item["_source_path"] = str(path)
            item["_source_week"] = week
            item["_source_index"] = index
            entries.append(item)

    entries.sort(key=entry_sort_key)
    return entries, source_paths


def entry_sort_key(entry: dict[str, Any]) -> tuple[str, str, int]:
    timestamp = entry.get("timestamp")
    if not isinstance(timestamp, str):
        timestamp = ""
    return (timestamp, str(entry.get("_source_week", "")), int(entry.get("_source_index", 0)))


def load_artifacts(vault: Path, slug: str) -> tuple[list[dict[str, Any]], str | None]:
    path = vault / "raw" / "artifacts" / f"{slug}.json"
    if not path.exists():
        return [], None
    artifacts = [item for item in load_json_array(path) if isinstance(item, dict)]
    return artifacts, str(path)


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def as_object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def as_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return dict(value)
    return None


def text_value(entry: dict[str, Any], field: str) -> str | None:
    value = entry.get(field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def has_explicit_decision_signal(entry: dict[str, Any]) -> bool:
    if entry.get("type") == "decision" or entry.get("archetype") == "decision":
        return True
    if as_string_list(entry.get("decision_threads")):
        return True
    return any(as_string_list(entry.get(field)) or text_value(entry, field) for field in EXPLICIT_FIELDS)


def stable_entry_id(slug: str, entry: dict[str, Any]) -> str:
    return f"raw:{slug}:{entry['_source_week']}:{entry['_source_index']}"


def entry_ref(entry: dict[str, Any], slug: str) -> dict[str, Any]:
    return {
        "entry_id": stable_entry_id(slug, entry),
        "week": entry["_source_week"],
        "path": entry["_source_path"],
        "timestamp": entry.get("timestamp"),
        "entry_index": entry["_source_index"],
    }


def artifact_refs_from_entry(entry: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend(as_string_list(entry.get("related_docs")))
    for context in entry.get("artifact_context", []):
        if not isinstance(context, dict):
            continue
        artifact_path = context.get("artifact_path")
        if isinstance(artifact_path, str) and artifact_path.strip():
            refs.append(artifact_path.strip())
        refs.extend(as_string_list(context.get("source_of_truth")))
    return dedupe(refs)


def direct_artifact_refs_from_entry(entry: dict[str, Any]) -> list[str]:
    """Return only artifact refs explicitly marked as source-of-truth evidence."""
    refs: list[str] = []
    for context in entry.get("artifact_context", []):
        if not isinstance(context, dict):
            continue
        refs.extend(as_string_list(context.get("source_of_truth")))
    return dedupe(refs)


def artifact_hints_for_entry(
    entry: dict[str, Any], artifacts: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    entry_refs = set(artifact_refs_from_entry(entry))
    if not entry_refs:
        return [], []

    artifact_ids: list[str] = []
    thread_hints: list[str] = []
    for artifact in artifacts:
        artifact_path = artifact.get("path")
        repo_path = artifact.get("repo_relative_path")
        candidates = [item for item in (artifact_path, repo_path, artifact.get("id")) if isinstance(item, str)]
        if not entry_refs.intersection(candidates):
            continue
        artifact_id = artifact.get("id")
        if isinstance(artifact_id, str) and artifact_id.strip():
            artifact_ids.append(artifact_id.strip())
        thread_hints.extend(as_string_list(artifact.get("decision_threads")))
        thread_hints.extend(as_string_list(artifact.get("topics")))
    return dedupe(artifact_ids), dedupe(thread_hints)


def keyword_tokens(text: str) -> list[str]:
    tokens = [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())
        if token not in STOPWORDS and not token.isdigit()
    ]
    return dedupe(tokens)


def cjk_lexical_tokens(text: str) -> list[str]:
    """Return deterministic CJK bigrams/trigrams without a tokenizer dependency."""
    normalized = CJK_QUERY_BOILERPLATE_RE.sub(" ", text)
    tokens: list[str] = []
    for run in CJK_RUN_RE.findall(normalized):
        for size in (2, 3):
            if len(run) < size:
                continue
            tokens.extend(run[index : index + size] for index in range(len(run) - size + 1))
    return dedupe(tokens)


def lexical_tokens(text: str) -> list[str]:
    return dedupe([*keyword_tokens(text), *cjk_lexical_tokens(text)])


def topic_key(value: str) -> str:
    """Return a stable readable key for either Latin or CJK topic text."""
    latin = slugify(value)
    if latin != "project" or not CJK_RUN_RE.search(value):
        return latin
    cjk = cjk_lexical_tokens(value)
    return "-".join(cjk[:3]) or "project"


def search_tokens(text: str) -> set[str]:
    tokens = set(lexical_tokens(text))
    for token in list(tokens):
        if "-" not in token or token.startswith("re-"):
            continue
        for part in token.split("-"):
            if len(part) >= 3 and part not in STOPWORDS and not part.isdigit():
                tokens.add(part)
    return tokens


def topic_keys(entry: dict[str, Any], artifact_thread_hints: list[str]) -> list[str]:
    keys: list[str] = []
    keys.extend(topic_key(item) for item in as_string_list(entry.get("decision_threads")))
    for field in ("project_area", "work_stream"):
        value = text_value(entry, field)
        if value:
            keys.append(topic_key(value))
    keys.extend(topic_key(item) for item in artifact_thread_hints)
    for context in entry.get("artifact_context", []):
        if not isinstance(context, dict):
            continue
        for field in ("scope", "delta"):
            value = text_value(context, field)
            if value:
                keys.extend(lexical_tokens(value)[:4])
    keys.extend(lexical_tokens(" ".join([str(entry.get("summary", "")), str(entry.get("context", ""))]))[:6])
    return dedupe([key for key in keys if key])


def thread_id_for(keys: list[str], entry: dict[str, Any]) -> str:
    for key in keys:
        if key:
            return f"thread:{topic_key(key)}"
    summary = text_value(entry, "summary") or f"entry-{entry.get('_source_index', 0)}"
    words = lexical_tokens(summary)
    fallback = "-".join(words[:3]) or f"entry-{entry.get('_source_index', 0)}"
    return f"thread:{fallback[:48]}"


def merge_suggestions(thread_ids: list[str], threshold: float = 0.7) -> list[dict[str, Any]]:
    """Return merge suggestions for similar thread_id values.

    Two threads are candidates when they share a common word (token Jaccard >= 0.5)
    OR their SequenceMatcher ratio is >= threshold. Returns advisory hints only —
    never auto-merges threads.
    """
    if len(thread_ids) < 2:
        return []

    def _tokens(tid: str) -> set[str]:
        name = tid.removeprefix("thread:")
        parts: set[str] = set()
        for token in name.split("-"):
            token = token.strip()
            if len(token) >= 2 and token not in STOPWORDS:
                parts.add(token)
        return parts

    suggestions: list[dict[str, Any]] = []
    unique = sorted(set(tid for tid in thread_ids if tid))
    for i, left in enumerate(unique):
        left_tokens = _tokens(left)
        if not left_tokens:
            continue
        for right in unique[i + 1 :]:
            right_tokens = _tokens(right)
            shared = left_tokens & right_tokens
            if not shared:
                continue
            jaccard = len(shared) / len(left_tokens | right_tokens)
            seq_ratio = difflib.SequenceMatcher(None, left, right).ratio()
            if jaccard >= 0.5 or seq_ratio >= threshold:
                suggestions.append(
                    {
                        "thread_a": left,
                        "thread_b": right,
                        "reason": (
                            f"shared_tokens={sorted(shared)}, "
                            f"jaccard={jaccard:.2f}, "
                            f"seq_ratio={seq_ratio:.2f}"
                        ),
                        "suggested_merge": _shorter_or_clearer(left, right),
                    }
                )
    return suggestions


def _shorter_or_clearer(a: str, b: str) -> str:
    """Prefer the more specific thread_id between two similar slugs."""
    name_a = a.removeprefix("thread:")
    name_b = b.removeprefix("thread:")
    if len(name_a) > len(name_b):
        return a
    return b


def chosen_path(entry: dict[str, Any]) -> str | None:
    paths = as_string_list(entry.get("exploration_paths"))
    chosen_markers = (
        "chosen",
        "selected",
        "adopted",
        "kept",
        "switched to",
        "replaced",
        "use ",
        "using ",
    )
    chosen = [path for path in paths if any(marker in path.lower() for marker in chosen_markers)]
    if chosen:
        return chosen[0]
    if has_explicit_decision_signal(entry) and text_value(entry, "summary"):
        return text_value(entry, "summary")
    return None


def split_option_reason(value: str) -> dict[str, str]:
    for separator in (" -> ", ": ", " because ", " — ", " - "):
        if separator in value:
            option, reason = value.split(separator, 1)
            return {"option": option.strip(), "reason": reason.strip()}
    return {"option": value.strip(), "reason": ""}


def rejected_paths(entry: dict[str, Any]) -> list[dict[str, str]]:
    rejected = as_string_list(entry.get("abandoned_alternatives"))
    for path in as_string_list(entry.get("exploration_paths")):
        lowered = path.lower()
        if any(marker in lowered for marker in ("rejected", "abandoned", "did not", "deferred")):
            rejected.append(path)
    return [split_option_reason(item) for item in dedupe(rejected)]


def node_from_entry(
    entry: dict[str, Any], slug: str, artifacts: list[dict[str, Any]]
) -> dict[str, Any]:
    artifact_ids, artifact_thread_hints = artifact_hints_for_entry(entry, artifacts)
    artifact_refs = dedupe([*artifact_refs_from_entry(entry), *artifact_ids])
    direct_artifact_refs = direct_artifact_refs_from_entry(entry)
    keys = topic_keys(entry, artifact_thread_hints)
    explicit = has_explicit_decision_signal(entry)
    why = text_value(entry, "motivation") or text_value(entry, "context")
    week = str(entry.get("_source_week", "unknown-week"))
    decision_threads = as_string_list(entry.get("decision_threads"))
    source_refs = as_object_list(entry.get("source_refs"))
    lifecycle_transition = as_object(entry.get("lifecycle_transition"))
    reporting = as_object(entry.get("reporting")) or {}
    boundary = reporting.get("evidence_boundary", "recorded")
    if not explicit or not isinstance(boundary, str) or boundary not in {"verified", "recorded", "limited"}:
        boundary = "limited"
    impact_boundary = reporting.get("impact_boundary", "unknown")
    if not isinstance(impact_boundary, str) or impact_boundary not in {"observed", "expected", "unknown"}:
        impact_boundary = "unknown"
    inference_notes = []
    if not explicit:
        inference_notes.append("Decision content inferred from summary/context because explicit decision fields were sparse.")
    node = {
        "id": stable_entry_id(slug, entry),
        "timestamp": entry.get("timestamp"),
        "week": week,
        "entry_type": entry.get("type"),
        "archetype": entry.get("archetype"),
        "status": entry.get("status"),
        "confidence": "explicit" if explicit else "inferred",
        "source_entry_refs": [entry_ref(entry, slug)],
        "evidence_boundary": boundary,
        "impact_boundary": impact_boundary,
        "evidence_gap": reporting.get("evidence_gap"),
        "summary": text_value(entry, "summary") or "Untitled raw entry",
        "decision": text_value(entry, "summary") or "Untitled raw entry",
        "why": why,
        "chosen": chosen_path(entry),
        "rejected": rejected_paths(entry),
        "open_questions": as_string_list(entry.get("open_questions")),
        "impact": text_value(entry, "impact"),
        "decision_threads": decision_threads,
        "lifecycle_transition": lifecycle_transition,
        "topic_keys": keys,
        "artifact_refs": artifact_refs,
        "direct_artifact_refs": direct_artifact_refs,
        "evidence_refs": as_string_list(entry.get("evidence_refs")),
        "source_refs": source_refs,
        "thread_id": thread_id_for(keys, entry),
        "inference_notes": inference_notes,
    }
    if boundary == "verified" and not has_direct_evidence(node):
        node["evidence_boundary"] = "recorded"
    return node


def build_nodes(
    entries: list[dict[str, Any]], slug: str, artifacts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry.get("summary"), str) or not isinstance(entry.get("context"), str):
            continue
        nodes.append(node_from_entry(entry, slug, artifacts))
    return nodes


def shared_values(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left).intersection(right))


def build_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    by_thread: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        by_thread.setdefault(str(node["thread_id"]), []).append(node)
    for thread_id, thread_nodes in by_thread.items():
        if len(thread_nodes) < 2:
            continue
        for left, right in zip(thread_nodes, thread_nodes[1:]):
            key = (left["id"], right["id"], "same_thread")
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "id": f"edge:{len(edges) + 1:04d}",
                    "from": left["id"],
                    "to": right["id"],
                    "type": "same_thread",
                    "confidence": "heuristic",
                    "reason": f"Consecutive entries in {thread_id}.",
                    "evidence_refs": [left["source_entry_refs"][0], right["source_entry_refs"][0]],
                }
            )

    for index, left in enumerate(nodes):
        for right in nodes[index + 1 :]:
            shared_artifacts = shared_values(left.get("artifact_refs", []), right.get("artifact_refs", []))
            if not shared_artifacts:
                continue
            key = (left["id"], right["id"], "touches_artifact")
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "id": f"edge:{len(edges) + 1:04d}",
                    "from": left["id"],
                    "to": right["id"],
                    "type": "touches_artifact",
                    "confidence": "heuristic",
                    "reason": "Entries reference shared artifact(s): " + ", ".join(shared_artifacts[:3]),
                    "artifact_refs": shared_artifacts,
                    "evidence_refs": [left["source_entry_refs"][0], right["source_entry_refs"][0]],
                }
            )

    return edges


def current_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_datetime(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def latest_entry_datetime(entries: list[dict[str, Any]]) -> dt.datetime | None:
    parsed = [item for item in (parse_datetime(entry.get("timestamp")) for entry in entries) if item is not None]
    return max(parsed) if parsed else None


def input_fingerprint(entries: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> str:
    payload = json.dumps([entries, artifacts], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def missing_raw_sources(index: dict[str, Any], entries: list[dict[str, Any]], paths: list[str]) -> bool:
    source = as_object(index.get("source")) or {}
    expected = {(Path(p).parent.name, Path(p).name) for p in as_string_list(source.get("raw_paths"))}
    present = {(Path(p).parent.name, Path(p).name) for p in paths}
    count = source.get("raw_entry_count", len(as_object_list(index.get("nodes"))))
    positions = {(entry['_source_week'], entry['_source_index']) for entry in entries}
    missing_positions = any(
        (ref.get('week'), ref.get('entry_index')) not in positions
        for node in as_object_list(index.get('nodes'))
        for ref in as_object_list(node.get('source_entry_refs'))
        if isinstance(ref.get('week'), str) and isinstance(ref.get('entry_index'), int)
    )
    return bool(expected - present) or missing_positions or (isinstance(count, int) and count > len(entries))


def index_is_current(index: dict[str, Any], entries: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> bool:
    source = index.get("source")
    if not isinstance(source, dict) or source.get("builder_version") != INDEX_BUILDER_VERSION:
        return False
    raw_entry_count = source.get("raw_entry_count")
    if isinstance(raw_entry_count, int) and raw_entry_count != len(entries):
        return False
    if source.get("input_fingerprint") != input_fingerprint(entries, artifacts):
        return False
    latest_entry = latest_entry_datetime(entries)
    if latest_entry is None:
        return True
    generated_at = parse_datetime(index.get("generated_at"))
    return generated_at is not None and generated_at >= latest_entry


def build_index(vault: Path, slug: str, generated_at: str | None = None) -> dict[str, Any]:
    slug = validate_project_slug(slug)
    entries, raw_paths = load_raw_entries(vault, slug)
    artifacts, artifact_path = load_artifacts(vault, slug)
    nodes = build_nodes(entries, slug, artifacts)
    edges = build_edges(nodes)
    all_thread_ids = [str(n.get("thread_id", "")) for n in nodes]
    thread_merge_hints = merge_suggestions(dedupe(all_thread_ids))
    source: dict[str, Any] = {
        "kind": "roadmap",
        "builder_version": INDEX_BUILDER_VERSION,
        "input_fingerprint": input_fingerprint(entries, artifacts),
        "raw_entry_count": len(entries),
        "raw_glob": str(vault / "raw" / "weeks" / "*" / f"{slug}.json"),
        "raw_paths": raw_paths,
        "node_count": len(nodes),
    }
    if thread_merge_hints:
        source["thread_merge_suggestions"] = thread_merge_hints
    if artifact_path:
        source["artifact_index_path"] = artifact_path
        source["artifact_index_use"] = "navigation_and_edge_hints_only"
    return {
        "schema_version": SCHEMA_VERSION,
        "project_slug": slug,
        "generated_at": generated_at or current_timestamp(),
        "source": source,
        "nodes": nodes,
        "edges": edges,
    }


def write_index(index: dict[str, Any], vault: Path, slug: str, output: Path | None) -> Path:
    slug = validate_project_slug(slug)
    target = output or vault / "raw" / "decisions" / f"{slug}.json"
    if target.exists():
        try:
            previous = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None
        if isinstance(previous, dict):
            entries, paths = load_raw_entries(vault, slug)
            if missing_raw_sources(previous, entries, paths):
                raise ValueError("raw sources missing or truncated; existing decision index preserved")
    write_json_atomic(target, index)
    return target


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        result.append(normalized)
        seen.add(normalized)
    return result


def command_build(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve()
    cfg, config_sources = resolve_config(cwd)
    vault = Path(args.vault).expanduser().resolve() if args.vault else Path(str(cfg["knowledge_vault"]))
    slug = validate_project_slug(args.slug) if args.slug else project_slug(cwd, vault, cfg.get("project_slug"))
    output = Path(args.output).expanduser().resolve() if args.output else None
    index = build_index(vault, slug, args.generated_at)
    path = write_index(index, vault, slug, output)
    print(
        json.dumps(
            {
                "path": str(path),
                "project_slug": slug,
                "vault": str(vault),
                "config_sources": config_sources,
                "entries_read": index["source"]["raw_entry_count"],
                "nodes": len(index["nodes"]),
                "edges": len(index["edges"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def load_index(vault: Path, slug: str) -> dict[str, Any]:
    slug = validate_project_slug(slug)
    path = vault / "raw" / "decisions" / f"{slug}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            entries, paths = load_raw_entries(vault, slug)
            if missing_raw_sources(data, entries, paths):
                return {**data, "nodes": [], "edges": [], "diagnostics": [
                    "Raw sources missing or truncated; existing index preserved, claims unavailable."
                ]}
            artifacts, _ = load_artifacts(vault, slug)
            if index_is_current(data, entries, artifacts):
                return data
            return build_index(vault, slug)
    return build_index(vault, slug)


def recent_decision_nodes(index: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    nodes = [item for item in index.get("nodes", []) if isinstance(item, dict)]
    nodes.sort(
        key=lambda item: (
            str(item.get("timestamp", "")),
            str(item.get("id", "")),
        ),
        reverse=True,
    )
    return nodes[:limit]


def read_or_rebuild_decision_context(
    vault: Path,
    slug: str,
    limit: int,
    write: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    slug = validate_project_slug(slug)
    path = vault / "raw" / "decisions" / f"{slug}.json"
    entries, paths = load_raw_entries(vault, slug)
    raw_latest = latest_entry_datetime(entries)
    status: dict[str, Any] = {
        "path": str(path),
        "rebuilt": False,
        "reason": "current",
        "raw_latest_timestamp": raw_latest.isoformat() if raw_latest else None,
    }

    def rebuild(reason: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        status["reason"] = reason
        status["rebuilt"] = True
        index = build_index(vault, slug)
        status["index_generated_at"] = index.get("generated_at")
        if write:
            try:
                write_index(index, vault, slug, None)
            except OSError as exc:
                status["write_error"] = str(exc)
        return recent_decision_nodes(index, limit), status

    if not path.exists():
        return rebuild("missing_index")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return rebuild("invalid_index_json")

    if isinstance(data, dict):
        status["index_generated_at"] = data.get("generated_at")
        if missing_raw_sources(data, entries, paths):
            status["reason"] = "missing_raw_sources"
            return [], status
        artifacts, _ = load_artifacts(vault, slug)
        if not index_is_current(data, entries, artifacts):
            return rebuild("stale_index")
        nodes = data.get("nodes")
        if isinstance(nodes, list):
            items = nodes
        else:
            value = data.get("decision_context")
            items = value if isinstance(value, list) else []
    elif isinstance(data, list):
        items = data
        if entries:
            return rebuild("stale_index")
    else:
        items = []

    decisions = [item for item in items if isinstance(item, dict)]
    if not decisions and entries:
        return rebuild("empty_index")

    decisions.sort(
        key=lambda item: (
            str(item.get("timestamp", "")),
            str(item.get("id", "")),
        ),
        reverse=True,
    )
    return decisions[:limit], status


def node_search_text(node: dict[str, Any], mode: str) -> str:
    rejected_text = " ".join(
        " ".join(str(item.get(field, "")) for field in ("option", "reason"))
        for item in node.get("rejected", [])
        if isinstance(item, dict)
    )
    base = " ".join(
        str(value)
        for value in (
            node.get("decision"),
            node.get("summary"),
            node.get("why"),
            node.get("chosen"),
            node.get("impact"),
            rejected_text,
            " ".join(as_string_list(node.get("open_questions"))),
            " ".join(as_string_list(node.get("decision_threads"))),
            " ".join(as_string_list(node.get("topic_keys"))),
            " ".join(as_string_list(node.get("artifact_refs"))),
        )
        if value
    )
    if mode == "alternatives":
        base = f"{rejected_text} {base}"
    elif mode == "impact":
        base = f"{node.get('impact') or ''} {' '.join(as_string_list(node.get('artifact_refs')))} {base}"
    elif mode == "revisit":
        base = f"{rejected_text} {' '.join(as_string_list(node.get('open_questions')))} {base}"
    elif mode == "why":
        base = f"{node.get('why') or ''} {base}"
    return base.lower()


def query_terms(query: str) -> list[str]:
    return lexical_tokens(query)


def score_node(node: dict[str, Any], terms: list[str], mode: str) -> int:
    if not terms:
        return 0
    score = 0
    node_tokens = search_tokens(node_search_text(node, mode))
    topic_tokens = search_tokens(" ".join(as_string_list(node.get("topic_keys"))))
    decision_tokens = search_tokens(str(node.get("decision", "")))
    why_tokens = search_tokens(str(node.get("why", "")))
    matched = [term for term in terms if term in node_tokens]
    required_matches = 1 if len(terms) == 1 else max(2, (len(terms) // 2) + 1)
    if len(matched) < required_matches:
        return 0
    score += len(matched) * 8
    for term in terms:
        if term in node_tokens:
            score += 10
        if term in topic_tokens:
            score += 8
        if term in decision_tokens:
            score += 6
        if term in why_tokens:
            score += 4
    if mode == "alternatives" and node.get("rejected"):
        score += 4
    if mode == "revisit" and (node.get("open_questions") or node.get("rejected")):
        score += 4
    if mode == "impact" and node.get("impact"):
        score += 4
    if mode == "why" and node.get("why"):
        score += 4
    if node.get("confidence") == "explicit":
        score += 2
    return score


def matched_terms(node: dict[str, Any], terms: list[str], mode: str) -> list[str]:
    haystack = search_tokens(node_search_text(node, mode))
    return [term for term in terms if term in haystack]


def compact_node(node: dict[str, Any], terms: list[str] | None = None, mode: str = "why") -> dict[str, Any]:
    result = {
        "id": node.get("id"),
        "timestamp": node.get("timestamp"),
        "week": node.get("week"),
        "confidence": node.get("confidence"),
        "evidence_boundary": node.get("evidence_boundary", "limited"),
        "impact_boundary": node.get("impact_boundary", "unknown"),
        "evidence_gap": node.get("evidence_gap"),
        "decision": node.get("decision"),
        "why": node.get("why"),
        "chosen": node.get("chosen"),
        "rejected": node.get("rejected", []),
        "open_questions": node.get("open_questions", []),
        "impact": node.get("impact"),
        "decision_threads": node.get("decision_threads", []),
        "lifecycle_transition": node.get("lifecycle_transition"),
        "topic_keys": node.get("topic_keys", []),
        "thread_id": node.get("thread_id"),
        "artifact_refs": node.get("artifact_refs", []),
        "direct_artifact_refs": node.get("direct_artifact_refs", []),
        "evidence_refs": node.get("evidence_refs", []),
        "source_entry_refs": node.get("source_entry_refs", []),
        "source_refs": node.get("source_refs", []),
        "inference_notes": node.get("inference_notes", []),
    }
    if terms is not None:
        result["matched_terms"] = matched_terms(node, terms, mode)
    return result


def supporting_nodes(
    selected: list[dict[str, Any]], all_nodes: list[dict[str, Any]], edges: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    selected_ids = {str(node.get("id")) for node in selected}
    wanted_ids: list[str] = []
    for edge in edges:
        left = str(edge.get("from"))
        right = str(edge.get("to"))
        if left in selected_ids and right not in selected_ids:
            wanted_ids.append(right)
        elif right in selected_ids and left not in selected_ids:
            wanted_ids.append(left)
    by_id = {str(node.get("id")): node for node in all_nodes}
    result = [by_id[node_id] for node_id in dedupe(wanted_ids) if node_id in by_id]
    return result[:limit]


def has_direct_evidence(node: dict[str, Any]) -> bool:
    """Direct evidence is distinct from raw-entry provenance."""
    return bool(
        any(not ref.lower().startswith(("conversation:", "session:", "repository_snapshot:"))
            for ref in as_string_list(node.get("evidence_refs")))
        or any(ref.get("type") in {"commit", "doc", "file", "test", "eval", "issue", "pr"}
               and isinstance(ref.get("ref"), str) and ref["ref"].strip()
               for ref in as_object_list(node.get("source_refs")))
        or as_string_list(node.get("direct_artifact_refs"))
    )


def evidence_strength(top: list[dict[str, Any]], terms: list[str], mode: str) -> str:
    if not top:
        return "none"
    strongest = top[0]
    match_count = len(matched_terms(strongest, terms, mode))
    has_provenance = bool(strongest.get("source_entry_refs"))
    direct_evidence = has_direct_evidence(strongest)
    boundary = strongest.get("evidence_boundary", "limited")
    if boundary != "verified" or (mode == "impact" and strongest.get("impact_boundary") != "observed"):
        return "weak"
    strong_match_floor = 1 if len(terms) == 1 else min(len(terms), 3)
    if strongest.get("confidence") == "explicit" and direct_evidence and match_count >= strong_match_floor:
        return "strong"
    if direct_evidence and match_count >= 1:
        return "moderate"
    if has_provenance and match_count >= 1:
        return "weak"
    return "weak"


def answerability_reason(top: list[dict[str, Any]], terms: list[str], mode: str, strength: str) -> str:
    if not terms:
        return "The query did not contain enough searchable decision terms."
    if not top:
        return "No decision index nodes matched enough query terms to ground an answer."
    top_node = top[0]
    matched = matched_terms(top_node, terms, mode)
    basis = "supporting reference" if has_direct_evidence(top_node) else "raw-entry provenance only"
    return (
        f"Top node {top_node.get('id')} matched {len(matched)}/{len(terms)} query terms "
        f"with {top_node.get('confidence', 'unknown')} confidence, {basis}, "
        f"{top_node.get('evidence_boundary', 'limited')} boundary, and {strength} evidence."
    )


def build_query_pack(index: dict[str, Any], query: str, mode: str, limit: int) -> dict[str, Any]:
    nodes = [node for node in index.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in index.get("edges", []) if isinstance(edge, dict)]
    terms = query_terms(query)
    scored = [
        (score_node(node, terms, mode), node)
        for node in nodes
    ]
    scored = [(score, node) for score, node in scored if score > 0]
    scored.sort(
        key=lambda item: (
            item[0],
            str(item[1].get("timestamp", "")),
        ),
        reverse=True,
    )
    top = [node for _, node in scored[:limit]]
    supporting = supporting_nodes(top, nodes, edges, max(limit, 1))
    top_matched_terms = dedupe([
        term
        for node in top
        for term in matched_terms(node, terms, mode)
    ])
    strength = evidence_strength(top, terms, mode)
    rejected: list[dict[str, Any]] = []
    open_questions: list[dict[str, Any]] = []
    docs: list[str] = []
    for node in top:
        for item in node.get("rejected", []):
            if isinstance(item, dict):
                rejected.append({"decision_id": node.get("id"), **item})
        for question in as_string_list(node.get("open_questions")):
            open_questions.append({"decision_id": node.get("id"), "question": question})
        docs.extend(as_string_list(node.get("artifact_refs")))
    if not top:
        missing_evidence = ["No decision index nodes matched the query terms."]
    elif not has_direct_evidence(top[0]):
        missing_evidence = [
            "The top matched decision has raw-entry provenance but lacks independent verification; conversation and repository_snapshot refs alone do not verify effects."
        ]
    elif top[0].get("evidence_boundary") != "verified":
        missing_evidence = ["The recorded evidence boundary does not establish independent verification."]
    elif mode == "impact" and top[0].get("impact_boundary") != "observed":
        missing_evidence = ["The impact is expected or unknown, not an observed result."]
    else:
        missing_evidence = []
    missing_evidence.extend(as_string_list(index.get("diagnostics")))
    if top and top[0].get("evidence_gap"):
        missing_evidence.append(str(top[0]["evidence_gap"]))
    return {
        "schema_version": QUERY_SCHEMA_VERSION,
        "project_slug": index.get("project_slug"),
        "generated_at": current_timestamp(),
        "query": query,
        "mode": mode,
        "answerable": bool(top),
        "terms": terms,
        "matched_terms": top_matched_terms,
        "evidence_strength": strength,
        "evidence_boundary": top[0].get("evidence_boundary", "limited") if top else "limited",
        "impact_boundary": top[0].get("impact_boundary", "unknown") if top else "unknown",
        "answerability_reason": answerability_reason(top, terms, mode, strength),
        "top_nodes": [compact_node(node, terms, mode) for node in top],
        "supporting_nodes": [compact_node(node, terms, mode) for node in supporting],
        "rejected_alternatives": rejected,
        "open_questions": open_questions,
        "missing_evidence": missing_evidence,
        "suggested_docs": dedupe(docs),
    }


def roadmap_thread_title(thread_id: str, nodes: list[dict[str, Any]]) -> str:
    for node in nodes:
        threads = as_string_list(node.get("decision_threads"))
        if threads:
            return threads[0]
    for node in nodes:
        keys = as_string_list(node.get("topic_keys"))
        if keys:
            return keys[0]
    return thread_id.removeprefix("thread:")


def confidence_mix(nodes: list[dict[str, Any]]) -> str:
    explicit = sum(1 for node in nodes if node.get("confidence") == "explicit")
    inferred = len(nodes) - explicit
    if explicit and inferred:
        return "mixed"
    if explicit:
        return "explicit"
    return "inferred"


def node_is_risk(node: dict[str, Any]) -> bool:
    fields = (
        node.get("entry_type"),
        node.get("archetype"),
        node.get("status"),
        node.get("decision"),
        node.get("summary"),
    )
    return any("risk" in str(value).lower() for value in fields if value)


def compact_risk(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": node.get("id"),
        "risk": node.get("summary") or node.get("decision"),
        "timestamp": node.get("timestamp"),
        "confidence": node.get("confidence"),
        "source_entry_refs": node.get("source_entry_refs", []),
    }


def compact_transition(node: dict[str, Any]) -> dict[str, Any] | None:
    transition = as_object(node.get("lifecycle_transition"))
    if not transition:
        return None
    return {
        "decision_id": node.get("id"),
        "timestamp": node.get("timestamp"),
        **transition,
        "source_entry_refs": node.get("source_entry_refs", []),
    }


def build_thread_summary(thread_id: str, nodes: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(nodes, key=lambda node: (str(node.get("timestamp", "")), str(node.get("id", ""))))
    explicit_count = sum(1 for node in ordered if node.get("confidence") == "explicit")
    inferred_count = len(ordered) - explicit_count
    rejected: list[dict[str, Any]] = []
    open_questions: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    risks: list[dict[str, Any]] = []
    artifact_refs: list[str] = []
    source_entry_refs: list[dict[str, Any]] = []
    inference_notes: list[str] = []

    for node in ordered:
        source_entry_refs.extend(as_object_list(node.get("source_entry_refs")))
        artifact_refs.extend(as_string_list(node.get("artifact_refs")))
        inference_notes.extend(as_string_list(node.get("inference_notes")))
        if node_is_risk(node):
            risks.append(compact_risk(node))
        transition = compact_transition(node)
        if transition:
            transitions.append(transition)
        for item in node.get("rejected", []):
            if isinstance(item, dict):
                rejected.append({
                    "decision_id": node.get("id"),
                    "timestamp": node.get("timestamp"),
                    **item,
                    "source_entry_refs": node.get("source_entry_refs", []),
                })
        for question in as_string_list(node.get("open_questions")):
            open_questions.append({
                "decision_id": node.get("id"),
                "timestamp": node.get("timestamp"),
                "question": question,
                "source_entry_refs": node.get("source_entry_refs", []),
            })

    return {
        "thread_id": thread_id,
        "title": roadmap_thread_title(thread_id, ordered),
        "confidence": confidence_mix(ordered),
        "node_count": len(ordered),
        "explicit_node_count": explicit_count,
        "inferred_node_count": inferred_count,
        "first_timestamp": ordered[0].get("timestamp") if ordered else None,
        "latest_timestamp": ordered[-1].get("timestamp") if ordered else None,
        "decisions": [compact_node(node) for node in ordered],
        "rejected_alternatives": rejected,
        "open_questions": open_questions,
        "lifecycle_transitions": transitions,
        "accumulating_risks": risks,
        "artifact_refs": dedupe(artifact_refs),
        "source_entry_refs": source_entry_refs,
        "inference_notes": dedupe(inference_notes),
    }


def build_roadmap_pack(index: dict[str, Any], limit_threads: int = 20) -> dict[str, Any]:
    nodes = [node for node in index.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in index.get("edges", []) if isinstance(edge, dict)]
    by_thread: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        thread_id = str(node.get("thread_id") or "thread:unknown")
        by_thread.setdefault(thread_id, []).append(node)

    threads = [build_thread_summary(thread_id, thread_nodes) for thread_id, thread_nodes in by_thread.items()]
    threads.sort(
        key=lambda thread: (
            str(thread.get("latest_timestamp", "")),
            str(thread.get("thread_id", "")),
        ),
        reverse=True,
    )
    limited_threads = threads[: max(limit_threads, 1)]
    included_thread_ids = {str(thread.get("thread_id")) for thread in limited_threads}
    node_to_thread = {
        str(node.get("id")): str(node.get("thread_id") or "thread:unknown")
        for node in nodes
    }
    cross_thread_edges = [
        edge for edge in edges
        if node_to_thread.get(str(edge.get("from"))) in included_thread_ids
        and node_to_thread.get(str(edge.get("to"))) in included_thread_ids
        and node_to_thread.get(str(edge.get("from"))) != node_to_thread.get(str(edge.get("to")))
    ]
    return {
        "schema_version": ROADMAP_SCHEMA_VERSION,
        "diagnostics": as_string_list(index.get("diagnostics")),
        "project_slug": index.get("project_slug"),
        "generated_at": current_timestamp(),
        "source": {
            "decision_index_generated_at": index.get("generated_at"),
            "decision_index_source": index.get("source", {}),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "thread_count": len(threads),
        "threads": limited_threads,
        "cross_thread_edges": cross_thread_edges,
        "open_questions": [
            question
            for thread in limited_threads
            for question in thread.get("open_questions", [])
            if isinstance(question, dict)
        ],
        "accumulating_risks": [
            risk
            for thread in limited_threads
            for risk in thread.get("accumulating_risks", [])
            if isinstance(risk, dict)
        ],
    }


def command_query(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve()
    cfg, _ = resolve_config(cwd)
    vault = Path(args.vault).expanduser().resolve() if args.vault else Path(str(cfg["knowledge_vault"]))
    slug = validate_project_slug(args.slug) if args.slug else project_slug(cwd, vault, cfg.get("project_slug"))
    index = load_index(vault, slug)
    pack = build_query_pack(index, args.query, args.mode, max(args.limit, 1))
    print(json.dumps(pack, ensure_ascii=False, indent=2))
    return 0


def command_roadmap(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).expanduser().resolve()
    cfg, _ = resolve_config(cwd)
    vault = Path(args.vault).expanduser().resolve() if args.vault else Path(str(cfg["knowledge_vault"]))
    slug = validate_project_slug(args.slug) if args.slug else project_slug(cwd, vault, cfg.get("project_slug"))
    index = load_index(vault, slug)
    pack = build_roadmap_pack(index, max(args.limit_threads, 1))
    print(json.dumps(pack, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Tracework Decision Replay Index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser(
        "build",
        help="Build {vault}/raw/decisions/{slug}.json from weekly raw entries",
    )
    build_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    build_parser.add_argument("--vault", help="Knowledge vault override")
    build_parser.add_argument("--slug", help="Project slug override")
    build_parser.add_argument("--output", help="Output path override")
    build_parser.add_argument("--generated-at", help="Generated timestamp override for deterministic fixtures")
    build_parser.set_defaults(func=command_build)

    query_parser = subparsers.add_parser(
        "query",
        help="Return a compact evidence pack from the decision replay index",
    )
    query_parser.add_argument("query", help="Decision question or keywords")
    query_parser.add_argument("--mode", choices=("why", "alternatives", "revisit", "impact"), default="why")
    query_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    query_parser.add_argument("--vault", help="Knowledge vault override")
    query_parser.add_argument("--slug", help="Project slug override")
    query_parser.add_argument("--limit", type=int, default=5, help="Maximum top nodes")
    query_parser.set_defaults(func=command_query)

    roadmap_parser = subparsers.add_parser(
        "roadmap",
        help="Return thread-level evidence for a decision roadmap",
    )
    roadmap_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    roadmap_parser.add_argument("--vault", help="Knowledge vault override")
    roadmap_parser.add_argument("--slug", help="Project slug override")
    roadmap_parser.add_argument("--limit-threads", type=int, default=20, help="Maximum decision threads")
    roadmap_parser.set_defaults(func=command_roadmap)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
