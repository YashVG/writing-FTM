from huggingface_hub import snapshot_download
from pathlib import Path
import json
model = 'mlx-community/Qwen3-4B-Instruct-2507-4bit'
revision = '50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b'
Path('runs/pilot').mkdir(parents=True, exist_ok=True)
path = snapshot_download(model, revision=revision)
Path('runs/pilot/model.json').write_text(json.dumps({'model': model, 'revision': revision, 'path': path}, indent=2))
print(path, flush=True)
