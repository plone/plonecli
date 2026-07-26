"""Coloured terminal output, shared by the commands and by ``plonecli.git``."""

from __future__ import annotations

import click


def echo(msg: str, fg: str = "green", reverse: bool = False) -> None:
    """Write a styled line to stdout."""
    click.echo(click.style(msg, fg=fg, reverse=reverse))


def error(msg: str) -> None:
    """Write a styled error line to stderr."""
    click.echo(click.style(msg, fg="red"), err=True)
