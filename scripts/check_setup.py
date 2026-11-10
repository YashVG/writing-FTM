"""Check local inference prerequisites without loading or downloading the model."""
import importlib.util
import platform
import sys
from writing_ftm.runtime import DEFAULT_MODEL_INFO, SetupError, load_model_info


def main():
    errors = []
    if sys.version_info < (3, 12):
        errors.append('Python 3.12 or newer is required.')
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        errors.append('Live inference requires Apple Silicon macOS; fixture mode works without it.')
    for module in ('mlx', 'mlx_lm', 'transformers'):
        if importlib.util.find_spec(module) is None:
            errors.append(f'Missing {module}. Run: uv pip sync --python .venv/bin/python requirements.lock')
    try:
        info = load_model_info()
        print(f'Model: {info["model"]} @ {info["revision"]}')
        print(f'Configuration: {DEFAULT_MODEL_INFO}')
        print(f'Template SHA-256: {info.get("template", {}).get("sha256", "not recorded")}')
    except SetupError as error:
        errors.append(str(error))
    for error in errors:
        print(f'FAIL: {error}')
    print('Setup needs attention.' if errors else 'PASS: Local inference setup is ready. No model was loaded.')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
