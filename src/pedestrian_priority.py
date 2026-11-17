"""Prioridade limitada de pedestres; nunca modifica a sequência semafórica."""

MIN_VEHICLE_GREEN_SECONDS = 10
PRIORITY_WAIT_SECONDS = 3
MIN_PEDESTRIAN_SERVICE_GREEN_SECONDS = 18


def crossing_green_map(state, controlled_links):
    """Relaciona aresta de faixa ao estado (verde ou não) de seu sinal."""
    result = {}
    for index, links in enumerate(controlled_links):
        if index >= len(state):
            break
        for link in links:
            if not link or not link[1]:
                continue
            target = link[1].rsplit('_', 1)[0]
            if target.startswith(':') and '_c' in target:
                result[target] = result.get(target, False) or state[index] in ('g', 'G')
    return result


def pending_red_crossings(pending_crossings, state, controlled_links):
    """Pedidos associados a faixas controladas cujo sinal NÃO está verde."""
    green_map = crossing_green_map(state, controlled_links)
    return {crossing: count for crossing, count in pending_crossings.items()
            if count > 0 and crossing in green_map and not green_map[crossing]}


def pedestrian_service_plan(base_green_seconds, state, controlled_links,
                            pending_crossings, occupied_authorized_crossings):
    """Planeja verde principal sem modificar fases intermediárias ou amarelo.

    A fase só recebe extensão planejada se autoriza pelo menos uma faixa
    e há demanda nessa própria faixa (pedido ou travessia já iniciada).
    """
    greens = crossing_green_map(state, controlled_links)
    authorized = {crossing for crossing, green in greens.items() if green}
    served_pending = {crossing: count for crossing, count in pending_crossings.items()
                      if crossing in authorized and count > 0}
    occupied = authorized.intersection(occupied_authorized_crossings)
    if not authorized:
        return base_green_seconds, 'FASE_SEM_VERDE_DE_PEDESTRE', []
    if not served_pending and not occupied:
        return base_green_seconds, 'SEM_DEMANDA_NA_FAIXA_AUTORIZADA', []
    planned = max(base_green_seconds, MIN_PEDESTRIAN_SERVICE_GREEN_SECONDS)
    return planned, ('RESERVA_VERDE_TRAVESSIA' if planned > base_green_seconds
                     else 'VERDE_EXISTENTE_SUFFICIENTE'), sorted(set(served_pending) | occupied)


def priority_remaining_green(*, phase_elapsed, remaining, waiting_count,
                             longest_wait_seconds, authorized_crossing_occupied):
    """Retorna nova duração RESTANTE ou None quando não há ajuste seguro.

    Somente a fase veicular verde atual pode ser encurtada, e nunca antes
    do mínimo de verde. A transição e as fases de segurança continuam no SUMO.
    """
    remaining_green, _ = priority_decision(
        phase_elapsed=phase_elapsed, remaining=remaining,
        waiting_count=waiting_count, longest_wait_seconds=longest_wait_seconds,
        authorized_crossing_occupied=authorized_crossing_occupied)
    return remaining_green


def priority_decision(*, phase_elapsed, remaining, waiting_count,
                      longest_wait_seconds, authorized_crossing_occupied):
    """Retorna (novo_tempo_restante, motivo), útil para auditoria de bloqueios."""
    if waiting_count < 1:
        return None, 'SEM_PEDIDO_PENDENTE'
    if longest_wait_seconds < PRIORITY_WAIT_SECONDS:
        return None, 'AGUARDANDO_LIMIAR'
    if authorized_crossing_occupied:
        return None, 'TRAVESSIA_AUTORIZADA_OCUPADA'
    minimum_remaining = max(1, MIN_VEHICLE_GREEN_SECONDS - phase_elapsed)
    if remaining <= minimum_remaining + 0.5:
        return None, 'VERDE_MINIMO_OU_TEMPO_INSUFICIENTE'
    return minimum_remaining, 'ENCURTAMENTO_SEGURO'
