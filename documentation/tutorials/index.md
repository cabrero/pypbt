# Tutorial

## Installation

The library can be installed in the usual way, using _pip_:

```sh
$ pip install pypbt
```

## Writing our first property

Let's start with a fresh python module `example_property.py`. First thing
first, import the neccessary library's modules:

```python
from pypbt import domain
from pypbt.quantifier import forall
```

Now we can write our first property: $\forall x\in\mathbb{Z}, x\times(-x) = -(x^2)$.
Once implemented using pypbt it will look like:

```python
@forall(x= domain.Int())
def prop_example(x):
    return (x * -x) == -(x**2)
```

A you can see, the _predicate_, the core of the property, is
implemented as a regular python function:

  - The name of the function is not relevant.
  
    !!! note
	    Many testing tools need you to write test's function names
		following a given pattern like `test_*`. This is not the
		case in our library, you can use any (python valid) name you want.
  
  - The argument of the function must be the variable being
    _quantified_, i.e. the variable which  must satisfy the predicate
	_for all_ values of the domain.
	
  - It must return a boolean indicating whether the predicate holds
    for the given parameter.
  
Finally, the quantifier part is implemented as a decorator of the
predicate function.

  - There is a decorator for each quantifier, in this example:
    `forall`.
	
  - The decorator has one named argument. The name of the
    argument is the name of the quantified variable, and the value is
    the domain over which it is being quantified. Thus,
	in our current example,	`x= domain.Int()` means `x∊ℤ`.

## Checking the property

TBD

```sh
$ pypbt example_property
```
