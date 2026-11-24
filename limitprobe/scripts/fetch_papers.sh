#!/usr/bin/env bash
# Download the papers into third_party/papers/ (not committed) and record their checksums.
# arXiv URLs name an exact version, so the text and every quote checked against it stay reproducible.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p third_party/papers
while read -r id url; do
  out="third_party/papers/$id.pdf"
  [ -s "$out" ] || curl -fsSL --retry 2 -A "limitprobe/0.1" -o "$out" "$url"
  [ "$(head -c 4 "$out")" = "%PDF" ] || { echo "$id: not a PDF" >&2; rm -f "$out"; exit 1; }
  echo "$id $(sha256sum "$out" | cut -c1-16) $url"
done <<'LIST'
flexprefill https://arxiv.org/pdf/2502.20766v1
minference https://arxiv.org/pdf/2407.02490v1
nnsmith https://arxiv.org/pdf/2207.13066v2
infinigen https://www.usenix.org/system/files/osdi24-lee.pdf
sparta https://www.usenix.org/system/files/osdi22-zheng-ningxin.pdf
LIST
