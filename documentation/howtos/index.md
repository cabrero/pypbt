# How-To


## Write a simple property

```python
@forall(x= domain.Int())
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```


## Define a subdomain

When can define a subdomain using any python's ways of implementing a
filter. Let's say we want to use the subdomain of integers greater
than 10.

  a) Using a _generator expression_:
  
```python
@forall(x= (i for i in domain.Int() if i > 10))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

!!! warning

    We must use a _generator expression_. If we use a _list comprehesion_
	the interpreter will try to build the whole list in memory and, as we
	know, the list of integers greater than 10 is infinite.

  b) Using the _filter_ builtin:

```python
@forall(x= filter(lambda i: i > 10, domain.Int()))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```


## Define a domain as a function of another domain

Analogous to the definition of a subdomain, we can define a new domain
in to ways. Let's say we want to define the domain of even integers:

a) Using a _generator expression_:

```python
@forall(x= (i*2 for i in domain.Int()))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

b) Using the `map` builtin:

```python
@forall(x= map(lamba i: i*2, domain.Int()))
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```


## Define a domain as the union of domains

When can define a domain as the _sum_, i.e. _union_ of other domains.
For example, let's use the domain of bools and integers:

```python
@forall(x= domain.Boolean() | domain.Int())
def prop_one_way_or_another(x) -> bool:
    return type(x) == bool or type(x) == int
```


## Use several quantifiers

We can write properties with more than one quantified variable: we
will use a decorator for each variable.


```python
@forall(x= domain.Int())
@forall(y= domain.Int())
def prop_example_2(x, y) -> bool:
    return (x > y) or (y > x) or (x == y)
```

!!! note

    The quantifiers are chained, that means that for each value of `x`
	it must hold that `forall y=...`.
	Or, if you rather like it, if we were to collapse the two quantifiers,
	we must use the product of the domains: `∀ x,y ∊ ℤxℤ`.


## Define a _dependant_ domain

We can define a domain whose value depends on the value of a previouly
quantifier variable. We will write a lambda function whose argument is
the variable the domain depends on. The body of the lambda function is
the expression that build the _dependant_ domain.

```python
@forall(xs= domain.List(domain.Int(), min_len= 4, max_len= 4))
@forall(x= lambda xs: domain.domain(xs, exhaustive= True))
def prop_list_and_element_from_it(xs, x) -> bool:
    return x in xs
```

```python
# Yes, this prop doesn't check when x == 0
@forall(x= domain.Int())
@forall(y= lambda x: domain.Int(max_value= x))
def prop_smaller_ratio_is_less_than_one(x, y) -> bool:
    return y/x <= 1
```


## Define a domain from a python iterable

We can define a domain whose elements are the values contained in any
python iterable. For example, let's write the domain that contains
the numbers from 1 to 8:

```python
domain.domain(range(1, 9))
```


## Check all the values of a domain

The cannonical behaviour of a property based tool is picking random 
samples from the domain and checking the predicate. We can avoid this
behaviour and indicate that we want the library to check every value
in the given domain.

```python
@forall(domain.domain(range(1, 9), exhaustive= True))
```

!!! warning

    Not every domain is suitable to be used in an exhaustive
    quantifier. The set of values must be finite and small enough to
    be computable.
   
    Trying to use the wrong domain with an exhaustive quantifier will
    result in a runtime exception.
   
   
!!! warning

    There is no way to check for any domain whether it can be
    exhaustively quantified. We, the property developers, must mark
    them as such providing the argument `exhaustive= True`.
   

## Use the existencial quantifier

The existencial quantifier is not suitable for property based
machinery: by just picking random samples we cannot prove the
existence o absence of a value checking the predicate. We 
can _only_ use it when the domain is marked as exhaustive.


```python
@forall(x= domain.Int())
@exists(y= domain.domain(range(1, 9), exhaustive= True))
def stupid_prop(x, y) -> bool:
    return x % y > 1
```


```python
@exists(x= domain.domain(range(10)), exhaustive= True))
def even_more_stupid_prop(x) -> bool:
    return x > 7
```


## Define a recurrent domain

Defining a recurrent domain takes quite many "extra steps". First, we
define a lamba function. The arg of the function is the domain
itself. The body is the expression that creates the domain as a union
of several domains. Then the domain must be marked as _recursive_ using
the function `domain.recursive`:


```python
@forall(t= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))())
def prop_a_tree_looks_like_a_tree(t) -> bool:
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)
```

!!! note

    At least one of the parts of the union must contain no
	recurrency at all, in order to guarantee that the values of the
	domains themselves are finite. Otherwise, the building of samples
	from the domain is not guaranteed to terminate.
	
	
```python
Tree= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))


@forall(t= Tree())
def prop_again_a_tree_looks_like_a_tree(t) -> bool:
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)
```


```python
Json = domain.recursive(lambda Json: (
	None |
	domain.Boolean() |
	domain.Int() |
	domain.List(Json()) |
	domain.Dict(domain.PyName(), Json())
))
```


# Define a new domain

Let's say we want to define the domain: `Fraction(Int(), Int())`. We may:

1. Use operators on iterables:
  
		:::python
		DomainFraction = (Fraction(numerator, denominator)
						  for numerator, denominator in zip(domain.Int(), domain.Int(min_value= 1)))

	
2. Use the domain of generic python objects
  
		:::python
		DomainFraction = domain.DomainPyObject(Fraction, domain.Int(), domain.Int(min_value= 1))
		
    or
   
		:::python
        DomainFraction = domain.DomainPyObject(Fraction,
		                                       numerator= domain.Int(),
											   denominator= domain.Int(min_value= 1))


1. Create a `Domain` class from scratch
  
	    :::python
	    class DomainFraction(Domain):
		    def __iter__(self) -> Iterator[Fraction]:
			    numerator = iter(domain.Int())
			    denominator = iter(domain.Int(min_value= 1))
			    while True:
				    yield Fraction(next(numerator), next(denominator))
  
    or
   
        :::python
		class DomainFraction(Domain):
		    def __iter__(self) -> Iterator[Fraction]:
			    for numerator, denominator in zip(domain.Int(), domain.Int(min_value= 1))
				    yield Fraction(numerator, denominator)
	

    !!! warning
	    Avoid the Borg pattern. Iterators created this way share the object's state.
		Domain objects should be inmutable.
		
		This will kill a kitty in internet:
		
		    :::python
		    class Foo:
					a: int= 0
					def __iter__(self) -> Iterator[int]:
						while True:
							yield self.a
							self.a = self.a + 2			
