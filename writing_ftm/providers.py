"""Lazy local model loading; no model download or ML imports for fixture tests."""
import json
from pathlib import Path
from threading import Lock


class MLXProvider:
    def __init__(self, model_info='runs/pilot/model.json', max_tokens=1024):
        self.info = json.loads(Path(model_info).read_text())
        if max_tokens <= 0:
            raise ValueError('max_tokens must be positive')
        self.max_tokens = max_tokens
        self._loaded = None
        self._lock = Lock()

    def metadata(self):
        return {'model': self.info['model'], 'revision': self.info['revision'],
                'temperature': 0, 'max_tokens': self.max_tokens, 'backend': 'mlx'}

    def generate(self, messages):
        from mlx_lm import load, stream_generate
        from mlx_lm.sample_utils import make_sampler
        with self._lock:
            if self._loaded is None:
                self._loaded = load(self.info['path'])
            model, tokenizer = self._loaded
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            chunks = list(stream_generate(model, tokenizer, prompt=prompt,
                          max_tokens=self.max_tokens, sampler=make_sampler(temp=0)))
            if not chunks or chunks[-1].generation_tokens >= self.max_tokens:
                raise ValueError('Empty or token-capped output; no critique accepted')
            return ''.join(chunk.text for chunk in chunks)
