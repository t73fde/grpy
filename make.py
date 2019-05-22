#! /usr/bin/env python
##
#    Copyright (c) 2019 Detlef Stern
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

import pathlib
import re
import shutil
import subprocess  # nosec
from typing import List, Sequence, Tuple, cast

import click
import requests


def exec_subprocess_no_report(args: Sequence[str], verbose: int):
    """Execute a subprocess with the given args."""
    if verbose:
        click.echo("Executing '{}' ...".format(" ".join(args)), nl=False)
    process = subprocess.run(  # nosec
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if verbose:
        click.echo(" done.")
    return process


def exec_subprocess(args: Sequence[str], verbose: int):
    """Execute a subprocess with the given args and report error messages."""
    process = exec_subprocess_no_report(args, verbose)
    if process.returncode:
        click.echo("!!!\n!!! Error in: " + " ".join(args))
        click.echo("!!!")
        click.echo(process.stderr)
        click.echo(process.stdout)
    return process


def run_subprocess(args: Sequence[str], verbose: int) -> bool:
    """Run a subprocess with the given args and report error messages."""
    process = exec_subprocess(args, verbose)
    return cast(int, process.returncode) == 0


def lint_formatting(source_paths: List[str], verbose: int) -> bool:
    """Check for an appropriate format of source code."""
    process = exec_subprocess(
        ["autopep8", "--diff", "--recursive"] + source_paths, verbose)
    if process.returncode == 0 and process.stdout:
        click.echo(process.stdout)
        click.echo("-- please format source code")
        return False
    return cast(int, process.returncode) == 0


def lint_flake8(source_paths: List[str], verbose: int) -> bool:
    """Run flake8."""
    try:
        from _multiprocessing import SemLock  # noqa: F401 pylint: disable=unused-import
        flake8_params: List[str] = []
    except ImportError:
        flake8_params = ["-j", "1"]

    return run_subprocess(["flake8"] + flake8_params + source_paths, verbose)


def run_coverage(paths: Sequence[str], test_directory: str, verbose: int) -> bool:
    """Run the coverage checks."""
    process = exec_subprocess(
        ["pytest", "--testmon-off", "--cov-report=term", "--cov-report=html"] +
        ["--cov=" + p for p in paths] + [test_directory],
        verbose)
    if process.returncode:
        return False
    match_obj = re.search(rb'\nTOTAL.+ (\d+)%\n', process.stdout)
    if match_obj is None:
        match_obj = re.search(rb' (\d+)%\n', process.stdout)
    covered = match_obj and match_obj[1] == b'100'
    if verbose > 1 or not covered:
        click.echo(process.stdout)
    return verbose > 2 or bool(covered)


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def main(ctx, verbose: int) -> None:
    """Entry point for all sub-commands."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@main.command()
@click.option('-f', '--force', is_flag=True)
@click.option('-q', '--quiet', is_flag=True)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def clean(ctx, force: bool, quiet: bool, verbose: int) -> None:
    """Remove temporary files and directories."""
    verbose += ctx.obj['verbose']
    base_path = pathlib.Path()
    paths = list(base_path.glob("**/__pycache__"))

    entries = [str(p) for p in base_path.iterdir()]
    process = exec_subprocess(["git", "check-ignore", *entries], verbose)
    if not process.returncode:
        paths.extend(
            [base_path / entry.decode('utf-8') for entry in process.stdout.split()])

    for path in paths:
        if not force:
            click.echo(path)
            continue

        if path.is_file():
            if not quiet:
                click.echo("rm " + str(path))
            path.unlink()
        elif path.is_dir():
            if not quiet:
                click.echo("rm -rf " + str(path))
            shutil.rmtree(str(path))


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def types(ctx, verbose: int) -> None:
    """Perform a type analysis."""
    verbose += ctx.obj['verbose']
    process = exec_subprocess_no_report(["mypy", "grpy"], verbose)
    errors = False
    for message in process.stdout.split(b"\n"):
        match_obj = re.search(rb'^[^0-9]+[0-9]+: ([^:]+): (.+)$', message)
        if not match_obj:
            continue
        msg_level, msg_text = match_obj.groups()
        if msg_level == b"note":
            continue
        if msg_text.startswith(b"No library stub file for module '"):
            continue
        if msg_text.startswith(b"Cannot find module named '"):
            continue
        click.echo(message)
        errors = True
    if errors:
        ctx.exit(1)


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def lint(ctx, verbose: int) -> None:
    """Perform a static code analysis."""
    verbose += ctx.obj['verbose']
    source_paths = ["grpy", "deploy", "wsgi.py", "make.py", "setup.py"]
    formatting_ok = lint_formatting(source_paths, verbose)
    docstyle_ok = run_subprocess(["pydocstyle", "-v", "-e"] + source_paths, verbose)
    flake8_ok = lint_flake8(source_paths, verbose)
    dodgy_ok = run_subprocess(["dodgy"], verbose)
    pylint_ok = run_subprocess(["pylint", "grpy"], verbose)
    bandit_ok = run_subprocess(["bandit", "-r", "-x", ".git,.tox,test", "."], verbose)

    if not (formatting_ok and docstyle_ok and flake8_ok and dodgy_ok and
            pylint_ok and bandit_ok):
        ctx.exit(1)


@main.command()
@click.argument('directory', required=False)
@click.option('-v', '--verbose', count=True)
@click.pass_context
def coverage(ctx, directory: str, verbose: int) -> None:
    """Perform a full test with coverage measurement."""
    verbose += ctx.obj['verbose']
    if directory is None:
        if not run_coverage(["grpy"], "grpy", verbose):
            ctx.exit(1)
    else:
        files, packages = collect_files_and_packages()
        if directory == "grpy":
            if not run_coverage(files, "grpy/test", verbose):
                ctx.exit(1)
        elif directory in packages:
            if not run_coverage([directory], directory, verbose):
                ctx.exit(1)
        else:
            click.echo(
                f"Unknown directory '{directory}'. "
                "Must be one of {sorted(['grpy'] + packages)}")
            ctx.exit(1)


def valid_directory(directory_path) -> bool:
    """Return True for directories to be covered."""
    invalid_names = {"__pycache__", "static", "test", "templates"}
    for name in reversed(directory_path.parts):
        if name in invalid_names:
            return False
    return True


def collect_files_and_packages() -> Tuple[List[str], List[str]]:
    """Scan subdirectores and collect needed files and packages."""
    no_python_dir = {
        "grpy/web/templates",
        "grpy/web/static",
    }

    packages = []
    files = []
    for path in pathlib.Path("grpy").glob('**/*'):
        name = path.parts[-1]
        if name.startswith("."):
            continue
        if path.is_dir():
            if valid_directory(path) and str(path) not in no_python_dir:
                packages.append(str(path))
        elif len(path.parts) == 2 and path.is_file():
            if path.suffix == ".py" and name != "__init__.py":
                files.append(str(path).replace("/", ".")[:-3])

    packages.sort(reverse=True)
    return files, packages


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def full_coverage(ctx, verbose: int) -> None:
    """Perform a full test with coverage measurement, for all packages."""
    verbose += ctx.obj['verbose']
    files, packages = collect_files_and_packages()
    if not run_coverage(files, "grpy/test", verbose):
        ctx.exit(1)
    for directory in packages:
        if not run_coverage([directory], directory, verbose):
            ctx.exit(1)
    ctx.invoke(coverage, directory=None, verbose=verbose)


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def outdated(ctx, verbose: int) -> None:
    """Check for outdated packages."""
    if not run_subprocess(["pipenv", "check"], verbose):
        ctx.exit(1)


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def check(ctx, verbose: int) -> None:
    """Perform a check: lint and coverage."""
    ctx.invoke(lint, verbose=verbose)
    ctx.invoke(coverage, verbose=verbose)
    ctx.invoke(outdated, verbose=verbose)


@main.command()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def full_check(ctx, verbose: int) -> None:
    """Perform a full check: lint and full-coverage."""
    ctx.invoke(lint, verbose=verbose)
    ctx.invoke(types, verbose=verbose)
    ctx.invoke(full_coverage, verbose=verbose)
    ctx.invoke(outdated, verbose=verbose)


@main.command()
@click.pass_context
def update_w3css(ctx) -> None:
    """Update the external CSS stylesheet W3.CSS."""
    response = requests.get("https://www.w3schools.com/w3css/4/w3.css")
    if response.status_code != 200:
        click.echo("Unable to download WS.CSS, HTTP status code: %d" % (
            response.status_code,))
        ctx.exit(1)
    with open("grpy/web/static/w3.css", "wb") as css_file:
        css_file.write(response.content)


if __name__ == '__main__':
    main(obj={})  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
