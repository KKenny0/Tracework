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
sys.path.insert(0, str(ROOT / 'references'))
replay = module('replay_context', 'references/decision_replay.py')


def concurrent_write(path, expected, text, queue):
    try:
        queue.put(writer.update(path, '2026-09-12', {'work': text}, expected))
    except writer.Conflict:
        queue.put('conflict')


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

    def test_input_boundaries(self):
        for day in ['20260912', '2026-W37-6', '2026-02-30']:
            with self.assertRaises(ValueError):
                writer.merge(b'', day, {'work': 'x'})
        for bodies in [{'all': 'x'}, {'': 'x'}, {'work': ''}, {'work': '### 2026.01.01'}, {'work': '<!-- /tracework:daily -->'}]:
            with self.assertRaises(writer.Conflict):
                writer.merge(b'', '2026-09-12', bodies)
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'original'
            original.write_bytes(b'user')
            link = Path(tmp) / 'link'
            link.symlink_to(original)
            with self.assertRaises(writer.Conflict):
                writer.update(link, '2026-09-12', {'work': 'new'}, writer.digest(b'user'))
            self.assertEqual(original.read_bytes(), b'user')

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

    def test_roadmap_can_recover_every_thread(self):
        nodes = [{'id': str(i), 'thread_id': f'thread:{i}', 'timestamp': f'2026-09-{i+1:02}',
                  'source_entry_refs': [{'week': '2026-W37', 'entry_index': i}]} for i in range(25)]
        index = {'nodes': nodes, 'edges': []}
        first = replay.build_roadmap_pack(index)
        self.assertEqual((first['thread_count'], len(first['threads'])), (25, 20))
        full = replay.build_roadmap_pack(index, first['thread_count'])
        self.assertEqual(sum(t['node_count'] for t in full['threads']), 25)
        self.assertEqual({d['id'] for t in full['threads'] for d in t['decisions']}, {str(i) for i in range(25)})

    def test_instruction_paths(self):
        shared = ROOT / 'references/reporting-narrative-contract.md'
        weekly = ROOT / 'skills/weekly'
        monthly_dir = ROOT / 'skills/monthly'
        paths = {
            'weekly quick': ([weekly/'SKILL.md', shared], 12000),
            'weekly brief': ([weekly/'SKILL.md', shared, weekly/'references/weekly-analysis-contract.md', weekly/'references/weekly-brief-template.md'], 30000),
            'weekly slides': ([weekly/'SKILL.md', shared, weekly/'references/weekly-analysis-contract.md', weekly/'references/weekly-slides-contract.md', weekly/'references/slide-template.md'], 58000),
            'monthly raw': ([monthly_dir/'SKILL.md', shared, monthly_dir/'references/worklog-summary-template.md'], 18000),
        }
        for name, (files, budget) in paths.items():
            count = sum(len(p.read_text()) for p in files)
            print(f'{name}: {count}/{budget} characters')
            self.assertLessEqual(count, budget, name)
        weekly_text = (weekly/'SKILL.md').read_text()
        self.assertIn('Quick must not load analysis or templates', weekly_text)
        self.assertIn('brief must not load slides rules', weekly_text)
        self.assertIn('only when Daily input exists', (monthly_dir/'SKILL.md').read_text())


if __name__ == '__main__':
    unittest.main()
