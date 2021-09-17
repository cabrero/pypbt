#!/usr/bin/env python3

from __future__ import annotations

import importlib
from pathlib import Path
import sys


def run_props(file: Path) -> None:
    parent = file.parent
    module_name = file.stem
    if parent != ".":
        sys.path.append(parent)
    module = importlib.import_module(module_name)
    for name in dir(module):
        if name.startswith("prop_"):
            prop = getattr(module, name)
            print(prop)
            prop()
            print()



if __name__ == "__main__":
    if len(sys.argv) != 2:
        cmd = Path(sys.argv[0]).name
        print(f"USAGE: {cmd} <props_file>")
        sys.exit(1)

    file = Path(sys.argv[1])
    if not file.exists():
        print(f"ERROR: File not found: {file}")
        sys.exit(1)

    run_props(file)

