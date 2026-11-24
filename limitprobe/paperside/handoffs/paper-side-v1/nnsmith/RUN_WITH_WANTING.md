# 直接接入 Wanting

此目录的 paper_side.json 原样传给 codeside.verify3b 的 --paper-side。不要把它替换成完整 conformance.json；后者是保留三类判断的扩展证据。

```bash
# 在 Wanting 仓库内，使用已装 pydantic / z3 / 文档检索依赖的 Python
python -m codeside.verify3b \
  --limitations results/pipeline/nnsmith/limitations.json \
  --artifact data/nnsmith/artifact.json \
  --pdf /绝对路径/交接包/nnsmith/evidence/paper.pdf \
  --repo /固定到artifact.json中commit的仓库路径 \
  --paper-side /绝对路径/交接包/nnsmith/paper_side.json \
  --model x-test-2 --repeats 3 --workers 3 \
  --out /新的结果目录/nnsmith-3b.json
```

这条命令会调用模型。当前 validation.json 的集成检查只加载实际消费者并运行其范围检查器，不冒充已经重新运行全文档核查。源码、图表和已完成语义核验均不构成已确认运行缺陷。

原始证据：evidence/paper.pdf、scope_interpretations.json、source_reads.json、code_evidence_registry.json；每条依赖引用有独立 repo/commit，不能当作主仓库路径。原始论文页与 prompt 的引用路径见 manifest 和实际调用记录。
