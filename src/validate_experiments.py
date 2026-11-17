"""Validação offline dos relatórios SUMO, sem reiniciar a simulação."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .server import ROOT, high_demand_comparison, load_runs

REQUIRED = (
    'completed_vehicle_trips', 'average_vehicle_waiting_seconds',
    'observed_pedestrian_crossing_starts', 'observed_pedestrian_crossing_completions',
    'average_pre_crossing_wait_seconds', 'pedestrian_priority_adjustments',
    'pedestrian_wait_alerts', 'green_adjustments',
)
LABELS = {'fixed': 'Fixo', 'adaptive_no_priority': 'Adaptativo sem prioridade',
          'adaptive_priority': 'Adaptativo com prioridade'}


def evaluate(runs):
    comparison = high_demand_comparison(runs)
    checks = []

    def check(label, condition, details=''):
        checks.append({'check': label, 'passed': bool(condition), 'details': details})

    check('Três cenários disponíveis (alta demanda, 600 passos)', len(comparison) == 3,
          f'Encontrados: {", ".join(comparison) or "nenhum"}')
    for key in ('fixed', 'adaptive_no_priority', 'adaptive_priority'):
        run = comparison.get(key)
        if not run:
            continue
        check(f'{LABELS[key]}: campos obrigatórios', all(field in run for field in REQUIRED))
        checks_missing = [name for name in REQUIRED if name not in run]
        if checks_missing:
            check(f'{LABELS[key]}: relatório incompleto', False, ', '.join(checks_missing))
            continue
        check(f'{LABELS[key]}: travessias concluídas não excedem iniciadas',
              0 <= run['observed_pedestrian_crossing_completions'] <= run['observed_pedestrian_crossing_starts'])
        check(f'{LABELS[key]}: espera de veículos não negativa', run['average_vehicle_waiting_seconds'] >= 0)
        check(f'{LABELS[key]}: espera de pedestres não negativa', run['average_pre_crossing_wait_seconds'] >= 0)
        check(f'{LABELS[key]}: número de viagens coerente', run['completed_vehicle_trips'] >= 0)
    fixed = comparison.get('fixed')
    no_priority = comparison.get('adaptive_no_priority')
    with_priority = comparison.get('adaptive_priority')
    if fixed and all(k in fixed for k in ('pedestrian_priority_adjustments', 'green_adjustments')):
        check('Semáforo fixo não ajustou fases', fixed['green_adjustments'] == 0)
        check('Semáforo fixo não acionou prioridade', fixed['pedestrian_priority_adjustments'] == 0)
    if no_priority and 'pedestrian_priority_adjustments' in no_priority:
        check('Adaptativo sem prioridade não acionou prioridade',
              no_priority['pedestrian_priority_adjustments'] == 0)
    if with_priority and 'pedestrian_priority_enabled' in with_priority:
        check('Adaptativo prioritário habilitado', with_priority['pedestrian_priority_enabled'] is True)

    def percentage_change(metric):
        if not fixed or not with_priority:
            return None
        baseline = fixed.get(metric)
        candidate = with_priority.get(metric)
        if not isinstance(baseline, (int, float)) or not isinstance(candidate, (int, float)) or baseline == 0:
            return None
        return round(100 * (candidate / baseline - 1), 2)

    return {'generated_at': datetime.now(timezone.utc).isoformat(),
            'selected_runs': {key: run['run_id'] for key, run in comparison.items()},
            'checks': checks, 'passed': all(c['passed'] for c in checks),
            'vehicle_wait_change_percent': percentage_change('average_vehicle_waiting_seconds'),
            'pedestrian_wait_change_percent': percentage_change('average_pre_crossing_wait_seconds'),
            'notes': ['Comparação dos últimos ensaios de 600 passos com demanda alta.',
                      'Redução percentual negativa representa melhora na espera.',
                      'Resultados válidos para o modelo simulado; não demonstram segurança em vias reais.',
                      'Ausência de alertas não comprova ausência de conflitos entre veículos e pedestres.']}


def main():
    parser = argparse.ArgumentParser(description='Validação offline dos ensaios do SUMO')
    parser.add_argument('--runs-dir', type=Path, default=ROOT / 'data/runs')
    parser.add_argument('--output', type=Path, help='Opcional: salvar relatório JSON de validação')
    args = parser.parse_args()
    result = evaluate(load_runs(args.runs_dir))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
