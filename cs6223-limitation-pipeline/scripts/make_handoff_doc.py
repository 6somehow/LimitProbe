#!/usr/bin/env python3
"""Write results/step4/HANDOFF.md: what the limitations of both sides look like, for Shanghao (steps 5-6).

Generated from results/step4/limitations_for_tests.json, so it stays in sync with every step-4 run:
  python scripts/run_step4.py && python scripts/make_handoff_doc.py
"""
import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATS = ["undisclosed", "contradicts_docs", "stated_differently", "docs_only", "paper_stated", "impl_deviates",
        "not_implemented"]
CAT_ZH = {
    "undisclosed": "代码有这个限制，用户能读到的地方都没写（核心发现）",
    "contradicts_docs": "文档写的和代码行为相反",
    "stated_differently": "文档写了，但边界不同或说得更弱（如“只测过 bf16”vs 代码强制 bf16）",
    "docs_only": "README / 公开 docstring 写了，论文没写",
    "paper_stated": "论文写了，边界和代码一致",
    "impl_deviates": "论文描述了，代码实现得不一样",
    "not_implemented": "论文描述了，代码里没有",
}
WSTATUS = ["solved", "solved_contrast_outside_scope", "trigger_only", "always", "infeasible", "untranslatable",
           "unknown", "no_condition"]
ORACLE = [
    ("reject", "抛异常 / 断言失败", "trigger 上断言抛出指定异常，contrast 上不抛"),
    ("path_change", "换了一条执行路径（回退、换 kernel、换策略）", "path hook：在两条路径的入口打桩，trigger 走限制分支、contrast 不走"),
    ("accuracy", "结果精度变差", "differential：和参考实现比，trigger 上误差超过阈值"),
    ("state", "依赖前几次调用留下的状态", "event_sequence：先按顺序调用把状态弄成 trigger，再检查"),
    ("resource / performance", "内存 / 时间", "resource：测量，对比 contrast"),
    ("other（论文侧几乎全是）", "实现和论文描述不同，没有确定的运行时后果",
     "witness 为 always 时：走到引用代码的任一输入，和论文公式 / 描述做 differential 或 metamorphic 对比；"
     "3a 只做了静态判断，后果未证实"),
]


def side(f: dict) -> str:
    o = {l["origin"] for l in f["limitations"]}
    return "两侧合并" if len(o) == 2 else ("代码侧" if "code" in o else "论文侧")


def short(s: str, n: int = 90) -> str:
    s = " ".join((s or "").split()).replace("|", "\\|")
    return s if len(s) <= n else s[: n - 1] + "…"


def counter_table(rows, cols, get, row_name, col_names=None) -> list[str]:
    out = [f"| {row_name} | " + " | ".join(col_names or cols) + " | 合计 |", "|---" * (len(cols) + 2) + "|"]
    for r, items in rows:
        c = Counter(get(f) for f in items)
        out.append(f"| {r} | " + " | ".join(str(c.get(x, 0)) for x in cols) + f" | {len(items)} |")
    return out


def compact(f: dict) -> str:
    """One finding as trimmed JSON: what Shanghao reads first."""
    keep = {k: f[k] for k in ("finding_id", "category", "priority", "effect_type", "scope_status", "review", "summary")}
    w = {k: v for k, v in f["witness_hint"].items()
         if k in ("kind", "status", "condition", "path_prefix", "aliases", "trigger", "contrast", "atoms", "note",
                  "location", "code_locations", "condition_source", "call_chain_status", "call_chain", "entry_terms",
                  "infeasible_because")}
    if "note" in w:
        w["note"] = short(w["note"], 200)
    if len(w.get("atoms", {})) > 6:  # long atom lists add nothing to an example
        w["atoms"] = f"... {len(w['atoms'])} atoms, see json"
    keep["witness_hint"] = w
    keep["limitations"] = [{"limitation_id": l["limitation_id"], "origin": l["origin"],
                            "condition_text": short(l["condition_text"], 160), "effect_text": short(l["effect_text"], 160),
                            "code_evidence": [f"{c['file']}:{c['line_start']}-{c['line_end'] or c['line_start']}"
                                              for c in l["code_evidence"]][:3],
                            "paper_quote": short(l["paper_evidence"][0]["quote"], 140) if l["paper_evidence"] else None}
                           for l in f["limitations"]]
    keep["verifications"] = [{"result": v["result"], "documented_in": v["documented_in"],
                              "quote": short(v["matching_evidence"][0]["quote"], 120) if v["matching_evidence"] else None}
                             for v in f["verifications"]]
    keep["rationale"] = short(f["rationale"], 300)
    b = f.get("process_confidence")
    if b:
        t, i = b["testability"], b["importance"]
        keep["process_confidence"] = {"checks": {k: c["status"] for k, c in b["checks"].items()},
                                      "found_in_runs": b["repeats"]["extraction_runs"].get("found_in"),
                                      "ceiling": t.get("ceiling") or t.get("expect_not_run"),
                                      "limited_by": t.get("limited_by"),
                                      "decision_on": i["path"].get("decision_on"),
                                      "guarded_statements": i["impact"].get("guarded_statements"),
                                      "note": "... evidence per check and the full numbers are in the json"}
    return json.dumps(keep, ensure_ascii=False, indent=1)


