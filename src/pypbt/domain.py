from __future__ import annotations

from dataclasses import dataclass, field, InitVar, replace
import random
import string
from typing import Callable, Iterable, Iterator, Optional, Protocol, Union
from typing import runtime_checkable

# TODO: ¿ queremos/podemos hacer que la semilla no sea una variable global del módulo ?

seed = random.randint(0, 10000)
_random = random.Random()
_random.seed(seed)


def get_seed():
    return seed


def set_seed(new_seed):
    global seed
    seed = new_seed
    _random.seed(new_seed)

    
def take(n: int, iterable: Iterable) -> Iterator:
    # No sé porqué está función no está en la stdlib
    it = iter(iterable)
    for _ in range(n):
        yield next(it)


#---------------------------------------------------------------------------
# Tipos
#---------------------------------------------------------------------------

# Interface de los objetos que representan un dominio.
@runtime_checkable
class Domain(Protocol):
    is_exhaustive: bool
    def as_exhaustive(self, exhaustive: bool) -> Domain: ...
    def __iter__(self) -> Iterator: ...
    def __or__(self, other: 'DomainCoercible') -> Domain: ...
    def __ror__(self, other: 'DomainCoercible') -> Domain: ...

# Soporte para azúcar sintático. En los cuantificadores se puede usar
# un objeto iterable en lugar de un objeto Domain. La librería se
# encarga de quitar el azúcar.
DomainCoercible = Union['Domain', 'RecSubDomain', Iterable]


# Entorno. Guarda las ligaduras de variables.
Env = dict[str, DomainCoercible]


def is_domain(arg: Any) -> bool:
    return isinstance(arg, Domain)


def desugar_domain(arg: DomainCoercible, exhaustive: Optional[bool]= None) -> Domain:
    if is_domain(arg):
        return arg if exhaustive is None else arg.as_exhaustive(exhaustive)
    elif isinstance(arg, Iterable):
        return ExhaustiveIterableAsDomain(arg) if exhaustive else IterableAsDomain(arg)
    else:
        # TODO: Otras formas de declarar un dominio, p.e.
        #    - tipos básicos: int, str, ...
        #    - función generadora
        raise TypeError(f"Cannot use {arg} as a domain here")


def domain(d: Any, exhaustive: bool= False) -> Domain:
    return desugar_domain(d, exhaustive)

            
RecStepFun = Callable[['RecDomainStep'], 'Domain']


def recursive(fun: RecStepFun, **props) -> RecDomain:
    def rec_dom_factory():
        return RecDomain(fun, **props)
    return rec_dom_factory


# ---------------------------------------------------------------------------
# Implementación de dominios
# ---------------------------------------------------------------------------
"""
Conocemos tres estrategias principales para generar la lista de
samples:

- Naïf. A partir de una semilla, generar una secuencia de números
  pseudoaleatorios y usar estos números para seleccionar lo elementos
  del conjunto.

- TODO: A mayores del caso anterior, usar heurísticas para incluir
  elementos que se sabe que son "problemáticos" en las pruebas, por
  ejemplo los zeros.

- TODO: Sized generation. Los elementos se eligen en orden creciente
  de tamaño y complejidad.  
"""

class DomainAbs(Domain):
    is_exhaustive : bool = False

    def as_exhaustive(self, exhaustive: bool) -> Domain:
        if exhaustive:
            raise TypeError(f"domain cannot be marked as exhaustive: {self}")
        return self
    
    def exhaustive_iterator(self) -> Iterator:
        raise TypeError(f"domain is not exhaustive: {self}")
    
    def __iter__(self) -> Iterator:
        raise NotImplementedError()
    
    def __str__(self) -> str:
        return f"Domain()"

    def __or__(self, other: DomainCoercible) -> Domain:
        return DomainUnion(self, other)
    
    def __ror__(self, other: DomainCoercible) -> Domain:
        return DomainUnion(other, self)


