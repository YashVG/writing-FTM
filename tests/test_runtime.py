import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.download_model import prepare_runtime
from writing_ftm.runtime import MODEL, REVISION, SetupError, load_model_info


class RuntimeTests(unittest.TestCase):
    def fixture(self, root):
        source = root / 'weights'
        source.mkdir()
        (source / 'tokenizer_config.json').write_text(json.dumps({'chat_template': 'original'}))
        (source / 'model.safetensors').write_bytes(b'fixture weights; never loaded')
        return {'model': MODEL, 'revision': REVISION, 'path': str(source)}

    def test_setup_is_idempotent_and_preserves_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            first = prepare_runtime(source, root / 'runtime')
            second = prepare_runtime(source, root / 'runtime')
            self.assertEqual(first, second)
            self.assertEqual(load_model_info(root / 'runtime/model.json'), first)
            original = json.loads((Path(source['path']) / 'tokenizer_config.json').read_text())
            self.assertEqual(original['chat_template'], 'original')
            self.assertEqual(len(list((root / 'runtime').glob('model-*'))), 1)

    def test_changed_template_and_missing_weights_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            info = prepare_runtime(source, root / 'runtime')
            template = Path(info['path']) / 'chat_template.jinja'
            before = template.read_text()
            template.write_text('changed')
            with self.assertRaisesRegex(SetupError, 'template changed'):
                load_model_info(root / 'runtime/model.json')
            template.write_text(before)
            (Path(source['path']) / 'model.safetensors').unlink()
            with self.assertRaisesRegex(SetupError, 'weights are missing'):
                load_model_info(root / 'runtime/model.json')

    def test_worker_missing_setup_is_actionable_without_echoing_input(self):
        with tempfile.TemporaryDirectory() as folder:
            # Import the real package with an empty working directory: no runtime metadata.
            code = 'import sys; sys.path.insert(0, sys.argv[1]); from writing_ftm.widget_feedback import main; main()'
            result = subprocess.run([sys.executable, '-c', code, str(Path.cwd())], cwd=folder,
                                    input=json.dumps({'passage': 'PRIVATE PASSAGE', 'source': 'PRIVATE SOURCE'}),
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('scripts.download_model', json.loads(result.stdout)['error'])
            self.assertNotIn('PRIVATE', result.stdout + result.stderr)
