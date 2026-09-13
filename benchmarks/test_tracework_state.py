#!/usr/bin/env python3
"""Correction, temporal state, reader agreement and scoped recovery checks."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'references'))
import tracework_state as state
import tracework_raw as raw
import decision_replay as replay


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


monthly = load('monthly_state', 'skills/monthly/scripts/prepare_monthly_data.py')
recall = load('recall_state', 'skills/recall/scripts/recall_context.py')
sessions = load('sessions_state', 'skills/capture/scripts/tracework_sessions.py')


def fact(summary, when='2026-08-25T10:00:00+08:00', **kwargs):
    return {'timestamp': when, 'captured_at': when, 'summary': summary, 'context': 'fixture context',
            'type': 'decision', 'source': 'session-recap', **kwargs}


def correction(target, index, summary='corrected, ongoing', operation='replace', captured='2026-09-13T10:00:00+08:00'):
    return fact(summary, target['timestamp'], captured_at=captured, correction={
        'operation': operation, 'target_ref': {'week': '2026-W35', 'entry_index': index, 'timestamp': target['timestamp']},
        'target_hash': state.entry_hash(target), 'reason': 'Original fact was inaccurate'})


class EffectiveState(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root/'vault'
        self.path = self.vault/'raw/weeks/2026-W35/demo.json'
        self.path.parent.mkdir(parents=True)
        self.input = self.root/'entry.json'
        self.original = fact('original delivered')
        self.write([self.original])

    def tearDown(self):
        self.temp.cleanup()

    def write(self, entries):
        self.path.write_text(json.dumps(entries))

    def view(self, **kwargs):
        return state.read_view(self.vault, 'demo', **kwargs)

    def append(self, entry):
        self.input.write_text(json.dumps(entry))
        return raw.append_entries(self.input, self.root, None, self.vault, 'demo')

    def test_chain_retract_and_hash_identity(self):
        first = correction(self.original, 0)
        self.append(first)
        records = json.loads(self.path.read_text())
        self.assertEqual(records[0], self.original)
        self.assertEqual(records[1]['timestamp'], self.original['timestamp'])
        self.assertEqual(self.view()['entries'][0]['summary'], 'corrected, ongoing')
        second = correction(records[1], 1, 'second correction')
        self.append(second)
        records = json.loads(self.path.read_text())
        self.assertEqual(self.view()['entries'][0]['_logical_id'], 'raw:demo:2026-W35:0')
        self.append(correction(records[2], 2, operation='retract'))
        self.assertEqual(self.view()['entries'], [])
        self.assertEqual(len(self.view()['correction_history']), 3)
        before = self.path.read_bytes()
        with self.assertRaises(ValueError): self.append(first)
        self.assertEqual(self.path.read_bytes(), before)

    def test_as_of_and_work_month_do_not_drift(self):
        replacement = correction(self.original, 0)
        self.write([self.original, replacement])
        old = self.view(as_of='2026-08-31T23:59:59+08:00')
        new = self.view(start='2026-08-01', end='2026-08-31')
        self.assertEqual(old['entries'][0]['summary'], 'original delivered')
        self.assertEqual(new['entries'][0]['summary'], 'corrected, ongoing')
        self.assertEqual(self.view(start='2026-09-01', end='2026-09-30')['entries'], [])
        legacy = dict(self.original); legacy.pop('captured_at')
        self.write([legacy])
        self.assertTrue(self.view(as_of='2026-08-31')['diagnostics'])

    def test_bad_targets_and_atomic_failure(self):
        valid = correction(self.original, 0)
        variants = []
        for key, value in [('entry_index', 9), ('timestamp', '2026-08-26T10:00:00+08:00'), ('project_slug', 'another')]:
            bad = json.loads(json.dumps(valid)); bad['correction']['target_ref'][key] = value; variants.append(bad)
        bad = json.loads(json.dumps(valid)); bad['correction']['target_hash'] = '0'*64; variants.append(bad)
        for bad in variants:
            before = self.path.read_bytes()
            with self.assertRaises(ValueError): self.append(bad)
            self.assertEqual(self.path.read_bytes(), before)
        with patch.object(raw, 'write_json_atomic', side_effect=OSError('disk failure')), self.assertRaises(OSError):
            self.append(valid)
        self.assertEqual(json.loads(self.path.read_text()), [self.original])
        self.append(valid)
        self.assertEqual(len(json.loads(self.path.read_text())), 2)

    def test_concurrent_correction_one_wins(self):
        command = [sys.executable, '-B', str(ROOT/'scripts/tracework_raw.py'), 'append-entry',
                   '--cwd', str(self.root), '--vault', str(self.vault), '--slug', 'demo', '--entry', str(self.input)]
        self.input.write_text(json.dumps(correction(self.original, 0)))
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        codes = [p.communicate(timeout=10) and p.returncode for p in processes]
        self.assertEqual(sorted(codes), [0, 1])
        self.assertEqual(len(json.loads(self.path.read_text())), 2)

    def test_conflicting_branches_excluded_without_harming_other_facts(self):
        other = fact('same title different record')
        first = correction(self.original, 0)
        second = correction(self.original, 0, 'optimistic branch', captured='2026-09-14T10:00:00+08:00')
        self.write([self.original, other, first, second])
        view = self.view()
        self.assertEqual([e['summary'] for e in view['entries']], [other['summary']])
        self.assertTrue(any('chain tail' in d for d in view['diagnostics']))

    def test_period_end_states_exact_subjects_and_conflicts(self):
        risk = fact('risk remains', type='risk', open_questions=['ship?', 'same words'])
        self.write([risk])
        target = 'risk:raw:demo:2026-W35:0'
        qtarget = 'open_question:raw:demo:2026-W35:0:0'
        next_week = self.vault/'raw/weeks/2026-W36/demo.json'; next_week.parent.mkdir()
        next_week.write_text(json.dumps([
            fact('risk mitigated', '2026-09-01T10:00:00+08:00', lifecycle_transition={'subject':target,'from':'open','to':'mitigated'}),
            fact('question resolved', '2026-09-01T11:00:00+08:00', lifecycle_transition={'subject':qtarget,'from':'open','to':'resolved'}),
            fact('old-name question', '2026-09-01T12:00:00+08:00', lifecycle_transition={'subject':'same words','from':'open','to':'resolved'}),
        ]))
        before = {x['subject']: x['state'] for x in self.view(end='2026-08-31')['states']}
        after = {x['subject']: x['state'] for x in self.view(end='2026-09-02')['states']}
        self.assertEqual(before[target], 'open'); self.assertEqual(after[target], 'mitigated')
        self.assertEqual(after[qtarget], 'resolved')
        self.assertEqual(after['open_question:raw:demo:2026-W35:0:1'], 'open')
        data = json.loads(next_week.read_text())
        data.append(fact('accepted branch', '2026-09-02T10:00:00+08:00', lifecycle_transition={'subject':target,'from':'open','to':'accepted'}))
        next_week.write_text(json.dumps(data))
        self.assertEqual(next(x for x in self.view()['states'] if x['subject']==target)['state'], 'conflict')
        conflicted = replay.load_index(self.vault, 'demo')
        risk_node = next(node for node in conflicted['nodes'] if node['id'] == 'raw:demo:2026-W35:0')
        self.assertEqual(risk_node['evidence_boundary'], 'limited')
        data[0]['lifecycle_transition']['to'] = 'accepted'; next_week.write_text(json.dumps(data[:3]))
        context = recall.build_context(self.root, str(self.vault), 'demo', 12)
        self.assertEqual(len(context['accepted_risks']), 1)
        self.assertEqual(context['risks'], [])
        self.assertEqual(len(context['open_questions']), 1)

    def test_correction_preserves_risk_but_not_changed_question_binding(self):
        original = fact('risk wording', type='risk', open_questions=['first', 'second'])
        change = correction(original, 0, 'corrected risk')
        change.update(type='risk', open_questions=['second'])
        transition = fact('state changed', '2026-08-26T10:00:00+08:00', lifecycle_transition={
            'subject':'risk:raw:demo:2026-W35:0','from':'open','to':'accepted'})
        question = fact('first answered', '2026-08-26T11:00:00+08:00', lifecycle_transition={
            'subject':'open_question:raw:demo:2026-W35:0:0','from':'open','to':'resolved'})
        self.write([original, change, transition, question])
        view = self.view()
        states = {s['subject']:s['state'] for s in view['states']}
        self.assertEqual(states['risk:raw:demo:2026-W35:0'], 'accepted')
        self.assertEqual(states['open_question:raw:demo:2026-W35:1:0'], 'open')
        self.assertTrue(any('missing exact subject' in d for d in view['diagnostics']))

    def test_six_consumers_agree_on_effective_fact(self):
        self.write([self.original, correction(self.original, 0)])
        expected = ['corrected, ongoing']
        for name in ('daily', 'weekly'):
            result = subprocess.check_output([sys.executable, '-B', str(ROOT/f'skills/{name}/scripts/tracework_state.py'),
                                              '--vault',str(self.vault),'--slug','demo','--start','2026-08-01','--end','2026-08-31'])
            self.assertEqual([e['summary'] for e in json.loads(result)['entries']], expected)
        self.assertEqual([x['entry']['summary'] for x in monthly.load_monthly_raw_entries(self.vault,'2026-08',['demo'])], expected)
        context = recall.build_context(self.root, str(self.vault),'demo',12)
        self.assertEqual([e['summary'] for e in context['recent_entries']], expected)
        index = replay.load_index(self.vault,'demo')
        query = replay.build_query_pack(index,'corrected','why',5)
        self.assertEqual([n['decision'] for n in query['top_nodes']], expected)
        roadmap = replay.build_roadmap_pack(index)
        self.assertEqual([n['decision'] for t in roadmap['threads'] for n in t['decisions']], expected)
        old = replay.load_index(self.vault,'demo',as_of='2026-08-31T23:59:59+08:00')
        self.assertEqual(old['nodes'][0]['summary'], 'original delivered')

    def test_same_vault_symlink_cannot_cross_project(self):
        other = self.path.with_name('other.json')
        other.write_bytes(self.path.read_bytes())
        self.path.unlink(); self.path.symlink_to(other)
        before = other.read_bytes()
        with self.assertRaises(ValueError): self.view()
        with self.assertRaises(ValueError): self.append(correction(self.original, 0))
        self.assertEqual(other.read_bytes(), before)

    def test_project_mismatch_never_opens_transcript_or_watermark(self):
        manifest = {'schema_version': sessions.SCHEMA_VERSION, 'runtime':'codex','session_id':'test','cwd':str(self.root)}
        profile = {'project_root':str(self.root/'other'),'reporting_group':'work','project_slug':'other'}
        with patch.object(sessions,'scan_enabled_payload',return_value=None), patch.object(sessions,'read_json',return_value=manifest), \
             patch.object(sessions,'classify_manifest',return_value=(profile,None)), \
             patch.object(sessions,'raw_watermark',side_effect=AssertionError('must not read')), \
             patch.object(sessions,'normalized_messages',side_effect=AssertionError('must not open')), contextlib.redirect_stdout(io.StringIO()) as output:
            sessions.collect_session('2026-09-13','work','codex','test',1,str(self.root))
        self.assertEqual(json.loads(output.getvalue())['skip'],'project_mismatch')


if __name__ == '__main__':
    unittest.main()
