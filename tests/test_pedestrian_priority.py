import unittest

from src.pedestrian_priority import (priority_remaining_green, priority_decision,
                                     pending_red_crossings, crossing_green_map,
                                     pedestrian_service_plan)


class PriorityTests(unittest.TestCase):
    def request(self, **overrides):
        data = dict(phase_elapsed=5, remaining=30, waiting_count=2,
                    longest_wait_seconds=8, authorized_crossing_occupied=False)
        data.update(overrides)
        return priority_remaining_green(**data)

    def test_prioritizes_waiting_without_skipping_minimum_green(self):
        self.assertEqual(self.request(), 5)
        self.assertEqual(self.request(phase_elapsed=12), 1)

    def test_does_not_shorten_occupied_pedestrian_green(self):
        self.assertIsNone(self.request(authorized_crossing_occupied=True))

    def test_wait_threshold_and_no_pedestrians(self):
        self.assertIsNone(self.request(waiting_count=0))
        self.assertIsNone(self.request(longest_wait_seconds=2))

    def test_does_not_extend_or_shorten_already_short_green(self):
        self.assertIsNone(self.request(phase_elapsed=5, remaining=4))

    def test_block_reason_auditable(self):
        remaining, reason = priority_decision(
            phase_elapsed=8, remaining=2, waiting_count=1,
            longest_wait_seconds=16, authorized_crossing_occupied=False)
        self.assertIsNone(remaining)
        self.assertEqual(reason, 'VERDE_MINIMO_OU_TEMPO_INSUFICIENTE')

    def test_only_targeted_red_crossing_can_request_priority(self):
        links = ((('from_0', 'to_0', ''),),
                 ((':center_w0_0', ':center_c0_0', ''),),
                 ((':center_w1_0', ':center_c1_0', ''),))
        self.assertEqual(crossing_green_map('rGr', links),
                         {':center_c0': True, ':center_c1': False})
        self.assertEqual(pending_red_crossings(
            {':center_c0': 2, ':center_c1': 3, ':unknown': 4}, 'rGr', links),
            {':center_c1': 3})

    def test_service_plan_only_for_authorized_green_crossing(self):
        links = ((('x', 'y', ''),),
                 ((':center_w0_0', ':center_c0_0', ''),),
                 ((':center_w1_0', ':center_c1_0', ''),))
        planned, reason, targets = pedestrian_service_plan(
            10, 'rGr', links, {':center_c0': 2, ':center_c1': 1}, set())
        self.assertEqual(planned, 18)
        self.assertEqual(reason, 'RESERVA_VERDE_TRAVESSIA')
        self.assertEqual(targets, [':center_c0'])

    def test_does_not_modify_clearance_without_crossing_green(self):
        links = (((':center_w0_0', ':center_c0_0', ''),),)
        self.assertEqual(pedestrian_service_plan(
            5, 'r', links, {':center_c0': 2}, set())[0], 5)


if __name__ == '__main__':
    unittest.main()
