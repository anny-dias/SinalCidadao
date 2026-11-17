import json
import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def setup_logger(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('citizenflow')
    logger.setLevel(logging.INFO)
    for old_handler in logger.handlers[:]:
        old_handler.close()
        logger.removeHandler(old_handler)
    handler = logging.FileHandler(path, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    return logger


def audit(logger, level, event_id, message):
    logger.info(json.dumps({'timestamp': now(), 'level': level, 'event_id': event_id, 'message': message}, ensure_ascii=False))


def connect(db):
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.execute('''CREATE TABLE IF NOT EXISTS decisions (
        event_id TEXT PRIMARY KEY, processed_at TEXT NOT NULL, source_timestamp TEXT NOT NULL,
        action TEXT NOT NULL, approach TEXT, green_seconds INTEGER,
        reason TEXT NOT NULL, mode TEXT NOT NULL)''')
    conn.commit()
    return conn


def validate(event):
    if not isinstance(event, dict) or not isinstance(event.get('event_id'), str) or not event['event_id'].strip():
        raise ValueError('event_id inválido')
    if not isinstance(event.get('timestamp'), str) or not event['timestamp']:
        raise ValueError('timestamp ausente')
    if type(event.get('camera_online')) is not bool:
        raise ValueError('camera_online deve ser booleano')
    approaches = event.get('approaches')
    if not isinstance(approaches, list) or not approaches:
        raise ValueError('approaches deve conter ao menos uma via')
    ids = set()
    for a in approaches:
        if not isinstance(a, dict) or not isinstance(a.get('id'), str) or not a['id'].strip():
            raise ValueError('id de via inválido')
        if a['id'] in ids:
            raise ValueError('vias duplicadas no evento')
        ids.add(a['id'])
        for key in ('queue_vehicles', 'wait_seconds', 'pedestrians_crossing'):
            value = a.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f'{key} inválido na via {a["id"]}')
    return event


def decide(event):
    approaches = event['approaches']
    if not event['camera_online']:
        return ('FIXED_TIME_FALLBACK', None, 30, 'Câmera indisponível; modo tempo fixo simulado', 'FALLBACK')
    pedestrians = [a for a in approaches if a['pedestrians_crossing'] > 0]
    if pedestrians:
        chosen = max(pedestrians, key=lambda a: a['pedestrians_crossing'])
        return ('HOLD_PEDESTRIAN_PHASE', chosen['id'], 15, 'Presença na faixa; extensão simulada limitada', 'ADAPTIVE')
    chosen = max(approaches, key=lambda a: a['queue_vehicles'] * 2 + a['wait_seconds'] / 10 + (100 if a['wait_seconds'] >= 90 else 0))
    duration = min(45, max(10, round(10 + chosen['queue_vehicles'] * 2)))
    return ('GRANT_GREEN', chosen['id'], duration, 'Prioridade por fila e espera (com proteção anti-inanição)', 'ADAPTIVE')


def process_batch(input_path, db_path, log_path):
    logger = setup_logger(log_path)
    try:
        return _process_batch(input_path, db_path, logger)
    finally:
        # No Windows, arquivos ainda abertos impedem TemporaryDirectory.cleanup().
        # Fechar o handler também libera o log quando a entrada é inválida.
        for handler in logger.handlers[:]:
            handler.flush()
            handler.close()
            logger.removeHandler(handler)


def _process_batch(input_path, db_path, logger):
    stats = {'processed': 0, 'duplicates': 0, 'failed': 0}
    try:
        with open(input_path, encoding='utf-8') as f:
            events = json.load(f)
        if not isinstance(events, list):
            raise ValueError('A raiz do JSON deve ser uma lista de eventos')
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        audit(logger, 'ERROR', None, f'Entrada não carregada: {exc}')
        raise
    # sqlite3.Connection.__exit__ confirma/reverte a transação, mas NÃO fecha
    # a conexão. closing garante liberação real do arquivo db.sqlite.
    with closing(connect(db_path)) as conn, conn:
        for index, event in enumerate(events):
            event_id = event.get('event_id') if isinstance(event, dict) else None
            try:
                validate(event)
                action, approach, duration, reason, mode = decide(event)
                cursor = conn.execute('''INSERT OR IGNORE INTO decisions VALUES (?,?,?,?,?,?,?,?)''',
                                      (event_id, now(), event['timestamp'], action, approach, duration, reason, mode))
                if cursor.rowcount == 0:
                    stats['duplicates'] += 1
                    audit(logger, 'WARN', event_id, 'SKIPPED_DUPLICATE')
                else:
                    stats['processed'] += 1
                    audit(logger, 'INFO', event_id, f'{action} via={approach} duração={duration}s')
            except (ValueError, TypeError, KeyError) as exc:
                stats['failed'] += 1
                audit(logger, 'ERROR', event_id, f'Item {index}: {exc}')
        conn.commit()
    audit(logger, 'INFO', None, f'Resumo: {stats}')
    return stats
