#!/usr/bin/env bash
# Clone every dataset artifact at its pinned commit into third_party/ (reads data/*/artifact.json).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY' | while read -r name url commit; do
import json, glob, pathlib
for f in sorted(glob.glob("data/*/artifact.json")):
    a = json.load(open(f))
    name = pathlib.Path(a["repo_url"]).name
    print(name, a["repo_url"], a["commit"])
PY
  dir="third_party/$name"
  if [ ! -d "$dir" ]; then git clone -q "$url" "$dir"; fi
  git -C "$dir" fetch -q --depth 1 origin "$commit" 2>/dev/null || git -C "$dir" fetch -q --all --tags
  git -C "$dir" checkout -q "$commit"
  echo "$name @ $(git -C "$dir" rev-parse --short HEAD)"
done
