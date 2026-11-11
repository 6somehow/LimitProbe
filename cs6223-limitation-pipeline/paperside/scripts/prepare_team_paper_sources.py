"""Acquire the five team-pinned snapshots without executing target code."""
import argparse
import subprocess
from pathlib import Path

from paperprobe.io import file_sha256, read_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--team", type=Path, required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    team = args.team.resolve()
    specs = read_json(root / "workstreams/zhaopeng/team-reviewed.json")
    artifacts = {a["artifact_id"]: a for p in team.glob("data/*/artifact.json") if (a := read_json(p))}
    if set(specs) != set(artifacts) or any(specs[p]["commit"] != artifacts[p]["commit"] for p in specs):
        raise SystemExit("Team artifact manifest changed; review pins before proceeding")
    subprocess.run(["bash", "scripts/fetch_papers.sh"], cwd=team, check=True, timeout=240)
    for pid, artifact in sorted(artifacts.items()):
        pdf = team / "third_party/papers" / f"{pid}.pdf"
        if file_sha256(pdf) != specs[pid]["pdf_sha256"]:
            raise SystemExit(f"PDF hash mismatch: {pid}")
        dest = root / "data/repos" / f"team-{pid}"
        dest.mkdir(parents=True, exist_ok=True)

        def git(*cmd):
            return subprocess.check_output(["git", "-C", str(dest), *cmd], text=True, timeout=120).strip()

        if not (dest / ".git").is_dir():
            if any(dest.iterdir()):
                raise SystemExit(f"Refusing to populate nonempty destination: {dest}")
            git("init", "-q")
        try:
            head = git("rev-parse", "--verify", "HEAD")
        except subprocess.CalledProcessError:
            git("fetch", "-q", "--depth", "1", artifact["repo_url"], artifact["commit"])
            git("checkout", "-q", "--detach", artifact["commit"])
            head = git("rev-parse", "--verify", "HEAD")
        if head != artifact["commit"] or git("status", "--porcelain", "--untracked-files=no"):
            raise SystemExit(f"Existing checkout is not the clean team pin: {pid}")
        print(f"{pid}: PDF and repository verified")


if __name__ == "__main__":
    main()
