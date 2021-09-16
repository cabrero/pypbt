#!/usr/bin/env python3

from __future__ import annotations

import inspect
import textwrap
from typing import Iterable, Iterator


from pypbt import domain

from pypbt.quantifier import exists, forall


"""
## Otras consideraciones

Normalmente no se suelen considerar la composición de los
cuantificadores como tal. Y tampoco que las variables cuantificadas
puede aparecer en un un cuantificador _más interno_, en cuyo caso son
variables ligadas.

Y después de esta explicación de mierda, el ejemplo:

```python
@forall(x= domain.Int())
@forall(y= lambda x: domain.Int(max_value= x))
def smaller_ratio_is_less_than_one(x, y):
    return y/x <= 1
```

En hypothesis sería:

```python
@given(st.integers().flatmap(
    lambda x: st.tuples(st.just(x), st.integers(max_size= x))))
def ...
```

> Si que es verdad que en ningún caso nos libramos de introducir la
> `lambda` porque sino no podríamos implementarlo sin transformar el
> código.


## Más ejemplos

Hypothesis

```python
@given(st.lists(st.integers(), min_size= 4, max_size=4).flatmap(
        lambda xs: st.tuples(st.just(xs), st.sampled_from(xs))
    ))
def test_list_and_element_from_it(self, pair):
    (generated_list, element) = pair
    self.assertIn(element, generated_list)
```

> Según el autor, la operación `flatmap` es análoga al `bind` de las
> mónadas.

vs

```python
@forall(xs= domain.List(domain.Int(), min_len= 4, max_len= 4))
@forall(x= lambda xs: domain(xs, finite= True))
def list_and_element_from_it(xs, x):
    return x in xs
```

En realidad la segunda versión no es equivalente a la primera porque
al aplicar el `flatmap` sólo obtenemos un _sample_. Para que fuese
exactamente igual, en la segunda versión necesitaríamos un parámetro
del tipo:

```python
@forall(x= lambda xs: domain(xs, finite= True), n_samples= 1)
```

Pero no le veo el beneficio.



### Shrinking.

### Misc

Cada generador (o la función `samples`) tiene un parámetro `seed`

Cada generador puede tener parámetros como max, min, ...

Cada generador le da un significado al parámetro del tamaño.  También
puede tener una estrategia para incrementar el tamaño en función del
número de muestras que se van a usar.

### Superproblemas

- Combinadores.

  Cosas con el _such_that_ pueden suponer un problema de eficiencia en
  la generación de samples.

- Generador de funciones.

  El generador de funciones (A -> B) sería un diccionario por cada
  función.  Como el dominio puede ser infinito, hay que construir el
  diccionario on-demand.



# CUANTIFICADORES

Los cuantificadores se definen para que ser puedan componer. Por
ejemplo:

```
ForAll x: Int,
  ForAll y: Int,
    ...
```

Evidentemente los cuantificadores "internos" tiene acceso a las
variables ligadas de los "externos". Es el mismo mecanismo que es
habitual en el scope de las variables en un lenguaje de programación.

## Crecimiento exponencial

En el ejemplo anterior tenemos que `(x, y)` pertenece al producto
cartesiano `Int x Int`. Esto se tiene que tener en cuenta a la hora de
calcular el número de muestras que se van a generar en la prueba.



## FORALL

Por el modo de funcionamiento de QuickCheck, es más un "for many" que un
"for all". Los declaramos como 

```
@forall(name= gen_expr)
```

name es la variable cuantificada, y gen_expr declara el dominio de la variable.

```
Env :: Map[Name, Sample]

GenExpr :: Gen Generator
         | GenBuilder Env -> Generator
```

- La primera opción es declarar directamente el generador que
  representa el dominio.

- La segunda opción es declarar una función que dado un entorno (Env)
  devuelve un generador. Un entorno no es más que una lista de
  bindings nombre -> valor, como en un cierre de una función.


## FORALLDOM

Cuando la variable cuantificada está definida sobre un DOMAIN en lugar
de un GENERATOR, es posible hacer realmente un "for all" y no un "for
many", comprobando la propiedad para todos los valores del conjunto.

De esta forma la prueba se convierte en una demostración.


## EXISTS

El cuantificador Existe no tiene sentido en QuickCheck:

- Comprobar un subconjunto aleatorio de valores no aporta ninguna
  información relevante.

- No es posible encontrar un contraejemplo.

Sin embargo, al igual que FORALLDOM, si lo definimos sobre un DOMAIN,
se pueden comprobar todos los valores del dominio y tener una
demostración de la propiedad cuantificada con el Existe.

Hay que tener en cuenta que, aún en este caso, si la propiedad no se
cumple, seguimos sin poder ofrecer un contraejemplo. En este sentido,
un Existe es equivalente a un predicado.

# QuicCheck

La prueba sobre una propiedad la definimos como 

```
Result :: Either[Fasilfy,Bool]

qc :: Env -> Iterator<Result>
```


# pytest, unittest

¿ Integrar con uno, con ambos ?


# Misc

¿ Esto vale la pena ?

```
@forall(gen.list(gen.int(), min_len= 1))
def max_returns_max_item(l):
    mx = max(l)
    return forall(dom.form_list(l), lambda x: not x > mx) 
```

o simplemente:

```
@forall(gen.list(gen.int(), min_len= 1))
def max_returns_max_item(l):
    mx = max(l)
    return all(dom.form_list(l), lambda x: not x > mx)
```

"""

