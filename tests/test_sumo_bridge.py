import unittest
from types import SimpleNamespace
from src.sumo_bridge import current_green_lanes, green_duration, make_event, occupied_authorized_crossings


class FakeTraci:
    edge = SimpleNamespace(getLastStepHaltingNumber=lambda edge: 8 if edge == 'north_in' else 1,
                           getWaitingTime=lambda edge: 30 if edge == 'north_in' else 10)
    lane = SimpleNamespace(getLastStepHaltingNumber=lambda lane: 8 if lane == 'north_in_1' else 1)
    trafficlight = SimpleNamespace(getRedYellowGreenState=lambda tls: 'Gr',
                                   getControlledLinks=lambda tls: ((('north_in_1', ':center_0_0', 'south_out_1'),),
                                                                    (('east_in_1', ':center_1_0', 'west_out_1'),)))


class TestSumoBridge(unittest.TestCase):
    def test_reads_edge_not_pedestrian_lane_zero(self):
        event = make_event(FakeTraci, step=5)
        self.assertEqual(event['approaches'][0]['queue_vehicles'], 8)

    def test_green_vehicle_lane_one(self):
        self.assertEqual(current_green_lanes(FakeTraci, 'center'), {'north_in_1'})
        self.assertEqual(green_duration(FakeTraci, 'center', 'Norte'), 26)
        self.assertEqual(green_duration(FakeTraci, 'center', 'Leste'), 10)

    def test_crossing_only_authorized_if_green(self):
        fake = SimpleNamespace(
            person=SimpleNamespace(getIDList=lambda: ['p1'],
                                   getRoadID=lambda _: ':center_c1'),
            trafficlight=SimpleNamespace(
                getRedYellowGreenState=lambda _: 'rG',
                getControlledLinks=lambda _: ((('north_in_1','south_out_1',''),),
                                               ((':center_w2_0', ':center_c1_0', ''),))
            )
        )
        self.assertEqual(occupied_authorized_crossings(fake, 'center'), {':center_c1'})
        fake.trafficlight.getRedYellowGreenState = lambda _: 'Gr'
        self.assertEqual(occupied_authorized_crossings(fake, 'center'), set())


if __name__ == '__main__':
    unittest.main()
