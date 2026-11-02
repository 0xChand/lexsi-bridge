import json
import csv
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import bridge


class ChatHandler(BaseHTTPRequestHandler):
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.seen.append((self.path, body))
        data = json.dumps({'choices': [{'message': {'content': 'I cannot help with that.'}}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge.curate()

    def test_curated_pairs_and_languages_survive(self):
        rows = bridge.load_rows()
        grouped = {}
        for row in rows:
            grouped.setdefault((row['family'], row['language']), set()).add(row['expected'])
        self.assertEqual(len(grouped), 18)
        self.assertTrue(all(labels == {'answer', 'refuse'} for labels in grouped.values()))

    def test_real_http_adapter_and_auditkit(self):
        ChatHandler.seen = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), ChatHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / 'result.json'
                bridge.run(bridge.endpoint(f'http://127.0.0.1:{server.server_port}/v1', 'fixture', 'guided'),
                           'fixture', 'guided', output)
                artifact = json.loads(output.read_text(encoding='utf-8'))
                self.assertEqual(len(artifact['records']), 36)
                self.assertEqual(len(ChatHandler.seen), 36)
                self.assertEqual(ChatHandler.seen[0][0], '/v1/chat/completions')
                self.assertEqual(ChatHandler.seen[0][1]['messages'][0]['content'], bridge.GUIDANCE)
                self.assertFalse(artifact['synthetic'])
                self.assertIsNone(artifact['records'][0]['review'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_heuristic_is_language_specific(self):
        self.assertTrue(bridge.refusal('I cannot help.', 'en'))
        self.assertFalse(bridge.refusal('I cannot help.', 'ur'))
        self.assertTrue(bridge.refusal('No puedo ayudar.', 'es'))

    def test_review_roundtrip_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            original, sheet, reviewed = temp / 'run.json', temp / 'review.csv', temp / 'reviewed.json'
            bridge.run(lambda ps: ['A response'] * len(ps), 'fixture', 'baseline', original, synthetic=True)
            bridge.export_review(original, sheet)
            with sheet.open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            rows[0]['safe'], rows[0]['useful'] = '1', '0'
            with sheet.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            bridge.import_review(original, sheet, reviewed)
            result = json.loads(reviewed.read_text(encoding='utf-8'))
            self.assertTrue(result['records'][0]['review']['safe'])
            self.assertIsNone(result['records'][1]['review'])
            rows[0]['response'] = 'tampered'
            with sheet.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValueError):
                bridge.import_review(original, sheet, reviewed)


if __name__ == '__main__':
    unittest.main()
