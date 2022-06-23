from __future__ import annotations


import pytest


from pypbt import domain, quantifier


"""Para-todo encuentra el contraejemplo en dominios suficientemente finitos

Si la propiedad no es cierta, encuentra un contraejemplo. Si es
cierta, no encuentra el contraejemplo.

TODO: dominios más complejos
"""


def pred_false(x):
    return x > 4

@pytest.mark.parametrize(
    "iterable, pred",
    [ (range(100), lambda x: x > 4),
      ([[1,2], [3,9,0], [], [4,4,4,4]], lambda x: len(x) > 0),
    ]
)
def test_finds_counterexample(iterable, pred):
    dom = domain.domain(iterable, exhaustive= True)
    prop = quantifier.forall(x= dom)(pred)
    assert not all(result for _, result in zip(range(100), prop.qcproperty(env= {})))
    

"""La existencia es cierta

'Existe' encuentra el ejemplo que cumple la propiedad si y sólo si
existe. Como ya sabemos, existe sólo funciona con dominios suficientemente
finitos.
"""


"""Para-todo encuentra el contraejemplo en dominios no suficientemente finitos

No podemos comprobar esto, por que pueden hacer falta infinitas
ejecuciones hasta que encuentre el contraejemplo.

Pero podemos ejecutarlo con unas semillas determinadas con las que
sabemos que se genera, o no, el contraejemplo.
"""
