#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from pathlib import Path

try:
    import click
except ImportError:  # pragma: no cover
    class _ClickShim:
        def group(self):
            return lambda fn: fn
        def command(self, *args, **kwargs):
            return lambda fn: fn
        def option(self, *args, **kwargs):
            return lambda fn: fn
        def argument(self, *args, **kwargs):
            return lambda fn: fn
        def echo(self, value):
            print(value)
    click = _ClickShim()

from interfaces.api.dependencies import get_app_container

@click.group()
def cli():
    pass

@cli.command()
def status():
    container = get_app_container()
    print(asyncio.run(container.intelligence_master()))

@cli.command()
@click.option('--symbol', default='SOLUSDT')
def signals(symbol: str):
    container = get_app_container()
    print(asyncio.run(container.intelligence_master())['market']['signals'].get(symbol))

@cli.command()
def portfolio():
    container = get_app_container()
    print(asyncio.run(container.portfolio_engine.optimize_live(container.market_data.candle_snapshot())))

@cli.command()
def halt():
    container = get_app_container()
    asyncio.run(container.agent.emergency_halt())
    print('halted')

@cli.command()
def verify():
    container = get_app_container()
    print(container.formal_verifier.verify_all())

@cli.command()
@click.option('--filter', 'filter_value', default='*')
def watch(filter_value: str):
    container = get_app_container()
    print({'filter': filter_value, 'events': container.event_bus.get_recent(limit=20)})

@cli.command()
@click.option('--days', default=30)
def backtest(days: int):
    container = get_app_container()
    pnl = asyncio.run(container.execution_bridge.track_pnl())
    print({'days': days, 'pnl': pnl})

@cli.command()
@click.option('--env', 'env_name', default='staging')
def deploy(env_name: str):
    print({'env': env_name, 'script': 'k8s/deploy.sh'})

if __name__ == '__main__':
    cli()
