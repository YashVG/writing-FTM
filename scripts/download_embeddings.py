"""Prepare a verified MiniLM snapshot for offline semantic retrieval."""
import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from writing_ftm.embedding_runtime import (
    DEFAULT_EMBEDDING_INFO, FILES_SHA256, MODEL, REVISION, verify_snapshot,
)


def prepare_embeddings(folder, output=Path(DEFAULT_EMBEDDING_INFO)):
    folder = Path(folder).resolve()
    verify_snapshot(folder)
    info = {'model': MODEL, 'revision': REVISION, 'path': str(folder), 'files_sha256': FILES_SHA256}
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as directory:
        temporary = Path(directory) / 'manifest.json'
        temporary.write_text(json.dumps(info, indent=2) + '\n')
        temporary.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument('--offline', action='store_true', help='Use only cached public weights')
    options.add_argument('--force-download', action='store_true', help='Replace damaged cache files')
    args = parser.parse_args()
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    try:
        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import LocalEntryNotFoundError
    except ImportError:
        parser.exit(1, 'Missing RAG dependencies. See docs/semantic-rag.md for setup.\n')
    try:
        folder = snapshot_download(MODEL, revision=REVISION, allow_patterns=list(FILES_SHA256),
                                   local_files_only=args.offline, force_download=args.force_download,
                                   token=False)
        prepare_embeddings(folder)
    except LocalEntryNotFoundError:
        parser.exit(1, 'Pinned MiniLM snapshot unavailable. Connect and run setup without --offline.\n')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Embedding setup failed: {exc}\n')
    print(f'Ready: {DEFAULT_EMBEDDING_INFO} (pinned local MiniLM)')


if __name__ == '__main__':
    main()
