import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.benchmark_rag import score_retrieval
from writing_ftm.__main__ import main

HAS_RAG = all(importlib.util.find_spec(name) for name in ('langchain_core', 'langchain_text_splitters'))


class DefaultRetrievalTests(unittest.TestCase):
    def test_default_lexical_and_missing_semantic_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / 'event.json'
            # -S hides all third-party packages, including in the optional environment.
            cmd = [sys.executable, '-S', '-m', 'writing_ftm', '--input', 'examples/critique-request.json',
                   '--fixture-response', 'examples/critique-response.json', '--output', str(event),
                   '--retrieve-k', '1']
            ok = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads(event.read_text())['retrieval'][0]['source_id'], 'demo')
            event.unlink()
            failed = subprocess.run(cmd + ['--retriever', 'semantic'], capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('docs/semantic-rag.md', failed.stderr)
            self.assertFalse(event.exists())

    def test_partial_recall_and_unanswerable_denominator(self):
        cases = [{'id': 'two', 'gold': ['a', 'b']}, {'id': 'none', 'gold': []}]
        rankings = {'two': [{'source_id': 'a'}, {'source_id': 'c'}], 'none': []}
        self.assertEqual(score_retrieval(cases, rankings, 2),
                         {'mean_recall': 0.5, 'all_gold_retrieved': 0, 'answerable_cases': 1})


class FixtureEmbeddings:
    """Make any chunk containing 'signal' win, so scores are independent of ML weights."""
    def embed_documents(self, texts):
        return [[1., 0.] if 'signal' in text else [0., 1.] for text in texts]

    def embed_query(self, text):
        return self.embed_documents([text])[0]

    def metadata(self):
        return {'model': 'test fixture'}


@unittest.skipUnless(HAS_RAG, 'requires optional LangChain packages')
class AttributionTests(unittest.TestCase):
    def test_chunk_offsets_ties_and_unique_parent_ids(self):
        from writing_ftm.semantic_retrieval import SemanticIndex
        text = 'Café.\n\nsignal one\n\nsignal two.\n\nLast line.'
        sources = {'b': text, 'a': text, 'c': 'Noise.'}
        index = SemanticIndex(sources, FixtureEmbeddings(), chunk_size=16, chunk_overlap=3)
        hits = index.retrieve('signal', k=3, min_score=0.8)
        self.assertEqual([hit['source_id'] for hit in hits], ['a', 'b'])
        for hit in hits:
            self.assertEqual(hit['text'], text)
            chunk = hit['matched_chunk']
            self.assertGreater(chunk['start'], 0)
            self.assertEqual(text[chunk['start']:chunk['end']], chunk['text'])
        with self.assertRaisesRegex(ValueError, 'context limit'):
            index.retrieve('signal', max_context_chars=4)

    def test_cli_validates_against_selected_original_text(self):
        from writing_ftm import semantic_retrieval
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = 'Café — signal.\n\nThe gauge rose by one metre.'
            request = {'passage': 'Water rose.', 'sources': {'log': parent, 'other': 'Water was warm.'}}
            (root / 'request').write_text(json.dumps(request))
            args = ['writing_ftm', '--retriever', 'semantic', '--retrieve-k', '1', '--retrieval-query', 'signal',
                    '--chunk-size', '16', '--chunk-overlap', '2', '--input', str(root / 'request'),
                    '--output', str(root / 'event')]
            prompts = []

            class Provider:
                def generate(self, messages):
                    prompts.append(json.loads(messages[-1]['content']))
                    return json.dumps(response)

                def metadata(self):
                    return {'backend': 'test'}

            response = {'schema_version': 1, 'verdict': 'retain', 'rationale': 'The gauge rose.',
                        'evidence': [{'source_id': 'log', 'quote': 'The gauge rose by one metre.'}], 'issues': []}
            with (patch.object(semantic_retrieval, 'LocalEmbeddings', return_value=FixtureEmbeddings()),
                  patch('writing_ftm.__main__.MLXProvider', return_value=Provider()), patch.object(sys, 'argv', args)):
                main()
                self.assertEqual(prompts, [{'passage': request['passage'], 'sources': {'log': parent}}])
                result = json.loads((root / 'event').read_text())
                ev = result['critique']['evidence'][0]
                self.assertEqual(parent[ev['start']:ev['end']], ev['quote'])
                self.assertNotIn(ev['quote'], result['retrieval'][0]['matched_chunk']['text'])
                (root / 'event').unlink()
                # Both quotes exist in the corpus, but neither belongs to the
                # selected source under the supplied ID.
                for citation in [{'source_id': 'other', 'quote': 'Water was warm.'},
                                 {'source_id': 'log', 'quote': 'Water was warm.'}]:
                    response['evidence'] = [citation]
                    with self.subTest(citation=citation), self.assertRaises(SystemExit):
                        main()
                    self.assertFalse((root / 'event').exists())
