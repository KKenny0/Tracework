// Ordered canonical -> skill-local copies; bundles are copied after this map.
const copies = (source, skills, target) => skills.map(skill => [source, `skills/${skill}/${target}`]);
export const skillCopies = [
  ['references/tracework_state.py', 'scripts/tracework_state.py'],
  ...copies('references/tracework_state.py', ['capture', 'cold-start-interview', 'daily', 'weekly', 'monthly', 'query', 'recall', 'roadmap'], 'scripts/tracework_state.py'),
  ...copies('references/tracework-storage-convention.md', ['capture', 'recall', 'roadmap', 'monthly'], 'references/tracework-storage-convention.md'),
  ...copies('references/reporting-narrative-contract.md', ['daily', 'weekly', 'monthly'], 'references/reporting-narrative-contract.md'),
  ...copies('references/decision_replay.py', ['query', 'roadmap', 'recall'], 'scripts/decision_replay.py'),
  ['scripts/tracework_raw.py', 'references/tracework_raw.py'],
  ...copies('scripts/tracework_raw.py', ['capture', 'cold-start-interview', 'daily', 'weekly', 'monthly', 'query', 'recall', 'roadmap'], 'scripts/tracework_raw.py'),
  ['skills/roadmap/scripts/decision_graph.py', 'skills/query/scripts/decision_graph.py'],
];