def pick(fs, pred, used: set):
    """First finding that matches, not used before, with a short witness (readable as an example)."""
    for limit in (900, 10 ** 9):
        for f in fs:
            if f["finding_id"] not in used and pred(f) and len(json.dumps(f["witness_hint"])) <= limit:
                used.add(f["finding_id"])
                return f
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="results/step4/limitations_for_tests.json")
    ap.add_argument("--out", default="results/step4/HANDOFF.md")
    a = ap.parse_args()
    data = json.loads((ROOT / a.src).read_text())
    fs = data["findings"]
    papers = list(dict.fromkeys(f["artifact_id"] for f in fs))
    by_paper = [(p, [f for f in fs if f["artifact_id"] == p]) for p in papers]
    by_side = [(s, [f for f in fs if side(f) == s]) for s in ("代码侧", "论文侧", "两侧合并")]
    n_lim = sum(len(f["limitations"]) for f in fs)
    L = []
    scope = "、".join(papers) if len(papers) <= 6 else f"{len(papers)} 篇"
    L += [f"# 步骤 4 交接：两侧 limitation 一览（给 Shanghao；{scope}）", "",
          f"> 自动生成（`scripts/make_handoff_doc.py`），数据来自 `{a.src}`。schema {data['schema_version']}，"
          f"witness 格式 {data['witness_format']}。方法细节见 `docs/09_step4_findings.md`。", "",
          "## 一句话", "",
          f"{len(papers)} 篇论文共 **{n_lim} 条 limitation**（代码侧 + 论文侧），去重后是 **{len(fs)} 条 Finding**。"
          "每条 Finding 就是一个要测试的对象：它说明在什么条件下代码会出现什么行为，给出触发点和对照点（witness_hint），"
          f"还附带它背后的全部原始记录。你要用的文件只有一个：`{a.src}`。", "",
          "## 1. 两侧的 limitation 有什么不同", "",
          "| | 代码侧（Wanting，步骤 2 + 3b） | 论文侧（Zhaopeng，步骤 1 + 3a） |",
          "|---|---|---|",
          "| 从哪来 | 从入口函数静态分析 + LLM 找出的检查、分支、回退 | 逐条读论文的机制描述，再去代码里找对应实现 |",
          "| 说的是什么 | “输入满足条件 X 时，代码会抛异常 / 换路径 / 改变状态” | “论文说要做 A，代码做的是 B（或没做）” |",
          "| 条件 | 有，是代码里的 Python 表达式（`condition.expr` + `path_prefix`） | 原始记录没有；步骤 4 由 LLM 写出，用代码核对过 |",
          "| 后果（effect_type） | reject / path_change / state / other …… | 几乎全是 other：只做了静态判断，后果未证实 |",
          "| 证据 | 代码位置（单行）+ 3b 在论文 / README / docstring 里找到的原文 | 论文原文 + 代码位置（常是一段行范围） |",
          "| ID 形式 | `CL-X###`（路线 A 静态）、`CL-B###`（路线 B 加 LLM） | `<论文>-gap-<机制>-<行为>`，如 `infinigen-gap-M01-B03` |",
          "| 类别 | undisclosed / contradicts_docs / stated_differently / docs_only / paper_stated | impl_deviates / not_implemented |",
          "| 典型 witness | solved：z3 给出边界两侧两个具体点 | always：每次走到引用代码都会出现 |",
          "| 适合的测试 | 异常断言、路径打桩，比较好写 | 和论文公式做 differential / metamorphic 对比，比较难写 |",
          "", "两侧说同一件事、经 LLM 判断合并后的 Finding，`limitations` 里两侧的记录都有。",
          "",
          "## 2. 数量", ""]
    L += counter_table(by_paper, ["代码侧", "论文侧", "两侧合并"], side, "论文") + [""]
    L += ["按类别：", ""] + counter_table(by_side, CATS, lambda f: f["category"], "来源") + [""]
    L += ["| 类别 | 意思 |", "|---|---|"] + [f"| `{c}` | {CAT_ZH[c]} |" for c in CATS] + [""]
    L += ["按 priority（1 = 先测）：", ""] + counter_table(by_side, [1, 2, 3], lambda f: f["priority"], "来源",
                                                         ["p1", "p2", "p3"]) + [""]
    L += ["按 effect_type：", ""] + counter_table(by_side, ["reject", "path_change", "state", "accuracy", "resource",
                                                            "performance", "other"], lambda f: f["effect_type"], "来源") + [""]
    L += ["按 witness 状态：", ""] + counter_table(by_side, WSTATUS, lambda f: f["witness_hint"].get("status"), "来源") + [""]
    L += ["按审阅状态（盲审由 LLM 子代理做，不是人工；只覆盖了部分代码侧条目）：", ""] + counter_table(
        by_side, ["worth_testing", "real_but_minor", "wrong", "unreviewed"], lambda f: f["review"], "来源") + [""]

    L += ["## 3. 一条记录里有什么", "",
          "`limitations_for_tests.json` 的结构是 `{schema_version, witness_format, rules, note, findings: [...]}`。"
          "`findings` 里每条记录的字段如下：", "",
          "| 字段 | 内容 | 测试时怎么用 |", "|---|---|---|",
          "| `finding_id` | `<论文>-F###`，在一篇论文内按 priority 排序 | TestCase.finding_id 填它 |",
          "| `category` | 7 类之一，见上表 | 决定这条测的是“没写”还是“和论文不同” |",
          "| `priority` | 1 / 2 / 3 | 先测 1 |",
          "| `effect_type` | reject / path_change / state / … | 决定 oracle，见第 5 节 |",
          "| `summary` | 一句话：什么条件下会怎样，附位置 | 给人看 |",
          "| `witness_hint` | 触发点、对照点和各名字的含义，见第 4 节 | 构造测试输入 |",
          "| `scope_status` | 是否在论文声明的范围内；目前几乎都是 unknown（论文侧参数映射很少） | out_of_scope 的不计入主结果 |",
          "| `review` / `review_note` | worth_testing / real_but_minor / wrong / unreviewed，以及是谁审的、理由 | wrong 的可以跳过 |",
          "| `rationale` | 分类依据、合并了谁、priority 的理由，以及判为“相关但不同”的其他 Finding | 查原因 |",
          "| `limitation_ids` / `limitations` | 背后的完整 Limitation 记录（两侧都可能有） | 看原始条件、论文原文和代码位置 |",
          "| `verification_ids` / `verifications` | 代码侧的 3b 结果：在哪里找到了说明、原文 | 判断“文档到底怎么写的” |",
          "| `confidence` | 目前全部是 llm_assisted | — |",
          "| `process_confidence` | 代码侧的静态证据：8 项检查的状态、重复测量、预测的测试档位上限、重要性数字（没有自己的档位），见第 6 节；"
          "纯论文侧的 Finding 为 null | 作为你定档的输入；不是测试结论 |", "",
          "注意：论文侧原始记录的 `effect_text` 有一部分写的是“同上……”，指的是 3a 同一条记录的 local_entry 描述。"
          "Finding 的 `summary` 已经展开，`limitations` 里保留原样。", "",
          "## 4. witness_hint 怎么读", "",
          "- `trigger`：满足条件的点，会走限制分支；`contrast`：离 trigger 最近、但不走限制分支的点。两者都满足 `path_prefix`。",
          "- `atoms` 说明每个名字该怎么造：`input` 直接给值；`local` 是局部变量，按 `aliases` 里的表达式造"
          "（如 `q_len` = `q.shape[1]`）；`derived` 要构造出这个值（如造一个第 1 维为 2 的张量）；"
          "`predicate` 是真假值，要 mock 或选输入（如 `is_flash_attn_2_available()`）；"
          "`category` 是字符串或枚举，`{\"not_in\": [...]}` 表示“列出的值以外的任意一个”。",
          "- `kind: event_sequence`（effect=state）：先通过前几次调用把状态弄成 trigger，再做检查。",
          "- 状态：", "",
          "| status | 意思 | 怎么测 |", "|---|---|---|",
          "| solved | 两个点都有 | 直接用 trigger / contrast |",
          "| solved_contrast_outside_scope | contrast 只能取在论文 scope 外 | 同上，注意 contrast 不在论文范围内 |",
          "| trigger_only | 条件在路径上总是成立，没有对照点 | 只用 trigger |",
          "| always | 论文侧：每次走到引用代码都会出现 | 任意走到 `code_locations` 的输入 |",
          "| infeasible | 条件和路径前缀矛盾，从入口走不到。`infeasible_because: call_chain` 表示是把被调函数的名字"
          "换成入口函数的名字之后才矛盾的（见下面“调用链”） | 已降为 p3，不用花预算 |",
          "| no_condition | 论文侧：没有可用条件 | 读 `note` 和 summary，人工判断 |",
          "| untranslatable / unknown | 条件翻译不了 / 求解超时 | 读 condition 原文 |", "",
          "调用链（`call_chain_status`）：", "",
          "| 值 | 意思 |", "|---|---|",
          "| resolved | `call_chain` 是从入口函数到目标所在函数的真实调用链（入口在前）。`call_sites` 逐层给出调用所在行、"
          "解析方式（`resolved_by`）和参数对应 `args`（被调函数的形参 -> 调用者里的表达式） |",
          "| entry_is_target | 目标就在入口函数里 |",
          "| module_level | 目标是模块级语句，import 时执行，没有调用链 |",
          "| not_found | 静态分析找不到从入口到目标的调用链（动态分发、回调，或目标不在入口的路径上）。"
          "有 `calls_entry` 时表示这个函数是调用入口的一方（如框架集成），要直接驱动它 |", "",
          "- `uncertain_steps` 列出靠猜解析的调用（方法名在仓库里唯一、子类覆盖、嵌套函数被传出去）。",
          "- `other_chains` 是其它调用链（例如同一个函数有两个调用点）。",
          "- `entry_terms`：条件和路径前缀换成入口函数名字后的写法，以及每个名字对应的入口表达式"
          "（如 `d` -> `k.shape[3]`）。有它时 `aliases` 也是用入口函数的名字写的。", "",
          "已知不足：",
          "- 没有调用链（not_found）时，`path_prefix` 仍混着各层函数的条件，同一个名字在调用者和被调用者里可能不是"
          "同一个东西。这时别名只在单层时参与求解，其余只列在 `aliases_not_applied` 里。",
          "- 多行语句的 `snippet` 是 `ast.unparse` 后的第一行：并成一行、去掉 assert 消息、去掉多余括号，最多 200 字符。"
          "请按解析后的条件比较，不要逐字比较。",
          "- 论文侧条件由 LLM 写出，只核对过“名字都出现在引用的代码里”，**语义不一定对**，要当提示用。",
          "- 所有值都没有实际执行验证过。", "",
          "## 5. 按 effect 选 oracle（建议）", "",
          "| effect_type | 意思 | 建议的 oracle |", "|---|---|---|"]
    L += [f"| {e} | {m} | {o} |" for e, m, o in ORACLE] + [""]

    pc = [f for f in fs if f.get("process_confidence")]
    if pc:
        by_paper_pc = [(p, [f for f in items if f.get("process_confidence")]) for p, items in by_paper]

        def ceiling(f):
            t = f["process_confidence"]["testability"]
            return "没测量" if not t.get("measured") else t["ceiling"] if t.get("testable") else "测不了"

        L += ["## 6. 代码侧的静态证据（未校准，没有自己的档位）", "",
              "每条有代码侧记录的 Finding 带一个 `process_confidence` 块（格式 `process-confidence-v2`，规则见 "
              "`docs/11_process_confidence.md`）。它是对你的档位的补充：**代码侧不定档，档位只由你的测试证据决定**。"
              "不执行代码、不调模型，同样的输入得到同样的结果。块里有四部分。", "",
              "**1. `checks`：核对表。** 词汇和你的 defeater 表一样："
              "`eliminated`（工具核对过）、`residual`（只有论证或模型判断）、`open`（没评估）、`refuted`（核对失败）。", "",
              "| 检查 | 对应的测试概念 | 对应你的 | `eliminated` 的条件 |", "|---|---|---|---|",
              "| C1 location | 输入有效性 | D12 | 固定 commit 下该行的语句就是记录的 snippet |",
              "| C2 condition | 语句的判定（decision） | D2 | 条件就是该语句的判定表达式或它的取反 |",
              "| C3 reachability | 可达性（RIPR 的 R） | D1、D14 | 从官方入口到目标有静态调用链，且没有靠猜的步骤 |",
              "| C4 feasibility | 不可行路径 | witness | z3 在完整路径前缀下找到触发点和对照点 |",
              "| C5 extraction | 分析的可重复性 | D8 | 静态路线找到，或 LLM 路线在全部抽取运行里都找到（同一文件同一行） |",
              "| C6 effect_label | oracle 与语句相符 | D4、效果类型 | 标注的效果能在该语句上判定（reject 要能抛异常，path_change 要是 if / while） |",
              "| C7 documentation | 缺失性断言，只作说明 | — | 3b 找到了原文；not_found 无法证明，为 residual；3 次重复不一致也为 residual |",
              "| C8 review | 审查（inspection） | — | 人工审过；LLM 盲审为 residual，没审为 open |", "",
              "**2. `repeats`：重复测量。** `extraction_runs`：这个位置在几次抽取运行里出现（`found_in` / `of`）；"
              "`documentation_check`：3b 重复几次、结果的一致率；`routes`：哪条路线找到的（`ast` 静态、`llm`）。", "",
              "**3. `testability`：预测你这边能测到哪一档。** 按你的规则推出来的上限，不是预报，实际可以更低。", "",
              "| 字段 | 含义 |", "|---|---|",
              "| `testable: false` + `expect_not_run` | C4 为 refuted 预计 `witness_unusable`；效果是 `other` 预计 `outcome_unsupported` |",
              "| `mutants` / `mutants_needed` | 用你的 `mutate.generate` 在目标行能造出几个变异体；少于 `n_min`（4）时 D3 消不掉 |",
              "| `ceiling` | `L1`：变异体不够；`L2`：没有调用链，D14 最多 residual；`L3`：静态上没有限制 |",
              "| `limited_by` | 卡在哪个 defeater，原因是什么 |",
              "| `condition_has_calls`、`integer_boundary` | 条件里有没有函数调用（影响 D2 能否直接求值）；边界变量是否都是整数（影响 D5 的邻点） |", "",
              "和已有测试报告对照（7 篇里测过的 130 条）：**没有一条的实际档位超过预测上限**，98 条正好等于上限；"
              "预计 `outcome_unsupported` 的 48 条、`witness_unusable` 的 12 条全部对上。这是在同一批数据上看的，不是独立验证。", "",
              "**4. `importance`：重要性，和把握分开。**", "",
              "- `path.decision_on`：`main` 每次调用都会求值这个判定；`side` 判定在某个 `if` / `except` / `case` 里面"
              "（自己函数里的见 `enclosing_conditions`，调用链上的见 `conditional_call_sites`）；`unknown` 没有调用链，看不到调用者。",
              "- `impact`：判定管住多少语句（分支体，或 assert / raise 之后函数里剩下的语句）、函数共多少语句、"
              "从入口来的调用链条数、仓库里解析到这个函数的调用点数。",
              "- `coverage`：目标函数里有多少个判定（if / while / assert）、代码侧列出了几个、入口能否静态到达这个函数。"
              "这是**分析的覆盖**，不是执行覆盖；执行覆盖在你的 `execution_report.json` 里。", "",
              "**建议的用法**：测之前按 `ceiling` 分配预算（`测不了` 的不测，`L1` 的少花时间）；测之后把 `limited_by` "
              "放在档位旁边，说明是这句本身测不到更高还是测得不够；没测的 Finding 把 `checks` 和 `repeats` 作为确定性的证据并排列出；"
              "`importance` 只用于排序，不进档位。", "",
              "预测的测试档位上限：", ""]
        L += counter_table(by_paper_pc, ["测不了", "L1", "L2", "L3", "没测量"], ceiling, "论文") + [""]
        L += ["判定在主路径还是侧路径：", ""] + counter_table(
            by_paper_pc, ["main", "side", "unknown"],
            lambda f: f["process_confidence"]["importance"]["path"].get("decision_on"), "论文") + [""]

    L += ["## 7. 典型例子", "", "每个例子是一条 Finding 的精简版，长字段已截断；完整内容在 json 里。"
          "例子是按规则自动挑的第一条，不是挑好看的。“论文侧 · LLM 写出条件”那条正好说明了它的局限："
          "条件在形式上能解，但不一定抓住了论文差异的本质，所以论文侧条件只当提示用。", ""]
    ex = [
        ("代码侧 · undisclosed · p1 · 有别名", lambda f: side(f) == "代码侧" and f["priority"] == 1
         and f["witness_hint"].get("aliases")),
        ("代码侧 · stated_differently（文档说得比代码弱）", lambda f: side(f) == "代码侧"
         and f["category"] == "stated_differently" and f["witness_hint"].get("status") == "solved"),
        ("代码侧 · docs_only（README / docstring 写了，论文没写）", lambda f: side(f) == "代码侧" and f["category"] == "docs_only"),
        ("代码侧 · state（事件序列）", lambda f: side(f) == "代码侧" and f["effect_type"] == "state"),
        ("代码侧 · infeasible（多半走不到，p3）", lambda f: f["witness_hint"].get("status") == "infeasible"),
        ("两侧合并", lambda f: side(f) == "两侧合并"),
        ("论文侧 · impl_deviates · always", lambda f: side(f) == "论文侧" and f["witness_hint"].get("status") == "always"
         and len(f["limitations"]) > 1),
        ("论文侧 · LLM 写出条件并求解", lambda f: side(f) == "论文侧" and f["witness_hint"].get("status") == "solved"),
        ("论文侧 · not_implemented", lambda f: f["category"] == "not_implemented"),
        ("论文侧 · no_condition", lambda f: f["witness_hint"].get("status") == "no_condition"),
    ]
    used: set = set()
    for title, pred in ex:
        f = pick(fs, pred, used)
        if f:
            L += [f"### {title}：`{f['finding_id']}`", "", "```json", compact(f), "```", ""]

    L += ["## 8. 全部 Finding 索引", "",
          "每篇按 priority 排序。列的含义：侧 = 代/论/合（代码侧 / 论文侧 / 两侧合并）；"
          "审 = 审阅状态（✓ worth_testing，~ real_but_minor，✗ wrong，空 = 未审）；"
          "过程 = 过程置信度档位和判定所在路径（第 6 节；论文侧为空）。", ""]
    mark = {"worth_testing": "✓", "real_but_minor": "~", "wrong": "✗", "unreviewed": ""}
    sd = {"代码侧": "代", "论文侧": "论", "两侧合并": "合"}
    for p, items in by_paper:
        L += [f"### {p}（{len(items)} 条）", "",
              "| ID | 侧 | 类别 | P | effect | witness | 审 | 上限 路径 | 位置 | 内容 |", "|---|---|---|---|---|---|---|---|---|---|"]
        for f in items:
            w = f["witness_hint"]
            loc = w.get("location") or (w.get("code_locations") or [""])[0]
            b = f.get("process_confidence")
            t = b["testability"] if b else {}
            proc = (f"{t.get('ceiling') or ('测不了' if t.get('measured') else '')} "
                    f"{b['importance']['path'].get('decision_on', '')}").strip() if b else ""
            L.append(f"| {f['finding_id'].split('-')[-1]} | {sd[side(f)]} | {f['category']} | {f['priority']} | "
                     f"{f['effect_type']} | {w.get('status')} | {mark[f['review']]} | {proc} | `{short(loc, 60)}` | "
                     f"{short(f['summary'].rsplit(' (', 1)[0] if side(f) != '论文侧' else f['summary'], 100)} |")
        L.append("")
    (ROOT / a.out).write_text("\n".join(L))
    print(f"wrote {a.out}: {len(fs)} findings, {len(L)} lines")


if __name__ == "__main__":
    main()
