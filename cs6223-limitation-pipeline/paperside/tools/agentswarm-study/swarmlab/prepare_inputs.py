"""Fetch the team's frozen public papers and author source, without running targets."""
import argparse
import subprocess
from importlib.metadata import version
from pathlib import Path

from .util import dump, git, load, sha


STRATA = {
    "dev": "development",
    "test": "expanded_source",
    "paper-only": "expanded_paper_only",
}


def fetch_pdf(folder, entry):
    pdf = folder / "original.pdf"
    if not pdf.exists():
        pending = folder / "original.pdf.download"
        subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                        "--retry", "2", "--max-time", "120", "--output", str(pending),
                        entry["pdf_url"]], check=True, timeout=380)
        if sha(pending.read_bytes()) != entry["pdf_sha256"]:
            raise ValueError(f"Publisher PDF hash differs for {folder.name}")
        pending.replace(pdf)
    if sha(pdf.read_bytes()) != entry["pdf_sha256"]:
        raise ValueError(f"Publisher PDF hash differs for {folder.name}")
    return pdf


def prepare_source(folder, entry):
    commit = entry["commit"]
    repo = folder / "repo.git"
    if not repo.exists():
        subprocess.run(["git", "init", "--bare", "--quiet", str(repo)], check=True, timeout=30)
    probe = ["git", "-C", str(repo), "cat-file", "-e", commit + "^{commit}"]
    if subprocess.run(probe, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      timeout=30).returncode:
        subprocess.run(["git", "-C", str(repo), "fetch", "--quiet", "--depth=1", "--no-tags",
                        entry["repo_url"], commit], check=True, timeout=250)
    blocks = []
    for span in entry["literature_study_source_spans"]:
        path, end = span["path"], span["end"]
        lines = git(str(repo), "show", f"{commit}:{path}").decode("utf-8").splitlines()[:end]
        if len(lines) != end:
            raise ValueError(f"Source span truncated for {folder.name}/{path}")
        block = "\n".join(f"{n}: {line}" for n, line in enumerate(lines, 1))
        blocks.append(f"FILE {path} | original lines 1–{end}\n{block}")
    packet = "\n\n".join(blocks).encode()
    if sha(packet) != entry["literature_study_source_packet_sha256"]:
        raise ValueError(f"Source packet hash differs for {folder.name}")
    (folder / "original-source-packet.txt").write_bytes(packet)
    return repo


def prepare(root, groups, resume=False):
    from pypdf import PdfReader

    manifest = load(Path(__file__).resolve().parents[1] / "study-corpus.json")
    root.mkdir(parents=True, exist_ok=resume)
    index_path = root / "input-index.json"
    index = load(index_path) if index_path.is_file() else {}
    for slug, entry in manifest.items():
        if entry["stratum"] not in {STRATA[g] for g in groups}:
            continue
        folder = root / slug
        folder.mkdir(exist_ok=resume)
        pdf = fetch_pdf(folder, entry)
        pages = []
        for number, page in enumerate(PdfReader(pdf).pages, 1):
            text = page.extract_text() or ""
            lines = "\n".join(f"{i}: {line}" for i, line in enumerate(text.splitlines(), 1))
            pages.append(dict(page=number, text=text, numbered=lines))
        dump(folder / "paper.json", pages)
        repo = prepare_source(folder, entry) if entry.get("commit") else None
        dump(folder / "source.json", dict(paper_id=slug, pdf_sha256=entry["pdf_sha256"],
                                        repo=str(repo) if repo else None, commit=entry.get("commit"),
                                        pypdf=version("pypdf")))
        names = ["paper.json", "source.json"]
        if repo:
            names.append("original-source-packet.txt")
        index.update({f"{slug}/{name}": sha((folder / name).read_bytes()) for name in names})
        dump(index_path, index)
        print(f"{slug}: {len(pages)} pages, original hashes verified", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--groups", nargs="+", choices=STRATA, default=["dev"])
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    prepare(args.root.resolve(), args.groups, args.resume)
