"""Build an isolated view of pinned weights with an explicit chat template."""
import hashlib
import json
from pathlib import Path

TEMPLATE = Path('configs/chat_templates/qwen3-instruct-2507.jinja')


def model_view(info, destination):
    template=TEMPLATE.read_text()
    provenance=json.loads(TEMPLATE.with_suffix('.json').read_text())
    if hashlib.sha256(template.encode()).hexdigest()!=provenance['sha256']:
        raise ValueError('Template checksum mismatch')
    if info['revision']!=provenance['model_revision']:
        raise ValueError('Template correction is only audited for the pinned model')
    source=Path(info['path'])
    destination.mkdir(parents=True,exist_ok=False)
    for path in source.iterdir():
        if path.name not in ('tokenizer_config.json','chat_template.jinja'):
            (destination/path.name).symlink_to(path.resolve(),target_is_directory=path.is_dir())
    config=json.loads((source/'tokenizer_config.json').read_text())
    config['chat_template']=template
    (destination/'tokenizer_config.json').write_text(json.dumps(config,indent=2))
    (destination/'chat_template.jinja').write_text(template)
    return {**info,'path':str(destination.resolve()),'template':provenance}
