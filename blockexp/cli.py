import asyncio
import logging
from typing import TextIO

import click
import toml

from blockexp import init_app
from blockexp.application import Application


@click.group()
def cli():
    pass


@cli.command()
@click.argument('config', type=click.File('r'), default="blockexp.toml")
def start(config: TextIO = None):
    if config is not None:
        with config:
            cfg = toml.load(config)
    else:
        cfg = {}

    logging.basicConfig(level=logging.INFO)

    app: Application = asyncio.run(init_app(cfg))
    app.serve()


if __name__ == '__main__':
    cli()
