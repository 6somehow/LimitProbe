# Limitations report: InfiniGen: Efficient Generative Inference of Large Language Models with Dynamic KV Cache Management

- artifact: `infinigen` (OSDI 2024), repository https://github.com/snu-comparch/InfiniGen at `3754f52d13`
- input: `results/step4/infinigen/limitations_for_tests.json` (sha256 `51f6ee77be8f`), 31 Findings
- generated: 2026-11-16T16:10:00+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
- environment: **not_ok** (repository third_party/InfiniGen is not checked out)

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 31 |
| tested | 0 |
| not tested | 31 |
| not tested, by reason | `env_unavailable` 20, `no_code_location` 11 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [infinigen-F001](#infinigen-f001) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:426` | not tested: `env_unavailable` |
| [infinigen-F002](#infinigen-f002) | undisclosed | state | `speedup/flexgen/infinigen/flex_opt.py:442` | not tested: `env_unavailable` |
| [infinigen-F003](#infinigen-f003) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:466` | not tested: `env_unavailable` |
| [infinigen-F004](#infinigen-f004) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:710` | not tested: `env_unavailable` |
| [infinigen-F005](#infinigen-f005) | undisclosed | reject | `speedup/flexgen/infinigen/flex_opt.py:1359` | not tested: `env_unavailable` |
| [infinigen-F006](#infinigen-f006) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:464` | not tested: `env_unavailable` |
| [infinigen-F007](#infinigen-f007) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:823` | not tested: `env_unavailable` |
| [infinigen-F008](#infinigen-f008) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:881` | not tested: `env_unavailable` |
| [infinigen-F009](#infinigen-f009) | stated_differently | path_change | `speedup/flexgen/infinigen/flex_opt.py:287` | not tested: `env_unavailable` |
| [infinigen-F010](#infinigen-f010) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:389` | not tested: `env_unavailable` |
| [infinigen-F011](#infinigen-f011) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:528` | not tested: `env_unavailable` |
| [infinigen-F012](#infinigen-f012) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:541` | not tested: `env_unavailable` |
| [infinigen-F013](#infinigen-f013) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:799` | not tested: `env_unavailable` |
| [infinigen-F014](#infinigen-f014) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:401` | not tested: `env_unavailable` |
| [infinigen-F015](#infinigen-f015) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:422` | not tested: `env_unavailable` |
| [infinigen-F016](#infinigen-f016) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:479` | not tested: `env_unavailable` |
| [infinigen-F017](#infinigen-f017) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:767` | not tested: `env_unavailable` |
| [infinigen-F018](#infinigen-f018) | impl_deviates | other | `accuracy/perplexity/table2.sh:27-45` | not tested: `no_code_location` |
| [infinigen-F019](#infinigen-f019) | impl_deviates | other | `accuracy/perplexity/table2.sh:27-45` | not tested: `no_code_location` |
| [infinigen-F020](#infinigen-f020) | impl_deviates | other | `speedup/flexgen/infinigen/flex_opt.py:282` | not tested: `no_code_location` |
| [infinigen-F021](#infinigen-f021) | impl_deviates | other | `speedup/flexgen/infinigen/flex_opt.py:513-524` | not tested: `no_code_location` |
| [infinigen-F022](#infinigen-f022) | impl_deviates | other | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | not tested: `no_code_location` |
| [infinigen-F023](#infinigen-f023) | impl_deviates | other | `speedup/infinigen/infinigen/kv_selection_controller.py:28-63` | not tested: `no_code_location` |
| [infinigen-F024](#infinigen-f024) | impl_deviates | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location` |
| [infinigen-F025](#infinigen-f025) | impl_deviates | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location` |
| [infinigen-F026](#infinigen-f026) | impl_deviates | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location` |
| [infinigen-F027](#infinigen-f027) | undisclosed | path_change | `speedup/flexgen/infinigen/flex_opt.py:690` | not tested: `env_unavailable` |
| [infinigen-F028](#infinigen-f028) | undisclosed | path_change | `speedup/flexgen/infinigen/pytorch_backend.py:326` | not tested: `env_unavailable` |
| [infinigen-F029](#infinigen-f029) | undisclosed | reject | `speedup/flexgen/infinigen/pytorch_backend.py:837` | not tested: `env_unavailable` |
| [infinigen-F030](#infinigen-f030) | not_implemented | other | `accuracy/perplexity/table2.sh:27-45` | not tested: `no_code_location` |
| [infinigen-F031](#infinigen-f031) | not_implemented | other | `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39` | not tested: `no_code_location` |

## infinigen-F001

**When self.policy.attn_sparsity >= 1.0: Path 2 (split GPU/CPU attention) asserts that sparsity >= 1.0, so sparse attention with mixed cache placement is rejected. (speedup/flexgen/infinigen/flex_opt.py:426)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:426` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.load_cache`
- condition: `self.policy.attn_sparsity >= 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: The assert only rejects FlexGen's top-k sparse attention baseline (attn_sparsity<1) in the mixed-cache CPU path, not InfiniGen's mechanism.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:426`): `assert self.policy.attn_sparsity >= 1.0`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F002

**When k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None: Prefetch path 2 requires MIXED device with populated GPU portion; otherwise path 1. (speedup/flexgen/infinigen/flex_opt.py:442)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:442` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.prefetch_cache`
- condition: `k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None`
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:442`): `if k_home.device.device_type == DeviceType.MIXED and k_home.data[0][0] is not None:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F003

**When path == 1 or path == 2: Prefetching is not implemented for CPU-compute paths 1 and 2; raises ValueError. (speedup/flexgen/infinigen/flex_opt.py:466)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:466` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.prefetch_cache`
- condition: `path == 1 or path == 2`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: prefetch_cache is called in the generation loop regardless of --cpu-cache-compute, and raises ValueError for CPU-compute paths 1/2, so InfiniGen prefetching cannot be combined with CPU attention compute.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:466`): `if path == 1 or path == 2:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F004

**When not (self.policy.act_gpu_percent == 100 or self.policy.act_cpu_percent == 100 or self.policy.act_disk_percent == 100): Any policy whose activation percentages are not a single 100% tier is rejected at construction time. (speedup/flexgen/infinigen/flex_opt.py:710)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:710` in `speedup/flexgen/infinigen/flex_opt.py::OptLM.__init__`
- condition: `not (self.policy.act_gpu_percent == 100 or self.policy.act_cpu_percent == 100 or self.policy.act_disk_percent == 100)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Requiring activations to live entirely on one tier is an inherited FlexGen offloading-policy restriction unrelated to InfiniGen's KV management.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:710`): `raise NotImplementedError()`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F005

**When args.compress_cache and args.attn_sparsity < 1.0: Combining cache compression with attention sparsity (the InfiniGen KV selection path) is not implemented; the run aborts. (speedup/flexgen/infinigen/flex_opt.py:1359)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:1359` in `speedup/flexgen/infinigen/flex_opt.py::run_flexgen`
- condition: `args.compress_cache and args.attn_sparsity < 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: This is FlexGen's own check against combining cache compression with its top-k sparse attention (attn_sparsity<1); it is not the InfiniGen KV selection path as claimed.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:1359`): `assert not (args.compress_cache and args.attn_sparsity < 1.0)`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F006

**When not (attn_sparsity >= 1.0): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:464)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:464` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `not (attn_sparsity >= 1.0)`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:464`): `assert attn_sparsity >= 1.0`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F007

**When not (src.device.device_type != DeviceType.MIXED): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:823)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:823` in `speedup/flexgen/infinigen/pytorch_backend.py::general_copy`
- condition: `not (src.device.device_type != DeviceType.MIXED)`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:823`): `assert src.device.device_type != DeviceType.MIXED`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F008

**When not (all((x.step is None for x in indices))): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:881)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:881` in `speedup/flexgen/infinigen/pytorch_backend.py::cut_indices`
- condition: `not (all((x.step is None for x in indices)))`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:881`): `assert all((x.step is None for x in indices))`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F009

**When self.layer_id > 1: partial_weight_ratio is only set for layers with layer_id > 1; layer 0 and 1 get None, so the partial-weight speculation path is disabled for the first two layers. (speedup/flexgen/infinigen/flex_opt.py:287)**

- category `stated_differently`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:287` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.__init__`
- condition: `self.layer_id > 1`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: Layers 0 and 1 always get partial_weight_ratio=None (and are excluded from prefetched cache loading), so InfiniGen speculation/selection never applies to the first two layers, which always use the full KV cache.
- paper/docs (paper, 4.3 Efficiently Prefetching KV Cache, p.10): “InfiniGen initiates speculation and prefetching from Layer 1 because the outliers, which are essential for exploiting input similarity, emerge during the computation in Layer 0.”
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:287`): `if self.layer_id > 1:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F010

**When self.policy.attn_sparsity >= 1.0: When sparsity >= 1.0 the full V cache is copied; otherwise V is deferred (v_home, False) for later selection, changing the data movement path. (speedup/flexgen/infinigen/flex_opt.py:389)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:389` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.load_cache`
- condition: `self.policy.attn_sparsity >= 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: attn_sparsity<1 picks FlexGen's top-k sparse attention baseline rather than InfiniGen's KV selection; same branch logic as infinigen-f04.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:389`): `if self.policy.attn_sparsity >= 1.0:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F011

**When self.enable_prefetching: When prefetching is enabled, mha_gen is called with p_w_q, partial_k_cache, speculation_stream, alpha and max_num_kv; otherwise those are passed as None, disabling the speculation/prefetch mechanism. (speedup/flexgen/infinigen/flex_opt.py:528)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:528` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.forward`
- condition: `self.enable_prefetching`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: enable_prefetching is fixed per layer in OptLM.__init__ (off only for the first and last layers), so it is an internal design detail rather than a user-reachable switch.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:528`): `if self.enable_prefetching:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F012

**When prev_partial_cache_read_buf is not None and self.layer_id > 1: Partial cache accumulation for the next layer only happens for layer_id > 1; earlier layers skip it. (speedup/flexgen/infinigen/flex_opt.py:541)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:541` in `speedup/flexgen/infinigen/flex_opt.py::SelfAttention.forward`
- condition: `prev_partial_cache_read_buf is not None and self.layer_id > 1`
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:541`): `if prev_partial_cache_read_buf is not None and self.layer_id > 1:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F013

**When j not in self.attn_layer[2:]: Cache loading is skipped for all attention layers except the first two (attn_layer[0], attn_layer[1]); those layers' KV caches are not loaded from cache_home, so the InfiniGen cache-load path only runs for the first two attention layers. (speedup/flexgen/infinigen/flex_opt.py:799)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:799` in `speedup/flexgen/infinigen/flex_opt.py::OptLM.load_cache`
- condition: `j not in self.attn_layer[2:]`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Skipping load_cache for attention layers after the first two is a fixed internal schedule (those layers get KV via prefetch), not a condition a user can trigger.
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:799`): `if j not in self.attn_layer[2:]:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F014

**When p_w_q is None: In TorchDevice.mha_gen, the InfiniGen KV speculation (speculate_attention) only runs when the caller passes a partial-weight query tensor p_w_q. When p_w_q is None, prefetch_idx stays None (line 400) and the whole dynamic KV selection / prefetch mechanism is skipped, so the run degrades to plain dense attention over the full KV cache. (speedup/flexgen/infinigen/pytorch_backe...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:401` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `p_w_q is None`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: p_w_q is None only for layers built with enable_prefetching=False, so this is the same 'early layers get no speculation/full KV' limitation already covered by infinigen-10.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:401`): `if p_w_q is not None:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F015

**When attn_sparsity >= 1.0: Caller-supplied attn_sparsity selects dense attention (decompress full k/v cache and dense bmm) versus sparse attention (top-k selection in _sparse_attention_value). (speedup/flexgen/infinigen/pytorch_backend.py:422)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:422` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `attn_sparsity >= 1.0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: The dense vs attn_sparsity<1 switch selects FlexGen's own top-k sparse attention baseline, not a variant of InfiniGen.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:422`): `if attn_sparsity >= 1.0:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F016

**When comp_config.group_dim == 0: Caller-supplied comp_config.group_dim decides whether k_new/v_new are re-sliced to a group-aligned boundary before compression. (speedup/flexgen/infinigen/pytorch_backend.py:479)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:479` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha_gen`
- condition: `comp_config.group_dim == 0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: group_dim rounding is an internal detail of FlexGen cache compression whose config is hardcoded in run_flexgen (group_dim=2), not a user-facing variant of InfiniGen.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:479`): `if comp_config.group_dim == 0:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F017

**When policy.cache_disk_percent == 0: When the configured disk cache percent is zero, the KV cache is split only between GPU and CPU (len_disk=0, len_cpu=shape-len_gpu), so no disk segment is allocated; otherwise the split uses cache_gpu_percent/cache_cpu_percent and the remainder goes to disk. The caller's policy config selects which cache layout the mechanism uses. (speedup/flexgen/infinigen/p...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:767` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchMixedDevice.init_cache_one_gpu_batch`
- condition: `policy.cache_disk_percent == 0`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: GPU/CPU/disk KV-cache segment sizing is FlexGen offloading plumbing, not a change to the mechanism.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:767`): `if policy.cache_disk_percent == 0:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F018

**论文要求覆盖受害者槽位；代码保留全部 K/V 只做注意力屏蔽（artifact 范围：无覆盖写步骤）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `accuracy/perplexity/table2.sh:27-45`
- condition: `past_key_value is not None`
- paper/docs (paper, PDF p.10): “the manager overwrites the selected victim with the newly generated key and value”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F019

**论文要求淘汰后更新 GPU 部分 key cache；代码无该步骤（artifact 范围：缺更新步骤）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `accuracy/perplexity/table2.sh:27-45`
- condition: `past_key_value is not None`
- paper/docs (paper, PDF p.10, text lines 31-34): “KV entry for eviction. Subsequently, the manager overwrites the selected victim with the newly generated key and value, along with updating the corresponding partial key cache re- siding in the GPU. It is noted that the order of KV entries can”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F020

**控制平面组件集合不完整（缺Pool Manager）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:282`
- paper/docs (paper, PDF p.7, text lines 112-115): “weights. We explain each operation in Section 4.3. The sec- ond component is the Pool Manager. It manages the KV cache pool on CPU memory under CPU memory pressure, which we discuss in Section 4.4.”
- paper/docs (paper, PDF p.7): “GPU Memory CPU Memory”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F021

**论文要求A=V；代码A为V列按σq·σk排序重排，A≠V（artifact 范围：A为排序重排后的V，非论文所述A=V）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:513-524`
- condition: `warmup`
- paper/docs (paper, PDF p.9): “We then set A to orthogonal matrix V”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F022

**预取集合由 top-k(均值) 决定，而非严格 >max−alpha 的令牌集合**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/kv_selection_controller.py:28-63`
- condition: `self.policy.attn_sparsity >= 1.0`
- paper/docs (paper, PDF p.9): “We select only the tokens with an attention score greater than the maximum score subtracted by alpha”
- paper/docs (paper, PDF p.10): “InfiniGen only prefetches the keys and values of the tokens with an attention score larger than the highest attention score minus alpha”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F023

**实验路径以绝对令牌数封顶，未实现 20% 比例上限**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/kv_selection_controller.py:28-63`
- condition: `mean > max_num_kv`
- paper/docs (paper, PDF p.10): “For each layer, we allow sending up to 20% of the total KV cache to the GPU if it contains more candidates.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F024

**实验路径缺少K的逐元素绝对值**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- condition: `partial_weight_ratio is not None and not warmup`
- paper/docs (paper, PDF p.9): “we first take the element-wise absolute values of the skewed query and key matrices”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F025

**求和对象缺少K_abs项**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- paper/docs (paper, PDF p.9): “We then sum the elements in each column”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F026

**单次topk未容纳K离群列**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- paper/docs (paper, PDF p.9): “perform top-k operation only once while accommodating the outlier columns of both query and key matrices”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F027

**When (i == 0) or (i == (self.config.num_hidden_layers - 1)): When sep_layer is set, the first and last layers are constructed as SelfAttention with the flag False (no InfiniGen KV selection), while all middle layers get True. So the InfiniGen mechanism is only applied to interior layers; boundary layers run the plain attention path. (speedup/flexgen/infinigen/flex_opt.py:690)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/flexgen/infinigen/flex_opt.py:690` in `speedup/flexgen/infinigen/flex_opt.py::OptLM.__init__`
- condition: `(i == 0) or (i == (self.config.num_hidden_layers - 1))`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: The last layer still has its KV selected by the previous layer's speculation and layer 1 also runs on full KV, so 'boundary layers run plain attention, interior layers get InfiniGen' misstates the effect (the real limitation is item 10).
- code snippet (`speedup/flexgen/infinigen/flex_opt.py:690`): `if i == 0 or i == self.config.num_hidden_layers - 1:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F028

**When warmup or partial_weight_ratio is None: In TorchDevice.mha, the partial-weight index (which heads/rows of the query projection are used for the InfiniGen speculation) is only computed when warmup is False and partial_weight_ratio is not None. Otherwise partial_weight_index stays None (line 325) and is returned as None (line 379), so mha_gen receives p_w_q=None and the KV speculation is sil...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:326` in `speedup/flexgen/infinigen/pytorch_backend.py::TorchDevice.mha`
- condition: `warmup or partial_weight_ratio is None`
- step 4 review: `wrong`: blind review by an LLM subagent (round 1), not human: partial_weight_index being None does not make mha_gen get p_w_q=None; p_w_q comes from partial_weight_read_buf (filled by the next layer) whenever enable_prefetching is set, so speculation is not skipped as claimed.
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:326`): `if not warmup and partial_weight_ratio is not None:`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F029

**When not (dst.device.device_type != DeviceType.MIXED): AssertionError (speedup/flexgen/infinigen/pytorch_backend.py:837)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/flexgen/infinigen/pytorch_backend.py:837` in `speedup/flexgen/infinigen/pytorch_backend.py::general_copy`
- condition: `not (dst.device.device_type != DeviceType.MIXED)`
- code snippet (`speedup/flexgen/infinigen/pytorch_backend.py:837`): `assert dst.device.device_type != DeviceType.MIXED`

**Not tested** (`env_unavailable`): repository third_party/InfiniGen is not checked out

## infinigen-F030

**论文要求饱和时全体减半；代码无该步骤（artifact 范围：无饱和减半）**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `accuracy/perplexity/table2.sh:27-45`
- condition: `self.eviction_policy == "counter"`
- paper/docs (paper, PDF p.10): “If any counter becomes saturated, all the counter values are reduced by half.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## infinigen-F031

**实验路径缺少论文指定的相加步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `speedup/infinigen/infinigen/partial_weight_generation_controller.py:5-39`
- paper/docs (paper, PDF p.9): “then add these two matrices together”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

