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

import os
import subprocess  # nosec
from typing import List

from setuptools import find_packages, setup

HEREDIR = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS_TXT = "requirements.txt"


def open_local(filename: str, mode: str = "r"):
    """Open a file in this directory."""
    return open(os.path.join(HEREDIR, filename), mode)


def create_requirements_txt() -> None:
    """Create file 'requirements.txt'."""
    try:
        with open_local("Pipfile.lock"):
            pass
    except FileNotFoundError:
        print("NOLO")
        return

    process = subprocess.run(  # nosec
        ["pipenv", "lock", "-r"], stdout=subprocess.PIPE)
    if process.returncode:
        print("RETC", process.returncode)
        return
    lines = [line for line in process.stdout.decode('utf-8').split("\n")[1:] if line]
    print("LINE", lines)
    with open_local(REQUIREMENTS_TXT, "w") as req_file:
        req_file.write("\n".join(lines))
        req_file.write("\n")


def read_requires() -> List[str]:
    """Read file 'requirements.txt' and return its lines as a list."""
    with open_local(REQUIREMENTS_TXT) as req_file:
        return [line.strip() for line in req_file.readlines()]


if __name__ == "__main__":
    create_requirements_txt()
    README = open_local("README.md").read()
    INSTALL_REQUIRES = read_requires()

    setup(
        name="grpy",
        description="Web Application to build groups / teams",
        long_description=README,
        version="0.0.1",
        packages=find_packages(),
        install_requires=INSTALL_REQUIRES,
        python_requires='>=3.6',
        license="AGPL3",
        url="https://gitlab.win.hs-heilbronn.de/kreuz/grpy",
        author="Detlef Stern",
        author_email="detlef.stern@hs-heilbronn.de",
        keywords="education gouping team-building",
        classifiers=[
            "Development Status :: 1 - Planning",
            "Environment :: Web Environment",
            "Framework :: Flask",
            "Intended Audience :: Education",
            "License :: OSI Approved :: "
            "GNU Affero General Public License v3 or later (AGPLv3+)",
            "Programming Language :: Python :: 3.7",
            "Topic :: Education",
        ],
    )
