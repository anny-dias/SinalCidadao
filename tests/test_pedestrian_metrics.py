import unittest

from src.pedestrian_metrics import PedestrianTracker


class TestPedestrianMetrics(unittest.TestCase):
    def test_wait_and_crossing_measured_separately(self):
        tracker = PedestrianTracker()
        tracker.update(1, [('p_simulada', 'north_in', 3)])
        pending = tracker.update(3, [('p_simulada', 'north_in', 5)])
        self.assertEqual(pending['waiting_count'], 1)
        self.assertEqual(pending['max_current_wait_seconds'], 5)
        tracker.update(4, [('p_simulada', ':center_c0', 0)])
        result = tracker.update(11, [('p_simulada', 'east_out', 0)])
        self.assertEqual(result['completed_crossings'], 1)
        self.assertEqual(tracker.summary()['average_pre_crossing_wait_seconds'], 5)
        self.assertEqual(tracker.summary()['average_crossing_seconds'], 7)

    def test_disappearance_on_crossing_counts_completion(self):
        tracker = PedestrianTracker()
        tracker.update(1, [('p2', ':center_c1', 0)])
        tracker.update(5, [])
        self.assertEqual(tracker.summary()['observed_pedestrian_crossing_completions'], 1)

    def test_no_identifiers_in_aggregate_result(self):
        tracker = PedestrianTracker()
        state = tracker.update(2, [('simulated_123', 'west_in', 20)])
        self.assertNotIn('simulated_123', str(state) + str(tracker.summary()))

    def test_request_persists_until_crossing_even_if_wait_resets(self):
        tracker = PedestrianTracker()
        tracker.update(1, [('p3', 'north_in', 2)])
        state = tracker.update(6, [('p3', 'north_in', 0)])
        self.assertEqual(state['pending_request_count'], 1)
        self.assertGreaterEqual(state['oldest_pending_request_seconds'], 5)
        state = tracker.update(7, [('p3', ':center_c0', 0)])
        self.assertEqual(state['pending_request_count'], 0)

    def test_alert_trigger_does_not_depend_on_sampling_modulo(self):
        tracker = PedestrianTracker()
        tracker.update(1, [('p4', 'south_in', 1)])
        state = tracker.update(16, [('p4', 'south_in', 1)])
        self.assertEqual(state['new_wait_alerts'], 1)
        state = tracker.update(17, [('p4', 'south_in', 1)])
        self.assertEqual(state['new_wait_alerts'], 0)

    def test_pending_crossing_target_tracks_next_edge(self):
        tracker = PedestrianTracker()
        tracker.update(3, [('simulated', 'north_in', 3, ':center_w0')])
        state = tracker.update(5, [('simulated', ':center_w0', 0, ':center_c0')])
        self.assertEqual(state['pending_crossings'], {':center_c0': 1})
        state = tracker.update(6, [('simulated', ':center_c0', 0, ':center_w1')])
        self.assertEqual(state['pending_crossings'], {})


if __name__ == '__main__':
    unittest.main()
