#!/usr/bin/env python3

from __future__ import annotations

from itertools import islice

from pypbt import domains


Tree= domains.recursive(lambda Tree: (
        domains.Boolean() |
        domains.Tuple(Tree(), Tree())
    ))


Json = domains.recursive(lambda Json: (
    None |
    domains.Boolean() |
    domains.Int() |
    domains.List(Json()) |
    domains.Dict(domains.PyName(), Json())
))


def print_n_samples(dom: domains.Domain, n:int = 10) -> None:
    for sample in islice(dom, n):
        print(sample)

        
if __name__ == "__main__":
    for i in range(1000,1200):
        print(f"seed= {i}")
        domains.set_seed(i)
        print_n_samples(Tree())
        print()
        print_n_samples(Json())
        print()

