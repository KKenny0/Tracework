import path from 'node:path';
import os from 'node:os';

export const PLUGIN_MARKETPLACE = 'tracework';
export const PLUGIN_NAME = 'tracework';
export const PLUGIN_VERSION = '0.10.0';
export const PLUGIN_KEY = `${PLUGIN_NAME}@${PLUGIN_MARKETPLACE}`;

export function expandHome(value: string): string {
  if (value === '~') return os.homedir();
  if (value.startsWith('~/')) return path.join(os.homedir(), value.slice(2));
  return value;
}

export function getCodexHome(override?: string): string {
  return path.resolve(expandHome(override || process.env.CODEX_HOME || path.join(os.homedir(), '.codex')));
}

export function getCodexPluginInstallPath(codexHomeOverride?: string): string {
  return path.join(getCodexHome(codexHomeOverride), 'plugins', 'cache', PLUGIN_MARKETPLACE, PLUGIN_NAME, PLUGIN_VERSION);
}

export function getCodexPluginSkillsPath(codexHomeOverride?: string): string {
  return path.join(getCodexPluginInstallPath(codexHomeOverride), 'skills');
}

export function getClaudePluginRoot(): string {
  return path.join(os.homedir(), '.claude', 'plugins');
}

export function getClaudePluginSkillsPath(): string {
  return path.join(getClaudePluginRoot(), 'cache', PLUGIN_MARKETPLACE, PLUGIN_NAME, PLUGIN_VERSION, 'skills');
}
