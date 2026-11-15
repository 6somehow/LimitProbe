#!/usr/bin/env bash
# Step 2 (route A) -> step 3b on the four development papers. Generated files go to out/3b/.
# No paper-side output exists for them yet, so scope and evaluated-in-paper come out unknown.
set -euo pipefail
cd "$(dirname "$0")/.."
MODEL="${MODEL:-x-test-2}"
REPEATS="${REPEATS:-3}"
python - <<'PY' | while IFS=$'\t' read -r id repo roots entries; do
import json, pathlib
for id_ in ("nnsmith", "minference", "infinigen", "sparta"):
    a = json.load(open(f"data/{id_}/artifact.json"))
    roots = "speedup/infinigen,speedup/flexgen" if id_ == "infinigen" else "."
    print(id_, pathlib.Path(a["repo_url"]).name, roots, ",".join(a["entry_points"]), sep="\t")
PY
  mkdir -p out/3b/dev
  merged="out/3b/dev/${id}_limitations.json"
  args=(); IFS=',' read -ra rs <<<"$roots"; for r in "${rs[@]}"; do args+=(--package-root "$r"); done
  i=0; files=()
  IFS=',' read -ra es <<<"$entries"
  for e in "${es[@]}"; do
    i=$((i+1))
    python -m codeside.cli extract --repo "third_party/$repo" --entry "$e" --artifact "$id" --out "out/3b/dev/${id}_r$i.json" "${args[@]}" >/dev/null
    python -m codeside.cli to-limitations --regions "out/3b/dev/${id}_r$i.json" --out "out/3b/dev/${id}_l$i.json" >/dev/null
    files+=("out/3b/dev/${id}_l$i.json")
  done
  python - "$merged" "${files[@]}" <<'PY'
import json, sys
out, seen = [], set()
for n, path in enumerate(sys.argv[2:], 1):
    for lim in json.load(open(path)):
        key = (lim["condition_text"], lim["code_evidence"][0]["file"], lim["code_evidence"][0]["line_start"])
        if key not in seen:
            seen.add(key)
            lim["limitation_id"] = f"CL{len(out) + 1:02d}"
            out.append(lim)
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
print(sys.argv[1], len(out), "limitations")
PY
  python -m codeside.verify3b --limitations "$merged" --artifact "data/$id/artifact.json" \
    --pdf "third_party/papers/$id.pdf" --repo "third_party/$repo" --model "$MODEL" --repeats "$REPEATS" \
    --out "out/3b/dev/${id}_3b.json" | tail -1
done
