"""Integra SUMO/TraCI ao RPA; sem comandos em semáforos físicos."""
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .automation import process_batch
from .metrics import parse_tripinfo
from .pedestrian_metrics import PedestrianTracker
from .pedestrian_priority import crossing_green_map, pedestrian_service_plan
from .visual_style import apply_visual_colors

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {'north_in': 'Norte', 'south_in': 'Sul', 'east_in': 'Leste', 'west_in': 'Oeste'}


def find_binary(gui=False):
    name = 'sumo-gui' if gui else 'sumo'
    executable = shutil.which(name)
    if not executable:
        raise RuntimeError(f'{name} não encontrado no PATH. Instale o Eclipse SUMO.')
    return executable


def generate_network(pedestrians=False):
    netconvert = shutil.which('netconvert')
    if not netconvert:
        raise RuntimeError('netconvert não encontrado no PATH')
    net = ROOT / ('sumo/cross_pedestrians.net.xml' if pedestrians else 'sumo/cross.net.xml')
    if not net.exists():
        cmd = [netconvert, '--node-files', str(ROOT/'sumo/cross.nod.xml'),
               '--edge-files', str(ROOT/'sumo/cross.edg.xml'),
               '--output-file', str(net), '--tls.default-type', 'static']
        if pedestrians:
            cmd += ['--sidewalks.guess', 'true', '--sidewalks.guess.max-speed', '20',
                    '--crossings.guess', 'true']
        subprocess.run(cmd, check=True)
    return net


def crossing_people(traci):
    """Contagem anônima de pessoas sobre arestas de travessia, sem identificar pessoas."""
    return sum(traci.person.getRoadID(person).startswith(':') and
               '_c' in traci.person.getRoadID(person)
               for person in traci.person.getIDList())


def occupied_authorized_crossings(traci, tls):
    """Apenas travessias ocupadas COM verde no programa SUMO atual.

    A referência são os links definidos pela própria rede, nunca índices
    fixos. Não altera os estados dos sinais.
    """
    occupied_roads = {traci.person.getRoadID(p) for p in traci.person.getIDList()}
    state = traci.trafficlight.getRedYellowGreenState(tls)
    links = traci.trafficlight.getControlledLinks(tls)
    matching = set()
    for index, signal in enumerate(state):
        if signal not in ('G', 'g') or index >= len(links):
            continue
        for link in links[index]:
            if not link:
                continue
            target = link[1].rsplit('_', 1)[0] if link[1] else ''
            if '_c' in target and target in occupied_roads:
                matching.add(target)
    return matching


