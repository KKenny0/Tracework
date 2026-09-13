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
const decisionGraph = path.join(repoRoot, 'skills', 'query', 'scripts', 'decision_graph.py');
const roadmapGraph = path.join(repoRoot, 'skills', 'roadmap', 'scripts', 'decision_graph.py');
const recallContext = path.join(repoRoot, 'skills', 'recall', 'scripts', 'recall_context.py');
const monthlyPrepare = path.join(repoRoot, 'skills', 'monthly', 'scripts', 'prepare_monthly_data.py');
const pythonEnv = { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONUTF8: '1' };

const STORYBOARD_PIPELINE_RAW_WEEKS = {
  '2026-W18': [
    {
      timestamp: '2026-04-28T16:20:00+08:00',
      type: 'feature',
      summary: 'Split storyboard validation into deterministic schema checks and LLM-assisted repair loops',
      context: 'Single-pass validation hid recurring panel continuity failures until export time. The split gives weekly reporting a clear reliability story and gives future debugging a stable contract boundary.',
      source: 'session-recap',
      status: 'done',
      impact: 'Weekly reporting can explain the reliability improvement without re-reading implementation commits.',
      project_area: 'validation',
      work_stream: 'Storyboard reliability',
      evidence_refs: ['abc1234', 'eval:continuity-regression-07'],
    },
    {
      timestamp: '2026-04-29T11:45:00+08:00',
      type: 'decision',
      summary: 'Kept panel layout generation separate from dialogue generation to preserve independent retry boundaries',
      context: 'Combining both stages made repair cheaper in the happy path but caused dialogue rewrites during layout-only failures. Separate contracts trade a small orchestration cost for more predictable retries.',
      source: 'session-recap',
      status: 'decision',
      impact: 'Architecture docs now preserve the retry-boundary decision for future stage changes.',
      project_area: 'pipeline orchestration',
      work_stream: 'Stage contract design',
      evidence_refs: ['doc:pipeline-evolution-v1'],
    },
  ],
  '2026-W19': [
    {
      timestamp: '2026-05-05T18:10:00+08:00',
      type: 'decision',
      summary: 'Kept validation repair loops inside the validation stage while preserving orchestration-level retry boundaries',
      context: 'Moving repair ownership upstream would make orchestration aware of validation internals. Keeping ownership local preserves stage encapsulation, while artifact index metadata gives future recall a stable document entry point.',
      source: 'session-recap',
      status: 'decision',
      impact: 'Future session-start recall can point directly to the validation-stage architecture doc instead of re-reading all weekly entries.',
      project_area: 'validation',
      work_stream: 'Stage contract design',
      evidence_refs: ['doc:validation-stage-v1'],
      motivation: 'Repair ownership was becoming ambiguous between validation and orchestration.',
      exploration_paths: [
        'Move repair ownership upstream into orchestration -> centralizes retries but leaks validation internals',
        'Keep repair ownership inside validation -> preserves encapsulation and narrower retry scope',
      ],
      abandoned_alternatives: [
        'Orchestration-level repair ownership: rejected because it would make orchestration depend on validation internals',
      ],
      open_questions: [
        'Should repair-loop latency be tracked at validation-stage level or orchestration level?',
      ],
    },
    {
      timestamp: '2026-05-06T09:30:00+08:00',
      type: 'risk',
      summary: 'Identified stale architecture docs as a recall risk when stage contracts change without re-indexing',
      context: 'Session-start recall can only be trusted if indexed docs remain tied to current contracts. Session recap should record sync suggestions after implementation changes.',
      source: 'session-recap',
      status: 'risk',
      impact: 'Decision roadmap and weekly outline can surface stale indexed docs before they mislead future sessions.',
      project_area: 'documentation',
      work_stream: 'Artifact governance',
      motivation: 'Artifact dossier index introduces a new source navigation and recorded-context layer that can become stale.',
      open_questions: [
        'What signal should mark an indexed artifact as stale: file mtime, raw entry lifecycle, or explicit sync suggestion?',
      ],
      sync_suggestions: [
        'Review architecture docs and artifact metadata when stage contracts change.',
      ],
    },
  ],
  '2026-W20': [
    {
      timestamp: '2026-05-12T10:15:00+08:00',
      archetype: 'decision',
      type: 'decision',
      summary: 'Chose explicit retry budget policy for validation repair loops',
      context: 'Validation repair loops needed a durable thread separate from broader orchestration governance. The raw entry records the policy thread directly so decision replay does not infer the topic from artifact hints.',
      source: 'session-recap',
      status: 'decision',
      project_area: 'orchestration',
      work_stream: 'Artifact governance',
      decision_threads: ['retry-budget-policy'],
      lifecycle_transition: {
        subject: 'decision:retry-budget-policy',
        from: 'proposed',
        to: 'chosen',
        reason: 'Validation repair retries need an explicit budget before orchestration retries are considered.',
      },
      source_refs: [
        {
          type: 'conversation',
          ref: 'session:2026-05-12-validation-retry-budget',
          note: 'Session discussion selected the validation-local retry budget policy.',
        },
      ],
      motivation: 'Without an explicit retry budget policy, validation-stage repair could be confused with orchestration-level retry governance.',
      exploration_paths: [
        'Infer retry policy from artifact topics -> keeps raw entries shorter but lets artifact metadata dominate thread assignment',
        'Record retry-budget-policy as an explicit decision thread -> preserves the intended replay topic',
      ],
      abandoned_alternatives: [
        'Artifact-derived retry thread: rejected because artifact governance hints should not override raw-entry decision intent',
      ],
      impact: 'Decision replay can group validation retry budget decisions without relying on artifact metadata.',
      evidence_refs: ['conversation:2026-05-12-validation-retry-budget'],
      artifact_context: [
        {
          artifact_path: '/Users/example/projects/storyboard-pipeline/DESIGN.md',
          scope: 'Orchestration retry governance and artifact lifecycle review.',
          delta: 'Noted that validation repair retry budget is owned by the validation stage.',
          open_questions: [],
          source_of_truth: ['src/stages/validation.py', 'tests/test_validation_retry_budget.py'],
        },
      ],
    },
  ],
};

