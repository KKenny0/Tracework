import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Mechanical checks only. An empty issue list is not evidence of factual accuracy.
export function checkReportOutput(text, { expectedRawDays = null, coverage = null } = {}) {
  if (coverage !== null) {
    if (!Array.isArray(coverage.raw_days) || !Number.isInteger(coverage.raw_entry_count) || coverage.raw_entry_count < 0
      || !(coverage.empty_days === null || Number.isInteger(coverage.empty_days) && coverage.empty_days >= 0)) {
      throw new TypeError('coverage requires raw_days, raw_entry_count and empty_days (null when unknown)');
    }
    expectedRawDays = new Set(coverage.raw_days).size;
  }
  if (typeof text !== 'string') throw new TypeError('Report must be text');
  if (expectedRawDays !== null && (!Number.isInteger(expectedRawDays) || expectedRawDays < 0)) {
    throw new TypeError('expectedRawDays must be a nonnegative integer or null');
  }
  const issues = [];
  const body = text.trim();
  if (!body) return [{ code: 'empty_report', line: 1, evidence: '' }];
  const unfenced = body.replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/i, '$1');
  let value;
  try {
    value = JSON.parse(unfenced);
  } catch {
    // Markdown is not JSON; this check says nothing about its other properties.
  }
  if (value !== null && typeof value === 'object') {
    issues.push({ code: 'json_instead_of_markdown', line: 1, evidence: body });
  }
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const normalized = line.replace(/[*`]/g, '');
    if (coverage) {
      const entries = normalized.match(/^\s*(?:[-+]\s*)?(?:Raw entries|原始记录条数|Raw 覆盖)\s*[:：]\s*(\d+)(?=\s|条|$)/i);
      if (entries && Number(entries[1]) !== coverage.raw_entry_count) {
        issues.push({ code: 'raw_entry_count_mismatch', line: index + 1, evidence: line, expected: coverage.raw_entry_count, actual: Number(entries[1]) });
      }
      const empty = normalized.match(/^\s*(?:[-+]\s*)?(?:Empty days|空日期数)\s*[:：]\s*(\d+)(?=\s|天|$)/i);
      if (empty && Number(empty[1]) !== coverage.empty_days) {
        issues.push({ code: coverage.empty_days === null ? 'unsupported_empty_day_count' : 'empty_day_count_mismatch', line: index + 1, evidence: line, expected: coverage.empty_days, actual: Number(empty[1]) });
      }
    }
    const match = normalized.match(/^\s*(?:[-+]\s*)?(?:Raw-backed days|原始记录覆盖天数)\s*[:：]\s*(\d+)\b(.*)$/i);
    if (!match) continue;
    const count = Number(match[1]);
    if (expectedRawDays !== null && count !== expectedRawDays) {
      issues.push({ code: 'raw_day_count_mismatch', line: index + 1, evidence: line, expected: expectedRawDays, actual: count });
    }
    // Only explicit, complete enumerations can be compared without interpreting prose.
    const enumeration = match[2].match(/^\s*[（(]\s*((?:(?:\d{4}-)?\d{2}-\d{2})(?:\s*[,，、]\s*(?:\d{4}-)?\d{2}-\d{2})*)\s*[）)]\s*$/);
    if (!enumeration) continue;
    const dates = enumeration[1].split(/\s*[,，、]\s*/);
    // Mixed year-qualified and short dates need context to disambiguate.
    if (new Set(dates.map(date => date.length)).size !== 1) continue;
    const uniqueCount = new Set(dates).size;
    if (count !== uniqueCount) {
      issues.push({ code: 'enumerated_day_count_mismatch', line: index + 1, evidence: line, expected: uniqueCount, actual: count });
    }
  }
  return issues;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [reportPath, expected] = process.argv.slice(2);
  if (!reportPath) throw new Error('Usage: node benchmarks/report-output-checks.mjs REPORT.md [EXPECTED_RAW_DAYS]');
  const issues = checkReportOutput(fs.readFileSync(reportPath, 'utf8'), {
    expectedRawDays: expected === undefined ? null : Number(expected),
  });
  console.log(JSON.stringify({ issues, mechanical_pass: issues.length === 0, semantic_status: 'not_checked' }, null, 2));
  process.exitCode = issues.length ? 1 : 0;
}
