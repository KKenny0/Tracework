#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { skillCopies } from './skill-copies.mjs';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-copies-'));
const run = command => spawnSync(process.execPath, [`cli/scripts/${command}.mjs`], { cwd: temp, encoding: 'utf8' });
try {
  for (const directory of ['skills', 'references', 'scripts', 'assets', 'hooks', '.codex-plugin', '.claude-plugin', '.agents/plugins', 'cli/scripts', 'cli/src']) {
    fs.cpSync(path.join(repo, directory), path.join(temp, directory), {
      recursive: true,
      filter: file => !['evals', '__pycache__', '.DS_Store'].includes(path.basename(file)) && !path.basename(file).endsWith('-workspace'),
    });
  }
  fs.symlinkSync(path.join(repo, 'cli/node_modules'), path.join(temp, 'cli/node_modules'), 'dir');
  assert.equal(run('copy-skills').status, 0);
  assert.equal(run('check-skills').status, 0);
  // Change only canonical inputs: pure check must fail without repairing copies.
  const prior = new Map(skillCopies.map(([, target]) => [target, fs.readFileSync(path.join(temp, target))]));
  for (const source of new Set(skillCopies.map(([source]) => source))) {
    fs.appendFileSync(path.join(temp, source), '\n# canonical mutation probe\n');
  }
  assert.notEqual(run('check-skills').status, 0);
  for (const [target, before] of prior) assert.deepEqual(fs.readFileSync(path.join(temp, target)), before);
  assert.equal(run('copy-skills').status, 0);
  assert.equal(run('check-skills').status, 0);
  for (const [source, target] of skillCopies) {
    assert.deepEqual(fs.readFileSync(path.join(temp, source)), fs.readFileSync(path.join(temp, target)));
    if (target.startsWith('skills/')) {
      assert.deepEqual(fs.readFileSync(path.join(temp, source)), fs.readFileSync(path.join(temp, 'plugins/tracework', target)));
    }
  }
  const generated = () => Object.fromEntries(fs.readdirSync(path.join(temp, 'plugins/tracework'), { recursive: true })
    .filter(file => fs.statSync(path.join(temp, 'plugins/tracework', file)).isFile())
    .map(file => [file, fs.readFileSync(path.join(temp, 'plugins/tracework', file))]));
  const first = generated();
  assert.equal(run('copy-skills').status, 0);
  assert.deepEqual(generated(), first);
  console.log('Canonical mutation, pure check, propagation and idempotence passed.');
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
