"""Build a standalone report of source checklist and automated paper review."""
import argparse
from collections import Counter
from html import escape
from pathlib import Path

from paperprobe.io import read_json, write_json

LABELS = dict(compound="复合行为", duplicate="重复", scope_drift="机制范围偏移",
              unsupported_inference="无依据推断", insufficient_evidence="引文支撑不足",
              missing_precondition="遗漏前提", runtime_effect="运行效果",
              overstatement="表述过强", not_checkable="不可独立核验")
COVER = dict(full="已覆盖", partial="部分覆盖", omitted="遗漏")


def quote(row):
    return "".join(f'<blockquote>{escape(q["locator"])} · {escape(q["quote"])}</blockquote>'
                   for q in row.get("evidence", []))


def render(checklist, review, draft, screening=None):
    screening = {r["id"]: r for r in (screening or {}).get("items", [])}
    automatic = {r["id"]: r for r in review["atomicity"]}
    human_flags = {r["id"] for r in checklist["behavior_review"] if r["issues"]}
    model_flags = {r["id"] for r in review["atomicity"] if r["issues"]}
    issues = Counter(i for r in review["atomicity"] for i in r["issues"])
    proposals = [p for chunk in review["coverage"] for p in chunk["proposals"]]
    claim_proposals = [p for chunk in review["coverage"] for p in chunk.get("claim_proposals", [])]
    baseline = Counter(r["coverage"] for r in checklist["references"])
    screen_counts = Counter(r["category"] for r in screening.values())
    summary = dict(proposal_screening=dict(screen_counts), reference_counts=dict(baseline), original_rows=len(checklist["behavior_review"]),
                   reference_flagged=len(human_flags), automatic_flagged=len(model_flags),
                   shared_flagged=len(human_flags & model_flags),
                   reference_only=sorted(human_flags - model_flags),
                   automatic_only=sorted(model_flags - human_flags),
                   proposed_revision_count=len(review["changes"]), proposal_count=len(proposals),
                   draft_rows=len(draft["behaviors"]), issue_counts=dict(issues),
                   claim_proposal_count=len(claim_proposals),
                   semantic_confirmation="pending", automatic_failures=review["failures"])

    refs = []
    for row in checklist["references"]:
        ids = ", ".join(row["matched_ids"]) or "—"
        claims = row.get("matched_claims", [])
        if claims:
            ids += " · 地图主张 " + ", ".join(map(str, claims))
        refs.append(f'<tr><td>{row["id"]}</td><td>{escape(row["topic"])}</td>'
                    f'<td>{escape(row["behavior"])}{quote(row)}</td>'
                    f'<td>{COVER[row["coverage"]]}<br>{escape(ids)}</td></tr>')
    records = []
    for original in checklist["behavior_review"]:
        decision = automatic.get(original["id"])
        manual = "、".join(LABELS[i["type"]] for i in original["issues"]) or "未发现问题"
        flags = "、".join(LABELS[i] for i in decision["issues"]) if decision else "未复核"
        reasons = "".join(f'<li>{LABELS[i["type"]]} · {escape(i["reason"])}</li>'
                          for i in original["issues"])
        replacement = ""
        if decision:
            rejected = "".join(f'<li>{r["index"]} · {escape(r["reason"])}</li>'
                               for r in decision["rejected"])
            replacement = "".join(f'<li><b>{b["id"]}</b> {escape(b["behavior"])}'
                                  f'<p>前提 {escape(b["precondition"])}</p>{quote(b)}</li>'
                                  for b in decision["replacements"])
            replacement = (f'<p>自动复核状态 {escape(decision["status"])} · '
                           f'{escape(decision["reason"])}</p>'
                           + (f'<p>格式校验 {escape(decision["validation_error"])}</p>'
                              if decision.get("validation_error") else "")
                           + (f'<ol>{replacement}</ol>' if replacement else "")
                           + (f'<p>淘汰的替换建议</p><ul>{rejected}</ul>' if rejected else ""))
        records.append(
            f'<details data-search="{escape(original["id"]+" "+original["behavior"], quote=True)}">'
            f'<summary>{original["id"]} · {escape(original["behavior"])}</summary>'
            f'<p>原前提 {escape(original["precondition"])}</p>{quote(original)}'
            f'<p>来源核对 {manual} · 自动复核 {flags or "未发现问题"}</p>'
            + (f'<ul>{reasons}</ul>' if reasons else "") + replacement + '</details>')
    category_names = dict(core_mechanism_gap="核心机制补充",
        existing_or_redundant="疑似已有或重复", example_detail="示例细节",
        example_integration="示例集成", context_statement="背景概括",
        artifact_procedure="artifact步骤", evaluation_procedure="评测步骤")
    def screening_note(pid):
        row = screening.get(pid)
        if not row:
            return ""
        return (f'<p><b>{category_names[row["category"]]}</b> · {escape(row["note"])}</p>'
                '<p>来源核对后的候选筛查，待团队确认。</p>')
    candidates = "".join(f'<article><h3>{p["id"]} · {escape(p["mechanism_name"])}</h3>'
                         f'{screening_note(p["id"])}<p>{escape(p["behavior"])}</p><p>前提 {escape(p["precondition"])}</p>'
                         f'{quote(p)}</article>' for p in proposals + claim_proposals)
    pages = []
    for chunk in review["coverage"]:
        for page in chunk["pages"]:
            anchors = "".join(f'<li>{escape(a["name"])} · {escape(a["disposition"])}'
                              f'<br>{escape(a["reason"])}{quote(a)}</li>' for a in page["anchors"])
            pages.append(f'<details><summary>PDF p.{page["page"]} · {page["status"]}</summary>'
                         f'<p>{escape(page.get("note") or "")}</p><ul>{anchors}</ul></details>')
    failed = escape(str(review["failures"] or "无"))
    unresolved = sum(p["status"] != "reviewed" for c in review["coverage"] for p in c["pages"])
    html = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>SparTA 论文拆解质量复核</title>
