#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from fastapi.testclient import TestClient
from interfaces.api.main import app


def main() -> int:
    parser = argparse.ArgumentParser(prog='prometeusz')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    signals = sub.add_parser('signals')
    signals.add_argument('--symbol', default=None)
    sub.add_parser('portfolio')
    sub.add_parser('halt')
    sub.add_parser('verify')
    sub.add_parser('backtest').add_argument('--days', type=int, default=30)
    watch = sub.add_parser('watch')
    watch.add_argument('--filter', default='*')
    deploy = sub.add_parser('deploy')
    deploy.add_argument('--env', default='staging')
    args = parser.parse_args()
    with TestClient(app) as client:
        if args.command == 'status':
            print(json.dumps(client.get('/intelligence/master').json(), indent=2))
        elif args.command == 'signals':
            payload = client.get('/intelligence/signals').json()
            if args.symbol:
                payload = [row for row in payload if row['symbol'] == args.symbol]
            print(json.dumps(payload, indent=2))
        elif args.command == 'portfolio':
            print(json.dumps(client.get('/quantum/portfolio').json(), indent=2))
        elif args.command == 'halt':
            print(json.dumps(client.post('/intelligence/agent/halt').json(), indent=2))
        elif args.command == 'verify':
            print(json.dumps(client.get('/intelligence/verify/all').json(), indent=2))
        elif args.command == 'backtest':
            data = client.get('/nexus/pnl').json()
            data['days'] = args.days
            print(json.dumps(data, indent=2))
        elif args.command == 'watch':
            print(f'watching consciousness stream filter={args.filter}')
        elif args.command == 'deploy':
            print(f'deploy request prepared for env={args.env}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
