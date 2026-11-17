import tempfile
import unittest
from pathlib import Path
from src.metrics import parse_tripinfo


class MetricsTests(unittest.TestCase):
    def test_completed_trips(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'tripinfo.xml'
            path.write_text('<tripinfos><tripinfo id="a" duration="20" waitingTime="5" />'
                            '<tripinfo id="b" duration="30" waitingTime="15" />'
                            '<personinfo id="p" duration="40" /></tripinfos>')
            results = parse_tripinfo(path)
            self.assertEqual(results['average_vehicle_duration_seconds'], 25)
            self.assertEqual(results['average_vehicle_waiting_seconds'], 10)
            self.assertEqual(results['completed_person_trips'], 1)

    def test_missing_file(self):
        self.assertIsNone(parse_tripinfo('missing.xml')['average_vehicle_duration_seconds'])
