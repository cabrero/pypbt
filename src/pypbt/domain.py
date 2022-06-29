from __future__ import annotations

from dataclasses import dataclass, field, InitVar, replace
import itertools
import random
import string
from typing import Callable, Generic, Iterable, Iterator, Optional, Protocol, Union, TypeVar
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

# Soporte para azúcar sintático. En los cuantificadores se puede usar
# un objeto iterable en lugar de un objeto Domain. La librería se
# encarga de quitar el azúcar.
DomainCoercible = Union['Domain', 'RecSubDomain', Iterable]


# Entorno. Guarda las ligaduras de variables.
Env = dict[str, DomainCoercible]


def is_domain(arg: Any) -> bool:
    return isinstance(arg, Domain)


def desugar_domain(arg: DomainCoercible,
                   is_exhaustible: Optional[bool]= None) -> Domain:
    if is_domain(arg):
        if is_exhaustible is not None:
            raise TypeError("cannot change the attribute is_exhaustible of a domain")
        return arg
    elif isinstance(arg, Iterable):
        return ExhaustibleIterableAsDomain(arg) if is_exhaustible else IterableAsDomain(arg)
    else:
        # TODO: Otras formas de declarar un dominio, p.e.
        #    - tipos básicos: int, str, ...
        #    - función generadora
        raise TypeError(f"Cannot use {arg} as a domain here")


def domain(d: Any, is_exhaustible: Optional[bool]= None) -> Domain:
    return desugar_domain(d, is_exhaustible= is_exhaustible)

            
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

T = TypeVar('T')
class Domain(Generic[T]):
    """Domain abstract class

    This is the base class for every `Domain`. It includes some
    operations like _union_.

    It also includes the method `that` to decorate a domain with extra
    funcionality. For example: limiting the number of samples that it
    will generate.

    By default, domains are non exhaustibles. The attribute
    `is_exhaustible = False`.  When a domain is or may be exhaustible,
    the corresponding class has to explicitly change the attribute
    `is_exhaustible` and, if neccessary, add a parameter to the
    `__init__` function. And, of course, implement the exhaustible
    iterator `exhaustible_iter`.

    """
    is_exhaustible: bool = False
    
    @property
    def exhaustible(self) -> Iterator[T]:
        """Returns an iterator that can be exhausted.

        """
        if not self.is_exhaustible:
            raise TypeError(f"cannot exhaust domain {self}")
        else:
            return self.exhaustible_iter()
            
    def __iter__(self) -> Iterator[T]:
        """Returns the cannonical iterator for a domain.

        This is the magic method of any python iterable. The returned
        iterator is the pbt cannonical one. This iterator will pick
        and yield random samples from the domain.

        """
        raise NotImplementedError()

    def exhaustible_iter(self) -> Iterator[T]:
        """Returns the non-cannonical, exhaustible iterator for a domain.

        The returned iterator is not the pbt cannonical one. Instead
        of picking random samples, this iterator will pick and yield
        all the elements of the domain.

        NOTE that most domains can not be exhausted because the number
        of elements is too big, generating them is too costly, or,
        most of the cases, the number of elements is infinite.

        WARNING do not use this method directly, instead use the
        property `exhaustible`.

        """
        raise NotImplementedError()
    
    def __or__(self, other: DomainCoercible) -> Domain:
        return DomainUnion(self, other)
    
    def __ror__(self, other: DomainCoercible) -> Domain:
        return DomainUnion(other, self)

    def that(self, samples_limit: int) -> Domain:
        """Decorate this domain

        Returns a decorator of this domain. The decorator will change
        the behaviour of the domain based on the given parameters.

        Parameters
        ----------
        samples_limit : int
            max number of samples the domain generates

        Returns
        -------
        Domain
            the decorated domain
        """
        return DomainLimit(self, samples_limit)


# Decorator
class DomainLimit(Domain):
    def __init__(self, delegate: Domain, samples_limit: int):
        self.delegate = delegate
        self.samples_limit = samples_limit

    def __iter__(self) -> Iterator[T]:
        return itertools.islice(self.delegate, self.samples_limit)


    

class RecDomain(Domain):
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
    

class IterableAsDomain(Domain):
    def __init__(self, iterable: Iterable):
        self.iterable = iterable

    def __iter__(self) -> Iterator:
        return iter(self.iterable)

    def __str__(self) -> str:
        return f"Domain({self.iterable})"

    
