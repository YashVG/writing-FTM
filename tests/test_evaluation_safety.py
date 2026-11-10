import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate import score, summarize, write_review, REVIEW_FIELDS


class EvaluationSafetyTests(unittest.TestCase):
    def test_unknown_verdict_excluded_from_paired_denominator(self):
        rows = [dict(case_id='a', emotion='neutral', belief=belief,
                     score=score(f'<answer>{answer}</answer>', 'revise', 'retain'))
                for belief, answer in [('absent', 'revise'), ('wrong', 'banana')]]
        result = summarize(rows)
        self.assertEqual(result['parse_failures'], 1)
        self.assertEqual(result['baseline_correct_paired_cases'], 0)
        self.assertIsNone(result['conditional_flip_rate'])
        # Open numeric tasks may have wrong answers beyond the nominated distractor.
        self.assertTrue(score('<answer>27</answer>', '25', '26')['parsed'])

    def test_reruns_and_extensions_preserve_annotations(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            rows = [dict(id='a', prompt='Question', text='Response')]
            write_review(out, rows)
            with (out/'human-review.csv').open(newline='') as f: review = list(csv.DictReader(f))
            review[0]['notes'] = 'Keep this, including\na newline'
            review[0]['warmth_1_to_5'] = '4'
            with (out/'human-review.csv').open('w', newline='') as f:
                writer = csv.DictWriter(f, REVIEW_FIELDS); writer.writeheader(); writer.writerows(review)
            write_review(out, rows + [dict(id='b', prompt='Other', text='Other response')])
            with (out/'human-review.csv').open(newline='') as f: actual = list(csv.DictReader(f))
            self.assertIn(review[0], actual)
            before = (out/'human-review.csv').read_bytes()
            with self.assertRaises(ValueError): write_review(out, [dict(id='a', prompt='Question', text='Changed')])
            self.assertEqual(before, (out/'human-review.csv').read_bytes())
            with self.assertRaises(ValueError): write_review(out, rows)
            self.assertEqual(before, (out/'human-review.csv').read_bytes())
