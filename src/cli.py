import argparse
import json
from .automation import process_batch


def main():
    parser = argparse.ArgumentParser(description='CitizenFlow - automação RPA')
    parser.add_argument('--input', default='data/leituras.json')
    parser.add_argument('--db', default='data/citizenflow.db')
    parser.add_argument('--log', default='logs/automation.jsonl')
    args = parser.parse_args()
    try:
        result = process_batch(args.input, args.db, args.log)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:
        parser.exit(1, f'Falha na automação: {exc}\n')


if __name__ == '__main__':
    main()
