"""Prepare a pinned, idempotent local runtime; historical pilot metadata stays separate."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.model_template import model_view, TEMPLATE
from writing_ftm.runtime import DEFAULT_MODEL_INFO, MODEL, REVISION, load_model_info


def prepare_runtime(info, root=Path('runs/runtime')):
    template = TEMPLATE.read_text()
    digest = hashlib.sha256(template.encode()).hexdigest()
    destination = root / f'model-{info["revision"][:12]}-{digest[:12]}'
    metadata_path = root / 'model.json'
    if destination.exists():
        provenance = json.loads(TEMPLATE.with_suffix('.json').read_text())
        result = {**info, 'path': str(destination.resolve()), 'template': provenance}
    else:
        result = model_view(info, destination)
    temporary = metadata_path.with_suffix('.json.tmp')
    try:
        temporary.write_text(json.dumps(result, indent=2) + '\n')
        load_model_info(temporary)
        temporary.replace(metadata_path)
    finally:
        temporary.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Use only an already cached pinned snapshot')
    args = parser.parse_args()
    from huggingface_hub import snapshot_download
    path = snapshot_download(MODEL, revision=REVISION, local_files_only=args.offline)
    info = {'model': MODEL, 'revision': REVISION, 'path': path}
    pilot = Path('runs/pilot/model.json')
    pilot.parent.mkdir(parents=True, exist_ok=True)
    # Compatibility for research scripts that explicitly request the original snapshot.
    if not pilot.exists():
        pilot.write_text(json.dumps(info, indent=2) + '\n')
    prepare_runtime(info)
    print(f'Ready: {DEFAULT_MODEL_INFO} (pinned base model + audited Instruct template; no adapter)')


if __name__ == '__main__':
    main()
