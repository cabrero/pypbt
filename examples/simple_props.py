from typing import Iterable


from pypbt import domains
from pypbt.domains import domain_expr, exhaustible
from pypbt.quantifiers import exists, forall


@forall(x= filter(lambda x: x<20, domains.Int()))
def prop_superstupid(x):
    return x > 4


@forall(x= (a for a in domains.Int() if a<20))
def prop_superstupid_2(x):
    return x > 4


@forall(xs= domains.List(domains.Int(), min_len= 4, max_len= 4))
@forall(x= lambda xs: exhaustible(xs))
def prop_list_and_element_from_it(xs, x):
    return x in xs


# Esta propiedad está mal (x=0).
# Pero es difícil que salte el error con el generador naïf
# Hace falta la heurística de generar el zero
@forall(x= domains.Int())
@forall(y= lambda x: domains.Int(max_value= x))
def prop_smaller_ratio_is_less_than_one(x, y):
    return y/x <= 1


@forall(l= domains.List(domains.Int(), min_len= 1))
def prop_max_returns_max_item(l):
    mx = max(l)
    return not any(x > mx for x in l)


@forall(x= domains.Int())
@forall(y= domains.Int())
def prop_la_suma_es_conmutativa(x, y):
    return x + y == y + x


@forall(x= domains.Int())
@exists(y= exhaustible(range(1, 9)))
def prop_stupid(x, y):
    return x % y > 1


@exists(x= exhaustible(range(10)))
def prop_even_more_stupid(x):
    return x > 7


@forall(x= (a*2 for a in domains.Int()))
def prop_even_is_even(x):
    return x % 2 == 0


@forall(x= domains.Boolean() | domains.Int())
def prop_one_way_or_another(x):
    return type(x) == bool or type(x) == int


def evens(input: Iterable[int]) -> Iterable[int]:
    return [ x for x in input if x % 2 == 0 or x == 101 ] # <- BUG

@forall(l= domains.List(domains.Int()))
@forall(l1= lambda l: domains.Sublists(evens(l), is_exhaustible= len(l) < 6))
def evens_sublists_sum_is_even(l, l1):
    return sum(l1) % 2 == 0

@forall(l= domains.List(domains.Int()))
def evens_len(l):
    return len(evens(l)) <= len(l)

@forall(l= domains.List(domains.Int()))
def evens_sum_is_even(l):
    return sum(evens(l)) % 2 == 0


from fractions import Fraction

@forall(
    fraction= domains.DomainPyObject(
        Fraction,
        numerator= domains.Int(),
        denominator= domains.Int(min_value= 1)
    )
)
def prop_broken_1(fraction):
    print(fraction)
    return fraction.denominator != 0


@forall(
    fraction= domains.DomainPyObject(
        Fraction,
        numerator= domains.Int(),
        denominator= (2, 3)
    )
)
def prop_broken_2(fraction):
    print(fraction)
    return fraction.denominator != 0


@forall(numerator= domains.Int(), denominator= domains.Int(min_value= 1))
def prop_broken_3(numerator, denominator):
    fraction = Fraction(numerator, denominator)
    print(fraction)
    return fraction.denominator != 0


@forall(numerator= domains.Int(), denominator= (3, 8))
def prop_broken_4(numerator, denominator):
    fraction = Fraction(numerator, denominator)
    print(fraction)
    return fraction.denominator != 0


@forall(s= domains.String(max_len= 4))
def prop_str_1(s):
    return len(s) < 5


@forall(s= domains.String(alphabet= exhaustible(['a', 'b']), max_len= 10))
def prop_str_2(s):
    return all(c in ['a', 'b'] for c in s)

