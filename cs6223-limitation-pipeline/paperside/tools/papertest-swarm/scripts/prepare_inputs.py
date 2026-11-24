"""Copy the frozen paper/repository packets from the archived study into this workspace.

The archived run is the authoritative source of the frozen inputs; this script
re-verifies hashes and never edits the originals.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from swarmlab.util import git, load, sha  # noqa: E402

DEV = {"nnsmith": "01", "minference": "02", "infinigen": "03", "sparta": "04"}
FILES = ("paper.json", "source.json", "original-source-packet.txt")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path,
                        default=Path("/Users/pp/Desktop/nus/cs6223/paperside-method-pilot/"
                                     "cs6223-limitation-pipeline/paperside/runs/cs6223-swarm-study-dev-v9"))
    parser.add_argument("--inputs", type=Path, default=Path("inputs"))
    parser.add_argument("--reference", type=Path,
                        default=Path("/Users/pp/Desktop/nus/cs6223/method-boundary-review-20261120"))
    args = parser.parse_args()
    study, inputs, reference = args.study, args.inputs, args.reference
    if inputs.exists() and any(inputs.iterdir()):
        raise SystemExit(f"Inputs already exist; use a new directory: {inputs}")
    index = {}
    for slug in DEV:
        source = study / slug
        target = inputs / slug
        target.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            src = source / name
            if not src.is_file():
                raise SystemExit(f"Missing frozen input: {src}")
            shutil.copy2(src, target / name)
            index[f"{slug}/{name}"] = sha((target / name).read_bytes())
        meta = load(target / "source.json")
        if meta.get("repo"):
            commit = meta["commit"]
            git(meta["repo"], "cat-file", "-e", commit + "^{commit}")
            print(f"{slug}: repo {meta['repo']} @ {commit[:12]}")
        pages = load(target / "paper.json")
        print(f"{slug}: {len(pages)} pages, packet {len((target / 'original-source-packet.txt').read_text())} chars")
    reference_index = {}
    for name in ("reference-rubric-20261121.md", "reference-rubric.json"):
        src = reference / name
        if not src.is_file():
            raise SystemExit(f"Missing reference: {src}")
        shutil.copy2(src, inputs.parent / "reference" / name)
        reference_index[name] = sha(src.read_bytes())
    (inputs.parent / "reference" / "input-index.json").write_text(
        json.dumps(reference_index, ensure_ascii=False, indent=2) + "\n")
    target_index = inputs.parent / "inputs" / "input-index.json"
    target_index.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {target_index}")


if __name__ == "__main__":
    main()
