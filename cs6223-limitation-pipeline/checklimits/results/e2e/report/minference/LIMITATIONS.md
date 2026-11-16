# Limitations report: MInference 1.0: Accelerating Pre-filling for Long-Context LLMs via Dynamic Sparse Attention

- artifact: `minference` (NeurIPS 2024), repository https://github.com/microsoft/MInference at `427b1ddbd2`
- input: `results/step4/minference/limitations_for_tests.json` (sha256 `6f02cbec16ce`), 73 Findings
- generated: 2026-11-16T16:10:00+08:00 by `checklimits test` (contract `checklimits-test-report/1`)
- environment: **not_ok** (repository third_party/MInference is not checked out)

## How to read this

* Every Finding of the input appears once below, tested or not. A Finding that was not tested says why.
* **Verdict** is decided by a deterministic harness from observations of the real code, not by a language model. A code agent designed the test; the harness re-ran it and checked what the agent declared.
* **Level** (L0 to L3, `invalid`, `n/a`) says how many of the known reasons a verdict could be wrong (the defeaters D1 to D14 in `CONFIDENCE_SPEC.md`) were measured and ruled out. **All levels are uncalibrated**: they are not accuracy, and no ground truth exists for these Findings.
* The *open doubts* listed under each tested Finding are the defeaters that were not ruled out.
* Step 4 labels (`review`) come from a blind LLM review, not a human.

## Summary

| | |
|---|---|
| Findings | 73 |
| tested | 0 |
| not tested | 73 |
| not tested, by reason | `env_unavailable` 50, `no_code_location` 23 |

