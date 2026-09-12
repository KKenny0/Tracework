#!/usr/bin/env bash
# Sync the canonical tracework_raw.py to all skill directories that bundle it.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$REPO_ROOT/scripts/tracework_raw.py"

if [ ! -f "$CANONICAL" ]; then
  echo "Error: canonical file not found at $CANONICAL"
  exit 1
fi

TARGETS=(
  "$REPO_ROOT/references/"
)
for skill in capture cold-start-interview daily weekly monthly query recall roadmap; do
  TARGETS+=("$REPO_ROOT/skills/$skill/scripts/")
done

for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  cp "$CANONICAL" "$target"
  echo "Synced to ${target}tracework_raw.py"
done