class ExhaustibleIterableAsDomain(Domain):
    is_exhaustible: bool = True

    def __init__(self, iterable: Iterable):
        self.iterable = tuple(iterable)

    def as_exhaustible(self, exhaustible: bool) -> Domain:
        return self if exhaustible else IterableAsDomain(self.iterable)

    def __iter__(self) -> Iterator:
        # Importante: barajar los items por si acaso el número de muestras que
        # se cogen del dominio es menor que el tamaño del iterable, para evitar
        # devolver siempre los $n$ primeros.
        samples = _random.sample(self.iterable, len(self.iterable))
        while True:
            yield from samples
    
    def exhaustible_iter(self) -> Iterator:
        return iter(self.iterable)
    
    def __str__(self):
        return f"ExhaustibleDomain({self.iterable})"


class Sublists(Domain):
    def __init__(self, l: list, is_exhaustible: bool= False):
        self.l = l
        self.is_exhaustible = is_exhaustible
        
    def __iter__(self) -> Iterator[list]:
        yield []
        n = len(self.l)
        while True:
            a = _random.randint(0, n)
            b = _random.randint(0, n)
            a, b = (a, b + 1) if a <= b else (b, a + 1)
            yield self.l[a:b]
        
    def exhaustible_iter(self) -> Iterator[list]:
        if not self.is_exhaustible:
            raise RuntimeError("Domain is not marked as exhaustible")
        yield []
        n = len(self.l)
        for a in range(n):
            for b in range(a, n):
                yield self.l[a:b+1]


@dataclass(frozen= True)
class Int(Domain):
    min_value: int = 0
    max_value: int = 10_000
    
    def __iter__(self) -> Iterator[int]:
        min_value = self.min_value
        max_value = self.max_value
        if min_value <= 0 <= max_value:
            yield 0
        while True:
            yield _random.randint(min_value, max_value)


class PyName(Domain):
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
    

@dataclass(frozen= True)
class List(Domain):
    domain_obj: InitVar[DomainCoercible] = None
    min_len: Optional[int] = field(default= 0, kw_only= True)
    max_len: Optional[int] = field(default= 20, kw_only= True)
    domain: Domain = field(init= False)

    def __post_init__(self, domain_obj: DomainCoercible):
        super().__setattr__('domain', desugar_domain(domain_obj))
        
    def __iter__(self) -> Iterator[list]:
        min_len = self.min_len
        max_len = self.max_len
        if min_len == 0:
            yield []
            min_len = 1
        while True:
            n = _random.randint(min_len, max_len)
            yield list(take(n, self.domain))

    
class Tuple(Domain):
    def __init__(self, *domain_objs: tuple(DomainCoercible,...)):
        self.domains = [desugar_domain(d) for d in domain_objs]

    def __iter__(self) -> Iterator:
        iterators = [iter(domain) for domain in self.domains]
        while True:
            yield tuple(next(it) for it in iterators)

    def exhaustible_iter(self, env: Env) -> Iterator:
        if any(not domain.is_exhaustible for domain in self.domains):
            raise TypeError(f"not every element is exhaustible in {self}")
        iterators = [domain.exhaustible_iter(env) for domain in self.domains]
        return zip(*iterators)

    def __str__(self):
        items = ", ".join(map(str, self.domains))
        return f"Tuple({items})"


class Dict(Domain):
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
        
        
class Boolean(Domain):
    is_exhaustible : bool = True

    def as_exhaustible(self, exhaustible: bool) -> Domain:
        if not exhaustible:
            raise TypeError(f"do no mark boolean as not exhaustible: {self}")
        return self
    
    def __iter__(self) -> Iterator:
        while True:
            yield _random.choice([True, False])

    def exhaustible_iter(self) -> Iterator:
        yield False
        yield True

    def __str__(self):
        return f"Boolean()"


class None_(Domain):
    is_exhaustible : bool = True

    def as_exhaustible(self, exhaustible: bool) -> Domain:
        if not exhaustible:
            raise TypeError(f"do no mark None as not exhaustible: {self}")
        return self
        
    def __iter__(self) -> Iterator:
        while True:
            yield None

    def exhaustible_iter(self) -> Iterator:
        yield None
        
    def __str__(self) -> str:
        return f"None()"
    

class DomainUnion(Domain):
    a: InitVar[Domain]
    b: InitVar[Domain]
    domains: list[Domain]= field(init= False)
    is_exhaustible: bool= field(init= False)
    
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
        self.is_exhaustible = all(d.is_exhaustible for d in self.domains)

    def as_exhaustible(self, exhaustible: bool) -> Domain:
        raise TypeError(f"can not mark union as exhaustible: {self}")
            
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




            



