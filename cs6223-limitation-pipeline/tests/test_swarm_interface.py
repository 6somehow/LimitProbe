import json
from pathlib import Path

import pymupdf
import pytest

from codeside.doc_index import Passage
from codeside.integrate import Context, Rules, integrate
from codeside.process_confidence import ProcessContext, assess_all
from codeside.verify3b import load_paper_side, swarm_passages
from paperside_bridge.swarm_to_paper_side import convert, write_handoff


@pytest.fixture
def swarm_inputs(tmp_path):
    pdf = tmp_path / "toy.pdf"
    quote = "The method requires a fixed batch size."
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), quote)
        doc.new_page().insert_text((72, 72), "The second page covers evaluation.")
        doc.save(pdf)
    report = tmp_path / "final.txt"
    candidate = {
        "id": "H1", "category": "applicability_limitation", "trigger": "changing batch sizes",
        "consequence": "The allocation budget can be exceeded.", "origin_ids": ["worker1:W1"],
        "paper_evidence": [{"page": 1, "quote": quote}],
        "code_evidence": [{"path": "toy.py", "start": 3, "end": 5}],
    }
    return pdf, report, candidate


def test_converts_and_checks_quotes_then_integrates(swarm_inputs, tmp_path):
    pdf, report, candidate = swarm_inputs
    quote = candidate["paper_evidence"][0]["quote"]
    entries = [
        candidate,
        {**candidate, "id": "H2", "category": "mechanism_origin_unclear"},
        {**candidate, "id": "H3", "category": "method_shortcoming"},
        {**candidate, "id": "H4", "paper_evidence": [{"page": 2, "quote": quote}]},
        {**candidate, "id": "H5", "paper_evidence": [{"page": 1, "quote": quote.lower()}]},
    ]
    report.write_text(json.dumps({"paper_id": "toy", "candidates": entries}))
    handoff, lims = convert("toy", report, pdf)
    # H4 cites the wrong page but the quote is verbatim elsewhere: kept, with the real page. H5 is not verbatim: dropped.
    assert [d["id"] for d in handoff["dropped"]] == ["H5"]
    assert lims[3].paper_evidence[0].locator == "PDF p.1"
    assert [lim.swarm_category for lim in lims[:3]] == [entry["category"] for entry in entries[:3]]
    assert lims[0].condition_text == candidate["trigger"]
    assert lims[0].paper_evidence[0].quote == quote
    assert lims[0].swarm_provenance["candidate"] == candidate
    assert not lims[0].code_evidence
    write_handoff(tmp_path / "out", handoff, lims)
    assert load_paper_side(str(tmp_path / "out/paper_side.json")) == ([], [], [])
    cited = Passage("P1", "paper", "Method, p.1", quote)
    other = Passage("P2", "paper", "Evaluation, p.2", "Other text.")
    assert swarm_passages(handoff, str(pdf), [cited, other]) == (cited,)
    with pytest.raises(ValueError, match="PDF hash"):
        swarm_passages(handoff, str(report), [cited])

    class Judge:
        def condition(self, _lim):
            pytest.fail("Swarm paper hypotheses have no executable conditions")

    findings, _ = integrate("toy", [], [], lims, None, Rules(), Context(judge=Judge()))
    assert len(findings) == 4  # H4's wrong-page quote is relocated, not dropped
    assert all(f.origin == "swarm" and f.category == "paper_hypothesis" and f.level == "L3"
               and f.witness_hint["status"] == "no_condition" for f in findings)
    records = [{**f.model_dump(mode="json"), "limitations": [lim.model_dump(mode="json")]}
               for f, lim in zip(findings, lims)]
    assert assess_all(records, ProcessContext(None))["not_assessed_paper_only"] == 4
    assert all(r["process_confidence"] is None for r in records)


def test_gap_receipt_and_v1_compatibility(swarm_inputs):
    pdf, report, candidate = swarm_inputs
    candidate.pop("category")
    candidate["kind"] = "disclosed_boundary"
    report.write_text(json.dumps({"paper_id": "toy", "verdict": "narrows", "candidates": [candidate]}))
    handoff, lims = convert("toy", report, pdf)
    assert lims[0].swarm_category == "applicability_limitation"
    assert handoff["provenance"]["receipt_verdict"] == "narrows"
    with pytest.raises(ValueError, match="artifact does not match"):
        convert("other", report, pdf)
    with pytest.raises(ValueError, match="generation archive"):
        convert("toy", report.parent / "labels" / "fixture.json", pdf)
    v1_lim = lims[0].model_copy(update={"swarm_category": None, "notes": "verdict=absent"})
    findings, _ = integrate("toy", [], [], [v1_lim], None, Rules())
    assert findings[0].category == "not_implemented"
    assert findings[0].origin == "v1"


