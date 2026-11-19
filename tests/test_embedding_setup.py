import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.download_embeddings import prepare_embeddings
from writing_ftm.embedding_runtime import FILES_SHA256, load_embedding_info


class EmbeddingSetupTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.output = self.root / 'runtime' / 'embedding-model.json'
        self.snapshot = self.root / 'snapshot'
        # Preserve the exact pinned upstream module layout. Substitute small
        # known bytes for the weights and tokenizer to keep tests offline.
        modules = [
            {'idx': i, 'name': str(i), 'path': path, 'type': f'sentence_transformers.models.{kind}'}
            for i, (path, kind) in enumerate([('', 'Transformer'), ('1_Pooling', 'Pooling'),
                                               ('2_Normalize', 'Normalize')])
        ]
        digests = {}
        for name in FILES_SHA256:
            file = self.snapshot / name
            file.parent.mkdir(parents=True, exist_ok=True)
            data = json.dumps(modules, indent=2).encode() if name == 'modules.json' else name.encode()
            file.write_bytes(data)
            digests[name] = hashlib.sha256(data).hexdigest()
        self.assertEqual(digests['modules.json'], FILES_SHA256['modules.json'])
        self.enterContext(patch.dict(FILES_SHA256, digests))

    def test_pinned_normalize_layout_prepares_and_reloads(self):
        prepare_embeddings(self.snapshot, self.output)
        before = self.output.read_bytes()
        prepare_embeddings(self.snapshot, self.output)
        self.assertEqual(before, self.output.read_bytes())
        self.assertEqual(load_embedding_info(self.output)['path'], str(self.snapshot.resolve()))

    def test_corrupt_or_missing_files_cannot_replace_a_working_manifest(self):
        prepare_embeddings(self.snapshot, self.output)
        before = self.output.read_bytes()
        (self.snapshot / 'modules.json').write_text('[]')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch for modules.json'):
            prepare_embeddings(self.snapshot, self.output)
        self.assertEqual(self.output.read_bytes(), before)
        (self.snapshot / 'model.safetensors').unlink()
        with self.assertRaisesRegex(ValueError, 'unreadable embedding file model.safetensors'):
            load_embedding_info(self.output)

    def test_missing_or_wrong_revision_manifest_has_setup_command(self):
        with self.assertRaisesRegex(ValueError, 'scripts.download_embeddings'):
            load_embedding_info(self.output)
        prepare_embeddings(self.snapshot, self.output)
        info = json.loads(self.output.read_text())
        info['revision'] = 'main'
        self.output.write_text(json.dumps(info))
        with self.assertRaisesRegex(ValueError, 'scripts.download_embeddings'):
            load_embedding_info(self.output)

    @unittest.skipUnless(importlib.util.find_spec('huggingface_hub'), 'requires Hugging Face Hub')
    def test_offline_setup_with_empty_cache(self):
        result = subprocess.run([sys.executable, '-m', 'scripts.download_embeddings', '--offline'],
                                env={**os.environ, 'HF_HUB_OFFLINE': '1', 'HF_HUB_CACHE': str(self.root / 'hub')},
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('without --offline', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
