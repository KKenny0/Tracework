import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { captureCommand, finishReportCapture } from './report-runner.mjs';

function setup(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-report-runner-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  return path.join(root, 'attempt');
}
const terminal = (result, extra = {}) => ({ type: 'result', subtype: 'success', is_error: false, result, ...extra });
const emit = (event) => `process.stdout.write(${JSON.stringify(JSON.stringify(event) + '\n')});`;
const fixture = (dir, code, timeoutMs = 5_000) => captureCommand({ command: process.execPath, args: ['-e', code], input: 'fixture', outputDir: dir, timeoutMs });

test('preserves both streams larger than a pipe buffer and records final timing', async (t) => {
  const dir = setup(t);
  const out = await fixture(dir, "process.stdout.write(JSON.stringify({type:'system',padding:'x'.repeat(100000)})+'\\n');process.stderr.write('e'.repeat(100000));" + emit(terminal('# Report\n\nOK')));
  assert.equal(out.status, 'complete');
  assert.equal(out.stage, 'after_result');
  assert.equal(fs.readFileSync(path.join(dir, 'stderr.log')).length, 100_000);
  assert.ok(fs.statSync(path.join(dir, 'stdout.ndjson')).size > 100_000);
  assert.ok(out.result_ms >= out.first_event_ms);
});

test('timeout retains partial answer and stderr and remains unresolved', async (t) => {
  const dir = setup(t);
  const delta = { type: 'stream_event', event: { type: 'content_block_delta', delta: { type: 'text_delta', text: '部分正文' } } };
  const out = await fixture(dir, emit(delta) + "process.stderr.write('diagnostic-before-timeout');setInterval(()=>{},1000);", 1_200);
  assert.equal(out.status, 'timeout');
  assert.equal(out.stage, 'during_generation');
  assert.equal(fs.readFileSync(path.join(dir, 'partial-message.txt'), 'utf8'), '部分正文');
  assert.equal(fs.readFileSync(path.join(dir, 'stderr.log'), 'utf8'), 'diagnostic-before-timeout');
  assert.ok(fs.readFileSync(path.join(dir, 'stdout.ndjson'), 'utf8').includes('部分正文'));
  assert.equal(out.result, null);
});

test('thinking before answer text is visible as generation progress, not a silent wait', async (t) => {
  const dir = setup(t);
  const event = { type: 'stream_event', event: { type: 'content_block_delta', delta: { type: 'thinking_delta', thinking: 'fixture' } } };
  const out = await fixture(dir, emit(event) + 'setInterval(()=>{},1000);', 1_200);
  assert.equal(out.status, 'timeout');
  assert.equal(out.stage, 'during_generation');
  assert.equal(out.thinking_chunks, 1);
  assert.ok(out.first_thinking_ms !== null);
  assert.equal(out.first_content_ms, null);
  assert.equal(fs.readFileSync(path.join(dir, 'partial-message.txt'), 'utf8'), '');
});

test('a result followed by a stuck client is a timeout after_result, not success', async (t) => {
  const dir = setup(t);
  const out = await fixture(dir, emit(terminal('# Complete text')) + 'setInterval(()=>{},1000);', 1_200);
  assert.equal(out.status, 'timeout');
  assert.equal(out.stage, 'after_result');
  assert.equal(JSON.parse(fs.readFileSync(path.join(dir, 'result-envelope.json'))).result, '# Complete text');
  assert.equal(finishReportCapture(out, dir).status, 'timeout');
  assert.equal(fs.existsSync(path.join(dir, 'outputs/report.md')), false);
});

test('recognizes the observed 403 shape even when result subtype says success', async (t) => {
  const dir = setup(t);
  const event = terminal('Access denied', { is_error: true, terminal_reason: 'api_error', api_error_status: 403 });
  const out = await fixture(dir, emit(event) + 'process.exitCode=1;');
  assert.equal(out.status, 'api_error');
  assert.equal(out.api_error_status, 403);
  assert.equal(finishReportCapture(out, dir).status, 'api_error');
  assert.equal(fs.existsSync(path.join(dir, 'outputs/report.md')), false);
});

