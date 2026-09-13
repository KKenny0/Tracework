#!/usr/bin/env python3
"""Shared Tracework raw storage helper.

This script keeps path resolution and raw-entry appends deterministic so skills
can focus on writing high-quality change signals.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import errno
import tempfile
import time
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None


LOCK_REGION_BYTES = 1
WINDOWS_LOCK_TIMEOUT_SECONDS = 4.0
WINDOWS_LOCK_RETRY_INTERVAL_SECONDS = 0.05


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def prepare_lock_file(handle: Any) -> None:
    """Ensure the Windows byte-range lock has a region to acquire."""
    handle.seek(0, os.SEEK_END)
    size = handle.tell()
    if size < LOCK_REGION_BYTES:
        handle.write(b"\0" * (LOCK_REGION_BYTES - size))
        handle.flush()
    handle.seek(0)


def lock_json_handle(handle: Any) -> None:
    """Acquire a short-lived cross-platform JSON lock."""
    if os.name == "nt":
        import msvcrt

        deadline = time.monotonic() + WINDOWS_LOCK_TIMEOUT_SECONDS
        while True:
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, LOCK_REGION_BYTES)
                return
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise
                if time.monotonic() >= deadline:
                    raise
                time.sleep(WINDOWS_LOCK_RETRY_INTERVAL_SECONDS)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)


def unlock_json_handle(handle: Any) -> None:
    """Release a lock acquired by lock_json_handle."""
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, LOCK_REGION_BYTES)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def json_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = path.with_suffix(path.suffix + ".lock")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    os.chmod(lock_path, 0o600)
    with os.fdopen(descriptor, "r+b") as handle:
        prepare_lock_file(handle)
        lock_json_handle(handle)
        try:
            yield path
        finally:
            unlock_json_handle(handle)


VALID_TYPES = {"feature", "fix", "refactor", "decision", "risk"}
VALID_SOURCES = {"session-recap", "arch-doc"}
VALID_STATUSES = {"done", "ongoing", "risk", "decision"}
VALID_CAPTURE_DEPTHS = {"lite", "standard", "deep"}
REPOSITORY_SNAPSHOT_TYPE = "repository_snapshot"
REQUIRED_FIELDS = ("timestamp", "type", "summary", "context", "source")
VALID_ARCHETYPES = {"decision", "build", "investigation", "repair", "maintenance"}
ARCHETYPE_REQUIRED_FIELDS = {
    "decision": ("motivation", "exploration_paths"),
    "build": ("motivation", "impact"),
    "investigation": ("exploration_paths", "open_questions"),
    "repair": ("motivation", "root_cause"),
    "maintenance": (),
}
VALID_ARTIFACT_TYPES = {
    "arch-doc",
    "design-doc",
    "plan-doc",
    "agents-rule",
    "prompt-contract",
    "schema-contract",
    "checklist",
    "roadmap",
    "review",
    "other",
}
VALID_ARTIFACT_STATUSES = {"active", "draft", "superseded", "obsolete", "missing"}
REQUIRED_ARTIFACT_FIELDS = (
    "id",
    "project_slug",
    "artifact_type",
    "title",
    "path",
    "created_at",
    "updated_at",
    "source",
    "status",
)
ARTIFACT_LIST_FIELDS = (
    "topics",
    "decision_threads",
    "open_questions",
    "risk_refs",
    "evidence_refs",
    "supersedes",
)
VALID_REPORTING_OUTCOME_KINDS = {"outcome", "progress", "activity"}
VALID_REPORTING_IMPACT_BOUNDARIES = {"observed", "expected", "unknown"}
VALID_REPORTING_EVIDENCE_BOUNDARIES = {"verified", "recorded", "limited"}
VALID_REPORTING_HARD_SIGNAL_KINDS = {
    "risk",
    "open_question",
    "abandoned_alternative",
    "candidate_rule_signal",
}
VALID_ARTIFACT_SOURCE_AVAILABILITY = {"available", "missing", "moved", "unknown"}
VALID_ARTIFACT_DELETION_BEHAVIOR = {"summary_remains_usable", "source_required"}
VALID_ARTIFACT_CLAIM_BOUNDARIES = {
    "navigation_only",
    "recorded_context",
    "direct_evidence",
}


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
    """Parse the small nested mapping shape used by Tracework configs.

    The fallback is intentionally not a general YAML parser. It supports
    indentation-based mappings and scalar values, which covers Tracework's
    profile, output, artifact-index, and session-scan settings without adding a
    mandatory PyYAML dependency.
    """
    result: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, result)]
    list_keys = {"repos", "categories", "patterns"}

    def scalar(value: str) -> Any:
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if lowered in {"null", "~"}:
            return None
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return value

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        while stack[-1][0] >= indent:
            stack.pop()
        owner = stack[-1][1]

        if stripped.startswith("-"):
            if not isinstance(owner, list):
                continue
            item = stripped[1:].strip()
            if not item:
                continue
            if ":" in item:
                key, value = item.split(":", 1)
                nested_item = {key.strip(): scalar(value.strip()) if value.strip() else {}}
                owner.append(nested_item)
                stack.append((indent, nested_item))
            else:
                owner.append(scalar(item))
            continue

        if ":" not in stripped or not isinstance(owner, dict):
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            nested: Any = [] if key in list_keys else {}
            owner[key] = nested
            stack.append((indent, nested))
            continue
        if value in {"|", ">"}:
            continue
        owner[key] = scalar(value)
    return result


def find_project_config(cwd: Path) -> Path | None:
    current = cwd.resolve()
    global_path = Path.home().resolve() / ".tracework" / "config.yaml"
    for directory in (current, *current.parents):
        candidate = directory / ".tracework" / "config.yaml"
        if candidate != global_path and candidate.exists():
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
    return cfg, sources


def iso_week(value: str | None = None) -> str:
    if value:
        date_value = dt.date.fromisoformat(value)
    else:
        date_value = dt.date.today()
    year, week, _ = date_value.isocalendar()
    return f"{year}-W{week:02d}"


def resolve_scope(cwd: Path, requested: str | None, purpose: str) -> dict[str, Any]:
    """Resolve a reporting lane without reading work records or transcripts."""
    if purpose not in {"report", "session"}:
        raise ValueError("purpose must be report or session")
    if requested is not None:
        validate_non_empty_string("scope", requested)
        return {"scope": requested.strip(), "scope_source": "explicit", "reason": "user_requested"}

    cfg, _ = resolve_config(cwd)
    profile = cfg.get("profile", {})
    if not isinstance(profile, dict):
        raise ValueError("profile must be a mapping")
    default = profile.get("default_reporting_group")
    if default is not None:
        validate_non_empty_string("profile.default_reporting_group", default)
        return {"scope": default.strip(), "scope_source": "configured", "reason": "default_reporting_group"}

    project_config = find_project_config(cwd)
    root = project_config.parent.parent if project_config else next(
        (path for path in (cwd.resolve(), *cwd.resolve().parents) if (path / ".git").exists()),
        cwd.resolve(),
    )
    project_profile = load_yaml_config(project_config).get("profile", {}) if project_config else {}
    if not isinstance(project_profile, dict):
        raise ValueError("project profile must be a mapping")
    group = project_profile.get("reporting_group")
    reason = "project_config"
    if group is None and cfg.get("knowledge_vault"):
        registry = Path(cfg["knowledge_vault"]) / "raw" / "projects.json"
        if registry.exists():
            projects = json.loads(registry.read_text(encoding="utf-8"))
            if not isinstance(projects, list):
                raise ValueError("project registry must be an array")
            groups = {
                row.get("reporting_group") for row in projects
                if isinstance(row, dict) and isinstance(row.get("path"), str)
                and same_path(row["path"], root) and isinstance(row.get("reporting_group"), str)
            }
            if len(groups) > 1:
                raise ValueError("conflicting reporting groups for current project")
            group = next(iter(groups), None)
            reason = "project_registry"
    if group is not None:
        validate_non_empty_string("profile.reporting_group", group)
        if group.strip() != "unassigned":
            return {"scope": group.strip(), "scope_source": "project", "reason": reason}
    return {
        "scope": "local" if purpose == "report" else None,
        "scope_source": "implicit-local" if purpose == "report" else "unresolved",
        "reason": "current_project_unassigned",
    }


def slugify(name: str) -> str:
    slug = re.sub(r"[\s_]+", "-", name.strip().lower())
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "project"


def same_path(left: str, right: Path) -> bool:
    left_path = Path(left).expanduser()
    right_path = right.expanduser()
    try:
        return left_path.resolve() == right_path.resolve()
    except OSError:
        return left_path.absolute() == right_path.absolute()


def project_slug(cwd: Path, vault: Path | None = None) -> str:
    cfg, _ = resolve_config(cwd)
    configured = cfg.get("project_slug")
    if isinstance(configured, str) and configured.strip():
        return configured.strip()

    resolved_vault = vault or Path(str(cfg["knowledge_vault"]))
    projects_file = resolved_vault / "raw" / "projects.json"
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
                            return slug_value
        except json.JSONDecodeError:
            pass

    return slugify(cwd.resolve().name)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def has_value(entry: dict[str, Any], field: str) -> bool:
    value = entry.get(field)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return value is not None


def validate_string_list(entry: dict[str, Any], field: str) -> None:
    if field in entry:
        if not isinstance(entry[field], list) or not all(
            isinstance(item, str) for item in entry[field]
        ):
            raise ValueError(f"entry {field} must be a list of strings when present")


def validate_non_empty_string(owner: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string when present")


def validate_string_list_value(owner: str, value: Any) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{owner} must be a list of strings when present")


def validate_source_entry_refs_value(owner: str, refs: Any) -> None:
    if not isinstance(refs, list):
        raise ValueError(f"{owner} must be a list when present")
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise ValueError(f"{owner}[{index}] must be an object")
        for field in ("week", "path", "timestamp", "entry_id"):
            if field in ref:
                validate_non_empty_string(f"{owner}[{index}].{field}", ref[field])
        if "entry_index" in ref and not isinstance(ref["entry_index"], int):
            raise ValueError(f"{owner}[{index}].entry_index must be an integer when present")


def validate_reporting(entry: dict[str, Any]) -> None:
    if "reporting" not in entry:
        return
    reporting = entry["reporting"]
    if not isinstance(reporting, dict):
        raise ValueError("entry reporting must be an object when present")

    outcome = reporting.get("outcome_candidate")
    if outcome is not None:
        if not isinstance(outcome, dict):
            raise ValueError("entry reporting.outcome_candidate must be an object when present")
        kind = outcome.get("kind")
        if kind is not None and kind not in VALID_REPORTING_OUTCOME_KINDS:
            raise ValueError(
                "entry reporting.outcome_candidate.kind must be one of: "
                + ", ".join(sorted(VALID_REPORTING_OUTCOME_KINDS))
            )
        for field in ("statement", "rationale"):
            if field in outcome:
                validate_non_empty_string(f"entry reporting.outcome_candidate.{field}", outcome[field])

    impact_boundary = reporting.get("impact_boundary")
    if impact_boundary is not None and impact_boundary not in VALID_REPORTING_IMPACT_BOUNDARIES:
        raise ValueError(
            "entry reporting.impact_boundary must be one of: "
            + ", ".join(sorted(VALID_REPORTING_IMPACT_BOUNDARIES))
        )

    evidence_boundary = reporting.get("evidence_boundary")
    if evidence_boundary is not None and evidence_boundary not in VALID_REPORTING_EVIDENCE_BOUNDARIES:
        raise ValueError(
            "entry reporting.evidence_boundary must be one of: "
            + ", ".join(sorted(VALID_REPORTING_EVIDENCE_BOUNDARIES))
        )

    for field in ("evidence_gap", "work_stream"):
        if field in reporting:
            validate_non_empty_string(f"entry reporting.{field}", reporting[field])

    if "module_scope" in reporting:
        validate_string_list_value("entry reporting.module_scope", reporting["module_scope"])

    if "carry_forward" in reporting:
        carry_forward = reporting["carry_forward"]
        if isinstance(carry_forward, list):
            validate_string_list_value("entry reporting.carry_forward", carry_forward)
        elif isinstance(carry_forward, dict):
            for key, value in carry_forward.items():
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("entry reporting.carry_forward keys must be non-empty strings")
                if isinstance(value, list):
                    validate_string_list_value(f"entry reporting.carry_forward.{key}", value)
                else:
                    validate_non_empty_string(f"entry reporting.carry_forward.{key}", value)
        else:
            raise ValueError("entry reporting.carry_forward must be a list or object when present")

    if "hard_signals" in reporting:
        hard_signals = reporting["hard_signals"]
        if not isinstance(hard_signals, list):
            raise ValueError("entry reporting.hard_signals must be a list when present")
        for index, signal in enumerate(hard_signals):
            if isinstance(signal, str):
                if not signal.strip():
                    raise ValueError(f"entry reporting.hard_signals[{index}] must be non-empty")
                continue
            if not isinstance(signal, dict):
                raise ValueError(f"entry reporting.hard_signals[{index}] must be a string or object")
            kind = signal.get("kind")
            if kind is not None and kind not in VALID_REPORTING_HARD_SIGNAL_KINDS:
                raise ValueError(
                    f"entry reporting.hard_signals[{index}].kind must be one of: "
                    + ", ".join(sorted(VALID_REPORTING_HARD_SIGNAL_KINDS))
                )
            for field in ("statement", "subject", "evidence_gap", "recurrence_key"):
                if field in signal:
                    validate_non_empty_string(
                        f"entry reporting.hard_signals[{index}].{field}", signal[field]
                    )


def validate_artifact_context(entry: dict[str, Any]) -> None:
    if "artifact_context" not in entry:
        return
    contexts = entry["artifact_context"]
    if not isinstance(contexts, list):
        raise ValueError("entry artifact_context must be a list when present")
    required = ("artifact_path", "scope", "delta", "source_of_truth")
    for index, context in enumerate(contexts):
        if not isinstance(context, dict):
            raise ValueError(f"entry artifact_context[{index}] must be an object")
        missing = [field for field in required if field not in context]
        if missing:
            raise ValueError(
                f"entry artifact_context[{index}] missing required fields: "
                + ", ".join(missing)
            )
        for field in ("artifact_path", "scope", "delta"):
            if not isinstance(context[field], str) or not context[field].strip():
                raise ValueError(
                    f"entry artifact_context[{index}].{field} must be a non-empty string"
                )
        if not Path(context["artifact_path"]).expanduser().is_absolute():
            raise ValueError(
                f"entry artifact_context[{index}].artifact_path must be absolute: "
                + context["artifact_path"]
            )
        for field in ("open_questions", "source_of_truth"):
            if field in context:
                if not isinstance(context[field], list) or not all(
                    isinstance(item, str) for item in context[field]
                ):
                    raise ValueError(
                        f"entry artifact_context[{index}].{field} must be a list of strings"
                    )


def validate_source_refs(entry: dict[str, Any]) -> None:
    if "source_refs" not in entry:
        return
    refs = entry["source_refs"]
    if not isinstance(refs, list):
        raise ValueError("entry source_refs must be a list when present")
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise ValueError(f"entry source_refs[{index}] must be an object")
        for field in ("type", "ref"):
            if not isinstance(ref.get(field), str) or not ref[field].strip():
                raise ValueError(f"entry source_refs[{index}].{field} must be a non-empty string")
        for field in ("path", "url", "note", "timestamp"):
            if field in ref and (not isinstance(ref[field], str) or not ref[field].strip()):
                raise ValueError(f"entry source_refs[{index}].{field} must be a non-empty string when present")
        if ref["type"] == REPOSITORY_SNAPSHOT_TYPE:
            if not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", ref["ref"]):
                raise ValueError(
                    f"entry source_refs[{index}].ref must be a full Git object id for repository_snapshot"
                )
            path = ref.get("path")
            if not isinstance(path, str) or not Path(path).expanduser().is_absolute():
                raise ValueError(
                    f"entry source_refs[{index}].path must be an absolute repository root for repository_snapshot"
                )


def validate_lifecycle_transition(entry: dict[str, Any]) -> None:
    if "lifecycle_transition" not in entry:
        return
    transition = entry["lifecycle_transition"]
    if not isinstance(transition, dict):
        raise ValueError("entry lifecycle_transition must be an object when present")
    for field in ("subject", "from", "to", "reason"):
        if field in transition and (
            not isinstance(transition[field], str) or not transition[field].strip()
        ):
            raise ValueError(f"entry lifecycle_transition.{field} must be a non-empty string when present")


def validate_artifact_summary(summary: Any) -> None:
    if not isinstance(summary, dict):
        raise ValueError("artifact artifact_summary must be an object when present")
    for field in ("scope", "non_scope"):
        if field in summary:
            validate_non_empty_string(f"artifact artifact_summary.{field}", summary[field])
    for field in ("key_decisions", "open_questions"):
        if field in summary:
            validate_string_list_value(f"artifact artifact_summary.{field}", summary[field])
    if "key_claims" in summary:
        claims = summary["key_claims"]
        if not isinstance(claims, list):
            raise ValueError("artifact artifact_summary.key_claims must be a list when present")
        for index, claim in enumerate(claims):
            if isinstance(claim, str):
                if not claim.strip():
                    raise ValueError(f"artifact artifact_summary.key_claims[{index}] must be non-empty")
                continue
            if not isinstance(claim, dict):
                raise ValueError(f"artifact artifact_summary.key_claims[{index}] must be a string or object")
            if "claim" in claim:
                validate_non_empty_string(
                    f"artifact artifact_summary.key_claims[{index}].claim", claim["claim"]
                )
            boundary = claim.get("evidence_boundary")
            if boundary is not None and boundary not in VALID_ARTIFACT_CLAIM_BOUNDARIES:
                raise ValueError(
                    f"artifact artifact_summary.key_claims[{index}].evidence_boundary "
                    "must be one of: "
                    + ", ".join(sorted(VALID_ARTIFACT_CLAIM_BOUNDARIES))
                )
            if "evidence_refs" in claim:
                validate_string_list_value(
                    f"artifact artifact_summary.key_claims[{index}].evidence_refs",
                    claim["evidence_refs"],
                )
            if "source_entry_refs" in claim:
                validate_source_entry_refs_value(
                    f"artifact artifact_summary.key_claims[{index}].source_entry_refs",
                    claim["source_entry_refs"],
                )


def validate_artifact_last_seen(last_seen: Any) -> None:
    if not isinstance(last_seen, dict):
        raise ValueError("artifact last_seen must be an object when present")
    for field in ("at", "content_hash"):
        if field in last_seen:
            validate_non_empty_string(f"artifact last_seen.{field}", last_seen[field])
    if "exists" in last_seen and not isinstance(last_seen["exists"], bool):
        raise ValueError("artifact last_seen.exists must be a boolean when present")


def validate_artifact_dossier(artifact: dict[str, Any]) -> None:
    if "source_entry_refs" in artifact:
        validate_source_entry_refs_value("artifact source_entry_refs", artifact["source_entry_refs"])
    if "artifact_summary" in artifact:
        validate_artifact_summary(artifact["artifact_summary"])
    if "last_seen" in artifact:
        validate_artifact_last_seen(artifact["last_seen"])
    source_availability = artifact.get("source_availability")
    if source_availability is not None and source_availability not in VALID_ARTIFACT_SOURCE_AVAILABILITY:
        raise ValueError(
            "artifact source_availability must be one of: "
            + ", ".join(sorted(VALID_ARTIFACT_SOURCE_AVAILABILITY))
        )
    deletion_behavior = artifact.get("deletion_behavior")
    if deletion_behavior is not None and deletion_behavior not in VALID_ARTIFACT_DELETION_BEHAVIOR:
        raise ValueError(
            "artifact deletion_behavior must be one of: "
            + ", ".join(sorted(VALID_ARTIFACT_DELETION_BEHAVIOR))
        )


def validate_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ValueError("entry must be a JSON object")
    missing = [field for field in REQUIRED_FIELDS if field not in entry]
    if missing:
        raise ValueError(f"entry missing required fields: {', '.join(missing)}")
    if entry["type"] not in VALID_TYPES:
        raise ValueError(f"entry type must be one of: {', '.join(sorted(VALID_TYPES))}")
    if entry["source"] not in VALID_SOURCES:
        raise ValueError(f"entry source must be one of: {', '.join(sorted(VALID_SOURCES))}")
    for field in ("timestamp", "summary", "context", "source", "type"):
        if not isinstance(entry[field], str) or not entry[field].strip():
            raise ValueError(f"entry field must be a non-empty string: {field}")
    for field in (
        "related_docs",
        "evidence_refs",
        "decision_threads",
        "exploration_paths",
        "abandoned_alternatives",
        "open_questions",
        "sync_suggestions",
    ):
        validate_string_list(entry, field)
    if "related_docs" in entry:
        relative_docs = [
            item for item in entry["related_docs"] if not Path(item).expanduser().is_absolute()
        ]
        if relative_docs:
            raise ValueError(
                "entry related_docs must contain absolute paths: "
                + ", ".join(relative_docs)
            )
    for field in ("project_area", "work_stream", "impact", "motivation", "root_cause"):
        if field in entry and (
            not isinstance(entry[field], str) or not entry[field].strip()
        ):
            raise ValueError(f"entry {field} must be a non-empty string when present")
    if "capture_depth" in entry and (
        not isinstance(entry["capture_depth"], str)
        or entry["capture_depth"] not in VALID_CAPTURE_DEPTHS
    ):
        raise ValueError(
            "entry capture_depth must be one of: "
            + ", ".join(sorted(VALID_CAPTURE_DEPTHS))
        )
    if 'correction' in entry:
        from tracework_state import validate_correction
        validate_correction(entry['correction'])
    validate_source_refs(entry)
    validate_lifecycle_transition(entry)
    validate_reporting(entry)
    if "status" in entry and entry["status"] not in VALID_STATUSES:
        raise ValueError(f"entry status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    if "archetype" in entry and entry["archetype"] not in VALID_ARCHETYPES:
        raise ValueError(
            f"entry archetype must be one of: {', '.join(sorted(VALID_ARCHETYPES))}"
        )
    validate_artifact_context(entry)
    if entry["source"] == "arch-doc":
        warn("entry source 'arch-doc' is legacy-only; new producers should use 'session-recap'")
    if entry["source"] == "session-recap" and "archetype" not in entry:
        warn("session-recap entry missing archetype; adaptive-depth consumers may treat it as legacy")
    archetype = entry.get("archetype")
    if isinstance(archetype, str) and archetype in ARCHETYPE_REQUIRED_FIELDS:
        for field in ARCHETYPE_REQUIRED_FIELDS[archetype]:
            if not has_value(entry, field):
                warn(f"{archetype} entry missing recommended field: {field}")
    return entry


def load_entries(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_entries = data if isinstance(data, list) else [data]
    return [validate_entry(entry) for entry in raw_entries]


def append_entries(
    entry_path: Path,
    cwd: Path,
    date_value: str | None,
    vault_override: Path | None,
    slug_override: str | None,
) -> dict[str, Any]:
    cfg, _ = resolve_config(cwd)
    vault = (vault_override or Path(str(cfg["knowledge_vault"]))).resolve()
    from tracework_state import validate_slug, validate_correction, effective_records, entry_hash, entry_id
    slug = validate_slug(slug_override or project_slug(cwd, vault))
    week = iso_week(date_value)
    entries = load_entries(entry_path)
    corrections = [entry for entry in entries if 'correction' in entry]
    if corrections:
        if len(entries) != 1:
            raise ValueError('append one correction at a time')
        ref = validate_correction(corrections[0]['correction'])
        week = ref['week']

    # timestamp is work time; captured_at is ingestion time. Historical recovery
    # must provide a timezone-aware source timestamp matching the explicit date.
    now_iso = dt.datetime.now().astimezone().isoformat()
    for entry in entries:
        if corrections:
            entry["captured_at"] = now_iso
            continue
        if date_value:
            occurred = dt.datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            if occurred.tzinfo is None or occurred.date() != dt.date.fromisoformat(date_value):
                raise ValueError("historical timestamp must include timezone and match --date")
        else:
            entry["timestamp"] = now_iso
        entry["captured_at"] = now_iso

    target_dir = vault / "raw" / "weeks" / week
    target_file = target_dir / f"{slug}.json"
    if target_file.resolve() != target_file:
        raise ValueError("raw storage symlinks cannot establish project ownership")
    target_dir.mkdir(parents=True, exist_ok=True)

    with json_lock(target_file):
        existing: list[Any] = []
        if target_file.exists():
            existing_data = json.loads(target_file.read_text(encoding="utf-8"))
            if not isinstance(existing_data, list):
                raise ValueError(f"target file is not a JSON array: {target_file}")
            existing = existing_data

        if corrections:
            correction = entries[0]['correction']
            ref = correction['target_ref']
            if ref['entry_index'] >= len(existing):
                raise ValueError('correction target missing')
            target = existing[ref['entry_index']]
            if not isinstance(target, dict) or target.get('timestamp') != ref['timestamp'] or entry_hash(target) != correction['target_hash']:
                raise ValueError('correction target timestamp/hash changed')
            if date_value and target['timestamp'][:10] != date_value:
                raise ValueError('correction --date must retain target work date')
            records = [dict(e, _source_week=week, _source_index=i, _source_path=str(target_file))
                       for i, e in enumerate(existing) if isinstance(e, dict)]
            effective, _, diagnostics = effective_records(records, slug)
            key = f"raw:{slug}:{week}:{ref['entry_index']}"
            if diagnostics or key not in {entry_id(e, slug) for e in effective}:
                raise ValueError('correction target is not an unambiguous effective chain tail')
            entries[0]['timestamp'] = target['timestamp']
        existing.extend(entries)
        write_json_atomic(target_file, existing)
    return {
        "week": week,
        "slug": slug,
        "vault": str(vault),
        "path": str(target_file),
        "entries_appended": len(entries),
        "total_entries": len(existing),
    }


def validate_artifact(artifact: Any) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise ValueError("artifact must be a JSON object")
    missing = [field for field in REQUIRED_ARTIFACT_FIELDS if field not in artifact]
    if missing:
        raise ValueError(f"artifact missing required fields: {', '.join(missing)}")
    for field in REQUIRED_ARTIFACT_FIELDS:
        if field == "status":
            continue
        if not isinstance(artifact[field], str) or not artifact[field].strip():
            raise ValueError(f"artifact field must be a non-empty string: {field}")
    if artifact["artifact_type"] not in VALID_ARTIFACT_TYPES:
        raise ValueError(
            "artifact artifact_type must be one of: "
            + ", ".join(sorted(VALID_ARTIFACT_TYPES))
        )
    if artifact["status"] not in VALID_ARTIFACT_STATUSES:
        raise ValueError(
            "artifact status must be one of: "
            + ", ".join(sorted(VALID_ARTIFACT_STATUSES))
        )
    if not Path(artifact["path"]).expanduser().is_absolute():
        raise ValueError(f"artifact path must be absolute: {artifact['path']}")
    for field in ARTIFACT_LIST_FIELDS:
        if field in artifact:
            if not isinstance(artifact[field], list) or not all(
                isinstance(item, str) for item in artifact[field]
            ):
                raise ValueError(f"artifact {field} must be a list of strings when present")
    if "repo_relative_path" in artifact and (
        not isinstance(artifact["repo_relative_path"], str)
        or not artifact["repo_relative_path"].strip()
    ):
        raise ValueError("artifact repo_relative_path must be a non-empty string when present")
    if "superseded_by" in artifact and artifact["superseded_by"] is not None:
        if not isinstance(artifact["superseded_by"], str) or not artifact["superseded_by"].strip():
            raise ValueError("artifact superseded_by must be a non-empty string or null")
    validate_artifact_dossier(artifact)
    return artifact


def load_artifact(path: Path) -> dict[str, Any]:
    return validate_artifact(json.loads(path.read_text(encoding="utf-8")))


def upsert_artifact(
    artifact_path: Path,
    cwd: Path,
    vault_override: Path | None,
    slug_override: str | None,
) -> dict[str, Any]:
    cfg, _ = resolve_config(cwd)
    vault = vault_override or Path(str(cfg["knowledge_vault"]))
    artifact = load_artifact(artifact_path)
    slug = slug_override or project_slug(cwd, vault)
    target_dir = vault / "raw" / "artifacts"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{slug}.json"

    with json_lock(target_file):
        existing: list[Any] = []
        if target_file.exists():
            existing_data = json.loads(target_file.read_text(encoding="utf-8"))
            if not isinstance(existing_data, list):
                raise ValueError(f"target file is not a JSON array: {target_file}")
            existing = existing_data

        action = "created"
        for index, item in enumerate(existing):
            if isinstance(item, dict) and item.get("id") == artifact["id"]:
                existing[index] = artifact
                action = "updated"
                break
        else:
            existing.append(artifact)

        write_json_atomic(target_file, existing)
    return {
        "slug": slug,
        "path": str(target_file),
        "artifact_id": artifact["id"],
        "action": action,
        "total_artifacts": len(existing),
    }


def register_project(
    cwd: Path,
    vault_override: Path | None,
    name: str | None,
    slug_override: str | None,
    priority: str | None,
    reporting_group: str | None,
) -> dict[str, Any]:
    cfg, _ = resolve_config(cwd)
    vault = vault_override or Path(str(cfg["knowledge_vault"]))
    slug = slug_override or project_slug(cwd, vault)
    project_name = name or slug.replace("-", " ").title()
    configured_group = cfg.get("profile", {}).get("reporting_group") if isinstance(cfg.get("profile"), dict) else None
    resolved_group = reporting_group or configured_group
    if resolved_group is not None:
        validate_non_empty_string("reporting_group", resolved_group)
    project_path = str(cwd.resolve())

    target_dir = vault / "raw"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "projects.json"

    with json_lock(target_file):
        existing: list[dict[str, Any]] = []
        if target_file.exists():
            data = json.loads(target_file.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError(f"target file is not a JSON array: {target_file}")
            existing = data

        updated = False
        for index, item in enumerate(existing):
            if isinstance(item, dict) and same_path(str(item.get("path", "")), cwd):
                if not resolved_group and isinstance(item.get("reporting_group"), str):
                    resolved_group = item["reporting_group"]
                existing[index]["name"] = project_name
                existing[index]["slug"] = slug
                existing[index]["path"] = project_path
                if priority:
                    existing[index]["priority"] = priority
                if resolved_group:
                    existing[index]["reporting_group"] = resolved_group
                updated = True
                break

        if not updated:
            entry: dict[str, Any] = {
                "name": project_name,
                "slug": slug,
                "path": project_path,
            }
            if priority:
                entry["priority"] = priority
            if resolved_group:
                entry["reporting_group"] = resolved_group
            existing.append(entry)

        write_json_atomic(target_file, existing)
    return {
        "action": "updated" if updated else "registered",
        "name": project_name,
        "slug": slug,
        "path": project_path,
        "reporting_group": resolved_group or "unassigned",
        "total_projects": len(existing),
    }


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def command_week(args: argparse.Namespace) -> int:
    print(iso_week(args.date))
    return 0


def command_resolve_config(args: argparse.Namespace) -> int:
    cfg, sources = resolve_config(Path(args.cwd))
    print_json({"config": cfg, "sources": sources})
    return 0


def command_project_slug(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve() if args.vault else None
    print(project_slug(Path(args.cwd), vault))
    return 0


def command_resolve_scope(args: argparse.Namespace) -> int:
    print_json(resolve_scope(Path(args.cwd).expanduser().resolve(), args.scope, args.purpose))
    return 0


def command_append_entry(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve() if args.vault else None
    result = append_entries(
        entry_path=Path(args.entry).expanduser().resolve(),
        cwd=Path(args.cwd).expanduser().resolve(),
        date_value=args.date,
        vault_override=vault,
        slug_override=args.slug,
    )
    print_json(result)
    return 0


def command_upsert_artifact(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve() if args.vault else None
    result = upsert_artifact(
        artifact_path=Path(args.artifact).expanduser().resolve(),
        cwd=Path(args.cwd).expanduser().resolve(),
        vault_override=vault,
        slug_override=args.slug,
    )
    print_json(result)
    return 0


def command_register_project(args: argparse.Namespace) -> int:
    vault = Path(args.vault).expanduser().resolve() if args.vault else None
    result = register_project(
        cwd=Path(args.cwd).expanduser().resolve(),
        vault_override=vault,
        name=args.name,
        slug_override=args.slug,
        priority=args.priority,
        reporting_group=args.reporting_group,
    )
    print_json(result)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tracework raw storage helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    week_parser = subparsers.add_parser("week", help="Print ISO week string")
    week_parser.add_argument("--date", help="Date in YYYY-MM-DD format")
    week_parser.set_defaults(func=command_week)

    config_parser = subparsers.add_parser("resolve-config", help="Resolve Tracework config")
    config_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    config_parser.set_defaults(func=command_resolve_config)

    scope_parser = subparsers.add_parser("resolve-scope", help="Resolve report or session scope without reading evidence")
    scope_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    scope_parser.add_argument("--scope", help="Explicit user-requested group or all")
    scope_parser.add_argument("--purpose", choices=["report", "session"], required=True)
    scope_parser.set_defaults(func=command_resolve_scope)

    slug_parser = subparsers.add_parser("project-slug", help="Resolve project slug")
    slug_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    slug_parser.add_argument("--vault", help="Knowledge vault override")
    slug_parser.set_defaults(func=command_project_slug)

    append_parser = subparsers.add_parser("append-entry", help="Append raw entry JSON")
    append_parser.add_argument("--entry", required=True, help="Path to entry JSON object or array")
    append_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    append_parser.add_argument("--date", help="Date in YYYY-MM-DD format for target ISO week")
    append_parser.add_argument("--vault", help="Knowledge vault override")
    append_parser.add_argument("--slug", help="Project slug override")
    append_parser.set_defaults(func=command_append_entry)

    artifact_parser = subparsers.add_parser("upsert-artifact", help="Upsert artifact index JSON")
    artifact_parser.add_argument("--artifact", required=True, help="Path to artifact JSON object")
    artifact_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    artifact_parser.add_argument("--vault", help="Knowledge vault override")
    artifact_parser.add_argument("--slug", help="Project slug override")
    artifact_parser.set_defaults(func=command_upsert_artifact)

    register_parser = subparsers.add_parser("register-project", help="Register project in projects.json")
    register_parser.add_argument("--cwd", default=os.getcwd(), help="Project working directory")
    register_parser.add_argument("--vault", help="Knowledge vault override")
    register_parser.add_argument("--name", help="Human-readable project name")
    register_parser.add_argument("--slug", help="Project slug override")
    register_parser.add_argument("--priority", choices=["core", "supporting", "exploratory"])
    register_parser.add_argument("--reporting-group", help="Reporting partition such as work or personal")
    register_parser.set_defaults(func=command_register_project)

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
