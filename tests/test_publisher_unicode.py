import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tester_spin.run_result_publisher import _git


class PublisherUnicodeTests(unittest.TestCase):
    def test_report_is_utf8_even_with_windows_legacy_default(self):
        text = '{"name":"Señal ∞ 🎰", "value":"日本語"}'
        raw = text.encode('utf-8')
        expected = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(['git','init','-q',tmp],check=True,capture_output=True)
            with patch('subprocess._text_encoding',return_value='cp1252'):
                actual = _git(Path(tmp),'hash-object','--stdin',input_text=text)
            self.assertEqual(actual.stdout.strip(),expected)
