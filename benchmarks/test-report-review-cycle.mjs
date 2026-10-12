import assert from 'node:assert/strict';
import test from 'node:test';
import { checkReportOutput } from './report-output-checks.mjs';
import { validateReportReview, runReviewedReport, sourceCoverage, reviewReport } from './report-review-cycle.mjs';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

test('source counts distinguish records from days and unknown empty days from zero', () => {
  const report = '# 月报\n\n- Raw-backed days: 2\n- Raw 覆盖：2条有效记录\n- Empty days: 0';
  const issues = checkReportOutput(report, { coverage: {
    raw_days: ['2026-11-03', '2026-11-18'], raw_entry_count: 3, empty_days: null,
  } });
  assert.deepEqual(issues.map(i => i.code), ['raw_entry_count_mismatch', 'unsupported_empty_day_count']);
});

test('a reviewer cannot pass by omitting a later contradictory section', () => {
  const report = '# 月报\n\n测量日期未定。\n\n## 需要决策\n\n必须先确定测量日期。';
  const sources = [{ id: 'S1', date: '2026-11-01', text: '负责人确认收集数据，日期未定。' }];
  const review = { blocks: [{ id: 'B1', verdict: 'non_claim', quote: '# 月报', reason: '标题', evidence: [] }], requirements: [] };
  assert.equal(validateReportReview({ report, sources, requirements: [], review }).status, 'invalid_review');
});

const sources = [{ id: 'S1', date: '2026-11-01', text: '版本已部署，生产延迟未测量。' }];
test('exact quotations are bound from source IDs, not copied or paraphrased by the model', () => {
  const first = { id: 'B1', verdict: 'supported', source_ids: ['S1'], reason: '部署已记录' };
  const last = { id: 'B2', verdict: 'unsupported', source_ids: ['S1'], reason: '未测量不能断言改善' };
  const result = validateReportReview({ report: '已部署。\n\n延迟改善。', sources, requirements: [], review: { blocks: [first, last], requirements: [] } });
  assert.equal(result.status, 'fail');
  assert.equal(result.anchored_review.blocks[1].quote, '延迟改善。');
  assert.equal(result.anchored_review.blocks[1].evidence[0].quote, '版本已部署，生产延迟未测量。');
});

const judgment = (_quote, verdict) => JSON.stringify({ blocks: [{ id: 'B1', verdict, reason: '部署不等于生产延迟改善', source_ids: ['S1'] }], requirements: [] });

test('a single JSON review fence is framing, but prose around it is not silently removed', async () => {
  const report = '版本已部署，生产延迟未测量。';
  const body = '```json\n' + judgment(report, 'supported') + '\n```';
  const check = text => reviewReport({ report, sources, invoke: async () => ({ status: 'complete', text }), outputDir: 'unused' });
  assert.equal((await check(body)).status, 'pass');
  assert.equal((await check('Explanation\n' + body)).status, 'invalid_review');
});

test('one repair is reviewed afresh while the initial failure stays archived', async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-review-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const replies = ['生产延迟已改善。', judgment('生产延迟已改善。', 'unsupported'), '版本已部署，生产延迟未测量。', judgment('版本已部署，生产延迟未测量。', 'supported')];
  const outputDir = path.join(root, 'attempt');
  const result = await runReviewedReport({ sources, requirements: [], prompt: '写月报', outputDir,
    invoke: async () => ({ status: 'complete', text: replies.shift() }) });
  assert.equal(result.status, 'review_pass_unconfirmed');
  assert.equal(result.first_attempt_review_pass, false);
  assert.equal(result.repair_attempted, true);
  assert.equal(result.eligible, false);
  assert.equal(fs.readFileSync(path.join(outputDir, 'initial-report.md'), 'utf8'), '生产延迟已改善。');
  assert.equal(fs.readFileSync(path.join(outputDir, 'repair-report.md'), 'utf8'), '版本已部署，生产延迟未测量。');
  await assert.rejects(runReviewedReport({ sources, requirements: [], prompt: '写月报', outputDir, invoke: async () => { throw Error('must not run'); } }), { code: 'EEXIST' });
});