const FIXTURE_PRESETS = {
  'storyboard-pipeline-decision-replay': {
    project_slug: 'storyboard-pipeline',
    raw_weeks: STORYBOARD_PIPELINE_RAW_WEEKS,
  },
};

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

function assertSourceRefs(nodes, fixtureId) {
  assert(nodes.length > 0, `${fixtureId}: expected at least one node`);
  for (const node of nodes) {
    assert(Array.isArray(node.source_entry_refs), `${fixtureId}: node ${node.id} missing source_entry_refs`);
    assert(node.source_entry_refs.length > 0, `${fixtureId}: node ${node.id} has empty source_entry_refs`);
    for (const ref of node.source_entry_refs) {
      assert(typeof ref.week === 'string' && ref.week, `${fixtureId}: source ref missing week`);
      assert(typeof ref.path === 'string' && ref.path, `${fixtureId}: source ref missing path`);
      assert(typeof ref.timestamp === 'string' && ref.timestamp, `${fixtureId}: source ref missing timestamp`);
      assert(Number.isInteger(ref.entry_index), `${fixtureId}: source ref missing entry_index`);
    }
  }
}

function assertNoSymlinks(root, sourceLabel) {
  const stack = [root];
  while (stack.length > 0) {
    const current = stack.pop();
    const stat = fs.lstatSync(current);
    if (stat.isSymbolicLink()) {
      throw new Error(`fixture vault must not contain symlinks: ${sourceLabel}`);
    }
    if (!stat.isDirectory()) continue;
    for (const entry of fs.readdirSync(current)) {
      stack.push(path.join(current, entry));
    }
  }
}

function writeRawWeek(tempVault, week, slug, entries) {
  if (!slug) throw new Error('raw fixture requires project_slug');
  if (!Array.isArray(entries)) throw new Error(`raw fixture week ${week} must be an array`);
  const rawPath = path.join(tempVault, 'raw', 'weeks', week, `${slug}.json`);
  fs.mkdirSync(path.dirname(rawPath), { recursive: true });
  fs.writeFileSync(rawPath, `${JSON.stringify(entries, null, 2)}\n`, 'utf-8');
}

