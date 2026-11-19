"""python -m writing_ftm --input examples/critique-request.json --output runs/critique.json"""
import argparse
import json
from pathlib import Path
from .engine import CritiqueEngine, parse_critique, ValidationError
from .providers import MLXProvider
from .runtime import DEFAULT_MODEL_INFO
from .retrieval import retrieve
from .embedding_runtime import DEFAULT_EMBEDDING_INFO


def select_evidence(request, args):
    """Return ranked original documents and optional semantic provenance."""
    query = request['passage'] if args.retrieval_query is None else args.retrieval_query
    if args.retriever == 'lexical':
        return retrieve(query, request['sources'], args.retrieve_k), None

    try:
        from .semantic_retrieval import LocalEmbeddings, SemanticIndex, fingerprint
    except ImportError as exc:
        raise ValidationError('Semantic retrieval needs the optional dependencies. '
                              'Run ./scripts/setup_rag.sh (see docs/semantic-rag.md).') from exc
    embeddings = LocalEmbeddings(args.embedding_model_info)
    index = SemanticIndex(request['sources'], embeddings, chunk_size=args.chunk_size,
                          chunk_overlap=args.chunk_overlap)
    hits = index.retrieve(query, args.retrieve_k, min_score=args.semantic_min_score,
                          max_context_chars=args.retrieval_context_chars)
    metadata = {**index.manifest, 'embedding': embeddings.metadata(), 'query': query,
                'query_sha256': fingerprint(query), 'k': args.retrieve_k,
                'min_score': args.semantic_min_score, 'max_context_chars': args.retrieval_context_chars}
    return hits, metadata


def main():
    parser = argparse.ArgumentParser(description='Assess a passage against supplied evidence locally.')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--retrieve-k', type=int, help='Select top-k source documents before critique generation')
    parser.add_argument('--retriever', choices=('lexical', 'semantic'), default='lexical')
    parser.add_argument('--retrieval-query', help='Optional short search query; the passage is still assessed unchanged')
    parser.add_argument('--embedding-model-info', default=DEFAULT_EMBEDDING_INFO)
    parser.add_argument('--chunk-size', type=int, default=600, help='Semantic search chunk size in characters')
    parser.add_argument('--chunk-overlap', type=int, default=100)
    parser.add_argument('--semantic-min-score', type=float, help='Optional cosine threshold; not a confidence probability')
    parser.add_argument('--retrieval-context-chars', type=int, default=16000, help='Semantic parent context limit; fail rather than truncate')
    parser.add_argument('--model-info', default=DEFAULT_MODEL_INFO)
    parser.add_argument('--fixture-response', type=Path, help='Replay supplied JSON; does not run a model')
    args = parser.parse_args()
    if args.retrieve_k is not None and args.retrieve_k < 1:
        parser.error('--retrieve-k must be positive')
    if args.retrieve_k is None and (args.retriever == 'semantic' or args.retrieval_query is not None):
        parser.error('--retriever semantic and --retrieval-query require --retrieve-k')
    if args.semantic_min_score is not None and args.retriever != 'semantic':
        parser.error('--semantic-min-score requires --retriever semantic')
    if args.output.exists():
        parser.error('Output already exists; choose a new event path')
    try:
        request = json.loads(args.input.read_text())
        retrieval = None
        retrieval_metadata = None
        if args.retrieve_k is not None:
            retrieval, retrieval_metadata = select_evidence(request, args)
            if not retrieval:
                raise ValidationError('Retrieval found no matching sources')
            request['sources'] = {row['source_id']: row['text'] for row in retrieval}
        if args.fixture_response:
            class Replay:
                def generate(self, messages): return args.fixture_response.read_text()
                def metadata(self): return {'backend': 'fixture', 'model': None}
            provider = Replay()
        else:
            provider = MLXProvider(args.model_info)
        # Previous input uses the same wire schema as a model response.
        previous = parse_critique(json.dumps(request['previous']), request['passage'], request['sources']) if 'previous' in request else None
        event = CritiqueEngine(provider).assess(request['passage'], request['sources'],
                    previous=previous, dispute=request.get('dispute'))
        event['retrieval'] = retrieval
        if retrieval_metadata is not None:
            event['retrieval_metadata'] = retrieval_metadata
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as output:
            output.write(json.dumps(event, indent=2, ensure_ascii=False) + '\n')
        print(f"Saved {event['critique']['verdict']} critique to {args.output}; substantive review required.")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'Critique rejected: {exc}\n')


if __name__ == '__main__':
    main()