###########################################################################

@forall(x= filter(lambda x: x<20, domain.Int()))
def superstupid_prop(x):
    return x > 4


@forall(x= (a for a in domain.Int() if a<20))
def superstupid_prop_2(x):
    return x > 4


@forall(xs= domain.List(domain.Int(), min_len= 4, max_len= 4))
@forall(x= lambda xs: domain.domain(xs, finite= True))
def list_and_element_from_it(xs, x):
    return x in xs


# Esta propiedad está mal (x=0).
# Pero es difícil que salte el error con el generador naïf
# Hace falta la heurística de generar el zero
@forall(x= domain.Int())
@forall(y= lambda x: domain.Int(max_value= x))
def smaller_ratio_is_less_than_one(x, y):
    return y/x <= 1


@forall(l= domain.List(domain.Int(), min_len= 1))
def max_returns_max_item(l):
    mx = max(l)
    return not any(x > mx for x in l)


@forall(x= domain.Int())
@forall(y= domain.Int())
def la_suma_es_conmutativa(x, y):
    return x + y == y + x


@forall(x= domain.Int())
@exists(y= domain.domain(range(1, 9), finite= True))
def stupid_prop(x, y):
    return x % y > 1


@exists(x= domain.domain(range(10), finite= True))
def even_more_stupid_prop(x):
    return x > 7


@forall(x= (a*2 for a in domain.Int()))
def even_is_even(x):
    return x % 2 == 0


@forall(x= domain.Boolean() | domain.Int())
def one_way_or_another(x):
    return type(x) == bool or type(x) == int


@forall(t= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))())
def a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)


Tree= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))


@forall(t= Tree())
def again_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)


Json = domain.recursive(lambda Json: (
    domain.None_() |
    domain.Boolean() |
    domain.Int() |
    domain.List(Json()) |
    domain.Dict(domain.PyName(), Json())
))

# TODO: propiedad que use el json


###########################################################################
def test():
    props = [
        superstupid_prop,
        superstupid_prop_2,
        list_and_element_from_it,
        smaller_ratio_is_less_than_one,
        max_returns_max_item,
        la_suma_es_conmutativa,
        stupid_prop,
        even_more_stupid_prop,
        even_is_even,
        one_way_or_another,
        a_tree_looks_like_a_tree,
        again_a_tree_looks_like_a_tree,
    ]

    for prop in props:
        print(prop)
        prop()
        print()
    

def pprint(tree, prefix= ""):
    if type(tree) == bool:
        print(prefix, tree, sep= "")
    else:
        print(prefix, "-", sep= "")
        pprint(tree[0], prefix+"  ")
        pprint(tree[1], prefix+"  ")


def tree():
    Tree = domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(max_depth= 4), Tree(max_depth= 7))
    ), max_depth= 8)
    
    it = iter(Tree())
    for _ in range(10):
        print(next(it))
    print()

    
def json():
    Json = domain.recursive(lambda Json: (
        domain.None_() |
        domain.Boolean() |
        domain.Int() |
        domain.List(Json()) |
        domain.Dict(domain.PyName(), Json())
    ))
    it = iter(Json())
    for _ in range(10):
        print(next(it))

class Job(domain.Domain):
    def __iter__(self) -> Iterator:
        while True:
            yield domain.fake.job()

    def __str__(self):
        return f"Job()"


if __name__ == '__main__':
    test()
    for i in range(1000,1200):
        print(i)
        domain.set_seed(i)
        tree()
        # json()
        print()

    #job = iter(Job())
    #for i in range(10):
    #    print(i, next(job))
    
