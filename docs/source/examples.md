# Examples

## ForAll, one variable

```python
@forall(x= domain.Int())
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

## Subdomain

Filter

```python
@forall(x= (i for i in domain.Int() if i > 10)
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```


```python
@forall(x= filter(lambda i: i > 10, domain.Int()))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

## New domain from domain/s in library

Map

```python
@forall(x= (i*2 for i in domain.Int()))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

```python
@forall(x= map(lamba i: i*2, domain.Int()))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

Union

```python
@forall(x= domain.Boolean() | domain.Int())
def prop_one_way_or_another(x):
    return type(x) == bool or type(x) == int
```

## ForAll, two variables

```python
@forall(x= domain.Int())
@forall(y= domain.Int())
def prop_example_2(x, y) -> bool:
    return (x > y) or (y > x) or (x == y)
```


## Binded variable in domain expression

```python
@forall(xs= domain.List(domain.Int(), min_len= 4, max_len= 4))
@forall(x= lambda xs: domain.domain(xs, finite= True))
def prop_list_and_element_from_it(xs, x):
    return x in xs
```

```python
# Yes, this prop doesn't check when x == 0
@forall(x= domain.Int())
@forall(y= lambda x: domain.Int(max_value= x))
def prop_smaller_ratio_is_less_than_one(x, y):
    return y/x <= 1
```

## Finite enough domain

By default every domain is infinite. It must explicitly be marked as
finite.

```python
domain.domain(range(1, 9), finite= True)
```


## Existencial quantifier

```python
@forall(x= domain.Int())
@exists(y= domain.domain(range(1, 9), finite= True))
def stupid_prop(x, y):
    return x % y > 1
```


```python
@exists(x= domain.domain(range(10), finite= True))
def even_more_stupid_prop(x):
    return x > 7
```


## Recursive domain

```python
@forall(t= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))())
def prop_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)
```

```python
Tree= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))


@forall(t= Tree())
def prop_again_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)
```


```python
Json = domain.recursive(lambda Json: (
	domain.None_() |
	domain.Boolean() |
	domain.Int() |
	domain.List(Json()) |
	domain.Dict(domain.PyName(), Json())
))
```
