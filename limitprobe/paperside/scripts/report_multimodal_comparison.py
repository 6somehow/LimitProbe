"""Render an offline, traceable text versus page-image decomposition comparison."""
import argparse
import base64
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import unicodedata

import pymupdf

from paperprobe.io import file_sha256, read_json, write_json
from paperprobe.multimodal_decomposition import parse_response


THEMES = [
    ("TeSA表示", "M01", "M01", "M01"),
    ("工作集传播", "M02", "M02", "M02"),
    ("剪枝代数", "M03", "M03", "M03"),
    ("Tensor Scrambling", "M04", "M04", "M04"),
    ("AD反向传播", "M05", "M05", "M05"),
    ("量化规则", "M06", "M06", "M06"),
    ("校准缓存", "M07", "M07", "M07"),
    ("执行计划转换", "M08", "M08", "M08"),
    ("位宽舍入", "M09", "M09", "M09"),
    ("加权分块覆盖", "M10", "M10", "M10"),
    ("块大小权重profiling", "M11", "M16", "M17"),
    ("特化提示", "M12", "M11", "M11"),
    ("代码特化", "M13", "M12", "M12"),
    ("dismantle", "M14", "M13", "M13"),
    ("量化指令特化", "M15", "M14", "M14"),
    ("Sparse Tensor Core策略", "M16", "M17", "M15"),
    ("Rammer集成", "M17", "M15", "M16"),
    ("稀疏探索反馈循环", "M18", None, None),
    ("Artifact复跑脚本", None, None, "M18"),
]


def normalize_visual_quote(text):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"(?<=[A-Za-z])[-‐]\s*\n\s*(?=[a-z])", "", text)
    return " ".join(text.split())


def arm_data(directory):
    raw = parse_response(read_json(directory / "map.raw.json"))
    mapped = read_json(directory / "mechanism-map.json")
    frozen = read_json(directory / "frozen.json")
    raw_behaviors = {}
    for path in sorted(p for p in directory.glob("M*.raw.json") if re.fullmatch(r"M\d{2}\.raw\.json", p.name)):
        for group in parse_response(read_json(path))["groups"]:
            raw_behaviors[group["id"]] = group
    usage = Counter()
    responses = [directory / "map.raw.json"] + sorted(p for p in directory.glob("M*.raw.json") if re.fullmatch(r"M\d{2}\.raw\.json", p.name))
    for path in responses:
        usage.update({k: read_json(path).get("usage", {}).get(k, 0)
                      for k in ("prompt_tokens", "completion_tokens", "total_tokens")})
    return dict(raw=raw, mapped=mapped, frozen=frozen, raw_behaviors=raw_behaviors,
                usage=dict(usage), requests=len(responses))


def citation_diagnostics(arm, pages):
    rows = []
    for rejected in arm["frozen"]["rejected"]:
        group = arm["raw_behaviors"][rejected["mechanism"]]
        behavior = group["behaviors"][rejected["index"] - 1]
        matches = []
        for evidence in behavior["evidence"]:
            page = evidence["page"]
            quote = evidence["quote"]
            valid = type(page) is int and 1 <= page <= len(pages)
            normalized = bool(valid and normalize_visual_quote(quote) in normalize_visual_quote(pages[page - 1]))
            matches.append(dict(page=page, quote=quote, normalized_text_match=normalized,
                                shorter_than_validator_minimum=len(" ".join(quote.split())) < 12))
        rows.append(dict(**rejected, behavior=behavior["behavior"], evidence=matches,
                         interpretation="Diagnostic only; original acceptance result is unchanged"))
    return rows


def quote_html(items):
    return "".join(
        f'<blockquote><button class="page-button" data-page="{q.get("page", int(q["locator"].split(".")[-1]) if "locator" in q else 1)}">'
        f'PDF p.{q.get("page", q.get("locator", "").split(".")[-1])}</button> {escape(q["quote"])}</blockquote>'
        for q in items
    )


