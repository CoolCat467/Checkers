#!/usr/bin/env python3

"""TITLE - DESCRIPTION."""

# Programmed by CoolCat467

from __future__ import annotations

# TITLE - DESCRIPTION
# Copyright (C) 2025  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "TITLE"
__author__ = "CoolCat467"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"

import sys
from pathlib import Path
from typing import Final

import tomllib

KEY: Final = "tool.hatch.build.targets.wheel.hooks.mypyc"

HERE: Final = Path(__file__).absolute().parent
ROOT: Final = HERE.parent
PYPROJECT_TOML: Final = ROOT / "pyproject.toml"


def run() -> int:
    """Run program."""
    assert (ROOT / "LICENSE").exists()

    with PYPROJECT_TOML.open("rb") as fp:
        pyproject = tomllib.load(fp)

    temp: dict[str, object] = pyproject
    for key in KEY.split("."):
        temp = temp[key]
    mypyc_data = temp

    exclude = [f"--exclude={e!r}" for e in sorted(mypyc_data["exclude"])]

    command = (
        # "MYPYC_MULTI_FILE=1",
        "mypyc",
        *exclude,
        "-a 'warnings.html'",
    )

    print(" ".join(command))

    return 0


if __name__ == "__main__":
    sys.exit(run())
