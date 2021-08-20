# VISION

Queremos que la librería sea lo más "natural" posible:

  - Existe una formulación matemática de las propiedades. La
    terminología e implementación se basa en ella.
  
  - El código que usa la librería (las propiedades) tiene que ser
    _idiomatic_. Tenemos que evitar la tentación de usar las
    construcciones del lenguaje de formas extrañas (distintas a la
    forma para la que se diseñaron) sólo para que el código de las
    propiedades quede "más resultón".
	
  - El concepto es simple, la implementación tiene que ser simple.


## Las propiedades con una variable cuantificada

Una propiedad con una variable cuantificada, tiene varias partes:

  - Un predicado, por ejemplo: `x·(-x) = -(x^2)`. Los predicados no
    tienen mucho que pensar. En prácticamente cualquier lenguaje se
    puede implementar directamente como una función que devuelve un
    booleano.
	
  - Una variable cuantificada, por ejemplo: `x`. Dentro del predicado
    esta variable no está libre, sino ligada, por tanto lo lógico es
    que sea un parámetro de la función del predicado.

  - Un cuantificador, por ejemplo el cuantificador universal:
    `∀`. Cuantifica una variable sobre un dominio concreto.
  
    En primer lugar, tenemos que nos interesa tener por cada propiedad
    una función cuya ejecución compruebe dicha propiedad (al estilo
    PBT). Esto nos facilita comprobar las propiedades directamente "a
    mano" simplemente ejecutando la función e integrar la librería con
    las herramientas de ejecución de pruebas existentes `unittest`,
    `pytest`, ... como si se tratase de una _prueba al uso_.
	
	Los cuantificadores los implementamos como decoradores que se
    aplican sobre los predicados.
	
	   - El decorador nos permite obtener la función de la propiedad a
         partir de la función del predicado.
		 
	   - El decorador tienen un argumento cuyo nombre es el nombre de
         la variable y cuyo valor es el dominio sobre el que se
         cuantifica.
		 
  - Un dominio. Normalmente tienen un número infinito de
    elementos. Desarrollamos este concepto en su propio subapartado.

Tomemos como ejemplo la propiedad:

```
∀x∊ℤ, x·(-x) = -(x^2)
```

Traducida a código sería:

```python
@forall(x= dom.Int())
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```

## Las propiedades con varias variables cuantificadas

Dado que los cuantificadores se implementa como un decoradores de
python, tambien es posible aplicar un cuantificador sobre otro
cuantificador y de esta manera obtener una propiedad con varias
variables cuantificadas. Ejemplo:

```python
@forall(x= domain.Int())
@forall(y= domain.Int())
def prop_example_2(x, y) -> bool:
    return (x >= y) or (y >= x)
```
 	

## El ingrediente principal: el Dominio

Como ya hemos dicho, normalmente son conjunto de cardinalidad infinita
por lo que no los podemos representar de forma extensional. Por
ejemplo: `ℤ`.

Con esta restricción necesitamos una estructura _perezosa_ para su
representación. En python la estructura que encaja de forma natural
son los _generadores_. Un generador es un iterador que nos permite
recorrer un conjunto infinito de elementos puesto que construye los
elementos de forma perezosa a cada paso de la iteración.

Representamos los dominios como objetos _iterables_ . Un iterable es
un objeto que representa una colección de datos y que puede
proporcionar un iterador que recorra dicha colección. Los iteradores
serán generadores que recorrer una secuencia ordenada al azar de los
elementos del dominio.

Evidentemente, la secuencia también es infinita y no podemos crearla
"en memoria". Tenemos que generar cada elemento de la secuencia en
cada paso de la iteración.

Otro aspecto primordial es que la secuencia, aunque sea generada al
azar, tiene que repetible para los casos en que querramos repetir una
prueba. Por tanto, la implementación de los iteradores tiene que estar
basada en el uso de algoritmos de generación de números
pseudoaleatorios (i.e. repetible a partir de una misma semilla). Por
ejemplo:
	
```python
def numeros_pares() -> Iterador[int]:
	while True:
        yield _random.randint(0, max_value) * 2
```

Como vemos, la mayor complejidad del planteamiento reside en la
implementación de los dominios. A cambio obtenemos las siguientes
ventajas:

  - Los dominios son iterables, es decir una construcción propia del
    lenguaje.  No necesitamos implementar los operadores básicos como
    `map`, `filter`, ...  podemos usar los operadores y librerías
    propias del lenguaje. Por ejemplo:
	
	```python
	@forall(x= filter(lambda a: a>42, numeros_pares()))
	    ...
	@forall(x= (a for a in numeros_pares() if a>42))
	    ...
    ```
	
  - Es más sencillo razonar sobre el resto de la librería. Y más
    sencillo razonar sobre la implementación aislada de los dominios.

  - Es más sencillo construir nuevos dominios como una combinación de
    dominios existentes.
	
  - Es más sencillo implementar los operadores de combinación de
    dominios, p.e. `union`.


## Versus otras librerías

El uso de decoradores es habitual para la definición de las
propiedades. En general, python y otros lenguajes, es habitual el uso
de alguna estructura/construcción/metaprogramación que permita
implementar las propiedades como funciones.

La aproximación que planteamos a la implementación de los dominios no
es la habitual. Por ejemplo, dentro del mundo python tenemos
_hypothesis_. En hypothesis los conjuntos de datos no se representan
como tal de ninguna manera. En su lugar disponemos de unas funciones
llamadas _strategies_ que devuelven muestras aleatorias de un conjunto
de datos.

Hypothesis tiene que implementar funciones como `filter`, `map`,
... para las strategies:

```python
@given(st.integers().filter(lambda x: x > 42))
def test_filtering(self, x):
    self.assertGreater(x, 42)
```
