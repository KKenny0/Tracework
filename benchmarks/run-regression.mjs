#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  validateReportContract,
  validateWeeklyBriefCompressionContract,
  validateWeeklyGoalLoopContract,
  validateWeeklyPptReadyMarkdownContract,
  validateWeeklyPptReadyMarkdownRejectionProbes,
  validateWeeklySourceGroundingRecoveryContract,
} from './report-contract.mjs';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '..');
const fixturesPath = path.join(scriptDir, 'regression-fixtures.json');
const captureRaw = path.join(repoRoot, 'skills', 'capture', 'scripts', 'tracework_raw.py');
const monthlyPrepare = path.join(repoRoot, 'skills', 'monthly', 'scripts', 'prepare_monthly_data.py');
const pythonEnv = { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONUTF8: '1' };

const failures = [];
const skipped = [];

function fail(message) {
  failures.push(message);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function runJson(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    encoding: 'utf-8',
    ...options,
    env: { ...pythonEnv, ...(options.env || {}) },
  });
  if (result.status !== 0) {
    throw new Error([
      `${command} ${args.join(' ')} failed with status ${result.status}`,
      result.stdout.trim(),
      result.stderr.trim(),
    ].filter(Boolean).join('\n'));
  }
  return JSON.parse(result.stdout);
}

function runGit(cwd, args, env = {}) {
  const result = spawnSync('git', args, {
    cwd,
    encoding: 'utf-8',
    env: { ...process.env, ...env },
  });
  if (result.status !== 0) {
    throw new Error([
      `git ${args.join(' ')} failed with status ${result.status}`,
      result.stdout.trim(),
      result.stderr.trim(),
    ].filter(Boolean).join('\n'));
  }
  return result.stdout.trim();
}

function gitCommitExists(repo, objectId) {
  return spawnSync('git', ['cat-file', '-e', `${objectId}^{commit}`], {
    cwd: repo,
    encoding: 'utf-8',
  }).status === 0;
}

function gitRepositoryIdentity(repo) {
  try {
    const commonDir = runGit(repo, ['rev-parse', '--git-common-dir']);
    return fs.realpathSync(path.resolve(repo, commonDir));
  } catch {
    return null;
  }
}

function gitIsAncestor(repo, ancestor, descendant) {
  return spawnSync('git', ['merge-base', '--is-ancestor', ancestor, descendant], {
    cwd: repo,
    encoding: 'utf-8',
  }).status === 0;
}

function selectCapturedSnapshot(candidates, asOf, targetRepository, evidenceCommit) {
  const targetIdentity = gitRepositoryIdentity(targetRepository);
  if (!targetIdentity) return null;
  return [...candidates]
    .filter(candidate => Date.parse(candidate.entry_timestamp) <= Date.parse(asOf))
    .sort((left, right) => Date.parse(right.entry_timestamp) - Date.parse(left.entry_timestamp))
    .find(candidate => (
      candidate.source_ref?.type === 'repository_snapshot'
      && path.isAbsolute(candidate.source_ref.path)
      && gitRepositoryIdentity(candidate.source_ref.path) === targetIdentity
      && gitCommitExists(candidate.source_ref.path, candidate.source_ref.ref)
      && gitIsAncestor(candidate.source_ref.path, evidenceCommit, candidate.source_ref.ref)
    )) || null;
}