class RecDomain(DomainAbs):
    def __init__(self, fun: RecStepFun, sub_i: int= 0, max_depth:int= 6):
        self.fun = fun
        self.sub_i = sub_i
        self.max_depth = max_depth

    def __iter__(self) -> Iterator:
        return self._samples(self.sub_i + 1)

    def _samples(self, sub_i: int) -> Iterator:
        if sub_i > self.max_depth:
            raise RecursionError()
        subdom = self.fun(lambda max_depth= 6: RecDomain(self.fun, sub_i= sub_i, max_depth= max_depth))
        yield from subdom

    def __str__(self) -> str:
        return f"RecDomain_{self.sub_i}({id(self)})"
    

class IterableAsDomain(DomainAbs):
    def __init__(self, iterable: Iterable):
        self.iterable = iterable

    def __iter__(self) -> Iterator:
        return iter(self.iterable)

    def __str__(self) -> str:
        return f"Domain({self.iterable})"

    
class ExhaustiveIterableAsDomain(DomainAbs):
    is_exhaustive : bool = True

    def __init__(self, iterable: Iterable):
        self.iterable = tuple(iterable)

    def as_exhaustive(self, exhaustive: bool) -> Domain:
        return self if exhaustive else IterableAsDomain(self.iterable)

    def __iter__(self) -> Iterator:
        # Importante: barajar los items por si acaso el número de muestras que
        # se cogen del dominio es menor que el tamaño del iterable, para evitar
        # devolver siempre los $n$ primeros.
        samples = _random.sample(self.iterable, len(self.iterable))
        while True:
            yield from samples
    
    def exhaustive_iterator(self) -> Iterator:
        return iter(self.iterable)
    
    def __str__(self):
        return f"ExhaustiveDomain({self.iterable})"


class Sublists(DomainAbs):
    def __init__(self, l: list, exhaustive: bool= False):
        self.l = l
        self.is_exhaustive = exhaustive

    def __iter__(self) -> Iterator:
        yield []
        n = len(self.l)
        while True:
            a = _random.randint(0, n)
            b = _random.randint(0, n)
            a, b = (a, b + 1) if a <= b else (b, a + 1)
            yield self.l[a:b]
        
    def exhaustive_iterator(self) -> Iterator:
        if not self.is_exhaustive:
            raise RuntimeError("Domain is not marked as exhaustive")
        yield []
        n = len(self.l)
        for a in range(n):
            for b in range(a, n):
                yield self.l[a:b+1]

    def __str__(self):
        return f"Sublists({self.l}"
        

class Int(DomainAbs):
    def __init__(self,
                 min_value: Optional[int]= None,
                 max_value: Optional[int]= None):
        self.min_value = min_value or 0
        self.max_value = max_value or 10_000

    def __iter__(self) -> Iterator:
        min_value = self.min_value
        max_value = self.max_value
        if min_value <= 0 <= max_value:
            yield 0
        while True:
            yield _random.randint(min_value, max_value)

    def __str__(self):
        return f"Int({self.min_value}, {self.max_value})"


class PyName(DomainAbs):
    def __init__(self, min_len: Optional[int]= 1, max_len: Optional[int]= 8):
        if min_len and min_len < 1:
            raise ValueError("min len ({min_len}) must be greater than zero. No python names allowed with less than one char")
        if max_len < min_len:
            raise ValueError(f"max len ({max_len}) cannot be smaller than min len ({min_len})")
        self.min_len = min_len
        self.max_len = max_len
        
    # TODO: Generar nombres de variables más adecuados
    def __iter__(self) -> Iterator:
        n = self.max_len - self.min_len
        head_chars = ['_', *string.ascii_letters]
        tail_chars = [*head_chars, *string.digits]
        
        while True:
            chars = [
                _random.choice(head_chars),
                *_random.choices(tail_chars, k= n)
            ]
            
            yield "".join(chars)

    def __str__(self) -> str:
        return f"PyName()"
    
            
class List(DomainAbs):
    def __init__(self,
                 domain_obj: DomainCoercible,
                 min_len: Optional[int]= 0,
                 max_len: Optional[int]= 20):
        self.domain = desugar_domain(domain_obj)
        self.min_len = min_len
        self.max_len = max_len
        
    def __iter__(self) -> Iterator:
        min_len = self.min_len
        max_len = self.max_len
        if min_len == 0:
            yield []
            min_len = 1
        while True:
            n = _random.randint(min_len, max_len)
            yield list(take(n, self.domain))

    def __str__(self):
        return f"List({self.domain})"

    
