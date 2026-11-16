# Labelling sheets (20 of 51 tested Findings)

Fill `sheet_<you>.csv` alone, without discussing and without opening `key.json` (it holds what the harness said).

* `q1_finding_true`: read the claim, the code location and the quote. Is the claim true of the code at that location?
  `true/false/unclear`. A claim that is true but trivial still counts as true.
* `q2_test_valid`: open the driver (`driver` column, relative to the results root) and read the two runs. Does the test
  show the claim, with the trigger taking the described path and the contrast not taking it, through a call of the
  product's entry or a function the product calls? `valid/invalid/unclear`.
* `notes`: one line when you answer `unclear` or `invalid`.

Then: `python -m checklimits labels evaluate --sheets sheet_r1.csv sheet_r2.csv sheet_r3.csv --key key.json`.

## LLM 第一遍（`llm/`）

`llm/sheet_gpt-61-sol_{1,2,3}.csv` 是 gpt-6.1-sol 对同一份表的三次独立回答（没有给它 harness 的判定、档位和 defeater，只给了断言、代码、driver 和两次运行的结果，提示在 `llm/llm_prompts.jsonl`）。**请先填完自己的表再看它**，否则会被带偏。它是第一遍，不是真值：`labels compare` 会列出它和 harness 不一致的条目，人工先看这几条。

```bash
python -m checklimits labels evaluate --sheets labels/sheet_shanghao.csv labels/sheet_wanting.csv labels/sheet_zhaopeng.csv --key labels/key.json
python -m checklimits labels compare --sheets labels/llm/sheet_gpt-61-sol_*.csv --key labels/key.json
```