def test_checklimits_paper_only_cli_runs_offline(swarm_inputs, tmp_path, monkeypatch, capsys):
    from checklimits.checklimits.cli import main

    pdf, report, candidate = swarm_inputs
    report.write_text(json.dumps({"candidates": [candidate]}))
    results = tmp_path / "results"
    monkeypatch.delenv("SOCLAAS_API_KEY", raising=False)
    monkeypatch.delenv("SOCLAAS_BASE_URL", raising=False)
    assert main(["paper-only", "toy", "--pdf", str(pdf), "--swarm-report", str(report),
                 "--results-root", str(results)]) == 0
    assert json.loads(capsys.readouterr().out)["n_records"] == 1
    handoff = json.loads((results / "step4/toy/limitations_for_tests.json").read_text())
    finding, = handoff["findings"]
    fid = finding["finding_id"]
    assert finding["origin"] == "swarm"
    rec = json.loads((results / "tests/toy" / fid / "report.json").read_text())
    assert rec["finding_id"] == fid and rec["analysis"]["tier"] == "A1"
    assert rec["analysis"]["assessment"] == "unclear"
    assert rec["status"] == "not_run" and rec["verdict"] is None and rec["level"] is None
    assert rec["evidence"]["paper"][0]["quote"] == candidate["paper_evidence"][0]["quote"]


def test_pipeline_routes_swarm_3b_and_step4_to_separate_outputs(swarm_inputs, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from pipeline import run as pipeline

    pdf, report, candidate = swarm_inputs
    report.write_text(json.dumps({"candidates": [candidate]}))
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps({"artifact_id": "toy", "repo_url": "some/toy", "commit": "pinned"}))
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline, "artifact_json", lambda _aid: artifact)
    monkeypatch.setattr(pipeline, "git_head", lambda _repo: "pinned")

    p = pipeline.Paths("toy", "swarm")
    p.pdf.parent.mkdir(parents=True)
    p.pdf.write_bytes(pdf.read_bytes())
    p.lims.parent.mkdir(parents=True)
    p.lims.write_text("[]")
    p.verify3b.write_text("legacy verification")
    calls = []

    def stage_command(cmd):
        calls.append(cmd)
        if "codeside.verify3b" in cmd:
            output = Path(cmd[cmd.index("--out") + 1])
            output.write_text("[]")
            output.with_suffix(".detail.json").write_text('{"items": []}')

    monkeypatch.setattr(pipeline, "sh", stage_command)
    args = SimpleNamespace(paper_side_source="swarm", swarm_report=str(report), swarm_pdf_extractor="pypdf",
                           pdf=None, model="fixture", run_paper_side=False, until="step4")
    assert pipeline.run("toy", args) == p.step4
    verify, step4 = calls
    handoff = verify[verify.index("--paper-side") + 1]
    assert json.loads(handoff.read_text())["origin"] == "swarm"
    assert step4[step4.index("--paper-dir") + 1] == handoff.parent.parent
    assert step4[step4.index("--code-dir") + 1] == verify[-1].parent.parent
    assert step4[step4.index("--labels") + 1] == ""
    assert step4[step4.index("--out") + 1] == tmp_path / "results/swarm/step4"
    assert p.verify3b.read_text() == "legacy verification"

    calls.clear()
    pipeline.run("toy", args)
    assert len(calls) == 1 and "scripts/run_step4.py" in calls[0]


def test_s7_quotes_and_conditions(swarm_inputs):
    pdf, report, candidate = swarm_inputs
    quote = candidate.pop('paper_evidence')[0]['quote']
    candidate.update(paper_quotes=[{'page_number': 1, 'quote': quote}],
                     causal_argument='The fixed budget cannot adapt.', conditions='variable input')
    candidate.pop('trigger')
    report.write_text(json.dumps({'candidates': [candidate, {**candidate, 'id': 'bad',
        'paper_quotes': [{'page_number': 2, 'quote': quote.lower()}]}]}))
    handoff, limitations = convert('toy', report, pdf)
    assert len(limitations) == 1  # a quote that is not verbatim in the PDF is dropped
    assert limitations[0].condition_text == 'variable input'
    assert limitations[0].swarm_provenance['candidate']['causal_argument'] == 'The fixed budget cannot adapt.'
    assert handoff['dropped_count'] == 1
