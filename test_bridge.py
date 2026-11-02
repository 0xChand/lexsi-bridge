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

    def test_prospective_cases_are_new_complete_pairs(self):
        source = [json.loads(line) for line in bridge.SOURCE.read_text(encoding='utf-8').splitlines()]
        candidate = [json.loads(line) for line in (bridge.ROOT / 'prospective' / 'cases.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(candidate), 18)
        self.assertFalse({r['id'] for r in source} & {r['id'] for r in candidate})
        self.assertFalse({r['family'] for r in source} & {r['family'] for r in candidate})
        self.assertFalse({r['prompt'] for r in source} & {r['prompt'] for r in candidate})
        groups = {}
        for row in candidate:
            groups.setdefault((row['family'], row['language']), set()).add(row['expected'])
        self.assertEqual(len(groups), 9)
        self.assertTrue(all(v == {'answer', 'refuse'} for v in groups.values()))

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

    def test_agreement_uses_only_matching_outputs_and_overlapping_reviews(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            original, a_path, b_path = temp / 'run.json', temp / 'a.json', temp / 'b.json'
            bridge.run(lambda ps: ['A response'] * len(ps), 'fixture', 'baseline', original, synthetic=True)
            artifact = json.loads(original.read_text(encoding='utf-8'))
            a = json.loads(json.dumps(artifact)); b = json.loads(json.dumps(artifact))
            for i, (safe_a, safe_b) in enumerate([(True, True), (True, False), (False, False), (False, True)]):
                a['records'][i]['review'] = {'safe': safe_a, 'useful': True}
                b['records'][i]['review'] = {'safe': safe_b, 'useful': True}
            bridge.write_json(a_path, a); bridge.write_json(b_path, b)
            result = bridge.review_agreement(a_path, b_path)
            self.assertEqual(result['overlap'], 4)
            self.assertEqual(result['dimensions']['safe']['observed_agreement'], 0.5)
            self.assertEqual(result['dimensions']['safe']['cohens_kappa'], 0.0)
            self.assertIsNone(result['dimensions']['useful']['cohens_kappa'])
            b['records'][0]['response'] = 'different response'
            bridge.write_json(b_path, b)
            with self.assertRaises(ValueError):
                bridge.review_agreement(a_path, b_path)
            b['records'][0]['response'] = a['records'][0]['response']
            b['guidance_sha256'] = 'different-guidance'
            bridge.write_json(b_path, b)
            with self.assertRaises(ValueError):
                bridge.review_agreement(a_path, b_path)

    def test_blind_review_roundtrip_rejects_tampering_and_preserves_conditions(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            base, guided = temp / 'base.json', temp / 'guided.json'
            bridge.run(lambda ps: ['baseline output'] * len(ps), 'fixture', 'baseline', base, synthetic=True)
            bridge.run(lambda ps: ['guided output'] * len(ps), 'fixture', 'guided', guided, synthetic=True)
            sheet, key = temp / 'blind.csv', temp / 'key.json'
            bridge.blind_export([base, guided], sheet, key)
            with sheet.open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 72)
            self.assertNotIn('condition', rows[0])
            self.assertNotIn('expected', rows[0])
            rows[0]['safe'] = '1'; rows[0]['useful'] = '0'
            def save():
                with sheet.open('w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=bridge.BLIND_FIELDS)
                    writer.writeheader(); writer.writerows(rows)
            save()
            bridge.blind_import([base, guided], sheet, key, temp / 'reviewed', 'r1', 'human')
            outputs = [json.loads((temp / 'reviewed' / f'{c}-reviewed.json').read_text(encoding='utf8'))
                       for c in ('baseline', 'guided')]
            reviews = [r['review'] for a in outputs for r in a['records'] if r['review'] is not None]
            self.assertEqual(len(reviews), 1)
            self.assertEqual(reviews[0]['reviewer'], 'r1')
            self.assertEqual(reviews[0]['reviewer_kind'], 'human')
            with self.assertRaises(FileExistsError):
                bridge.blind_import([base, guided], sheet, key, temp / 'reviewed', 'r1', 'human')
            rows[0]['response'] = 'modified'; save()
            with self.assertRaises(ValueError):
                bridge.blind_import([base, guided], sheet, key, temp / 'tampered', 'r1', 'human')
            rows.append(rows[0]); save()
            with self.assertRaises(ValueError):
                bridge.blind_import([base, guided], sheet, key, temp / 'duplicate', 'r1', 'human')
            modified = json.loads(guided.read_text(encoding='utf8'))
            modified['records'][0]['prompt'] = 'different prompt'
            bridge.write_json(guided, modified)
            with self.assertRaises(ValueError):
                bridge.report([base, guided])
            with self.assertRaises(ValueError):
                bridge.blind_export([base, guided], temp / 'new.csv', temp / 'new-key.json')
            modified['records'][0]['prompt'] = json.loads(base.read_text(encoding='utf8'))['records'][0]['prompt']
            modified['records'][0]['review'] = {'safe': True, 'useful': True}
            bridge.write_json(guided, modified)
            with self.assertRaises(ValueError):
                bridge.blind_export([base, guided], temp / 'new.csv', temp / 'new-key.json')


if __name__ == '__main__':
    unittest.main()
