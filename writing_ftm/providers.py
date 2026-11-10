"""Lazy local model loading; no model download or ML imports for fixture tests."""
from threading import Lock
from .runtime import DEFAULT_MODEL_INFO, load_model_info


class MLXProvider:
    def __init__(self, model_info=DEFAULT_MODEL_INFO, max_tokens=1024):
        self.info = load_model_info(model_info)
        if max_tokens <= 0:
            raise ValueError('max_tokens must be positive')
        self.max_tokens = max_tokens
        self._loaded = None
        self._lock = Lock()

    def metadata(self):
        return {'model': self.info['model'], 'revision': self.info['revision'],
                'template': self.info.get('template'), 'temperature': 0, 'max_tokens': self.max_tokens, 'backend': 'mlx'}

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
