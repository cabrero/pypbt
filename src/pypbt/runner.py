#!/usr/bin/env python3

from __future__ import annotations

import importlib
from pathlib import Path
import sys

from pypbt.quantifiers import is_qcproperty


def run_props(file: Path) -> None:
    parent = str(file.parent)
    module_name = file.stem
    if parent not in sys.path:
        sys.path.append(parent)
    module = importlib.import_module(module_name)
    for name in dir(module):
        obj = getattr(module, name)
        if is_qcproperty(obj):
            prop = obj
            try:
                # TODO: Truncate after n lines of predicate
                s = prop.get_source()
            except OSError:
                s = str(prop)
            print(s)
            for i, result in enumerate(prop(env= {}), start= 1):
                if result:
                    print(".", end= "", flush= True)
                else:
                    print("x")
                    print(f"After {i} tests" if i>1 else "After 1 test")
                    if result.exc is not None:
                        print(result.exc)
                    print(", ".join(f"{k} = {v}" for k,v in result.env.items()))
                    break
            else:
                print()
                print(f"Passed {i} tests" if i>1 else "Passed 1 test")
            print()


def main():
    if len(sys.argv) != 2:
        cmd = Path(sys.argv[0]).name
        print(f"USAGE: {cmd} <props_file>")
        sys.exit(1)

    file = Path(sys.argv[1])
    if not file.exists():
        print(f"ERROR: File not found: {file}")
        sys.exit(1)

    run_props(file)


if __name__ == '__main__':
    main()
