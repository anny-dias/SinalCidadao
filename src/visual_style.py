"""Estilo puramente visual do SUMO-GUI; não modifica física ou temporização."""

VEHICLE_COLORS = {
    'north_flow': (56, 189, 248, 255),
    'south_flow': (34, 211, 153, 255),
    'east_flow': (251, 146, 60, 255),
    'west_flow': (167, 139, 250, 255),
}
PEDESTRIAN_COLOR = (250, 204, 21, 255)


def vehicle_color(identifier):
    return next((color for prefix, color in VEHICLE_COLORS.items()
                 if identifier.startswith(prefix)), (226, 232, 240, 255))


def apply_visual_colors(traci, vehicle_ids, person_ids, painted_vehicles, painted_people):
    """Aplica cor uma vez por objeto somente quando GUI está aberta."""
    for vehicle in vehicle_ids:
        if vehicle not in painted_vehicles:
            traci.vehicle.setColor(vehicle, vehicle_color(vehicle))
            painted_vehicles.add(vehicle)
    for person in person_ids:
        if person not in painted_people:
            traci.person.setColor(person, PEDESTRIAN_COLOR)
            painted_people.add(person)
