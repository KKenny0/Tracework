#!/usr/bin/env node
import fs from 'node:fs';
import { skillCopies, officialSkills, validateSkillSources } from './skill-copies.mjs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const cliRoot = path.resolve(scriptDir, '..');
const repoRoot = path.resolve(cliRoot, '..');
const sourceSkillsDir = path.join(repoRoot, 'skills');
const bundledSkillsDir = path.join(cliRoot, 'skills');
const sourceAssetsDir = path.join(repoRoot, 'assets');
const sourceHooksDir = path.join(repoRoot, 'hooks');
const bundledAssetsDir = path.join(cliRoot, 'assets');
const sitePublicDir = path.join(repoRoot, 'site', 'public');
const sourceCodexPluginDir = path.join(repoRoot, '.codex-plugin');
const sourceClaudePluginDir = path.join(repoRoot, '.claude-plugin');
const codexPluginBundleDir = path.join(repoRoot, 'plugins', 'tracework');
const bundledCodexPluginDir = path.join(codexPluginBundleDir, '.codex-plugin');
const bundledClaudePluginDir = path.join(codexPluginBundleDir, '.claude-plugin');
const bundledCodexSkillsDir = path.join(codexPluginBundleDir, 'skills');
const bundledCodexAssetsDir = path.join(codexPluginBundleDir, 'assets');
const bundledCodexHooksDir = path.join(codexPluginBundleDir, 'hooks');



const officialAssets = [
  'logo.png',
  'mark.svg',
  'tracework-three-actions.png',
];

const siteBrandAssets = [
  'logo.png',
  'mark.svg',
];

function shouldSkip(name) {
  return name === 'evals' || name.endsWith('-workspace') || name === '__pycache__';
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (entry.isDirectory() && shouldSkip(entry.name)) continue;
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

validateSkillSources(repoRoot);
for (const source of [
  ...officialAssets.map(asset => path.join(sourceAssetsDir, asset)),
  path.join(sourceCodexPluginDir, 'plugin.json'),
  path.join(sourceClaudePluginDir, 'plugin.json'),
  path.join(sourceHooksDir, 'hooks.json'),
]) {
  if (!fs.statSync(source).isFile()) throw new Error(`Copy source is not a file: ${source}`);
}

for (const [source, target] of skillCopies) {
  copyFile(path.join(repoRoot, source), path.join(repoRoot, target));
}

fs.rmSync(bundledSkillsDir, { recursive: true, force: true });
fs.mkdirSync(bundledSkillsDir, { recursive: true });

for (const skill of officialSkills) {
  const skillPath = path.join(sourceSkillsDir, skill);
  copyDir(skillPath, path.join(bundledSkillsDir, skill));
}

fs.rmSync(bundledAssetsDir, { recursive: true, force: true });
if (fs.existsSync(sourceAssetsDir)) {
  for (const asset of officialAssets) {
    copyFile(path.join(sourceAssetsDir, asset), path.join(bundledAssetsDir, asset));
  }
}

fs.rmSync(codexPluginBundleDir, { recursive: true, force: true });
fs.mkdirSync(bundledCodexPluginDir, { recursive: true });
fs.mkdirSync(bundledClaudePluginDir, { recursive: true });
fs.mkdirSync(bundledCodexSkillsDir, { recursive: true });
copyDir(sourceCodexPluginDir, bundledCodexPluginDir);
copyFile(
  path.join(sourceClaudePluginDir, 'plugin.json'),
  path.join(bundledClaudePluginDir, 'plugin.json'),
);

for (const skill of officialSkills) {
  const skillPath = path.join(sourceSkillsDir, skill);
  copyDir(skillPath, path.join(bundledCodexSkillsDir, skill));
}

if (fs.existsSync(sourceHooksDir)) {
  copyDir(sourceHooksDir, bundledCodexHooksDir);
}

if (fs.existsSync(sourceAssetsDir)) {
  for (const asset of officialAssets) {
    copyFile(path.join(sourceAssetsDir, asset), path.join(bundledCodexAssetsDir, asset));
  }

  for (const asset of siteBrandAssets) {
    copyFile(path.join(sourceAssetsDir, asset), path.join(sitePublicDir, asset));
  }
}

console.log(`Copied skills to ${bundledSkillsDir}`);
if (fs.existsSync(bundledAssetsDir)) {
  console.log(`Copied assets to ${bundledAssetsDir}`);
}
console.log(`Synced plugin bundle to ${codexPluginBundleDir}`);
console.log(`Synced site brand assets to ${sitePublicDir}`);
