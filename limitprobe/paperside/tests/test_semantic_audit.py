import subprocess
import tempfile
import unittest
from pathlib import Path

from paperprobe.semantic_audit import adjudicate, freeze, index, retrieve


class SemanticAuditTest(unittest.TestCase):
    def test_freeze_rejects_quote_absent_from_claimed_page(self):
        row = dict(claim="Graph propagation", behavior="Initialize work set",
                   precondition="Graph exists", basis="explicit", kind="mechanism",
                   search_terms=["work set"], evidence=[dict(page=1, quote="initialize the work set")])
        other = dict(row, behavior="Pop work item",
                     evidence=[dict(page=1, quote="pop the next work item")])
        kept, rejected = freeze({"behaviors": [row, other]},
                                ["initialize the work set", "pop the next work item"])
        self.assertEqual([r["id"] for r in kept], ["B01"])
        self.assertEqual([r["index"] for r in rejected], [2])

    def test_parent_anchor_retrieves_called_stub_from_pinned_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            def git(*args):
                return subprocess.check_output(["git", "-C", tmp, *args], text=True)
            git("init", "-q")
            (repo / "pkg").mkdir()
            (repo / "pkg/__init__.py").write_text("from .graph import *\n")
            (repo / "pkg/graph.py").write_text('__all__ = ["propagate"]\ndef propagate(graph):\n    return {}\n')
            (repo / "run.py").write_text("from pkg import propagate\ndef run(graph):\n    return propagate(graph)\n")
            git("add", ".")
            git("-c", "user.email=test@example.test", "-c", "user.name=Test", "commit", "-qm", "fixture")
            commit = git("rev-parse", "HEAD").strip()
            (repo / "pkg/graph.py").write_text("raise Exception('working tree')\n")
            defs, edges, _ = index(repo, commit)
        rows = [dict(id="B01", claim="Propagation algorithm", behavior="Insert DFG nodes",
                     search_terms=["DFG"], kind="mechanism")]
        pool = retrieve(defs, edges, rows)
        src = pool["B01"]
        edge_id, edge = next(iter(src["edges"].items()))
        self.assertEqual(src["snippets"][edge["callee"]]["lines"]["3"], "    return {}")
        valid = dict(id="B01", result="local_mismatch", entry=edge["caller"],
                     edges=[edge_id], snippets=[edge["callee"]])
        self.assertEqual(adjudicate({"checks": [valid]}, rows, pool)[0]["result"], "local_mismatch")
        invalid = dict(valid, entry=edge["callee"])
        self.assertEqual(adjudicate({"checks": [invalid]}, rows, pool)[0]["result"], "unlocated")
        invented = dict(valid, edges=["E999"])
        self.assertEqual(adjudicate({"checks": [invented]}, rows, pool)[0]["result"], "unlocated")