test('coverage uses dated source records, not context or invented empty dates', () => {
  const records = [{ id: 'CTX', date: null, text: '两个独立项目' }, ...sources,
    { id: 'S2', date: '2026-11-01', text: '文档完成。' }, { id: 'S3', date: '2026-11-03', text: '仍已部署。' }];
  assert.deepEqual(sourceCoverage(records), { raw_days: ['2026-11-01', '2026-11-03'], raw_entry_count: 3, empty_days: null });
  assert.throws(() => sourceCoverage([{ ...sources[0], date: '2026-02-30' }]), TypeError);
  assert.throws(() => sourceCoverage([sources[0], sources[0]]), TypeError);
});

test('later unsupported claims, uncertain readings and fabricated citations cannot pass', () => {
  const report = '版本已部署，生产延迟未测量。\n\n生产延迟已改善。';
  const first = JSON.parse(judgment('版本已部署，生产延迟未测量。', 'supported')).blocks[0];
  const last = { ...first, id: 'B2', quote: '生产延迟已改善。', verdict: 'unsupported' };
  const check = review => validateReportReview({ report, sources, requirements: [], review });
  assert.equal(check({ verdict: 'pass', blocks: [first, last], requirements: [] }).status, 'fail');
  assert.equal(check({ blocks: [first, { ...last, verdict: 'uncertain' }], requirements: [] }).status, 'uncertain');
  assert.equal(check({ blocks: [first, { ...last, source_ids: ['invented-source'] }], requirements: [] }).status, 'invalid_review');
});

for (const [name, tail, expected] of [
  ['residual error after the only repair', [judgment('生产延迟已改善。', 'unsupported'), '生产延迟已改善。', judgment('生产延迟已改善。', 'unsupported')], 'rejected'],
  ['malformed review', ['{"blocks":'], 'invalid_review'],
  ['review service failure', [null], 'review_error'],
]) {
  test(`${name} stays unresolved instead of retrying until green`, async t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-review-'));
    t.after(() => fs.rmSync(root, { recursive: true, force: true }));
    const replies = ['生产延迟已改善。', ...tail];
    const result = await runReviewedReport({ sources, prompt: '月报', outputDir: path.join(root, 'attempt'), invoke: async () => {
      const text = replies.shift();
      if (text === undefined) throw Error('No further requests authorized');
      return text === null ? { status: 'api_error' } : { status: 'complete', text };
    } });
    assert.equal(result.status, expected);
    assert.equal(result.eligible, false);
    assert.equal(result.first_attempt_review_pass, false);
  });
}

test('missing material facts fail and requirement references cannot name nonexistent blocks', () => {
  const report = '版本已部署，生产延迟未测量。';
  const review = JSON.parse(judgment(report, 'supported'));
  const check = row => validateReportReview({ report, sources, requirements: ['生产延迟未测量'], review: { ...review, requirements: [row] } });
  assert.equal(check({ id: 'Q1', verdict: 'missing', block_ids: [], reason: '缺少所需事实' }).status, 'fail');
  assert.equal(check({ id: 'Q1', verdict: 'covered', block_ids: ['B2'], reason: '引用不存在段落' }).status, 'invalid_review');
  assert.equal(check({ id: 'B1', verdict: 'covered', block_ids: ['B1'], reason: '错误的要求编号' }).status, 'invalid_review');
});

test('invalid source configuration rejects before creating a model attempt', async t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-review-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const outputDir = path.join(root, 'attempt');
  await assert.rejects(runReviewedReport({ sources: [], prompt: '月报', outputDir, invoke: async () => { throw Error('must not run'); } }), TypeError);
  assert.equal(fs.existsSync(outputDir), false);
});
