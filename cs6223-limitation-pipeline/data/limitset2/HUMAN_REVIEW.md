# limitset2 label review sheet

Status: human-reviewed. Mark each label: keep / edit / drop.
## LS2-01-L1 (flexprefill) - applicability_limitation - mechanism_reported_consequence_inferred

**Selecting Vertical-Slash indexes from the last query block does not guarantee coverage for mid-sequence queries**

For Vertical-Slash heads, which the paper reports are the large majority of heads, FlexPrefill computes attention only for the last block_size (128) queries, keeps the vertical and slash lines that reach cumulative mass gamma for that block, and then applies those lines to every query in the prompt. The gamma target is therefore checked only for the end-of-prompt queries; the paper gives no coverage guarantee for queries elsewhere in the sequence. This fits workloads where the trailing queries, such as a final question, decide the answer. It may fit less well when accuracy depends on long-range attention from mid-sequence tokens to keys the last block does not attend to (for example, multi-hop chains inside the document). The paper's own ablation shows that index quality depends strongly on which queries serve as the proxy, but the ablation cannot tell which property of the last block makes it work.

- Critical link: The key step is whether, in real workloads, mid-sequence queries need long-range keys that the last block's lines miss, and whether that changes final outputs after dense decoding. Table 8 shows strong sensitivity to the proxy's position, but the effect is confounded with causal reach, so it does not show that prompt layout or task structure matters.
- Conditions: The head is classified as Vertical-Slash (the common case per Appendix H).; Task-relevant long-range dependencies of mid-sequence tokens point to keys that receive little attention mass from the last query block.; Those mid-sequence representations affect the answer even though decoding is dense.; Comparison at the same gamma and minimum-budget settings as a full-attention or per-query-coverage baseline.
- Defeaters: The retained first/last key blocks, slash lines, and the 1024-token minimum budget already cover the keys mid-sequence queries need.; Vertical lines that are important are shared across query positions (e.g., sinks and salient tokens), so the last block's selection transfers well.; Benchmarks with multi-hop tracing and aggregation (RULER) show no degradation at matched gamma, as the paper's averages suggest.; A variant that uses several representative blocks gives the same accuracy as the last-block version.
- Locations: §3 Cumulative-Attention Based Index Selection; Algorithm 3; PDF pages 5-6; §4.1 Implementation Details; PDF page 7; Appendix F.3; Table 8; PDF page 23; Appendix H; Figure 8; PDF page 26
- Review: [x] keep  [ ] edit  [ ] drop
- Review rationale（中文）: 核心机制和推断边界均准确。Algorithm 3 在末尾 128 个 query 的聚合分布上分别选择 vertical/slash 线，再扩展到整张注意力图；这不能推出中间 query 的逐查询覆盖率。Table 8 的 middle 代理使平均分从 89.18 降至 38.18，但更换代理同时改变因果可见范围，原文已明确这一混杂。保留该条作为条件性适用限制，不能把它升级为论文已经测得中段依赖失败。gamma 应理解为代理集合的聚合阈值，亦非末块每一个 query 的独立保证。
- Confidence: high
- Sources: [S01](https://arxiv.org/html/2502.20766v1) — §3; Algorithms 3–4; §4.1 Implementation Details； [S01](https://arxiv.org/html/2502.20766v1) — Appendix F.3, Table 8; Appendix H, Figure 8

## LS2-01-L2 (flexprefill) - method_shortcoming - mixed_reported_and_inferred

**Attention-mass selection does not by itself guarantee task accuracy, and aggressive thresholds require length-specific validation**

FlexPrefill uses attention mass as its selection proxy. Its local error argument depends on retained mass and value magnitudes, while the implementation estimates coverage using pooled blocks or a representative query subset. Consequently, gamma is not a guarantee that every task-relevant interaction survives or that the final answer is unchanged. A low-mass interaction could matter when its value contribution or downstream decision sensitivity is large. Table 5 shows larger losses at 128k for aggressive gamma settings, but the default 0.95 remains competitive with full attention. Because the budget adapts to the input, fixed gamma alone does not imply a worsening length trend; the observed losses do not identify tail truncation as their cause.

- Critical link: Separate losses from genuinely omitted interactions, errors in the coverage proxy, and the model's baseline long-context limitations using matched dense-attention prompts and controlled interventions.
- Conditions: Task-relevant contributions are excluded by the selected blocks or lines and are not recovered by other heads or layers; The local perturbation changes a later decision; low attention mass alone does not establish importance; Compare the same model, prompts, gamma, minimum budget, and protected blocks across lengths.
- Defeaters: The decisive interactions remain in the selected set or are redundant across heads and layers; The loss disappears after correcting the coverage estimator without retaining the proposed low-mass keys; Matched long-context tasks remain close to full attention at the chosen gamma and minimum budget.
- Locations: §3 Eq. 3, Algorithms 3–4; Appendix A Eq. 6; Appendix E Table 5; Appendix F.4–F.5 Tables 9–10; Appendix J
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 保留“注意力权重总量不是任务级充分条件”的核心，但原稿把固定 gamma 与长度增加后的损失联系得过于直接。方法会随输入调整预算，不能从固定 gamma 推出保留键数固定或遗漏必然随长度变坏；Table 5 在默认 gamma=0.95 时128k分数79.09还高于full attention的78.13。明显退化出现在更激进阈值。另需区分真实逐 query 注意力权重总量、池化估计和末块代理，不能把推导中的a_S直接当成实现保证。低权重键是否关键取决于值向量、决策margin和后续网络传播。
- Confidence: high
- Sources: [S01](https://arxiv.org/html/2502.20766v1) — §3 Eq. 3, Algorithms 3–4; Appendix A Eq. 6； [S01](https://arxiv.org/html/2502.20766v1) — Appendix E, Table 5; Appendix F.4, Table 9

## LS2-02-L1 (flexposit) - method_shortcoming - mixed_reported_and_inferred

**Matching BitMoD's WikiText-2 perplexity does not establish matched downstream-task accuracy**

FlexPosit ranks channel windows by the perplexity improvement from upgrading one window, and uses PEB—the minimum precision matching BitMoD's 4-bit WikiText-2 perplexity—for its main aggregate hardware comparison. This establishes an iso-PPL operating point, not downstream-task equivalence. Table V lacks a BitMoD downstream baseline and does not report every model's exact PEB point. Algorithm 2 also leaves the profiling dataset's separation from evaluation unspecified; overlap is not established. Thus the reported performance advantage is supported under the stated perplexity criterion, while its size at matched downstream accuracy remains unmeasured.

- Critical link: Evaluate FlexPosit at each model's PEB and BitMoD at 4 bits on identical downstream tasks, and document the profiling/evaluation split.
- Conditions: The intended deployment evaluates task accuracy or another quality metric not fully captured by WikiText-2 perplexity; A downstream quality gap persists under the same evaluation protocol and requires additional FlexPosit precision to close; Any profiling/evaluation overlap must be verified before attributing optimistic results to it.
- Defeaters: Matched downstream evaluation shows equivalent or better FlexPosit quality at PEB; Independent profiling and held-out task evaluation reproduce the comparison; The deployment's agreed quality target is perplexity itself, so the original comparison answers that narrower question.
- Locations: §IV-B Algorithm 2; §VI-A; Table II; §VI-B Table V; Figures 9, 11–12
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 保留iso-PPL不能自动升级为iso-downstream-quality的质疑，但原稿的“所有硬件比较均采用PEB”不准确：Fig.9/12还扫描其他精度点，PEB针对主要汇总比较。Algorithm 2只称数据集D，没有证明就是WikiText-2或与评估重合，因此数据泄漏只能列为待核验项。Table V没有BitMoD对照，也没有LLaMA-2-7B确切PEB=4.6b列；4.4b/5b低于FP16不能证明PEB点比BitMoD差。应把标签收窄为比较证据缺口。
- Confidence: high
- Sources: [S02](https://arxiv.org/html/2609.04724v2) — §IV-B, Algorithm 2; §VI-A; Table II； [S02](https://arxiv.org/html/2609.04724v2) — Table V; Figures 9, 11–12

## LS2-02-L2 (flexposit) - applicability_limitation - inferred

**The reported compute-density advantage is not yet validated for bandwidth-bound, small-batch decode**

FlexPosit's compact array and shared-weight MAC clusters benefit from reuse across activation rows. With one or a few decode tokens per step, such reuse may fall and weight-memory traffic may dominate, reducing the benefit of additional compute capacity. The paper defaults to batch 1 and a 256-token input and extends its sweep to larger workloads, but does not isolate single-token decode. Whether its speedup persists therefore depends on the actual GEMM mapping, memory traffic and utilization. Nominal 4.1–5.0-bit versus 4-bit precision alone cannot settle the comparison: both methods' scales, datatype metadata, packing and rereads must be counted.

- Critical link: Measure phase-separated decode latency and off-chip bytes for the same model, quality target, memory system and small batch, including utilization of the four shared-weight lanes.
- Conditions: Small-batch autoregressive decode dominates the application's total time; Weights do not remain resident and measured memory bandwidth limits the relevant GEMMs; The implementation cannot remap or batch enough independent work to recover the presumed lost utilization.
- Defeaters: The evaluated simulator already models representative small-M decode and phase-specific results preserve the gains; Measured metadata and data traffic still favor FlexPosit enough to sustain a decode advantage; Batching, speculative decoding, on-chip residency or another mapping keeps the target workload compute-limited.
- Locations: §V-A Dataflow; §V-B; Figure 6; §VI-A Hardware Implementation; §VI-C; Figure 11; Table X
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 小batch decode可能受带宽限制、降低计算密度收益的推断合理，但原稿把“256-token输入”直接解释为全部被测计算的M=256过于确定，论文未分开报告prefill与decode。更明显的问题是用FlexPosit有效位宽4.1–5.0与BitMoD裸4b推断谁的DRAM字节更多，忽略BitMoD的group scale和datatype元数据、打包及重读。应删除“PEB权重一定不更小”与已发生反转的暗示，保留尚未验证的decode适用范围。
- Confidence: high
- Sources: [S02](https://arxiv.org/html/2609.04724v2) — §V-A Dataflow; §V-B 4-Way MAC Clusters； [S02](https://arxiv.org/html/2609.04724v2) — §VI-A Hardware Implementation; §VI-C; Table X

## LS2-03-L1 (qoserve) - method_shortcoming - mechanism_reported_consequence_inferred

**Cumulative token deadlines do not themselves bound every inter-token gap**

QoServe schedules against D_n = arrival + SLO_TTFT + (n−1)·SLO_TBT and can spend accumulated slack on larger prefill chunks. Meeting these absolute deadlines does not mathematically imply that every consecutive-token gap is at most SLO_TBT: an earlier token can arrive well ahead of its deadline. This creates a conditional fluency risk if the implementation permits long mixed iterations during active decoding. Section 3.5 also describes reverting to smaller chunks, so actual behavior needs verification. The reported below-0.1% TBT violations and omitted plots do not provide enough measurement detail to identify the counting rule or bound raw gap tails.

- Critical link: Check the scheduler's actual per-iteration cap and report raw inter-token p99/max gaps alongside cumulative-deadline violations for active interactive requests.
- Conditions: An interactive request has accumulated early-completion slack; The scheduler spends that slack on an iteration longer than the request's desired per-gap bound; Users receive tokens directly and their experience depends on individual gaps.
- Defeaters: An independent per-iteration latency cap enforces the desired raw-gap bound; Measured p99/max gaps stay within the application's tolerance despite slack-based scheduling; A permitted client-side output buffer smooths the gaps while meeting the application's latency requirements.
- Locations: §3.2 Equations 1–2; §3.3 Figure 4; Algorithm 1; §3.5 Figure 6; §4.1.4 Figure 9; §4.2
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: Eq.2的累计deadline确不蕴含相邻token间隔上限，核心数学质疑成立。但论文§4.2只说平均TBT violations <0.1%，没有给出足够细的统计定义，不能凭调度公式就断定这个数字必然按累计deadline统计。§3.5还写进入decode后恢复小chunk，同时仍可利用积累slack，因此应承认该限定并要求核查实际策略。保留“未保证逐间隔”而不把潜在长gap写成已观测退化。
- Confidence: high
- Sources: [S03](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/10/QoServe_CC_final_v2.pdf) — §3.2 Equations 1–2; §3.3; Algorithm 1； [S03](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/10/QoServe_CC_final_v2.pdf) — §3.5; §4.1.4 Figure 9; §4.2

## LS2-03-L2 (qoserve) - applicability_limitation - mixed_reported_and_inferred

**Non-interactive scheduling needs further validation when TTLT headroom is comparable to decode-length uncertainty**

QoServe estimates unknown non-interactive decode length from application history with a two-standard-deviation allowance, justified by typically generous TTLT deadlines. Its relegation check occurs during prefill selection and decoding requests are not preempted. If actual output length is substantially underestimated, a request can become unable to finish on time after it has passed that selection stage. The evaluated minute-scale TTLT settings support the tested regime, but do not establish robustness to tight headroom, heavy tails or distribution drift. This is a conditional sensitivity, not a claim that large slack is necessary for correct scheduling; prediction quality and the weight given to remaining work also matter.

- Critical link: Sweep TTLT headroom relative to decode prediction error under overload, and compare realized violations and ordering with an oracle-length or better-prediction baseline.
- Conditions: TTLT headroom is comparable to prediction error in remaining decode time; Output lengths are heavy-tailed, shift from application history, or are insufficiently bounded; Overload makes request ordering and irreversible admission to decoding consequential.
- Defeaters: Prediction error remains small relative to available headroom, even with a tight nominal TTLT; Enforced output caps or improved per-request prediction adequately bound the remaining work; Matched overload experiments show negligible sensitivity to realistic length errors and drift.
- Locations: §3.4 Eq.5, Eager Relegation, Selective Preemption; Algorithm 1; §3.6; Tables 2–3; §4.4.1–4.4.2
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 历史输出长度加两倍标准差、prefill阶段relegation、decode不抢占和600/1800s主实验SLO均可核实。需要把“只有TTLT远大于处理时间才可靠”改为风险条件：宽裕deadline有利于容忍预测误差，但不是必要条件；紧SLO下若预测准确、长度受控或alpha很小也可能工作。mean+2σ不是重尾下的普适上界，不能把它本身当保证。§4.4.2另测1000s非交互SLO，但仍未覆盖接近服务时间的紧TTLT或分布漂移。
- Confidence: high
- Sources: [S03](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/10/QoServe_CC_final_v2.pdf) — §3.4 Eq.5; Eager Relegation; Selective Preemption; Algorithm 1； [S03](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/10/QoServe_CC_final_v2.pdf) — Tables 2–3; §4.4.2 Varying SLO

## LS2-04-L1 (tessera) - method_shortcoming - mixed_reported_and_inferred

**Partitioning by profiled post-overlap costs has an unquantified robustness boundary under changing routing distributions**

Tessera minimizes the maximum profiled post-overlap edge cost, a surrogate for the pipeline critical path. Its statement that each distinct pair is profiled once describes profile deduplication and reuse, not necessarily a single timing sample. The cited 15% tail error concerns the primitive-level fallback estimator rather than the default chunk-pair measurements. A narrower concern remains: if deployment routing changes candidate costs enough to reverse their ordering, a partition selected from fixed profiles can become suboptimal, and DBO cannot move its boundaries. The paper does not quantify this sensitivity; it does not demonstrate that such a reversal occurred in the reported deployments.

- Critical link: Measure candidate-cost distributions under representative routing and compare their ordering and bottleneck gaps with the selected static partition. Neither the number of profiling samples nor a numerical routing-induced partition error can be inferred from the reuse policy.
- Conditions: Deployment routing changes the relative post-overlap costs of competing partitions, rather than merely shifting all costs together; The cost differences between the best candidates are small relative to that change; The comparison holds pipeline template, device topology, DBO policy, and profiling effort constant.
- Defeaters: Profiling covers representative routing and the selected partition remains best across the measured distributions; A substantial cost margin makes candidate ordering insensitive to the observed variation; Runtime repartitioning or timely reprofiling removes the distribution mismatch.
- Locations: §2.3.3 and Fig.5; §3.1.2–3.1.3 and Eq.1; §5 Granularity of Cost Profiling; §6.4 and Fig.12. USENIX PDF pp.5–7, 10, 13 (including cover).
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 保留静态代价对路由变化敏感这一条件性问题，但必须纠正两处证据误读。§3.1.2 的每种 pair 只 profiling 一次是去重并复用 profile，不能据此断言只测了一次迭代；§5 的最高 15% 尾部误差属于 primitive-level 组合估计这一低成本备选方案，默认使用的是实际 chunk-pair profiling。原文尚未给出 profile 的路由采样分布和方差，因此可写成未验证的稳健性边界，不能把实际分区不稳或 15% 路由误差写成已测事实。
- Confidence: high
- Sources: [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) — §3.1.2–3.1.3; printed p.292; PDF p.7 (including proceedings cover)； [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) — §5, Granularity of Cost Profiling; printed p.295; PDF p.10； [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) — §2.3.3; §3 introduction; Fig.5–6; PDF pp.5–6

## LS2-04-L2 (tessera) - applicability_limitation - mechanism_reported_consequence_inferred

**Bubble filling cannot remove a persistent hot-rank bottleneck when that rank lacks usable scheduling slack**

Tessera moves eligible work into rank-local idle slots; it does not redistribute expert work. Persistent routing skew can therefore limit its benefit when the same hot rank determines the iteration critical path and has insufficient eligible slots for deferred work. Filling waits on other ranks alone cannot eliminate that bottleneck. This is a conditional ceiling, not a requirement that hot ranks rotate: local dependency gaps, overlap between different microbatches, and pipeline waits can provide useful slots even with persistent skew. The paper reports such opportunities, so the hot rank cannot simply be assumed to have no idle time.

- Critical link: Use per-rank critical-path traces to establish whether the persistent hot rank actually lacks eligible slots, and separate routing-wait recovery from pipeline-wait recovery. Hot-rank identity alone is insufficient.
- Conditions: The same EP rank repeatedly lies on the iteration critical path because of routing skew; Its movable work cannot fit available local, communication, or pipeline waits before deadlines; No complementary expert redistribution or replication mechanism removes the sustained load imbalance; Compare DBO enabled and disabled with the same static partition and routing trace.
- Defeaters: The hot rank still has sufficient eligible local or pipeline idle slots; A different dependency, rather than hot-rank work, determines iteration completion and is shortened by DBO; Load balancing or changes in routing prevent a persistent critical-path bottleneck.
- Locations: §3.2.1–3.2.2, Fig.8 and Algorithm 2; §6.6 and Table 3; §7 Dynamic MoE Load Balancing. USENIX PDF pp.8–9, 14–15 (including cover).
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 原标题把热点 rank 轮换说成 DBO 有效的必要条件，正文又假设热点 rank 没有任何可填空隙，均过强。§3.2.1 明确有 local bubbles 与跨设备等待，两个 overlap chunk 可来自不同 microbatch；§6.6 还明确把额外收益归于 PP wait。能成立的是：若持续热点决定关键路径且没有可用本地空隙，其他 rank 的 bubble filling 无法消除该热点的工作量瓶颈。需将必要条件改成这一条件性上限。
- Confidence: high
- Sources: [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) — §3.2.1; Fig.8; printed p.293; PDF p.8； [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) — §3.2.2; Algorithm 2; PDF pp.8–9； [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) — §6.6; Table 3; printed p.299; PDF p.14

## LS2-05-L1 (distserve) - method_shortcoming - inferred

**Tuning prefill and decoding separately to the attainment target does not guarantee the joint TTFT-and-TPOT attainment target**

Algorithm 1 searches prefill and decoding configurations separately and replicates each phase according to its goodput. If both searches use the same 90% attainment target as the end-to-end goal, the two marginal guarantees alone do not imply that 90% of requests satisfy both constraints. With independent 90% marginal attainment the joint value is 81%; without an independence assumption it can be as low as 80%. These are conditional probability calculations, not measured DistServe results. Rounding headroom, overlapping failure sets, stricter marginal targets, or a joint validation step may close the gap. The concern applies to Algorithm 1, not automatically to the jointly simulated Algorithm 2 used in most testbed experiments.

- Critical link: Establish the actual marginal targets and whether the complete placement is jointly validated, then measure the overlap between TTFT and TPOT failure sets. The paper's pseudocode does not settle these implementation details.
- Conditions: The high-node-affinity Algorithm 1 is used; Each phase is sized to the end-to-end attainment target without a joint check or sufficient extra margin; TTFT and TPOT failures do not occur on essentially the same requests; Replica rounding adds too little headroom to remove the discrepancy.
- Defeaters: The complete placement passes joint end-to-end simulation or trace validation; For a 90% joint target, each marginal attainment is at least 95%; the union bound then suffices without assuming independence; If independence is established, marginal attainments of at least sqrt(0.9) suffice instead; Correlated failure sets or replica-rounding headroom keep measured joint attainment above the target.
- Locations: §4.1 and Algorithm 1; §4.2 and Algorithm 2; §6.1; §6.4 and Fig.11. USENIX PDF pp.8, 10–11, 13 (including cover).
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 核心可保留，但需轻量修改反证条件：每阶段目标提高到 sqrt(0.9) 只在独立假设下足以达到联合 90%；不假设依赖结构时，可把每阶段失败率控制在 5% 以内，用 union bound 保证联合至少 90%，或直接联合验证。§4.1 确实分别模拟两阶段并按 goodput 复制，但 81% 是条件性计算，非论文实测。主要真实集群实验采用 Algorithm 2；未据公开实现额外确认 Algorithm 1 是否加严 per-phase 目标。
- Confidence: medium
- Sources: [S05](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf) — §4.1; Algorithm 1; printed p.199; PDF p.8； [S05](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf) — Abstract; §2; §6.1 experiment setup; PDF pp.2, 4, 10

## LS2-05-L2 (distserve) - applicability_limitation - mechanism_reported_consequence_inferred

**A finite prefill-side KV buffer can propagate sustained decode congestion to later prefill admission**

DistServe lets decoding instances pull completed KV caches from prefill-side GPU memory, which temporarily buffers a rate mismatch. That buffer has finite capacity. If completed-prefill KV accumulates faster than decoding can accept it for long enough, and no other release mechanism intervenes, admitting subsequent prefills must eventually slow or stop. Their TTFT can then rise through queueing backpressure even though prefill and decode computation remain on separate GPUs. The paper includes periodic replanning; the relevant limitation is whether buffering and adaptation can absorb a particular burst or workload shift, not whether disaggregation removes all possible queueing dependence.

- Critical link: Compare the accumulated bytes of completed-prefill KV waiting for decode with available prefill buffer capacity, and compare the buffer-fill time with replanning and reconfiguration latency.
- Conditions: The byte-weighted rate of completed-prefill KV exceeds decode acceptance for a sustained interval; The resulting backlog exceeds the prefill-side capacity available after other live allocations; Replanning, scaling, offload, or another buffer-release mechanism does not intervene before capacity is reached.
- Defeaters: Decode headroom or prompt/cache size makes the transient backlog fit within the buffer; Replanning or scaling restores balance before the buffer fills; Another KV storage tier or explicit overload policy absorbs the backlog while preserving the required TTFT.
- Locations: §4.3 Combat burstiness and Replanning, Fig.6; §6.1 workloads. USENIX PDF pp.9–10 (including cover).
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 有限 KV 缓冲下产生背压的推理成立，但应避免把排队耦合表述为计算干扰重新出现，或宣称解耦整体只在短突发时有效。论文已实现 workload shift 检测与周期性 replanning，而非完全不处理长期失衡。修订后明确：必须是积压超过可用缓冲、且扩容/重规划/其他释放手段来不及生效，才会拖慢后续 prefill 的接纳与 TTFT；这仍是待 trace 验证的条件性限制。
- Confidence: high
- Sources: [S05](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf) — §4.3 Combat burstiness and Replanning; Fig.6; printed p.200; PDF p.9； [S05](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf) — §6.1 Model and workloads setup; PDF p.10

## LS2-06-L1 (sarathi) - applicability_limitation - mixed_reported_and_inferred

**A fixed token budget bounds the token count per iteration, not its latency, once attention over long contexts dominates**

Stall-free batching caps the number of tokens per iteration at a token budget. That budget is chosen once by profiling, as the largest token count that does not violate the TBT SLO. The paper claims this bounds iteration latency and makes it nearly independent of prompt length. That holds when linear layers dominate cost, which the paper shows for sequences of up to a few thousand tokens. Attention cost per token grows with context length, both for later chunks of a long prompt (which re-read all earlier chunks' KV) and for decodes with long KV caches. With much longer contexts than those evaluated (requests over 8K/16K tokens were filtered out), the same token budget may produce iterations that exceed the TBT SLO. Alternatively, the budget has to be calibrated for the worst-case context, which lowers throughput for everyone.

- Critical link: How large attention's share of iteration time becomes for the contexts actually served. Below roughly 8-16K tokens on the evaluated models it appears small, which is why the evaluation does not show the effect.
- Conditions: Prompt or decode contexts well beyond the evaluated 8K/16K-token range.; A single fixed token budget per deployment, as in the evaluation.; A TBT SLO tight enough that context-dependent attention time matters.
- Defeaters: The budget is profiled at the maximum supported context, accepting lower efficiency.; The budget is adjusted dynamically by context length (the paper names dynamic budgets as future work; later systems shrink chunks over a prompt).; Attention kernels or sliding-window/GQA models keep attention cost small even at long contexts.
- Locations: §1; PDF page 3; §3.1 Fig. 4; PDF page 5; §4.3; PDF page 9; §5 Workloads; Table 2; PDF page 10; §5.4.1 Fig. 14; PDF page 13
- Verified locations: §3.1 and Fig.4; §4.3; §5 Workloads and Table 2; §5.1; §5.4.1 and Fig.14. USENIX PDF pp.6, 10–12, 14 (including cover).
- Review: [x] keep  [ ] edit  [ ] drop
- Review rationale（中文）: 保留为超出已测上下文范围时的条件性限制。论文确实用一次性 profiling/部署配置选择 token budget，讨论先前 chunk KV 重读，并把动态 budget 留为未来工作。§5 按数据集剔除了总长超过 8192/16384 的请求；因此固定 token 数不是任意上下文长度下的时延定理。这里的长上下文超 SLO 是机制推断，不能写成论文已观察到退化；现有 GQA/滑窗模型、最大长度 profiling 等反证条件应保留。
- Confidence: high
- Sources: [S06](https://www.usenix.org/system/files/osdi24-agrawal.pdf) — §4.3; printed p.125; PDF p.10； [S06](https://www.usenix.org/system/files/osdi24-agrawal.pdf) — §5 Workloads; §5.1; printed pp.126–127; PDF pp.11–12

## LS2-06-L2 (sarathi) - method_shortcoming - mixed_reported_and_inferred

**Decode-first packing moves interference onto prefill progress, so TTFT tails can grow with the decode batch**

Stall-free batching first packs every running decode into the budget, then any partially completed prefill, and admits new requests only with the leftover tokens. Each decode uses one budget slot. As the running decode batch grows toward its maximum, the share of the budget left for prefill shrinks, so a long prompt needs more iterations to finish prefill. Prefills therefore still wait on decodes: the interference is moved into slower prefill progress rather than removed. The evaluation defines capacity using P99 TBT and a median scheduling-delay limit, and reports median TTFT. TTFT tails for long prompts under heavy decode load are not covered by this capacity metric.

- Critical link: How much of the budget running decodes actually use at the operating point (decode batch size relative to budget), and whether TTFT tails, not medians, would bind the capacity.
- Conditions: A strict (small) token budget with a large running decode batch.; Long prompts that need many chunks.; An SLO that constrains TTFT tail latency, not only the median scheduling delay.
- Defeaters: Decode batches stay small relative to the budget at the operating point.; A relaxed SLO allows a large budget (2048), so the decode share is minor.; TTFT P99 measurements show no meaningful growth over the baselines at the reported capacity.
- Locations: §4.2; Algorithm 3; PDF pages 8-9; §5 Metrics; §5.1; PDF page 10; §5.4.2; Table 4; PDF page 13
- Verified locations: §4.2 and Algorithm 3; §5 Metrics; §5.1; Fig.12; §5.4.2 and Table 4. USENIX PDF pp.9–11, 13–14 (including cover).
- Review: [x] keep  [ ] edit  [ ] drop
- Review rationale（中文）: 保留。Algorithm 3 的顺序确为 running decodes→partly completed prefill→new requests，因而固定 budget 下 decode 份额增加会减少可用 prefill token；P50 TTFT 与 median scheduling delay≤2s 也不能约束 P99 TTFT。不过这只说明机制与评估盲区，并非证明实际实验发生严重 TTFT 尾退化。Fig.12 的最大 batch 是 128、budget 是 512/2048，不能扩写为实验配置下 prefill 必然耗尽配额或饿死。
- Confidence: high
- Sources: [S06](https://www.usenix.org/system/files/osdi24-agrawal.pdf) — §4.2; Algorithm 3; printed pp.124–125; PDF pp.9–10； [S06](https://www.usenix.org/system/files/osdi24-agrawal.pdf) — §5 Metrics; §5.1; printed p.126; PDF p.11； [S06](https://www.usenix.org/system/files/osdi24-agrawal.pdf) — Fig.12; Table 4; printed pp.128–129; PDF pp.13–14

## LS2-07-L1 (streamingllm) - applicability_limitation - mixed_reported_and_inferred

**A small sink region does not preserve the full opening prompt after it leaves the recent window**

In the four-sink configuration, opening-prompt tokens beyond the first four eventually leave the cache. Stable perplexity therefore does not establish persistent access to those instructions. Table 8 reports that 1750+1750 recovers performance relative to 4+3496; the authors suggest loss of initial input information as an explanation. That comparison neither isolates instruction following nor establishes 1750 as a required threshold. For dialogue whose later answers depend on opening instructions, the risk is conditional on those instructions not being pinned, repeated, or adequately represented in retained states. Enlarging the retained prefix trades away recent context at a fixed budget.

- Critical link: Measure instruction adherence before and after eviction while controlling the retained prefix, recent context, and total cache budget; LongBench prompt retention is supporting evidence, not a dialogue-persistence test.
- Conditions: Task-relevant opening instructions extend beyond the retained prefix and have left the recent window; Their information is not sufficiently preserved in retained states or repeated in later turns.
- Defeaters: Pinning or reinjecting the relevant instructions preserves adherence within the same memory budget; A controlled multi-turn evaluation finds no material adherence loss after eviction.
- Locations: §3.2; §4.3; Appendix A (Limitations); Appendix D, Table 8; official configurable streaming example
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 核心边界成立，但原稿把 Table 8 的因果解释和配置要求写得过强。作者仅将 4+3496 的下降归因于初始输入信息丢失的可能性；1750+1750 是一个已测试的恢复配置，不是已证明唯一或最低的必要配置。该实验也没有单独测量多轮聊天中的系统指令遵循。应保留缓存淘汰这一事实，把指令漂移明确写成条件性风险。
- Confidence: high
- Sources: [S07](https://arxiv.org/html/2309.17453v4#S3.SS2) — §3.2; Appendix A; Appendix D, Table 8； [S13](https://github.com/mit-han-lab/streaming-llm/blob/main/examples/run_streaming_llama.py) — main arguments: start_size and recent_size; streaming_inference

## LS2-07-L2 (streamingllm) - mechanism_origin_unclear - mixed_reported_and_inferred

**Non-monotone cache-size results leave the source of degradation unresolved**

Table 6 establishes that a larger StreamingLLM cache need not improve perplexity in the tested models. It does not identify the cause. Cache-relative positioning and reuse of contextualized states are possible contributors alongside the base model's context use. However, §3.2 explicitly reapplies RoPE to cached unrotated keys, so this is not evidence of stale rotary transformations. A plain sliding-window recomputation comparison would also change the retained information and sink treatment. Attribution requires controls that separate these changes. Cache size should consequently be validated for the target model rather than assumed to improve quality monotonically.

- Critical link: Compare state reuse and recomputation while matching retained token identities, sink treatment, and positional policy; separately vary positioning. A difference from ordinary sliding-window recomputation alone does not identify the cause.
- Conditions: The non-monotone pattern reproduces across texts or seeds at the deployment-relevant cache sizes; Cache size is selected for quality as well as memory or latency.
- Defeaters: Matched controls show that the observed pattern is explained by the base model and retained context, with no additional effect from state reuse or positioning; The pattern disappears on representative target data or tasks.
- Locations: §3.2, Figure 4; §4.1; §4.4, Table 6
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: Table 6 的非单调结果核对无误：Llama-2-7B 从 2048 到 4096 总缓存时 PPL 9.08→9.59；Falcon-7B 从 1024 到 2048 时 12.34→12.84；MPT-7B 随四档缓存递增而变差。需要修改的是机制推断：§3.2 明确缓存旋转前的 key 并重新施加当前缓存位置的 RoPE，不能暗示直接使用过时的旋转 key。缓存隐藏状态的上下文历史仍可作为候选因素，但未证实。普通 sliding-window recomputation 同时改变 sink/近期 token 集合和上下文，单独比较不能二分证明“模型原因”或“方法原因”。
- Confidence: high
- Metadata change: `mechanism_origin_unclear` / `mechanism_reported_consequence_inferred` → `mechanism_origin_unclear` / `mixed_reported_and_inferred`.
- Sources: [S07](https://arxiv.org/html/2309.17453v4#S4.SS4) — §4.4, Table 6； [S07](https://arxiv.org/html/2309.17453v4#S3.SS2) — §3.2, Rolling KV Cache with Attention Sinks

## LS2-08-L1 (h2o) - method_shortcoming - mechanism_reported_consequence_inferred

**Irreversible eviction cannot recover a key whose relevance rises after its removal**

H2O retains keys using accumulated attention plus a recent-token reserve. A key removed before a later query needs it is unavailable to that query unless its information survives elsewhere. This is a conditional weakness when future relevance differs from the available attention history. The timing matters: Appendix A selects the reduced cache after prefill, so a question at the end of one fully processed prompt is not automatically unseen before selection. It can contribute to the scores, although that contribution may still be insufficient. Appendix C.4 tests document-before-question inputs, but does not isolate low-score-at-eviction cases against a full-cache reference.

- Critical link: Track whether answer-bearing keys are present at the actual eviction boundary and how their absence changes output relative to full cache, separating full-prefill from streaming or chunked ingestion.
- Conditions: A needed key is evicted before its decisive later use, or scores too low for the post-prefill retained set; The cache budget creates eviction pressure and retained states do not preserve enough of its information.
- Defeaters: Query-aware prefill scoring or the recent-token reserve consistently retains the needed keys; Controlled delayed-relevance tests match full-cache accuracy at the claimed budget.
- Locations: §3.2; §4.1; Algorithm 1; Appendix A; Appendix C.4, Figure 9; corroborating later evidence: Quest §3.3 and Table 1
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 不可恢复淘汰与未来需求变化之间的风险成立，但原稿需要区分在线/分块输入与一次完整 prefill。Appendix A 的系统实现先计算 prefill attention，再保留 K 个 heavy hitters 与 K 个 recent tokens。因此同一完整 prompt 中“问题放在末尾”本身并不证明证据已在问题到达前淘汰；仍可能因累计分数竞争而在 prefill 后丢失。应把核心条件改为“相关 query 在实际淘汰之后到达，或其贡献不足以让 key 进入保留集”。Appendix C.4 确有文末问题的多文档 QA 对照，不能说完全未测此类任务。Quest 后续实验提供支持，但其具体 H2O 基线实现不宜追溯当作原系统完全相同的行为。
- Confidence: high
- Sources: [S08](https://proceedings.neurips.cc/paper_files/paper/2023/file/6ceefa7b15572587b78ecfcebb2827f8-Paper-Conference.pdf) — §4.1; Algorithm 1; Appendix A, prefill compute_attention/select; Appendix C.4, Figure 9； [S09](https://arxiv.org/html/2406.10774v2#S3.SS3) — §3.3, Figure 4; §4.2.2, Table 1

## LS2-08-L2 (h2o) - mechanism_origin_unclear - mixed_reported_and_inferred

**Heavy-hitter utility is established more clearly than the relative roles of content, position, and frequency**

H2O's ablations support the usefulness of its selected keys, but do not fully separate why those keys receive accumulated attention. Semantic information, repeated occurrence, positional exposure, and sink-like behavior can coexist. Crucially, Appendix C.4 already compares H2O with matched-budget initial-plus-local policies, including 256+256, and favors H2O. This weakens a simple explanation based only on retaining initial tokens. The narrower unresolved question is how much each mechanism contributes and whether that balance predicts transfer to other domains. The attention-score guarantee does not by itself settle this causal question or establish downstream failure under distribution shift.

- Critical link: Use token-level analyses and controlled content/position/frequency interventions to explain the incremental benefit over the existing matched-budget initial-plus-local baselines.
- Conditions: The label is used as an open mechanism question, not as evidence of measured cross-domain degradation; A target domain materially changes the candidate mechanisms and the retained-key competition.
- Defeaters: Controlled interventions explain which retained tokens matter and accurately predict transfer; The existing matched-budget initial-plus-local results already contradict a claim that H2O merely preserves a fixed initial prefix.
- Locations: §3.2, Figure 2; §4.2; Appendix B.2; Appendix C.4, Figure 9; Appendix C.6, Table 9
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 机制分解仍未解决，但原稿把关键对照说成不存在，且低估了已有反证。Appendix C.4 Figure 9 除 4+508 外还比较 StreamingLLM-256-256 与 H2O-256-256，H2O 更好；不能再说缺少等预算 sink/initial+local baseline，也不能仅称对照是四个 sink tokens。B.2 的累计分数年龄偏置和平均分数消融确实存在。应将问题收窄为 semantic、frequency、position 与注意力归一化贡献尚未分离，不把它们写成互斥解释或据此断言跨域性能会变差。
- Confidence: high
- Sources: [S08](https://proceedings.neurips.cc/paper_files/paper/2023/file/6ceefa7b15572587b78ecfcebb2827f8-Paper-Conference.pdf) — §3.2, Figure 2; Appendix B.2; Appendix C.4, Figure 9; Appendix C.6, Table 9； [S07](https://arxiv.org/html/2309.17453v4#S3.SS1) — §3.1, Table 1

## LS2-09-L1 (quest) - method_shortcoming - mechanism_reported_consequence_inferred

**Pagewise min/max bounds can over-rank pages; the accuracy effect of larger pages is unmeasured**

Quest's score can combine extrema from different keys, so a high page bound need not correspond to a high-scoring real token. For example, with q=(1,1), keys (10,0) and (0,10) give bound 20 although their best dot product is 10; a page containing two copies of (6,6) has bound and true maximum 12. The bound can therefore select the wrong page at a tight budget. Larger pages reduce metadata traffic, but do not necessarily worsen the bound gap: both the bound and the true page maximum can increase. The score also remains query-dependent. An accuracy sweep at fixed token budget is needed to quantify the practical trade-off.

- Critical link: Measure true critical-token recall, bound gaps, and task accuracy as page size varies, holding total token budget B fixed so that selected-page count is approximately B/S.
- Conditions: Within-page key diversity makes the componentwise bound substantially exceed actual dot products; Misranked pages displace required pages at the selected token budget.
- Defeaters: Key coherence keeps bounds sufficiently discriminative across practical page sizes; Fixed-budget page-size sweeps preserve recall and task accuracy with acceptable latency.
- Locations: §3.4, Figure 5 and Algorithm 1; §3.5; §4.3.1, Figure 8
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 逐通道 min/max 拼出的上界确会由不同 token 提供，能产生页排序假阳性；此数学批评成立。需删掉两个未成立的强结论：增大 page 会使包围盒及其上界不减，但真实最高 q·k 也会变大，上界与真实最大值的差距不保证单调变大；评分始终依赖 query，不能概括成向 query-agnostic magnitude ranking 必然退化。还须固定 token budget B 来讨论 page size，否则固定 K 时页变大同时增加读取 token 数，准确率/开销结论会混淆。论文 page-size sweep 为效率，未提供对应准确率扫参。
- Confidence: high
- Sources: [S09](https://arxiv.org/html/2406.10774v2#S3.SS4) — §3.4, Algorithm 1; §3.5; §4.3.1, Figure 8

## LS2-09-L2 (quest) - applicability_limitation - inferred

**Quest's reported speedups do not establish the same savings for GQA implementations**

The paper's evaluated models and single-batch decoding results do not establish GQA-specific speedups. With g query heads sharing a KV head, each head can retain its own page selection. If each selects K of N pages, the number of distinct pages requested by the group lies between K and min(gK,N). Under ideal cross-head reuse, replacing K by that union size gives a corresponding group-level byte estimate; actual traffic also depends on metadata reuse, caches, and kernel design. Shared selection is an alternative with its own accuracy trade-off, not a requirement of GQA. Consequently the paper's savings formula needs an explicit implementation and overlap assumption when extrapolated to GQA. Later model support does not supply those missing measurements.

- Critical link: Measure per-group page overlap, actual memory traffic, selection overhead, and end-to-end decode latency against an optimized dense GQA baseline at matched accuracy.
- Conditions: Query heads in a GQA group select sufficiently different pages to limit shared-load reuse; The remaining KV-memory cost is large enough for sparsity to affect overall decode time.
- Defeaters: High page overlap and efficient shared loads preserve the expected memory savings; A group-level selection method or independent-head kernel achieves the claimed speedup at matched accuracy on GQA models.
- Locations: Quest §3.5, §4.1, §4.3.2 and Figure 10; GQA §1–2; later official repository support announcement (separate from original-paper evidence)
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 原论文只在所列 MHA 模型及 single-batch decode 场景报告加速，GQA 性能外推缺少实测是合理局限。但“只能统一加载 union 或统一 selection”不是架构必然二选一：query heads 可独立稀疏读取共享 KV，union 描述跨 head 的不同页面集合，HBM 流量还受缓存和 kernel 复用影响。对于 g 个 query heads、N 页、各选 K 页，理想去重后的 union 大小介于 K 和 min(gK,N)；这并不等于实际流量必然放大 g 倍。当前官方仓库已公告 2024/10 的 Llama-3.1/Mistral 支持，故将条目严格限定于论文证据与实现相关性能，不能暗示现今算法不兼容 GQA。
- Confidence: high
- Sources: [S09](https://arxiv.org/html/2406.10774v2#S3.SS5) — §3.5; §4.1; §4.3.1–4.3.2, Figures 9–10； [S14](https://aclanthology.org/2023.emnlp-main.298.pdf) — §1–2; Figure 1； [S15](https://github.com/mit-han-lab/Quest) — News, 2024/10; scripts/passkey.sh example

## LS2-10-L1 (awq) - applicability_limitation - mechanism_reported_consequence_inferred

**AWQ's zero-extra-operation scaling depends on the operator graph and on compensating every affected consumer**

AWQ requires an equivalent transformation of the computation graph. A producer need not itself be linear: its output parameters can sometimes absorb inverse scaling, and a shared tensor can be rescaled if every consumer is compensated consistently. Joint scaling can nevertheless restrict the available search space. For a non-homogeneous activation, an explicit output scaling operation or kernel fusion may be needed. These constraints can create architecture-specific implementation costs or leave some layers unscaled; they do not establish an accuracy loss. Shared q/k/v inputs already occur in the evaluated families, and the paper includes GQA results. A defensible limitation is that free folding and independent per-layer scaling cannot be assumed for every graph.

- Critical link: Measure which layers cannot be folded or require joint scales, then isolate their accuracy contribution and any additional runtime operations.
- Conditions: An affected producer cannot absorb inverse scaling through an equivalent parameter change, or several consumers require coupled scaling; Affected layers contribute materially to quantization error or the extra operation is not fused; The comparison fixes the model, bit width, group size, calibration data, and inference kernels.
- Defeaters: Joint scaling preserves accuracy, or skipping the affected scale has negligible effect; A fused activation or GEMM epilogue performs the extra scale at negligible cost; Measured end-to-end accuracy and latency remain competitive on the target architecture.
- Locations: AWQ arXiv:2306.00978v4, §3.2 Eq. 4–5; §5.2 Table 5; official auto_scale.py: scale_ln_fcs, auto_scale_block, apply_scale.
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 原文把“可免费折叠”错误地限定为整个前驱必须线性且只能有一个消费者。LayerNorm/RMSNorm 可通过输出仿射参数吸收缩放；共享输入也可同时补偿所有消费者。官方实现已对 q/k/v 联合搜索缩放，对 GELU 使用 ScaledActivation，并在部分 GQA 形状下跳过 v_proj→o_proj 缩放。论文 Table 5 还报告了 Mistral/Mixtral 的 GQA 结果。因此保留架构相关的融合与搜索约束，删除“超出 LLaMA/OPT 就较弱”的泛化；精度/延迟损失须实测。
- Confidence: high
- Sources: [S10](https://arxiv.org/html/2306.00978v4) — §3.2, Eq. 4–5; §5.2, Table 5； [S12](https://github.com/mit-han-lab/llm-awq/blob/main/awq/quantize/auto_scale.py) — scale_ln_fcs; auto_scale_block (Llama/Qwen2 branches); apply_scale

## LS2-10-L2 (awq) - applicability_limitation - mechanism_reported_consequence_inferred

**A calibration-derived scaling family can miss rare or shifted activation patterns despite output-error tuning**

The remaining concern is whether calibration adequately represents deployment inputs. AWQ does not rely on activation ranking alone: it chooses a scale exponent using calibration output error, and the paper offers both an error analysis and cross-task evidence. Nevertheless, a finite calibration set can miss rare events, and a scale family built from per-channel means cannot express every possible channel ranking. If deployment requires a different allocation of quantization precision, the fixed scales may be suboptimal. This is an unmeasured conditional generalization risk, not an established failure on code, visual inputs, or instruction following, all of which receive positive evidence in the paper.

- Critical link: Compare matched and mismatched calibration sets on the same deployment distribution, measuring channel rankings, output errors, and task quality; separate this from generic low-bit quantization loss.
- Conditions: Important deployment activations are absent or seriously underrepresented in calibration, or their relative channel importance changes; The restricted scaling family, clipping, and group-wise quantization fail to absorb that change; The bit width, group size, model, and evaluation data are held fixed.
- Defeaters: Target-domain calibration provides no meaningful improvement; Channel saliency remains stable across the actual deployment distributions; Existing task results generalize to the proposed shift, including rare-event slices.
- Locations: AWQ arXiv:2306.00978v4, §3.1–3.2 Eq. 4–5; §5.2 Tables 6–8; §5.3 Fig. 8; official auto_scale.py: get_act_scale and _search_module_scale.
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: “重要特征”的语义解释确为假说，但算法并非仅凭均值排序：§3.2 有量化误差推导，Eq. 4–5 用校准输出误差选择 α，另有权重裁剪。可保留的是有限校准数据和受限缩放族面对罕见激活/分布变化的条件性风险，宜改归 applicability_limitation。论文已有指令、视觉、编程与数学任务结果，须作为反证，不能笼统说这些领域未覆盖。
- Confidence: high
- Metadata change: `mechanism_origin_unclear` / `mixed_reported_and_inferred` → `applicability_limitation` / `mechanism_reported_consequence_inferred`.
- Sources: [S10](https://arxiv.org/html/2306.00978v4) — §3.1–3.2, Eq. 4–5; §5.2 Tables 6–8; §5.3 Fig. 8； [S12](https://github.com/mit-han-lab/llm-awq/blob/main/awq/quantize/auto_scale.py) — get_act_scale; _search_module_scale

## LS2-11-L1 (vattention) - applicability_limitation - mixed_reported_and_inferred

**Fixed byte-sized pages can become coarse in token units when each worker holds few KV heads**

Without tensor slicing, the allocation quantum in tokens is G/(H_worker D P), where G is the page-group size and P is bytes per KV element. It grows with tensor parallelism only while KV heads are actually sharded, and also grows at lower KV precision. For example, a 64KiB group with one 128-dimensional KV head holds 256 FP16 tokens or 512 one-byte tokens. These are derived examples, not measurements from the paper. The issue is increased relative waste for short requests. Rounding-only internal fragmentation remains below one page-group per request, per layer, and per K or V tensor; eagerly mapped reserves and deferred-reclamation capacity are additional allocations. The paper already evaluates GQA at TP-1/TP-2, so the open question concerns more extreme per-worker layouts and small-token-block comparators, not GQA as an untested category.

- Critical link: Measure aggregate tail-page waste and achievable batch size at the target head-sharding, KV precision, request-length distribution, and comparator block size.
- Conditions: Few KV heads per worker or lower KV precision make the token quantum large; Many requests have short contexts relative to that quantum, and KV capacity limits batching; Tensor slicing is absent and the PagedAttention comparator uses substantially smaller token blocks.
- Defeaters: Supported tensor slicing or finer physical pages reduce the quantum; Long requests make the unused tail a negligible fraction of memory; The relevant PagedAttention kernel uses comparably large token blocks.
- Locations: vAttention arXiv:2405.04437v3, §5.1.3; §7 Table 5; §7.6.3 Table 8 and Fig. 15; §8.2 Table 10.
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 64KB 对应的 token 数确由每个 worker 的 KV 字节数决定，但不能无限随 TP 成比例增加：KV heads 不再细分、改为复制时该关系停止。原文也容易暗示 GQA 未被评测，实际 Table 5 的三个模型均是 GQA。另需区分 token 粒度/相对浪费与每个 tensor 尾页的绝对字节上界；纯取整浪费仍小于一页，但不包括提前映射与延迟回收保留的容量。将绝对化标题改为条件性限制，并保留 tensor slicing 与具体 PagedAttention block 大小的影响。
- Confidence: high
- Sources: [S11](https://arxiv.org/html/2405.04437v3) — §5.1.3; Tables 5 and 8; §7.6.3; §8.2 and Table 10

## LS2-11-L2 (vattention) - method_shortcoming - mixed_reported_and_inferred

**Prefill allocation can re-enter the critical path when reuse and eager mapping do not cover the arriving prompt**

Deferred reclamation and eager mapping reduce allocation work but do not guarantee that an arriving prompt is fully mapped. A short recycled slot or insufficient eagerly mapped capacity can require additional mapping before prefill. Frequent misses could make small-page allocation overhead visible under memory pressure, but the paper does not establish their frequency or an end-to-end regression. Its dynamic and online evaluations provide counterevidence to a blanket failure claim. The unresolved issue is the conditional tail-latency cost of mapping misses at high KV occupancy, rather than the absence of variable-length workloads.

- Critical link: Under controlled near-capacity traces, report reused/pre-mapped coverage, synchronous mapping time, and TTFT percentiles by page size; separate memory pressure from ordinary queueing and attention-kernel effects.
- Conditions: Small page-groups are used and the mapped reserve is often insufficient; New prompt lengths exceed recycled-slot coverage often enough to matter; Additional mappings cannot be completed before prefill begins, and their cost is material relative to compute.
- Defeaters: Measured reuse and eager-mapping hit rates remain high at the target occupancy; Chunked scheduling or look-ahead overlaps the remaining allocations; Near-capacity TTFT measurements show negligible mapping overhead; Faster attention and larger feasible batches outweigh the residual allocation cost.
- Locations: vAttention arXiv:2405.04437v3, §6.1.2; §7.4 Fig. 10; §7.6.2 Fig. 13; §7.6.3 Fig. 15; §7.6.4 Table 9.
- Review: [ ] keep  [x] edit  [ ] drop
- Review rationale（中文）: 复用槽位和预映射备用页不足时会触发同步补映射，这一机制性疑问成立；但“压力大就最弱/经常失败”未被证明。论文并非只有单提示或定长测试：§7.4 有接近服务容量的在线变长轨迹，Fig.15 还有 OpenChat 动态负载的小页收益。真正缺口是未单独报告高 KV 压力下复用命中率、临界路径映射比例和 TTFT 尾延迟。7.59/35.17 GB/s 是分配带宽，不能直接当请求延迟。
- Confidence: high
- Sources: [S11](https://arxiv.org/html/2405.04437v3) — §6.1.2; §7.4; §7.6.2 Fig. 13; §7.6.3 Fig. 15; Table 9

## 一手来源目录

| 来源 | 文献 / 实现 | 核查版本 |
| --- | --- | --- |
| [S01](https://arxiv.org/html/2502.20766v1) | FlexPrefill: A Context-Aware Sparse Attention Mechanism for Efficient Long-Sequence Inference | arXiv:2502.20766v1（2025-02-28） |
| [S02](https://arxiv.org/html/2609.04724v2) | FlexPosit: Tunable Fractional Precision for LLM Inference Accelerators | arXiv:2609.04724v2（2026-09-13） |
| [S03](https://www.microsoft.com/en-us/research/wp-content/uploads/2025/10/QoServe_CC_final_v2.pdf) | QoServe: Breaking the Silos of LLM Inference Serving | 微软官方 ASPLOS 2026 定稿，QoServe_CC_final_v2.pdf；按 PDF 出版信息识别版本 |
| [S04](https://www.usenix.org/system/files/osdi26-hu-weifang.pdf) | Tessera: A Holistic Pipeline Parallelism Framework for Trillion-Parameter Heterogeneous MoE Training | USENIX OSDI 2026 proceedings PDF（含封面） |
| [S05](https://www.usenix.org/system/files/osdi24-zhong-yinmin.pdf) | DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving | USENIX OSDI 2024 proceedings PDF（含封面） |
| [S06](https://www.usenix.org/system/files/osdi24-agrawal.pdf) | Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve | USENIX OSDI 2024 proceedings PDF（含封面） |
| [S07](https://arxiv.org/html/2309.17453v4) | Efficient Streaming Language Models with Attention Sinks | arXiv:2309.17453v4（2024-04-07） |
| [S08](https://proceedings.neurips.cc/paper_files/paper/2023/file/6ceefa7b15572587b78ecfcebb2827f8-Paper-Conference.pdf) | H₂O: Heavy-Hitter Oracle for Efficient Generative Inference of Large Language Models | NeurIPS 2023 proceedings PDF，含附录 |
| [S09](https://arxiv.org/html/2406.10774v2) | Quest: Query-Aware Sparsity for Efficient Long-Context LLM Inference | arXiv:2406.10774v2（2024-08-26） |
| [S10](https://arxiv.org/html/2306.00978v4) | AWQ: Activation-aware Weight Quantization for On-Device LLM Compression and Acceleration | arXiv:2306.00978v4（2024-04-23）；核查 §3.2、Table 5 和 §5.3 |
| [S11](https://arxiv.org/html/2405.04437v3) | vAttention: Dynamic Memory Management for Serving LLMs without PagedAttention | arXiv:2405.04437v3（2025-01-29），ASPLOS 2025 |
| [S12](https://github.com/mit-han-lab/llm-awq/blob/main/awq/quantize/auto_scale.py) | AWQ official implementation: auto_scale.py | 官方仓库当前可访问代码；访问日期 2026-11-23 |
| [S13](https://github.com/mit-han-lab/streaming-llm/blob/main/examples/run_streaming_llama.py) | StreamingLLM official streaming example | 官方仓库当前可访问代码；访问日期 2026-11-23 |
| [S14](https://aclanthology.org/2023.emnlp-main.298.pdf) | GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints | EMNLP 2023 原论文 |
| [S15](https://github.com/mit-han-lab/Quest) | Quest official repository | 后续支持公告及实现说明；访问日期 2026-11-23 |

## 完整性核对

- 22 个原始标签 ID 均已保留，顺序与附件一致。
- 每条仅勾选一个 keep / edit / drop。
- 19 条 edit 均有完整替代文案；3 条 keep 均有证据核查说明。
- 已保留“未经人工审查”的状态，未将文献推断标记为复现实验结果。
