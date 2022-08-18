#!/usr/bin/env python3

from __future__ import annotations
from fractions import Fraction
from itertools import islice
from typing import Iterator


from pypbt import domains


class FractionsDom(domains.Domain[Fraction]):
    def __iter__(self) -> Iterator[Fraction]:
        it = iter(domains.Int())
        while True:
            yield Fraction(next(it), next(it))

    def __str__(self) -> str:
        return f"{domains.D}:Fraction()"
    

if __name__ == "__main__":
    dom = FractionsDom()
    n_samples = 20
    print(f"Showing {n_samples} samples from domain: {dom}")
    for item in islice(dom, n_samples):
        print(item)

