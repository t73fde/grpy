#! /usr/bin/env python
##
#    Copyright (c) 2018 Detlef Stern
#
#    This file is part of grpy - user grouping.
#
#    Grpy is free software: you can redistribute it and/or modify it under the
#    terms of the GNU Affero General Public License as published by the Free
#    Software Foundation, either version 3 of the License, or (at your option)
#    any later version.
#
#    Grpy is distributed in the hope that it will be useful, but WITHOUT ANY
#    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#    FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
#    more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with grpy. If not, see <http://www.gnu.org/licenses/>.
##

"""
Management / development script.

Provides commands for static and dynamic tests.
"""

import subprocess  # nosec
from typing import List, Sequence

import click


def exec_subprocess(args: Sequence[str], verbose: bool):
    """Execute a subprocess with the given args and report error messages."""
    if verbose:
        click.echo("Executing '{}' ...".format(" ".join(args)), nl=False)
    process = subprocess.run(  # nosec
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if verbose:
        click.echo(" done.")
    if process.returncode:
        click.echo("!!!\n!!! Error in: " + " ".join(args))
        click.echo("!!!")
        click.echo(process.stderr)
        click.echo(process.stdout)
    return process


def run_subprocess(args: Sequence[str], verbose: bool) -> bool:
    """Run a subprocess with the given args and report error messages."""
    process = exec_subprocess(args, verbose)
    return process.returncode == 0


def lint_formatting(source_paths: List[str], verbose: bool) -> bool:
    """Check for an appropriate format of source code."""
    process = exec_subprocess(
        ["autopep8", "--diff", "--recursive"] + source_paths, verbose)
    if process.returncode == 0 and process.stdout:
        click.echo(process.stdout)
        click.echo("-- please format source code")
        return False
    return process.returncode == 0


def lint_flake8(source_paths: List[str], verbose: bool) -> bool:
    """Run flake8."""
    try:
        from _multiprocessing import SemLock  # noqa: F401 pylint: disable=unused-import
        flake8_params = []
    except ImportError:
        flake8_params = ["-j", "1"]

    return run_subprocess(["flake8"] + flake8_params + source_paths, verbose)


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, verbose):  # pylint: disable=unused-argument
    """Entry point for all sub-commands."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def lint(ctx, verbose):
    """Perform a static code analysis."""
    verbose += ctx.obj['verbose']
    source_paths = ["grpy", "scripts", "wsgi.py", "manage.py"]
    formatting_ok = lint_formatting(source_paths, verbose)
    docstyle_ok = run_subprocess(["pydocstyle", "-v", "-e"] + source_paths, verbose)
    flake8_ok = lint_flake8(source_paths, verbose)
    dodgy_ok = run_subprocess(["dodgy"], verbose)
    pylint_ok = run_subprocess(["pylint", "grpy"], verbose)
    bandit_ok = run_subprocess(["bandit", "-r", "-x", "test", "."], verbose)

    if not (formatting_ok and docstyle_ok and flake8_ok and dodgy_ok and
            pylint_ok and bandit_ok):
        ctx.exit(1)


if __name__ == '__main__':
    main(obj={})  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
