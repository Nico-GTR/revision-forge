#!/usr/bin/env bash
# Package each skill as <skill-name>.zip (skill folder at the root of the archive),
# ready to upload in Claude (Customize > Skills > Upload a skill).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/dist"
mkdir -p "$OUT"

cd "$ROOT/skills"
for dir in */; do
  name="${dir%/}"
  rm -f "$OUT/$name.zip"
  zip -rq "$OUT/$name.zip" "$name" -x '*.DS_Store'
  echo "built dist/$name.zip"
done
