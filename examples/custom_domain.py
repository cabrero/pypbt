#!/usr/bin/env python3

from __future__ import annotations
from fractions import Fraction
from itertools import islice
from typing import Iterator


from pypbt import domains


class FractionsDom(domains.Domain[Fraction]):
    def __iter__(self) -> Iterator[Fraction]:
        it = iter(domains.Int())
        # Another alternative would be to use two domains
        # The difference will be given by the heuristics of the domain generator
        while True:
            yield Fraction(next(it), next(it))

    def __str__(self) -> str:
        return f"{domains.D}:Fraction()"


class FractionsDomv2:
    def __iter__(self) -> Iterator[Fraction]:
        numerator = domains.Int()
        denominator = domains.Int(min_value= 1)
        for n, d in zip(numerator, denominator):
            yield Fraction(n, d)
            
    def __str__(self) -> str:
        return f"{domains.D}:Fraction() v2"


if __name__ == "__main__":
    doms = (
        FractionsDom(),
        FractionsDomv2(),
        domains.domain_expr(
            Fraction(n, d) for n, d in zip(domains.Int(), domains.Int(min_value= 1))
        ),
        domains.DomainPyObject(Fraction, domains.Int(), domains.Int(min_value= 1))
    )
    n_samples = 10
    for dom in doms:
        print(f"== Showing {n_samples} samples from domain: {dom} ==")
        print(", ".join(str(sample) for sample in islice(dom, n_samples)))
        print()

    