def make_event(traci, step, pedestrians=False):
    approaches = []
    for edge, label in ENTRIES.items():
        approaches.append({'id': label,
                           'queue_vehicles': traci.edge.getLastStepHaltingNumber(edge),
                           'wait_seconds': round(traci.edge.getWaitingTime(edge), 2),
                           'pedestrians_crossing': 0})
    if pedestrians:
        approaches.append({'id': 'Travessia', 'queue_vehicles': 0,
                           'wait_seconds': 0, 'pedestrians_crossing': crossing_people(traci)})
    return {'event_id': f'sumo-{step:05d}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'camera_online': True, 'approaches': approaches}


def current_green_lanes(traci, tls):
    state = traci.trafficlight.getRedYellowGreenState(tls)
    links = traci.trafficlight.getControlledLinks(tls)
    greens = set()
    for index, signal in enumerate(state):
        if signal in ('G', 'g') and index < len(links):
            for link in links[index]:
                if link and link[0].rsplit('_', 1)[0] in ENTRIES:
                    greens.add(link[0])
    return greens


def green_duration(traci, tls, recommended_approach=None):
    greens = current_green_lanes(traci, tls)
    if not greens:
        return None
    if recommended_approach and recommended_approach not in {
        ENTRIES[lane.rsplit('_', 1)[0]] for lane in greens
        if lane.rsplit('_', 1)[0] in ENTRIES
    }:
        return 10
    pressure = max(traci.lane.getLastStepHaltingNumber(lane) for lane in greens)
    return min(45, max(10, 10 + pressure * 2))


def run(mode, gui=False, steps=600, pedestrians=False, demand='normal', pedestrian_priority=True):
    try:
        import traci
    except ImportError as exc:
        raise RuntimeError('Biblioteca TraCI ausente. Instale: pip install traci') from exc
    generate_network(pedestrians)
    runs = ROOT/'data/runs'
    runs.mkdir(parents=True, exist_ok=True)
    # Não mistura métricas de diferentes execuções, mas IDs persistem separados.
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    prefix = runs/f'{mode}-{timestamp}'
    db_path = str(prefix) + '.db'
    logs = str(prefix) + '.jsonl'
    output = str(prefix) + '.metrics.json'
    telemetry = str(prefix) + '.telemetry.jsonl'
    tripinfo = str(prefix) + '.tripinfo.xml'
    safety_log = str(prefix) + '.safety.jsonl'
    if demand == 'high' and not pedestrians:
        raise ValueError('Demanda alta exige --pedestrians')
    config = ('cross_pedestrians_high.sumocfg' if demand == 'high' else
              'cross_pedestrians.sumocfg') if pedestrians else 'cross.sumocfg'
    cmd = [find_binary(gui), '-c', str(ROOT/'sumo'/config), '--seed', '42',
           '--no-step-log', '--duration-log.disable', '--quit-on-end',
           '--tripinfo-output', tripinfo]
    if gui:
        cmd += ['--start', '--gui-settings-file', str(ROOT/'sumo/sinal_cidadao.view.xml')]
    traci.start(cmd)
    painted_vehicles = set()
    painted_people = set()
    seen = set()
    total_wait = 0.0
    active_samples = 0
    completed = 0
    stopped = 0
    last_phase = {}
    pedestrian_priority_adjustments = 0
    priority_block_reasons = {}
    adjustments = 0
    recommended_approach = None
    pedestrian_hold_steps = 0
    extension_per_phase = {}
    pedestrians_crossing_samples = 0
    pedestrian_tracker = PedestrianTracker()
    maximum_waiting_pedestrians = 0
    pedestrian_wait_alerts = 0
    try:
        with open(telemetry, 'w', encoding='utf-8') as telemetry_file, \
             open(safety_log, 'w', encoding='utf-8') as safety_file:
            for step in range(steps):
                traci.simulationStep()
                simulation_time = traci.simulation.getTime()
                vehicle_ids = traci.vehicle.getIDList()
                if gui:
                    apply_visual_colors(traci, vehicle_ids, traci.person.getIDList(),
                                        painted_vehicles, painted_people)
                seen.update(vehicle_ids)
                stopped += sum(traci.vehicle.getSpeed(v) < .1 for v in vehicle_ids)
                arrived = traci.simulation.getArrivedIDList()
                completed += len(arrived)
                total_wait += sum(traci.vehicle.getWaitingTime(v) for v in vehicle_ids)
                active_samples += len(vehicle_ids)
                occupied = crossing_people(traci) if pedestrians else 0
                pedestrians_crossing_samples += occupied
                if pedestrians:
                    observations = [(p, traci.person.getRoadID(p),
                                     traci.person.getWaitingTime(p), traci.person.getNextEdge(p))
                                    for p in traci.person.getIDList()]
                    pedestrian_state = pedestrian_tracker.update(simulation_time, observations)
                    maximum_waiting_pedestrians = max(maximum_waiting_pedestrians,
                                                      pedestrian_state['waiting_count'])
                    # Alerta emitido na primeira passagem pelo limiar,
                    # sem depender do instante exato de uma amostragem.
                    if pedestrian_state['new_wait_alerts']:
                        pedestrian_wait_alerts += pedestrian_state['new_wait_alerts']
                        safety_file.write(json.dumps({
                            'step': step, 'event': 'PEDIDO_TRAVESSIA_PENDENTE',
                            'new_alerts': pedestrian_state['new_wait_alerts'],
                            'pending_requests': pedestrian_state['pending_request_count'],
                            'oldest_pending_seconds': round(pedestrian_state['oldest_pending_request_seconds'], 1),
                            'action': 'manter pedido ativo ate entrada na faixa'
                        }, ensure_ascii=False) + '\n')
                if step % 5 == 0:
                    event = make_event(traci, step, pedestrians)
                    telemetry_file.write(json.dumps(event, ensure_ascii=False)+'\n')
                    with tempfile.NamedTemporaryFile('w', suffix='.json', encoding='utf-8', delete=False) as tmp:
                        json.dump([event], tmp)
                        tmp_name = tmp.name
                    try:
                        process_batch(tmp_name, db_path, logs)
                        with closing(sqlite3.connect(db_path)) as database:
                            result = database.execute('SELECT approach FROM decisions WHERE event_id=?', (event['event_id'],)).fetchone()
                            recommended_approach = result[0] if result else None
                    finally:
                        os.unlink(tmp_name)
                if mode == 'adaptive':
                    for tls in traci.trafficlight.getIDList():
                        phase = traci.trafficlight.getPhase(tls)
                        state = traci.trafficlight.getRedYellowGreenState(tls)
                        signature = (phase, state)
                        if last_phase.get(tls) != signature:
                            last_phase[tls] = signature
                            extension_per_phase[tls] = 0
                            links = traci.trafficlight.getControlledLinks(tls)
                            pedestrian_main_green = any(crossing_green_map(state, links).values())
                            # Fases de limpeza de travessia e amarelo mantêm
                            # seus tempos NATIVOS; só fase principal é adaptada.
                            duration = (green_duration(traci, tls, recommended_approach)
                                        if not pedestrians or pedestrian_main_green else None)
                            if duration is not None:
                                if pedestrians and pedestrian_priority:
                                    authorized_occupied = occupied_authorized_crossings(traci, tls)
                                    planned, reason, targets = pedestrian_service_plan(
                                        duration, state, links,
                                        pedestrian_state['pending_crossings'], authorized_occupied)
                                    if planned > duration:
                                        pedestrian_priority_adjustments += 1
                                        safety_file.write(json.dumps({
                                            'step': step, 'event': 'PRIORIDADE_PEDESTRE',
                                            'controller': tls, 'phase': phase,
                                            'target_crossings': targets,
                                            'base_green_seconds': duration,
                                            'planned_green_seconds': planned,
                                            'reason': reason
                                        }, ensure_ascii=False) + '\n')
                                    elif pedestrian_state['pending_request_count']:
                                        priority_block_reasons[reason] = priority_block_reasons.get(reason, 0) + 1
                                        safety_file.write(json.dumps({
                                            'step': step, 'event': 'PRIORIDADE_NAO_APLICADA',
                                            'controller': tls, 'phase': phase,
                                            'reason': reason,
                                            'pending_requests': pedestrian_state['pending_request_count'],
                                            'base_green_seconds': duration
                                        }, ensure_ascii=False) + '\n')
                                    duration = planned
                                traci.trafficlight.setPhaseDuration(tls, duration)
                                adjustments += 1
                        # Extende apenas a fase corrente, quando a travessia
                        # ocupada está explicitamente VERDE no programa do SUMO.
                        # Amarelo/vermelho não são prolongados; nem ocorre
                        # salto de fase ou abertura de movimento conflitante.
                        if pedestrians and occupied and extension_per_phase.get(tls, 0) < 10:
                            allowed = occupied_authorized_crossings(traci, tls)
                            remaining = traci.trafficlight.getNextSwitch(tls) - traci.simulation.getTime()
                            if allowed and remaining <= 1.5:
                                traci.trafficlight.setPhaseDuration(tls, 2)
                                extension_per_phase[tls] = extension_per_phase.get(tls, 0) + 2
                                pedestrian_hold_steps += 2
                                safety_file.write(json.dumps({
                                    'step': step, 'event': 'EXTENSAO_VERDE_PEDESTRE',
                                    'controller': tls, 'phase': phase,
                                    'authorized_crossings_occupied': len(allowed),
                                    'extension_seconds': 2,
                                    'extension_in_current_phase_seconds': extension_per_phase[tls],
                                    'reason': 'travessia ocupada com sinal de pedestre verde'
                                }, ensure_ascii=False) + '\n')
    finally:
        traci.close()
    metrics = {'mode': mode, 'steps': steps, 'pedestrians_enabled': pedestrians,
               'pedestrian_demand': demand,
               'pedestrian_priority_enabled': mode == 'adaptive' and pedestrians and pedestrian_priority,
               'pedestrian_priority_adjustments': pedestrian_priority_adjustments,
               'priority_block_reason_samples': priority_block_reasons,
               'pedestrian_crossing_samples': pedestrians_crossing_samples,
               'pedestrian_hold_steps': pedestrian_hold_steps,
               'max_simultaneously_waiting_pedestrians': maximum_waiting_pedestrians,
               'pedestrian_wait_alerts': pedestrian_wait_alerts,
               'pedestrian_safety_log': safety_log,
               'vehicles_seen': len(seen),
               'vehicles_arrived': completed, 'stopped_vehicle_samples': stopped,
               'mean_waiting_seconds_per_active_vehicle_sample': round(total_wait / max(1, active_samples), 2),
               'green_adjustments': adjustments, **pedestrian_tracker.summary(),
               **parse_tripinfo(tripinfo),
               'note': 'Métrica de espera soma esperas acumuladas por passo; não representa média por viagem.'}
    Path(output).write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'metrics_file': output, **metrics}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['adaptive', 'fixed'], default='adaptive')
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--steps', type=int, default=600)
    parser.add_argument('--pedestrians', action='store_true',
                        help='Cenário experimental com calçadas e travessias')
    parser.add_argument('--demand', choices=['normal', 'high'], default='normal',
                        help='Intensidade de fluxo pedestre no cenário com --pedestrians')
    parser.add_argument('--no-pedestrian-priority', dest='pedestrian_priority', action='store_false',
                        help='Desativa prioridade de espera; mantém extensão de travessias ocupadas')
    args = parser.parse_args()
    run(args.mode, args.gui, args.steps, args.pedestrians, args.demand, args.pedestrian_priority)
