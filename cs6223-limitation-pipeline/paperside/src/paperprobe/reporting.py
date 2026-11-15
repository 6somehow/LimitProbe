"""Honest status reports for raw generation runs and human-review aggregation."""
from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path

from .review_ui import render_value


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _fraction(value) -> str:
    return "—" if value is None else f"{value:.1%}"


def write_run_report(results: dict, output_path: Path) -> None:
    """Write Chinese Markdown or standalone HTML based on the output extension."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aggregated = isinstance(results.get("methods"), dict)
    run_id = str(results.get("run_id", "unknown"))
    status = results.get("human_review_status", "pending")
    disclaimer = "本报告记录生成、静态定位与人工审查状态。未执行真实被测软件；不能据此声称可执行性、触达、bug 检出或已验证 Oracle。"
    if results.get("backend") in {"heuristic", "deterministic_heuristic"}:
        disclaimer += "此 backend 仅为流程示例，不能充当真实 LLM 方法比较结果。"
    if aggregated:
        methods = results["methods"]
        headers = ["方法", "全部任务", "候选", "确认合格数量下界–上界", "任务完成率下界–上界"]
        rows = [[method, data["task_count"], data["candidate_count"],
                 f'{data["qualified_yield_lower"]}–{data["qualified_yield_upper"]}',
                 f'{_fraction(data["task_completion_lower"])}–{_fraction(data["task_completion_upper"])}']
                for method, data in methods.items()]
        explanation = "上下界保留待审、unknown 与分歧；它们不是置信区间。零输出任务保留在任务分母中。前五项共同决定规格质量，Oracle 设计单独统计。"
    else:
        headers = ["方法", "全部任务", "原始候选", "生成状态", "人工审查"]
        rows = []
        for method in results.get("methods", []):
            tasks = [task for task in results.get("tasks", []) if task.get("method") == method]
            rows.append([method, len(tasks), sum(len(task.get("candidates", [])) for task in tasks),
                         json.dumps(dict(Counter(task.get("status", "unknown") for task in tasks)), ensure_ascii=False), "pending"])
        explanation = "原始候选和静态检查数量不是人工认定的合格数量。人工审查尚未完成，当前不能判断方法优劣。"
    markdown = [f"# PaperProbe 运行记录：{_cell(run_id)}", "", disclaimer, "",
                f"人工审查状态：`{_cell(status)}`。Backend：`{_cell(results.get('backend', 'unknown'))}`；模式：`{_cell(results.get('mode', 'unknown'))}`。", "", explanation, "",
                "| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    markdown.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    details_html = []
    references = results.get("metadata", {}).get("paper_references", {})
    if references:
        markdown.extend(["", "## 论文与固定版本仓库", ""])
        for paper_id, reference in references.items():
            markdown.append(f"- **{_cell(paper_id)}**")
            if isinstance(reference, dict):
                for key, value in reference.items():
                    if isinstance(value, str) and (value.startswith(("https://", "http://", "/"))):
                        target = "<" + value + ">" if " " in value else value
                        markdown.append(f"  - {key}: [{_cell(value)}]({target})")
                    else:
                        markdown.append(f"  - {key}: {_cell(value)}")
        details_html.append('<h2>论文与固定版本仓库</h2>' + render_value(references))
    if aggregated:
        markdown.extend(["", "## 人工各项判定", "", "yes / no 为有足够独立审查者支持的判定；unknown、conflict、pending 分别保留。"])
        for method, data in methods.items():
            markdown.extend(["", f"### {_cell(method)}", "", "```json", json.dumps(data["criteria_counts"], ensure_ascii=False, indent=2), "```"])
            details_html.append('<h3>' + html.escape(method) + '</h3>' + render_value(data["criteria_counts"]))
        markdown.extend(["", "## 任务级原始计数", "", "| Task | 方法 | 生成状态 | 候选 | 合格下界–上界 |", "| --- | --- | --- | --- | --- |"])
        for task in results["tasks"]:
            markdown.append("| " + " | ".join(_cell(value) for value in [task["task_id"], task["method"], task["generation_status"], task["candidate_count"], f'{task["qualified_yield_lower"]}–{task["qualified_yield_upper"]}']) + " |")
        if not results.get("human_conclusions_available"):
            markdown.extend(["", "人工判断尚有待审、unknown 或分歧；不要将数量下界解读为所有未决候选不合格，也不能据此宣布方法胜出。"])
        markdown.extend(["", "## 双人审查与配对结果", "", "```json", json.dumps({"agreement": results["pairwise_agreement"], "paired_yield_differences": results["paired_yield_differences"]}, ensure_ascii=False, indent=2), "```", "", "## 静态检查（非人工评分）", "", "原始机械检查单列保存在 evaluation.json 的 static_checks；未转换为任何人工评分。"])
        details_html.append('<h3>双人审查与配对结果</h3>' + render_value({"agreement": results["pairwise_agreement"], "paired_yield_differences": results["paired_yield_differences"]}))
    else:
        for task in results.get("tasks", []):
            markdown.extend(["", f"## {_cell(task.get('paper_id'))} / {_cell(task.get('method'))}", "", f"生成状态：`{_cell(task.get('status'))}`；候选：{len(task.get('candidates', []))}。"])
            if task.get("error"):
                markdown.extend(["", "```text", str(task["error"]), "```"])
            for candidate in task.get("candidates", []):
                evidence = {key: candidate.get(key) for key in ("strategy", "inputs", "target_condition", "paper_evidence", "code_evidence", "oracle", "checks")}
                markdown.extend(["", f"### {_cell(candidate.get('candidate_id'))}", "", "证据原文、版本与拟议方案：", "", "```json", json.dumps(evidence, ensure_ascii=False, indent=2), "```"])
                details_html.append('<details><summary>' + html.escape(str(candidate.get("candidate_id"))) + '</summary>' + render_value(evidence) + '</details>')
    markdown.extend(["", "限制：匿名格式仍可能从内容推测来源方法；自动去重仅处理完全重复字段。团队需独立核对原论文和固定版本代码。", ""])
    if output_path.suffix.lower() == ".html":
        table = '<table><thead><tr>' + ''.join('<th>' + html.escape(header) + '</th>' for header in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + html.escape(str(value)) + '</td>' for value in row) + '</tr>' for row in rows) + '</tbody></table>'
        page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PaperProbe 运行记录</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:1000px;margin:40px auto;padding:0 20px;color:#213547}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccd6dc;padding:10px;text-align:left}th{background:#eff5f7}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.6 monospace}dl{display:grid;grid-template-columns:150px 1fr;gap:6px}dd{margin:0}details{border:1px solid #ccd6dc;padding:14px;border-radius:8px;margin:12px 0}a{color:#176ea1;overflow-wrap:anywhere}.note{background:#fff4d6;padding:14px;border-radius:8px}</style><h1>PaperProbe 运行记录：' + html.escape(run_id) + '</h1><p class="note">' + html.escape(disclaimer) + '</p><p>人工审查：' + html.escape(status) + '</p><p>' + html.escape(explanation) + '</p>' + table + ''.join(details_html) + '<p>原始数据与所有待审项保留在 JSON；本报告不代写 final paper，不填入虚构人工判断。</p></html>'
        output_path.write_text(page, encoding="utf-8")
    else:
        output_path.write_text("\n".join(markdown), encoding="utf-8")
