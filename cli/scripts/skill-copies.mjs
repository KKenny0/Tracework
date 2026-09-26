import fs from 'node:fs';
import path from 'node:path';

export const officialSkills = JSON.parse(fs.readFileSync(new URL('../skill-catalog.json', import.meta.url), 'utf8'));
if (!Array.isArray(officialSkills) || !officialSkills.length
  || officialSkills.some(skill => typeof skill !== 'string' || !/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(skill))
  || new Set(officialSkills).size !== officialSkills.length) {
  throw new Error('skill-catalog.json must contain nonempty, unique, safe skill names');
}

// Ordered canonical -> skill-local copies; bundles are copied after this map.
const copies = (source, skills, target) => skills.map(skill => [source, `skills/${skill}/${target}`]);
export const skillCopies = [
  ['references/tracework_state.py', 'scripts/tracework_state.py'],
  ...copies('references/tracework_state.py', officialSkills, 'scripts/tracework_state.py'),
  ...copies('references/tracework-storage-convention.md', ['capture', 'monthly'], 'references/tracework-storage-convention.md'),
  ...copies('references/reporting-narrative-contract.md', ['daily', 'weekly', 'monthly'], 'references/reporting-narrative-contract.md'),
  ['scripts/tracework_raw.py', 'references/tracework_raw.py'],
  ...copies('scripts/tracework_raw.py', officialSkills, 'scripts/tracework_raw.py'),
];

// Validate the entire plan before any local copy or generated bundle is changed.
export function validateSkillSources(repoRoot) {
  const sourceDir = path.join(repoRoot, 'skills');
  const sourceSkills = fs.readdirSync(sourceDir, { withFileTypes: true })
    .filter(entry => entry.isDirectory() && fs.existsSync(path.join(sourceDir, entry.name, 'SKILL.md')) && fs.statSync(path.join(sourceDir, entry.name, 'SKILL.md')).isFile())
    .map(entry => entry.name);
  if (sourceSkills.length !== officialSkills.length || officialSkills.some(skill => !sourceSkills.includes(skill))) {
    throw new Error('skill-catalog.json must match source skills with SKILL.md');
  }
  for (const [source, target] of skillCopies) {
    const skill = target.startsWith('skills/') ? target.split('/')[1] : null;
    if (skill && !officialSkills.includes(skill)) throw new Error(`Copy target skill is not in catalog: ${skill}`);
    if (!fs.statSync(path.join(repoRoot, source)).isFile()) throw new Error(`Canonical source is not a file: ${source}`);
  }
}
