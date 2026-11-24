"""Render the paper-only mechanism inventory and behavior evidence as HTML."""
import argparse
from html import escape
import json
from pathlib import Path


def render(mapped, frozen, atomicity=None):
    def quotes(row):
        return "".join(f'<blockquote>{escape(q["locator"])} · {escape(q["quote"])}</blockquote>'
                       for q in row["evidence"])

    def links(ids):
        return ", ".join(f'<a href="#{escape(i)}">{escape(i)}</a>' for i in ids) or "—"

    cards = []
    for m in mapped["mechanisms"]:
        group = frozen["decomposition"][m["id"]]
        behaviors = "".join(
            f'<details><summary>{escape(b["id"])} · {escape(b["behavior"])}</summary>'
            f'<p>{escape(b["basis"])} · 前提 {escape(b["precondition"])}</p>{quotes(b)}</details>'
            for b in group["behaviors"])
        gaps = "".join(f'<li>{escape(q)}</li>' for q in group["open_questions"])
        rejected = "".join(f'<li>候选 {r["index"]} · {escape(r["reason"])}</li>' for r in group["rejected"])
        review = ""
        if atomicity and m["id"] == "M02":
            rows = "".join(f'<li>{escape(b["behavior"])}{quotes(b)}</li>' for b in atomicity["behaviors"])
            rejects = "".join(f'<li>候选 {r["index"]} · {escape(r["reason"])}</li>'
                              for r in atomicity["rejected"])
            review = (f'<details><summary>算法 1 原子性复核 · {len(atomicity["behaviors"])} 条'
                      f'（独立草稿）</summary><ol>{rows}</ol><ul>{rejects}</ul></details>')
        cards.append(f'<article id="{m["id"]}"><h2>{m["id"]} · {escape(m["name"])}</h2>'
                     f'<p>{escape(m["description"])}</p><p>上游 {links(m["depends_on"])}'
                     f' · {escape(group["status"])} · {len(group["behaviors"])} 条行为</p>'
                     + ('<p>补充批次：地图引文经人工修订，行为仍由模型拆解并校验。</p>'
                        if m.get("supplemental") else "")
                     + (f'<p>未解析依赖：{escape(", ".join(m["unresolved_dependencies"]))}</p>'
                        if m["unresolved_dependencies"] else "")
                     + quotes(m) + behaviors + review + (f'<h3>未决与淘汰</h3><ul>{gaps}{rejected}</ul>'
                                                if gaps or rejected else "") + '</article>')
    claims = "".join(f'<details><summary>{escape(c["kind"])} · {escape(c["statement"])}</summary>'
                     f'{quotes(c)}</details>' for c in mapped["claims"])
    coverage = "".join(f'<tr><th scope="row">{r["page"]}</th><td>{escape(r["role"])}</td>'
                       f'<td>{links(r["mechanisms"])}</td><td>{escape(r["note"])}'
                       + (f'<br>未解析主题：{escape(", ".join(r["unresolved_topics"]))}'
                          if r.get("unresolved_topics") else "") + "</td></tr>" for r in mapped["coverage"])
    map_rejects = "".join(f'<li>{escape(r["type"])} {r["index"]} · {escape(r["reason"])}</li>'
                          for r in mapped["rejected"])
    ids = [m["id"] for m in mapped["mechanisms"]]
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>论文语义拆解</title>
<style>
body{font:16px/1.6 system-ui,sans-serif;color:#152c24;background:#f1f5f1;margin:0}
main{max-width:970px;margin:auto;padding:32px 16px}article{background:white;padding:16px 20px;
margin:20px 0;border:1px solid #cbd9d1;border-radius:10px}a{color:#076348}
details{padding:8px 0;border-top:1px solid #d8e1da}summary{cursor:pointer}
blockquote{margin:8px 0;padding:6px 12px;border-left:4px solid #739c87;background:#ebf4ef}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:7px;border-bottom:1px solid #cbd9d1}
</style><main>""" + f"""<h1>{escape(mapped["paper"])} · 整篇论文语义拆解</h1>
<p>{len(mapped["coverage"])} 页 · {len(ids)} 个机制 · {len(frozen["behaviors"])} 条冻结行为
· {len(mapped["claims"])} 条范围、评测或限制主张</p>
<p>PDF → 机制地图 → 逐机制行为 → 引文核验 → 冻结。页面索引来自模型；引文经过文本校验，语义完整性需要复核。</p>
<nav>{links(ids)} · <a href="#claims">其他主张</a> · <a href="#coverage">逐页覆盖</a></nav>
{"".join(cards)}
<section id="claims"><h2>范围、评测与限制</h2>{claims}</section>
<section id="coverage"><h2>逐页覆盖</h2>
<table><thead><tr><th>PDF 页</th><th>类别</th><th>机制</th><th>页面说明</th></tr></thead>
<tbody>{coverage}</tbody></table></section>
<h2>地图候选淘汰</h2><ul>{map_rejects or "<li>无</li>"}</ul></main></html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--supplement", type=Path)
    args = parser.parse_args()
    mapped, frozen = [json.loads((args.run / p).read_text())
                      for p in ("mechanism-map.json", "frozen.json")]
    if args.supplement:
        extra_map, extra_frozen = [json.loads((args.supplement / p).read_text())
                                   for p in ("mechanism-map.json", "frozen.json")]
        if mapped["pdf_sha256"] != extra_map["pdf_sha256"]:
            raise ValueError("Supplement PDF differs from the base run")
        supplement = {m["name"]: m["id"] for m in extra_map["mechanisms"]}
        if set(supplement.values()) & set(frozen["decomposition"]):
            raise ValueError("Duplicate mechanism IDs in supplement")
        mapped["mechanisms"].extend(dict(m, supplemental=True) for m in extra_map["mechanisms"])
        mapped["mechanisms"].sort(key=lambda m: m["id"])
        frozen["behaviors"].extend(extra_frozen["behaviors"])
        frozen["decomposition"].update(extra_frozen["decomposition"])
        for row in mapped["coverage"]:
            topics = row.get("unresolved_topics", [])
            row["mechanisms"].extend(supplement[name] for name in topics if name in supplement)
            row["unresolved_topics"] = [name for name in topics if name not in supplement]
        for mechanism in mapped["mechanisms"]:
            names = mechanism["unresolved_dependencies"]
            mechanism["depends_on"].extend(supplement[name] for name in names if name in supplement)
            mechanism["unresolved_dependencies"] = [name for name in names if name not in supplement]
    review_path = args.run / "M02-atomicity.json"
    atomicity = json.loads(review_path.read_text())["group"] if review_path.exists() else None
    (args.run / "report.html").write_text(render(mapped, frozen, atomicity), encoding="utf-8")