def report(run, baseline, output):
    arms = {"historical": arm_data(baseline), "text": arm_data(run / "text-control"),
            "vision": arm_data(run / "vision")}
    protocol = read_json(run / "protocol.json")
    alignment = read_json(run / "theme-alignment.json")
    directories = {"historical": baseline, "text": run / "text-control", "vision": run / "vision"}
    if alignment["map_response_sha256"] != {name: file_sha256(path / "map.raw.json") for name, path in directories.items()}:
        raise ValueError("Source-reviewed theme alignment belongs to different map responses")
    themes = alignment["themes"]
    image_tokens = read_json(run / "vision/map.raw.json")["usage"]["prompt_tokens_details"]["multimodal_tokens"]["image"]
    pages = [p["text"] for p in read_json(baseline / "map.raw.request.json")["data"]["pages"]]
    diagnostics = {name: citation_diagnostics(arm, pages) for name, arm in arms.items()}
    write_json(run / "citation-diagnostics.json", diagnostics)
    summary = {}
    for name, arm in arms.items():
        summary[name] = dict(
            raw_mechanisms=len(arm["raw"]["mechanisms"]),
            quote_valid_mechanisms=len(arm["mapped"]["mechanisms"]),
            rejected_mechanisms=sum(r["type"] == "mechanism" for r in arm["mapped"]["rejected"]),
            raw_behaviors=sum(len(g["behaviors"]) for g in arm["raw_behaviors"].values()),
            quote_valid_behaviors=len(arm["frozen"]["behaviors"]),
            rejected_behaviors=len(arm["frozen"]["rejected"]),
            unresolved_groups=[mid for mid, g in arm["frozen"]["decomposition"].items() if not g["behaviors"]],
            requests=arm["requests"], tokens=arm["usage"],
            actual_model=arm["mapped"]["model"]["model"])
    write_json(run / "summary.json", dict(arms=summary,
               inference="One paper, one run per arm. Quote matching is not semantic accuracy.",
               figure_theme_alignment="Source-based Codex review; not independent human annotation"))
    rows = []
    columns = ["historical", "text", "vision"]
    metric_names = [
        ("模型提出的机制", "raw_mechanisms"), ("机制引文匹配通过", "quote_valid_mechanisms"),
        ("模型提出的行为", "raw_behaviors"), ("行为引文匹配通过", "quote_valid_behaviors"),
        ("行为引文未通过", "rejected_behaviors"), ("API请求数", "requests")]
    for label, key in metric_names:
        rows.append(f'<tr><th>{label}</th>' + "".join(f'<td>{summary[c][key]}</td>' for c in columns) + "</tr>")
    rows.append('<tr><th>总token（含输入与输出）</th>' +
                "".join(f'<td>{summary[c]["tokens"]["total_tokens"]:,}</td>' for c in columns) + "</tr>")

    def mechanism_cell(arm_name, mid):
        if mid is None:
            return '<td class="absent">本次地图未提出</td>'
        arm = arms[arm_name]
        index = int(mid[1:]) - 1
        mechanism = arm["raw"]["mechanisms"][index]
        kept = any(m["id"] == mid for m in arm["mapped"]["mechanisms"])
        group = arm["raw_behaviors"].get(mid)
        accepted = arm["frozen"]["decomposition"].get(mid, {}).get("behaviors", [])
        status = "机制引文通过" if kept else "机制引文未通过，未进入拆解"
        behavior_detail = ""
        if group:
            frozen_group = arm["frozen"]["decomposition"][mid]
            rejects = {r["index"]: r["reason"] for r in frozen_group["rejected"]}
            parts = []
            for i, behavior in enumerate(group["behaviors"], 1):
                state = "引文通过" if i not in rejects else "引文未通过 · " + rejects[i]
                parts.append(f'<li><b>{mid}-B{i:02d}</b> <span class="meta">{escape(state)}</span>'
                             f'<p>{escape(behavior["behavior"])}</p>'
                             f'<p class="meta">前提 {escape(behavior["precondition"])}</p>'
                             f'{quote_html(behavior["evidence"])}</li>')
            behavior_detail = (f'<details><summary>展开行为 · 原始{len(group["behaviors"])}条 / 引文通过{len(accepted)}条</summary>'
                               f'<ol>{"".join(parts)}</ol></details>')
        return (f'<td><span class="id">{mid}</span> <b>{escape(mechanism["name"])}</b>'
                f'<p>{escape(mechanism["description"])}</p><span class="badge {"warn" if not kept else ""}">{status}</span>'
                f'<details><summary>地图原始引文</summary>{quote_html(mechanism["evidence"])}</details>{behavior_detail}</td>')

    theme_rows = []
    for label, historical, text, vision in themes:
        theme_rows.append(f'<tr><th>{escape(label)}</th>{mechanism_cell("historical", historical)}'
                          f'{mechanism_cell("text", text)}{mechanism_cell("vision", vision)}</tr>')

    # Illustrative evidence crops are original PDF content, not model-generated images.
    image_paths = protocol["image_pages"]
    page_images = {str(i["page"]): "data:image/jpeg;base64," +
                   base64.b64encode(Path(i["path"]).read_bytes()).decode() for i in image_paths}
    documents = pymupdf.open()
    crops = []
    pdf = baseline.parent.parent / "data/papers/sparta/paper.pdf"
    if not pdf.exists():
        pdf = baseline.parent.parent.parent / "team-codeside-review/cs6223-limitation-pipeline/third_party/papers/sparta.pdf"
    documents = pymupdf.open(pdf)
    for page, rect, title in [
        (5, (54, 70, 300, 220), "算法1 · 循环条件与取出节点"),
        (5, (317, 70, 562, 175), "表2 · 各条件分支"),
        (13, (317, 388, 562, 644), "Sparse Tensor Core策略 · 原文语境"),
    ]:
        pixmap = documents[page - 1].get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=pymupdf.Rect(rect))
        uri = "data:image/jpeg;base64," + base64.b64encode(pixmap.tobytes("jpeg", jpg_quality=92)).decode()
        crops.append(f'<figure><img src="{uri}" alt="{escape(title)}" loading="lazy"><figcaption>{title} · PDF p.{page}</figcaption></figure>')

    cases = [
        ("循环条件与弹出节点",
         "当前文字版M02-B02把循环条件与弹出节点放在同一条。图文版原始M02-B02与B03将它们分开，粒度更细。",
         "图文版循环条件引文写成“while S ≠ ∅ do”，与提取文本“while S⁄= /0 do”不匹配；返回G的引文又短于校验下限。这些失败不等于原文缺少对应动作。"),
        ("剪枝代数的条件分支",
         "当前文字版M03将一元、加减、乘除等规则分别写成复合记录；图文版把剪枝和非剪枝分支展开，原始共9条，7条通过引文校验。",
         "细粒度展开不保证规则本身的适用前提完整。例如表2对cos和零值语义的对应仍需澄清，图像没有自动消除这个问题。"),
        ("AD反向传播",
         "历史和当前文字版都提出了AD机制，但其地图引文未全部匹配，因而整项未进入自动拆解。图文版选择了可匹配的短引文，并生成3条行为。",
         "文字输入本身已包含AD段落。这主要显示引文选择和拆解路径的变化，尚不能证明只有图像才让模型发现AD。3条中仍有复合公式和前提需要检查。"),
        ("Sparse Tensor Core策略",
         "当前文字版的地图候选未通过引文校验；图文版地图通过，并提出“分解”和“两个部分分别用不同kernel执行”三条行为。",
         "图文版三条行为全部被同一严格校验器拒收。NFKC与断词诊断可帮助解释ﬁrst/first和decom-换行pose的差异；当前冻结结果保留为未决，未事后放宽规则重算。"),
        ("Artifact步骤的边界",
         "图文版新增Artifact reproduction scripts及7条行为，涉及Dockerfile、初始化和run_all脚本。",
         "这些是复跑流程，不能直接当成新增研究机制。图文版93条通过记录中包含这7条，因此总量增加不能直接解释为更全面的系统机制拆解。"),
        ("仍然遗漏的反馈循环",
         "历史地图明确列出稀疏探索反馈循环；这次文字版和图文版地图都没有独立列出它。",
         "同一路由和温度0仍出现输出变化。一次对照不足以给出视觉输入必然提高完整性的结论。"),
    ]
    case_html = "".join(f'<article class="case"><h3>{escape(title)}</h3><p>{escape(observation)}</p>'
                        f'<p class="caution">{escape(boundary)}</p></article>' for title, observation, boundary in cases)
    prompts = []
    archives = {}
    for arm_name, directory in [("historical", baseline), ("text", run / "text-control"), ("vision", run / "vision")]:
        filenames = sorted(p for p in directory.glob("*.raw.request.json")
                           if re.fullmatch(r"(map|M\d{2})\.raw\.request\.json", p.name))
        filenames += sorted(p for p in directory.glob("*.raw.json")
                            if re.fullmatch(r"(map|M\d{2})\.raw\.json", p.name))
        for path in filenames:
            archives[arm_name + "/" + path.name] = read_json(path)
        key = arm_name + "/map.raw.json"
        request_key = arm_name + "/map.raw.request.json"
        prompts.append(
            f'<details><summary>{arm_name} · 机制地图实际请求与原始返回</summary>'
            f'<h4>实际system prompt</h4><pre>{escape(read_json(directory / "map.raw.request.json")["prompt"])}</pre>'
            f'<h4>原样返回文本</h4><pre>{escape(read_json(directory / "map.raw.json")["choices"][0]["message"]["content"])}</pre>'
            f'<button class="download" data-key="{request_key}">下载请求记录</button>'
            f'<button class="download" data-key="{key}">下载完整响应</button></details>')
    downloads = "".join(f'<button class="download" data-key="{escape(key)}">{escape(key)}</button>' for key in archives)
    diagnostic_html = []
    for name in columns:
        parts = []
        for row in diagnostics[name]:
            checks = "".join(f'<li>PDF p.{e["page"]} · 规范化后匹配 {e["normalized_text_match"]}'
                             f' · 短于12字符 {e["shorter_than_validator_minimum"]}'
                             f'<blockquote>{escape(e["quote"])}</blockquote></li>' for e in row["evidence"])
            parts.append(f'<details><summary>{row["mechanism"]}-B{row["index"]:02d} · {escape(row["reason"])}</summary>'
                         f'<p>{escape(row["behavior"])}</p><ul>{checks}</ul></details>')
        diagnostic_html.append(f'<h3>{name}</h3>' + ("".join(parts) or "<p>无行为引文拒收。</p>"))
    css = """
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:80px}
body{margin:0;background:#faf7ef;color:#203348;font:15px/1.8 "IBM Plex Sans","PingFang SC",sans-serif}
header{background:#15283f;color:#f6f2e8;padding:28px max(24px,calc((100vw - 1260px)/2))}
header p{color:#c3cdd6}h1{font:400 clamp(30px,4vw,48px)/1.3 Lora,serif;margin:12px 0}
nav{position:sticky;top:0;background:#f6f2e8;border-bottom:1px solid #d9d1c1;z-index:5;overflow:auto;white-space:nowrap;padding:14px 24px}
nav a{margin-right:24px;color:#354e67;font-size:13px}main{max-width:1310px;margin:auto;padding:28px}
section{margin:0 0 32px;padding:24px;background:#fffdf8;border:1px solid #ddd6c9;border-radius:7px}
h2{font-size:24px;margin:0 0 16px}h3{font-size:17px}.intro{max-width:1000px}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;border-bottom:1px solid #ddd6ca;padding:12px;vertical-align:top}
th{font-weight:500}td{overflow-wrap:anywhere}td p{margin:8px 0}.table-scroll{overflow:auto}
.mechanism-table{min-width:1020px;table-layout:fixed}.mechanism-table th{width:11%}.mechanism-table td{width:29.6%;font-size:13px}
.id,.meta{font-size:11px;color:#76808b}.badge{display:inline-block;font-size:11px;background:#e4eee6;color:#395b45;padding:3px 7px;border-radius:3px}.warn{background:#f4e2d5;color:#80513d}
.absent{color:#8c8c8c}details{padding:10px 0;border-top:1px solid #e2dacc}summary{cursor:pointer;font-size:13px}
blockquote{margin:8px 0;background:#f0ece2;border-left:3px solid #b3a58b;padding:8px 12px;white-space:pre-wrap;overflow-wrap:anywhere}
.case{padding:14px 18px;border-left:3px solid #9eadd0;background:#edf1f6;margin:14px 0}.case h3{margin:0 0 8px}.caution{color:#675443;border-top:1px solid #d6cebf;padding-top:10px}
.note{padding:14px 18px;background:#efe9dc;border-left:3px solid #ae9973}.gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
figure{margin:0}img{max-width:100%;height:auto}figcaption{font-size:12px;color:#75808a}
pre{background:#15283f;color:#e8edf3;white-space:pre-wrap;overflow-wrap:anywhere;max-height:500px;overflow:auto;padding:18px;font:12px/1.8 monospace}
button{font:inherit;cursor:pointer}.download{font-size:12px;padding:6px 10px;background:#f0ece2;border:1px solid #cfc4ae;border-radius:4px;margin:5px 8px 5px 0;overflow-wrap:anywhere}
.page-button{background:none;border:0;border-bottom:1px dotted #6c8198;color:#4d6b8a;font-size:12px}
a{color:#365d80}.methods{display:grid;grid-template-columns:1fr 1fr;gap:20px}.methods>div{min-width:0}.hash{overflow-wrap:anywhere}
dialog{border:0;padding:0;max-width:min(1100px,96vw);max-height:94vh;background:#fff}
dialog::backdrop{background:#102137b8}.modalbar{position:sticky;top:0;background:#15283f;color:white;display:flex;justify-content:space-between;padding:12px 18px}.modalbar button{background:#334b66;color:white;border:1px solid #7c8a9d;padding:4px 12px}
@media(max-width:800px){main{padding:15px}section{padding:18px}header{padding:24px 20px}.gallery,.methods{grid-template-columns:1fr}table{font-size:12px}td,th{padding:7px}nav{padding:12px 15px}}
"""
    font_path = baseline.parent / "sparta-annotated-reading/fonts.css"
    fonts = font_path.read_text() if font_path.exists() else ""
    page_json = json.dumps(page_images).replace("<", "\u003c")
    archive_json = json.dumps(archives, ensure_ascii=False).replace("<", "\u003c")
    html = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SparTA · 文字与图文拆解对照 · CS6223</title><link rel="icon" href="data:,"><style>{fonts}{css}</style>
