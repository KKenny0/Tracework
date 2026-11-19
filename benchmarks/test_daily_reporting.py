#!/usr/bin/env python3
"""Batch-two safety and compatibility checks; temporary files only."""
import importlib.util
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


sys.path.insert(0, str(ROOT / 'references'))
writer = module('daily_writer', 'skills/daily/scripts/update_daily_note.py')
monthly = module('monthly_context', 'skills/monthly/scripts/prepare_monthly_data.py')


def concurrent_write(path, expected, text, queue):
    try:
        queue.put(writer.update(path, '2026-09-12', {'work': text}, expected))
    except writer.Conflict:
        queue.put('conflict')


def paused_lock_initialization(path, initialized, release):
    raw = sys.modules[writer.json_lock.__wrapped__.__module__]
    original = raw.prepare_lock_file
    def pause(handle):
        initialized.set()
        if not release.wait(5):
            raise TimeoutError('Initializer was not released')
        original(handle)
    with patch.object(raw, 'prepare_lock_file', pause), writer.json_lock(path):
        pass


def enter_second_lock(path, started, entered):
    started.set()
    with writer.json_lock(path):
        entered.set()


class DailyReporting(unittest.TestCase):
    def test_owned_blocks_idempotence_and_byte_preservation(self):
        original = b'User preface\r\n### 2026.09.11\r\nOld user text\r\n'
        first = writer.merge(original, '2026-09-12', {'work': 'Work body', 'personal': 'Private body'})
        self.assertTrue(first.startswith(original))
        self.assertEqual(writer.merge(first, '2026-09-12', {'work': 'Work body'}), first)
        changed = writer.merge(first + b'\nUser tail\r\n', '2026-09-12', {'work': 'Updated work'})
        self.assertIn(b'Private body\n', changed)
        self.assertTrue(changed.endswith(b'\nUser tail\r\n'))
        self.assertEqual(changed.count(b'### 2026.09.12'), 1)
        extra = writer.merge(changed, '2026-09-12', {'client': 'Another group'})
        self.assertIn(b'Updated work\n', extra)
        self.assertEqual(extra.count(b'### 2026.09.12'), 1)

    def test_conflicts_leave_file_untouched(self):
        base = writer.merge(b'', '2026-09-12', {'work': 'Generated'})
        cases = [base.replace(b'Generated', b'User edit'), base.replace(b'sha256=', b'hash='),
                 base + b'\n<!-- /tracework:daily -->', base + base,
                 b'### 2026.09.12\nLegacy unknown text',
                 base.replace(b'### 2026.09.12', b'### 2026.09.11')]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Daily Note.md'
            for before in cases:
                path.write_bytes(before)
                with self.assertRaises(writer.Conflict):
                    writer.update(path, '2026-09-12', {'work': 'Replacement'}, writer.digest(before))
                self.assertEqual(path.read_bytes(), before)
            path.write_bytes(base)
            with self.assertRaises(writer.Conflict):
                writer.update(path, '2026-09-12', {'work': 'Replacement'}, 'stale-hash')
            self.assertEqual(path.read_bytes(), base)

    def test_snapshot_cli_reads_only_requested_day_and_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Daily.md'
            command = [sys.executable, '-B', str(ROOT / 'skills/daily/scripts/update_daily_note.py'),
                       '--inspect', '--path', str(path), '--date', '2026-09-12', '--group', 'work']

            def inspect(*args):
                run = subprocess.run(command + list(args), capture_output=True, text=True)
                return run.returncode, json.loads(run.stdout)

            self.assertEqual(inspect(), (0, {'status': 'ready', 'expected_file_hash': 'missing', 'bodies': {}}))
            self.assertEqual(list(path.parent.iterdir()), [])
            original = writer.merge(b'', '2026-09-11', {'work': 'Prior day'})
            title = '#### 剧本｜排练准备'
            work = title + '\n\n- **分场稿**：交给排练组。'
            original = writer.merge(original, '2026-09-12', {'work': work, 'personal': 'Private'})
            # The unrelated group's hand edit survives and cannot enter the snapshot payload.
            original = original.replace(b'Private', b'Private edit')
            path.write_bytes(original)
            self.assertEqual(inspect('--group', 'client'), (0, {
                'status': 'ready', 'expected_file_hash': writer.digest(original), 'bodies': {'work': work + '\n'}}))
            self.assertEqual(path.read_bytes(), original)
            for group_args, content in [
                (('--group', 'personal'), original),
                ((), b'### 2026.09.12\nLegacy unknown text'),
                ((), original + b'\n<!-- /tracework:daily -->'),
                ((), original.replace(b'### 2026.09.12', b'### 2026.09.13')),
            ]:
                path.write_bytes(content)
                status, payload = inspect(*group_args)
                self.assertEqual(status, 2)
                self.assertNotIn('bodies', payload)
                self.assertEqual(path.read_bytes(), content)

    def test_unowned_group_edits_are_preserved(self):
        base = writer.merge(b'', '2026-09-12', {'work': 'Generated', 'personal': 'Private'})
        edited = base.replace(b'Private', b'User-edited private')
        changed = writer.merge(edited, '2026-09-12', {'work': 'New work'})
        self.assertIn(b'User-edited private', changed)

    def test_during_write_and_atomic_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Daily.md'
            path.write_bytes(b'Before')
            real_merge = writer.merge
            def racing_merge(*args):
                path.write_bytes(b'Concurrent editor')
                return real_merge(*args)
            with patch.object(writer, 'merge', racing_merge), self.assertRaises(writer.Conflict):
                writer.update(path, '2026-09-12', {'work': 'Draft'}, writer.digest(b'Before'))
            self.assertEqual(path.read_bytes(), b'Concurrent editor')
            with patch.object(writer.os, 'replace', side_effect=OSError('disk failure')), self.assertRaises(OSError):
                writer.update(path, '2026-09-12', {'work': 'Draft'}, writer.digest(path.read_bytes()))
            self.assertEqual(path.read_bytes(), b'Concurrent editor')
            self.assertEqual(list(Path(tmp).glob('.tracework-daily-*')), [])

    def test_concurrent_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Daily.md'
            ctx = multiprocessing.get_context('spawn')
            queue = ctx.Queue()
            workers = [ctx.Process(target=concurrent_write, args=(path, 'missing', body, queue)) for body in ['A', 'B']]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(10)
                self.assertEqual(worker.exitcode, 0)
            self.assertEqual(sorted(queue.get(timeout=2) for _ in workers), ['conflict', 'updated'])

    def test_lock_initialization_excludes_other_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Daily.md.tracework'
            ctx = multiprocessing.get_context('spawn')
            initialized, release, started, entered = [ctx.Event() for _ in range(4)]
            first = ctx.Process(target=paused_lock_initialization, args=(path, initialized, release))
            second = ctx.Process(target=enter_second_lock, args=(path, started, entered))
            first.start()
            try:
                self.assertTrue(initialized.wait(5))
                second.start()
                self.assertTrue(started.wait(5))
                self.assertFalse(entered.wait(0.5), 'Another writer entered during lock initialization')
            finally:
                release.set()
                first.join(10)
                if second.pid is not None:
                    second.join(10)
            self.assertEqual(first.exitcode, 0)
            self.assertEqual(second.exitcode, 0)
            self.assertTrue(entered.is_set(), 'Second writer must enter after initialization is released')

    def test_input_boundaries(self):
        for day in ['20260912', '2026-W37-6', '2026-02-30']:
            with self.assertRaises(ValueError):
                writer.merge(b'', day, {'work': 'x'})
        for bodies in [{'all': 'x'}, {'': 'x'}, {'work': ''}, {'work': '### 2026.01.01'},
                       {'work': '# 剧本｜排练准备'}, {'work': '  ## 剧本｜排练准备'},
                       {'work': '<!-- /tracework:daily -->'}]:
            with self.assertRaises(writer.Conflict):
                writer.merge(b'', '2026-09-12', bodies)
    def test_symlink_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'original'
            original.write_bytes(b'user')
            link = Path(tmp) / 'link'
            try:
                link.symlink_to(original)
            except OSError as error:
                if getattr(error, 'winerror', None) == 1314:
                    self.skipTest('Windows token cannot create file symlinks; exercised by Linux CI')
                raise
            with self.assertRaises(writer.Conflict):
                writer.update(link, '2026-09-12', {'work': 'new'}, writer.digest(b'user'))
            self.assertEqual(original.read_bytes(), b'user')

    def test_missing_parent_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'absent' / 'Daily.md'
            with self.assertRaises(FileNotFoundError):
                writer.update(path, '2026-09-12', {'work': 'Draft'}, 'missing')
            self.assertFalse(path.parent.exists())

    def test_fenced_code_comments_are_allowed_but_outer_headings_are_rejected(self):
        for body in ['```sh\n  # deploy command\n```', '  ~~~~sh\n### example\n~~~\n## still code\n  ~~~~']:
            with self.subTest(body=body):
                result = writer.merge(b'', '2026-09-12', {'work': body})
                self.assertIn(body.encode(), result)
                for heading in ['# Title', '  ## Title', '   ###']:
                    with self.assertRaises(writer.Conflict):
                        writer.merge(b'', '2026-09-12', {'work': body + '\n' + heading})

    def test_archive_preserves_adjacent_managed_markers(self):
        source = writer.merge(b'', '2026-09-12', {'work': 'Work\r\nbody', 'personal': 'Private'})
        source = source.replace(writer.END + b'\n\n<!--', writer.END + b'<!--')
        source = source[source.index(b'### '):]
        self.assertEqual(len(writer.validate_targets(source, '2026-09-12', ['work', 'personal'])[0]), 2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Daily.md'
            path.write_bytes(source)
            out = Path(tmp) / 'archive'
            result = self.run_archive(path, out, '--month-filter', '2026-09')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((out / '2026-09.md').read_bytes(), source)
            self.assertEqual(path.read_bytes(), source)

    def test_archive_month_filter_isolates_unclosed_blocks(self):
        september = writer.merge(b'', '2026-09-12', {'work': 'Work'}).lstrip(b'\n')
        october = writer.merge(b'', '2026-10-01', {'work': 'October\n    ### 2026.09.01\nExample'}).lstrip(b'\n')
        broken = october.replace(writer.END, b'')
        for source in [broken + september, september + broken]:
            with self.subTest(broken_first=source.startswith(broken)), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'Daily.md'
                path.write_bytes(source)
                out = Path(tmp) / 'archive'
                result = self.run_archive(path, out, '--month-filter', '2026-09')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((out / '2026-09.md').read_bytes(), september)
                self.assertFalse((out / '2026-10.md').exists())
                for args in [(), ('--month-filter', '2026-10')]:
                    result = self.run_archive(path, out, *args)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('Unclosed managed Daily block', result.stderr)
                    self.assertEqual(list(out.iterdir()), [out / '2026-09.md'])
                    self.assertEqual((out / '2026-09.md').read_bytes(), september)
                self.assertEqual(path.read_bytes(), source)

    def run_archive(self, path, out, *args):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'skills/monthly/scripts/split_daily_note.py'),
                               str(path), str(out), *args], capture_output=True, text=True, encoding='utf-8')

    def test_writer_archive_monthly_round_trip_preserves_managed_bytes(self):
        view = {'status': 'complete', 'scope': 'work', 'scope_source': 'explicit',
                'period': {'start': '2026-09-01', 'end': '2026-09-30'}, 'groups': {}}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'Daily Note.md'
            archive = root / 'archive'
            archive.mkdir()
            historical = archive / '2026-07.md'
            historical.write_bytes(b'historical\r\n')
            path.write_bytes('### 2026.07.31\r\nJuly source\r\n## 2026年8月\r\n'
                             '### 2026.08.31\r\nAugust\r\n'.encode())
            body = ('#### 剧本交付\r\n交付可排练分场稿。\n    ### 2026.10.01\r\n此行是示例。'
                    '\n```markdown\n### 2026.10.01\n```')
            writer.update(path, '2026-09-12', {'work': body, 'personal': 'Private'},
                          writer.digest(path.read_bytes()))
            path.write_bytes(path.read_bytes() + b'\n### 2026.10.01\r\nOctober\r\n')
            source = path.read_bytes()
            self.assertEqual(writer.inspect_snapshot(path, '2026-09-12', ['work'])['bodies'], {'work': body + '\n'})
            result = self.run_archive(path, archive, '--overwrite-policy', 'skip_existing')
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary['months_created'], ['2026-08', '2026-09', '2026-10'])
            self.assertEqual(summary['months_skipped'], ['2026-07'])
            september = archive / '2026-09.md'
            first = source.index(b'### 2026.09.12')
            last = source.index(b'### 2026.10.01\r\nOctober')
            self.assertEqual(september.read_bytes(), source[first:last])
            self.assertEqual((archive / '2026-10.md').read_bytes(), source[last:])
            self.assertEqual(historical.read_bytes(), b'historical\r\n')
            self.assertEqual(path.read_bytes(), source)
            signals = monthly.build_signals(view, september, '2026-09')
            self.assertEqual([row['text'] for row in signals['editorial_context']], [body + '\n'])
            self.assertEqual(signals['excluded_editorial'], {'managed_blocks': 1})

    def test_monthly_raw_old_new_none(self):
        view = {'status': 'complete', 'scope': 'work', 'scope_source': 'explicit',
                'period': {'start': '2026-09-01', 'end': '2026-09-12'},
                'groups': {'work': [{'slug': 'demo', 'name': 'Demo', 'reporting_group': 'work',
                                    'view': {'project_slug': 'demo', 'states': [], 'entries': []}}]}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '2026-09.md'
            old = b'### 2026.09.12\n- [demo]\n  - [x] Legacy judgment\n'
            new = writer.merge(b'', '2026-09-12', {'work': 'No production acceptance yet.\n- [x] prose is not a task fact'})
            for content in [old, new, None]:
                if content is not None:
                    path.write_bytes(content)
                signals = monthly.build_signals(view, path if content else None, '2026-09')
                result = monthly.build_review_skeleton(signals)
                self.assertEqual(result['evidence_source'], 'daily_only_limited' if content else 'empty')
                self.assertEqual(result['raw_work_streams'], [])
                self.assertNotIn('statistics', result)
                if content:
                    self.assertEqual(signals['editorial_context'][0]['evidence_boundary'], 'editorial_only')

    def test_monthly_scope_period_and_raw_identity(self):
        def project(slug, entries, states=None):
            return {'slug': slug, 'name': 'Same name', 'reporting_group': 'work',
                    'view': {'project_slug': slug, 'entries': entries, 'states': states or [],
                             'correction_history': [{'correction': 'retained'}], 'diagnostics': ['conflict retained']}}
        entry = {'timestamp': '2026-09-10T12:00:00+08:00', 'summary': 'Still unverified',
                 'status': 'open', '_source_path': 'synthetic', '_source_index': 0}
        view = {'status': 'complete', 'scope': 'work', 'scope_source': 'explicit',
                'period': {'start': '2026-09-01', 'end': '2026-09-12'},
                'groups': {'work': [project('one', [entry]), project('two', [entry]),
                                    project('carried', [], [{'subject': 'risk:r', 'state': 'open'},
                                                          {'subject': 'risk:a', 'state': 'accepted'}])]}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '2026-09.md'
            content = writer.merge(b'', '2026-09-10', {'work': 'Completed! repeated judgment', 'personal': 'PRIVATE_MANAGED'})
            content = writer.merge(content, '2026-09-11', {'work': 'Completed! repeated judgment'})
            content = writer.merge(content, '2026-09-13', {'work': 'FUTURE'})
            content += b'\n### 2026.09.10\n- [personal]\nPRIVATE_LEGACY\n- [Same name]\nAMBIGUOUS\n- [one]\nLegacy completed\n- [private] Private project\nTAIL_PRIVATE\n- [one]\nStill in scope\n### 2026.09.13 Future\nTAIL_FUTURE\n'
            path.write_bytes(content)
            signals = monthly.build_signals(view, path, '2026-09')
            skeleton = monthly.build_review_skeleton(signals)
            payload = json.dumps(signals)
            for secret in ['PRIVATE_MANAGED', 'PRIVATE_LEGACY', 'AMBIGUOUS', 'FUTURE', 'TAIL_PRIVATE', 'TAIL_FUTURE']:
                self.assertNotIn(secret, payload)
            self.assertEqual(signals['excluded_editorial']['legacy_blocks'], 3)
            self.assertEqual(len(signals['editorial_context']), 4)
            self.assertEqual(skeleton['projects']['one']['raw_entry_indexes'], [0])
            self.assertEqual(skeleton['projects']['two']['raw_entry_indexes'], [1])
            self.assertEqual(skeleton['projects']['carried']['effective_view_indexes'], [2])
            self.assertEqual(len(skeleton['current_risks']), 1)
            self.assertEqual(len(skeleton['accepted_risks']), 1)
            self.assertEqual(signals['raw_entries'][0]['entry']['status'], 'open')
            self.assertNotIn('entries', signals['effective_views'][0])
            self.assertEqual(signals['effective_views'][0]['diagnostics'], ['conflict retained'])
            self.assertEqual([s['work_stream'] for s in skeleton['raw_work_streams']], ['one', 'two'])
            for mode in ['light', 'engineering_review']:
                other = monthly.build_review_skeleton(signals, mode)
                other['summary_mode'] = skeleton['summary_mode']
                self.assertEqual(other, skeleton)
            narrowed = monthly.build_signals(view, path, '2026-09', allow_group_context=False)
            self.assertEqual(len(narrowed['editorial_context']), 2)
            view['status'] = 'partial'
            self.assertEqual(len(monthly.build_signals(view, path, '2026-09')['editorial_context']), 2)

    def test_instruction_paths(self):
        shared = ROOT / 'references/reporting-narrative-contract.md'
        weekly = ROOT / 'skills/weekly'
        monthly_dir = ROOT / 'skills/monthly'
        # Shared clarity rules add ~3k characters; monthly additionally loads
        # its mandatory source-review guide. Keep explicit, bounded read paths.
        paths = {
            'weekly quick': ([weekly/'SKILL.md', shared], 15000),
            'weekly brief': ([weekly/'SKILL.md', shared, weekly/'references/weekly-analysis-contract.md', weekly/'references/weekly-brief-template.md'], 33000),
            'weekly slides': ([weekly/'SKILL.md', shared, weekly/'references/weekly-analysis-contract.md', weekly/'references/weekly-slides-contract.md', weekly/'references/slide-template.md'], 58000),
            'monthly raw': ([monthly_dir/'SKILL.md', shared, monthly_dir/'references/worklog-summary-template.md', monthly_dir/'references/monthly-source-review.md'], 29000),
        }
        for name, (files, budget) in paths.items():
            count = sum(len(p.read_text(encoding='utf-8')) for p in files)
            print(f'{name}: {count}/{budget} characters')
            self.assertLessEqual(count, budget, name)
        weekly_text = (weekly/'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('Quick must not load analysis or templates', weekly_text)
        self.assertIn('brief must not load slides rules', weekly_text)
        self.assertIn('only when Daily input exists', (monthly_dir/'SKILL.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
