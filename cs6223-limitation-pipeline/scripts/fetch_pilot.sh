#!/usr/bin/env bash
# Clone the pilot artifact at the pinned commit into third_party/.
set -euo pipefail
cd "$(dirname "$0")/.."
COMMIT=a24b27bf117fd6ad4ba34b0db82c598e7786fd59
if [ ! -d third_party/FlexPrefill ]; then
  git clone https://github.com/bytedance/FlexPrefill.git third_party/FlexPrefill
fi
git -C third_party/FlexPrefill fetch --depth 1 origin "$COMMIT" 2>/dev/null || true
git -C third_party/FlexPrefill checkout -q "$COMMIT"
echo "FlexPrefill @ $(git -C third_party/FlexPrefill rev-parse --short HEAD)"
