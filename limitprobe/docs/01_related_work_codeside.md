# Code-side related work (steps 2, 3b, 4)

The full survey is in the project document `claude/related-work-survey.md`. This file retains only the parts directly relevant to the code side.
Check publication details before citing 2026 preprints (Dude, CASCADE, SeGa, etc.).

## 1. Repository analysis: approaches in existing work

| Approach | Representative work | Starting point | Exploration | How conclusions are confirmed |
|---|---|---|---|---|
| Put the entire repository in context | SciCoQA evaluation | No selection | No exploration | LLM |
| General agent + file tools | Dude, SWE-agent, Agora | LLM chooses | grep / read loop | LLM (Dude uses multi-agent negotiation) |
| Read known units one by one | WhiteFox | Enumerate optimization registry | Read only that unit's source | Instrumentation confirms triggering + on/off differential |
| Feed structures extracted by program analysis to an LLM | SymPrompt, TELPA, KernelGPT, Ciri | AST, call graph, handler extraction | Extract path conditions / call chains; KernelGPT iteratively asks for missing definitions | Execution / fuzzer |
| Static analysis driven + LLM on demand | RepoAudit, LLMDFA, IRIS | tree-sitter rules locate source | Function by function, with memory, expand caller/callee on demand | Validator / solver |

Key points:

- **SciCoQA**'s "put the entire repository in context" approach degrades markedly with length: code brought 70 of 266 papers above 100K tokens, and recall declined with length ([arXiv 2601.12910](https://arxiv.org/html/2601.12910v1)).
- **RepoAudit** (ICML 2025): an initiator uses tree-sitter to find sources, an explorer analyzes one function at a time and stores memory, and a validator checks satisfiability of path conditions; precision was 78.43% on 15 projects ([arXiv 2501.18160](https://arxiv.org/html/2501.18160v3)). **Our extractor follows this structure**, replacing the source from "bug patterns" with "paper mechanism entry points".
- **LLMDFA** (NeurIPS 2024): an LLM writes scripts that call parsing libraries to extract source/sink; a theorem prover handles path feasibility ([arXiv 2402.10754](https://arxiv.org/abs/2402.10754v2)). Lesson: the LLM generates checks, and tools execute them.
- **SymPrompt**: uses an AST to collect branch conditions on each return path; manual inspection found that only 6/10 tests actually took the target path ([arXiv 2402.00097](https://arxiv.org/html/2402.00097v2)). Lesson: execution must determine whether a path was triggered.
- **Agora** (ICML 2026): an ordinary ReAct code-reading agent found 0 protocol logic bugs; after mined bug patterns were added, it found 15 ([arXiv 2605.29910](https://arxiv.org/pdf/2605.29910)). Lesson: free exploration is insufficient; external knowledge must indicate where to look—we use the paper.
- **WhiteFox** (OOPSLA 2024): reads optimization source to summarize trigger conditions, uses instrumentation to confirm triggering, and compares on/off behavior; 101 bugs ([arXiv 2310.15991](https://arxiv.org/html/2310.15991v3)). It can "read one by one" because optimizations can be enumerated from a registry; research prototypes have no registry.

## 2. Code → paper verification (3b)

- **SciCoQA**: calls "present in code, absent from the paper" Paper Omission; it is the hardest category and accounts for 50% of differences in reproduction reports. **Its definition excludes bugs, hyperparameter inconsistencies fixable by configuration, and trivial engineering details**—precisely the thresholds, fallbacks, and configuration limits we focus on. Systems are also outside its coverage.
- **Dude** (arXiv 2609.03416, preprint): in the code→paper direction, a code claimer extracts "noteworthy implementations", then a paper verifier checks the paper, with anchor / relevance filtering; F1 86.55 on SciCoQA (GPT-5.4). It uses only grep/glob/read for static inspection and relies on an LLM for judgments. **This is the most direct comparison for 3b**: our differences are (a) checking conditional regions rather than descriptions, (b) judging scope and whether they were evaluated, and (c) producing witnesses.
- **NeurIPS 2026 agentic code audit** (Iversen et al.): 87 papers, 609 discrepancies, about half supported by executable checks written by agents ([poster](https://neurips.cc/virtual/2026/poster/157023)).
- **CASCADE** (FSE 2026, preprint): lists "if [condition] then [behavior]" from function documentation, generates and runs tests, then uses "regenerate the implementation from documentation" for differential filtering; P 0.88 / R 0.21 ([arXiv 2604.19400](https://arxiv.org/pdf/2604.19400)). This matches our "condition → effect" structure, but at the granularity of individual functions.
- **SeGa** (ISSTA 2026, preprint): teams considered about 30% of reports intentional ([arXiv 2604.23509](https://arxiv.org/pdf/2604.23509)). Lesson: 3b and step 4 must distinguish bugs, undisclosed limitations, and reasonable engineering trade-offs.
- **RFC → constraints** (Liu et al.): LLM recall for recovering constraints from text was only about 17% (independent constraints) and 0% (dependent constraints) ([alphaXiv 2511.17977](https://www.alphaxiv.org/abs/2511.17977.md)). Lesson: **mine thresholds from code; use the paper only to judge scope and intent**.

## 3. Configuration and thresholds

- **ctest** (OSDI 2020): reruns existing tests under the target configuration, reusing their assertions; 62/64 real configuration failures ([PDF](https://www.usenix.org/system/files/osdi20-sun.pdf)). Research prototypes usually lack test suites, so we must generate witnesses ourselves.
- **Ciri**: an LLM statically judges whether configurations are faulty; F1 for cross-parameter dependency errors is only about 0.3 ([arXiv 2310.09690](https://arxiv.org/html/2310.09690v2)). Lesson: configuration-dependent regions (such as FlexPrefill's `min_budget` determining the fallback boundary) cannot be left to an LLM to judge.
- **DocTer** (ISSTA 2022): mines constraints from API documentation and generates valid, invalid, and boundary inputs ([arXiv 2109.01002](https://arxiv.org/html/2109.01002v4)). Our witness_hint generation follows the same idea, but constraints come from code.

## 4. Tool selection

| Tool | Use | Status / notes |
|---|---|---|
| Python `ast` (standard library) | v0 extractor: conditions, assert, calls, line numbers | Zero dependencies; `ast.unparse` requires Python 3.9+ |
| LibCST | When preserving formatting or rewriting code (such as creating mutants) | For Shanghao's mutation testing |
| tree-sitter | Multiple languages (C++/CUDA call layer) | Introduce when needed |
| PyCG | Python call graph | **Archived on 2023-11-26 and no longer maintained** ([GitHub](https://github.com/vitsalis/PyCG)); not used as a dependency |
| Scalpel | Python static analysis framework (CFG, call graph) | [GitHub](https://github.com/SMAT-Lab/Scalpel); an alternative for call resolution |
| z3-solver | Region ∩ scope intersection, path feasibility, witness solving | `pip install z3-solver`; simple intervals can initially be handled by hand |

## 5. Conclusions for code-side design

1. The paper supplies the seed (the mechanism entry point in Binding); explore by function with memory, and leave judgments to the AST and solver.
2. Split 3b judgment into three independent questions: whether it is documented (retrieval + LLM, with a verbatim, verifiable quote), whether it is in scope (deterministic), and whether it was evaluated (deterministic).
3. Output must be verifiable: each Region has file:line and the original condition expression; each Verification has a verbatim quote.

## 6. Design rationale for route B (static + LLM)

| Work | Approach | Use in route B |
|---|---|---|
| [IRIS](https://arxiv.org/html/2405.17238v3) (ICLR 2025) | LLM supplements CodeQL specifications, then judges each alert with path context | Previously used to remove false positives (hybrid-v2), removed in v3 |
| [ZeroFalse](https://arxiv.org/html/2510.02534v1) (preprint) | Sends analyzer alerts, traces, and context to an LLM for adjudication | Previously used to remove false positives (hybrid-v2), removed in v3 |
| [LLM4PFA](https://arxiv.org/abs/2506.10322) (preprint) | LLM agent judges path feasibility to filter false positives | Previously used for reachability judgments (hybrid-v2), removed in v3 |
| [RepoAudit](https://icml.cc/virtual/2025/poster/45170) (ICML 2025) | Explores by function on demand; validator guards against hallucinations | Recover missed reports by function and validate output |
| [SEA](https://themoonlight.io/review/semantic-enhanced-indirect-call-analysis-with-large-language-models) | Static analysis supplies candidate targets and an LLM filters them (indirect calls in C) | Added call edges must be selected from real definitions |
| [Empirical study of LLM call graphs](https://arxiv.org/pdf/2410.00603) | PyCG generally outperforms LLMs on Python call graphs; LLMs add edges only in some cases | Do not let the LLM freely produce call edges |
| [Datadog false-positive filtering](https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives.md) | Engineering practice: stronger filtering increases the risk of missing real issues | Deletion risks missing real issues, so v3 no longer deletes |

The above is based on search results and abstracts; the full papers have not yet been read closely. Verify them before writing the report.
