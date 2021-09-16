"""markdown

# Domain

Normalmente los __Dominios__ son conjuntos infinitos de objetos.
Incluso cuando no lo son, su cardinalidad puede ser demasiado grande
como para poder comprobar una propiedad con todos los objetos del
dominio. Por eso en PBT sólo comprobamos una propiedad contra un
subconjunto elegido al azar.

Aún así, en python podemos representar un conjunto infinito de
elementos de varias formas. De entre la posibilidades existentes
elegimos una _función generadora_, _generator_. Por ejemplo:

```
DomainGenerator :: None -> Iterator[DomainObject]
```

Como vemos, en python estos generadores son iterables, pero no nos
interesa iterar sobre los objetos del dominio siempre con la misma
secuencia. Para el PBT nos interesa que el generador nos devuelva cada
vez un iterador distinto que recorre el dominio en un orden al azar.

Es muy importante dejar claro que en realidad el orden no puede ser
realmente aleatorio, sino _pseudoaleatorio_ porque estamos haciendo
pruebas y, cuando encontramos un error, tenemos que ser capaces de
repetir la misma secuencia _pseudoaleatoria_ de objetos.

Para que la falta de transparencia referencial no nos cree sarpullido,
podemos pensar en la función generadora como:

```
DomainGenerator :: Seed -> Iterator[DomainObject]
```

De esta forma para la misma semilla devuelve el mismo iterador que
realiza el mismo recorrido.


Siguiendo con la implementación, aunque el dominio esté representado
como una función generadora, la vamos a envolver en un objeto python
.`Domain`, donde incluiremos:

  - Parámetros del dominio. P.e. max_size, min_size, ...

  - Pretty print

  - Operadores sobre dominios, p.e. la unión `|`

  - Semilla

  - ...


## Estrategias de generación

Conocemos tres estrategias principales para generar el recorrido
pseudoaleatorio del domino:


- Naïf. A partir de una semilla, generar una secuencia de números
  pseudoaleatorios y usar estos números para seleccionar los elementos
  del conjunto.

- TODO: A mayores del caso anterior, usar heurísticas para incluir
  elementos que se sabe que son "problemáticos" en las pruebas, por
  ejemplo los zeros.

- TODO: Sized generation. Los elementos se eligen en orden creciente
  de tamaño y complejidad.



# DomainExpr

Además de los objetos de tipo `Domain` con sus correspondiente
funciones generadoras, vamos a tener en cuentra otras expresiones que
nos permiten representar un dominio. Siguiendo con la filosofía de
los dominios, estas expresiones deben evaluarse a un iterable.

Las expresiones `DomainExpr` que vamos a tener en cuenta son:

- Un tipo de dato que sea iterable. Su uso principal es
  representar dominios finitos. P.e. una lista.

- Otro tipo de iterables que podamos crear con el propio lenguaje o
  algún módulo. Son muy útiles para aplicar transformaciones sobre un
  dominio. P.e. `filter`, `map`, ... o las _generator expressions_
  `(x*2 for x in ...) `

Ejemplos:

```python
@forall(x= (a for a in domain.Int() if a < 20))

@forall(x= filter(lambda a: a > 42, domain.Int())
```


# UnboundedDomain

Tomemos como ejemplo la propiedad:

```
forall x in Integer, y in Integer-[-inf,x] ...
```

Que traducida a código podría ser:

```python
@forall(x= Interger())
@forall(y= Integer(lower= x))
```

Pero en el segundo `forall` la `x` está fuera del _scope_ del primero
y, por tanto, está _libre_, a.k.a sin ligar. Lo natural es que durante
la ejecución de las pruebas, la librería le asigne cada uno de los
valores que va generando para el dominio del primer cuantificador.

Pero para que la librería pueda hacer esa asignación, necesitamos
alguna construcción del lenguaje que nos lo permita. Una forma natural
de hacerlo es envolver la expresión de dominio en una función cuyos
parámetros sean las variable libres de la expresión de dominio:

```python
@forall(x= Interger())
@forall(y= lambda x: Integer(lower= x))
```

Igual que hacemos con las funciones generadoras, estás funciones "de
binding" también las envolvermos en un objeto. Este objeto tendrá una
operación para ligar las variables libres y devolver un objeto
`Domain`.


# Dominios 'suficientemente' finitos

Algunos dominios son finitos y su cardinalidad es suficientemente
pequeña como para poder comprobar una propiedad para todos los objetos
del dominio. En estos casos podríamos incluso usar un _cuantificador
existencial_.

Comprobar si un dominio es finito es demasiado complejo. Es
reponsabilidad del cliente marcar los dominios como finitos:

```python
@exists(y= domain.finite_domain(range(1,9)))
```

# Dominios "recursivos"

En la definición de los objetos de un dominio puede aparecer objetos
del propio dominio. De ahí lo de _recursivo_. El ejemplo mítico son
los árboles.

> _N.B._ Para que la recursión se pueda resolver tiene que haber al
> menos un caso base a mayores de un paso recursivo. Esta condición
> sólo se da en dominios creados a partir de operadores como el `|`.

Como primera aproximación pensemos en un dominio cuyos objetos son
árboles binarios de cualquier tamaño y cuyos nodos hoja son valores
booleanos:

TODO: formulación "más matematica"

```python
Tree = domain.Boolean() | domain.Tuple(Tree(), Tree())
```

El código anterior no se puede usar directamente porque:

- En la parte derecha la variable `Tree` todavía no está definida.

  Podríamos arreglarlo diferiendo la evaluación de `Tree()`
  envolviendola en una lambda: `lambda: Tree()`, pero nos complicaría
  la implementación del runtime y la solución del siguiente problema.

- Si `Tree` estuviese definida, entraríamos en un bucle infinito.

Para solucionar estos problemas hay que marcar explicitamente las
definiciones recursivas. El código resultante es un poco _contrived_,
pero no parece fácil hacer algo más natural sin analizar el código
fuente

```python
Tree = recursive(lambda Tree: domain.Boolean() | domain.Tuple(Tree(), Tree()))
Tree = recursive(lambda Tree: (
    domain.Boolean() |
    domain.Tuple(Tree(), Tree()))
)
```

"""

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
    is_finite: bool
    def as_finite(self, finite: bool) -> Domain: ...
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


