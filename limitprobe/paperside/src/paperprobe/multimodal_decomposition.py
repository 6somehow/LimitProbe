"""Replay archived paper prompts with text and original PDF page images."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re


from .io import file_sha256, read_json, write_json
from .paper_decomposition import inventory, numbered, split_group
from .team_paper_side import gateway


def parse_response(response):
    choice = response["choices"][0]
    if choice["finish_reason"] != "stop":
        raise ValueError(f"Incomplete generation: {choice['finish_reason']}")
    content = choice["message"]["content"].strip()
    fence = re.fullmatch(r"\x60\x60\x60(?:json)?\s*(.*?)\s*\x60\x60\x60", content, re.S | re.I)
    result = json.loads(fence[1] if fence else content)
    if not isinstance(result, dict):
        raise ValueError("Expected JSON object")
    return result


def make_content(data, images):
    # Exactly the same textual JSON serialization as the legacy team_run.call.
    text = json.dumps(data, ensure_ascii=False)
    if not images:
        return text
    return [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": image["data_url"]}}
        for image in images
    ]


def call(model, prompt, data, images, destination):
    request_path = destination.with_suffix(".request.json")
    if request_path.exists() or destination.exists():
        raise ValueError("An existing API attempt must not be overwritten")
    record = dict(model=model, prompt=prompt, data=data,
                  image_pages=[{k: v for k, v in image.items() if k != "data_url"} for image in images],
                  settings=dict(temperature=0, max_tokens=6500, reasoning_effort="none"),
                  content_order="serialized text first; image blocks in ascending physical page order")
    write_json(request_path, record)
    response = gateway("/chat/completions", dict(
        model=model, temperature=0, max_tokens=6500, reasoning_effort="none",
        messages=[dict(role="system", content=prompt),
                  dict(role="user", content=make_content(data, images))]))
    write_json(destination, response)
    raw = parse_response(response)
    meta = dict(model=response.get("model"), usage=response.get("usage"),
                finish_reason=response["choices"][0]["finish_reason"])
    return raw, meta


def images_from_pdf(pdf, output):
    directory = output / "images"
    directory.mkdir()
    images = []
    import pymupdf  # Optional vision dependency; text/interface checks work without it.
    with pymupdf.open(pdf) as document:
        for i, page in enumerate(document, 1):
            # 1224×1584 per page, with color retained for graph and legend relations.
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
            content = pixmap.tobytes("jpeg", jpg_quality=92)
            path = directory / f"page-{i:02d}.jpg"
            path.write_bytes(content)
            images.append(dict(page=i, path=str(path.resolve()), sha256=file_sha256(path),
                               width=pixmap.width, height=pixmap.height, mime_type="image/jpeg",
                               data_url="data:image/jpeg;base64," + base64.b64encode(content).decode()))
    return images


def run(pdf, baseline, output, model):
    if output.exists():
        raise ValueError("Use a fresh comparison output directory")
    original_request = read_json(baseline / "map.raw.request.json")
    original_map = read_json(baseline / "mechanism-map.json")
    if file_sha256(pdf) != original_map["pdf_sha256"]:
        raise ValueError("Paper differs from historical experiment")
    pages = [row["text"] for row in original_request["data"]["pages"]]
    if [row["page"] for row in original_request["data"]["pages"]] != list(range(1, len(pages) + 1)):
        raise ValueError("Historical PDF pages must be contiguous and ascending")
    split_request = read_json(baseline / "M01.raw.request.json")
    output.mkdir(parents=True)
    images = images_from_pdf(pdf, output)
    if len(images) != len(pages):
        raise ValueError("Image/text PDF page count mismatch")
    protocol = dict(
        question="Does adding original page images change paper-only mechanism and behavior extraction?",
        pdf_sha256=file_sha256(pdf), baseline=str(baseline.resolve()),
        baseline_map_request_sha256=file_sha256(baseline / "map.raw.request.json"),
        baseline_map_response_sha256=file_sha256(baseline / "map.raw.json"),
        historical_model=original_map["model"]["model"], requested_model=model,
        map_prompt=original_request["prompt"], split_prompt=split_request["prompt"],
        textual_input="unchanged archived per-page pypdf text",
        intervention="original PDF images appended in physical page order",
        image_pages=[{k: v for k, v in image.items() if k != "data_url"} for image in images],
        settings=dict(temperature=0, max_tokens=6500, reasoning_effort="none"),
        validation="same exact-quote validator for all arms; unmatched visual quotes retained as rejections",
        validation_mechanism_cap=60, legacy_validation_cap=18,
        mechanism_cap_note="Uniform post-generation cap for replay arms prevents discarding new candidates above legacy budget; prompt unchanged.",
        concurrency=2, request_budget=22, split_batch_size=3, retries=0,
        stages=["contemporary text-only map", "text+images map", "text+images mechanism splits", "current text-only mechanism splits"],
        target_execution="not_run", reference_annotations_input="not_supplied",
        inference_limit="single-paper development comparison; one generation per condition",
        implementation_sha256=file_sha256(Path(__file__)))
    write_json(output / "protocol.json", protocol)
    # Revalidate history using the same post-generation cap as both current arms.
    historical = inventory(parse_response(read_json(baseline / "map.raw.json")), pages, max_mechanisms=60)
    write_json(output / "historical-revalidated.json", historical)

    def map_arm(name):
        arm = output / name
        arm.mkdir()
        raw, meta = call(model, original_request["prompt"], original_request["data"],
                         images if name == "vision" else [], arm / "map.raw.json")
        mapped = dict(paper=original_map["paper"], pdf_sha256=protocol["pdf_sha256"],
                      requested_model=model, model=meta,
                      **inventory(raw, pages, max_mechanisms=60))
        write_json(arm / "mechanism-map.json", mapped)
        print(name, len(raw["mechanisms"]), "raw mechanisms", len(mapped["mechanisms"]),
              "valid", len(mapped["rejected"]), "rejected", flush=True)
        return mapped

    maps, failures = {}, []
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [(name, executor.submit(map_arm, name)) for name in ("text-control", "vision")]
        for name, job in jobs:
            try:
                maps[name] = job.result()
            except (ValueError, KeyError, TypeError) as exc:
                failures.append(dict(stage=name, reason=str(exc)))
    if "vision" not in maps:
        write_json(output / "failures.json", failures)
        raise ValueError("Vision map failed; raw attempt preserved")
    mechanisms = maps["vision"]["mechanisms"]
    batches = [mechanisms[i:i + 3] for i in range(0, len(mechanisms), 3)]

    def split(batch):
        indices = sorted({page for mechanism in batch for page in mechanism["pages"]})
        payload = dict(mechanisms=batch, pages=numbered(pages, indices))
        raw, meta = call(model, split_request["prompt"], payload,
                         [images[i - 1] for i in indices],
                         output / "vision" / f'{batch[0]["id"]}.raw.json')
        groups = {m["id"]: split_group(raw, m, pages) for m in batch}
        write_json(output / "vision" / f'{batch[0]["id"]}.validated.json',
                   dict(groups=groups, model=meta))
        print("split", [m["id"] for m in batch],
              sum(len(g["behaviors"]) for g in groups.values()), "valid behaviors", flush=True)
        return groups, meta

    groups, models = {}, []
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [(batch, executor.submit(split, batch)) for batch in batches]
        for batch, job in jobs:
            try:
                values, meta = job.result()
                groups.update(values)
                models.append(meta)
            except (ValueError, KeyError, TypeError) as exc:
                failures.append(dict(stage="split", ids=[m["id"] for m in batch], reason=str(exc)))
    for mechanism in mechanisms:
        groups.setdefault(mechanism["id"], dict(status="unresolved", behaviors=[], rejected=[],
                          open_questions=["No validated batch result"]))
    frozen = dict(
        paper=original_map["paper"], pdf_sha256=protocol["pdf_sha256"],
        map_sha256=file_sha256(output / "vision" / "mechanism-map.json"),
        behaviors=[row for g in groups.values() for row in g["behaviors"]],
        decomposition=groups,
        rejected=[dict(mechanism=mid, **row) for mid, group in groups.items() for row in group["rejected"]],
        model=maps["vision"]["model"], batch_models=models, failures=failures,
        semantic_review="pending", source_access="text_and_original_page_images",
        implementation_sha256=protocol["implementation_sha256"])
    write_json(output / "vision" / "frozen.json", frozen)
    write_json(output / "failures.json", failures)
    print("done", len(frozen["behaviors"]), "vision behaviors;", len(failures), "failed stages", flush=True)
    if "text-control" in maps:
        # Reuse the ordinary text-only entry point, preserving its normal callers.
        from pypdf import PdfReader
        from .paper_decomposition import SPLIT, run as run_text
        if SPLIT != split_request["prompt"]:
            raise ValueError("Current text splitter differs from the archived prompt")
        if [p.extract_text() or "" for p in PdfReader(pdf).pages] != pages:
            raise ValueError("Current text parser differs from the archived page input")
        attempted = len(list(output.glob("*/*.raw.request.json")))
        text_batches = (len(maps["text-control"]["mechanisms"]) + 2) // 3
        if attempted + text_batches > protocol["request_budget"]:
            raise ValueError("Text-control continuation would exceed the request budget")
        run_text(pdf, original_map["paper"], output / "text-control", model, 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="x-test-2")
    args = parser.parse_args()
    run(args.pdf, args.baseline, args.output, args.model)