function copyFixtureVault(config) {
  const preset = config.fixture_preset ? FIXTURE_PRESETS[config.fixture_preset] : null;
  if (config.fixture_preset && !preset) {
    throw new Error(`unknown fixture preset: ${config.fixture_preset}`);
  }
  const effectiveConfig = preset ? { ...preset, ...config } : config;
  if (effectiveConfig.raw_weeks && typeof effectiveConfig.raw_weeks === 'object') {
    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
    const tempVault = path.join(tempRoot, 'vault');
    for (const [week, entries] of Object.entries(effectiveConfig.raw_weeks)) {
      writeRawWeek(tempVault, week, effectiveConfig.project_slug, entries);
    }
    return { tempRoot, tempVault };
  }
  if (Array.isArray(effectiveConfig.raw_entries)) {
    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
    const tempVault = path.join(tempRoot, 'vault');
    const week = effectiveConfig.week || '2026-W24';
    writeRawWeek(tempVault, week, effectiveConfig.project_slug, effectiveConfig.raw_entries);
    return { tempRoot, tempVault };
  }
  const sourceVault = path.resolve(repoRoot, effectiveConfig.vault);
  const realSourceVault = fs.realpathSync(sourceVault);
  const allowedRoots = [
    fs.realpathSync(path.join(repoRoot, 'benchmarks')),
  ];
  if (!allowedRoots.some(root => realSourceVault === root || realSourceVault.startsWith(`${root}${path.sep}`))) {
    throw new Error(`fixture vault must be under benchmarks/: ${effectiveConfig.vault}`);
  }
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-regression-'));
  const tempVault = path.join(tempRoot, 'vault');
  fs.cpSync(realSourceVault, tempVault, { recursive: true, dereference: false });
  assertNoSymlinks(tempVault, effectiveConfig.vault);
  return { tempRoot, tempVault };
}

function assertQueryMetadata(queryPack, fixture) {
  assert(Array.isArray(queryPack.matched_terms), `${fixture.id}: missing matched_terms`);
  assert(
    typeof queryPack.evidence_strength === 'string' && queryPack.evidence_strength,
    `${fixture.id}: missing evidence_strength`,
  );
  assert(
    typeof queryPack.answerability_reason === 'string' && queryPack.answerability_reason,
    `${fixture.id}: missing answerability_reason`,
  );
}

function assertMatchedTerms(queryPack, expectedTerms, fixtureId) {
  if (!Array.isArray(expectedTerms) || expectedTerms.length === 0) return;
  const matched = new Set((queryPack.matched_terms || []).map(term => String(term).toLowerCase()));
  for (const term of expectedTerms) {
    assert(matched.has(String(term).toLowerCase()), `${fixtureId}: matched_terms missing ${term}`);
  }
}

function buildDecisionIndex(tempVault, slug) {
  const buildResult = runJson('python3', [
    decisionGraph,
    'build',
    '--vault',
    tempVault,
    '--slug',
    slug,
    '--cwd',
    repoRoot,
  ]);
  const index = readJson(buildResult.path);
  return { buildResult, index };
}

function queryDecisionIndex(tempVault, slug, query, mode = 'why') {
  return runJson('python3', [
    decisionGraph,
    'query',
    query,
    '--vault',
    tempVault,
    '--slug',
    slug,
    '--mode',
    mode,
    '--limit',
    '5',
  ]);
}

function roadmapDecisionIndex(tempVault, slug, limitThreads = 10) {
  return runJson('python3', [
    roadmapGraph,
    'roadmap',
    '--vault',
    tempVault,
    '--slug',
    slug,
    '--cwd',
    repoRoot,
    '--limit-threads',
    String(limitThreads),
  ]);
}

function assertBuiltIndex(index, slug, fixtureId) {
  assert(index.schema_version === 'tracework.decision_replay.v1', `${fixtureId}: bad index schema`);
  assert(index.project_slug === slug, `${fixtureId}: bad project slug`);
  assert(index.source?.builder_version === 4, `${fixtureId}: bad decision index builder version`);
  assert(Array.isArray(index.nodes), `${fixtureId}: index nodes must be an array`);
  assert(Array.isArray(index.edges), `${fixtureId}: index edges must be an array`);
  assertSourceRefs(index.nodes, fixtureId);
}

function runQueryPositiveFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const query = config.query;
  const mode = config.mode || 'why';
  const { tempRoot, tempVault } = copyFixtureVault(config);

  try {
    const { index } = buildDecisionIndex(tempVault, slug);
    assertBuiltIndex(index, slug, fixture.id);

    const queryPack = queryDecisionIndex(tempVault, slug, query, mode);
    assert(queryPack.schema_version === 'tracework.decision_query.v1', `${fixture.id}: bad query schema`);
    assert(queryPack.answerable === true, `${fixture.id}: expected query to be answerable`);
    assertQueryMetadata(queryPack, fixture);
    assertMatchedTerms(queryPack, config.expected_matched_terms, fixture.id);
    assert(Array.isArray(queryPack.top_nodes) && queryPack.top_nodes.length > 0, `${fixture.id}: missing top nodes`);
    const topNode = queryPack.top_nodes[0] || {};
    assert(
      topNode.id === config.expected_top_node,
      `${fixture.id}: expected top node ${config.expected_top_node}, got ${topNode.id}`,
    );
    assert(topNode.confidence === 'explicit', `${fixture.id}: expected explicit top node`);
    assertSourceRefs(queryPack.top_nodes, fixture.id);
    if (config.expected_evidence_strength) {
      assert(
        queryPack.evidence_strength === config.expected_evidence_strength,
        `${fixture.id}: expected evidence_strength ${config.expected_evidence_strength}, got ${queryPack.evidence_strength}`,
      );
    }
    if (config.expected_missing_evidence_text) {
      assert(
        queryPack.missing_evidence?.some(item => String(item).includes(config.expected_missing_evidence_text)),
        `${fixture.id}: missing_evidence should mention ${config.expected_missing_evidence_text}`,
      );
    }
    if (config.expected_evidence_ref) {
      assert(
        topNode.evidence_refs?.includes(config.expected_evidence_ref),
        `${fixture.id}: compact top node lost evidence ref ${config.expected_evidence_ref}`,
      );
    }
    if (config.expected_direct_artifact_ref) {
      assert(
        topNode.direct_artifact_refs?.includes(config.expected_direct_artifact_ref),
        `${fixture.id}: compact top node lost source-of-truth artifact ref ${config.expected_direct_artifact_ref}`,
      );
    }
    if (config.expected_supporting_decision_absent) {
      assert(
        !queryPack.supporting_nodes?.some(node => String(node.decision || '').includes(config.expected_supporting_decision_absent)),
        `${fixture.id}: unrelated supporting node leaked into the query pack`,
      );
    }
    if (config.expected_thread_id) {
      const indexedTopNode = index.nodes.find(node => node.id === config.expected_top_node) || {};
      assert(topNode.thread_id === config.expected_thread_id, `${fixture.id}: top node thread_id was ${topNode.thread_id}`);
      assert(
        indexedTopNode.thread_id === config.expected_thread_id,
        `${fixture.id}: indexed node thread_id was ${indexedTopNode.thread_id}`,
      );
    }
    if (Array.isArray(config.expected_topic_key_prefix)) {
      for (const [index, expectedKey] of config.expected_topic_key_prefix.entries()) {
        assert(
          topNode.topic_keys?.[index] === expectedKey,
          `${fixture.id}: expected topic_keys[${index}]=${expectedKey}, got ${topNode.topic_keys?.[index]}`,
        );
      }
    }
    if (config.expected_lifecycle_subject) {
      assert(
        topNode.lifecycle_transition?.subject === config.expected_lifecycle_subject,
        `${fixture.id}: lifecycle_transition.subject was ${topNode.lifecycle_transition?.subject}`,
      );
    }
    if (config.expected_source_ref_type) {
      assert(
        topNode.source_refs?.some(ref => ref.type === config.expected_source_ref_type),
        `${fixture.id}: missing source_refs type ${config.expected_source_ref_type}`,
      );
    }
    if (config.expected_rejected_option || config.expected_rejected_reason) {
      assert(
        queryPack.rejected_alternatives.some(item => (
          String(item.option || '').includes(config.expected_rejected_option)
          && String(item.reason || '').includes(config.expected_rejected_reason)
        )),
        `${fixture.id}: missing expected rejected alternative`,
      );
    }
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runQueryNegativeFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const query = config.query;
  const mode = config.mode || 'why';
  const { tempRoot, tempVault } = copyFixtureVault(config);

  try {
    buildDecisionIndex(tempVault, slug);
    const negativePack = queryDecisionIndex(tempVault, slug, query, mode);
    assert(negativePack.answerable === false, `${fixture.id}: negative query should not be answerable`);
    assertQueryMetadata(negativePack, fixture);
    assert(
      Array.isArray(negativePack.missing_evidence) && negativePack.missing_evidence.length > 0,
      `${fixture.id}: negative query should include missing_evidence`,
    );
    const absentTerms = new Set((config.expected_matched_terms_absent || []).map(term => String(term).toLowerCase()));
    const matched = (negativePack.matched_terms || []).map(term => String(term).toLowerCase());
    assert(
      matched.every(term => !absentTerms.has(term)),
      `${fixture.id}: unrelated query terms should not be treated as matched evidence`,
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runQueryIndexFallbackFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const query = config.query;
  const mode = config.mode || 'why';
  const { tempRoot, tempVault } = copyFixtureVault(config);
  const decisionPath = path.join(tempVault, 'raw', 'decisions', `${slug}.json`);

  try {
    fs.mkdirSync(path.dirname(decisionPath), { recursive: true });
    fs.writeFileSync(decisionPath, '{not json', 'utf-8');
    const invalidJsonPack = queryDecisionIndex(tempVault, slug, query, mode);
    assert(
      invalidJsonPack.top_nodes?.[0]?.id === config.expected_top_node,
      `${fixture.id}: invalid JSON fallback returned ${invalidJsonPack.top_nodes?.[0]?.id}`,
    );

    fs.writeFileSync(decisionPath, JSON.stringify({
      schema_version: 'tracework.decision_replay.v1',
      project_slug: slug,
      generated_at: '2000-01-01T00:00:00+00:00',
      source: {
        kind: 'test-stale-index',
        raw_entry_count: 0,
        node_count: 0,
      },
      nodes: [],
      edges: [],
    }, null, 2), 'utf-8');
    const stalePack = queryDecisionIndex(tempVault, slug, query, mode);
    assert(
      stalePack.top_nodes?.[0]?.id === config.expected_top_node,
      `${fixture.id}: stale index fallback returned ${stalePack.top_nodes?.[0]?.id}`,
    );

    const { index: currentIndex } = buildDecisionIndex(tempVault, slug);
    const legacyBuilderIndex = structuredClone(currentIndex);
    delete legacyBuilderIndex.source.builder_version;
    legacyBuilderIndex.generated_at = '2999-01-01T00:00:00+00:00';
    legacyBuilderIndex.nodes = [{
      ...legacyBuilderIndex.nodes.find(node => node.id === config.expected_top_node),
      id: 'legacy-builder-sentinel',
    }];
    legacyBuilderIndex.edges = [];
    fs.writeFileSync(decisionPath, JSON.stringify(legacyBuilderIndex, null, 2), 'utf-8');
    const legacyBuilderPack = queryDecisionIndex(tempVault, slug, query, mode);
    assert(
      legacyBuilderPack.top_nodes?.[0]?.id === config.expected_top_node,
      `${fixture.id}: old builder index was reused instead of rebuilt`,
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runRecallRebuildFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const limit = String(config.limit || 5);
  const { tempRoot, tempVault } = copyFixtureVault(config);
  const decisionPath = path.join(tempVault, 'raw', 'decisions', `${slug}.json`);

  try {
    fs.rmSync(decisionPath, { force: true });
    const rebuiltContext = runJson('python3', [
      recallContext,
      '--vault',
      tempVault,
      '--slug',
      slug,
      '--cwd',
      repoRoot,
      '--limit',
      limit,
    ]);

    assert(Array.isArray(rebuiltContext.decision_context), `${fixture.id}: missing decision_context`);
    assert(
      rebuiltContext.decision_context.some(item => item.id === config.expected_decision_id),
      `${fixture.id}: rebuilt decision_context missing ${config.expected_decision_id}`,
    );
    assert(fs.existsSync(decisionPath), `${fixture.id}: expected rebuilt decision index at ${decisionPath}`);
    assert(
      rebuiltContext.decision_context_source && typeof rebuiltContext.decision_context_source === 'object',
      `${fixture.id}: missing decision_context_source`,
    );
    assert(
      fs.realpathSync.native(String(rebuiltContext.decision_context_source.path || ''))
        === fs.realpathSync.native(decisionPath),
      `${fixture.id}: decision_context_source.path should point at the derived decision index`,
    );
    assert(rebuiltContext.decision_context_source.rebuilt === true, `${fixture.id}: expected rebuilt=true`);
    assert(
      typeof rebuiltContext.decision_context_source.reason === 'string'
        && rebuiltContext.decision_context_source.reason,
      `${fixture.id}: missing rebuild reason`,
    );

    const freshContext = runJson('python3', [
      recallContext,
      '--vault',
      tempVault,
      '--slug',
      slug,
      '--cwd',
      repoRoot,
      '--limit',
      limit,
    ]);
    assert(
      freshContext.decision_context_source && typeof freshContext.decision_context_source === 'object',
      `${fixture.id}: fresh run missing decision_context_source`,
    );
    assert(freshContext.decision_context_source.rebuilt === false, `${fixture.id}: expected rebuilt=false on fresh run`);
    assert(
      Array.isArray(freshContext.decision_context)
        && freshContext.decision_context.some(item => item.id === config.expected_decision_id),
      `${fixture.id}: fresh decision_context missing ${config.expected_decision_id}`,
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runRoadmapThreadsFixture(fixture) {
  const config = fixture.fixture || {};
  const slug = config.project_slug;
  const { tempRoot, tempVault } = copyFixtureVault(config);

  try {
    const roadmapPack = roadmapDecisionIndex(tempVault, slug, config.limit_threads || 10);
    assert(roadmapPack.schema_version === 'tracework.decision_roadmap.v1', `${fixture.id}: bad roadmap schema`);
    assert(roadmapPack.project_slug === slug, `${fixture.id}: bad project slug`);
    assert(Array.isArray(roadmapPack.threads), `${fixture.id}: roadmap threads must be an array`);
    assert(
      roadmapPack.source?.node_count === config.expected_node_count,
      `${fixture.id}: expected node_count ${config.expected_node_count}, got ${roadmapPack.source?.node_count}`,
    );

    const validationThread = roadmapPack.threads.find(thread => thread.thread_id === config.expected_thread_id);
    assert(validationThread, `${fixture.id}: missing thread ${config.expected_thread_id}`);
    assert(validationThread.node_count === config.expected_thread_node_count, `${fixture.id}: bad validation node count`);
    assert(validationThread.confidence === config.expected_thread_confidence, `${fixture.id}: bad thread confidence`);
    assertSourceRefs(validationThread.decisions || [], fixture.id);
    for (const expectedId of config.expected_thread_decision_ids || []) {
      assert(
        validationThread.decisions?.some(node => node.id === expectedId),
        `${fixture.id}: thread missing decision ${expectedId}`,
      );
    }
    assert(
      validationThread.rejected_alternatives?.some(item => String(item.option || '').includes(config.expected_rejected_option)),
      `${fixture.id}: validation thread missing expected rejected alternative`,
    );
    assert(
      validationThread.open_questions?.some(item => String(item.question || '').includes(config.expected_open_question_text)),
      `${fixture.id}: validation thread missing expected open question`,
    );

    const retryThread = roadmapPack.threads.find(thread => thread.thread_id === config.expected_lifecycle_thread_id);
    assert(retryThread, `${fixture.id}: missing thread ${config.expected_lifecycle_thread_id}`);
    assert(
      retryThread.lifecycle_transitions?.some(item => item.subject === config.expected_lifecycle_subject),
      `${fixture.id}: retry thread missing lifecycle transition ${config.expected_lifecycle_subject}`,
    );
    assert(
      retryThread.decisions?.[0]?.source_refs?.some(ref => ref.type === config.expected_source_ref_type),
      `${fixture.id}: retry thread missing source_refs type ${config.expected_source_ref_type}`,
    );

    assert(
      roadmapPack.accumulating_risks?.some(item => String(item.risk || '').includes(config.expected_risk_text)),
      `${fixture.id}: roadmap pack missing accumulating risk`,
    );
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

function runUnsafeSlugFixture(fixture) {
  const config = fixture.fixture || {};
  const { tempRoot, tempVault } = copyFixtureVault(config);
  const unsafeSlug = config.unsafe_slug || '../outside';
  const escapedPath = path.resolve(tempVault, 'raw', 'outside.json');

  try {
    const buildResult = spawnSync('python3', [
      decisionGraph,
      'build',
      '--vault',
      tempVault,
      '--slug',
      unsafeSlug,
      '--cwd',
      repoRoot,
    ], {
      cwd: repoRoot,
      encoding: 'utf-8',
      env: pythonEnv,
    });
    assert(buildResult.status !== 0, `${fixture.id}: decision graph build should reject unsafe slug`);
    assert(
      `${buildResult.stderr}\n${buildResult.stdout}`.includes('project slug must be a filename-safe value'),
      `${fixture.id}: decision graph build should explain unsafe slug rejection`,
    );

    const queryResult = spawnSync('python3', [
      decisionGraph,
      'query',
      'why validation repair ownership',
      '--vault',
      tempVault,
      '--slug',
      unsafeSlug,
      '--cwd',
      repoRoot,
    ], {
      cwd: repoRoot,
      encoding: 'utf-8',
      env: pythonEnv,
    });
    assert(queryResult.status !== 0, `${fixture.id}: decision graph query should reject unsafe slug`);

    const recallResult = spawnSync('python3', [
      recallContext,
      '--vault',
      tempVault,
      '--slug',
      unsafeSlug,
      '--cwd',
      repoRoot,
    ], {
      cwd: repoRoot,
      encoding: 'utf-8',
      env: pythonEnv,
    });
    assert(recallResult.status !== 0, `${fixture.id}: recall should reject unsafe slug`);
    assert(!fs.existsSync(escapedPath), `${fixture.id}: unsafe slug created escaped path ${escapedPath}`);
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
      '--real-projects',
      config.expected_project,
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
    assert(signals.projects_detected.includes(config.expected_project), `${fixture.id}: project not detected`);
    assert(signals.raw_entries?.length === (config.raw_entries || []).length, `${fixture.id}: matching raw entries not loaded`);
    const entry = signals.entries[0] || {};
    assert(
      entry.report_items?.some(item => item.field === '进展' && String(item.text).includes(config.expected_progress_text)),
      `${fixture.id}: progress report field not parsed`,
    );
    assert(
      entry.evidence_boundaries?.includes(config.expected_evidence_boundary),
      `${fixture.id}: evidence boundary not parsed`,
    );
    const projectData = skeleton.by_project?.[config.expected_project] || {};
    assert(projectData.report_items?.length >= config.expected_min_report_items, `${fixture.id}: skeleton report_items missing`);
    assert(skeleton.raw_entries_by_project?.[config.expected_project]?.length === (config.raw_entries || []).length, `${fixture.id}: raw entries not exposed by project`);
    assert(skeleton.reporting_groups?.[config.expected_reporting_group]?.includes(config.expected_project), `${fixture.id}: reporting group not preserved`);
    assert(skeleton.raw_work_streams?.some(item => item.work_stream === config.expected_work_stream), `${fixture.id}: raw work stream not built`);
    assert(
      skeleton.risks?.some(item => String(item.signal).includes(config.expected_risk_text)),
      `${fixture.id}: risk field not carried into skeleton`,
    );
    if (config.expected_absent_risk_text) {
      assert(
        !skeleton.risks?.some(item => String(item.signal).includes(config.expected_absent_risk_text)),
        `${fixture.id}: no-risk placeholder leaked into skeleton risks`,
      );
    }
    assert(
      skeleton.next_actions?.some(item => String(item.signal).includes(config.expected_next_text)),
      `${fixture.id}: next action field not carried into skeleton`,
    );
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
  } else if (kind === 'query-positive') {
    runQueryPositiveFixture(fixture);
  } else if (kind === 'query-negative') {
    runQueryNegativeFixture(fixture);
  } else if (kind === 'query-index-fallback') {
    runQueryIndexFallbackFixture(fixture);
  } else if (kind === 'recall-rebuild') {
    runRecallRebuildFixture(fixture);
  } else if (kind === 'roadmap-threads') {
    runRoadmapThreadsFixture(fixture);
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
