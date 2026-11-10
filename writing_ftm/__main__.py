"""python -m writing_ftm --input examples/critique-request.json --output runs/critique.json"""
import argparse
import json
from pathlib import Path
from .engine import CritiqueEngine, parse_critique, ValidationError
from .providers import MLXProvider
from .runtime import DEFAULT_MODEL_INFO
from .retrieval import retrieve


def main():
    parser = argparse.ArgumentParser(description='Assess a passage against supplied evidence locally.')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--retrieve-k', type=int, help='Select top-k evidence documents with the lexical baseline')
    parser.add_argument('--model-info', default=DEFAULT_MODEL_INFO)
    parser.add_argument('--fixture-response', type=Path, help='Replay supplied JSON; does not run a model')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; choose a new event path')
    try:
        request = json.loads(args.input.read_text())
        if args.fixture_response:
            class Replay:
                def generate(self, messages): return args.fixture_response.read_text()
                def metadata(self): return {'backend': 'fixture', 'model': None}
            provider = Replay()
        else:
            provider = MLXProvider(args.model_info)
        retrieval = None
        if args.retrieve_k is not None:
            retrieval = retrieve(request['passage'], request['sources'], args.retrieve_k)
            if not retrieval:
                raise ValidationError('Retrieval found no matching sources')
            request['sources'] = {row['source_id']: row['text'] for row in retrieval}
        # Previous input uses the same wire schema as a model response.
        previous = parse_critique(json.dumps(request['previous']), request['passage'], request['sources']) if 'previous' in request else None
        event = CritiqueEngine(provider).assess(request['passage'], request['sources'],
                    previous=previous, dispute=request.get('dispute'))
        event['retrieval'] = retrieval
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as output:
            output.write(json.dumps(event, indent=2, ensure_ascii=False) + '\n')
        print(f"Saved {event['critique']['verdict']} critique to {args.output}; substantive review required.")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'Critique rejected: {exc}\n')


if __name__ == '__main__':
    main()