<style>
body{font:16px/1.6 system-ui,sans-serif;color:#183029;background:#f2f5f3;margin:0}
main{max-width:1100px;margin:auto;padding:30px 16px}a{color:#0b6851}section{margin:32px 0}
details,article{background:white;padding:12px 16px;border:1px solid #cbd9d1;border-radius:8px;margin:8px 0}
summary{cursor:pointer}blockquote{margin:8px 0;padding:6px 12px;border-left:4px solid #729d87;background:#eef6f0;white-space:pre-wrap}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;vertical-align:top;border-bottom:1px solid #ccd8cf;padding:8px}
input{padding:10px;width:min(90%,600px);font:inherit}.stats{padding:16px;background:#dfeee4;border-radius:8px}
nav a{display:inline-block;margin:8px}
</style><main><h1>SparTA 论文拆解质量复核</h1>"""
    html += f"""<p>基于论文逐段整理的开发参考表，加上程序独立运行的覆盖与原子性复核。
参考表由 Codex 协助整理，团队人工确认待完成，未作为自动复核的输入。</p>
<div class="stats">{len(checklist["references"])} 个来源检查点 · 原清单 {len(checklist["behavior_review"])} 条行为<br>
参考表覆盖情况：已覆盖 {baseline["full"]} · 部分覆盖 {baseline["partial"]} · 遗漏 {baseline["omitted"]}<br>
来源核对标出 {len(human_flags)} 条 · 自动复核标出 {len(model_flags)} 条 · 共同标出 {len(human_flags & model_flags)} 条<br>
{len(review["changes"])} 条原记录有通过引文校验的修订建议 · {len(proposals)} 条行为补充候选，{len(claim_proposals)} 条其他主张补充候选 · 修订草稿 {len(draft["behaviors"])} 条<br>
失败批次 {failed} · 未返回页面 {len(review["missing_pages"])} · 页面复核未决 {unresolved}
</div>
<p>草稿中的新增和替换只通过了结构与引文检查。重复项及范围偏移项继续保留、等待确认；
数量与重合数用于开发诊断，不能解释为准确率或完整率。</p>
<nav><a href="#references">来源参考表</a><a href="#records">逐条问题与修订</a>
<a href="#additions">遗漏补充候选</a><a href="#pages">逐页自动回查</a><a href="review.json">复核JSON</a><a href="reviewed-frozen.json">修订草稿JSON</a></nav>
<section id="references"><h2>来源参考表</h2><p>覆盖判定针对原有 102 条行为及地图主张。
检查点选择偏重设计章节与算法1–3，未穷尽所有评测结果。</p>
<table><thead><tr><th>ID</th><th>主题</th><th>论文要求及引文</th><th>原清单覆盖</th></tr></thead>
<tbody>{"".join(refs)}</tbody></table></section>
<section id="records"><h2>逐条问题与修订</h2><input id="search" placeholder="搜索行为 ID 或原行为文字"
aria-label="搜索行为"><div id="records-list">{"".join(records)}</div></section>
<section id="additions"><h2>遗漏补充候选</h2><p>来源核对后筛出 {screen_counts["core_mechanism_gap"]} 条核心机制候选；其余包含评测、artifact、示例及疑似重复。类别来自事后核对，自动原始输出保留。</p>{candidates or "<p>无通过校验的补充候选。</p>"}</section>
<section id="pages"><h2>逐页自动回查</h2>{"".join(pages)}</section>
<script>document.getElementById('search').addEventListener('input',event=>{{
const term=event.target.value.toLowerCase();
document.querySelectorAll('#records-list>details').forEach(row=>{{
row.hidden=!row.dataset.search.toLowerCase().includes(term);}});
}});</script></main></html>"""
    return html, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--checklist", type=Path, required=True)
    args = parser.parse_args()
    checklist = read_json(args.checklist)
    review, draft = [read_json(args.run / name) for name in ("review.json", "reviewed-frozen.json")]
    if checklist["pdf_sha256"] != draft["pdf_sha256"] or checklist["inputs"] != draft["inputs"]:
        raise ValueError("Reference and automatic review use different inputs")
    screen_path = args.run / "proposal-screening.json"
    html, summary = render(checklist, review, draft, read_json(screen_path) if screen_path.exists() else None)
    (args.run / "report.html").write_text(html, encoding="utf-8")
    write_json(args.run / "comparison.json", summary)