<header><p>NUS CS6223 · ADVANCED TOPICS IN SOFTWARE TESTING</p><h1>SparTA · 文字与图文拆解对照</h1>
<p class="intro">同一篇论文、同一prompt、同一模型路由，在相同逐页文字上增加21页原PDF图像。保留历史结果，并增加当前文字版以观察重复生成带来的变化。</p></header>
<nav><a href="#summary">结果概览</a><a href="#cases">一起检查差异</a><a href="#mechanisms">逐机制与行为</a><a href="#citations">引用诊断</a><a href="#trace">真实请求与返回</a><a href="#methods">对照条件</a></nav>
<main><p><a href="sparta-independent-k2.html">最新流程：k=2 独立机制发现、合并与旧版对比（含实际 prompts）</a></p><section id="summary"><h2>结果概览</h2>
<table><thead><tr><th>统计项</th><th>历史文字版</th><th>当前文字版</th><th>当前图文版</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
<p class="note">“引文通过”只表示匹配了提取文本。图文版新增artifact步骤、仍有复合行为及引用格式差异，因此机制数和行为数不能直接当成准确率或完整率。</p>
<p>两次当前机制地图均由{escape(summary["vision"]["actual_model"])}返回。图文版机制地图的usage明确记录了{image_tokens:,}个图像token，确认21页图像进入推理输入。历史主跑使用86条行为，不混入后续人工补引文或复核得到的102／181条草稿。</p>
<a href="sparta-annotated-reading.html">打开原论文双栏批注精读页</a></section>
<section id="cases"><h2>先检查这些具体差异</h2>{case_html}<div class="gallery">{"".join(crops)}</div></section>
<section id="mechanisms"><h2>逐机制与行为对照</h2><p>主题行由Codex依据原文及返回内容对齐，待团队确认。M编号在各次运行中重新分配，不能只按编号横向比较。展开可见所有原始行为及被拒收的引文。</p>
<div class="table-scroll"><table class="mechanism-table"><thead><tr><th>对齐主题</th><th>历史文字版</th><th>当前文字版</th><th>当前图文版</th></tr></thead><tbody>{"".join(theme_rows)}</tbody></table></div></section>
<section id="citations"><h2>引用诊断</h2><p>保留原来的严格判定。下方额外做NFKC字符规范化、合并行末断词和空白的诊断，帮助识别ﬁrst/first、decom-换行pose等差异。诊断没有将记录重新接纳，也不能替代语义核对。</p>{"".join(diagnostic_html)}</section>
<section id="trace"><h2>真实prompt、请求和返回</h2><p>图文请求记录保存原始文字、图像顺序、文件路径及SHA256。页面原图已经内嵌，可点击引文页码检查。模型请求中的图像数据可由这些图像文件重建。</p>{"".join(prompts)}
<details><summary>下载各批次实际请求与响应</summary>{downloads}</details></section>
<section id="methods"><h2>对照条件与边界</h2><div class="methods"><div><h3>保持一致</h3><ul><li>同一个PDF及历史pypdf逐页文本。</li><li>原始MAP和SPLIT prompt不变，temperature=0，max_tokens=6500，reasoning_effort=none。</li><li>机制每三项一批，同一严格引文校验和20条行为接收上限。</li><li>当前两种输入条件均重跑机制地图和行为拆解。</li></ul></div>
<div><h3>明确变化</h3><ul><li>图文版在同一文字输入后，按物理页序追加21张1224×1584彩色页面图像。</li><li>重放接收上限统一设为60项机制，避免旧的18项预算门槛丢弃新增候选；没有改变生成prompt。历史按同一门槛重校验仍为16项。</li><li>两版机制地图不同，后续批次的具体内容随之变化；这是端到端流程对照。</li><li>单篇、每个条件一次生成，没有独立人工金标。历史与当前文字版的变化显示仍存在生成差异。</li></ul></div></div>
<p class="hash">PDF SHA256 {protocol["pdf_sha256"]}</p><p>实际输入、图像hash、各阶段失败状态、用量和实现版本保存在本地运行目录。实验读取论文，未读取目标系统源码或执行目标系统。</p></section></main>
<dialog id="source-dialog" aria-label="PDF原页对照"><div class="modalbar"><span id="page-label"></span><button id="close-page">关闭</button></div><img id="source-page" alt="原始PDF页面"></dialog>
<script id="pages" type="application/json">{page_json}</script><script id="archives" type="application/json">{archive_json}</script>
<script>
const pages=JSON.parse(document.getElementById('pages').textContent);
const archives=JSON.parse(document.getElementById('archives').textContent);
const dialog=document.getElementById('source-dialog');
document.querySelectorAll('[data-page]').forEach(button=>{{
 button.addEventListener('click',()=>{{
  const page=button.dataset.page;
  document.getElementById('page-label').textContent='PDF p.'+page;
  document.getElementById('source-page').src=pages[page];
  dialog.showModal();
 }});
}});
document.getElementById('close-page').addEventListener('click',()=>dialog.close());
document.querySelectorAll('[data-key]').forEach(button=>{{
 button.addEventListener('click',()=>{{
  const key=button.dataset.key;
  const blob=new Blob([JSON.stringify(archives[key],null,2)],{{type:'application/json;charset=utf-8'}});
  const url=URL.createObjectURL(blob);
  const link=document.createElement('a');
  link.href=url;link.download=key.replaceAll('/','-');link.click();
  setTimeout(()=>URL.revokeObjectURL(url),5000);
 }});
}});
</script></html>"""
    output.write_text(html, encoding="utf-8")
    write_json(run / "report-manifest.json", dict(output=str(output.resolve()), sha256=file_sha256(output),
               bytes=output.stat().st_size, theme_alignment="Codex source-based review; pending team confirmation",
               mechanism_table_themes=len(themes), embedded_pdf_pages=len(page_images),
               raw_archive_count=len(archives), protocol_sha256=file_sha256(run / "protocol.json")))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(output.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report(args.run, args.baseline, args.output)
