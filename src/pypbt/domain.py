from __future__ import annotations

from dataclasses import dataclass, field, InitVar
import inspect
from itertools import islice
import random
import string
from typing import (
    Any,
    Callable,
    Generator,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    Union,
    Sized,
    TypeVar
)
import unicodedata


# --------------------------------------------------------------------------------------
# Pseudo random
# --------------------------------------------------------------------------------------
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

    
# --------------------------------------------------------------------------------------
# Syntax sugar
# --------------------------------------------------------------------------------------

# Actually, any python object could be coerced into a Domain.
# See fun `domain_expr`
"""Any syntax sugared expression defining a Domain.

When such an expression is used where the library expects a Domain, it is 
automatically coerced into the Domain it defines.

To explicitly coerce it, a.k.a as desugaring it, you should use the function
[domain_expr].
"""
DomainCoercible = Any


def domain_expr(arg: DomainCoercible, is_exhaustible: Optional[bool]= None) -> Domain:
    """Desugar domain expressions

    Converts any expression declaring a domain into a Domain object.
    The options are:

    - If arg is already a Domain object, returns it. Parameters are
      not allowed.

    - If arg is any python iterable, returns a Domain object whose
      elements are the items in the iterable. The programmer may mark
      the domain as exhaustible when neccessary.

    - If arg is a generator function, equivalent to iterable, taking
      the elements from the generator returned by the function.

    - If arg is any other python object, returns a Domain containing
      only one element: arg.

    """
    if is_domain(arg):
        if is_exhaustible is not None:
            raise TypeError("cannot change the attribute is_exhaustible of a domain")
        return arg
    elif isinstance(arg, Iterable):
        return DomainFromIterable(arg, is_exhaustible= is_exhaustible or False)
    elif inspect.isgeneratorfunction(arg):
        return DomainFromGeneratorFun(arg,  is_exhaustible= is_exhaustible or False)
    else:
        return DomainSingleton(arg)
    # TODO: Otras formas de declarar un dominio, p.e.
    #    - tipos básicos: int, str, ...
    #    - función generadora

            
