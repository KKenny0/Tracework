import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { checkReportOutput } from './report-output-checks.mjs';

const save = (dir, name, value) => fs.writeFileSync(path.join(dir, name), JSON.stringify(value, null, 2) + '\n');

// One immutable attempt. Raw streams are saved as they arrive, including on timeout.
// This checks transport/protocol/format only; it cannot certify factual correctness.
export async function captureCommand({ command, args = [], input = '', cwd, outputDir, timeoutMs = 300_000 }) {
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new TypeError('timeoutMs must be positive');
  const dir = path.resolve(outputDir);
  fs.mkdirSync(path.dirname(dir), { recursive: true });
  fs.mkdirSync(dir); // Refuse to replace an earlier attempt, even after failure.
  fs.writeFileSync(path.join(dir, 'prompt.txt'), input);
  const stdout = fs.openSync(path.join(dir, 'stdout.ndjson'), 'wx');
  const stderr = fs.openSync(path.join(dir, 'stderr.log'), 'wx');
  const progress = fs.openSync(path.join(dir, 'progress.ndjson'), 'wx');
  const partial = fs.openSync(path.join(dir, 'partial-message.txt'), 'wx');
  const started = performance.now();
  const elapsed = () => Math.round(performance.now() - started);
  let pending = Buffer.alloc(0), result = null, apiErrors = 0, protocolErrors = 0;
  let stdoutBytes = 0, stderrBytes = 0, events = 0, sawDeltas = false;
  let firstEvent = null, firstContent = null, lastContent = null, resultAt = null;
  let firstThinking = null, lastThinking = null, thinkingChunks = 0;
  let lastEvent = null, lastSubtype = null, timedOut = false, launchError = null;
  let finished = false, child, deadline, cleanupDeadline;
  const log = (entry) => fs.writeSync(progress, JSON.stringify({ elapsed_ms: elapsed(), ...entry }) + '\n');
  const content = (text) => {
    if (!text) return;
    firstContent ??= elapsed();
    lastContent = elapsed();
    fs.writeSync(partial, text);
  };
  const consume = (bytes) => {
    if (!bytes.toString('utf8').trim()) return;
    let event;
    try {
      event = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
      if (!event || typeof event.type !== 'string') throw new Error('Missing event type');
    } catch {
      protocolErrors++;
      log({ type: 'protocol_error', bytes: bytes.length });
      return;
    }
    events++;
    firstEvent ??= elapsed();
    lastEvent = event.type;
    lastSubtype = event.subtype ?? event.event?.type ?? null;
    log({ type: event.type, subtype: lastSubtype, delta_type: event.event?.delta?.type ?? null });
    if (event.type === 'stream_event' && event.event?.delta?.type === 'thinking_delta') {
      firstThinking ??= elapsed();
      lastThinking = elapsed();
      thinkingChunks++;
    }
    if (event.is_api_error_message || event.api_error_status || event.terminal_reason === 'api_error') apiErrors++;
    if (event.type === 'stream_event' && event.event?.delta?.type === 'text_delta') {
      sawDeltas = true;
      content(event.event.delta.text);
    }
    if (event.type === 'assistant' && !event.is_api_error_message && !sawDeltas) {
      for (const item of event.message?.content ?? []) if (item.type === 'text') content(item.text);
    }
    if (event.type === 'result') {
      result = event;
      resultAt = elapsed();
      save(dir, 'result-envelope.json', event);
    }
  };
  return await new Promise((resolve) => {
    const finish = (code, signal, forcedCleanup = false) => {
      if (finished) return;
      finished = true;
      clearTimeout(deadline);
      clearTimeout(cleanupDeadline);
      if (pending.length) consume(pending);
      let status;
      if (timedOut) status = 'timeout';
      else if (launchError) status = 'launch_error';
      else if (result?.terminal_reason === 'api_error' || result?.api_error_status || (result?.is_error && !result.terminal_reason && apiErrors)) status = 'api_error';
      else if (!result && apiErrors) status = 'api_error';
      else if (code !== 0 || result?.is_error) status = 'process_error';
      else if (protocolErrors || !result || typeof result.result !== 'string') status = 'protocol_error';
      else status = 'complete';
      const stage = resultAt !== null ? 'after_result' : firstContent !== null || firstThinking !== null ? 'during_generation' : firstEvent !== null ? 'before_content' : 'before_first_event';
      const outcome = {
        status, stage, exit_code: code, signal, elapsed_ms: elapsed(), timeout_ms: timeoutMs,
        stdout_bytes: stdoutBytes, stderr_bytes: stderrBytes, events,
        first_event_ms: firstEvent, first_content_ms: firstContent, last_content_ms: lastContent,
        first_thinking_ms: firstThinking, last_thinking_ms: lastThinking, thinking_chunks: thinkingChunks,
        result_ms: resultAt, last_event: lastEvent, last_subtype: lastSubtype,
        api_error_events: apiErrors, api_error_status: result?.api_error_status ?? null,
        protocol_errors: protocolErrors, launch_error: launchError, forced_cleanup: forcedCleanup,
      };
      log({ type: 'capture_complete', status, stage });
      for (const fd of [stdout, stderr, progress, partial]) fs.closeSync(fd);
      save(dir, 'outcome.json', outcome);
      resolve({ ...outcome, result });
    };
    try {
      child = spawn(command, args, { cwd, shell: false, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    } catch (error) {
      launchError = error.code ?? error.message;
      finish(null, null);
      return;
    }
    child.on('error', (error) => { launchError = error.code ?? error.message; });
    child.stdout.on('data', (data) => {
      if (finished) return;
      stdoutBytes += data.length;
      fs.writeSync(stdout, data);
      pending = Buffer.concat([pending, data]);
      let index;
      while ((index = pending.indexOf(10)) !== -1) {
        consume(pending.subarray(0, index));
        pending = pending.subarray(index + 1);
      }
    });
    child.stderr.on('data', (data) => {
      if (finished) return;
      stderrBytes += data.length;
      fs.writeSync(stderr, data);
    });
    child.stdin.on('error', (error) => { if (!finished) log({ type: 'stdin_error', code: error.code }); });
    child.on('close', (code, signal) => finish(code, signal));
    deadline = setTimeout(() => {
      timedOut = true;
      log({ type: 'deadline' });
      child.kill('SIGKILL'); // Only the child this attempt created.
      cleanupDeadline = setTimeout(() => {
        child.stdout.destroy();
        child.stderr.destroy();
        finish(child.exitCode, child.signalCode, true);
      }, 1_000);
    }, timeoutMs);
    child.stdin.end(input);
  });
}

export function claudeReportArgs({ model, effort = 'medium', systemPrompt }) {
  return ['-p', '--safe-mode', '--model', model, '--effort', effort, '--tools', '',
    '--disable-slash-commands', '--strict-mcp-config', '--no-session-persistence',
    '--output-format', 'stream-json', '--verbose', '--include-partial-messages',
    '--system-prompt', systemPrompt];
}

export function finishReportCapture(capture, outputDir, expectedRawDays = null) {
  const { result, ...outcome } = capture;
  outcome.transport_status = capture.status;
  outcome.semantic_status = 'not_checked';
  if (capture.status === 'complete') {
    const report = result.result;
    fs.mkdirSync(path.join(outputDir, 'outputs'));
    fs.writeFileSync(path.join(outputDir, 'outputs/report.md'), report);
    const issues = checkReportOutput(report, { expectedRawDays });
    const mechanical = { issues, mechanical_pass: issues.length === 0, semantic_status: 'not_checked' };
    save(outputDir, 'mechanical.json', mechanical);
    outcome.mechanical_pass = mechanical.mechanical_pass;
    if (issues.length) outcome.status = issues.some(({ code }) => ['json_instead_of_markdown', 'empty_report'].includes(code)) ? 'format_error' : 'coverage_error';
    save(outputDir, 'timing.json', { total_duration_seconds: capture.elapsed_ms / 1000, usage: result.usage ?? null, model_usage: result.modelUsage ?? null, cost_usd: result.total_cost_usd ?? null });
  }
  save(outputDir, 'outcome.json', outcome);
  return outcome;
}

export async function runReportEvaluation({ cli, model, effort = 'medium', prompt, systemPrompt, outputDir, cwd, timeoutMs, expectedRawDays = null }) {
  const capture = await captureCommand({ command: cli, args: claudeReportArgs({ model, effort, systemPrompt }), input: prompt, outputDir, cwd, timeoutMs });
  save(outputDir, 'invocation.json', { model, effort, timeout_ms: timeoutMs ?? 300_000, output_format: 'stream-json', system_prompt: systemPrompt });
  return finishReportCapture(capture, outputDir, expectedRawDays);
}
