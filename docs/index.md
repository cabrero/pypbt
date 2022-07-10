---
layout: default
---

# Welcome to pypbt's developers doc

:Version: |version|
:Date: |today|
:Copyright: GNU Free Documentation License 1.3 with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts

	    
These pages documents the diverse aspects of the development of PyPBT including:

  - Writing user documentation
  
  - The design of the library
  
  - The development and deployment processes

  - Bibliography references used during the research phase


# Why yet another library ?

Our motivation was to answer:

  - Is it possible another approach to the design and implementation ?
  
  - Providing it is, this approach eases writing and reading the properties ?

The main challenge is to design it in such a way that it is easy to
define and tranform the Domains of the properties' variables.


## What's next if the answers are yes ?

The library will be missing several features that were not neccessary
to answer the questions.  But these features are almost essential in
order to use the library in production. For example:

  - Shrinking.
  
  - Integration with test runners.
  
  - Different sampling strategies.
  
  - ...

At this point we would be able to continue our work in two ways:

  - Continue the development of the library adding the missing
    features.
	
  - Answering a new question: is this approach valid to improve
    other libraries, even in other programming languages ?


# QuickCheck has a few downsides.

From _Production Haskell_:

The ability of QuickCheck to find a bug is dependent on how well tuned
the random value generators are to the problem. QuickCheck uses type
classes for generating values by default, and the default generator is
probably not well tuned to your domain. It’s entirely possible that
the random number generation just never generates a value that trips
an edge case. Since the tests are non-deterministic, it’s also easily
possible that you’ll write test cases that fail sometimes but not
others. QuickCheck allows you to provide a seed value to reproduce
these test, of course, but randomly failing tests can be difficult to
track down.

Once a failing value is found, shrinking that value becomes
essential - otherwise you’ll end up with a massive and difficult to
understand input test case. QuickCheck defines shrink with a default
method that does nothing, so most custom types don’t shrink at
all. This limits the usefulness of QuickCheck with custom types,
unless you manually define shrinking functions, and there’s no
guarantee that your shrinking function works properly for your domain.


# Other languages

Other languages may benefit from this ideas. But the idiomatic implementation
should differ.

## Hypothesis vs eris https://hypothesis.works/articles/hypothesis-vs-eris/ 

```php
<?php
use Eris\Generator;
use Eris\TestTrait;

class IntegerTest extends PHPUnit_Framework_TestCase
{
    use TestTrait;

    public function testSumIsCommutative()
    {
        $this
            ->forAll(
                Generator\int(),
                Generator\int()
            )
            ->then(function ($first, $second) {
                $x = $first + $second;
                $y = $second + $first;
                $this->assertEquals(
                    $x,
                    $y,
                    "Sum between {$first} and {$second} should be commutative"
                );
            });
    }
```

function forAll ... then ...
El argumento de then es una función con la "propiedad".

En python hacemos que le quantificador decore el predicado de la
propiedad porque no podemos tener una función anónima con varias
expresiones.

