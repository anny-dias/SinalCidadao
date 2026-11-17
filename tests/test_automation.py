import json
import logging
import tempfile
import unittest
from pathlib import Path
from src.automation import decide, process_batch, validate


class AutomationTests(unittest.TestCase):
    def event(self):
        return {'event_id': 'a', 'timestamp': '2026-11-17T12:00:00Z', 'camera_online': True,
                'approaches': [{'id': 'N', 'queue_vehicles': 7, 'wait_seconds': 15, 'pedestrians_crossing': 0},
                               {'id': 'S', 'queue_vehicles': 1, 'wait_seconds': 95, 'pedestrians_crossing': 0}]}

    def test_decision_anti_starvation(self):
        self.assertEqual(decide(validate(self.event()))[1], 'S')

    def test_pedestrian_priority(self):
        e = self.event()
        e['approaches'][0]['pedestrians_crossing'] = 1
        self.assertEqual(decide(validate(e))[0], 'HOLD_PEDESTRIAN_PHASE')

    def test_camera_failure(self):
        e = self.event()
        e['camera_online'] = False
        self.assertEqual(decide(validate(e))[0], 'FIXED_TIME_FALLBACK')

    def test_invalid_data(self):
        e = self.event()
        e['approaches'][0]['queue_vehicles'] = -1
        with self.assertRaises(ValueError):
            validate(e)

    def test_batch_duplicate_and_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            good = self.event()
            bad = self.event().copy()
            bad['event_id'] = 'bad'
            bad['approaches'] = []
            (path / 'input.json').write_text(json.dumps([good, good, bad]), encoding='utf-8')
            result = process_batch(path/'input.json', path/'db.sqlite', path/'log.jsonl')
            self.assertEqual(result, {'processed': 1, 'duplicates': 1, 'failed': 1})
            self.assertIn('SKIPPED_DUPLICATE', (path/'log.jsonl').read_text())
            self.assertFalse(logging.getLogger('citizenflow').handlers)

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            with self.assertRaises(FileNotFoundError):
                process_batch(path/'missing.json', path/'db.sqlite', path/'log.jsonl')
            self.assertFalse(logging.getLogger('citizenflow').handlers)


if __name__ == '__main__':
    unittest.main()
