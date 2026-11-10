"""Create a model view with the official pinned Instruct template; never edit HF cache."""
import hashlib
import json
from pathlib import Path
import urllib.request
import yaml

REVISION='cdbee75f17c01a7cc42f958dc650907174af0554'
URL=f'https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/{REVISION}/tokenizer_config.json'
root=Path('runs/finetuning/template-repair')
if root.exists(): raise SystemExit('Repair run exists; refusing overwrite')
root.mkdir(parents=True)
info=json.loads(Path('runs/pilot/model.json').read_text())
source=Path(info['path'])
with urllib.request.urlopen(URL) as response: official=json.load(response)
template=official['chat_template']
folder=Path('configs/chat_templates');folder.mkdir(parents=True,exist_ok=True)
target=folder/'qwen3-instruct-2507.jinja'
if target.exists() and target.read_text()!=template: raise ValueError('Stored template differs')
target.write_text(template)
provenance={'url':URL,'upstream_revision':REVISION,'sha256':hashlib.sha256(template.encode()).hexdigest(),
            'model_revision':info['revision'],'reason':'Remove thinking-model template from Instruct SFT; use official Instruct template'}
(folder/'qwen3-instruct-2507.json').write_text(json.dumps(provenance,indent=2)+'\n')
view=root/'model';view.mkdir()
for path in source.iterdir():
 if path.name not in ('tokenizer_config.json','chat_template.jinja'):
  (view/path.name).symlink_to(path.resolve(),target_is_directory=path.is_dir())
config=json.loads((source/'tokenizer_config.json').read_text());config['chat_template']=template
(view/'tokenizer_config.json').write_text(json.dumps(config,indent=2))
(view/'chat_template.jinja').write_text(template)
(root/'model.json').write_text(json.dumps({**info,'path':str(view.resolve()),'template':provenance},indent=2))
training=yaml.safe_load(Path('runs/finetuning/pilot-v1/config.yaml').read_text())
training.update(model=str(view.resolve()),adapter_path=str(root/'adapters'))
(root/'config.yaml').write_text(yaml.safe_dump(training))
print(json.dumps(provenance,indent=2))