| Finding | category | effect | location | result |
|---|---|---|---|---|
| [minference-F001](#minference-f001) | undisclosed | reject | `minference/minference_configuration.py:56` | not tested: `env_unavailable` |
| [minference-F003](#minference-f003) | undisclosed | state | `minference/modules/minference_forward.py:165-172` | not tested: `env_unavailable` |
| [minference-F004](#minference-f004) | undisclosed | state | `minference/modules/minference_forward.py:390` | not tested: `env_unavailable` |
| [minference-F006](#minference-f006) | undisclosed | reject | `minference/modules/minference_forward.py:484-488` | not tested: `env_unavailable` |
| [minference-F008](#minference-f008) | undisclosed | state | `minference/modules/minference_forward.py:681` | not tested: `env_unavailable` |
| [minference-F010](#minference-f010) | undisclosed | reject | `minference/ops/block_sparse_flash_attention.py:126` | not tested: `env_unavailable` |
| [minference-F011](#minference-f011) | undisclosed | reject | `minference/ops/block_sparse_flash_attention.py:127` | not tested: `env_unavailable` |
| [minference-F012](#minference-f012) | undisclosed | reject | `minference/ops/pit_sparse_flash_attention_v2.py:149` | not tested: `env_unavailable` |
| [minference-F013](#minference-f013) | undisclosed | reject | `minference/ops/pit_sparse_flash_attention_v2.py:150` | not tested: `env_unavailable` |
| [minference-F014](#minference-f014) | undisclosed | reject | `minference/ops/streaming_kernel.py:414` | not tested: `env_unavailable` |
| [minference-F015](#minference-f015) | undisclosed | reject | `minference/ops/streaming_kernel.py:605` | not tested: `env_unavailable` |
| [minference-F016](#minference-f016) | undisclosed | reject | `minference/ops/streaming_kernel.py:606` | not tested: `env_unavailable` |
| [minference-F017](#minference-f017) | undisclosed | reject | `minference/patch.py:207` | not tested: `env_unavailable` |
| [minference-F019](#minference-f019) | undisclosed | reject | `minference/patch.py:1253` | not tested: `env_unavailable` |
| [minference-F020](#minference-f020) | undisclosed | path_change | `minference/minference_configuration.py:52` | not tested: `env_unavailable` |
| [minference-F021](#minference-f021) | undisclosed | path_change | `minference/modules/minference_forward.py:63` | not tested: `env_unavailable` |
| [minference-F022](#minference-f022) | undisclosed | path_change | `minference/modules/minference_forward.py:192` | not tested: `env_unavailable` |
| [minference-F023](#minference-f023) | undisclosed | path_change | `minference/modules/minference_forward.py:418-419` | not tested: `env_unavailable` |
| [minference-F024](#minference-f024) | undisclosed | path_change | `minference/modules/minference_forward.py:421` | not tested: `env_unavailable` |
| [minference-F025](#minference-f025) | undisclosed | path_change | `minference/modules/minference_forward.py:423` | not tested: `env_unavailable` |
| [minference-F026](#minference-f026) | undisclosed | path_change | `minference/modules/minference_forward.py:425-426` | not tested: `env_unavailable` |
| [minference-F027](#minference-f027) | undisclosed | path_change | `minference/modules/minference_forward.py:427` | not tested: `env_unavailable` |
| [minference-F028](#minference-f028) | undisclosed | path_change | `minference/modules/minference_forward.py:432` | not tested: `env_unavailable` |
| [minference-F029](#minference-f029) | undisclosed | path_change | `minference/modules/minference_forward.py:434` | not tested: `env_unavailable` |
| [minference-F030](#minference-f030) | undisclosed | path_change | `minference/modules/minference_forward.py:521` | not tested: `env_unavailable` |
| [minference-F031](#minference-f031) | undisclosed | path_change | `minference/modules/minference_forward.py:613` | not tested: `env_unavailable` |
| [minference-F032](#minference-f032) | undisclosed | path_change | `minference/modules/minference_forward.py:756` | not tested: `env_unavailable` |
| [minference-F033](#minference-f033) | undisclosed | path_change | `minference/modules/minference_forward.py:864` | not tested: `env_unavailable` |
| [minference-F034](#minference-f034) | undisclosed | path_change | `minference/modules/snap_kv.py:321` | not tested: `env_unavailable` |
| [minference-F035](#minference-f035) | undisclosed | path_change | `minference/modules/snap_kv.py:347` | not tested: `env_unavailable` |
| [minference-F037](#minference-f037) | undisclosed | path_change | `minference/ops/streaming_kernel.py:609` | not tested: `env_unavailable` |
| [minference-F038](#minference-f038) | undisclosed | path_change | `minference/ops/streaming_kernel.py:620` | not tested: `env_unavailable` |
| [minference-F039](#minference-f039) | undisclosed | path_change | `minference/ops/streaming_kernel.py:701` | not tested: `env_unavailable` |
| [minference-F040](#minference-f040) | undisclosed | path_change | `minference/patch.py:835` | not tested: `env_unavailable` |
| [minference-F041](#minference-f041) | undisclosed | path_change | `minference/patch.py:840` | not tested: `env_unavailable` |
| [minference-F042](#minference-f042) | impl_deviates | other | `csrc/vertical_slash_index.cu:27-99` | not tested: `no_code_location` |
| [minference-F043](#minference-f043) | impl_deviates | other | `experiments/README.md:13-30` | not tested: `no_code_location` |
| [minference-F044](#minference-f044) | impl_deviates | other | `experiments/README.md:13-30` | not tested: `no_code_location` |
| [minference-F045](#minference-f045) | impl_deviates | other | `experiments/README.md:13-30` | not tested: `no_code_location` |
| [minference-F046](#minference-f046) | impl_deviates | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location` |
| [minference-F047](#minference-f047) | impl_deviates | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location` |
| [minference-F048](#minference-f048) | impl_deviates | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location` |
| [minference-F049](#minference-f049) | impl_deviates | other | `minference/models_patch.py:66-73` | not tested: `no_code_location` |
| [minference-F050](#minference-f050) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F051](#minference-f051) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F052](#minference-f052) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F053](#minference-f053) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F054](#minference-f054) | impl_deviates | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F055](#minference-f055) | impl_deviates | other | `minference/modules/minference_forward.py:199-246` | not tested: `no_code_location` |
| [minference-F056](#minference-f056) | impl_deviates | other | `minference/ops/block_sparse_flash_attention.py:150-165` | not tested: `no_code_location` |
| [minference-F002](#minference-f002) | undisclosed | other | `minference/modules/minference_forward.py:30` | not tested: `env_unavailable` |
| [minference-F057](#minference-f057) | undisclosed | other | `minference/modules/minference_forward.py:34` | not tested: `env_unavailable` |
| [minference-F058](#minference-f058) | undisclosed | state | `minference/modules/minference_forward.py:74` | not tested: `env_unavailable` |
| [minference-F059](#minference-f059) | undisclosed | other | `minference/modules/minference_forward.py:194` | not tested: `env_unavailable` |
| [minference-F060](#minference-f060) | undisclosed | other | `minference/modules/minference_forward.py:430` | not tested: `env_unavailable` |
| [minference-F005](#minference-f005) | undisclosed | other | `minference/modules/minference_forward.py:441` | not tested: `env_unavailable` |
| [minference-F007](#minference-f007) | undisclosed | other | `minference/modules/minference_forward.py:504` | not tested: `env_unavailable` |
| [minference-F061](#minference-f061) | undisclosed | other | `minference/modules/minference_forward.py:523` | not tested: `env_unavailable` |
| [minference-F062](#minference-f062) | undisclosed | other | `minference/modules/minference_forward.py:526` | not tested: `env_unavailable` |
| [minference-F009](#minference-f009) | undisclosed | other | `minference/modules/minference_forward.py:754` | not tested: `env_unavailable` |
| [minference-F036](#minference-f036) | undisclosed | other | `minference/ops/block_sparse_flash_attention.py:130` | not tested: `env_unavailable` |
| [minference-F063](#minference-f063) | undisclosed | other | `minference/ops/block_sparse_flash_attention.py:164` | not tested: `env_unavailable` |
| [minference-F064](#minference-f064) | undisclosed | other | `minference/ops/pit_sparse_flash_attention.py:150` | not tested: `env_unavailable` |
| [minference-F065](#minference-f065) | undisclosed | path_change | `minference/ops/pit_sparse_flash_attention_v2.py:188` | not tested: `env_unavailable` |
| [minference-F018](#minference-f018) | undisclosed | other | `minference/patch.py:1252` | not tested: `env_unavailable` |
| [minference-F066](#minference-f066) | not_implemented | other | `experiments/README.md:13-30` | not tested: `no_code_location` |
| [minference-F067](#minference-f067) | not_implemented | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location` |
| [minference-F068](#minference-f068) | not_implemented | other | `experiments/infinite_bench/args.py:63-78` | not tested: `no_code_location` |
| [minference-F069](#minference-f069) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F070](#minference-f070) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F071](#minference-f071) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F072](#minference-f072) | not_implemented | other | `minference/modules/minference_forward.py:99-197` | not tested: `no_code_location` |
| [minference-F073](#minference-f073) | not_implemented | other | `minference/modules/minference_forward.py:199-246` | not tested: `no_code_location` |

## minference-F001

**When config_path is None and model_name not in MODEL2PATH: If no `config_path` is given, the model name must be a key of the hard-coded `MODEL2PATH` table; any other model (including a local path or a fine-tune) aborts with an AssertionError, so the mechanism is only usable for the enumerated model list unless the caller supplies a pattern file. (minference/minference_configuration.py:56)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/minference_configuration.py:56` in `minference/minference_configuration.py::MInferenceConfig.update_config_path`
- condition: `config_path is None and model_name not in MODEL2PATH`
- code snippet (`minference/minference_configuration.py:56`): `assert model_name in MODEL2PATH`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F003

**When SEARCH_MASK is None # first call only: module-level cache initialised on first call and reused (minference/modules/minference_forward.py:165)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:165-172` in `minference/modules/minference_forward.py::search_pattern`
- condition: `SEARCH_MASK is None # first call only`
- code snippet (`minference/modules/minference_forward.py:165`): `if SEARCH_MASK is None:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F004

**When "vs" in self.__dict__: Static pattern reuses vertical_topk/slash cached in self.vs from an earlier call instead of recomputing them. (minference/modules/minference_forward.py:390)**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:390` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4.vertical_and_slash_kernel_static`
- condition: `"vs" in self.__dict__`
- code snippet (`minference/modules/minference_forward.py:390`): `if 'vs' in self.__dict__:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F006

**When True: raise ValueError(f'The cache structure has changed since version v4.36. If you are using {self.__class__.__name__} for a (minference/modules/minference_forward.py:484)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:484-488` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `self.layer_idx is None`
- code snippet (`minference/modules/minference_forward.py:484`): `raise ValueError(f'The cache structure has changed since version v4.36. If you are using {self.__class__.__name__} for auto-regressive decoding with k/v caching, please make sure to initialize the att`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F008

**When key_states.shape[-2] != kv_seq_len: Whether SnapKV compression runs depends on `self.kv_seq_len` cached from earlier calls: on the first (prefill) call the KV is compressed and `self.kv_seq_len` registered; on later calls the else-branch just appends to the cache. So the same input produces different KV contents depending on call history, and the sparse pattern is then computed over the co...**

- category `undisclosed`, effect `state`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/modules/minference_forward.py:681` in `minference/modules/minference_forward.py::minference_with_snapkv_forward.forward`
- condition: `key_states.shape[-2] != kv_seq_len`
- code snippet (`minference/modules/minference_forward.py:681`): `if key_states.shape[-2] == kv_seq_len:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F010

**When not (Lq == Lk and Lk == Lv): AssertionError (minference/ops/block_sparse_flash_attention.py:126)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:126` in `minference/ops/block_sparse_flash_attention.py::_triton_block_sparse_attention`
- condition: `not (Lq == Lk and Lk == Lv)`
- code snippet (`minference/ops/block_sparse_flash_attention.py:126`): `assert Lq == Lk and Lk == Lv`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F011

**When not (Lk in {16, 32, 64, 128}): AssertionError (minference/ops/block_sparse_flash_attention.py:127)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:127` in `minference/ops/block_sparse_flash_attention.py::_triton_block_sparse_attention`
- condition: `not (Lk in {16, 32, 64, 128})`
- code snippet (`minference/ops/block_sparse_flash_attention.py:127`): `assert Lk in {16, 32, 64, 128}`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F012

**When not (Lq == Lk and Lk == Lv): AssertionError (minference/ops/pit_sparse_flash_attention_v2.py:149)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention_v2.py:149` in `minference/ops/pit_sparse_flash_attention_v2.py::_triton_mixed_sparse_attention`
- condition: `not (Lq == Lk and Lk == Lv)`
- code snippet (`minference/ops/pit_sparse_flash_attention_v2.py:149`): `assert Lq == Lk and Lk == Lv`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F013

**When not (Lk in {16, 32, 64, 128}): AssertionError (minference/ops/pit_sparse_flash_attention_v2.py:150)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention_v2.py:150` in `minference/ops/pit_sparse_flash_attention_v2.py::_triton_mixed_sparse_attention`
- condition: `not (Lk in {16, 32, 64, 128})`
- code snippet (`minference/ops/pit_sparse_flash_attention_v2.py:150`): `assert Lk in {16, 32, 64, 128}`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F014

**When Lk not in {16, 32, 64, 128}: Head dimension (q/k/v last dim) must be one of 16/32/64/128; other model head sizes abort the streaming attention forward. (minference/ops/streaming_kernel.py:414)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/streaming_kernel.py:414` in `minference/ops/streaming_kernel.py::_forward`
- condition: `Lk not in {16, 32, 64, 128}`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: _forward asserts head_dim in {16,32,64,128}, and streaming_forward does not pad head_dim 256/512, so models with such head sizes are rejected on the A-shape/streaming path.
- code snippet (`minference/ops/streaming_kernel.py:414`): `assert Lk in {16, 32, 64, 128}`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F015

**When not (q.dim() == 4): AssertionError (minference/ops/streaming_kernel.py:605)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/streaming_kernel.py:605` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `not (q.dim() == 4)`
- code snippet (`minference/ops/streaming_kernel.py:605`): `assert q.dim() == 4`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F016

**When not (q.shape == k.shape == v.shape): AssertionError (minference/ops/streaming_kernel.py:606)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/ops/streaming_kernel.py:606` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `not (q.shape == k.shape == v.shape)`
- code snippet (`minference/ops/streaming_kernel.py:606`): `assert q.shape == k.shape == v.shape`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F017

**When output_attentions: If the caller requests attention outputs, execution is aborted by the assertion. (minference/patch.py:207)**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/patch.py:207` in `minference/patch.py::huggingface_forward.hf_forward`
- condition: `output_attentions`
- code snippet (`minference/patch.py:207`): `assert not output_attentions`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F019

**When not (isinstance(model, LlamaForCausalLM) or isinstance(model, MistralForCausalLM) or isinstance(model, Qwen2ForCausalLM) or model.__class__.__name__ == "MiniCPMForCausalLM" or model.__class__.__name__ == "Phi3ForCausalLM" or model.__class__.__name__ == "ChatGLMForConditionalGeneration"): If the caller passes a model that is not one of the recognized classes, patch_hf raises ValueError and ...**

- category `undisclosed`, effect `reject`, step 4 level L2, priority 1, scope `unknown`
- code: `minference/patch.py:1253` in `minference/patch.py::patch_hf`
- condition: `not (isinstance(model, LlamaForCausalLM) or isinstance(model, MistralForCausalLM) or isinstance(model, Qwen2ForCausalLM) or model.__class__.__name__ == "MiniCPMForCausalLM" or model.__class__.__name_…`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: patch_hf is reached only for the inf_llm baseline (streaming2 is rejected by the config), while the MInference path goes through minference_patch, so this class whitelist limits baseline code, not the mechanism.
- code snippet (`minference/patch.py:1253`): `raise ValueError('Only supports llama, mistral and qwen2 models.')`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F020

**When self.attn_type in self.STASTIC_ATTENTION_TYPES: For any `attn_type` in `STASTIC_ATTENTION_TYPES` (`minference_with_dense`, `static`, `dilated1`, `dilated2`, `streaming`, `inf_llm`, `hf`) the user-supplied `config_path` is silently discarded (`return ""`), so the searched per-head pattern is never used and a fixed/static pattern or a different attention implementation runs instead. (minfere...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/minference_configuration.py:52` in `minference/minference_configuration.py::MInferenceConfig.update_config_path`
- condition: `self.attn_type in self.STASTIC_ATTENTION_TYPES`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: For non-minference attn_types (e.g. 'static'), the user's config_path is silently dropped, so the static variant always uses the hard-coded default pattern sizes.
- code snippet (`minference/minference_configuration.py:52`): `if self.attn_type in self.STASTIC_ATTENTION_TYPES:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F021

**When not (self.config_path is not None and os.path.exists(self.config_path) and self.layer_idx < len(json.load(open(self.config_path)))): The searched per-head pattern is only loaded when `config_path` exists and has an entry for `self.layer_idx`; otherwise `self.best_pattern = {}` and every head uses the hard-coded default pattern (see line 430). A missing/typo'd `config_path` therefore silent...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:63` in `minference/modules/minference_forward.py::init_minference_parameters`
- condition: `not (self.config_path is not None and os.path.exists(self.config_path) and self.layer_idx < len(json.load(open(self.config_path))))`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: With a missing config_path, or one that has too few layers, best_pattern is empty and every head silently uses the default vertical_and_slash (1000, 6096) pattern instead of the searched per-head pattern.
- code snippet (`minference/modules/minference_forward.py:63`): `if self.config_path is not None and os.path.exists(self.config_path) and (self.layer_idx < len(json.load(open(self.config_path)))):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F022

**When best_ty == "stream_llm": If streaming wins the search, it is overridden to vertical_and_slash, so the streaming variant is never actually selected. (minference/modules/minference_forward.py:192)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:192` in `minference/modules/minference_forward.py::search_pattern`
- condition: `best_ty == "stream_llm"`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: The offline pattern search can never assign the A-shape (stream_llm) pattern; it is always remapped to vertical_and_slash, so one of the paper's three patterns is effectively unused.
- code snippet (`minference/modules/minference_forward.py:192`): `if best_ty == 'stream_llm':`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F023

**When q_len == 1: returns via dense (minference/modules/minference_forward.py:418)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:418-419` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `q_len == 1`
- code snippet (`minference/modules/minference_forward.py:418`): `if q_len == 1:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F024

**When self.config.to_dict().get("dilated1", False): Config flag switches to the fixed 'dilated1' sparse pattern (8k local with stride 2) instead of the dynamic vertical/slash topk selection. (minference/modules/minference_forward.py:421)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:421` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("dilated1", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: dilated1 is a baseline attention type selected by attn_type, not a variant of the paper's mechanism.
- code snippet (`minference/modules/minference_forward.py:421`): `if self.config.to_dict().get('dilated1', False):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F025

**When self.config.to_dict().get("dilated2", False): Config flag switches to the fixed 'dilated2' sparse pattern (2k dense local + 4k strided local) instead of dynamic selection. (minference/modules/minference_forward.py:423)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:423` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("dilated2", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: dilated2 is a baseline attention type selected by attn_type, not a variant of the paper's mechanism.
- code snippet (`minference/modules/minference_forward.py:423`): `if self.config.to_dict().get('dilated2', False):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F026

**When self.config.to_dict().get('dense', False): returns via dense (minference/modules/minference_forward.py:425)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:425-426` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get('dense', False)`
- code snippet (`minference/modules/minference_forward.py:425`): `if self.config.to_dict().get('dense', False):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F027

**When self.config.to_dict().get("streaming", False): Config flag switches to streaming_forward with n_init/n_local from streaming_kwargs instead of the vertical/slash mechanism. (minference/modules/minference_forward.py:427)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:427` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("streaming", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: The streaming flag is set only by attn_type='streaming', so this is the same config-driven variant switch already covered by minference-24.
- code snippet (`minference/modules/minference_forward.py:427`): `if self.config.to_dict().get('streaming', False):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F028

**When self.config.to_dict().get("static_pattern", False): Config flag switches to vertical_and_slash_kernel_static, which caches and reuses the first computed vertical/slash indices. (minference/modules/minference_forward.py:432)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:432` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("static_pattern", False)`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: The static_pattern config (attn_type='static') switches to a kernel that computes the vertical/slash indices once and reuses them, instead of estimating them online.
- code snippet (`minference/modules/minference_forward.py:432`): `if self.config.to_dict().get('static_pattern', False):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F029

**When self.config.to_dict().get("vs_only", False): Config flag forces the vertical_and_slash_kernel regardless of the per-head pattern type ty. (minference/modules/minference_forward.py:434)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:434` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `self.config.to_dict().get("vs_only", False)`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: vs_only is real but is not exposed through MInferenceConfig/attn_type and is never set by the package, so it is a hidden debug flag.
- code snippet (`minference/modules/minference_forward.py:434`): `if self.config.to_dict().get('vs_only', False):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F030

**When self.layer_idx >= self.starting_layer and not self.is_search: Layers below starting_layer (or in search mode) skip the sparse mechanism and use dense flash attention / gather_qkv. (minference/modules/minference_forward.py:521)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:521` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `self.layer_idx >= self.starting_layer and not self.is_search`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: Layers below the configurable starting_layer silently run dense flash attention (or gather_qkv) instead of sparse attention.
- code snippet (`minference/modules/minference_forward.py:521`): `if self.layer_idx >= self.starting_layer and (not self.is_search):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F031

**When self.layer_idx >= self.starting_layer: Layers below starting_layer use dense flash_attn_func; only layers at/after starting_layer use the sparse gather_last_q_vertical_slash_topk_v4 path. starting_layer is a constructor/config attribute deciding which algorithm runs per layer. (minference/modules/minference_forward.py:613)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:613` in `minference/modules/minference_forward.py::minference_kv_cache_cpu_forward.forward`
- condition: `self.layer_idx >= self.starting_layer`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: The starting_layer config makes layers below it use dense flash attention instead of the sparse vertical-slash path.
- code snippet (`minference/modules/minference_forward.py:613`): `if self.layer_idx >= self.starting_layer:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F032

**When q_len == 1: In gather_last_q_vertical_slash_topk_vllm, a single query token bypasses the sparse pattern selection and runs dense flash attention. (minference/modules/minference_forward.py:756)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:756` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_vllm`
- condition: `q_len == 1`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: In the vLLM path, decode steps (q_len==1) always use dense flash attention, so sparsity applies only to prefill.
- code snippet (`minference/modules/minference_forward.py:756`): `if q_len == 1:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F033

**When kv_cache is None or prefill_meta.block_tables.numel() == 0: Only when there is no KV cache or empty block tables does the code run the MInference sparse prefill (minference_prefill_func); otherwise it falls to PagedAttention.forward_prefix, a different (dense/prefix) implementation. (minference/modules/minference_forward.py:864)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:864` in `minference/modules/minference_forward.py::minference_vllm_forward.forward`
- condition: `kv_cache is None or prefill_meta.block_tables.numel() == 0`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 2), not human: In the vLLM integration, prefill with prefix cache or chunked prefill (non-empty block tables) silently uses dense PagedAttention.forward_prefix instead of sparse attention.
- code snippet (`minference/modules/minference_forward.py:864`): `if kv_cache is None or prefill_meta.block_tables.numel() == 0:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F034

**When q_len < self.max_capacity_prompt: When the prompt length is below max_capacity_prompt, update_kv returns the full key/value states unchanged, silently skipping the SnapKV compression (dense baseline) instead of applying the sparse selection. (minference/modules/snap_kv.py:321)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/snap_kv.py:321` in `minference/modules/snap_kv.py::SnapKVCluster.update_kv`
- condition: `q_len < self.max_capacity_prompt`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: Skipping compression for short prompts is normal SnapKV behaviour in an optional add-on, not a limit of MInference's sparse prefill.
- code snippet (`minference/modules/snap_kv.py:321`): `if q_len < self.max_capacity_prompt:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F035

**When self.pooling == "avgpool": The pooling attribute (set from config.pooling in init_snapkv) selects avg_pool1d vs max_pool1d for the attention-score smoothing that drives token selection, changing which KV entries are kept. (minference/modules/snap_kv.py:347)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/snap_kv.py:347` in `minference/modules/snap_kv.py::SnapKVCluster.update_kv`
- condition: `self.pooling == "avgpool"`
- code snippet (`minference/modules/snap_kv.py:347`): `if self.pooling == 'avgpool':`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F037

**When head_dim not in [16, 32, 64, 128, 256, 512]: For head dimensions not in the hard-coded list, q/k/v are zero-padded to the next power of two before the streaming kernel runs, changing the computation path (and the padded dims are sliced off at line 633). (minference/ops/streaming_kernel.py:609)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/streaming_kernel.py:609` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `head_dim not in [16, 32, 64, 128, 256, 512]`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Zero-padding head_dim to a power of two gives the same result and is an internal kernel-compatibility detail.
- code snippet (`minference/ops/streaming_kernel.py:609`): `if head_dim not in [16, 32, 64, 128, 256, 512]:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F038

**When k_len > n_local: The streaming (StreamingLLM) variant only keeps the `n_init` sink tokens when the KV length exceeds `n_local`; for shorter sequences it degenerates to plain sliding-window attention with no attention sinks, so the same head runs a different algorithm depending on the input length. `n_init`/`n_local` come from `config.streaming_kwargs`. (minference/ops/streaming_kernel.py:620)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/streaming_kernel.py:620` in `minference/ops/streaming_kernel.py::streaming_forward`
- condition: `k_len > n_local`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: When k_len <= n_local the sliding window already covers every key, so skipping the sink pass gives the same result; this is an implementation detail.
- code snippet (`minference/ops/streaming_kernel.py:620`): `if k_len > n_local:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F039

**When len_k <= n_local + n_init: The KV cache kept for subsequent decoding is either the full h_k/h_v or a concatenation of the first n_init keys and the last n_local keys, depending on caller-supplied n_local/n_init and the accumulated length. This changes what state later calls see. (minference/ops/streaming_kernel.py:701)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/streaming_kernel.py:701` in `minference/ops/streaming_kernel.py::stream_llm_forward.forward`
- condition: `len_k <= n_local + n_init`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Truncating the KV cache to sink plus local tokens belongs to the StreamingLLM baseline forward (stream_llm_forward), not to MInference.
- code snippet (`minference/ops/streaming_kernel.py:701`): `if len_k <= n_local + n_init:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F040

**When config.kv_cache_cpu: Caller-supplied config flag switches to the KV-cache-on-CPU variant (minference_patch_kv_cache_cpu) instead of the standard minference_forward path. (minference/patch.py:835)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/patch.py:835` in `minference/patch.py::minference_patch`
- condition: `config.kv_cache_cpu`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 2), not human: kv_cache_cpu only changes where the KV cache is placed (memory/device plumbing), not the sparse mechanism.
- code snippet (`minference/patch.py:835`): `if config.kv_cache_cpu:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F041

**When config.use_snapkv: Caller-supplied config flag switches to the SnapKV variant (minference_patch_with_snapkv) instead of the standard minference_forward path. (minference/patch.py:840)**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/patch.py:840` in `minference/patch.py::minference_patch`
- condition: `config.use_snapkv`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: The user config flag use_snapkv switches patching to a different forward (minference_with_snapkv_forward) that combines sparse prefill with SnapKV compression, which is a config-driven variant.
- code snippet (`minference/patch.py:840`): `if config.use_snapkv:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F042

**论文要求循环守卫 s_v≤k_s；代码用 while(1)+break，s 仅在 else 分支递增，终止由 s>=NNZ_S 决定**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `csrc/vertical_slash_index.cu:27-99`
- condition: `s_idx < end_m`
- paper/docs (paper, PDF p.25, text lines 23-25): “# Merge points (vertical indexes) and ranges (slash indexes) whilesv≤ks do”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F043

**实验配置未体现{(1024,4096)}，实际候选为(100,800)**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/README.md:13-30`
- paper/docs (paper, PDF p.18): “We set the target FLOPs t to be the same as 1k global tokens and 4k local window tokens in the A-shape pattern.”
- paper/docs (paper, PDF p.18): “A-shape {(1024, 4096)}”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F044

**实验配置未体现论文候选集**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/README.md:13-30`
- paper/docs (paper, PDF p.18): “Vertical-Slash {(30, 2048), (100, 1800), (500, 1500), (3000, 200)}”
- paper/docs (paper, PDF p.18): “Vertical-Slash represents the Top-K number of vertical and diagonal lines”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F045

**配置层未体现{100}**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/README.md:13-30`
- paper/docs (paper, PDF p.18): “Block-Sparse {100}”
- paper/docs (paper, PDF p.18): “Block-Sparse represents the Top-K number of blocks retained”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F046

**论文Table4/Fig5报告static变体结果；评估入口未暴露static选项，且底层static实现本身只覆盖VS。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type == "minference"`
- paper/docs (paper, PDF p.8): “(1) Ours w/ static, which uses a static sparse mask in the Vertical-Slash and Block-Sparse patterns”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F047

**评估入口无'only A-shape'变体选择，无法复现Table4的该变体。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type == 'minference'`
- paper/docs (paper, PDF p.8): “(2) Ours w/ only A-shape, which is equivalent to StreamingLLM”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F048

**无变体入口，无法复现Table4的only block-sparse行。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type == "minference"`
- paper/docs (paper, PDF p.8): “(3) Ours w/ only block-sparse, which uses only the Block-Sparse pattern in the dynamic sparse calculation”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F049

**论文 1k 全局/4k 局部；代码 128 全局/3968 局部，两参数均不符。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/models_patch.py:66-73`
- condition: `n_init == 128 and n_local == 3968`
- paper/docs (paper, PDF p.6, text lines 32-33): “compiler PIT [ZJZ+23]. We set the target FLOPst to 1k global tokens and 4k local windows in the A-shape pattern. We set last_q = 64 andblock_size = 64 in the Vertical-Slash and Block-Sparse”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F050

**论文要求遍历调用方给定的初始化搜索空间 σ；代码遍历写死的候选表，σ 输入不存在（artifact 范围：无 σ 输入，候选表硬编码）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5): “fori← 1 to|σ| do”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F051

**论文要求 dense 注意力输出 y（含 V）；代码只算注意力权重矩阵，未形成输出**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 24-26): “y← Softmax(QK⊤/ √ d)”
- paper/docs (paper, PDF p.5): “fori← 1 to|ρ| do yi← SparseAttention(QK⊤/ √ d,ρ i)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F052

**论文要求最小化与 dense 输出的偏差；代码最大化权重保留分数，方向与参照对象均不同**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5): “pbest← argmin(yi−y,p best)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F053

**论文要求六类输入；代码签名缺 V、patterns、ρ、t、σ**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 10-12): “Input: Q, K, V ∈ RS×dh, patternsp, search spaceρ, target FLOPst, initial- ized search spaceσ”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F054

**论文要求空集初始化；代码以数值 0 与空字符串初始化，且该初值使负分候选永不被选**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5): “pbest←ϕ”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F055

**论文要求最小化 t_sparse(M)+t_overhead(M)；artifact 执行路径未实现该时间目标。**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/modules/minference_forward.py:199-246`
- paper/docs (paper, PDF p.5): “min tsparse(M ) +toverhead(M ), (2)”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F056

**论文要求块级 logits 先 softmax（并除 √d）得 Â；代码省略 softmax 与缩放，仅用因果掩码后的原始点积排序（artifact 范围：无 softmax/√d 的块级注意力矩阵）**

- category `impl_deviates`, effect `other`, step 4 level L2, priority 2, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:150-165`
- paper/docs (paper, PDF p.5): “bA← softmax  bQcK⊤/ √ d +mcasual ”
- paper/docs (paper, PDF p.6): “Since the mean pooling and matrix multiplication operations are commutative, the resulting attention weights are approximately equivalent to the actual attention weights after mean pooling.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F002

**When ROPE_TYPE is not None: `ROPE_TYPE` is a module-level global computed once from the *first* attention module's `rotary_emb.forward` signature and then reused for every model/layer in the process (`if ROPE_TYPE is not None: return`). Loading a second model with a different RoPE signature in the same process keeps the first model's convention, and `get_cos_sin` then calls `self.rotary_emb` wi...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:30` in `minference/modules/minference_forward.py::set_rope_type`
- condition: `ROPE_TYPE is not None`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: ROPE_TYPE caching only matters when mixing models with different RoPE signatures in one process; it is model-compat plumbing, not a limitation of the sparse mechanism.
- code snippet (`minference/modules/minference_forward.py:30`): `def set_rope_type(self):`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F057

**When "seq_len" in inspect.signature(self.rotary_emb.forward).parameters: ROPE_TYPE is chosen by introspecting the installed transformers rotary embedding signature, so behavior depends on the transformers version. (minference/modules/minference_forward.py:34)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:34` in `minference/modules/minference_forward.py::set_rope_type`
- condition: `"seq_len" in inspect.signature(self.rotary_emb.forward).parameters`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Detecting the RoPE call signature only adapts to the model's rotary-embedding API and does not change the sparse mechanism.
- code snippet (`minference/modules/minference_forward.py:34`): `if 'seq_len' in inspect.signature(self.rotary_emb.forward).parameters:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F058

**When "apply_rotary_pos_emb" not in self.__dict__: `apply_rotary_pos_emb` is rebound as a module-level global from the *first* attention module's `rotary_emb.__class__.__module__` (`getattr(import_module(model_path), "apply_rotary_pos_emb")`), and the guard `if "apply_rotary_pos_emb" not in self.__dict__` is always true because the attribute is never set on `self` (only `self.apply_rotary_pos_em...**

- category `undisclosed`, effect `state`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:74` in `minference/modules/minference_forward.py::init_minference_parameters`
- condition: `"apply_rotary_pos_emb" not in self.__dict__`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: The check is not always true: the branch sets self.apply_rotary_pos_emb = True, so it runs once per module, and cross-model global overwrite is an internal multi-model detail.
- code snippet (`minference/modules/minference_forward.py:74`): `if 'apply_rotary_pos_emb' not in self.__dict__:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F059

**When best_ty == "block_sparse": If block_sparse wins, it is replaced by hard-coded vertical_and_slash with best_v=1000, best_s=6096, ignoring the searched parameters. (minference/modules/minference_forward.py:194)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:194` in `minference/modules/minference_forward.py::search_pattern`
- condition: `best_ty == "block_sparse"`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: The offline pattern search replaces a winning block_sparse (and stream_llm) result with vertical_and_slash 1000/6096, so searched configs can never contain those patterns.
- code snippet (`minference/modules/minference_forward.py:194`): `if best_ty == 'block_sparse':`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F060

**When head_id not in self.best_pattern: When the per-layer pattern file (`config_path`) is missing, unreadable, or has fewer entries than `self.layer_idx`, `init_minference_parameters` sets `self.best_pattern = {}` and every head silently falls back to the hard-coded tuple `("vertical_and_slash", 1000, 6096, 1)` — i.e. vertical=1000, slash=6096 regardless of the actual head. The `ty` element is ...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:430` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `head_id not in self.best_pattern`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 3), not human: Heads missing from the pattern config (or a missing/empty config_path) silently get a fixed default vertical_and_slash (1000, 6096) pattern; the 'whole sequence' claim only holds for q_len <= 6096.
- code snippet (`minference/modules/minference_forward.py:430`): `ty, vertical_size, slash_size, _ = self.best_pattern.get(head_id, ('vertical_and_slash', 1000, 6096, 1))`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F005

**When ty not in {"stream_llm", "vertical_and_slash", "block_sparse"}: The implementation is chosen by the `ty` string read from the user-supplied pattern JSON (`config_path`). Any other value in that file (e.g. a typo, or a pattern produced by a different search version) raises an uncaught `KeyError` at prefill time rather than falling back. (minference/modules/minference_forward.py:441)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:441` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_v4`
- condition: `ty not in {"stream_llm", "vertical_and_slash", "block_sparse"}`
- code snippet (`minference/modules/minference_forward.py:441`): `}[ty]`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F007

**When self.is_search and os.path.exists(self.config_path) and self.layer_idx < len(config_list): With `is_search` enabled, if the output `config_path` already contains an entry for this layer, the forward pass hits a bare `assert False` and aborts — the search cannot be re-run into an existing file. Also, when `is_search` is true the sparse mechanism is never applied (`not self.is_search` in the...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:504` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `self.is_search and os.path.exists(self.config_path) and self.layer_idx < len(config_list)`
- step 4 review: `worth_testing`: blind review by an LLM subagent (round 1), not human: In search mode the code hits assert False when the config file already has an entry for the layer (true by default, since config_path comes from the shipped MODEL2PATH file), and search mode runs dense attention.
- code snippet (`minference/modules/minference_forward.py:504`): `if self.is_search:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F061

**When is_flash_attn_2_available(): When the sparse path is not taken, availability of flash-attn 2 decides between flash_attn_func and gather_qkv. (minference/modules/minference_forward.py:523)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:523` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `is_flash_attn_2_available()`
- code snippet (`minference/modules/minference_forward.py:523`): `if is_flash_attn_2_available():`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F062

**When not (is_flash_attn_2_available()): attn_output = gather_qkv(q, k, v, attention_mask) (minference/modules/minference_forward.py:526)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:526` in `minference/modules/minference_forward.py::minference_forward.forward`
- condition: `not (is_flash_attn_2_available())`
- code snippet (`minference/modules/minference_forward.py:526`): `attn_output = gather_qkv(q, k, v, attention_mask)`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F009

**When head_id not in self.best_pattern: The vLLM variant indexes `self.best_pattern[head_id]` directly (unlike the HF variant's `.get(..., default)`), so a pattern file whose per-layer dict lacks an entry for some head raises `KeyError` during prefill. `self.best_pattern` is rebuilt from the caller-supplied `pattern_config[layer_idx]` on every forward (line 790), so a short/mismatched pattern fi...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:754` in `minference/modules/minference_forward.py::gather_last_q_vertical_slash_topk_vllm`
- condition: `head_id not in self.best_pattern`
- code snippet (`minference/modules/minference_forward.py:754`): `ty, vertical_size, slash_size, _ = self.best_pattern[head_id]`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F036

**When q.dtype != torch.bfloat16: The Triton kernel's compute dtype is chosen from the input dtype: bfloat16 inputs use tl.bfloat16, but any other dtype (e.g. float32 or float16) is silently forced to tl.float16, so the kernel runs a different precision path than the caller's tensor dtype. (minference/ops/block_sparse_flash_attention.py:130)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:130` in `minference/ops/block_sparse_flash_attention.py::_triton_block_sparse_attention`
- condition: `q.dtype != torch.bfloat16`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 1), not human: Choosing the Triton compute dtype (non-bf16 cast to fp16 inside the kernel) is a kernel precision detail, not a limit of the sparse-attention mechanism.
- code snippet (`minference/ops/block_sparse_flash_attention.py:130`): `dtype = tl.bfloat16 if q.dtype == torch.bfloat16 else tl.float16`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F063

**When top_k > context_size // block_size_N: The requested `top_k` (derived from the searched `slash_size`/`vertical_size` in `block_sparse_kernel`) is silently clamped to `context_size // block_size_N`, so for short sequences the block-sparse pattern is denser/different than the searched budget; also `_build_block_index` is called with `block_size_N` for both the M and N block sizes (line 183), ...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/block_sparse_flash_attention.py:164` in `minference/ops/block_sparse_flash_attention.py::_build_block_index`
- condition: `top_k > context_size // block_size_N`
- step 4 review: `real_but_minor`: blind review by an LLM subagent (round 3), not human: Clamping top_k to the number of key blocks that exist is a trivial bound, and block_size_M/N are equal by default, so the mix-up is an internal detail.
- code snippet (`minference/ops/block_sparse_flash_attention.py:164`): `top_k = min(top_k, context_size // block_size_N)`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F064

**When q.dtype != torch.bfloat16: Any query dtype other than bfloat16 (float32, float64, float16 is fine) is silently treated as float16 in the Triton kernel, so a float32 model runs the sparse kernel in half precision without any check or cast of the inputs. (minference/ops/pit_sparse_flash_attention.py:150)**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention.py:150` in `minference/ops/pit_sparse_flash_attention.py::triton_sparse_forward`
- condition: `q.dtype != torch.bfloat16`
- code snippet (`minference/ops/pit_sparse_flash_attention.py:150`): `dtype = tl.bfloat16 if q.dtype == torch.bfloat16 else tl.float16`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F065

**When head_dim not in [16, 32, 64, 128, 256, 512]: For head dims outside the power-of-two list (e.g. 96, 80, 160) the q/k/v are zero-padded up to the next power of two and the kernel runs on the padded tensors; the result is then sliced back with `out[..., :context_size, :head_dim]`. The padded dims contribute zeros to the dot product, so the softmax scale `head_dim ** -0.5` is still correct, bu...**

- category `undisclosed`, effect `path_change`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/ops/pit_sparse_flash_attention_v2.py:188` in `minference/ops/pit_sparse_flash_attention_v2.py::vertical_slash_sparse_attention`
- condition: `head_dim not in [16, 32, 64, 128, 256, 512]`
- step 4 review: `wrong`: blind review by an LLM subagent (round 3), not human: Zero-padding the head dim adds nothing to q.k dot products and sm_scale uses the original head_dim, so the softmax is unchanged, contrary to the claim.
- code snippet (`minference/ops/pit_sparse_flash_attention_v2.py:188`): `if head_dim not in [16, 32, 64, 128, 256, 512]:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F018

**When not isinstance(model, (LlamaForCausalLM, MistralForCausalLM, Qwen2ForCausalLM)) and model.__class__.__name__ not in {"MiniCPMForCausalLM", "Phi3ForCausalLM", "ChatGLMForConditionalGeneration"}: `patch_hf` dispatches on the concrete model class and raises `ValueError("Only supports llama, mistral and qwen2 models.")` for anything else, so the mechanism cannot be applied to other architectur...**

- category `undisclosed`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/patch.py:1252` in `minference/patch.py::patch_hf`
- condition: `not isinstance(model, (LlamaForCausalLM, MistralForCausalLM, Qwen2ForCausalLM)) and model.__class__.__name__ not in {"MiniCPMForCausalLM", "Phi3ForCausalLM", "ChatGLMForConditionalGeneration"}`
- code snippet (`minference/patch.py:1252`): `else:`

**Not tested** (`env_unavailable`): repository third_party/MInference is not checked out

## minference-F066

**实验入口未暴露或设定步长50**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/README.md:13-30`
- condition: `is_search`
- paper/docs (paper, PDF p.18): “The step size of ChangeSpace is set to 50”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F067

**无变体配置，无法复现Table7的only vertical行。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- paper/docs (paper, PDF p.21): “1) Ours w/ only vertical, which only uses vertical lines and the top-1 slash line in Vertical-Slash pattern”
- paper/docs (paper, PDF p.21): “2) Ours w/ only slash, which only uses slash lines and the top-1 vertical line in Vertical-Slash pattern”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F068

**无换算配置入口。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `experiments/infinite_bench/args.py:63-78`
- condition: `attn_type in ("minference", "minference_with_dense")`
- paper/docs (paper, PDF p.21): “The corresponding top-K quantities are set after converting based on FLOPs in kernel.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F069

**论文要求每候选计算真实 kernel FLOPs；代码不计算任何 FLOPs**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- condition: `is_search`
- paper/docs (paper, PDF p.5): “ti← FLOPs_in_kernel(σi)”
- paper/docs (paper, PDF p.5, text lines 45-48): “have similar computational cost. Kernel-aware here in- dicates the computational cost reflects the real FLOPs in GPU kernels, instead of conceptual estimations, which is crucial to achieve the optimal acceleration.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F070

**论文要求以目标 FLOPs 为停止条件的迭代调整；代码无该循环与调整算子**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 16-19): “while|ti−t|>ϵ do σi← ChangeSpace(σi,p i) ti← FLOPs_in_kernel(σi) end while”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F071

**论文要求累积 FLOPs 对齐后的候选到 ρ；代码无该累积步骤**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 20-20): “ρ←ρ∪σi”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F072

**论文要求 FlashAttention 与 V 信息参与选择；代码为稠密权重计算且完全不含 V**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:99-197`
- paper/docs (paper, PDF p.5, text lines 53-56): “approach leverages FlashAttention [ Dao24] to reduce GPU memory overhead and incorporates the informa- tion from the V matrix, enabling end-to-end selection of the best pattern, which further enhances performance.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

## minference-F073

**论文要求分别定义 t_sparse 与 t_overhead；artifact 路径无对应实现。**

- category `not_implemented`, effect `other`, step 4 level L2, priority 3, scope `unknown`
- code: `minference/modules/minference_forward.py:199-246`
- paper/docs (paper, PDF p.5): “where tsparse and toverhead represent the time spent on dynamic sparse attention computation and estimation of the approximate dynamic sparse pattern, respectively.”

**Not tested** (`no_code_location`): no code location (paper-side finding or no code evidence)

