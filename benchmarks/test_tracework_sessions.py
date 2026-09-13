#!/usr/bin/env python3
"""Executable regression coverage for Tracework session indexing and scanning."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor


REPO_ROOT = Path(__file__).resolve().parents[1]
SESSION_HELPER = REPO_ROOT / "skills" / "capture" / "scripts" / "tracework_sessions.py"
RAW_HELPER = REPO_ROOT / "skills" / "capture" / "scripts" / "tracework_raw.py"
TARGET_DATE = dt.datetime.now().astimezone().date().isoformat()
TARGET_WEEK = dt.date.fromisoformat(TARGET_DATE).strftime("%G-W%V")


def target_timestamp(hour: int, minute: int = 0, second: int = 0) -> str:
    target = dt.date.fromisoformat(TARGET_DATE)
    return dt.datetime(target.year, target.month, target.day, hour, minute, second).astimezone().isoformat(
        timespec="seconds"
    )


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")


def codex_message(timestamp: str, role: str, text: str) -> dict:
    return {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": role,
            "content": [{"type": "input_text" if role != "assistant" else "output_text", "text": text}],
        },
    }


def claude_message(timestamp: str, role: str, text: str) -> dict:
    return {
        "timestamp": timestamp,
        "type": role,
        "message": {"role": role, "content": [{"type": "text", "text": text}]},
    }


class SessionScanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="tracework-session-test-")
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.index = self.root / "index"
        self.vault = self.root / "vault"
        self.home.mkdir()
        self.vault.mkdir()
        (self.home / ".tracework").mkdir()
        (self.home / ".tracework" / "config.yaml").write_text(
            "\n".join(
                [
                    f"knowledge_vault: {self.vault}",
                    "profile:",
                    "  default_reporting_group: work",
                    "session_scan:",
                    "  enabled: true",
                    "  retention_days: 30",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.work = self.make_project("work-project", "work", "Work Project")
        self.personal = self.make_project("personal-project", "personal", "Personal Project")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_project(self, slug: str, group: str, name: str) -> Path:
        project = self.root / slug
        config_dir = project / ".tracework"
        config_dir.mkdir(parents=True)
        (config_dir / "config.yaml").write_text(
            "\n".join(
                [
                    f"project_slug: {slug}",
                    "profile:",
                    f"  project_name: {name}",
                    f"  reporting_group: {group}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return project

    def env(self, runtime: str = "codex") -> dict[str, str]:
        env = dict(os.environ)
        env.update(
            {
                "HOME": str(self.home),
                "USERPROFILE": str(self.home),
                "TRACEWORK_SESSION_INDEX": str(self.index),
                "TRACEWORK_SESSION_RUNTIME": runtime,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUTF8": "1",
            }
        )
        return env

    def run_helper(
        self,
        *args: str,
        runtime: str = "codex",
        payload: dict | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-B", str(SESSION_HELPER), *args],
            input=json.dumps(payload) if payload is not None else None,
            text=True,
            capture_output=True,
            cwd=self.home,
            env=self.env(runtime),
            check=True,
        )

    def observe(self, session_id: str, cwd: Path, transcript: Path, runtime: str = "codex") -> dict:
        result = self.run_helper(
            "observe",
            runtime=runtime,
            payload={
                "session_id": session_id,
                "transcript_path": str(transcript),
                "cwd": str(cwd),
                "hook_event_name": "Stop",
            },
        )
        self.assertEqual(result.stdout, "")
        manifest = self.index / runtime / f"{session_id}.json"
        return json.loads(manifest.read_text(encoding="utf-8"))

    def list_day(self, scope: str = "work") -> dict:
        result = self.run_helper("list-day", "--date", TARGET_DATE, "--scope", scope)
        return json.loads(result.stdout)

    def collect_session(self, runtime: str, session_id: str, scope: str = "work", chunk: int = 1) -> dict:
        result = self.run_helper(
            "collect-session",
            "--date",
            TARGET_DATE,
            "--scope",
            scope,
            "--runtime",
            runtime,
            "--session-id",
            session_id,
            "--chunk",
            str(chunk),
            runtime=runtime,
        )
        return json.loads(result.stdout)

    def test_nested_yaml_fallback_supports_profile_and_session_scan(self) -> None:
        spec = importlib.util.spec_from_file_location("tracework_raw_test", RAW_HELPER)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        module.yaml = None
        parsed = module.parse_simple_yaml(
            "profile:\n  reporting_group: work\nsession_scan:\n  enabled: true\n  retention_days: 30\n"
            "daily_note:\n  repos:\n    - /tmp/one\n    - /tmp/two\n"
        )
        self.assertEqual(parsed["profile"]["reporting_group"], "work")
        self.assertIs(parsed["session_scan"]["enabled"], True)
        self.assertEqual(parsed["session_scan"]["retention_days"], 30)
        self.assertEqual(parsed["daily_note"]["repos"], ["/tmp/one", "/tmp/two"])

    def test_disabled_hook_is_a_noop(self) -> None:
        (self.home / ".tracework" / "config.yaml").write_text(
            "session_scan:\n  enabled: false\n",
            encoding="utf-8",
        )
        transcript = self.root / "disabled.jsonl"
        write_jsonl(transcript, [codex_message(target_timestamp(9), "user", "hello")])
        result = self.run_helper(
            "observe",
            payload={"session_id": "disabled", "transcript_path": str(transcript), "cwd": str(self.work)},
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.index.exists())
        collected = self.list_day("work")
        self.assertEqual(collected["error"], "session_scan_disabled")
        self.assertEqual(collected["sessions"], [])

    def test_work_scope_filters_before_personal_transcript_read(self) -> None:
        work_transcript = self.root / "work.jsonl"
        write_jsonl(
            work_transcript,
            [
                codex_message(target_timestamp(9), "developer", "hidden instructions"),
                codex_message(target_timestamp(9, 1), "user", "<environment_context>noise</environment_context>"),
                codex_message(target_timestamp(9, 2), "user", "Fix the retry boundary"),
                codex_message(target_timestamp(9, 3), "assistant", "Working on it"),
                codex_message(target_timestamp(9, 4), "assistant", "Moved validation before export and tests pass"),
            ],
        )
        personal_missing = self.root / "personal-does-not-exist.jsonl"
        manifest = self.observe("work-session", self.work, work_transcript)
        self.observe("personal-session", self.personal, personal_missing)

        self.assertNotIn("Fix the retry boundary", json.dumps(manifest))
        listed = self.list_day("work")
        self.assertEqual(len(listed["sessions"]), 1)
        collected = self.collect_session("codex", "work-session")
        text = json.dumps(collected["session"], ensure_ascii=False)
        self.assertIn("Fix the retry boundary", text)
        self.assertIn("Moved validation before export", text)
        self.assertNotIn("Working on it", text)
        personal_skip = next(item for item in listed["skipped"] if item.get("session_id") == "personal-session")
        self.assertEqual(personal_skip["reason"], "out_of_scope")

    def test_claude_adapter_and_scan_watermark_are_incremental(self) -> None:
        transcript = self.root / "claude.jsonl"
        write_jsonl(
            transcript,
            [
                claude_message(target_timestamp(10), "user", "Choose the storage boundary"),
                claude_message(target_timestamp(10, 1), "assistant", "Drafting"),
                claude_message(target_timestamp(10, 2), "assistant", "Kept raw entries as semantic truth"),
            ],
        )
        self.observe("claude-session", self.work, transcript, runtime="claude")
        first = self.collect_session("claude", "claude-session")
        session = first["session"]
        through = session["captured_through"]
        text = json.dumps(session, ensure_ascii=False)
        self.assertIn("Choose the storage boundary", text)
        self.assertIn("Kept raw entries as semantic truth", text)
        self.assertNotIn("Drafting", text)

        self.run_helper(
            "mark-scanned",
            "--runtime",
            "claude",
            "--session-id",
            "claude-session",
            "--date",
            TARGET_DATE,
            "--through",
            through,
            runtime="claude",
        )
        second = self.collect_session("claude", "claude-session")
        self.assertEqual(second["skip"], "no_new_messages")

        with transcript.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(claude_message(target_timestamp(10, 5), "user", "Add the final evidence gap")) + "\n")
            handle.write(json.dumps(claude_message(target_timestamp(10, 6), "assistant", "Recorded missing install smoke")) + "\n")
        third = self.collect_session("claude", "claude-session")
        delta = third["session"]
        delta_text = json.dumps(delta, ensure_ascii=False)
        self.assertIn("Add the final evidence gap", delta_text)
        self.assertNotIn("Choose the storage boundary", delta_text)

    def test_raw_source_ref_recovers_watermark_after_local_state_loss(self) -> None:
        transcript = self.root / "raw-watermark.jsonl"
        write_jsonl(
            transcript,
            [
                codex_message(target_timestamp(11), "user", "Old prompt"),
                codex_message(target_timestamp(11, 1), "assistant", "Old result"),
                codex_message(target_timestamp(11, 5), "user", "New prompt"),
                codex_message(target_timestamp(11, 6), "assistant", "New result"),
            ],
        )
        self.observe("raw-session", self.work, transcript)
        raw_dir = self.vault / "raw" / "weeks" / TARGET_WEEK
        raw_dir.mkdir(parents=True)
        (raw_dir / "work-project.json").write_text(
            json.dumps(
                [
                    {
                        "source_refs": [
                            {
                                "type": "conversation",
                                "ref": "session:codex:raw-session",
                                "timestamp": target_timestamp(11, 1),
                            }
                        ]
                    }
                ]
            ),
            encoding="utf-8",
        )
        collected = self.collect_session("codex", "raw-session")
        session = collected["session"]
        text = json.dumps(session, ensure_ascii=False)
        self.assertIn("New prompt", text)
        self.assertNotIn("Old prompt", text)

    def test_mixed_project_session_fails_closed(self) -> None:
        transcript = self.root / "mixed.jsonl"
        write_jsonl(transcript, [codex_message(target_timestamp(12), "user", "mixed")])
        self.observe("mixed-session", self.work, transcript)
        self.observe("mixed-session", self.personal, transcript)
        collected = self.list_day("all")
        self.assertFalse(any(item["session_id"] == "mixed-session" for item in collected["sessions"]))
        skipped = next(item for item in collected["skipped"] if item.get("session_id") == "mixed-session")
        self.assertEqual(skipped["reason"], "ambiguous_project_or_group")

    def test_concurrent_observations_preserve_scope_history_and_private_modes(self) -> None:
        transcript = self.root / "concurrent.jsonl"
        write_jsonl(transcript, [codex_message(target_timestamp(12, 30), "user", "mixed")])
        payloads = [
            {"session_id": "concurrent-session", "transcript_path": str(transcript), "cwd": str(cwd)}
            for cwd in (self.work, self.personal)
            for _ in range(8)
        ]
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda payload: self.run_helper("observe", payload=payload), payloads))

        manifest_path = self.index / "codex" / "concurrent-session.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            {item["cwd"] for item in manifest["cwd_history"]},
            {str(self.work.resolve()), str(self.personal.resolve())},
        )
        if os.name != "nt":
            self.assertEqual(manifest_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(manifest_path.parent.stat().st_mode & 0o777, 0o700)
        listed = self.list_day("all")
        skipped = next(item for item in listed["skipped"] if item.get("session_id") == "concurrent-session")
        self.assertEqual(skipped["reason"], "ambiguous_project_or_group")

    def test_unknown_transcript_format_fails_closed(self) -> None:
        transcript = self.root / "unknown.jsonl"
        write_jsonl(
            transcript,
            [{"timestamp": target_timestamp(13), "type": "future_host_record", "body": "do not infer"}],
        )
        self.observe("unknown-session", self.work, transcript)
        listed = self.list_day("work")
        self.assertTrue(any(item["session_id"] == "unknown-session" for item in listed["sessions"]))
        collected = self.collect_session("codex", "unknown-session")
        self.assertEqual(collected["skip"], "unsupported_transcript")

    def test_targeted_project_filter_and_partial_read_do_not_advance(self) -> None:
        other = self.make_project('other-work', 'work', 'Other Work')
        transcript = self.root / 'targeted.jsonl'
        write_jsonl(transcript, [codex_message(target_timestamp(14), 'user', 'x' * 70000)])
        self.observe('selected', self.work, transcript)
        self.observe('excluded', other, transcript)
        before = {str(p): p.read_bytes() for p in self.index.glob('*/*.json')}
        listed = json.loads(self.run_helper('list-day', '--date', TARGET_DATE, '--scope', 'work',
                                           '--project-root', str(self.work)).stdout)
        self.assertEqual([s['session_id'] for s in listed['sessions']], ['selected'])
        excluded = json.loads(self.run_helper('collect-session', '--date', TARGET_DATE, '--scope', 'work',
            '--runtime', 'codex', '--session-id', 'excluded', '--project-root', str(self.work)).stdout)
        self.assertEqual(excluded['skip'], 'project_mismatch')
        selected = json.loads(self.run_helper('collect-session', '--date', TARGET_DATE, '--scope', 'work',
            '--runtime', 'codex', '--session-id', 'selected', '--project-root', str(self.work), '--chunk', '1').stdout)
        self.assertGreater(selected['session']['chunk_count'], 1)
        self.assertEqual({str(p): p.read_bytes() for p in self.index.glob('*/*.json')}, before)
        self.assertFalse((self.vault / 'raw/weeks').exists())

    def test_large_session_returns_one_bounded_chunk_at_a_time(self) -> None:
        transcript = self.root / "large.jsonl"
        write_jsonl(
            transcript,
            [codex_message(target_timestamp(14), "user", "x" * 70000)],
        )
        self.observe("large-session", self.work, transcript)
        first = self.collect_session("codex", "large-session", chunk=1)["session"]
        self.assertGreater(first["chunk_count"], 1)
        self.assertEqual(first["chunk"], 1)
        self.assertLessEqual(len(json.dumps(first["messages"]).encode("utf-8")), 64 * 1024)
        second = self.collect_session("codex", "large-session", chunk=2)["session"]
        self.assertEqual(second["chunk"], 2)
        self.assertEqual(second["captured_through"], first["captured_through"])

    def test_many_small_messages_stay_within_serialized_chunk_bound(self) -> None:
        transcript = self.root / "many-small.jsonl"
        records = [
            codex_message(
                target_timestamp(15, index // 60, index % 60),
                "user" if index % 2 == 0 else "assistant",
                f"message-{index}",
            )
            for index in range(3000)
        ]
        write_jsonl(transcript, records)
        self.observe("many-small-session", self.work, transcript)
        first = self.collect_session("codex", "many-small-session", chunk=1)["session"]
        self.assertGreater(first["chunk_count"], 1)
        self.assertLessEqual(
            len(json.dumps(first["messages"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")),
            64 * 1024,
        )


if __name__ == "__main__":
    unittest.main()
