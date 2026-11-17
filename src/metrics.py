"""Métricas por viagem efetivamente concluída; entradas não concluídas ficam explícitas."""
from pathlib import Path
from statistics import mean
from xml.etree import ElementTree as ET


def parse_tripinfo(path):
    if not Path(path).exists():
        return {'completed_vehicle_trips': 0, 'average_vehicle_duration_seconds': None,
                'average_vehicle_waiting_seconds': None, 'completed_person_trips': 0,
                'average_person_duration_seconds': None}
    root = ET.parse(path).getroot()
    vehicle_trips = root.findall('tripinfo')
    people = root.findall('personinfo')
    vehicle_durations = [float(row.attrib['duration']) for row in vehicle_trips if 'duration' in row.attrib]
    vehicle_waits = [float(row.attrib['waitingTime']) for row in vehicle_trips if 'waitingTime' in row.attrib]
    pedestrian_durations = [float(row.attrib['duration']) for row in people if 'duration' in row.attrib]
    return {'completed_vehicle_trips': len(vehicle_trips),
            'average_vehicle_duration_seconds': round(mean(vehicle_durations), 2) if vehicle_durations else None,
            'average_vehicle_waiting_seconds': round(mean(vehicle_waits), 2) if vehicle_waits else None,
            'completed_person_trips': len(people),
            'average_person_duration_seconds': round(mean(pedestrian_durations), 2) if pedestrian_durations else None}
