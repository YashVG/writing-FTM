"""Compare two local retrievers on the same synthetic corpus and passages."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean

from writing_ftm.engine import CritiqueEngine
from writing_ftm.providers import MLXProvider
from writing_ftm.retrieval import retrieve

REQUEST = Path('examples/rag-request.json')
CASES = Path('examples/rag-cases.json')
K = 2


def score_retrieval(cases, rankings, k):
    # A query requiring two documents gets half credit for either one.
    recalls = []
    for case in cases:
        relevant = set(case['gold'])
        if relevant:
            found = {hit['source_id'] for hit in rankings[case['id']][:k]}
            recalls.append(len(found & relevant) / len(relevant))
    return {'mean_recall': mean(recalls), 'all_gold_retrieved': recalls.count(1),
            'answerable_cases': len(recalls)}


def assess_cases(engine, sources, cases, rankings):
    rows = {}
    for case in cases:
        selected = {hit['source_id']: sources[hit['source_id']] for hit in rankings[case['id']]}
        row = {'expected': case['verdict']}
        if selected:
            try:
                event = engine.assess(case['passage'], selected)
                row.update(critique=event['critique'], prompt_sha256=event['prompt_sha256'])
            except ValueError as exc:
                row['error'] = str(exc)
        else:
            row['error'] = 'No retrieved sources'
        rows[case['id']] = row
        print(case['id'], row.get('error') or row['critique']['verdict'], flush=True)
    answerable = [row for row in rows.values() if row['expected'] is not None]
    return {'valid': sum('critique' in row for row in answerable),
            'correct_verdicts': sum(row.get('critique', {}).get('verdict') == row['expected']
                                    for row in answerable),
            'answerable_cases': len(answerable), 'cases': rows}


def benchmark(live):
    from writing_ftm.semantic_retrieval import LocalEmbeddings, SemanticIndex
    cases = json.loads(CASES.read_text())
    sources = json.loads(REQUEST.read_text())['sources']
    embeddings = LocalEmbeddings()
    index = SemanticIndex(sources, embeddings, chunk_size=160, chunk_overlap=32)
    report = {
        'provenance': {'fixture_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in (REQUEST, CASES)},
                       'embedding': embeddings.metadata(), 'index': index.manifest,
                       'query': 'passage', 'k': K, 'min_cosine_score': None},
        'labels': {case['id']: case['gold'] for case in cases}, 'retrieval': {},
    }
    for name in ('lexical', 'semantic'):
        rankings = {}
        for case in cases:
            if name == 'lexical':
                hits = retrieve(case['passage'], sources, K)
            else:
                hits = index.retrieve(case['passage'], K)
            rankings[case['id']] = [{'source_id': hit['source_id'], 'score': hit['score']} for hit in hits]
        report['retrieval'][name] = {
            'at_1': score_retrieval(cases, rankings, 1), 'at_2': score_retrieval(cases, rankings, K),
            'hits_on_unanswerable': {case['id']: len(rankings[case['id']]) for case in cases if not case['gold']},
            'rankings': rankings,
        }
    del index, embeddings
    if live:
        provider = MLXProvider()
        engine = CritiqueEngine(provider)
        report['provenance'].update(provider=provider.metadata(), engine_sha256=hashlib.sha256(
            Path('writing_ftm/engine.py').read_bytes()).hexdigest())
        report['critique'] = {}
        for name, results in report['retrieval'].items():
            print(f'Running Qwen with {name} evidence', flush=True)
            report['critique'][name] = assess_cases(engine, sources, cases, results['rankings'])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Also score Qwen verdicts with each top-2 context')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path')
    report = benchmark(args.live)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
        file.write('\n')
    print(f'Saved {args.output}')


if __name__ == '__main__':
    main()
