"""Executa tarefas locais predefinidas do painel, uma por vez."""
import re
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = {
    'fixed_gui': ('Fixo · SUMO-GUI', ['-m', 'src.sumo_bridge', '--mode', 'fixed', '--pedestrians', '--demand', 'high', '--gui']),
    'adaptive_gui': ('Adaptativo · SUMO-GUI', ['-m', 'src.sumo_bridge', '--mode', 'adaptive', '--pedestrians', '--demand', 'high', '--no-pedestrian-priority', '--gui']),
    'priority_gui': ('Prioridade pedestre · SUMO-GUI', ['-m', 'src.sumo_bridge', '--mode', 'adaptive', '--pedestrians', '--demand', 'high', '--gui']),
    'tests': ('Testes automatizados', ['-m', 'unittest', 'discover', '-s', 'tests', '-v']),
}
COMPARE = ('fixed_gui', 'adaptive_gui', 'priority_gui')


def initial_state():
    return {'job_id': 0, 'action': None, 'label': None, 'status': 'idle',
            'current': 0, 'total': 0, 'started_at': None, 'finished_at': None,
            'results': [], 'error': None, 'tests_summary': None}


class RunManager:
    def __init__(self, runner=subprocess.run):
        self._lock = threading.Lock()
        self._state = initial_state()
        self._runner = runner

    def status(self):
        with self._lock:
            return {**self._state, 'results': [dict(r) for r in self._state['results']]}

    def start(self, action):
        if action not in COMMANDS and action != 'compare':
            raise ValueError('Operação não permitida')
        with self._lock:
            if self._state['status'] == 'running':
                return None
            job_id = self._state['job_id'] + 1
            self._state = {**initial_state(), 'job_id': job_id, 'action': action,
                           'label': 'Comparação dos três cenários' if action == 'compare' else COMMANDS[action][0],
                           'status': 'running', 'started_at': datetime.now(timezone.utc).isoformat(),
                           'total': 3 if action == 'compare' else 1}
        threading.Thread(target=self._execute, args=(job_id, action), daemon=True).start()
        return self.status()

    def _execute(self, job_id, action):
        queue = COMPARE if action == 'compare' else (action,)
        try:
            for index, kind in enumerate(queue, 1):
                label, args = COMMANDS[kind]
                with self._lock:
                    if self._state['job_id'] != job_id:
                        return
                    self._state['current'] = index
                    self._state['current_label'] = label
                try:
                    # Lista fixa de argumentos: o navegador nunca escolhe um comando ou caminho.
                    process = self._runner([sys.executable, *args], cwd=ROOT, text=True,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           encoding='utf-8', errors='replace', timeout=1200,
                                           env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
                    output = process.stdout or ''
                    returncode = process.returncode
                except subprocess.TimeoutExpired:
                    output, returncode = 'Tempo máximo de 20 minutos excedido.', 124
                except (OSError, subprocess.SubprocessError) as exc:
                    output, returncode = f'{type(exc).__name__}: {exc}', 1
                result = {'label': label, 'passed': returncode == 0, 'exit_code': returncode,
                          'output_tail': output[-5000:]}
                if kind == 'tests':
                    match = re.search(r'Ran (\d+) tests? in [\d.]+s', output)
                    result['tests_count'] = int(match.group(1)) if match else None
                    result['tests_ok'] = returncode == 0 and bool(re.search(r'^OK\s*$', output, re.M))
                with self._lock:
                    self._state['results'].append(result)
                    if kind == 'tests':
                        self._state['tests_summary'] = {'count': result['tests_count'], 'ok': result['tests_ok']}
                if returncode:
                    raise RuntimeError(f'{label} terminou com erro {returncode}; veja os detalhes')
            with self._lock:
                self._state['status'] = 'completed'
        except Exception as exc:
            with self._lock:
                self._state['status'] = 'failed'
                self._state['error'] = str(exc)
        finally:
            with self._lock:
                self._state['finished_at'] = datetime.now(timezone.utc).isoformat()
