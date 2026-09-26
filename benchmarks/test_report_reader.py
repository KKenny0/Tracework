"""Shared report entry checks: scoped reads, partial results and installed callers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import tracework_raw as raw
import tracework_state as state


class ReportReader(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='tracework-report-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.home = self.root / 'home'
        self.home.mkdir()
        self.vault = self.root / 'vault'
        self.cwd = self.root / 'current'
        self.config(self.cwd, 'work', 'current')
        self.rows = [self.project('current', 'work'), self.project('other', 'work'),
                     self.project('private', 'personal'), self.project('unknown', None)]
        self.registry()
        self.paths = {}
        for slug in ['current', 'other', 'private', 'unknown', 'orphan']:
            self.paths[slug] = self.write(f'vault/raw/weeks/2026-W35/{slug}.json', [self.fact(slug)])
        self.addCleanup(patch.stopall)
        patch.object(Path, 'home', return_value=self.home).start()

    def fact(self, summary, **extra):
        return dict(timestamp='2026-08-25T10:00:00+08:00', captured_at='2026-08-25T10:00:00+08:00',
                    type='decision', source='session-recap', summary=summary, context='fixture', **extra)

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        return path

    def config(self, path, group, slug, extra=''):
        target = path / '.tracework/config.yaml'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f'knowledge_vault: {self.vault}\nproject_slug: {slug}\n'
                          f'profile:\n  default_reporting_group: null\n  reporting_group: {group}\n' + extra)
        return target

    def project(self, slug, group):
        row = dict(slug=slug, name=slug.upper(), path=str(self.root / slug))
        if group is not None:
            row['reporting_group'] = group
        return row

    def registry(self):
        return self.write('vault/raw/projects.json', self.rows)

    def read(self, report='weekly', **kwargs):
        return raw.read_report(self.cwd, report, '2026-08-01', '2026-08-31', **kwargs)

    def slugs(self, result):
        return {p['slug'] for projects in result['groups'].values() for p in projects}

    def cli(self, script, args):
        return subprocess.run([sys.executable, '-B', str(ROOT / script), *args],
                              cwd=self.root, capture_output=True, text=True,
                              env={**os.environ, 'HOME': str(self.home), 'USERPROFILE': str(self.home)})

    def test_partition_precedes_body_read_and_config_overrides_registry(self):
        self.config(self.root / 'other', 'personal', 'other')
        self.config(self.root / 'private', 'work', 'private')
        forbidden = {self.paths[s] for s in ['other', 'unknown', 'orphan']}
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            self.assertNotIn(path, forbidden, 'out-of-scope body opened')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', guarded):
            for kind in ['daily', 'weekly', 'monthly']:
                result = self.read(kind)
                self.assertEqual(self.slugs(result), {'current', 'private'})
                self.assertEqual(result['status'], 'complete')
                self.assertEqual(result['write_policy'], 'normal')
                for slug in ['other', 'unknown', 'orphan']:
                    self.assertNotIn(str(self.paths[slug]), json.dumps(result))

    def test_all_local_no_vault_and_daily_only_restriction(self):
        result = self.read(scope='all')
        self.assertEqual(set(result['groups']), {'work', 'personal', 'unassigned'})
        self.config(self.cwd, 'work', 'current', f'daily_note:\n  repos:\n    - {self.cwd}\n')
        self.assertEqual(self.slugs(self.read('daily', scope='all')), {'current'})
        self.assertEqual(len(self.slugs(self.read('weekly', scope='all'))), 5)
        self.assertEqual(len(self.slugs(self.read('monthly', scope='all'))), 5)
        self.config(self.cwd, 'unassigned', 'current')
        local = self.read()
        self.assertEqual(local['scope_source'], 'implicit-local')
        self.assertEqual(self.slugs(local), {'current'})
        self.assertEqual(local['write_policy'], 'conversation_only')
        self.config(self.cwd, 'local', 'current')
        self.assertEqual(self.read(scope='local')['write_policy'], 'normal')
        (self.cwd / '.tracework/config.yaml').write_text('project_slug: current\n')
        no_vault = self.read()
        self.assertEqual(no_vault['groups']['local'][0]['view'], None)
        self.assertEqual(no_vault['write_policy'], 'conversation_only')

    def test_ambiguous_ownership_is_not_read_or_named(self):
        self.rows.append(dict(self.rows[1], path=str(self.root / 'elsewhere')))
        self.rows.append(dict(self.rows[2], slug='alias'))
        self.registry()
        original = state.read_view
        with patch.object(state, 'read_view', wraps=original) as reader:
            result = self.read(scope='all')
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['write_policy'], 'explicit_save_only')
        self.assertEqual({call.args[1] for call in reader.call_args_list}, {'current', 'unknown', 'orphan'})
        self.assertEqual(result['excluded']['ambiguous_project'], 4)
        for name in ['OTHER', 'PRIVATE', 'elsewhere', 'alias']:
            self.assertNotIn(name, json.dumps(result))

    def test_invalid_metadata_blocks_without_raw_reads(self):
        self.registry().write_text('{broken')
        with patch.object(state, 'read_view', side_effect=AssertionError('raw read')):
            result = self.read(scope='work')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['groups'], {})
        self.assertEqual(result['write_policy'], 'conversation_only')
        self.registry()
        self.config(self.root / 'other', 'work', 'different-slug')
        result = self.read()
        self.assertEqual(self.slugs(result), {'current'})
        self.assertEqual(result['status'], 'partial')
        # A conflicting configured slug also contests its other registered owner.
        self.config(self.root / 'other', 'work', 'private')
        with patch.object(state, 'read_view', wraps=state.read_view) as reader:
            result = self.read(scope='all')
        self.assertEqual({call.args[1] for call in reader.call_args_list}, {'current', 'unknown', 'orphan'})
        self.assertEqual(result['excluded']['ambiguous_project'], 2)

    def test_failed_raw_is_partial_but_absent_raw_is_empty(self):
        self.paths['other'].write_text('{broken')
        result = self.read()
        self.assertEqual(self.slugs(result), {'current'})
        self.assertEqual(result['failures'], [{'slug': 'other', 'reporting_group': 'work', 'reason': 'raw_read_failed'}])
        self.assertEqual(result['write_policy'], 'explicit_save_only')
        self.paths['other'].unlink()
        result = self.read()
        self.assertEqual(result['status'], 'complete')
        other = next(p for p in result['groups']['work'] if p['slug'] == 'other')
        self.assertEqual(other['view']['entries'], [])
        self.assertEqual(other['view']['raw_paths'], [])

    def test_fallback_yaml_rejects_unreadable_metadata_before_body_reads(self):
        target = self.config(self.root / 'other', 'work', 'other')
        invalid = ['profile:\n  reporting_group personal\n',
                   'profile: |\n  reporting_group: personal\n',
                   'profile: {}\n', 'profile:\n\treporting_group: personal\n',
                   'profile: work\n  reporting_group: personal\n']
        for content in invalid:
            with self.subTest(content=content), patch.object(raw, 'yaml', None):
                target.write_text(content)
                with patch.object(state, 'read_view', wraps=state.read_view) as reader:
                    result = self.read(scope='work')
                self.assertEqual({call.args[1] for call in reader.call_args_list}, {'current'})
                self.assertEqual(result['status'], 'partial')
                self.assertEqual(result['excluded']['project_metadata_unavailable'], 1)
        target.write_text(invalid[0])
        run = subprocess.run([sys.executable, '-S', '-B', str(ROOT / 'scripts/tracework_raw.py'),
                              'read-report', '--cwd', str(self.cwd), '--report', 'weekly',
                              '--start', '2026-08-01', '--end', '2026-08-31', '--scope', 'work'],
                             capture_output=True, text=True,
                             env={**os.environ, 'HOME': str(self.home), 'USERPROFILE': str(self.home)})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.slugs(json.loads(run.stdout)), {'current'})
        self.assertEqual(json.loads(run.stdout)['status'], 'partial')
        with patch.object(raw, 'yaml', None):
            self.assertEqual(raw.load_yaml_config(ROOT / 'references/tracework-config-template.yaml')
                             ['profile']['default_reporting_group'], 'work')
            self.assertEqual(raw.parse_simple_yaml('daily_note:\n  repos:\n    - /tmp/repo\n'
                                                   'categories:\n  - name: code\n    patterns: ["*.py"]\n'),
                             {'daily_note': {'repos': ['/tmp/repo']},
                              'categories': [{'name': 'code', 'patterns': ['*.py']}]})

    def test_only_known_outside_scope_vault_errors_preserve_complete(self):
        target = self.config(self.root / 'private', 'personal', 'private')
        target.write_text(target.read_text().replace(str(self.vault), str(self.root / 'elsewhere')))
        with patch.object(state, 'read_view', wraps=state.read_view) as reader:
            result = self.read(scope='work')
        self.assertEqual({call.args[1] for call in reader.call_args_list}, {'current', 'other'})
        self.assertEqual((result['status'], result['write_policy']), ('complete', 'normal'))
        self.assertEqual(self.read(scope='personal')['status'], 'partial')
        self.assertEqual(self.read(scope='all')['status'], 'partial')
        target.write_text('profile:\n  reporting_group personal\n')
        with patch.object(raw, 'yaml', None):
            self.assertEqual(self.read(scope='work')['status'], 'partial')
        self.config(self.root / 'private', 'personal', 'private')
        self.rows.append(dict(self.rows[2], path=str(self.root / 'duplicate')))
        self.registry()
        self.assertEqual(self.read(scope='work')['status'], 'partial')

    def test_current_slug_matches_capture_config_without_leaking_to_foreign_projects(self):
        global_config = self.home / '.tracework/config.yaml'
        global_config.parent.mkdir()
        global_config.write_text(f'knowledge_vault: {self.vault}\nproject_slug: actual-project\n')
        (self.cwd / '.tracework/config.yaml').write_text('profile:\n  reporting_group: work\n')
        self.rows = self.rows[1:]
        self.registry()
        self.paths['current'].unlink()
        self.write('vault/raw/weeks/2026-W35/actual-project.json', [self.fact('captured')])
        result = self.read(scope='work')
        self.assertEqual(raw.project_slug(self.cwd), 'actual-project')
        self.assertEqual(self.slugs(result), {'actual-project', 'other'})
        self.assertEqual(result['status'], 'complete')
        actual = next(p for p in result['groups']['work'] if p['slug'] == raw.project_slug(self.cwd))
        self.assertEqual(actual['view']['entries'][0]['summary'], 'captured')
        self.config(self.cwd, 'work', 'local-project')
        self.assertEqual(raw.project_slug(self.cwd), 'local-project')
        self.assertEqual(self.slugs(self.read(scope='work')), {'local-project', 'other'})

    def test_project_filter_never_grants_scope_and_bad_dates_fail_before_reads(self):
        with patch.object(state, 'read_view', side_effect=AssertionError('raw read')):
            self.assertEqual(self.slugs(self.read(project_slugs=['private'])), set())
            self.assertEqual(self.read(project_slugs=['missing'])['status'], 'partial')
            for kwargs in [dict(start='2026-08-31', end='2026-08-01'),
                           dict(start='2026-02-30', end='2026-08-01'),
                           dict(start='2026-08-01', end='2026-08-31', project_slugs=['../escape'])]:
                with self.assertRaises(ValueError):
                    raw.read_report(self.cwd, 'weekly', **kwargs)

    def test_installed_report_callers_agree_and_keep_corrections(self):
        original = self.fact('original')
        replacement = self.fact('corrected')
        original['type'] = replacement['type'] = 'risk'
        replacement['captured_at'] = '2026-09-01T10:00:00+08:00'
        replacement['correction'] = {'operation': 'replace', 'target_ref': {
            'week': '2026-W35', 'entry_index': 0, 'timestamp': original['timestamp']},
            'target_hash': state.entry_hash(original), 'reason': 'fix factual error'}
        self.paths['current'].write_text(json.dumps([original, replacement]))
        views = []
        for kind in ['daily', 'weekly', 'monthly']:
            args = ['read-report', '--cwd', str(self.cwd), '--report', kind,
                    '--start', '2026-08-01', '--end', '2026-08-31', '--project-slug', 'current']
            for prefix in ['skills', 'plugins/tracework/skills']:
                run = self.cli(f'{prefix}/{kind}/scripts/tracework_raw.py', args)
                self.assertEqual(run.returncode, 0, run.stderr)
                view = json.loads(run.stdout)['groups']['work'][0]['view']
                self.assertEqual(view['entries'][0]['summary'], 'corrected')
                self.assertEqual(len(view['correction_history']), 1)
                self.assertEqual(view['states'][0]['state'], 'open')
                self.assertEqual(view['states'][0]['text'], 'corrected')
                views.append(view)
        self.assertTrue(all(v == views[0] for v in views))
        old = self.read(project_slugs=['current'], as_of='2026-08-31T23:59:59+08:00')
        self.assertEqual(old['groups']['work'][0]['view']['entries'][0]['summary'], 'original')

    def test_monthly_partial_never_writes_without_explicit_save(self):
        self.paths['other'].write_text('{broken')
        signals, skeleton = self.root / 'signals.json', self.root / 'skeleton.json'
        args = ['--cwd', str(self.cwd), '--month', '2026-08',
                '--signals-output', str(signals), '--skeleton-output', str(skeleton)]
        run = self.cli('skills/monthly/scripts/prepare_monthly_data.py', args)
        self.assertEqual(run.returncode, 0, run.stderr)
        payload = json.loads(run.stdout)
        self.assertEqual(payload['skeleton']['report_context']['status'], 'partial')
        self.assertEqual({p['project_slug'] for p in payload['signals']['raw_entries']}, {'current'})
        self.assertFalse(signals.exists())
        self.assertFalse(skeleton.exists())
        run = self.cli('skills/monthly/scripts/prepare_monthly_data.py', args + ['--save-draft'])
        self.assertEqual(run.returncode, 0, run.stderr)
        prior = signals.read_bytes()
        failed = self.cli('skills/monthly/scripts/prepare_monthly_data.py', args + ['--save-draft'])
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(signals.read_bytes(), prior)
        self.assertEqual(self.cli('skills/monthly/scripts/prepare_monthly_data.py', args + ['--save-draft', '--overwrite']).returncode, 0)
        # A normal invocation still returns a draft and leaves existing outputs intact.
        self.assertEqual(self.cli('skills/monthly/scripts/prepare_monthly_data.py', args).returncode, 0)
        self.assertEqual(signals.read_bytes(), prior)
        self.registry().write_text('{broken')
        blocked = self.cli('skills/monthly/scripts/prepare_monthly_data.py', args + ['--save-draft', '--overwrite'])
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(signals.read_bytes(), prior)
        self.registry()
        self.config(self.cwd, 'unassigned', 'current')
        local = self.cli('skills/monthly/scripts/prepare_monthly_data.py', args + ['--save-draft', '--overwrite'])
        self.assertEqual(json.loads(local.stdout)['signals']['report_context']['write_policy'], 'conversation_only')
        self.assertEqual(signals.read_bytes(), prior)
        (self.cwd / '.tracework/config.yaml').write_text('project_slug: current\n')
        no_vault = self.cli('skills/monthly/scripts/prepare_monthly_data.py', args + ['--save-draft', '--overwrite'])
        self.assertEqual(json.loads(no_vault.stdout)['signals']['raw_entries'], [])
        self.assertEqual(signals.read_bytes(), prior)


if __name__ == '__main__':
    unittest.main()
