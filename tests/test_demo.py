"""Exercise the actual fixture HTTP API without a browser or model."""
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request


class DemoTests(unittest.TestCase):
    def test_fixture_roundtrip_and_write_protection(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        process=subprocess.Popen([sys.executable,'-m','writing_ftm.demo','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        base=f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                try:
                    with urllib.request.urlopen(base,timeout=1) as response: page=response.read().decode()
                    break
                except urllib.error.URLError:time.sleep(.02)
            else:self.fail('Demo server did not start')
            token=re.search(r"X-Demo-Token':'([^']+)'",page)[1]
            def post(path,payload,auth=token):
                req=urllib.request.Request(base+path,json.dumps(payload).encode(),{'Content-Type':'application/json','X-Demo-Token':auth})
                with urllib.request.urlopen(req,timeout=2) as response:return json.load(response)
            request=json.loads(Path('examples/critique-request.json').read_text())
            payload={'passage':request['passage'],'source':request['sources']['demo']}
            with self.assertRaises(urllib.error.HTTPError) as caught:post('/assess',payload,'wrong')
            self.assertEqual(caught.exception.code,403)
            event=post('/assess',payload)
            self.assertEqual(event['provider']['backend'],'fixture')
            result=post('/present',{'warmth':'warm','directness':'action-first'})
            self.assertEqual(result['verdict'],'revise')
            self.assertTrue(post('/rate',{'rating':'this works'})['saved'])
            with self.assertRaises(urllib.error.HTTPError):post('/assess',{**payload,'passage':'Changed'})
        finally:
            process.terminate();process.wait(timeout=5)
            process.stderr.close()
