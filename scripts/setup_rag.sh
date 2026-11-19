#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

case "$#:${1:-}" in
    0:|1:--offline) ;;
    *) echo 'Usage: ./scripts/setup_rag.sh [--offline]' >&2; exit 2 ;;
esac
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
    echo 'The combined RAG and MLX environment requires Apple Silicon macOS.' >&2
    exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
    echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2
    exit 1
fi
if [ "${1:-}" = '--offline' ]; then
    export UV_OFFLINE=1 HF_HUB_OFFLINE=1
fi

rag_python=runs/rag-venv/bin/python
if [ ! -x "$rag_python" ]; then
    uv venv --python 3.12 --python-preference only-managed runs/rag-venv
fi
uv pip sync --python "$rag_python" --require-hashes requirements-rag.lock
"$rag_python" -m scripts.download_model "$@"
"$rag_python" -m scripts.download_embeddings "$@"
"$rag_python" -m scripts.check_setup