function runUnsafeSlugFixture(fixture) {
  const config = fixture.fixture || {};
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  const entryPath = path.join(tempRoot, 'entry.json');
  const unsafeSlug = config.unsafe_slug || '../outside';
  try {
    fs.mkdirSync(tempVault);
    fs.writeFileSync(entryPath, JSON.stringify({
      timestamp: '2026-09-26T10:00:00+08:00', type: 'decision',
      summary: 'Synthetic safety check', context: 'Reject unsafe project paths.', source: 'session-recap',
    }));
    const commands = [
      [captureRaw, 'append-entry', '--entry', entryPath, '--cwd', repoRoot, '--date', '2026-09-26'],
      [path.join(repoRoot, 'skills', 'daily', 'scripts', 'tracework_state.py')],
    ];
    for (const args of commands) {
      const result = spawnSync('python3', [...args, '--vault', tempVault, '--slug', unsafeSlug], {
        cwd: repoRoot, encoding: 'utf-8', env: pythonEnv,
      });
      assert(result.status !== 0, `${fixture.id}: ${args[0]} should reject unsafe slug`);
      assert(`${result.stderr}\n${result.stdout}`.includes('invalid project slug'),
        `${fixture.id}: rejection must come from slug validation`);
    }
    assert(fs.readdirSync(tempVault).length === 0, `${fixture.id}: unsafe slug mutated vault`);
    assert(!fs.existsSync(path.join(tempRoot, 'outside.json')), `${fixture.id}: unsafe slug escaped vault`);
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runCaptureHelperRepairFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const entry = config.entry;
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  const entryPath = path.join(tempRoot, 'repair-entry.json');

  try {
    fs.mkdirSync(tempVault, { recursive: true });
    fs.writeFileSync(entryPath, JSON.stringify(entry, null, 2), 'utf-8');
    const appendResult = runJson('python3', [
      captureRaw,
      'append-entry',
      '--entry',
      entryPath,
      '--cwd',
      repoRoot,
      '--vault',
      tempVault,
      '--slug',
      slug,
      '--date',
      config.date,
    ]);

    assert(appendResult.week === config.expected_week, `${fixture.id}: wrote week ${appendResult.week}`);
    assert(appendResult.slug === slug, `${fixture.id}: wrote slug ${appendResult.slug}`);
    assert(appendResult.entries_appended === 1, `${fixture.id}: expected one appended entry`);
    assert(fs.existsSync(appendResult.path), `${fixture.id}: missing raw output ${appendResult.path}`);

    const entries = readJson(appendResult.path);
    assert(Array.isArray(entries), `${fixture.id}: raw output should be a JSON array`);
    assert(entries.length === 1, `${fixture.id}: expected exactly one raw entry`);
    const appended = entries[0] || {};

    assert(appended.source === 'session-recap', `${fixture.id}: expected source=session-recap`);
    assert(appended.archetype === 'repair', `${fixture.id}: expected archetype=repair`);
    assert(String(appended.root_cause || '').includes('export time'), `${fixture.id}: root_cause lost late export guard`);
    assert(String(appended.root_cause || '').includes('validation repair loop'), `${fixture.id}: root_cause lost repair-loop ownership`);
    assert(
      Array.isArray(appended.exploration_paths)
        && appended.exploration_paths.some(item => String(item).includes('export fallback'))
        && appended.exploration_paths.some(item => String(item).includes('upfront validation')),
      `${fixture.id}: exploration_paths should preserve both compared paths`,
    );
    assert(
      Array.isArray(appended.abandoned_alternatives)
        && appended.abandoned_alternatives.some(item => String(item).includes('Export fallback only')),
      `${fixture.id}: abandoned_alternatives should preserve rejected fallback-only path`,
    );
    assert(typeof appended.impact === 'string' && appended.impact.length > 0, `${fixture.id}: missing impact`);
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runCaptureHelperReportingValidFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const entry = config.entry;
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  const entryPath = path.join(tempRoot, 'reporting-entry.json');

  try {
    fs.mkdirSync(tempVault, { recursive: true });
    fs.writeFileSync(entryPath, JSON.stringify(entry, null, 2), 'utf-8');
    const appendResult = runJson('python3', [
      captureRaw,
      'append-entry',
      '--entry',
      entryPath,
      '--cwd',
      repoRoot,
      '--vault',
      tempVault,
      '--slug',
      slug,
      '--date',
      config.date,
    ]);
    const entries = readJson(appendResult.path);
    const appended = entries[0] || {};
    if (config.expected_capture_depth) {
      assert(
        appended.capture_depth === config.expected_capture_depth,
        `${fixture.id}: capture_depth not preserved`,
      );
    }
    assert(appended.reporting?.outcome_candidate?.kind === config.expected_kind, `${fixture.id}: reporting kind not preserved`);
    assert(appended.reporting?.impact_boundary === config.expected_impact_boundary, `${fixture.id}: impact boundary not preserved`);
    assert(appended.reporting?.evidence_boundary === config.expected_evidence_boundary, `${fixture.id}: evidence boundary not preserved`);
    assert(
      appended.reporting?.hard_signals?.some(signal => signal.kind === config.expected_hard_signal_kind),
      `${fixture.id}: hard signal kind not preserved`,
    );
    if (config.expected_commit_source_path) {
      assert(
        appended.source_refs?.some(ref => ref.type === 'commit' && ref.path === config.expected_commit_source_path),
        `${fixture.id}: qualified commit source path not preserved`,
      );
    }
    if (config.expected_repository_snapshot_ref) {
      assert(
        appended.source_refs?.some(ref => (
          ref.type === 'repository_snapshot'
          && ref.ref === config.expected_repository_snapshot_ref
          && ref.path === config.expected_repository_snapshot_path
        )),
        `${fixture.id}: immutable repository snapshot not preserved`,
      );
    }
    if (config.expected_doc_source_ref) {
      assert(
        appended.source_refs?.some(ref => (
          ref.type === 'doc'
          && ref.ref === config.expected_doc_source_ref
          && ref.url === config.expected_doc_source_url
        )),
        `${fixture.id}: durable document locator not preserved`,
      );
    }
    for (const [index, probe] of (config.invalid_repository_snapshot_probes || []).entries()) {
      const invalidEntry = structuredClone(entry);
      const snapshot = invalidEntry.source_refs.find(ref => ref.type === 'repository_snapshot');
      snapshot.ref = probe.ref;
      snapshot.path = probe.path;
      const invalidPath = path.join(tempRoot, `invalid-snapshot-${index}.json`);
      fs.writeFileSync(invalidPath, JSON.stringify(invalidEntry, null, 2), 'utf-8');
      const result = spawnSync('python3', [
        captureRaw,
        'append-entry',
        '--entry',
        invalidPath,
        '--cwd',
        repoRoot,
        '--vault',
        tempVault,
        '--slug',
        slug,
        '--date',
        config.date,
      ], {
        cwd: repoRoot,
        encoding: 'utf-8',
        env: pythonEnv,
      });
      assert(result.status !== 0, `${fixture.id}: malformed repository snapshot should fail`);
      assert(
        `${result.stderr}\n${result.stdout}`.includes(probe.expected_error_text),
        `${fixture.id}: missing snapshot validation error ${probe.expected_error_text}`,
      );
    }
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runGitSnapshotResolutionFixture(fixture) {
  const config = fixture.fixture || {};
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-git-snapshot-'));
  const otherRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-other-repo-'));

  try {
    runGit(tempRoot, ['init', '-b', 'main']);
    runGit(tempRoot, ['config', 'user.name', 'Tracework Benchmark']);
    runGit(tempRoot, ['config', 'user.email', 'benchmark@example.invalid']);

    fs.writeFileSync(path.join(tempRoot, 'architecture.txt'), 'base\n', 'utf-8');
    runGit(tempRoot, ['add', 'architecture.txt']);
    runGit(tempRoot, ['commit', '-m', 'base'], {
      GIT_AUTHOR_DATE: '2026-07-30T10:00:00+08:00',
      GIT_COMMITTER_DATE: '2026-07-30T10:00:00+08:00',
    });
    const baseCommit = runGit(tempRoot, ['rev-parse', 'HEAD']);

    fs.writeFileSync(path.join(tempRoot, 'architecture.txt'), 'base\nevidence delta\n', 'utf-8');
    runGit(tempRoot, ['add', 'architecture.txt']);
    runGit(tempRoot, ['commit', '-m', 'evidence delta'], {
      GIT_AUTHOR_DATE: '2026-07-31T10:00:00+08:00',
      GIT_COMMITTER_DATE: '2026-07-31T10:00:00+08:00',
    });
    const evidenceCommit = runGit(tempRoot, ['rev-parse', 'HEAD']);

    fs.writeFileSync(path.join(tempRoot, 'architecture.txt'), 'base\nevidence delta\ncaptured state\n', 'utf-8');
    runGit(tempRoot, ['add', 'architecture.txt']);
    runGit(tempRoot, ['commit', '-m', 'captured architecture'], {
      GIT_AUTHOR_DATE: '2026-07-31T17:00:00+08:00',
      GIT_COMMITTER_DATE: '2026-07-31T17:00:00+08:00',
    });
    const capturedSnapshot = runGit(tempRoot, ['rev-parse', 'HEAD']);

    runGit(tempRoot, ['checkout', '-b', 'divergent', baseCommit]);
    fs.writeFileSync(path.join(tempRoot, 'architecture.txt'), 'base\ndivergent state\n', 'utf-8');
    runGit(tempRoot, ['add', 'architecture.txt']);
    runGit(tempRoot, ['commit', '-m', 'later divergent architecture'], {
      GIT_AUTHOR_DATE: '2026-08-01T08:00:00+08:00',
      GIT_COMMITTER_DATE: '2026-08-01T08:00:00+08:00',
    });
    const laterSnapshot = runGit(tempRoot, ['rev-parse', 'HEAD']);
    const divergentSnapshot = laterSnapshot;

    runGit(otherRoot, ['init', '-b', 'main']);
    runGit(otherRoot, ['config', 'user.name', 'Tracework Benchmark']);
    runGit(otherRoot, ['config', 'user.email', 'benchmark@example.invalid']);
    fs.writeFileSync(path.join(otherRoot, 'architecture.txt'), 'unrelated repository\n', 'utf-8');
    runGit(otherRoot, ['add', 'architecture.txt']);
    runGit(otherRoot, ['commit', '-m', 'unrelated snapshot']);
    const otherSnapshot = runGit(otherRoot, ['rev-parse', 'HEAD']);
    const missingObject = 'f'.repeat(capturedSnapshot.length);
    const candidates = [
      {
        entry_timestamp: config.eligible_snapshot_at,
        source_ref: {type: 'repository_snapshot', ref: capturedSnapshot, path: tempRoot},
      },
      {
        entry_timestamp: '2026-07-31T20:00:00+08:00',
        source_ref: {type: 'repository_snapshot', ref: otherSnapshot, path: otherRoot},
      },
      {
        entry_timestamp: '2026-07-31T19:00:00+08:00',
        source_ref: {type: 'repository_snapshot', ref: divergentSnapshot, path: tempRoot},
      },
      {
        entry_timestamp: '2026-07-31T18:30:00+08:00',
        source_ref: {type: 'repository_snapshot', ref: missingObject, path: tempRoot},
      },
      {
        entry_timestamp: config.late_snapshot_at,
        source_ref: {type: 'repository_snapshot', ref: laterSnapshot, path: tempRoot},
      },
    ];

    const selected = selectCapturedSnapshot(candidates, config.as_of, tempRoot, evidenceCommit);
    assert(selected?.source_ref.ref === capturedSnapshot, `${fixture.id}: wrong snapshot selected for as_of`);
    assert(runGit(tempRoot, ['rev-parse', 'HEAD']) !== capturedSnapshot, `${fixture.id}: fixture did not move current HEAD`);
    assert(
      spawnSync('git', ['merge-base', '--is-ancestor', evidenceCommit, capturedSnapshot], {cwd: tempRoot}).status === 0,
      `${fixture.id}: evidence commit should be an ancestor of the captured snapshot`,
    );
    assert(!gitCommitExists(tempRoot, missingObject), `${fixture.id}: missing object unexpectedly resolved`);
    assert(
      selectCapturedSnapshot([{entry_timestamp: config.eligible_snapshot_at, source_ref: {type: 'repository_snapshot', ref: missingObject, path: tempRoot}}], config.as_of, tempRoot, evidenceCommit) === null,
      `${fixture.id}: unavailable snapshot should degrade instead of resolving`,
    );
    assert(
      selectCapturedSnapshot([{entry_timestamp: config.eligible_snapshot_at, source_ref: {type: 'repository_snapshot', ref: divergentSnapshot, path: tempRoot}}], config.as_of, tempRoot, evidenceCommit) === null,
      `${fixture.id}: divergent snapshot should degrade instead of resolving`,
    );
    assert(
      selectCapturedSnapshot([{entry_timestamp: config.eligible_snapshot_at, source_ref: {type: 'repository_snapshot', ref: otherSnapshot, path: otherRoot}}], config.as_of, tempRoot, evidenceCommit) === null,
      `${fixture.id}: other repository snapshot should degrade instead of resolving`,
    );
  } finally {
    fs.rmSync(tempRoot, {recursive: true, force: true});
    fs.rmSync(otherRoot, {recursive: true, force: true});
  }
}

function runCaptureHelperCaptureDepthInvalidFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const entry = config.entry;
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  const entryPath = path.join(tempRoot, 'bad-capture-depth-entry.json');

  try {
    fs.mkdirSync(tempVault, { recursive: true });
    fs.writeFileSync(entryPath, JSON.stringify(entry, null, 2), 'utf-8');
    const result = spawnSync('python3', [
      captureRaw,
      'append-entry',
      '--entry',
      entryPath,
      '--cwd',
      repoRoot,
      '--vault',
      tempVault,
      '--slug',
      slug,
      '--date',
      config.date,
    ], {
      cwd: repoRoot,
      encoding: 'utf-8',
      env: pythonEnv,
    });
    assert(result.status !== 0, `${fixture.id}: invalid capture_depth enum should fail`);
    assert(
      `${result.stderr}\n${result.stdout}`.includes(config.expected_error_text),
      `${fixture.id}: missing validation error ${config.expected_error_text}`,
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runCaptureHelperReportingInvalidFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const entry = config.entry;
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  const entryPath = path.join(tempRoot, 'bad-reporting-entry.json');

  try {
    fs.mkdirSync(tempVault, { recursive: true });
    fs.writeFileSync(entryPath, JSON.stringify(entry, null, 2), 'utf-8');
    const result = spawnSync('python3', [
      captureRaw,
      'append-entry',
      '--entry',
      entryPath,
      '--cwd',
      repoRoot,
      '--vault',
      tempVault,
      '--slug',
      slug,
      '--date',
      config.date,
    ], {
      cwd: repoRoot,
      encoding: 'utf-8',
      env: pythonEnv,
    });
    assert(result.status !== 0, `${fixture.id}: invalid reporting enum should fail`);
    assert(
      `${result.stderr}\n${result.stdout}`.includes(config.expected_error_text),
      `${fixture.id}: missing validation error ${config.expected_error_text}`,
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runArtifactUpsertDossierFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  const dossierPath = path.join(tempRoot, 'artifact-dossier.json');
  const thinPath = path.join(tempRoot, 'artifact-thin.json');

  try {
    fs.mkdirSync(tempVault, { recursive: true });
    const dossierArtifact = structuredClone(config.dossier_artifact);
    const thinArtifact = structuredClone(config.thin_artifact);
    dossierArtifact.path = path.join(tempRoot, 'project', dossierArtifact.repo_relative_path || 'reporting-model.md');
    thinArtifact.path = path.join(tempRoot, 'project', 'docs', 'thin.md');
    for (const sourceRef of dossierArtifact.source_entry_refs || []) {
      if (sourceRef && typeof sourceRef === 'object' && typeof sourceRef.path === 'string') {
        sourceRef.path = path.join(tempVault, 'raw', 'weeks', sourceRef.week || 'unknown-week', `${slug}.json`);
      }
    }
    fs.writeFileSync(dossierPath, JSON.stringify(dossierArtifact, null, 2), 'utf-8');
    fs.writeFileSync(thinPath, JSON.stringify(thinArtifact, null, 2), 'utf-8');
    const dossierResult = runJson('python3', [
      captureRaw,
      'upsert-artifact',
      '--artifact',
      dossierPath,
      '--cwd',
      repoRoot,
      '--vault',
      tempVault,
      '--slug',
      slug,
    ]);
    runJson('python3', [
      captureRaw,
      'upsert-artifact',
      '--artifact',
      thinPath,
      '--cwd',
      repoRoot,
      '--vault',
      tempVault,
      '--slug',
      slug,
    ]);
    const artifacts = readJson(dossierResult.path);
    assert(artifacts.length === 2, `${fixture.id}: expected dossier and old thin artifact`);
    const dossier = artifacts.find(item => item.id === config.dossier_artifact.id) || {};
    const thin = artifacts.find(item => item.id === config.thin_artifact.id) || {};
    assert(dossier.artifact_summary?.scope === config.expected_scope, `${fixture.id}: dossier scope not preserved`);
    assert(dossier.source_availability === config.expected_source_availability, `${fixture.id}: source availability not preserved`);
    assert(dossier.deletion_behavior === config.expected_deletion_behavior, `${fixture.id}: deletion behavior not preserved`);
    assert(
      dossier.artifact_summary?.key_decisions?.includes(config.expected_design_relationship),
      `${fixture.id}: recoverable design relationship not preserved`,
    );
    assert(thin.id === config.thin_artifact.id && !thin.artifact_summary, `${fixture.id}: old thin artifact was not preserved as thin`);
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runCaptureSourceRequiredWarningFixture(fixture) {
  const config = fixture.fixture || {};
  const artifact = config.artifact || {};
  const receipt = String(config.candidate_receipt || '');
  assert(artifact.deletion_behavior === 'source_required', `${fixture.id}: fixture is not source-required`);
  assert(artifact.source_availability === 'missing', `${fixture.id}: fixture source is not missing`);
  assert(artifact.last_seen?.exists === false, `${fixture.id}: fixture still claims the source exists`);
  for (const term of config.required_warning_terms || []) {
    assert(receipt.includes(term), `${fixture.id}: capture receipt omits source deletion warning term ${term}`);
  }
  const mutant = receipt.replace(config.warning_line, '');
  assert(
    (config.required_warning_terms || []).some(term => !mutant.includes(term)),
    `${fixture.id}: removing the warning line did not invalidate the receipt`,
  );
}

function runMonthlyPrepareDailyReportFixture(fixture) {
  const config = fixture.fixture || {};
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const inputPath = path.join(tempRoot, config.archive_name || '2026-07.md');
  const signalsPath = path.join(tempRoot, 'signals.json');
  const skeletonPath = path.join(tempRoot, 'skeleton.json');
  const tempVault = path.join(tempRoot, 'vault');

  try {
    fs.writeFileSync(inputPath, `${config.daily_note_archive.join('\n')}\n`, 'utf-8');
    const rawDir = path.join(tempVault, 'raw', 'weeks', '2026-W28');
    fs.mkdirSync(rawDir, { recursive: true });
    fs.writeFileSync(
      path.join(rawDir, `${config.expected_slug}.json`),
      `${JSON.stringify(config.raw_entries || [], null, 2)}\n`,
      'utf-8',
    );
    fs.writeFileSync(
      path.join(tempVault, 'raw', 'projects.json'),
      `${JSON.stringify([{ name: config.expected_project, slug: config.expected_slug, path: '/tmp/tracework', reporting_group: config.expected_reporting_group }], null, 2)}\n`,
      'utf-8',
    );
    const result = spawnSync('python3', [
      monthlyPrepare,
      '--cwd',
      tempRoot,
      '--scope',
      config.expected_reporting_group,
      '--input',
      inputPath,
      '--signals-output',
      signalsPath,
      '--skeleton-output',
      skeletonPath,
      '--vault',
      tempVault,
      '--month',
      '2026-07',
      '--summary-mode',
      'project_focused',
    ], {
      cwd: repoRoot,
      encoding: 'utf-8',
      env: pythonEnv,
    });
    if (result.status !== 0) {
      throw new Error([result.stdout.trim(), result.stderr.trim()].filter(Boolean).join('\n'));
    }
    const signals = readJson(signalsPath);
    const skeleton = readJson(skeletonPath);
    assert(signals.raw_entries?.length === (config.raw_entries || []).length, `${fixture.id}: matching raw entries not loaded`);
    assert(skeleton.projects?.[config.expected_slug]?.raw_entry_indexes.length === (config.raw_entries || []).length, `${fixture.id}: raw indexes missing`);
    assert(skeleton.reporting_groups?.[config.expected_reporting_group]?.includes(config.expected_slug), `${fixture.id}: group missing`);
    assert(skeleton.raw_work_streams?.some(item => item.work_stream === config.expected_work_stream), `${fixture.id}: explicit stream missing`);
    assert(!('statistics' in skeleton) && !('by_project' in skeleton), `${fixture.id}: Daily semantic derivation survived`);
    assert(signals.editorial_context.length === 0, `${fixture.id}: display-name-only legacy context admitted`);
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runExecutableFixture(fixture) {
  const kind = fixture.execution?.kind || 'documented-only';
  if (kind === 'capture-helper-repair') {
    runCaptureHelperRepairFixture(fixture);
  } else if (kind === 'capture-helper-reporting-valid') {
    runCaptureHelperReportingValidFixture(fixture);
  } else if (kind === 'capture-helper-capture-depth-invalid') {
    runCaptureHelperCaptureDepthInvalidFixture(fixture);
  } else if (kind === 'capture-helper-reporting-invalid') {
    runCaptureHelperReportingInvalidFixture(fixture);
  } else if (kind === 'artifact-upsert-dossier') {
    runArtifactUpsertDossierFixture(fixture);
  } else if (kind === 'capture-source-required-warning') {
    runCaptureSourceRequiredWarningFixture(fixture);
  } else if (kind === 'monthly-prepare-daily-report-format') {
    runMonthlyPrepareDailyReportFixture(fixture);
  } else if (kind === 'report-contract') {
    validateReportContract(fixture);
  } else if (kind === 'weekly-goal-loop-contract') {
    validateWeeklyGoalLoopContract(fixture);
  } else if (kind === 'weekly-brief-compression-contract') {
    validateWeeklyBriefCompressionContract(fixture);
  } else if (kind === 'weekly-ppt-ready-markdown-contract') {
    validateWeeklyPptReadyMarkdownContract(fixture);
    validateWeeklyPptReadyMarkdownRejectionProbes(fixture);
  } else if (kind === 'weekly-source-grounding-recovery-contract') {
    validateWeeklySourceGroundingRecoveryContract(fixture);
  } else if (kind === 'git-snapshot-resolution') {
    runGitSnapshotResolutionFixture(fixture);
  } else if (kind === 'unsafe-slug') {
    runUnsafeSlugFixture(fixture);
  } else if (kind === 'documented-only') {
    skipped.push(fixture.id);
  } else {
    throw new Error(`unknown executable fixture kind: ${kind}`);
  }
}

function main() {
  const data = readJson(fixturesPath);
  const fixtures = Array.isArray(data.fixtures) ? data.fixtures : [];
  for (const fixture of fixtures) {
    try {
      runExecutableFixture(fixture);
    } catch (error) {
      fail(`${fixture.id}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  if (failures.length > 0) {
    console.error('Regression checks failed:');
    for (const failure of failures) console.error(`- ${failure}`);
    if (skipped.length > 0) {
      console.error(`Documented-only fixtures: ${skipped.join(', ')}`);
    }
    process.exit(1);
  }

  console.log(`Regression checks passed (${fixtures.length - skipped.length} executable, ${skipped.length} documented).`);
  if (skipped.length > 0) {
    console.log(`Documented-only fixtures: ${skipped.join(', ')}`);
  }
}

main();
