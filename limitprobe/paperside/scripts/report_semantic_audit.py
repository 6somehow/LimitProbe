"""Render a local, standalone evidence report from frozen semantic audit runs."""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path

PAPERS = ("sparta", "flexprefill", "minference", "infinigen", "nnsmith")
LABELS = dict(supported="支持", partial="部分支持", local_mismatch="局部不一致",
              unlocated="未定位", static_undecidable="静态不可裁决")


def read(path):
    return json.loads(path.read_text())


def render(root):
    summaries, sections = [], []
    for paper in PAPERS:
        run = root / paper
        if not (run / "audit.json").exists():
            summaries.append(f"<li>{paper}：暂无源码审计结果</li>")
            continue
        frozen, audit, context = (read(run / filename) for filename in
                                  ("frozen.json", "audit.json", "source-context.json"))
        rows = {b["id"]: b for b in frozen["behaviors"]}
        counts = Counter(c["result"] for c in audit["checks"])
        count_text = " · ".join(f"{LABELS[k]} {counts[k]}" for k in LABELS if counts[k])
        summaries.append(f'<li><a href="#{paper}">{paper}</a>：{count_text}，引文淘汰 {len(frozen["rejected"])}</li>')
        cards = []
        for check in audit["checks"]:
            behavior = rows[check["id"]]
            source = context[check["id"]]
            snippets = source["snippets"]
            quotes = "".join(f'<blockquote>{escape(q["locator"])} · {escape(q["quote"])}</blockquote>'
                             for q in behavior["evidence"])
            calls = []
            for edge_id in check["edges"]:
                edge = source["edges"][edge_id]
                caller, callee = (snippets[edge[side]] for side in ("caller", "callee"))
                calls.append(f'<li><code>{escape(caller["function"])} → {escape(callee["function"])}</code>'
                             f'<br><code>{escape(caller["path"])}:{edge["line"]} {escape(edge["quote"])}</code></li>')
            code = []
            for sid in check["snippets"]:
                s = snippets[sid]
                lines = "\n".join(f"{i}  {line}" for i, line in s["lines"].items())
                scope = "完整函数体" if s["complete"] else "节选，行号可能跳跃"
                code.append(f'<details><summary>{sid} · {escape(s["path"])}:{s["start"]}–{s["end"]} · {scope}'
                            f'</summary><pre>{escape(lines)}</pre></details>')
            entry = snippets[check["entry"]]["function"] if check["entry"] else "未绑定"
            cards.append(
                f'<article><h3>{check["id"]} · {LABELS[check["result"]]}</h3>'
                f'<p>{escape(behavior["behavior"])}</p><p>论文依据 {escape(behavior["basis"])}'
                f' · 前提 {escape(behavior["precondition"])}</p>{quotes}'
                f'<p>入口 <code>{escape(entry)}</code> · 论文实验路径 {escape(check["experiment_path"])}</p>'
                f'<p>{escape(check["rationale"] or "无模型解释")}</p>'
                + (f'<p>引用校验：{escape(check["gate_failure"])}</p>' if check["gate_failure"] else "")
                + (f'<ol>{"".join(calls)}</ol>' if calls else "") + "".join(code) + "</article>")
        sections.append(f'<section id="{paper}"><h2>{paper}</h2>'
                        f'<p>固定 commit <code>{escape(audit["commit"])}</code>'
                        f' · 模型 <code>{escape(audit["model"]["model"])}</code></p>{"".join(cards)}</section>')
    return """<!DOCTYPE html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>论文行为与源码调用证据</title>
<style>
body{font:16px/1.65 system-ui,sans-serif;background:#f3f6f4;color:#162b22;margin:0}
main{max-width:960px;margin:auto;padding:32px 16px}section{margin:36px 0}
article{background:white;border:1px solid #ccd9d1;border-radius:10px;padding:12px 20px;margin:12px 0}
blockquote{margin:12px 0;padding:8px 12px;border-left:4px solid #739c87;background:#edf5f0}
a{color:#145c46}code{overflow-wrap:anywhere}pre{overflow:auto;background:#eef2ef;padding:12px}
summary{cursor:pointer}h3{color:#145c46}
</style><main><h1>论文行为与源码调用证据</h1>
<p>论文 PDF → 冻结行为与原文 → 固定 commit 检索 → 调用边与源码 → 范围限定的静态判定。</p>
<p>每条记录附论文原文、可展开的代码和模型判断。静态调用边只描述可解析的调用，
目标系统没有运行，实验路径保持未决。这些结果尚未经过独立标注核验。</p>
<ul>""" + "".join(summaries) + "</ul>" + "".join(sections) + "</main></html>"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(render(args.run), encoding="utf-8")
