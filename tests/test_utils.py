from __future__ import annotations
from typing import Iterable

import pytest


from pypbt import domain


"""
Típicos test de unidad:

- Positivo: valor de entrada, valor de salida.

- Negativo: valor de entrada, excepción
"""
@pytest.mark.parametrize(
    "n, iterable, result",
    [
        (1, range(10), (0,)),
        (0, range(2), ()),
        (10, range(10), (0,1,2,3,4,5,6,7,8,9)),
    ]
)
def test_take_positive(n: int, iterable: Iterable, result: tuple):
    assert tuple(domain.take(n, iterable)) == result


@pytest.mark.parametrize(
    "n, iterable",
    [
        (11, range(10)),
    ]
)
def test_take_negative(n: int, iterable: Iterable):
    with pytest.raises(RuntimeError):
        tuple(domain.take(n, iterable))
