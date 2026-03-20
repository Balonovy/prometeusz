import json
import subprocess
import sys


def test_cli_status():
    result = subprocess.run([sys.executable, 'cli/prometeusz.py', 'status'], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert 'agent' in payload


def test_cli_verify():
    result = subprocess.run([sys.executable, 'cli/prometeusz.py', 'verify'], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert 'proof_valid' in payload
