"""One explicit local inference configuration; loading never downloads weights."""
import hashlib
import json
from pathlib import Path

DEFAULT_MODEL_INFO = 'runs/runtime/model.json'
MODEL = 'mlx-community/Qwen3-4B-Instruct-2507-4bit'
REVISION = '50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b'


class SetupError(ValueError):
    """Safe, actionable errors that contain no user input or model output."""


def load_model_info(path=DEFAULT_MODEL_INFO):
    try:
        info = json.loads(Path(path).read_text())
        if not all(isinstance(info.get(key), str) and info[key] for key in ('path', 'model', 'revision')):
            raise SetupError('Local model metadata is incomplete. Run the model setup again.')
        model = Path(info['path'])
        if not model.is_dir() or not any(weight.is_file() for weight in model.glob('*.safetensors')):
            raise SetupError('Local model weights are missing. Run: .venv/bin/python -m scripts.download_model')
        if not (model / 'tokenizer_config.json').is_file():
            raise SetupError('Local tokenizer is missing. Run the model setup again.')
        if 'template' in info:
            template = (model / 'chat_template.jinja').read_text()
            tokenizer = json.loads((model / 'tokenizer_config.json').read_text())
            if (hashlib.sha256(template.encode()).hexdigest() != info['template']['sha256']
                    or tokenizer.get('chat_template') != template):
                raise SetupError('Local chat template changed. Run the model setup again.')
        return info
    except SetupError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise SetupError('Local model configuration is missing or invalid. Run: .venv/bin/python -m scripts.download_model') from None
