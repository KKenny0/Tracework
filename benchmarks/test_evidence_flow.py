"""End-to-end guards for evidence preservation and independent monthly input."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


raw = load('raw', 'scripts/tracework_raw.py')
replay = load('replay', 'references/decision_replay.py')
sessions = load('sessions', 'skills/capture/scripts/tracework_sessions.py')
monthly = load('monthly', 'skills/monthly/scripts/prepare_monthly_data.py')
split = load('split', 'skills/monthly/scripts/split_daily_note.py')


class EvidenceFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tracework-evidence-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entry = self.root / 'entry.json'
        self.entry.write_text(json.dumps({
            'timestamp': '2026-08-31T12:00:00+08:00', 'type': 'decision',
            'summary': 'Direction chosen; rollout remains unverified',
            'context': 'Goal: preserve evidence. Gate: validate the rollout.',
            'source': 'session-recap', 'archetype': 'maintenance',
        }))
        self.config = patch.object(raw, 'resolve_config', return_value=({}, []))
        self.config.start()
        self.addCleanup(self.config.stop)

    def append(self):
        return raw.append_entries(self.entry, self.root, '2026-08-31', self.root, 'probe')

    def test_historical_capture_reaches_monthly_without_daily(self):
        result = self.append()
        stored = json.loads(Path(result['path']).read_text())[0]
        self.assertEqual(stored['timestamp'], '2026-08-31T12:00:00+08:00')
        self.assertIn('captured_at', stored)
        self.assertEqual(len(monthly.load_monthly_raw_entries(self.root, '2026-08')), 1)
        command = [sys.executable, '-B', str(ROOT / 'skills/monthly/scripts/prepare_monthly_data.py'),
                   '--vault', str(self.root), '--month', '2026-08',
                   '--signals-output', str(self.root / 'signals.json'),
                   '--skeleton-output', str(self.root / 'skeleton.json')]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        skeleton = json.loads((self.root / 'skeleton.json').read_text())
        self.assertEqual(len(skeleton['raw_entries']), 1)
        self.assertEqual(skeleton['statistics']['total_days'], 0)

    def test_concurrent_append_preserves_all_entries(self):
        result = self.append()
        target = Path(result['path'])
        original = Path.read_text
        def slow_read(path, *args, **kwargs):
            content = original(path, *args, **kwargs)
            if path == target:
                time.sleep(0.01)
            return content
        with patch.object(Path, 'read_text', slow_read):
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda _: self.append(), range(16)))
        self.assertEqual(len(json.loads(target.read_text())), 17)

    def test_failed_replace_preserves_original(self):
        target = Path(self.append()['path'])
        original = target.read_bytes()
        with patch.object(Path, 'replace', side_effect=OSError('synthetic write failure')):
            with self.assertRaises(OSError):
                self.append()
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(list(target.parent.glob('*.tmp')))

    def test_historical_date_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            raw.append_entries(self.entry, self.root, '2026-08-30', self.root, 'probe')
        self.assertFalse((self.root / 'raw').exists())

    def test_registry_parallel_updates_and_corruption_preservation(self):
        def register(index):
            project = self.root / f"project-{index}"
            project.mkdir(exist_ok=True)
            return raw.register_project(project, self.root, f"Project {index}",
                                        f"project-{index}", None, "work")
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(register, range(16)))
        registry = self.root / "raw/projects.json"
        self.assertEqual(len(json.loads(registry.read_text())), 16)
        registry.write_text("invalid original")
        with self.assertRaises(ValueError):
            register(17)
        self.assertEqual(registry.read_text(), "invalid original")

    def test_empty_month_and_explicit_missing_archive(self):
        command = [sys.executable, '-B', str(ROOT / 'skills/monthly/scripts/prepare_monthly_data.py'),
                   '--vault', str(self.root), '--month', '2026-08',
                   '--signals-output', str(self.root / 'signals.json'),
                   '--skeleton-output', str(self.root / 'skeleton.json')]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        signals = json.loads((self.root / 'signals.json').read_text())
        self.assertEqual(signals['raw_entries'], [])
        self.assertEqual(signals['entries'], [])
        previous = (self.root / 'signals.json').read_bytes()
        failed = subprocess.run(command + ['--input', str(self.root / 'missing.md')],
                                capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual((self.root / 'signals.json').read_bytes(), previous)

    def test_daily_formats_preserve_body_through_archive_and_parser(self):
        for date in ('2026.08.31', '2026-08-31'):
            with self.subTest(date=date):
                note = self.root / 'Daily Note.md'
                body = f'### {date}\n\n- [Probe]\n  - 进展：已记录，仍待验证\n'
                note.write_text(body)
                months, _ = split.parse_daily_note(note)
                self.assertEqual(''.join(months['2026-08']), body)
                archive = self.root / '2026-08.md'
                archive.write_text(''.join(months['2026-08']))
                parsed = monthly.parse_monthly_file(archive)
                self.assertEqual(parsed['total_days'], 1)
                self.assertIn('已记录，仍待验证', parsed['entries'][0]['raw_text'])


class ScopeAndReplayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tracework-scope-replay-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        home = patch.object(Path, 'home', return_value=self.root)
        home.start()
        self.addCleanup(home.stop)
        self.entry = {
            'timestamp': '2026-09-08T10:00:00+08:00', 'type': 'decision',
            'summary': 'Validation repair ownership stays in validation',
            'context': 'Keep validation repair ownership separate from orchestration',
            'motivation': 'Validation repair ownership avoids coupling',
            'impact': 'Validation repair ownership is now isolated',
            'source': 'session-recap',
        }

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    def config(self, parent, body):
        path = parent / '.tracework/config.yaml'
        path.parent.mkdir(exist_ok=True)
        path.write_text(body)

    def pack(self, entry, mode='why'):
        self.write('raw/weeks/2026-W37/probe.json', [entry])
        return replay.build_query_pack(replay.build_index(self.root, 'probe'),
                                       'validation repair ownership', mode, 3)

    def test_scope_precedence_and_no_transcript_reads(self):
        for purpose, expected in [('report', 'local'), ('session', None)]:
            self.assertEqual(raw.resolve_scope(self.project, None, purpose)['scope'], expected)
        self.config(self.root, 'profile:\n  reporting_group: work\n')
        self.assertIsNone(raw.find_project_config(self.project))
        self.assertIsNone(raw.resolve_scope(self.project, None, 'session')['scope'])
        self.assertEqual(sessions.profile_for_cwd(self.project)['reporting_group'], 'unassigned')
        self.config(self.project, 'project_slug: probe\n')
        self.assertEqual(sessions.profile_for_cwd(self.project)['reporting_group'], 'unassigned')
        self.config(self.project, 'profile:\n  reporting_group: personal\n')
        for purpose in ('report', 'session'):
            self.assertEqual(raw.resolve_scope(self.project, None, purpose)['scope'], 'personal')
        self.config(self.root, 'profile:\n  default_reporting_group: work\n')
        self.assertEqual(raw.resolve_scope(self.project, None, 'report')['scope'], 'work')
        self.assertEqual(raw.resolve_scope(self.project, 'all', 'session')['scope'], 'all')
        self.assertEqual(raw.resolve_scope(self.project, 'personal', 'report')['scope_source'], 'explicit')

    def test_registry_group_and_project_override(self):
        self.config(self.root, f'knowledge_vault: {self.root}\n')
        self.write('raw/projects.json', [{'path': str(self.project), 'reporting_group': 'personal'}])
        self.assertEqual(raw.resolve_scope(self.project, None, 'session')['scope'], 'personal')
        self.config(self.project, 'profile:\n  reporting_group: consulting\n')
        self.assertEqual(raw.resolve_scope(self.project, None, 'report')['scope'], 'consulting')

    def test_session_cli_requires_scope_before_dispatch(self):
        import contextlib
        import io
        for args in (['list-day', '--date', '2026-09-12'],
                     ['collect-session', '--date', '2026-09-12', '--runtime', 'codex', '--session-id', 'probe']):
            with self.subTest(args=args), patch.object(sessions, 'collect_session') as collect:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    sessions.build_parser().parse_args(args)
                self.assertEqual(error.exception.code, 2)
                collect.assert_not_called()

    def test_boundary_survives_query_and_limits_strength(self):
        for ref_type in ('conversation', 'repository_snapshot'):
            entry = {**self.entry, 'source_refs': [{'type': ref_type, 'ref': 'session:probe'}],
                     'reporting': {'evidence_boundary': 'verified', 'impact_boundary': 'expected'}}
            pack = self.pack(entry)
            self.assertTrue(pack['answerable'])
            self.assertEqual(pack['evidence_strength'], 'weak')
            self.assertEqual(pack['evidence_boundary'], 'recorded')
            self.assertEqual(pack['top_nodes'][0]['impact_boundary'], 'expected')
            self.assertTrue(pack['missing_evidence'])
        legacy = {**self.entry, 'evidence_refs': ['test:validation-repair']}
        self.assertEqual(self.pack(legacy)['evidence_boundary'], 'recorded')
        verified = {**legacy, 'reporting': {'evidence_boundary': 'verified', 'impact_boundary': 'observed'}}
        self.assertEqual(self.pack(verified)['evidence_strength'], 'strong')
        self.assertEqual(self.pack(verified, 'impact')['evidence_strength'], 'strong')
        verified['reporting']['impact_boundary'] = 'expected'
        self.assertEqual(self.pack(verified, 'impact')['evidence_strength'], 'weak')
        inferred = {**self.entry, 'type': 'feature', 'motivation': ''}
        self.assertEqual(self.pack(inferred)['evidence_boundary'], 'limited')

    def test_stable_ids_after_append_backfill_and_sort(self):
        self.write('raw/weeks/2026-W37/probe.json', [self.entry])
        before = replay.build_index(self.root, 'probe')['nodes'][0]
        self.write('raw/weeks/2026-W37/probe.json', [self.entry,
                   {**self.entry, 'timestamp': '2026-09-07T10:00:00+08:00'}])
        self.write('raw/weeks/2026-W36/probe.json', [{**self.entry, 'timestamp': '2026-09-01T10:00:00+08:00'}])
        after = next(n for n in replay.build_index(self.root, 'probe')['nodes'] if n['timestamp'] == self.entry['timestamp'])
        self.assertEqual(before['id'], 'raw:probe:2026-W37:0')
        self.assertEqual(after['id'], before['id'])
        self.assertEqual(after['source_entry_refs'], before['source_entry_refs'])

    def test_index_rebuild_content_artifact_missing_raw_and_atomic_failure(self):
        raw_path = self.write('raw/weeks/2026-W37/probe.json', [self.entry])
        index = replay.build_index(self.root, 'probe')
        index['source']['builder_version'] = 2
        target = replay.write_index(index, self.root, 'probe', None)
        nodes, status = replay.read_or_rebuild_decision_context(self.root, 'probe', 10)
        self.assertTrue(status['rebuilt'])
        self.assertEqual(json.loads(target.read_text())['source']['builder_version'], 4)
        self.write('raw/weeks/2026-W37/probe.json', [{**self.entry, 'summary': 'Changed in place'}])
        self.assertEqual(replay.load_index(self.root, 'probe')['nodes'][0]['summary'], 'Changed in place')
        fresh = replay.build_index(self.root, 'probe')
        replay.write_index(fresh, self.root, 'probe', None)
        self.write('raw/artifacts/probe.json', [{'id': 'artifact:probe', 'path': 'PLAN.md'}])
        self.assertNotEqual(replay.load_index(self.root, 'probe')['source']['input_fingerprint'],
                            fresh['source']['input_fingerprint'])
        original = target.read_bytes()
        with patch.object(Path, 'replace', side_effect=OSError('synthetic failure')):
            with self.assertRaises(OSError):
                replay.write_index(replay.build_index(self.root, 'probe'), self.root, 'probe', None)
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(list(target.parent.glob('*.tmp')))
        raw_path.unlink()
        pack = replay.build_query_pack(replay.load_index(self.root, 'probe'), 'validation repair ownership', 'why', 3)
        self.assertFalse(pack['answerable'])
        self.assertIn('preserved', ' '.join(pack['missing_evidence']))
        self.assertTrue(replay.build_roadmap_pack(replay.load_index(self.root, 'probe'))['diagnostics'])
        self.assertEqual(replay.read_or_rebuild_decision_context(self.root, 'probe', 10)[1]['reason'], 'missing_raw_sources')
        with self.assertRaises(ValueError):
            replay.write_index(replay.build_index(self.root, 'probe'), self.root, 'probe', None)
        self.assertEqual(target.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