def desugar_domain(arg: DomainCoercible, finite: Optional[bool]= None) -> Domain:
    if is_domain(arg):
        return arg if finite is None else arg.as_finite(finite)
    elif isinstance(arg, Iterable):
        return FiniteIterableAsDomain(arg) if finite else IterableAsDomain(arg)
    else:
        # TODO: Otras formas de declarar un dominio, p.e.
        #    - tipos básicos: int, str, ...
        #    - función generadora
        raise TypeError(f"Cannot use {arg} as a domain here")


def domain(d: Any, finite: bool= False) -> Domain:
    return desugar_domain(d, finite)

            
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
    is_finite : bool = False

    def as_finite(self, finite: bool) -> Domain:
        if finite:
            raise TypeError(f"domain cannot be marked as finite: {self}")
        return self
    
    def finite_iterator(self) -> Iterator:
        raise TypeError(f"domain is not finite enough: {self}")
    
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

    
class FiniteIterableAsDomain(DomainAbs):
    is_finite : bool = True

    def __init__(self, iterable: Iterable):
        self.iterable = tuple(iterable)

    def as_finite(self, finite: bool) -> Domain:
        return self if finite else IterableAsDomain(self.iterable)

    def __iter__(self) -> Iterator:
        # Importante: barajar los items por si acaso el número de muestras que
        # se cogen del dominio es menor que el tamaño del iterable, para evitar
        # devolver siempre los $n$ primeros.
        samples = _random.sample(self.iterable, len(self.iterable))
        while True:
            yield from samples
    
    def finite_iterator(self) -> Iterator:
        return iter(self.iterable)
    
    def __str__(self):
        return f"FiniteDomain({self.iterable})"


class Sublists(DomainAbs):
    def __init__(self, l: list, finite: bool= False):
        self.l = l
        self.is_finite = finite

    def __iter__(self) -> Iterator:
        yield []
        n = len(self.l)
        while True:
            a = _random.randint(0, n)
            b = _random.randint(0, n)
            a, b = (a, b + 1) if a <= b else (b, a + 1)
            yield self.l[a:b]
        
    def finite_iterator(self) -> Iterator:
        if not self.is_finite:
            raise RuntimeError("Domain is not marked as finite enough")
        yield []
        n = len(self.l)
        for a in range(n):
            for b in range(a, n):
                yield self.l[a:b+1]

    def __str__(self):
        return f"Sublists({self.l}"
        

class Int(DomainAbs):
    def __init__(self, max_value: Optional[int]= None):
        self.args = {'max_value': max_value or 10_000 }

    def __iter__(self) -> Iterator:
        max_value = self.args['max_value']
        while True:
            yield _random.randint(0, max_value)

    def __str__(self):
        args = ", ".join(f"{k}= {v}" for k,v in self.args.items())
        return f"Int({args})"


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

    def finite_iterator(self, env: Env) -> Iterator:
        iterators = [domain.finite_iterator(env) for domain in self.domains]
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
    is_finite : bool = True

    def as_finite(self, finite: bool) -> Domain:
        if not finite:
            raise TypeError(f"do no mark boolean as infinite: {self}")
        return self
    
    def __iter__(self) -> Iterator:
        while True:
            yield _random.choice([True, False])

    def finite_iterator(self) -> Iterator:
        yield False
        yield True

    def __str__(self):
        return f"Boolean()"


class None_(DomainAbs):
    is_finite : bool = True

    def as_finite(self, finite: bool) -> Domain:
        if not finite:
            raise TypeError(f"do no mark None as not infinite: {self}")
        return self
        
    def __iter__(self) -> Iterator:
        while True:
            yield None

    def finite_iterator(self) -> Iterator:
        yield None
        
    def __str__(self) -> str:
        return f"None()"
    

class DomainUnion(DomainAbs):
    a: InitVar[Domain]
    b: InitVar[Domain]
    domains: list[Domain]= field(init= False)
    is_finite: bool= field(init= False)
    
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
        self.is_finite = all(d.is_finite for d in self.domains)

    def as_finite(self, finite: bool) -> Domain:
        raise TypeError(f"can not mark union as finite: {self}")
            
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




            



