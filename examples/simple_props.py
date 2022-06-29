from typing import Iterable


from pypbt import domain
from pypbt.quantifier import exists, forall


@forall(x= filter(lambda x: x<20, domain.Int()))
def prop_superstupid(x):
    return x > 4


@forall(x= (a for a in domain.Int() if a<20))
def prop_superstupid_2(x):
    return x > 4


@forall(xs= domain.List(domain.Int(), min_len= 4, max_len= 4))
@forall(x= lambda xs: domain.domain(xs, is_exhaustible= True))
def prop_list_and_element_from_it(xs, x):
    return x in xs


# Esta propiedad está mal (x=0).
# Pero es difícil que salte el error con el generador naïf
# Hace falta la heurística de generar el zero
@forall(x= domain.Int())
@forall(y= lambda x: domain.Int(max_value= x))
def prop_smaller_ratio_is_less_than_one(x, y):
    return y/x <= 1


@forall(l= domain.List(domain.Int(), min_len= 1))
def prop_max_returns_max_item(l):
    mx = max(l)
    return not any(x > mx for x in l)


@forall(x= domain.Int())
@forall(y= domain.Int())
def prop_la_suma_es_conmutativa(x, y):
    return x + y == y + x


@forall(x= domain.Int())
@exists(y= domain.domain(range(1, 9), is_exhaustible= True))
def prop_stupid(x, y):
    return x % y > 1


@exists(x= domain.domain(range(10), is_exhaustible= True))
def prop_even_more_stupid(x):
    return x > 7


@forall(x= (a*2 for a in domain.Int()))
def prop_even_is_even(x):
    return x % 2 == 0


@forall(x= domain.Boolean() | domain.Int())
def prop_one_way_or_another(x):
    return type(x) == bool or type(x) == int


def evens(input: Iterable[int]) -> Iterable[int]:
    return [ x for x in input if x % 2 == 0 or x == 101 ] # <- BUG

@forall(l= domain.List(domain.Int()))
@forall(l1= lambda l: domain.Sublists(evens(l), is_exhaustible= len(l) < 6))
def evens_sublists_sum_is_even(l, l1):
    return sum(l1) % 2 == 0

@forall(l= domain.List(domain.Int()))
def evens_len(l):
    return len(evens(l)) <= len(l)

@forall(l= domain.List(domain.Int()))
def evens_sum_is_even(l):
    return sum(evens(l)) % 2 == 0

