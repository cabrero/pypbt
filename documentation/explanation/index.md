# Explanation

In this section we are going to look at the library from a higher
perspective. This will help you graps a better understanding of the
ideas and decisions behind the design of the library.


## Philosphy

The design of the library is based on these ideas:

  - There is a well-known mathematical language for property
    expressions. We don't need to create new terminology.
	
	Although it is not viable to use the usual symbols of the
    mathematical expressions, we still can mimic the syntax. Again, we
    don't need to create new syntax.
	
  - The concept of property is simple. The implementation should be
    simple.
	
  - We should code each element of a property as an element of the
    programming languge.

    Thus, the implementation _should_ be as idiomatic as possible, and
	we must avoid using the constructions of the language in
	unexpected ways.

These ideas are language-agnostic. If they are valid for our python
implementation, it could be valid for other programming langauges.


## The design of a property

When we write a property like $\forall x\in \mathbb{Z}, x + 0 = x$ we
found the following parts:

  - One _predicate_, $x + 0 = x$, that is a logical expression that
    evaluates to true o false.
	
	We implement this as a python function returning a _bool_ whose
	arguments are the _quantified variables_ of the property.

  - A _quantified variable_, $x$. This variable is quantified over a
    _domain_, $\mathbb{Z}$, the domain of the integers. The
    _quantifier_ is a _forall_, $\forall$, meaning that for every
    value of the domain, when we bind the variable to that value, the
    following _predicate_ must hold.
  
    In order to implement quantifying a predicate, i.e. modifying it, as
    it is implemented as a python function, we will use python
    function decorators.
	
When we write a property containig more than one quantifier like
$\forall x\in \mathbb{Z}, forall y\in\mathbb{Z}, ...$ we follow the
same design for one quantifier. In python we can use a decorator on
the result of another decorator. Thus in the implementation of our
property we can apply quantifier decorator to other quantifer
decorator that we applied to the predicate function.
	
	
## The design of a domain

A _domain_, $\mathbb{Z}$. This is the hardest part, even the basic
domains like this contains an infinite number of values. We cannot
construct a data structure that contains every value of the domain in
memory at once, we need some kind of lazy construct that builds every
value only in the moment of begin used. Our options for lazy
structures in python are: custom data type plus operations on that
type, custom iterator, generator functions and expressions.
	
Custom data types will not be part of the data types of python. This
will add much more effort to the development of the library and will
drive us off the idea of _idomatic_.
	
Both iterators and generators are part of the language and python
already implements the usual operations on them. So this is our
chooice a _domain_ is implemented as a lazy python iterable.

Given that the domains are implemented as python iterables, we can
provide two type of iterators over them:

  - One that randomly goes over the values of the domain.
  
  - One that exhaustively iterates over every value of the domain.

The first one eases the implementation of the pbt mechanism. The
second one will not be viable in many cases, b.e. $\mathbb{Z}$.

As domains are implemented as python iterables, we can transform a
domain applying the usual operators: _filter_, _map_, ...

By it's implementation, it possible random values from a domain just
by iterating over it.


## Randonmly iterating over a domain

TBD

  - Use pseudo random to be able to repeat the sequence of samples.
  
  - Need domain specific heuristics
  
### Estrategias de generación

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


  
  
## Core PBT machinery

The PBT machinery:

  - To obtain samples from a domain it iterates over it.

  - To check the predicate for any sample/s, it calls the predicate
    function passing the sample/s as argument/s.


## Shrink

TBD

domain specific
lot of heuristics


## State machines

TBD

- How to represent

- How to iterate