class Tuple(DomainAbs):
    def __init__(self, *domain_objs: tuple(DomainCoercible,...)):
        self.domains = [desugar_domain(d) for d in domain_objs]

    def __iter__(self) -> Iterator:
        iterators = [iter(domain) for domain in self.domains]
        while True:
            yield tuple(next(it) for it in iterators)

    def exhaustive_iterator(self, env: Env) -> Iterator:
        iterators = [domain.exhaustive_iterator(env) for domain in self.domains]
        return zip(*iterators)

    def __str__(self):
        items = ", ".join(map(str, self.domains))
        return f"Tuple({items})"


class Dict(DomainAbs):
    def __init__(self, key_domain: DomainCoercible, value_domain: DomainCoercible, min_len: int= 0, max_len: int= 20):
        self.key_domain = desugar_domain(key_domain)
        self.value_domain = desugar_domain(value_domain)
        self.min_len = min_len
        self.max_len = max_len

    def __iter__(self) -> Iterator:
        min_len = self.min_len
        max_len = self.max_len
        if min_len == 0:
            yield {}
            min_len = 1
        key_it = iter(self.key_domain)
        value_it = iter(self.value_domain)
        while True:
            n = _random.randint(min_len, max_len)
            yield { next(key_it): next(value_it) for _ in range(n) }

    def __str__(self):
        return f"Dict({self.key_domain}, {self.value_domain})"
        
        
class Boolean(DomainAbs):
    is_exhaustive : bool = True

    def as_exhaustive(self, exhaustive: bool) -> Domain:
        if not exhaustive:
            raise TypeError(f"do no mark boolean as not exhaustive: {self}")
        return self
    
    def __iter__(self) -> Iterator:
        while True:
            yield _random.choice([True, False])

    def exhaustive_iterator(self) -> Iterator:
        yield False
        yield True

    def __str__(self):
        return f"Boolean()"


class None_(DomainAbs):
    is_exhaustive : bool = True

    def as_exhaustive(self, exhaustive: bool) -> Domain:
        if not exhaustive:
            raise TypeError(f"do no mark None as not exhaustive: {self}")
        return self
        
    def __iter__(self) -> Iterator:
        while True:
            yield None

    def exhaustive_iterator(self) -> Iterator:
        yield None
        
    def __str__(self) -> str:
        return f"None()"
    

class DomainUnion(DomainAbs):
    a: InitVar[Domain]
    b: InitVar[Domain]
    domains: list[Domain]= field(init= False)
    is_exhaustive: bool= field(init= False)
    
    def __init__(self, a: DomainCoercible, b: DomainCoercible):
        if isinstance(a, DomainUnion):
            a = a.domains
        else:
            a = [desugar_domain(a)]
        if isinstance(b, DomainUnion):
            b = b.domains
        else:
            b = [desugar_domain(b)]
        self.domains = [*a, *b]
        self.is_exhaustive = all(d.is_exhaustive for d in self.domains)

    def as_exhaustive(self, exhaustive: bool) -> Domain:
        raise TypeError(f"can not mark union as exhaustive: {self}")
            
    def __iter__(self) -> Iterator:
        iterators = [iter(domain) for domain in self.domains]
        n = len(iterators)
        while True:
            idxs = _random.sample(range(n), k= n)
            for i in idxs:
                try:
                    yield next(iterators[i])
                    break
                except RecursionError:
                    # Si alguna alternativa llega al nivel de
                    # recursión máximo, la descartamos y reiniciamos
                    # el iterador para la siguiente
                    iterators[i] = iter(self.domains[i])
            else:
                raise RecursionError(f"max recursion at {self}")

    # TODO: ¿ Cómo detectar si es suficientemente finito ?
    #       ¿ La unión de dos dominios suficientemente finitos puede dar lugar a uno no suficientemente finito ?
    
    def __str__(self):
        return " | ".join(map(str, self.domains))




            



