#!/usr/bin/env python3
"""Index and normalize local agent sessions for Tracework Capture Day.

The Stop hook records metadata only. Transcript content is read only after an
explicit Capture Day invocation has resolved and accepted the reporting scope.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

import tracework_raw


SCHEMA_VERSION = "tracework.session_index.v1"
MAX_CHUNK_BYTES = 64 * 1024
NOISE_PREFIXES = (
    "<recommended_plugins>",
    "# AGENTS.md instructions for ",
    "<environment_context>",
    "<permissions instructions>",
    "<apps_instructions>",
    "<skill>",
    "<system-reminder>",
    "<task-notification>",
)


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def parse_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
    return parsed


def timestamp_key(value: str | None) -> float:
    parsed = parse_timestamp(value)
    return parsed.timestamp() if parsed else float("-inf")


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "session"


def index_root() -> Path:
    override = os.environ.get("TRACEWORK_SESSION_INDEX")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".tracework" / "session-index"


def runtime_name() -> str:
    explicit = os.environ.get("TRACEWORK_SESSION_RUNTIME")
    if explicit in {"codex", "claude"}:
        return explicit
    if os.environ.get("PLUGIN_ROOT"):
        return "codex"
    return "claude"


def manifest_path(runtime: str, session_id: str) -> Path:
    return index_root() / runtime / f"{safe_id(session_id)}.json"


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


@contextmanager
def manifest_lock(runtime: str, session_id: str):
    path = manifest_path(runtime, session_id)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    with tracework_raw.json_lock(path):
        yield path


def session_scan_settings(cwd: Path) -> tuple[bool, int]:
    cfg, _ = tracework_raw.resolve_config(cwd)
    section = cfg.get("session_scan")
    if not isinstance(section, dict):
        return False, 30
    enabled = section.get("enabled") is True
    retention = section.get("retention_days", 30)
    if not isinstance(retention, int) or retention < 1:
        retention = 30
    return enabled, retention


def clean_expired(retention_days: int) -> None:
    threshold = dt.datetime.now().astimezone() - dt.timedelta(days=retention_days)
    root = index_root()
    if not root.exists():
        return
    for path in root.glob("*/*.json"):
        manifest = read_json(path, {})
        seen = parse_timestamp(manifest.get("last_seen_at")) if isinstance(manifest, dict) else None
        if seen is not None and seen < threshold:
            try:
                path.unlink()
            except OSError:
                pass


def observe() -> int:
    """Best-effort Stop hook. Never block the host session."""
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        session_id = payload.get("session_id")
        transcript_path = payload.get("transcript_path")
        cwd_value = payload.get("cwd")
        if not all(isinstance(value, str) and value.strip() for value in (session_id, transcript_path, cwd_value)):
            return 0
        cwd = Path(cwd_value).expanduser().resolve()
        enabled, retention = session_scan_settings(cwd)
        if not enabled:
            return 0

        runtime = runtime_name()
        stamp = now_iso()
        with manifest_lock(runtime, session_id) as path:
            manifest = read_json(path, {})
            if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
                manifest = {
                    "schema_version": SCHEMA_VERSION,
                    "runtime": runtime,
                    "session_id": session_id,
                    "first_seen_at": stamp,
                    "cwd_history": [],
                    "scanned_through": {},
                }
            transcript = Path(transcript_path).expanduser()
            if not transcript.is_absolute():
                transcript = cwd / transcript
            manifest["transcript_path"] = str(transcript.resolve())
            manifest["last_seen_at"] = stamp

            history = manifest.setdefault("cwd_history", [])
            if not isinstance(history, list):
                history = []
                manifest["cwd_history"] = history
            existing = next(
                (item for item in history if isinstance(item, dict) and item.get("cwd") == str(cwd)),
                None,
            )
            if existing is None:
                history.append({"cwd": str(cwd), "first_seen_at": stamp, "last_seen_at": stamp})
            else:
                existing["last_seen_at"] = stamp

            tracework_raw.write_json_atomic(path, manifest)
        clean_expired(retention)
    except Exception:
        return 0
    return 0


def profile_for_cwd(cwd: Path) -> dict[str, Any]:
    cfg, _ = tracework_raw.resolve_config(cwd)
    project_config = tracework_raw.find_project_config(cwd)
    if project_config is None:
        return {"reporting_group": "unassigned", "cwd": str(cwd)}
    root = project_config.parent.parent.resolve()
    profile = cfg.get("profile") if isinstance(cfg.get("profile"), dict) else {}
    project_profile = tracework_raw.load_yaml_config(project_config).get("profile", {})
    group = project_profile.get("reporting_group") if isinstance(project_profile, dict) else None
    if not isinstance(group, str) or not group.strip():
        group = "unassigned"
    slug = cfg.get("project_slug")
    if not isinstance(slug, str) or not slug.strip():
        slug = tracework_raw.slugify(root.name)
    name = profile.get("project_name")
    if not isinstance(name, str) or not name.strip():
        name = root.name
    return {
        "project_root": str(root),
        "project_slug": slug.strip(),
        "project_name": name.strip(),
        "reporting_group": group.strip(),
        "knowledge_vault": cfg.get("knowledge_vault"),
    }


def classify_manifest(manifest: dict[str, Any], scope: str) -> tuple[dict[str, Any] | None, str | None]:
    history = manifest.get("cwd_history")
    if not isinstance(history, list) or not history:
        return None, "missing_cwd"
    profiles: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in history:
        if not isinstance(item, dict) or not isinstance(item.get("cwd"), str):
            continue
        profile = profile_for_cwd(Path(item["cwd"]))
        key = (
            str(profile.get("project_root", "")),
            str(profile.get("project_slug", "")),
            str(profile.get("reporting_group", "unassigned")),
        )
        profiles[key] = profile
    if len(profiles) != 1:
        return None, "ambiguous_project_or_group"
    profile = next(iter(profiles.values()))
    group = profile["reporting_group"]
    if group == "unassigned":
        return None, "unassigned"
    if scope != "all" and group != scope:
        return None, "out_of_scope"
    return profile, None


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type not in {"text", "input_text", "output_text"}:
            continue
        text = block.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n\n".join(parts)


def record_message(record: dict[str, Any]) -> tuple[str, str, str] | None:
    timestamp = record.get("timestamp")
    if not isinstance(timestamp, str):
        return None

    if record.get("type") == "response_item":
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "message":
            return None
        role = payload.get("role")
        text = content_text(payload.get("content"))
    elif record.get("type") in {"user", "assistant"}:
        message = record.get("message")
        if not isinstance(message, dict):
            return None
        role = message.get("role", record.get("type"))
        text = content_text(message.get("content"))
    else:
        return None

    if role not in {"user", "assistant"} or not text:
        return None
    stripped = text.lstrip()
    if role == "user" and stripped.startswith(NOISE_PREFIXES):
        return None
    return timestamp, role, text


def normalized_messages(
    path: Path,
    target: dt.date,
    after: str | None,
) -> tuple[list[dict[str, str]], int, int]:
    messages: list[dict[str, str]] = []
    parsed_records = 0
    recognized_messages = 0
    after_key = timestamp_key(after)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            parsed_records += 1
            extracted = record_message(record)
            if extracted is None:
                continue
            recognized_messages += 1
            timestamp, role, text = extracted
            parsed = parse_timestamp(timestamp)
            if parsed is None or parsed.astimezone().date() != target:
                continue
            if parsed.timestamp() <= after_key:
                continue
            message = {"timestamp": parsed.astimezone().isoformat(), "role": role, "text": text}
            if role == "assistant" and messages and messages[-1]["role"] == "assistant":
                messages[-1] = message
            else:
                messages.append(message)
    return messages, recognized_messages, parsed_records


def split_text(text: str, byte_limit: int) -> list[str]:
    if len(text.encode("utf-8")) <= byte_limit:
        return [text]
    parts: list[str] = []
    remaining = text
    while remaining:
        low, high = 1, len(remaining)
        while low < high:
            middle = (low + high + 1) // 2
            if len(remaining[:middle].encode("utf-8")) <= byte_limit:
                low = middle
            else:
                high = middle - 1
        parts.append(remaining[:low])
        remaining = remaining[low:]
    return parts


def chunk_messages(messages: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    expanded: list[dict[str, str]] = []
    for message in messages:
        for index, part in enumerate(split_text(message["text"], MAX_CHUNK_BYTES - 1024), start=1):
            item = dict(message)
            item["text"] = part
            if index > 1:
                item["part"] = str(index)
            expanded.append(item)

    chunks: list[list[dict[str, str]]] = []
    current: list[dict[str, str]] = []
    current_bytes = 2  # JSON list brackets
    for message in expanded:
        message_bytes = len(
            json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
        separator_bytes = 1 if current else 0
        if current and current_bytes + separator_bytes + message_bytes > MAX_CHUNK_BYTES:
            chunks.append(current)
            current = [message]
            current_bytes = 2 + message_bytes
        else:
            current.append(message)
            current_bytes += separator_bytes + message_bytes
    if current:
        chunks.append(current)
    return chunks


def source_ref(runtime: str, session_id: str) -> str:
    return f"session:{runtime}:{session_id}"


def raw_watermark(profile: dict[str, Any], runtime: str, session_id: str, target: dt.date) -> str | None:
    vault = profile.get("knowledge_vault")
    slug = profile.get("project_slug")
    if not isinstance(vault, str) or not isinstance(slug, str):
        return None
    path = Path(vault) / "raw" / "weeks" / tracework_raw.iso_week(target.isoformat()) / f"{slug}.json"
    entries = read_json(path, [])
    if not isinstance(entries, list):
        return None
    wanted = source_ref(runtime, session_id)
    timestamps: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        refs = entry.get("source_refs")
        if not isinstance(refs, list):
            continue
        for ref in refs:
            if not isinstance(ref, dict) or ref.get("type") != "conversation" or ref.get("ref") != wanted:
                continue
            timestamp = ref.get("timestamp")
            parsed = parse_timestamp(timestamp)
            if parsed is not None and parsed.astimezone().date() == target:
                timestamps.append(parsed.astimezone().isoformat())
    return max(timestamps, key=timestamp_key) if timestamps else None


def scan_enabled_payload(date_value: str, scope: str) -> dict[str, Any] | None:
    enabled, _ = session_scan_settings(Path.cwd())
    if enabled:
        return None
    return {
        "date": date_value,
        "scope": scope,
        "sessions": [],
        "skipped": [],
        "error": "session_scan_disabled",
    }


def manifest_overlaps_date(manifest: dict[str, Any], target: dt.date) -> bool:
    first = parse_timestamp(manifest.get("first_seen_at"))
    last = parse_timestamp(manifest.get("last_seen_at"))
    if first is None or last is None:
        return True
    return first.astimezone().date() <= target <= last.astimezone().date()


def list_day(date_value: str, scope: str) -> int:
    disabled = scan_enabled_payload(date_value, scope)
    if disabled is not None:
        print(json.dumps(disabled, ensure_ascii=False, indent=2))
        return 0
    target = dt.date.fromisoformat(date_value)
    sessions: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    root = index_root()
    for path in sorted(root.glob("*/*.json")) if root.exists() else []:
        manifest = read_json(path, {})
        if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
            skipped.append({"manifest": str(path), "reason": "unsupported_manifest"})
            continue
        runtime = manifest.get("runtime")
        session_id = manifest.get("session_id")
        transcript = manifest.get("transcript_path")
        if not all(isinstance(value, str) and value for value in (runtime, session_id, transcript)):
            skipped.append({"manifest": str(path), "reason": "invalid_manifest"})
            continue
        if not manifest_overlaps_date(manifest, target):
            continue
        profile, reason = classify_manifest(manifest, scope)
        if profile is None:
            skipped.append({"session_id": session_id, "runtime": runtime, "reason": reason or "excluded"})
            continue
        sessions.append(
            {
                "runtime": runtime,
                "session_id": session_id,
                "project_root": profile["project_root"],
                "project_slug": profile["project_slug"],
                "project_name": profile["project_name"],
                "reporting_group": profile["reporting_group"],
            }
        )
    print(json.dumps({"date": date_value, "scope": scope, "sessions": sessions, "skipped": skipped}, ensure_ascii=False, indent=2))
    return 0


def collect_session(
    date_value: str,
    scope: str,
    runtime: str,
    session_id: str,
    chunk_number: int,
) -> int:
    disabled = scan_enabled_payload(date_value, scope)
    if disabled is not None:
        print(json.dumps(disabled, ensure_ascii=False, indent=2))
        return 0
    target = dt.date.fromisoformat(date_value)
    path = manifest_path(runtime, session_id)
    manifest = read_json(path, {})
    if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
        print(json.dumps({"date": date_value, "scope": scope, "skip": "unsupported_manifest"}))
        return 0
    if manifest.get("runtime") != runtime or manifest.get("session_id") != session_id:
        print(json.dumps({"date": date_value, "scope": scope, "skip": "invalid_manifest"}))
        return 0
    profile, reason = classify_manifest(manifest, scope)
    if profile is None:
        print(json.dumps({"date": date_value, "scope": scope, "skip": reason or "excluded"}))
        return 0

    scanned = manifest.get("scanned_through")
    local_watermark = scanned.get(date_value) if isinstance(scanned, dict) else None
    raw_mark = raw_watermark(profile, runtime, session_id, target)
    watermark_values = [value for value in (local_watermark, raw_mark) if isinstance(value, str)]
    watermark = max(watermark_values, key=timestamp_key) if watermark_values else None

    transcript = manifest.get("transcript_path")
    if not isinstance(transcript, str):
        print(json.dumps({"date": date_value, "scope": scope, "skip": "invalid_manifest"}))
        return 0
    transcript_path = Path(transcript).expanduser()
    if not transcript_path.is_file():
        print(json.dumps({"date": date_value, "scope": scope, "skip": "missing_transcript"}))
        return 0
    try:
        messages, recognized, parsed_records = normalized_messages(transcript_path, target, watermark)
    except OSError:
        print(json.dumps({"date": date_value, "scope": scope, "skip": "unreadable_transcript"}))
        return 0
    if recognized == 0 and parsed_records > 0:
        print(json.dumps({"date": date_value, "scope": scope, "skip": "unsupported_transcript"}))
        return 0
    if not messages:
        print(json.dumps({"date": date_value, "scope": scope, "skip": "no_new_messages"}))
        return 0

    chunks = chunk_messages(messages)
    if chunk_number < 1 or chunk_number > len(chunks):
        raise ValueError(f"--chunk must be between 1 and {len(chunks)}")
    print(
        json.dumps(
            {
                "date": date_value,
                "scope": scope,
                "session": {
                    "runtime": runtime,
                    "session_id": session_id,
                    "source_ref": source_ref(runtime, session_id),
                    "project_root": profile["project_root"],
                    "project_slug": profile["project_slug"],
                    "project_name": profile["project_name"],
                    "reporting_group": profile["reporting_group"],
                    "captured_after": watermark,
                    "captured_through": messages[-1]["timestamp"],
                    "chunk": chunk_number,
                    "chunk_count": len(chunks),
                    "messages": chunks[chunk_number - 1],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def mark_scanned(runtime: str, session_id: str, date_value: str, through: str) -> int:
    parsed_through = parse_timestamp(through)
    target_date = dt.date.fromisoformat(date_value)
    if parsed_through is None:
        raise ValueError("--through must be an ISO 8601 timestamp")
    if parsed_through.astimezone().date() != target_date:
        raise ValueError("--through must fall on --date in the local timezone")
    with manifest_lock(runtime, session_id) as path:
        manifest = read_json(path, {})
        if not isinstance(manifest, dict) or manifest.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"session manifest not found: {runtime}/{session_id}")
        scanned = manifest.setdefault("scanned_through", {})
        if not isinstance(scanned, dict):
            scanned = {}
            manifest["scanned_through"] = scanned
        previous = scanned.get(date_value)
        if not isinstance(previous, str) or timestamp_key(through) > timestamp_key(previous):
            scanned[date_value] = parsed_through.astimezone().isoformat()
        tracework_raw.write_json_atomic(path, manifest)
    print(json.dumps({"runtime": runtime, "session_id": session_id, "date": date_value, "scanned_through": scanned[date_value]}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tracework local session index helper")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("observe", help="Record metadata from a Stop hook")

    list_parser = subparsers.add_parser("list-day", help="List scoped session manifests without reading transcripts")
    list_parser.add_argument("--date", default=dt.date.today().isoformat())
    list_parser.add_argument("--scope", required=True)

    collect = subparsers.add_parser("collect-session", help="Return one bounded normalized transcript chunk")
    collect.add_argument("--date", default=dt.date.today().isoformat())
    collect.add_argument("--scope", required=True)
    collect.add_argument("--runtime", required=True, choices=("codex", "claude"))
    collect.add_argument("--session-id", required=True)
    collect.add_argument("--chunk", type=int, default=1)

    mark = subparsers.add_parser("mark-scanned", help="Advance a session scan watermark")
    mark.add_argument("--runtime", required=True, choices=("codex", "claude"))
    mark.add_argument("--session-id", required=True)
    mark.add_argument("--date", required=True)
    mark.add_argument("--through", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "observe":
        return observe()
    if args.command == "list-day":
        return list_day(args.date, args.scope)
    if args.command == "collect-session":
        return collect_session(args.date, args.scope, args.runtime, args.session_id, args.chunk)
    if args.command == "mark-scanned":
        return mark_scanned(args.runtime, args.session_id, args.date, args.through)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
