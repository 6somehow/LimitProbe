"""Self-contained, offline human-review page; no methods or verdicts are injected."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

LABELS = {
    "scope_relevance": "论文范围相关性", "code_alignment": "代码条件对齐",
    "input_concreteness": "输入与前提具体性", "strategy_appropriateness": "策略适当性",
    "observation_clarity": "观察目标清晰度", "oracle_design": "拟议 Oracle 合理性",
    "strategy": "测试策略", "inputs": "具体输入 / 配置", "preconditions": "前置条件",
    "target_condition": "目标代码条件", "observation": "拟观察行为",
    "paper_evidence": "论文证据：页码、原文与来源", "code_evidence": "代码证据：版本、行号与原文",
    "oracle": "拟议 Oracle（未运行验证）", "scope_status": "生成器声明的范围（仍须独立核查）",
    "limitations": "已知限制 / 未决项",
}
CRITERIA = tuple(key for key in LABELS if key in {
    "scope_relevance", "code_alignment", "input_concreteness", "strategy_appropriateness",
    "observation_clarity", "oracle_design",
})


def render_value(value) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return '<span class="muted">未提供；不能由此自动判定不合格</span>'
    if isinstance(value, dict):
        return '<dl>' + ''.join(
            '<dt>' + html.escape(str(key)) + '</dt><dd>' + render_value(item) + '</dd>'
            for key, item in value.items()
        ) + '</dl>'
    if isinstance(value, list):
        return '<ol>' + ''.join('<li>' + render_value(item) + '</li>' for item in value) + '</ol>'
    text = str(value)
    if text.startswith(("https://", "http://")) and not any(char.isspace() for char in text):
        return '<a target="_blank" rel="noopener noreferrer" href="' + html.escape(text, quote=True) + '">' + html.escape(text) + '</a>'
    if text.startswith("/") and "\n" not in text:
        href = "file://" + quote(text, safe="/:@")
        return '<a href="' + html.escape(href, quote=True) + '">' + html.escape(text) + '</a>'
    return '<pre>' + html.escape(text) + '</pre>'


def _details(label: str, content: str) -> str:
    return '<details><summary>' + html.escape(label) + '</summary><div class="detail-body">' + content + '</div></details>'


def _raw_json(value) -> str:
    return '<pre class="raw-json">' + html.escape(json.dumps(value, ensure_ascii=False, indent=2, default=str)) + '</pre>'


def _quote(value) -> str:
    if not isinstance(value, str) or not value:
        return render_value(value)
    return '<blockquote><pre>' + html.escape(value) + '</pre></blockquote>'


def _fields(value: dict, names: dict[str, str]) -> str:
    return '<dl class="compact-fields">' + ''.join(
        '<dt>' + html.escape(label) + '</dt><dd>' + render_value(value[key]) + '</dd>'
        for key, label in names.items() if key in value
    ) + '</dl>'


def _line_label(value: dict) -> str:
    start = value.get("line_start", value.get("line"))
    end = value.get("line_end", start)
    if start is None:
        return "行号未提供"
    return "行 " + str(start) + ("–" + str(end) if end is not None and end != start else "")


def _source_context(value) -> str:
    if not isinstance(value, list):
        return render_value(value)
    snippets = []
    for item in value:
        if not isinstance(item, dict):
            snippets.append(render_value(item))
            continue
        heading = str(item.get("path", "文件未提供")) + " · " + _line_label(item)
        snippets.append('<div class="quotation"><p class="citation">' + html.escape(heading)
                        + '</p>' + _fields(item, {"kind": "片段类型", "contract_kind": "契约候选类型",
                                               "applicability_status": "适用性状态"})
                        + _quote(item.get("quote")) + _fields(item, {"limitations": "片段限制"})
                        + _details("片段完整元数据", _raw_json(item)) + '</div>')
    return ''.join(snippets) or render_value(value)


def _target_condition(value) -> str:
    if not isinstance(value, dict) or not value:
        return render_value(value)
    primary = {"path": "文件", "symbol": "符号 / 函数", "expression": "原子条件",
               "test_expression": "完整条件", "variable": "代码变量 / 表达式",
               "value_type": "值类型", "input_binding": "输入映射",
               "activation_preconditions": "激活其他条件的前提", "limitations": "目标条件限制"}
    visible = dict(value)
    if value.get("test_expression") == value.get("expression"):
        visible.pop("test_expression", None)  # Exact duplicate remains in raw JSON.
    rendered = '<p class="citation">' + html.escape(_line_label(value)) + '</p>' + _fields(visible, primary)
    context = value.get("source_context")
    if context:
        rendered += _details("邻近源码与契约候选（适用性须核查）", _source_context(context))
    return rendered + _details("完整目标条件 JSON（含全部引用与元数据）", _raw_json(value))


def _paper_evidence(value) -> str:
    if not isinstance(value, (dict, list)) or not value:
        return render_value(value)
    citations = [value] if isinstance(value, dict) else value
    rendered = []
    for citation in citations:
        if not isinstance(citation, dict):
            rendered.append(render_value(citation))
            continue
        page = "页码未提供" if citation.get("page") is None else "第 " + str(citation["page"]) + " 页"
        rendered.append('<div class="quotation"><p class="citation">' + html.escape(page) + '</p>'
                        + _quote(citation.get("quote"))
                        + _details("完整论文引用 / 校验元数据", _raw_json(citation)) + '</div>')
    return ''.join(rendered)


def _code_evidence(value, reference) -> str:
    if not isinstance(value, (dict, list)) or not value:
        return render_value(value)
    citations = [value] if isinstance(value, dict) else value
    rendered = []
    for citation in citations:
        if not isinstance(citation, dict):
            rendered.append(render_value(citation))
            continue
        location = str(citation.get("path", "文件未提供")) + " · " + _line_label(citation)
        commit = citation.get("commit")
        if not commit and isinstance(reference, dict):
            commit = reference.get("commit", reference.get("repository_commit"))
        version = '<p class="citation">记录版本 <code>' + html.escape(str(commit)) + '</code></p>' if commit else ''
        rendered.append('<div class="quotation"><p class="citation">' + html.escape(location) + '</p>'
                        + version + _quote(citation.get("quote"))
                        + _details("完整代码引用 / 校验元数据", _raw_json(citation)) + '</div>')
    return ''.join(rendered)


def _oracle(value) -> str:
    if not isinstance(value, dict) or not value:
        return render_value(value)
    fields = {"type": "判定类型", "status": "方案状态", "relation": "拟议判定关系",
              "preconditions": "Oracle 前提", "limitations": "Oracle 限制"}
    rendered = _fields(value, fields)
    if "evidence" in value:
        rendered += _details("Oracle 证据（展开核查）", render_value(value["evidence"]))
    metadata = {key: item for key, item in value.items() if key not in {*fields, "evidence"}}
    if metadata:
        rendered += _details("Oracle 其他原始字段", _raw_json(metadata))
    return rendered + _details("完整 Oracle JSON", _raw_json(value))


def _section(field: str, content: str) -> str:
    return '<section><h3>' + LABELS[field] + '</h3>' + content + '</section>'


def render_review_html(items: list[dict], run_id: str) -> str:
    cards = []
    for index, item in enumerate(items, 1):
        rid = html.escape(item["review_id"], quote=True)
        candidate = item["candidate"]
        reference = item.get("source_reference")
        summary = _section("target_condition", _target_condition(candidate.get("target_condition")))
        summary += _section("observation", render_value(candidate.get("observation")))
        content = '<div class="spec-grid">' + _section("inputs", render_value(candidate.get("inputs")))
        content += _section("preconditions", render_value(candidate.get("preconditions"))) + '</div>'
        content += _section("oracle", _oracle(candidate.get("oracle")))
        content += _section("limitations", render_value(candidate.get("limitations")))
        content += _section("paper_evidence", _paper_evidence(candidate.get("paper_evidence")))
        content += _section("code_evidence", _code_evidence(candidate.get("code_evidence"), reference))
        content += _details("核对全文 / 仓库来源", render_value(reference))
        other = {key: value for key, value in candidate.items() if key not in LABELS}
        if other:
            content += _details("其他候选原始字段", _raw_json(other))
        scores = ''.join(
            '<label>' + LABELS[field] + '<select data-field="' + field + '">'
            '<option value="">待评（空白）</option><option value="yes">yes — 支持</option>'
            '<option value="no">no — 不支持</option><option value="unknown">unknown — 无法判定</option>'
            '</select></label>' for field in CRITERIA
        )
        cards.append(
            '<article class="card" data-review-id="' + rid + '"><div class="heading"><h2>候选 '
            + str(index) + ' · ' + html.escape(item["paper_id"]) + '</h2><span class="badge">未执行真实测试</span></div>'
            '<p class="muted">匿名编号 ' + rid + '</p>'
            '<div class="candidate-meta">' + _fields(candidate, {"strategy": LABELS["strategy"], "scope_status": LABELS["scope_status"]})
            + '</div><div class="candidate-summary">' + summary + '</div>'
            '<div class="review-controls"><h3>独立评分</h3><p class="muted">请核对下方规格与展开的原文后填写；空白保持待审。</p>'
            '<div class="scores">' + scores
            + '</div><label>审查理由与依据（请记录页码 / 文件 / 行）<textarea data-field="reason" rows="3"></textarea></label></div>'
            '<div class="evidence">' + content + '</div></article>'
        )
    payload = json.dumps({"run_id": run_id, "review_ids": [item["review_id"] for item in items], "criteria": list(CRITERIA)}, ensure_ascii=False).replace("<", "\\u003c")
    page = r'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PaperProbe · 匿名人工审查</title><style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#182b39;background:#f4f6f8}body{max-width:1100px;margin:32px auto;padding:0 20px}h1{margin-bottom:8px}h2{font-size:21px}h3{font-size:15px;color:#355267;margin:16px 0 6px}.toolbar,.card{background:white;border:1px solid #dbe3e9;border-radius:14px;padding:22px;margin:18px 0}.toolbar{position:sticky;top:8px;z-index:1;box-shadow:0 4px 16px #18304112}.heading{display:flex;justify-content:space-between;gap:16px;align-items:center}.badge{color:#6c4300;background:#fff1ce;padding:6px 10px;border-radius:20px;font-size:12px;white-space:nowrap}.muted{color:#607581;font-size:13px}.scores{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;border-top:1px solid #e2e8ed;margin-top:18px;padding-top:16px}label{display:block;font-size:14px}select,input,textarea{display:block;width:100%;box-sizing:border-box;margin:6px 0 12px;border:1px solid #b8c6d0;border-radius:7px;padding:9px;background:white;font:inherit}textarea{resize:vertical}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,monospace;margin:4px 0}dl{display:grid;grid-template-columns:minmax(90px,160px) 1fr;margin:6px 0;gap:6px}dt{font-size:13px;color:#607581}dd{margin:0;min-width:0}a{color:#136caf;overflow-wrap:anywhere}details{background:#f7fafc;padding:12px;border-radius:9px}summary{cursor:pointer;font-weight:600}button{padding:9px 14px;border:0;border-radius:7px;background:#1c637d;color:white;font:inherit;margin:4px;cursor:pointer}.actions{display:flex;flex-wrap:wrap;align-items:center}#importFile{max-width:260px;font-size:12px}#progress{font-size:13px}#message{font-size:13px;color:#355267}ol{padding-left:20px}@media(max-width:700px){.scores{grid-template-columns:1fr}.heading{display:block}dl{grid-template-columns:1fr}.toolbar{position:static}}
.candidate-meta{background:#f7fafc;border-radius:8px;padding:8px 12px}.candidate-meta dl{margin:0}.candidate-summary{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:20px}.candidate-summary section,.spec-grid section{min-width:0}.spec-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.citation{font-size:13px;color:#355267;margin:8px 0;overflow-wrap:anywhere}.quotation{margin:10px 0 16px}blockquote{margin:6px 0;padding:8px 12px;border-left:3px solid #bed2df;background:#fafcfd}.review-controls{background:#f7fafc;border:1px solid #dbe3e9;border-radius:10px;padding:0 14px 10px;margin:16px 0}.review-controls .scores{border-top:0;margin-top:0;padding-top:0}.review-controls textarea{margin-bottom:0}details{margin:8px 0;padding:9px 12px}summary{font-size:13px}.detail-body{padding-top:8px}.raw-json{font-size:12px}.evidence-links{font-size:13px;margin-bottom:10px}.compact-fields{grid-template-columns:minmax(95px,145px) minmax(0,1fr)}.compact-fields pre{margin:0}.evidence>section{margin-top:16px}@media(max-width:850px){.candidate-summary,.spec-grid{grid-template-columns:1fr;gap:0}}@media(max-width:700px){.review-controls .scores{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:420px){.review-controls .scores,.compact-fields{grid-template-columns:1fr}}
</style><h1>候选测试 · 匿名独立审查</h1>
<p>核对原论文与固定版本代码后填写。评价的是候选规格和拟议判定方案；静态定位、分支描述和 Oracle 文字均不证明真实执行或正确性。</p>
<p class="muted">缺少论文引文不能直接判相关性失败：仍应对照全文判断。请独立完成后提交；不要查看 private 方法映射。原文措辞和证据数量可能暴露方法，盲审存在这种限制。</p>
<div class="toolbar"><label>你的 reviewer_id（两名审查者必须不同）<input id="reviewer" placeholder="例如 reviewer-A" autocomplete="off"></label>
<div class="actions"><button id="exportJson">导出 JSON 审查记录</button><button id="exportCsv">导出 CSV</button><label>导入上次 JSON<input type="file" id="importFile" accept=".json"></label></div>
<p id="progress"></p><p id="message">记录仅保存在当前浏览器；请导出文件交给评估模块，不会自动上传。</p></div>
__CARDS__<script id="review-data" type="application/json">__PAYLOAD__</script><script>
"use strict";
const cfg=JSON.parse(document.getElementById("review-data").textContent), fields=[...cfg.criteria,"reason"], cards=[...document.querySelectorAll(".card")], reviewer=document.getElementById("reviewer"), storagePrefix="paperprobe-review:"+cfg.run_id+":", sessionKey=storagePrefix+"active";let activeReviewer="";
const message=text=>document.getElementById("message").textContent=text;
function collect(){return cards.map(card=>{const row={review_id:card.dataset.reviewId,reviewer_id:activeReviewer};for(const field of fields)row[field]=card.querySelector('[data-field="'+field+'"]').value;return row})}
function progress(){const rows=collect(), full=rows.filter(row=>cfg.criteria.every(field=>row[field])).length, started=rows.filter(row=>cfg.criteria.some(field=>row[field])).length;document.getElementById("progress").textContent=`${rows.length} 条候选 · ${full} 条六项填写完整 · ${started} 条已开始；空白保持待审。`}
function save(){progress();try{localStorage.setItem(storagePrefix+activeReviewer,JSON.stringify({run_id:cfg.run_id,reviewer_id:activeReviewer,reviews:collect()}));localStorage.setItem(sessionKey,activeReviewer)}catch(error){message("浏览器不允许本地保存；请导出文件保存草稿。")}}
function apply(data){if(!data||data.run_id!==cfg.run_id||!Array.isArray(data.reviews))throw Error("run_id 或 reviews 不匹配");const map=new Map(),valid=new Set(cfg.review_ids);for(const row of data.reviews){if(!row||!valid.has(row.review_id)||map.has(row.review_id))throw Error("未知或重复匿名编号");for(const field of cfg.criteria)if(!["","yes","no","unknown"].includes(row[field]??""))throw Error("非法评分");map.set(row.review_id,row)}const ids=[...new Set(data.reviews.map(row=>row.reviewer_id).filter(Boolean))];if(ids.length>1)throw Error("页面只可导入一位审查者的记录");if(data.reviewer_id&&ids.length&&data.reviewer_id!==ids[0])throw Error("reviewer_id 与记录身份冲突");activeReviewer=data.reviewer_id||ids[0]||"";reviewer.value=activeReviewer;for(const card of cards){const row=map.get(card.dataset.reviewId);for(const field of fields)card.querySelector('[data-field="'+field+'"]').value=row?.[field]??""}progress()}
function switchReviewer(){const next=reviewer.value.trim();if(next===activeReviewer)return;save();activeReviewer=next;for(const card of cards)for(const field of fields)card.querySelector('[data-field="'+field+'"]').value="";try{const saved=localStorage.getItem(storagePrefix+activeReviewer);if(saved)apply(JSON.parse(saved))}catch(error){message("无法读取此审查者的草稿。")}reviewer.value=activeReviewer;save();message("已切换审查者；该身份独立保存，不继承其他人的评分。")}
function download(type){switchReviewer();const rows=collect();if(rows.some(row=>cfg.criteria.some(field=>row[field])||row.reason)&&!reviewer.value.trim()){message("已有评分或理由时，请先填写 reviewer_id。");reviewer.focus();return}const csvFields=["review_id","reviewer_id",...fields], escape=v=>'"'+String(v??"").replaceAll('"','""')+'"';const text=type==="json"?JSON.stringify({schema_version:"1.0",run_id:cfg.run_id,reviews:rows},null,2):[csvFields.map(escape).join(","),...rows.map(row=>csvFields.map(field=>escape(row[field])).join(","))].join("\r\n");const url=URL.createObjectURL(new Blob([text],{type:type==="json"?"application/json":"text/csv;charset=utf-8"})),a=document.createElement("a");a.href=url;a.download="reviews-"+(reviewer.value.trim()||"draft").replace(/[^a-zA-Z0-9_-]/g,"_")+"."+type;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message("已导出；请保留文件。评估模块会验证记录并保留待审与分歧。");save()}
document.addEventListener("input",event=>{if(event.target!==reviewer)save()});document.addEventListener("change",event=>{if(event.target!==reviewer&&event.target.id!=="importFile")save()});reviewer.onchange=switchReviewer;document.getElementById("exportJson").onclick=()=>download("json");document.getElementById("exportCsv").onclick=()=>download("csv");document.getElementById("importFile").onchange=async event=>{try{const file=event.target.files[0];if(file){apply(JSON.parse(await file.text()));save();message("已导入草稿。")}}catch(error){message("导入失败："+error.message)}};
try{activeReviewer=localStorage.getItem(sessionKey)||"";reviewer.value=activeReviewer;const saved=localStorage.getItem(storagePrefix+activeReviewer);if(saved)apply(JSON.parse(saved))}catch(error){message("无法恢复本地草稿；可从导出的 JSON 导入。")};progress();
</script></html>'''
    return page.replace("__CARDS__", ''.join(cards) if cards else '<p>本 run 没有候选；任务仍保留在 manifest，yield 为 0。无需填写虚构审查。</p>').replace("__PAYLOAD__", payload)
