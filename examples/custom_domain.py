#!/usr/bin/env python3

from __future__ import annotations

import mimesis

from pypbt import domains

class ProgrammingLanguage(domains.Domain):
    def __iter__(self) -> Iterator:
        provider = mimesis.Development()
        while True:
            yield provider.programming_language()

    def __str__(self) -> str:
        return "ProgrammingLanguage()"


def print_n_samples(dom: domains.Domain, n:int = 10) -> None:
    for sample in domains.take(n, dom):
        print(sample)

if __name__ == "__main__":
    dom = ProgrammingLanguage()
    n_samples = 20
    print(f"Showing {n_samples} samples from domain {dom}")
    print_n_samples(dom, n_samples)

