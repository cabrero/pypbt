#!/usr/bin/env python3

from __future__ import annotations

from pypbt import domain


Tree= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))


Json = domain.recursive(lambda Json: (
    domain.None_() |
    domain.Boolean() |
    domain.Int() |
    domain.List(Json()) |
    domain.Dict(domain.PyName(), Json())
))


def print_n_samples(dom: domain.Domain, n:int = 10) -> None:
    for sample in domain.take(n, dom):
        print(sample)

if __name__ == "__main__":
    for i in range(1000,1200):
        print(f"seed= {i}")
        domain.set_seed(i)
        print_n_samples(Tree())
        print()
        print_n_samples(Json())
        print()

