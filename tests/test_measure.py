import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class MeasurementTests(unittest.TestCase):
    def test_isolated_output_and_no_overwrite(self):
        # psutil is a runtime dependency; dependency-free CI skips this integration check.
        try:
            import psutil
        except ImportError:
            self.skipTest('psutil not installed')
        with tempfile.TemporaryDirectory() as directory:
            command=[sys.executable,'scripts/measure.py','--output-dir',directory,'smoke','--',sys.executable,'-c','print("ok")']
            run=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            report=json.loads((Path(directory)/'smoke.json').read_text())
            self.assertEqual(report['exit_code'],0)
            before=(Path(directory)/'smoke.log').read_bytes()
            rerun=subprocess.run(command,capture_output=True,text=True)
            self.assertNotEqual(rerun.returncode,0)
            self.assertEqual(before,(Path(directory)/'smoke.log').read_bytes())
