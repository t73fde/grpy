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

"""Setup script."""

import datetime
import os
import subprocess  # nosec
from typing import List

from setuptools import find_packages, setup

HEREDIR = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS_TXT = "requirements.txt"
VERSION_TXT = "VERSION.txt"


def open_local(filename: str, mode: str = "r"):
    """Open a file in this directory."""
    return open(os.path.join(HEREDIR, filename), mode)


def execute_command(args: List[str]) -> List[str]:
    """Execute a external command and return stdout as list of strings."""
    process = subprocess.run(args, stdout=subprocess.PIPE)  # nosec
    if process.returncode:
        return []
    return [line for line in process.stdout.decode('utf-8').split("\n")]


def create_requirements_txt() -> None:
    """Create file 'requirements.txt'."""
    try:
        with open_local("Pipfile.lock"):
            pass
    except FileNotFoundError:
        return

    pipenv_lines = execute_command(["pipenv", "lock", "-r"])
    if not pipenv_lines:
        return
    lines = [line for line in pipenv_lines[1:] if line]
    with open_local(REQUIREMENTS_TXT, "w") as req_file:
        req_file.write("### DO NOT EDIT! This file was generated.\n")
        req_file.write("\n".join(lines))
        req_file.write("\n")


def read_requires() -> List[str]:
    """Read file 'requirements.txt' and return its lines as a list."""
    with open_local(REQUIREMENTS_TXT) as req_file:
        return [
            line for line in (
                line.strip() for line in req_file.readlines())
            if not line.startswith("#")]


def create_version_txt() -> None:
    """Create version file."""
    try:
        with open_local(".git/HEAD"):
            pass
    except FileNotFoundError:
        return

    git_version_lines = execute_command([
        "git", "describe", "--always", "--dirty", "--long", "--tags", "--abbrev=16"])
    if not git_version_lines:
        return

    git_version = git_version_lines[0]
    with open_local(VERSION_TXT, "w") as version_file:
        version_file.write(git_version)
        version_file.write("\n")
        version_file.write(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
        version_file.write("\n")


if __name__ == "__main__":
    create_requirements_txt()
    create_version_txt()
    README = open_local("README.md").read()
    INSTALL_REQUIRES = read_requires()

    setup(
        name="grpy",
        description="Web Application to build groups / teams",
        long_description=README,
        version="2019.5.28",
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        install_requires=INSTALL_REQUIRES,
        python_requires='>=3.6',
        license="AGPL3",
        url="https://github.com/t73fde/grpy",
        author="Detlef Stern",
        author_email="detlef.stern@hs-heilbronn.de",
        keywords=["education", "gouping", "team-building"],
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Web Environment",
            "Framework :: Flask",
            "Intended Audience :: Education",
            "License :: OSI Approved :: "
            "GNU Affero General Public License v3 or later (AGPLv3+)",
            "Natural Language :: English",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Topic :: Education",
            "Topic :: Office/Business :: Scheduling",
            "Typing :: Typed",
        ],
        platforms=["Linux"],
    )
