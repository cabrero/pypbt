from __future__ import annotations
from collections import Counter
from itertools import islice
import os
from typing import Callable


import pytest


from pypbt import domain


DEFAULT_N_SAMPLES = 1000


# data = list(factory, counter)
# factory: crea un dominio
# counter: crea un objeto counter para la lista de samples
#          P.e. las listas no son hashables y no se pueden usar directamente con Counter


domain_data = [
        (lambda: domain.Int(), Counter),
        
        (lambda: domain.PyName(), Counter),
        
        (lambda: domain.Tuple(domain.Int(), domain.Int(), domain.Int()), Counter),
        
        (lambda: domain.List(domain.Int()),
         lambda samples: Counter(map(tuple, samples))),
        
        (lambda: domain.Dict(domain.PyName(), domain.Int()),
         lambda samples: Counter(tuple(sample.items()) for sample in samples)),
        
        (lambda: (domain.Int() |
                  domain.PyName() |
                  domain.List(domain.Tuple(domain.Int(), domain.Int()))),
         lambda samples: Counter(tuple(sample) if type(sample) == list else sample
                                 for sample in samples)),
    ]


def domain_data_id_func(param):
    try:
        return str(param())
    except TypeError:
        return param

    
"""Las muestras son suficientemente aleatorias

Es imposible comprobar que las muestras sean realmente aleatorias para
un dominio infinito y muy difícil para un subconjunto. Para
simplificar, generamos una secuencia (¿con la longitud por defecto?) y
comprobamos que no se repite ningún objeto.

Para los dominios finitos pasamos. Si el número de muestras es mayor
que el tamaño del dominio, se tienen que repetir las muestras. En caso
contrario, la implementación del dominio concreto se tiene que ocupar
de barajar los objetos antes de iterar sobre ellos. Una vez barajados,
se cogen los $n$ primeros, con lo cual no es posible repetir.

Como no parece posible que no se repita ninguna muestra (al menos con el
módulo random de python), vamos a comprobar que el número de repeticiones
no supera un determinado %

TODO: En Ankh-Morpork (mundo imperativo, con efectos colaterales) igual
sí es buena idea que las muestras se repitan.

TODO: Este test a veces pasa, a veces falla. ¿ el 5% es poco ? ¿
existen algoritmos de pseudoaleatorios mejores ?
"""
@pytest.mark.xfail(os.environ.get('GITHUB_ACTIONS', False),
                   reason= "Ignore errors on Github Actions")
@pytest.mark.parametrize("domain_factory, counter_factory",
                         domain_data,
                         ids= domain_data_id_func)
def test_samples_are_random_enough(domain_factory: Callable, counter_factory: Callable):
    dom = domain_factory()
    print(dom)
    for n_samples in (100, 1000):
        samples = islice(dom, n_samples)
        counter = counter_factory(samples)
        repeated_samples = [sample for sample, count in counter.items() if count > 1]
        assert len(repeated_samples) / n_samples < (5/100)
    
    


"""
Si hacemos el metadomino
```
for d in domain.DomainSet():
    assert domain.is_domain(d)
```
"""


"""Las secuencias son reproducibles

Si partimos de la misma semilla, obtenemos la misma secuencia de
objetos.
"""
@pytest.mark.parametrize("domain_factory",
                         [domain_factory for domain_factory, _ in domain_data],
                         ids= domain_data_id_func)
def test_generation_is_reproducible(domain_factory: Callable):
    seed = domain.get_seed()
    domain.set_seed(seed)
    dom = domain_factory()
    print(dom, seed)
    # `islice` devuelve un generador, o sea un objeto perezoso.
    # hay que realizarlo ("desperezarlo") antes de cambiar la semilla.
    # Cosas que pasan con los efectos colaterales.¯\_(ツ)_/¯
    first_sequence = tuple(islice(dom, DEFAULT_N_SAMPLES))
    domain.set_seed(seed)
    dom = domain_factory()
    print(dom, seed)
    second_sequence = tuple(islice(dom, DEFAULT_N_SAMPLES))
    assert first_sequence == second_sequence


"""
Operador Unión. Comprobamos:

- Todas las muestras son de los dominios unidos.

- Hay muestras de todos los dominios.

- TODO: La proporción del número de muestras de cada dominio es
  correcta.
 
"""
def test_union_is_fair():
    dom = (domain.Int() |
           domain.PyName() |
           domain.List(domain.Tuple(domain.Int(), domain.Int())))
    samples = islice(dom, DEFAULT_N_SAMPLES)
    counter = Counter(type(sample) for sample in samples)
    n_int_samples = counter[int]
    n_pyname_samples = counter[str]
    n_list_samples = counter[list]
    assert n_int_samples + n_pyname_samples + n_list_samples == DEFAULT_N_SAMPLES
    assert n_int_samples > 1
    assert n_pyname_samples > 1
    assert n_list_samples > 1

    
"""El argumento `samples_limit`

El argumento realmente limita el número de samples que podemos obtener
de un dominio.

"""
def test_samples_limit():
    dom = domain.Int().that(samples_limit= 10)
    x = islice(dom, 100)
    assert len(list(x)) == 10


def test_domain_char_ascii():
    """El domino Char(ascii) sólo genera caracteres ascii.
    """
    dom = domain.Char(coding= 'ascii')
    for char in islice(dom, DEFAULT_N_SAMPLES):
        assert ord(char) < 256

        
def test_domain_char_ascii_printable():
    """El domino Char(ascii.printable) sólo genera caracteres ascii
    printables.

    """
    dom = domain.Char(coding= 'ascii.printable')
    for char in islice(dom, DEFAULT_N_SAMPLES):
        assert 8 < ord(char) < 127


def test_domain_char_utf8():
    """El dominio Char(utf-8) sólo genera caracters utf-8.
    """
    dom = domain.Char(coding= 'utf-8')
    for char in islice(dom, DEFAULT_N_SAMPLES):
        try:
            char.encode('utf-8')
        except UnicodeEncodeError:
            assert False, f"0x{ord(char):04x} is not a valid utf-8 codepoint"


def test_domain_str():
    """El dominio devuelve cadenas de caracteres de la longuitud
    especificada.

    """
    dom = domain.String(max_len= 78)
    for s in islice(dom, DEFAULT_N_SAMPLES):
        assert 0<= len(s) <= 78
