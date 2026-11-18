"""Driver for flexposit-F009: run the channel_window CLI budget mode.

The target `if args.downgrade:` lives in the argparse-driven CLI `main` of
flexposit.mpq.channel_window.  The declared call-chain has status `not_found`:
the Python API entry `flexposit.api.quantize` never calls this CLI main.  The
driver therefore calls the CLI main directly (entry_reason in form.json) after
building a tiny, real (not stubbed) GPT-2 checkpoint, tokenizer and sensitivity
CSV in a scratch directory, and passing the witness values through argv.
"""

import csv
import os
import shutil
import sys
import tempfile

import torch

# Make the pinned repository importable regardless of the harness' cwd.
def _add_repo_src():
    # The harness puts the repository root first on sys.path. Prefer that exact
    # checkout (src layout) so a clean-checkout replay imports its own pinned copy.
    for entry in list(sys.path):
        if not entry:
            continue
        for cand in (os.path.join(entry, "src"),
                     os.path.join(entry, "third_party", "FlexPosit", "src")):
            if os.path.isdir(os.path.join(cand, "flexposit")):
                if cand not in sys.path:
                    sys.path.insert(0, cand)
                return
    here = os.path.abspath(__file__)
    roots = [os.getcwd()]
    p = here
    for _ in range(10):
        p = os.path.dirname(p)
        roots.append(p)
    for root in roots:
        cand = os.path.join(root, "third_party", "FlexPosit", "src")
        if os.path.isdir(os.path.join(cand, "flexposit")):
            if cand not in sys.path:
                sys.path.insert(0, cand)
            return

_add_repo_src()

from flexposit.mpq import channel_window
from flexposit.utils import quantizable_layers, to_cout_first


def _build_tiny_checkpoint(root):
    from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace

    model_dir = os.path.join(root, "tiny_gpt2")
    os.makedirs(model_dir, exist_ok=True)
    if not os.path.isfile(os.path.join(model_dir, "config.json")):
        torch.manual_seed(0)
        cfg = GPT2Config(vocab_size=128, n_embd=32, n_layer=2, n_head=2, n_positions=64)
        model = GPT2LMHeadModel(cfg).eval()
        model.save_pretrained(model_dir, safe_serialization=True)

        vocab = {f"tok{i}": i for i in range(127)}
        vocab["[UNK]"] = 127
        backend = Tokenizer(WordLevel(vocab, unk_token="[UNK]"))
        backend.pre_tokenizer = Whitespace()
        tok = PreTrainedTokenizerFast(
            tokenizer_object=backend, unk_token="[UNK]", pad_token="[UNK]", eos_token="[UNK]"
        )
        tok.save_pretrained(model_dir)
    return model_dir


def _write_sensitivity(model_dir, root):
    from transformers import AutoModelForCausalLM

    csv_path = os.path.join(root, "sensitivity.csv")
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float32)
    rows = []
    for name, mod in quantizable_layers(model, skip_lm_head=True):
        cout = to_cout_first(mod, mod.weight).shape[0]
        for wi, ws in enumerate(range(0, cout, 8)):
            we = min(cout, ws + 8)
            # Deterministic spread: both negative and positive delta_ppl.
            dp = -1.0 + 0.1 * (wi % 10)
            rows.append((name, ws, we, dp, 1))
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["layer", "win_start", "win_end", "delta_ppl", "channel_window"])
        for r in rows:
            w.writerow([r[0], r[1], r[2], f"{r[3]:.6f}", r[4]])
    return csv_path


def run(inputs):
    torch.manual_seed(0)
    torch.set_num_threads(1)
    root = tempfile.mkdtemp(prefix="f009_", dir=os.path.dirname(os.path.abspath(__file__)))
    model_dir = _build_tiny_checkpoint(root)
    csv_path = _write_sensitivity(model_dir, root)
    out_dir = os.path.join(root, "out")

    argv = [
        "channel_window",
        "--base_dir", model_dir,
        "--fp32_reference_dir", model_dir,
        "--sensitivity_csv", csv_path,
        "--out_dir", out_dir,
        "--target_avg_bits", str(inputs["target_avg_bits"]),
        "--base_bits", "4",
        "--upgrade_bits", "5",
        "--dtype", "fp32",
        "--dry_run",
    ]
    if inputs["downgrade"]:
        argv.append("--downgrade")

    old_argv = sys.argv
    sys.argv = argv
    try:
        return channel_window.main()
    finally:
        sys.argv = old_argv
        shutil.rmtree(root, ignore_errors=True)