# --------------------------------------------------------------------------------------
# Domain base class
# --------------------------------------------------------------------------------------
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

    ## Exhaustible vs non-exhaustible
    By default, domains are non exhaustibles. Thus, their attribute
    `is_exhaustible = False` and they do not implement any exhaustible
    iterator. Exhaustible Domains set that attribute to `True`
    themselves. When a domain may be exhaustible, includes a parameter
    in the `__init__` function. And, of course, implements the
    exhaustible iterator.

    """
    is_exhaustible: bool = False
    
    @property
    def exhaustible(self) -> Iterator[T]:
        """Returns an iterator that can be exhausted.

        The Domain must be marked as exhaustible. The library cannot
        infer whether a Domain is exhaustible.

        !!! warning

            Forcing the exhaustible attribute on a Domain that does
            not implement the exhaustible iterator will result in an
            exception when trying to use this property.

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
            max number of samples the domain generates. See [DomainLimit]

        Returns
        -------
        Domain
            the decorated domain
        """
        return DomainLimit(self, samples_limit)

    
def is_domain(arg: Any) -> bool:
    return isinstance(arg, Domain)


#--------------------------------------------------------------------------------------
# Domain decorators
#--------------------------------------------------------------------------------------
class DomainLimit(Domain):
    """Modify a Domain in order to limit the number of generated samples.

    Parameters
    ----------
    samples_limit : int
        max number of samples each iterator will yield
    """
    def __init__(self, delegate: Domain, samples_limit: int):
        self.delegate = delegate
        self.samples_limit = samples_limit

    def __iter__(self) -> Iterator[T]:
        return islice(self.delegate, self.samples_limit)


# --------------------------------------------------------------------------------------
# Composition of Domains
# --------------------------------------------------------------------------------------
class DomainUnion(Domain):
    def __init__(self, a: DomainCoercible, b: DomainCoercible):
        if isinstance(a, DomainUnion):
            a = a.domains
        else:
            a = [domain_expr(a)]
        if isinstance(b, DomainUnion):
            b = b.domains
        else:
            b = [domain_expr(b)]
        self.domains = [*a, *b]
        # TODO: La unión de dos dominios exhaustibles pueden ser
        # demasiado grande para seguir siendo considerada
        # exhaustible. ¿ Cómo gestionamos esto ?
        self.is_exhaustible = all(d.is_exhaustible for d in self.domains)

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

    # TODO: ¿ Cómo detectar si es suficientemente finito ?  ¿ La unión
    #       de dos dominios suficientemente finitos puede dar lugar a
    #       uno no suficientemente finito ?
    
    def __str__(self):
        return " | ".join(map(str, self.domains))


# --------------------------------------------------------------------------------------
# Domain recursive
# --------------------------------------------------------------------------------------
RecStepFun = Callable[['RecDomain'], Domain]


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
        subdom = self.fun(
            lambda max_depth= 6: RecDomain(self.fun, sub_i= sub_i, max_depth= max_depth)
        )
        yield from subdom

    def __str__(self) -> str:
        return f"RecDomain_{self.sub_i}({id(self)})"


def recursive(fun: RecStepFun, **props) -> RecDomain:
    def rec_dom_factory():
        return RecDomain(fun, **props)
    return rec_dom_factory


# --------------------------------------------------------------------------------------
# Domains of simple objects
# --------------------------------------------------------------------------------------
class DomainSingleton(Domain):
    is_exhaustible = True
    
    def __init__(self, element: Any):
        self.element = element

    def __iter__(self) -> Iterator:
        element = self.element
        while True:
            yield element

    def exhaustible_iter(self) -> Iterator:
        yield self.element

    def __str__(self) -> str:
        return f"Dom({self.element})"
    

@dataclass(frozen= True)
class Int(Domain[int]):
    min_value: int = 0
    max_value: int = 10_000
    
    def __iter__(self) -> Iterator[int]:
        min_value = self.min_value
        max_value = self.max_value
        if min_value <= 0 <= max_value:
            yield 0
        while True:
            yield _random.randint(min_value, max_value)


# TODO: Nombre más adecuado para el dominio.
#       Son los míticos nombres de variables, funciones, ...
#       No es algo específico de python. Suele ser la misma
#       sintáxis en mucho lenguajes.
class PyName(Domain[str]):
    def __init__(self, min_len: Optional[int]= 1, max_len: Optional[int]= 8):
        if min_len and min_len < 1:
            raise ValueError(
                f"min len ({min_len}) must be greater than zero."
                f" No python names allowed with less than one char"
            )
        if max_len < min_len:
            raise ValueError(
                f"max len: {max_len} cannot be smaller than min len: {min_len}"
            )
        self.min_len = min_len
        self.max_len = max_len
        
    # TODO: Generar nombres de variables más adecuados
    def __iter__(self) -> Iterator[str]:
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
    

class Boolean(Domain[bool]):
    is_exhaustible: bool = True

    def __iter__(self) -> Iterator[bool]:
        while True:
            yield _random.choice([True, False])

    def exhaustible_iter(self) -> Iterator[bool]:
        yield False
        yield True

    def __str__(self):
        return f"Boolean()"


@dataclass(frozen= True, kw_only= True)
class Char(Domain):
    coding: str = 'utf-8'  # 'utf-8', 'ascii', 'ascii.printable'

    def __iter__(self) -> Iterator[str]:
        if self.coding == 'ascii.printable':
            samples = string.printable
            while True:
                yield _random.choice(samples)
        elif self.coding == 'ascii':
            while True:
                yield chr(_random.randint(0, 255))
        elif self.coding == 'utf-8':
            # Opción desechada: listar los intervalos de codepoints válidos y generar uno
            # dentro del intervalo.
            # Para grandes números, parece (no lo hemos comprobado) más eficiente generar
            # al azar y rechazar los que sean inválidos.
            while True:
                char = chr(_random.randint(0x20, 0xE007f))
                if unicodedata.category(char)[0] != 'C':
                    yield char
        else:
            raise ValueError(f"unkown character coding: {self.coding}")
                          
        
@dataclass(frozen= True, kw_only= True)
class String(Domain):
    coding: str = 'utf-8' # 'utf-8', 'ascii', 'ascii.printable'
    min_len: int = 0
    max_len: int = 80

    def __iter__(self) -> Iterator[str]:
        min_len = self.min_len
        max_len = self.max_len
        if min_len == 0:
            yield ''
            min_len = 1
        dom_char = Char(coding= self.coding)
        while True:
            yield "".join(islice(dom_char, _random.randint(min_len, max_len)))


# --------------------------------------------------------------------------------------
# Domains of aggregated objects
# --------------------------------------------------------------------------------------
class DomainFromIterable(Domain):
    def __init__(self, iterable: Iterable, is_exhaustible: bool):
        self.iterable = iterable
        self.is_exhaustible = is_exhaustible

    def __iter__(self) -> Iterator:
        if not self.is_exhaustible:
            yield from self.iterable
        else:
            # Importante: barajar los items por si acaso el número de muestras que
            # se cogen del dominio es menor que el tamaño del iterable, para evitar
            # devolver siempre los $n$ primeros.
            samples = self.iterable
            if not isinstance(samples, Sequence):
                # Por ejemplo: un generator object es un Iterable
                # Pero la función random.sample sólo admite Sequence como
                # parámetro (ver doc.)
                samples = tuple(samples)
            samples = _random.sample(samples, len(samples))
            while True:
                yield from samples

    def exhaustible_iter(self) -> Iterator:
        return iter(self.iterable)


class DomainFromGeneratorFun(Domain):
    def __init__(self, fun: Callable, is_exhaustible: bool):
        self.fun = fun
        self.is_exhaustible = is_exhaustible

    def __iter__(self) -> Iterator:
        generator = self.fun()
        if not self.is_exhaustible:
            yield from generator
        else:
            # Importante: barajar los items por si acaso el número de muestras que
            # se cogen del dominio es menor que el tamaño del iterable, para evitar
            # devolver siempre los $n$ primeros.
            samples = tuple(generator)
            samples = _random.sample(samples, len(samples))
            while True:
                yield from samples

    def exhaustible_iter(self) -> Iterator:
        return self.fun()
    

class Tuple(Domain):
    """Domain of n-tuples.

    Implements the sum, not the product.
    I.e. `tuple(Dom([1,2,...]),Dom(['a','b',...]))`
    may yield: `(1,'b'), (2,'a')`, but not: `(1,'a'),(1,'b'),(2,'a'),(2,'b')`.

    Note that it is not possible to implement the product of
    non-exhaustible domains.
    """
    def __init__(self, *domain_objs: tuple(DomainCoercible, ...)):
        self.domains = [domain_expr(d) for d in domain_objs]

    def __iter__(self) -> Iterator:
        iterators = [iter(domain) for domain in self.domains]
        while True:
            yield tuple(next(it) for it in iterators)

    def exhaustible_iter(self) -> Iterator:
        if any(not domain.is_exhaustible for domain in self.domains):
            raise TypeError(f"not every element is exhaustible in {self}")
        iterators = [domain.exhaustible for domain in self.domains]
        # TODO: si un dominio es más grande que otro,
        #       ¿ nos vale este comportamiento  o queremos implementar otros ?
        # TODO: ¿ es interesante implementar el producto de exhaustibles ?
        return zip(*iterators)

    def __str__(self):
        items = ", ".join(map(str, self.domains))
        return f"Tuple({items})"


@dataclass(frozen= True)
class List(Domain):
    domain_obj: InitVar[DomainCoercible] = None
    min_len: Optional[int] = field(default= 0, kw_only= True)
    max_len: Optional[int] = field(default= 20, kw_only= True)
    domain: Domain = field(init= False)

    def __post_init__(self, domain_obj: DomainCoercible):
        super().__setattr__('domain', domain_expr(domain_obj))
        
    def __iter__(self) -> Iterator[list]:
        min_len = self.min_len
        max_len = self.max_len
        if min_len == 0:
            yield []
            min_len = 1
        while True:
            n = _random.randint(min_len, max_len)
            yield list(islice(self.domain, n))

    
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


class Dict(Domain):
    def __init__(self,
                 key_domain: DomainCoercible,
                 value_domain: DomainCoercible,
                 min_len: int= 0,
                 max_len: int= 20):
        self.key_domain = domain_expr(key_domain)
        self.value_domain = domain_expr(value_domain)
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
        

# --------------------------------------------------------------------------------------
# Domains specific to python
# --------------------------------------------------------------------------------------
class DomainPyObject(Domain):
    def __init__(self,
                 factory: Callable,
                 *domain_args: tuple(DomainCoercible,...),
                 **domain_kwargs: dict[str, DomainCoercible]):
        self.factory = factory
        self.domain_args = [domain_expr(d) for d in domain_args]
        self.domain_kwargs = { key: domain_expr(d) for key, d in domain_kwargs.items() }

    def __iter__(self) -> Iterator:
        factory = self.factory
        args_iterators = [iter(domain) for domain in self.domain_args]
        kwargs_iterators = { key: iter(domain)
                             for key, domain in self.domain_kwargs.items() }
        while True:
            yield factory(
                *(next(it) for it in args_iterators),
                **{ key: next(it) for key, it in kwargs_iterators.items() })

    def exhaustible_iter(self) -> Iterator:
        if any(not domain.is_exhaustible for domain in self.domain_args):
            raise TypeError(f"not every element is exhaustible in {self}")
        factory = self.factory
        args_iterators = [domain.exhaustible for domain in self.domain_args]
        kwargs_iterators = { key: domain.exhaustible
                             for key, domain in self.domain_kwargs.items() }

        # TODO: si un dominio es más grande que otro, ¿ nos vale este comportamiento
        #  o queremos implementar otros ?
        while True:
            try:
                yield factory(*(next(it) for it in args_iterators),
                              **{ key: next(it)
                                  for key, it in kwargs_iterators.items() })
            except StopIteration:
                break
