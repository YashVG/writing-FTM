"""Integrity checks for the public MiniLM snapshot used by local retrieval."""
import hashlib
import json
from pathlib import Path

MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
DEFAULT_EMBEDDING_INFO = 'runs/rag/embedding-model.json'
SETUP_HINT = 'Run runs/rag-venv/bin/python -m scripts.download_embeddings'
# Digests of the ten inference files in REVISION. Pinning modules.json checks
# Transformer -> mean Pooling -> Normalize. Normalize has no parameter file.
FILES_SHA256 = {
    'model.safetensors': '53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db',
    'config.json': '953f9c0d463486b10a6871cc2fd59f223b2c70184f49815e7efbcab5d8908b41',
    'config_sentence_transformers.json': '061ca9d39661d6c6d6de5ba27f79a1cd5770ea247f8d46412a68a498dc5ac9f3',
    'modules.json': '84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf',
    'sentence_bert_config.json': 'fc1993fde0a95c24ec6c022539d41cf6e2f7c9721e5415d6fb6897472a9cd4b7',
    '1_Pooling/config.json': '4be450dde3b0273bb9787637cfbd28fe04a7ba6ab9d36ac48e92b11e350ffc23',
    'tokenizer.json': 'be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037',
    'tokenizer_config.json': 'acb92769e8195aabd29b7b2137a9e6d6e25c476a4f15aa4355c233426c61576b',
    'special_tokens_map.json': '303df45a03609e4ead04bc3dc1536d0ab19b5358db685b6f3da123d05ec200e3',
    'vocab.txt': '07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3',
}


def verify_snapshot(folder):
    for name, expected in FILES_SHA256.items():
        try:
            with (folder / name).open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
        except OSError as exc:
            raise ValueError(f'Missing or unreadable embedding file {name}. {SETUP_HINT}') from exc
        if digest != expected:
            raise ValueError(f'Embedding checksum mismatch for {name}. {SETUP_HINT} --force-download')


def load_embedding_info(path=DEFAULT_EMBEDDING_INFO):
    try:
        info = json.loads(Path(path).read_text())
        folder = Path(info['path'])
        if (info['model'], info['revision'], info['files_sha256']) != (MODEL, REVISION, FILES_SHA256):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError(f'Pinned embedding model manifest is missing or invalid. {SETUP_HINT}') from None
    verify_snapshot(folder)
    return info
