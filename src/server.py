"""Painel local de resultados SUMO; somente leitura, sem controlar semáforos."""
import argparse
import json
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from sqlite3 import Row, connect
from urllib.parse import urlsplit

from .run_manager import RunManager

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'data' / 'runs'


def load_runs(runs_dir=RUNS, limit=100):
    """Lê relatórios completos, ignorando arquivos parciais ou danificados."""
    records = []
    if not runs_dir.exists():
        return records
    for path in sorted(runs_dir.glob('*.metrics.json'), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            if path.stat().st_size > 256_000:
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('mode') not in ('fixed', 'adaptive'):
                continue
            records.append({'run_id': path.name.removesuffix('.metrics.json'),
                            'created_at': path.stat().st_mtime, **data})
        except (OSError, ValueError, UnicodeError):
            continue
        if len(records) >= limit:
            break
    return records


def high_demand_comparison(runs):
    """Seleciona os três últimos ensaios equivalentes de 600 passos."""
    selected = {}
    for run in runs:
        if run.get('steps') != 600 or not run.get('pedestrians_enabled') or run.get('pedestrian_demand') != 'high':
            continue
        key = ('fixed' if run['mode'] == 'fixed' else
               'adaptive_priority' if run.get('pedestrian_priority_enabled') else 'adaptive_no_priority')
        selected.setdefault(key, run)
    return selected


def make_handler(db, runs_dir=RUNS, manager=None):
    manager = manager if manager is not None else RunManager()

    class Handler(BaseHTTPRequestHandler):
        def send_json(self, value, status=200):
            content = json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            if urlsplit(self.path).path != '/api/jobs':
                self.send_error(404)
                return
            # O serviço é exclusivamente local; recusa requisições cross-site.
            origin = self.headers.get('Origin')
            host = self.headers.get('Host', '')
            if host not in ('127.0.0.1:' + str(self.server.server_port),
                            'localhost:' + str(self.server.server_port)):
                self.send_json({'error': 'Host não permitido'}, 403)
                return
            if origin and origin not in ('http://127.0.0.1:' + str(self.server.server_port),
                                         'http://localhost:' + str(self.server.server_port)):
                self.send_json({'error': 'Origem não permitida'}, 403)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 1 <= length <= 1024:
                    raise ValueError('Corpo da requisição inválido')
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict) or set(payload) != {'action'} or not isinstance(payload['action'], str):
                    raise ValueError('Formato inválido')
                started = manager.start(payload['action'])
            except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
                self.send_json({'error': str(exc)}, 400)
                return
            if started is None:
                self.send_json({'error': 'Já existe uma execução em andamento'}, 409)
                return
            self.send_json(started, 202)

        def do_GET(self):
            route = urlsplit(self.path).path
            if route in ('/', '/index.html'):
                content = Path(__file__).with_name('dashboard.html').read_bytes()
                mime = 'text/html; charset=utf-8'
            elif route in ('/api/runs', '/api/comparison'):
                runs = load_runs(runs_dir)
                result = runs if route == '/api/runs' else high_demand_comparison(runs)
                content = json.dumps(result, ensure_ascii=False, allow_nan=False).encode('utf-8')
                mime = 'application/json; charset=utf-8'
            elif route == '/api/jobs':
                self.send_json(manager.status())
                return
            elif route == '/api/decisions':
                try:
                    with closing(connect(db)) as conn:
                        conn.row_factory = Row
                        records = [dict(row) for row in conn.execute(
                            'SELECT * FROM decisions ORDER BY processed_at DESC, event_id DESC LIMIT 100')]
                    content = json.dumps(records, ensure_ascii=False).encode('utf-8')
                except Exception:
                    self.send_error(503, 'Banco de decisoes indisponivel')
                    return
                mime = 'application/json; charset=utf-8'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=str(ROOT/'data/citizenflow.db'))
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    print(f'Painel Sinal Cidadao: http://localhost:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(args.db)).serve_forever()


if __name__ == '__main__':
    main()
