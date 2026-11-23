"""Plot diagnosis coverage for the report's eight source-backed papers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SPLITS = {
    "dev": ("nnsmith", "minference", "infinigen", "sparta"),
    "test-source": ("prompt-cache", "spinquant", "kvquant", "dx100"),
}
WORKFLOWS = ("gap_receipt_swarm", "api_once", "single_agent")
GRADERS = {"Blinded": "results", "Strict": "results-holistic"}


def load_grades(directory: Path) -> dict:
    expected = {(split, paper, workflow) for split, papers in SPLITS.items()
                for paper in papers for workflow in WORKFLOWS}
    rows = {}
    for row in json.loads((directory / "manifest.json").read_text()):
        key = row["split"], row["paper"], row["condition"]
        if key not in expected:
            continue
        split, paper, workflow = key
        prefix = directory / split / workflow / paper
        grade = json.loads(prefix.with_suffix(".json").read_text())["match"]
        digest = hashlib.sha256(prefix.with_suffix(".txt").read_bytes()).hexdigest()
        if (key in rows or grade not in {"core", "partial", "miss"}
                or (grade, digest) != (row["match"], row["final_sha256"])):
            raise ValueError(f"Invalid grade or final for {key} in {directory}")
        rows[key] = grade, digest
    if rows.keys() != expected:
        raise ValueError(f"Missing grades in {directory}: {expected - rows.keys()}")
    return rows


def main() -> None:
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True, help="SVG or PDF output path")
    args = parser.parse_args()
    graders = {name: load_grades(args.root / directory) for name, directory in GRADERS.items()}
    blind, strict = graders.values()
    if any(blind[key][1] != strict[key][1] for key in blind):
        raise ValueError("Graders must score identical finals")

    plt.rcParams.update({"font.size": 9, "pdf.fonttype": 42, "svg.fonttype": "none",
                        "svg.hashsalt": "cs6223-paper-side", "axes.spines.top": False,
                        "axes.spines.right": False})
    figure, axes = plt.subplots(1, 2, figsize=(5.5, 2.35), sharey=True, layout="constrained")
    figure.supxlabel("Papers with a core or partial diagnosis (out of 4)", fontsize=9)
    panels = (("dev", "Development"), ("test-source", "Test with source"))
    for axis, (split, title) in zip(axes, panels):
        counts = [sum(blind[split, paper, workflow][0] != "miss" for paper in SPLITS[split])
                  for workflow in WORKFLOWS]
        bars = axis.barh(("S7", "A", "B"), counts, color=("#285f8e", "#96611f", "#52766a"),
                         height=0.53)
        axis.bar_label(bars, labels=[f"{value}/4" for value in counts], padding=3)
        axis.set(title=title, xlim=(0, 4.65), xticks=(0, 1, 2, 3, 4))
        axis.grid(axis="x", color="#e4e9ee", linewidth=0.65)
        axis.set_axisbelow(True)
    axes[0].invert_yaxis()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"Date": None} if args.output.suffix == ".svg" else {"CreationDate": None}
    figure.savefig(args.output, metadata=metadata)
    if args.output.suffix == ".svg":
        lines = args.output.read_text(encoding="utf-8").splitlines()
        args.output.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
