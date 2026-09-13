#!/usr/bin/env python3
"""Prepare bounded Tracework recall context for the current project."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from tracework_state import read_view
from decision_replay import (
    load_index,
    recent_decision_nodes,
    read_or_rebuild_decision_context,
    validate_project_slug,
)


SKIP_DIRS = {".git", "node_modules", "dist", "__pycache__"}
INTENT_ARTIFACT_RE = re.compile(
    r"\b(DESIGN\.md|PLAN\.md|AGENTS\.md|README(?:\.cn)?\.md)\b|"
    r"(design|plan|architecture|prompt|schema|contract|migration|config)",
    re.IGNORECASE,
)


def load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(raw) or {}
        return data if isinstance(data, dict) else {}
    result: dict[str, Any] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or line[:1].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip("'\"")
    return result


def find_project_config(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for directory in (current, *current.parents):
        candidate = directory / ".tracework" / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def resolve_config(cwd: Path) -> dict[str, Any]:
    global_cfg = load_yaml_config(Path.home() / ".tracework" / "config.yaml")
    project_path = find_project_config(cwd)
    project_cfg = load_yaml_config(project_path) if project_path else {}
    cfg = dict(global_cfg)
    for key, value in project_cfg.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            nested = dict(cfg[key])
            nested.update(value)
            cfg[key] = nested
        else:
            cfg[key] = value
    return cfg


def slugify(name: str) -> str:
    slug = re.sub(r"[\s_]+", "-", name.strip().lower())
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    return re.sub(r"-+", "-", slug).strip("-") or "project"


def same_path(left: str, right: Path) -> bool:
    try:
        return Path(left).expanduser().resolve() == right.expanduser().resolve()
    except OSError:
        return Path(left).expanduser().absolute() == right.expanduser().absolute()


def project_slug(cwd: Path, vault: Path | None, slug_override: str | None) -> str:
    if slug_override:
        return validate_project_slug(slug_override)
    cfg = resolve_config(cwd)
    configured = cfg.get("project_slug")
    if isinstance(configured, str) and configured.strip():
        return validate_project_slug(configured.strip())
    if vault:
        projects_file = vault / "raw" / "projects.json"
        if projects_file.exists():
            try:
                projects = json.loads(projects_file.read_text(encoding="utf-8"))
                if isinstance(projects, list):
                    for project in projects:
                        if isinstance(project, dict) and isinstance(project.get("path"), str):
                            if same_path(project["path"], cwd) and isinstance(project.get("slug"), str):
                                return validate_project_slug(project["slug"])
            except (json.JSONDecodeError, ValueError):
                pass
    return validate_project_slug(slugify(cwd.name))


def resolve_vault(cwd: Path, vault_override: str | None) -> Path | None:
    if vault_override:
        return Path(vault_override).expanduser().resolve()
    cfg = resolve_config(cwd)
    value = cfg.get("knowledge_vault")
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser().resolve()
    return None


def read_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def parse_timestamp(entry: dict[str, Any]) -> str:
    value = entry.get("timestamp")
    return value if isinstance(value, str) else ""


def signal_score(entry: dict[str, Any]) -> int:
    score = 0
    if entry.get("type") == "decision":
        score += 5
    if entry.get("status") == "risk" or entry.get("type") == "risk":
        score += 5
    for field, weight in (
        ("open_questions", 4),
        ("abandoned_alternatives", 3),
        ("exploration_paths", 2),
        ("motivation", 1),
    ):
        value = entry.get(field)
        if isinstance(value, list) and value:
            score += weight
        elif isinstance(value, str) and value.strip():
            score += weight
    return score


def read_entries(vault: Path, slug: str) -> list[dict[str, Any]]:
    return list(reversed(read_view(vault, slug)['entries']))


def public_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in entry.items() if not key.startswith("_")}


def extract_list(entries: list[dict[str, Any]], field: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for entry in entries:
        timestamp = parse_timestamp(entry)
        value = entry.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    results.append({"timestamp": timestamp, "value": item.strip(), "summary": str(entry.get("summary", ""))})
    return results


def extract_decisions(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    decisions: list[dict[str, str]] = []
    for entry in entries:
        if entry.get("type") == "decision" or entry.get("status") == "decision":
            decisions.append({
                "timestamp": parse_timestamp(entry),
                "summary": str(entry.get("summary", "")),
                "context": str(entry.get("context", "")),
            })
    return decisions


def extract_risks(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    for entry in entries:
        if entry.get("type") == "risk" or entry.get("status") == "risk":
            risks.append({
                "timestamp": parse_timestamp(entry),
                "summary": str(entry.get("summary", "")),
                "context": str(entry.get("context", "")),
            })
    return risks


def extract_intent_artifact_flags(entries: list[dict[str, Any]], limit: int) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    for entry in entries:
        explicit = entry.get("sync_suggestions")
        if isinstance(explicit, list):
            for item in explicit:
                if isinstance(item, str) and item.strip():
                    flags.append({
                        "timestamp": parse_timestamp(entry),
                        "summary": str(entry.get("summary", "")),
                        "reason": item.strip(),
                        "source": "sync_suggestions",
                    })
        searchable = " ".join(
            str(value)
            for key, value in entry.items()
            if key in {"summary", "context", "motivation", "impact"}
        )
        related_docs = entry.get("related_docs")
        if isinstance(related_docs, list):
            searchable = f"{searchable} {' '.join(str(item) for item in related_docs)}"
        if INTENT_ARTIFACT_RE.search(searchable):
            flags.append({
                "timestamp": parse_timestamp(entry),
                "summary": str(entry.get("summary", "")),
                "reason": "Recent raw entry mentions an intent artifact or contract-like change; review for possible staleness.",
                "source": "presence_match",
            })
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for flag in flags:
        key = (flag["timestamp"], flag["summary"], flag["reason"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(flag)
    return unique[:limit]


def read_artifacts(vault: Path, slug: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    path = vault / "raw" / "artifacts" / f"{slug}.json"
    artifacts = read_json_array(path)
    missing: list[dict[str, str]] = []
    for artifact in artifacts:
        path_value = artifact.get("path")
        if isinstance(path_value, str) and not Path(path_value).expanduser().exists():
            missing.append({
                "artifact_id": str(artifact.get("id", "")),
                "path": path_value,
            })
    return artifacts, missing


def read_decision_context(
    vault: Path,
    slug: str,
    limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return read_or_rebuild_decision_context(vault, slug, limit, write=True)


def add_decision_context(
    context: dict[str, Any],
    vault: Path,
    slug: str,
    limit: int,
) -> dict[str, Any]:
    decision_context, source = read_decision_context(vault, slug, limit)
    context["decision_context_source"] = source
    if decision_context:
        context["decision_context"] = decision_context
    return context


def build_context(cwd: Path, vault_override: str | None, slug_override: str | None, limit: int, end=None, as_of=None) -> dict[str, Any]:
    vault = resolve_vault(cwd, vault_override)
    slug = project_slug(cwd, vault, slug_override)
    if vault is None or not vault.exists():
        return {
            "project_slug": slug,
            "recent_entries": [],
            "open_questions": [],
            "risks": [],
            "abandoned_alternatives": [],
            "decisions": [],
            "artifacts": [],
            "intent_artifact_flags": [],
            "missing_sources": [{"type": "vault", "path": str(vault) if vault else ""}],
        }

    view = read_view(vault, slug, end=end, as_of=as_of)
    entries = list(reversed(view['entries']))
    ranked = sorted(entries, key=lambda entry: (signal_score(entry), parse_timestamp(entry)), reverse=True)
    recent_entries = [public_entry(entry) for entry in ranked[:limit]]
    artifacts, missing_artifacts = read_artifacts(vault, slug)
    context: dict[str, Any] = {
        "project_slug": slug,
        "recent_entries": recent_entries,
        "open_questions": extract_list(entries, "open_questions")[:limit],
        "risks": extract_risks(entries)[:limit],
        "abandoned_alternatives": extract_list(entries, "abandoned_alternatives")[:limit],
        "decisions": extract_decisions(entries)[:limit],
        "artifacts": artifacts[:limit],
        "intent_artifact_flags": extract_intent_artifact_flags(entries, limit),
        "missing_sources": missing_artifacts,
    }
    context['states'] = view['states']
    context['correction_history'] = view['correction_history']
    context['diagnostics'] = view['diagnostics']
    context['open_questions'] = [dict(state, value=state['text']) for state in view['states']
        if state['subject'].startswith('open_question:') and state['state'] not in ('resolved', 'closed')][:limit]
    context['risks'] = [dict(state, summary=state['text']) for state in view['states']
        if state['subject'].startswith('risk:') and state['state'] not in ('mitigated', 'resolved', 'closed', 'accepted')][:limit]
    context['accepted_risks'] = [state for state in view['states'] if state['subject'].startswith('risk:') and state['state'] == 'accepted']
    if end or as_of:
        index = load_index(vault, slug, end=end, as_of=as_of)
        context['decision_context'] = recent_decision_nodes(index, limit)
        context['decision_context_source'] = {'reason': 'scoped_ephemeral', 'diagnostics': index.get('diagnostics', [])}
        return context
    return add_decision_context(context, vault, slug, limit)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Tracework session-start recall context")
    parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    parser.add_argument("--vault", help="Knowledge vault override")
    parser.add_argument("--slug", help="Project slug override")
    parser.add_argument("--limit", type=int, default=12, help="Maximum entries per section")
    parser.add_argument('--end')
    parser.add_argument('--as-of')
    args = parser.parse_args()

    context = build_context(
        cwd=Path(args.cwd).expanduser().resolve(),
        vault_override=args.vault,
        slug_override=args.slug,
        limit=max(args.limit, 1),
        end=args.end, as_of=args.as_of,
    )
    print(json.dumps(context, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
