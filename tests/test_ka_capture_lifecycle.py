from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from playwright.sync_api import Error, TimeoutError
from tools import ka_ws_capture_probe as probe

class KACaptureLifecycleTests(unittest.TestCase):
    def capture(self, *, navigation_error=None, wait_error=None, socket_payload=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        output = Path(directory.name)/'nested'/'capture.json'
        page = MagicMock()
        callbacks = {}
        page.on.side_effect = lambda event, callback: callbacks.update({event: callback})
        request = MagicMock(method='POST',url='https://rmpdemo.kaga88.com/kaga/rmp/startGame',resource_type='xhr',headers={'ctx':'demo-context'},post_data='{"gn":"GoldenBull"}')
        def navigate(*args, **kwargs):
            callbacks['request'](request)
            if socket_payload is not None:
                socket = MagicMock(url='wss://pml.example/kaga/fish/demo')
                frames = {}
                socket.on.side_effect = lambda event, callback: frames.update({event:callback})
                callbacks['websocket'](socket)
                frames['framesent'](socket_payload)
            if navigation_error: raise navigation_error
        page.goto.side_effect = navigate
        page.wait_for_timeout.side_effect = wait_error
        page.is_closed.return_value = bool(wait_error)
        browser = MagicMock()
        context = browser.new_context.return_value
        context.new_page.return_value = page
        engine = MagicMock()
        engine.chromium.launch.return_value = browser
        with patch.object(probe,'sync_playwright') as factory, patch('sys.argv',['capture','GoldenBull','--wait','1','--output',str(output)]):
            factory.return_value.__enter__.return_value = engine
            try:
                code = probe.main()
            except Error:
                code = None
        self.assertTrue(output.is_file(), 'observed traffic must survive interrupted capture')
        payload = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(payload['requests'][0]['post_data'],'{"gn":"GoldenBull"}')
        return code, payload

    def test_window_close_preserves_observed_session(self):
        code, data = self.capture(wait_error=Error('Target page, context or browser has been closed'))
        self.assertEqual(code,0)
        self.assertEqual(data['stop_reason'],'browser_closed')

    def test_navigation_timeout_preserves_observed_session(self):
        code, data = self.capture(navigation_error=TimeoutError('navigation timeout'))
        self.assertEqual(code,1)
        self.assertIn('navigation timeout',data['error'])

    def test_full_socket_payload_survives_window_close(self):
        _, data = self.capture(wait_error=Error('Target closed'),socket_payload='x'*3000)
        self.assertEqual(data['events'][1]['payload'],'x'*3000)
