import json
import unittest
from pathlib import Path
from writing_ftm.engine import parse_critique
from writing_ftm.presentation import present
from writing_ftm.retrieval import retrieve


class PresentationTests(unittest.TestCase):
    def test_repeated_tone_changes_preserve_content(self):
        request=json.loads(Path('examples/critique-request.json').read_text())
        record=parse_critique(Path('examples/critique-response.json').read_text(),**request)
        for _ in range(6):
            for warmth in ('neutral','warm'):
                for order in ('explanation-first','action-first'):
                    result=present(record,warmth,order)
                    self.assertEqual(result['verdict'],record.verdict)
                    self.assertEqual(result['rationale'],record.rationale)
                    for section,issue in zip(result['sections'],record.issues):
                        self.assertIn(issue.diagnosis,section['text'])
                        self.assertIn(issue.recommendation,section['text'])
                        self.assertEqual(section['severity'],issue.severity)
                        self.assertEqual(section['uncertainty'],issue.uncertainty)

    def test_retrieval_returns_provenance_and_excludes_zero_match(self):
        sources={'sleep':'Sleep and concentration survey.', 'food':'Apples and oranges.'}
        hits=retrieve('Sleep predicts concentration',sources,1)
        self.assertEqual(hits[0]['source_id'],'sleep')
        self.assertEqual(hits[0]['text'],sources['sleep'])
        self.assertEqual(retrieve('zzzz',sources),[])
        with self.assertRaises(ValueError):retrieve('sleep',sources,0)
