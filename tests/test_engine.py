import copy
import json
import unittest
from pathlib import Path
from writing_ftm.engine import CritiqueEngine, ValidationError, parse_critique

REQUEST = json.loads(Path('examples/critique-request.json').read_text())
RESPONSE = json.loads(Path('examples/critique-response.json').read_text())


class Provider:
    def __init__(self, response): self.response = response; self.messages = None
    def generate(self, messages): self.messages = messages; return json.dumps(self.response)
    def metadata(self): return {'backend': 'fixture'}


class EngineTests(unittest.TestCase):
    def parse(self, obj):
        return parse_critique(json.dumps(obj), **REQUEST)

    def test_offsets_resolve_to_exact_text(self):
        record = self.parse(RESPONSE)
        issue = record.issues[0]
        self.assertEqual(REQUEST['passage'][issue.passage_start:issue.passage_end], issue.passage_quote)
        ev = issue.evidence[0]
        self.assertEqual(REQUEST['sources'][ev.source_id][ev.start:ev.end], ev.quote)

    def test_reject_bad_records(self):
        for field, value in [('severity', 'critical'), ('uncertainty', 0.9),
                             ('passage_quote', 'invented'), ('recommendation', '')]:
            obj = copy.deepcopy(RESPONSE); obj['issues'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError): self.parse(obj)
        for field, value in [('source_id', 'unknown'), ('quote', 'invented')]:
            obj = copy.deepcopy(RESPONSE); obj['evidence'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValidationError): self.parse(obj)
        for raw in ['not JSON', '[]', 'null', '{}']:
            with self.assertRaises(ValidationError): parse_critique(raw, **REQUEST)

    def test_verdict_requires_consistent_issues(self):
        obj = copy.deepcopy(RESPONSE); obj['verdict'] = 'retain'
        with self.assertRaises(ValidationError): self.parse(obj)
        obj['issues'] = []
        self.assertEqual(self.parse(obj).verdict, 'retain')
        obj['evidence'] = []
        with self.assertRaises(ValidationError): self.parse(obj)

    def test_ambiguous_quote_and_duplicate_id_rejected(self):
        with self.assertRaises(ValidationError):
            parse_critique(json.dumps(RESPONSE), REQUEST['passage'] * 2, REQUEST['sources'])
        obj = copy.deepcopy(RESPONSE); obj['issues'] *= 2
        with self.assertRaises(ValidationError): self.parse(obj)

    def test_dispute_can_correct_previous_critique(self):
        previous = self.parse(RESPONSE)
        corrected = copy.deepcopy(RESPONSE)
        corrected.update(verdict='retain', issues=[], rationale='Reassessment fixture')
        provider = Provider(corrected)
        event = CritiqueEngine(provider).assess(**REQUEST, previous=previous, dispute='Recheck the diagnosis')
        self.assertEqual(event['action'], 'reassess')
        self.assertEqual(event['critique']['verdict'], 'retain')
        self.assertEqual(event['previous']['verdict'], 'revise')
        self.assertTrue(event['human_review_required'])
        self.assertIn('Recheck the diagnosis', provider.messages[1]['content'])

    def test_missing_evidence_fails_before_generation(self):
        provider = Provider(RESPONSE)
        with self.assertRaises(ValidationError): CritiqueEngine(provider).assess('Passage', {})
        self.assertIsNone(provider.messages)
        with self.assertRaises(ValidationError): CritiqueEngine(provider).assess(**REQUEST, dispute='Incorrect')

class CLITests(unittest.TestCase):
    def test_fixture_cli_and_no_overwrite(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'event.json'
            command = [sys.executable, '-m', 'writing_ftm', '--input',
                       'examples/critique-request.json', '--fixture-response',
                       'examples/critique-response.json', '--output', str(output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            before = output.read_bytes()
            self.assertEqual(json.loads(before)['provider']['backend'], 'fixture')
            rerun = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(rerun.returncode, 0)
            self.assertEqual(before, output.read_bytes())