for (const [name, code, status] of [
  ['malformed stream', "process.stdout.write('not-json\\n');", 'protocol_error'],
  ['missing final result', emit({ type: 'assistant', message: { content: [{ type: 'text', text: 'unfinished' }] } }), 'protocol_error'],
  ['non-API process error', "process.stderr.write('client failure');process.exitCode=2;", 'process_error'],
  ['non-API terminal failure after an earlier API error', emit({ type: 'assistant', is_api_error_message: true }) + emit(terminal('', { is_error: true, terminal_reason: 'max_turns' })), 'process_error'],
  ['API terminal marker despite a conflicting success flag', emit(terminal('Access denied', { terminal_reason: 'api_error', api_error_status: 403 })), 'api_error'],
]) {
  test(`classifies ${name} without calling it a valid report`, async (t) => {
    const out = await fixture(setup(t), code);
    assert.equal(out.status, status);
  });
}

test('missing executable produces launch_error with persisted diagnostics', async (t) => {
  const dir = setup(t);
  const out = await captureCommand({ command: path.join(dir, 'missing-executable'), outputDir: dir, timeoutMs: 2_000 });
  assert.equal(out.status, 'launch_error');
  assert.equal(JSON.parse(fs.readFileSync(path.join(dir, 'outcome.json'))).status, 'launch_error');
});

test('UTF-8 split across chunks is preserved and malformed UTF-8 fails protocol', async (t) => {
  const dir = setup(t);
  const body = '# 月报\n\n测试通过。';
  const line = Buffer.from(JSON.stringify(terminal(body)) + '\n');
  const split = line.indexOf(Buffer.from('月')) + 1;
  const code = `const b=Buffer.from(${JSON.stringify([...line])});process.stdout.write(b.subarray(0,${split}));setTimeout(()=>process.stdout.write(b.subarray(${split})),10);`;
  const out = await fixture(dir, code);
  assert.equal(out.status, 'complete');
  assert.equal(out.result.result, body);
  const bad = await fixture(path.join(path.dirname(dir), 'bad-encoding'), "process.stdout.write(Buffer.from([123,255,125,10]));");
  assert.equal(bad.status, 'protocol_error');
  assert.deepEqual(fs.readFileSync(path.join(path.dirname(dir), 'bad-encoding/stdout.ndjson')), Buffer.from([123,255,125,10]));
  const masked = await fixture(path.join(path.dirname(dir), 'masked-encoding'), "process.stdout.write(Buffer.from([160,10]));" + emit(terminal('# Report')));
  assert.equal(masked.status, 'protocol_error');
});

test('JSON wrapping Markdown is rejected without extracting a passing report', async (t) => {
  const dir = setup(t);
  const text = JSON.stringify({ markdown: '# Report\n\nOK' });
  const capture = await fixture(dir, emit(terminal(text)));
  const out = finishReportCapture(capture, dir);
  assert.equal(out.transport_status, 'complete');
  assert.equal(out.status, 'format_error');
  assert.equal(out.semantic_status, 'not_checked');
  assert.equal(fs.readFileSync(path.join(dir, 'outputs/report.md'), 'utf8'), text);
});

test('valid Markdown passes format only; independent expected dates still reject mismatches', async (t) => {
  const dir = setup(t);
  const text = '# Report\n\n- Raw-backed days: 4\n';
  const capture = await fixture(dir, emit(terminal(text)));
  const out = finishReportCapture(capture, dir, 4);
  assert.equal(out.status, 'complete');
  assert.equal(out.semantic_status, 'not_checked');
  const other = path.join(path.dirname(dir), 'bad-count');
  const bad = finishReportCapture(await fixture(other, emit(terminal(text))), other, 5);
  assert.equal(bad.status, 'coverage_error');
  assert.equal(JSON.parse(fs.readFileSync(path.join(other, 'mechanical.json'))).issues[0].code, 'raw_day_count_mismatch');
});

test('refuses to overwrite an existing attempt, preserving earlier output', async (t) => {
  const dir = setup(t);
  await fixture(dir, emit(terminal('# Original')));
  const before = fs.readFileSync(path.join(dir, 'stdout.ndjson'));
  await assert.rejects(fixture(dir, emit(terminal('# Replacement'))), { code: 'EEXIST' });
  assert.deepEqual(fs.readFileSync(path.join(dir, 'stdout.ndjson')), before);
});
