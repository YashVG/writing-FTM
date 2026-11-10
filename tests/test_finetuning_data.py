import hashlib
import json
from pathlib import Path
import unittest


class FineTuningDataTests(unittest.TestCase):
    def test_payloads_match_source_and_preserve_split(self):
        root=Path('data/finetuning-pilot-v1')
        manifest=json.loads((root/'manifest.json').read_text())
        provenance=json.loads((root/'provenance.json').read_text())
        groups=[]
        for split,count in [('train',20),('valid',8)]:
            original={r['id']:r for r in map(json.loads,Path(f'data/writing-v1/neutral/{split}.jsonl').read_text().splitlines())}
            payloads=list(map(json.loads,(root/f'{split}.jsonl').read_text().splitlines()))
            self.assertEqual(len(payloads),count)
            self.assertEqual(len({r['case_id'] for r in provenance[split]}),count)
            for row,ref in zip(payloads,provenance[split]):
                self.assertEqual(row['messages'],original[ref['id']]['messages'])
                self.assertTrue(ref['id'].endswith('-neutral-absent'))
                self.assertEqual(set(row),{'messages'})
            groups.append({r['source_group'] for r in provenance[split]})
            self.assertLessEqual(manifest['max_sequence_tokens'][split],512)
        self.assertFalse(groups[0] & groups[1])
        for file,digest in manifest['output_sha256'].items():
            self.assertEqual(hashlib.sha256((root/file).read_bytes()).hexdigest(),digest)
