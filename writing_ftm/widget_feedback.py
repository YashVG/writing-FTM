"""One-shot local critique worker. Inputs and results stay in memory, never logged."""
import json
import sys

from .engine import CritiqueEngine, ValidationError
from .presentation import from_record, present
from .providers import MLXProvider
from .runtime import SetupError

MAX_CHARS = 8000
MAX_BYTES = 100000  # UTF-8 JSON envelope for both 8,000-character fields.


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError('Expected a JSON request.')
    for key, label in (('passage', 'passage'), ('source', 'source evidence')):
        value = request.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'Add {label} before requesting feedback.')
        if len(value) > MAX_CHARS:
            raise ValueError(f'Keep {label} under 8,001 characters.')
    return request['passage'], {'source-1': request['source']}


def run(request, provider):
    passage, sources = validate_request(request)
    event = CritiqueEngine(provider).assess(passage, sources)
    critique = from_record(event['critique'])
    # Precompute all views once. Switching controls never calls the model again.
    presentations = {
        f'{warmth}/{directness}': present(critique, warmth, directness)
        for warmth in ('neutral', 'warm')
        for directness in ('explanation-first', 'action-first')
    }
    return {'presentations': presentations, 'provider': event['provider'],
            'validation': event['validation'], 'human_review_required': True}


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('Request is too large.')
        request = json.loads(raw)
        validate_request(request)
        result = run(request, MLXProvider(max_tokens=1536))
        print(json.dumps(result, ensure_ascii=False))
    except Exception as error:
        # Validators/provider errors can contain model text. Never echo them.
        message = str(error) if isinstance(error, SetupError) else ('The model returned an invalid critique or unverified quote. No feedback accepted. Try a shorter passage and source.'
                   if isinstance(error, ValidationError) else
                   'Local critique failed. Check that both fields are filled, each is at most 8,000 characters, and the local model is installed. A shorter passage may help.')
        print(json.dumps({'error': message}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
