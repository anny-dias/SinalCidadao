"""Métricas agregadas de pedestres simulados, sem persistir identificadores."""
from statistics import mean
from collections import Counter


def is_crossing(road):
    return road.startswith(':') and '_c' in road


class PedestrianTracker:
    """Acompanha pessoas apenas em memória durante a execução do SUMO.

    A espera é a maior espera contínua observada antes de entrar na faixa.
    A travessia é o intervalo entre entrar e sair de uma aresta de faixa.
    """

    def __init__(self):
        self._active = {}
        self.waits = []
        self.crossings = []
        self.peak_wait_seen = 0.0
        self.alerted_waiters = 0

    def update(self, simulation_time, observations):
        """Observações (id, via, espera[, próxima_aresta]), somente em memória."""
        present = set()
        currently_waiting = []
        pending_waiting = []
        pending_crossings = Counter()
        currently_crossing = 0
        completed = []
        new_alerts = 0
        for observation in observations:
            person_id, road, waiting_seconds = observation[:3]
            next_edge = observation[3] if len(observation) > 3 else ''
            present.add(person_id)
            state = self._active.setdefault(person_id, {
                'peak_wait': 0.0, 'crossing_start': None, 'finished': False,
                'request_started': None, 'alerted': False, 'target_crossing': None
            })
            on_crossing = is_crossing(road)
            if on_crossing:
                currently_crossing += 1
                if state['crossing_start'] is None and not state['finished']:
                    state['crossing_start'] = simulation_time
                    self.waits.append(state['peak_wait'])
            elif state['crossing_start'] is not None and not state['finished']:
                duration = max(0.0, simulation_time - state['crossing_start'])
                self.crossings.append(duration)
                completed.append(duration)
                state['finished'] = True
            elif not state['finished']:
                state['peak_wait'] = max(state['peak_wait'], max(0.0, waiting_seconds))
                self.peak_wait_seen = max(self.peak_wait_seen, state['peak_wait'])
                if waiting_seconds >= 1:
                    currently_waiting.append(waiting_seconds)
                    if state['request_started'] is None:
                        state['request_started'] = simulation_time - waiting_seconds
                if state['request_started'] is not None:
                    if is_crossing(next_edge):
                        state['target_crossing'] = next_edge
                    age = max(0, simulation_time - state['request_started'])
                    pending_waiting.append(age)
                    if state['target_crossing']:
                        pending_crossings[state['target_crossing']] += 1
                    if age >= 15 and not state['alerted']:
                        state['alerted'] = True
                        self.alerted_waiters += 1
                        new_alerts += 1

        # Pessoas concluídas podem desaparecer da simulação no mesmo passo.
        for missing in set(self._active) - present:
            state = self._active[missing]
            if state['crossing_start'] is not None and not state['finished']:
                duration = max(0.0, simulation_time - state['crossing_start'])
                self.crossings.append(duration)
                completed.append(duration)
            del self._active[missing]
        return {
            'waiting_count': len(currently_waiting),
            'max_current_wait_seconds': max(currently_waiting, default=0),
            'pending_request_count': len(pending_waiting),
            'oldest_pending_request_seconds': max(pending_waiting, default=0),
            'pending_crossings': dict(pending_crossings),
            'new_wait_alerts': new_alerts,
            'crossing_count': currently_crossing,
            'completed_crossings': len(completed),
        }

    def summary(self):
        return {
            'observed_pedestrian_crossing_starts': len(self.waits),
            'observed_pedestrian_crossing_completions': len(self.crossings),
            'average_pre_crossing_wait_seconds': round(mean(self.waits), 2) if self.waits else None,
            'maximum_observed_pre_crossing_wait_seconds': round(self.peak_wait_seen, 2),
            'observed_wait_alerts': self.alerted_waiters,
            'average_crossing_seconds': round(mean(self.crossings), 2) if self.crossings else None,
            'pedestrian_measurement_note': 'Espera e travessia estimadas por amostras TraCI; não equivalem à duração total da viagem.'
        }
