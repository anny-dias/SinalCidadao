import unittest
from types import SimpleNamespace

from src.visual_style import apply_visual_colors, vehicle_color, PEDESTRIAN_COLOR


class VisualStyleTests(unittest.TestCase):
    def test_directional_palette(self):
        self.assertNotEqual(vehicle_color('north_flow.1'), vehicle_color('east_flow.1'))

    def test_colors_applied_only_once(self):
        vehicle_calls = []
        person_calls = []
        fake = SimpleNamespace(
            vehicle=SimpleNamespace(setColor=lambda *args: vehicle_calls.append(args)),
            person=SimpleNamespace(setColor=lambda *args: person_calls.append(args)))
        veh_seen, people_seen = set(), set()
        for _ in range(2):
            apply_visual_colors(fake, ['north_flow.1'], ['person1'], veh_seen, people_seen)
        self.assertEqual(len(vehicle_calls), 1)
        self.assertEqual(person_calls, [('person1', PEDESTRIAN_COLOR)])


if __name__ == '__main__':
    unittest.main()
