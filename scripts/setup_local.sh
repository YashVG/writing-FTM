#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
    printf '%s\n' 'Live inference requires Apple Silicon macOS. For the model-free demo: python3 -m writing_ftm.demo' >&2
    exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
    printf '%s\n' 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2
    exit 1
fi
if [ ! -x .venv/bin/python ]; then
    uv venv --python 3.12 --python-preference only-managed .venv
fi
uv pip sync --python .venv/bin/python requirements.lock
.venv/bin/python -m scripts.download_model "$@"
.venv/bin/python -m scripts.check_setup
