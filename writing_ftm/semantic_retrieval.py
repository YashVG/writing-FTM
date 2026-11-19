"""Local LangChain chunk search over an in-memory index of source documents."""
import hashlib
import importlib.metadata
import json
import math
import os

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .embedding_runtime import DEFAULT_EMBEDDING_INFO, load_embedding_info

MAX_CORPUS_CHARS = 250_000
MAX_CHUNKS = 2000
DEFAULT_CONTEXT_CHARS = 16_000


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class LocalEmbeddings(Embeddings):
    """LangChain adapter for CPU Sentence Transformers, with no silent truncation."""
    def __init__(self, model_info=DEFAULT_EMBEDDING_INFO):
        info = load_embedding_info(model_info)
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        try:
            from sentence_transformers import SentenceTransformer
            import torch
        except ImportError as exc:
            raise ValueError('Missing embedding runtime. Install the dependencies in docs/semantic-rag.md.') from exc
        torch.set_num_threads(4)
        self.model = SentenceTransformer(info['path'], device='cpu', local_files_only=True,
                                         trust_remote_code=False, token=False,
                                         model_kwargs={'use_safetensors': True})
        self.info = {key: info[key] for key in ('model', 'revision', 'files_sha256')}

    def embed_documents(self, texts):
        lengths = [len(tokens) for tokens in self.model.tokenizer(
            texts, truncation=False, padding=False)['input_ids']]
        if any(length > self.model.max_seq_length for length in lengths):
            raise ValueError('Text exceeds the embedding token limit; shorten --retrieval-query '
                             'or reduce --chunk-size. No truncated embedding was accepted.')
        return self.model.encode(texts, batch_size=32, normalize_embeddings=True,
                                 show_progress_bar=False, convert_to_numpy=True).tolist()

    def embed_query(self, text):
        return self.embed_documents([text])[0]

    def metadata(self):
        return {**self.info, 'device': 'cpu', 'threads': 4, 'normalize_embeddings': True,
                'dimensions': self.model.get_embedding_dimension(),
                'max_sequence_tokens': self.model.max_seq_length}


class SemanticIndex:
    """Rank parents by their best chunk; return unchanged full parents for validation.

    Searching all chunks permits deterministic source-ID tie breaks and unique
    parents. InMemoryVectorStore already does exhaustive cosine search, not ANN.
    """
    def __init__(self, sources, embeddings, *, chunk_size=600, chunk_overlap=100):
        if not isinstance(sources, dict) or not sources:
            raise ValueError('Semantic retrieval needs a nonempty source collection.')
        if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
               for k, v in sources.items()):
            raise ValueError('Every source needs a nonempty string ID and text.')
        if not isinstance(chunk_size, int) or not isinstance(chunk_overlap, int) or not 0 <= chunk_overlap < chunk_size:
            raise ValueError('Chunk size must be positive and overlap smaller than the size.')
        if sum(map(len, sources.values())) > MAX_CORPUS_CHARS:
            raise ValueError(f'Semantic corpus exceeds {MAX_CORPUS_CHARS:,} characters.')
        self.sources = dict(sorted(sources.items()))
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                                                  add_start_index=True, strip_whitespace=False)
        chunks = splitter.create_documents(list(self.sources.values()),
                                           metadatas=[{'source_id': key} for key in self.sources])
        if not chunks or len(chunks) > MAX_CHUNKS:
            raise ValueError(f'Semantic index requires 1–{MAX_CHUNKS} chunks.')
        for chunk in chunks:
            source_id = chunk.metadata['source_id']
            start = chunk.metadata['start_index']
            end = start + len(chunk.page_content)
            if start < 0 or self.sources[source_id][start:end] != chunk.page_content:
                raise ValueError('Chunk does not map exactly to its original source.')
            chunk.metadata.update(start=start, end=end)
            chunk.id = fingerprint([source_id, start, end, chunk.page_content])
        self.chunk_count = len(chunks)
        self.store = InMemoryVectorStore(embeddings)
        self.store.add_documents(chunks)
        self.manifest = {
            'method': 'langchain-semantic-parent', 'score': 'cosine_similarity',
            'corpus_sha256': fingerprint(self.sources), 'documents': len(self.sources),
            'chunks': self.chunk_count, 'chunk_size_chars': chunk_size, 'chunk_overlap_chars': chunk_overlap,
            'context_policy': 'unchanged full parent documents; never concatenated chunks',
            'libraries': {name: importlib.metadata.version(name) for name in
                          ('langchain-core', 'langchain-text-splitters')},
        }

    def retrieve(self, query, k=3, *, min_score=None, max_context_chars=DEFAULT_CONTEXT_CHARS):
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Retrieval query must be nonempty.')
        if k < 1 or max_context_chars < 1:
            raise ValueError('k and context limit must be positive.')
        if min_score is not None and (not math.isfinite(min_score) or not -1 <= min_score <= 1):
            raise ValueError('Minimum cosine score must be between -1 and 1.')
        matches = self.store.similarity_search_with_score(query, k=self.chunk_count)
        ranked = sorted(matches, key=lambda pair: (-float(pair[1]), pair[0].metadata['source_id'],
                                                   pair[0].metadata['start']))
        hits = []
        seen = set()
        for chunk, score in ranked:
            if not math.isfinite(float(score)):
                raise ValueError('Embedding search produced a non-finite score.')
            source_id = chunk.metadata['source_id']
            if source_id in seen or (min_score is not None and score < min_score):
                continue
            seen.add(source_id)
            hits.append({'source_id': source_id, 'score': float(score), 'text': self.sources[source_id],
                         'matched_chunk': {'id': chunk.id, 'start': chunk.metadata['start'],
                                           'end': chunk.metadata['end'], 'text': chunk.page_content}})
            if len(hits) == k:
                break
        if sum(len(hit['text']) for hit in hits) > max_context_chars:
            raise ValueError('Selected parent documents exceed the context limit. Lower --retrieve-k '
                             'or supply shorter sources; evidence was not silently truncated.')
        return hits
