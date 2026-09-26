#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { skillCopies, officialSkills } from './skill-copies.mjs';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'tracework-copies-'));
const run = command => spawnSync(process.execPath, [`cli/scripts/${command}.mjs`], { cwd: temp, encoding: 'utf8' });
try {
  for (const directory of ['skills', 'references', 'scripts', 'assets', 'hooks', '.codex-plugin', '.claude-plugin', '.agents/plugins', 'cli/scripts', 'cli/src', 'cli/dist']) {
    fs.cpSync(path.join(repo, directory), path.join(temp, directory), {
      recursive: true,
      filter: file => !['evals', '__pycache__', '.DS_Store'].includes(path.basename(file)) && !path.basename(file).endsWith('-workspace'),
    });
  }
  for (const file of ['skill-catalog.json', 'package.json']) {
    fs.copyFileSync(path.join(repo, 'cli', file), path.join(temp, 'cli', file));
  }
  assert.equal(spawnSync(process.execPath, ['cli/dist/utils.js'], { cwd: temp }).status, 0);
  assert.deepEqual(fs.readdirSync(path.join(repo, 'skills')).filter(name => fs.existsSync(path.join(repo, 'skills', name, 'SKILL.md'))).sort(), [...officialSkills].sort());
  const { listSkills } = await import('../dist/utils.js');
  assert.deepEqual(listSkills(), officialSkills);
  fs.symlinkSync(path.join(repo, 'cli/node_modules'), path.join(temp, 'cli/node_modules'), 'dir');
  // Simulate stale installed bundles: regeneration must remove retired skills.
  for (const root of ['cli/skills', 'plugins/tracework/skills']) {
    for (const skill of ['query', 'recall', 'roadmap']) {
      fs.mkdirSync(path.join(temp, root, skill), { recursive: true });
      fs.writeFileSync(path.join(temp, root, skill, 'SKILL.md'), 'retired');
    }
  }
  assert.equal(run('copy-skills').status, 0);
  assert.equal(run('check-skills').status, 0);
  for (const root of ['cli/skills', 'plugins/tracework/skills']) {
    assert.deepEqual(fs.readdirSync(path.join(temp, root)).sort(),
      [...officialSkills].sort());
  }
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
  const generated = () => Object.fromEntries(['plugins/tracework', 'cli/skills', 'cli/assets'].flatMap(root =>
    fs.readdirSync(path.join(temp, root), { recursive: true })
      .filter(file => fs.statSync(path.join(temp, root, file)).isFile())
      .map(file => [`${root}/${file}`, fs.readFileSync(path.join(temp, root, file))])));
  const first = generated();
  assert.equal(run('copy-skills').status, 0);
  assert.deepEqual(generated(), first);
  const catalogPath = path.join(temp, 'cli/skill-catalog.json');
  const setCatalog = value => fs.writeFileSync(catalogPath, JSON.stringify(value));
  const assertRejectedWithoutWrites = () => {
    const before = generated();
    const local = new Map(skillCopies.map(([, target]) => [target, fs.readFileSync(path.join(temp, target))]));
    assert.notEqual(run('copy-skills').status, 0);
    assert.notEqual(run('check-skills').status, 0);
    assert.deepEqual(generated(), before);
    for (const [target, content] of local) assert.deepEqual(fs.readFileSync(path.join(temp, target)), content);
  };
  for (const invalid of [[], {}, ['../capture'], ['capture', 'capture'], [42]]) {
    setCatalog(invalid);
    assertRejectedWithoutWrites();
    assert.notEqual(spawnSync(process.execPath, ['cli/dist/utils.js'], { cwd: temp }).status, 0);
  }
  setCatalog(officialSkills);
  const missingSkill = path.join(temp, 'skills/capture/SKILL.md');
  fs.renameSync(missingSkill, `${missingSkill}.bak`);
  assertRejectedWithoutWrites();
  fs.renameSync(`${missingSkill}.bak`, missingSkill);
  const missingResource = path.join(temp, 'references/tracework-storage-convention.md');
  fs.renameSync(missingResource, `${missingResource}.bak`);
  assertRejectedWithoutWrites();
  fs.renameSync(`${missingResource}.bak`, missingResource);
  // A source skill cannot silently become an undeclared published skill.
  setCatalog(officialSkills.filter(skill => skill !== 'cold-start-interview'));
  assertRejectedWithoutWrites();
  fs.rmSync(path.join(temp, 'skills/cold-start-interview'), { recursive: true });
  assert.equal(run('copy-skills').status, 0);
  assert.equal(run('check-skills').status, 0);
  for (const root of ['cli/skills', 'plugins/tracework/skills']) {
    assert(!fs.existsSync(path.join(temp, root, 'cold-start-interview')));
  }
  // Explicit subset dependencies must refer to declared skills.
  setCatalog(officialSkills.filter(skill => !['cold-start-interview', 'monthly'].includes(skill)));
  fs.rmSync(path.join(temp, 'skills/monthly'), { recursive: true });
  const beforeSubsetFailure = generated();
  assert.notEqual(run('copy-skills').status, 0);
  assert.deepEqual(generated(), beforeSubsetFailure);
  console.log('Catalog validation, removal, CLI order, canonical propagation, pure check and idempotence passed.');
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}
