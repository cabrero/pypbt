# Presentación

Esta prueba de concepto se centra en la representación de las
_propiedades_ en un lenguaje de programación concreto: python. El reto
principal es conseguir que sea sencillo definir y manipular los
_dominios_ de las variables.


La idea en la que nos basamos es emplear estructuras del lenguaje de
programación que encajen con el concepto de domino y al mismo tiempo
se puedan manipular con sus operaciones habituales.


> En relación a este trabajo. Las estructuras y operaciones que usemos
> para implementar los dominios es muy probable que existan en otros
> lenguajes de programación actuales. A priori es posible trasladar
> los resultados a esos lenguajes.


Otros aspectos básicos del PBT que no se tratan en esta prueba de
concepto:

  - Shrinking.

  - Calidad de las muestras de los dominios generadas.


Otros aspectos que no se tratan:

  - Integración con otras herramientas. P.e.: `pytest`, covertura, ...


# Terminología

Usaremos la terminología más cercana posible a la formulación
matemática de una propiedad, porque:

  - Nos proporciona un lenguaje más universal.
  
  - Evitamos usar terminos cercanos a la implementación. P.e.:
    _generador_ para referirnos a un dominio.
	
  - Evitamos usar terminos confusos. P.e. _generador_ es una
    construcción en muchos lenguajes de programación.
  
  - Parece que chanamos más.
  
  
# Visión

Como hemos dicho en la presentación, representamos cada componente
de una _propiedad_ con la estructura más "natural" en el lenguaje de
programación:

  - _Predicado_: Lo representamos como un predicado, i.e. una función
    que devuelve verdadero o falso. Los parámetros de la función son
    las variables libres del predicado.
	
	De esta manera la maquinaría de testing puede llamar a la función
    pasándole como argumentos objetos de los dominios de las variables
    cuantificadas y comprobar que el predicado se cumple para esos
    objetos.
	
	```python
	def max_returns_max_item(l):
	    mx = max(l)
		return not any(x > mx for x in l)
	```

  - _Cuantificadores_: Dado que cuantifican las variables libres del
    predicado, lo representamos como decoradores de las funciones de
    los predicados. Los parámetros del decorador son el nombre de la
    variable cuantificada y el dominio sobre el que se cuantifica.
	
	El decorador transforma la función en una nueva con el
    procedimiento de PBT: tomar al azar un número finito de _muestras_
    del dominio y validar el predicado.
	
	```python
	@forall(l= domain.List(domain.Int(), min_size= 1))
	def max_returns_max_item(l):
	    ...
	```
	
	
  - _Dominios_: Esta es la parte más compleja porque normalmente son
    conjuntos infinitos o suficientemente grandes para que no los
    podamos representar de forma extensional. Necesitamos algún tipo
    de estructura _perezosa_ para representarlos. Al mismo tiempo
    necesitamos _iterar_ sobre los objetos del dominio de manera que
    en cada recorrido se realize sobre una secuencia de un subconjunto
    del dominio elegidos al azar.

   
    En python se separa bien los conceptos de _iterable_ e _iterador_,
    y ambos pueden ser _perezosos_. Esto nos viene bien para hacer la
    siguiente representación:
	 
	  - iterable ~= dominio. Representa el conjunto de objetos,
        probablemente infinito.

	  - iterador ~= secuencia de muestras del domino elegidas al azar.
	    Potencialmente, el iterador podría recorrer el dominio entero
	    (en un tiempo infinito).
		
		Por cada iterable podemos crear tantos iteradores como sea
        necesario, y cada iterador puede realizar un recorrido distinto.

    Principalmente usamos las _funciones generadoras_ y podemos
	aplicar las operaciones habituales sobre iterables e iteradores.

    Ejemplo de función generadora:
	
    ```python
	def int_samples() -> Iterator:
	    while True:
		    yield fake.pyint()
	```


# Razonamiento sobre los dominos

En otras librerías no se usa la aproximación de representar los
dominios como objetos iterables o colecciones. Por ejemplo para python
tenemos _hypothesis_ donde no exites una representación de los dominos
como tal. En su lugar disponemos de funciones llamadas _strategies_
que devuelven muestras aleatorias de un conjunto de datos. El uso de
estas funciones es totalmente procedimental y la librería tiene que
implementar operaciones básicas como `filter`, `map`, etc:

```python
@given(st.integers().filter(lambda x: x > 42))
def test_filtering(self, x):
    self.assertGreater(x, 42)
```


Por otro lado, si implementamos los dominios como objetos iterables,
podemos usar las construcciones y operaciones del lenguaje que manipulan
iterables e iteradores:

```python
@forall(x= filter(lambda x: x > 42, domain.Int()))
def test_filtering(x):
    return x > 42
```

```python
@forall(x= (a for a in domain.Int() if a > 42))
def test_filtering(x):
    return x > 42
```


# Aleatorio sí, pero poco

En PBT "sólo" comprobamos una propiedad para un subconjunto del
dominio de las variables cuantificadas. Este subconjunto se elige al
azar, pero al mismo tiempo no nos interesa que la elección sea
totalmente aleatoria porque en caso de encontrar un error es
importante poder repetir la prueba con los mismos valores. Por eso
generamos valores _pseudoaleatorios_ a partir de una _semilla_.


# Be transparent my friend

Si nos fijamos en el ejemplo de función generadora:
	
```python
def int_samples() -> Iterator:
    while True:
        yield fake.pyint()
```

Y asumimos que faltan ciertos detalles sobre su aplicación en la
implementación real, podemos pensar que su tipo es:

```
Domain[A] :: None -> Iterator[A]
```

Pero como hemos dicho cada iterador realiza un recorrido distinto,
elegido al azar. Esto quiere decir que la función devuelve un
resultado distinto de cada vez.

Para que la falta de transparencia referencial no nos cree mucho
sarpullido, podemos pensar en la función generadora como:

```
Domain[A] :: Seed -> Iterator[A]
```

Donde `Seed` es una semilla que se usar para generar una secuencia de
valores _pseudoaleatoria_, de forma que la misma semilla genera la
misma secuencia. Es decir, que para una misma semilla la función
devuelve un iterador que realiza el mismo recorrido.

> Si nos aburrimos, podemos seguir discutiendo el tema porque en
> realidad, para la misma semilla, devuelve un objeto iterator
> distinto de cada vez, aunque todos realizen el mismo recorrido.


# Más sobre la implementación de los dominios

En lugar de representar los dominios directamente por su función
generadora, esta función la vamos a envolver en un objeto python de
tipo `Domain`. En estos objetos incluiremos datos y operaciones
útiles:

  - Parámetros del dominio. P.e. max_size, min_size, ...
  
  - Pretty print

  - Operadores sobre dominios. P.e. unión `|`
  
  
  
# Otros "dominios"

Además de los objetos de tipo `Domain` existen otras estructuras del
lenguaje que nos permiten crear iterables, y como hemos dicho, un
iterable es una representación de un dominio. Los que tenemos en
cuenta son:

  - Un tipo de dato que sea iterable. Su uso principal es representar
    dominios finitos. P.e. una lista.

    ```python
    @exists(y= domain.finite_domain(range(1, 10)))
    ```

  - Otro tipo de iterables que podamos crear con el propio lenguaje o
    algún módulo. Son muy útiles para aplicar transformaciones sobre
    un dominio. P.e. `filter`, `map`, ... o las _generator
    expressions_ `(x*2 for x in ...) `

    Repetimos los ejemplos:

    ```python
    @forall(x= (a for a in domain.Int() if a > 42))

    @forall(x= filter(lambda a: a > 42, domain.Int())
    ```


# Dominios suficientemente finitos

Algunos dominios contienen un número finito de objetos suficientemente
pequeño como para poder tratarlos de forma exhaustiva. P.e. `Boolean`

TODO: Con estos dominios podemos hacer un _forall_ de verdad, comprobando la
propiedad para todos los objetos del dominio.

También podemos usar el _cuantificador existencial_: _exists_. Hay que
destacar que normalmente este cuantificador no tiene sentido en PBT
porque:

  - Comprobar una subconjunto del domino no genera ninguna confianza
    en que exista o no un objeto que cumpla la propiedad.
	
  - No es posible encontar un contraejemplo.
  
Pero si podemos comprobar todos los objetos del dominio, podemos probar si
la propiedad se cumple o no.
  

# Scope, binding y demás cosas de las variables

Supongamos el caso en que tenemos una propiedad donde hay más de una
variable cuantificada. P.e.:

```
\forall x \in Integer(), y \in Integer(lower= x), ...
```

Podemos hacer una primera traducción a código sin mayor problema
porque los decoradores están implementados de manera que se pueden
componer:

```python
@forall(x= domain.Integer())
@forall(l= domain.Integer(lower= x))
def some_property ...
```

Pero tenemos un problema: en el segundo cuantificador la `x` no está
definida. O incluso peor, es una variable "más global".

Para poder ligar esa variable y asignarle un valor durante la
ejecución de la pruebas, lo más sencillo es envolver la expresión en
una función. Y en este caso lo más ergonómico es una lambda:

```python
@forall(x= domain.Integer())
@forall(l= lambda x: domain.Integer(lower= x))
def some_property ...
```


# Dominios _recursivos_

Esta es la que puntua para nota: cuando en la definición de un dominio
hay una parte que se refiere al propio domino. Ejemplo mítico, un
árbol:

TODO: formulación "más matematica"
```
Tree = Boolean | (Tree, Tree)
```

Y en python:

```python
Tree = domain.Boolean() | domain.Tuple(Tree(), Tree()))
```

Si no lo tenemos en cuenta, al construir una muestras como las partes
del objeto del dominio se eligen al azar podemos entrar en un bucle
infinito. En la práctica lo que va a ocurrir es que vamos al alcanzar
el límite de recursión de python (número máximo de llamadas que
podemos acumular en la pila de llamads). En otros lenguajes tendríamos
un _stack overflow_, o nos quedaríamos sin memoria.

Lo primero en que nos vamos a fijar es que para que una recursión se
pueda resolver tiene que haber al menos una alternativa que defina el
caso base. Si trasladamos esta idea a la definición de los dominios,
lo que vemos es que las alternativas se presentan en la únion de
dominios.

El código anterior, además del problema del bucle infinito, también
presenta el problema de que la variable `Tree` no está definida en la
parte derecha de la asignación.

Como solución, una vez más, envolvemos la definición en una
función. Y, a mayores, pasamos la expresión a una función de _factory_
que construye un dominio capaz de contar las "llamadas" recursivas
sobre sí mismo.

El resultado es más _contrived_ de lo que nos gustaría, pero la única
alternativa que hemos encontrado es hacer un análisis y tranformación
código a código:

```python
Tree = recursive(lambda Tree: domain.Boolean() | domain.Tuple(Tree(), Tree()))

Tree = recursive(lambda Tree: (
    domain.Boolean() |
    domain.Tuple(Tree(), Tree()))
)
```

Los dominios creados con la función `recursive` paran cuando detectan
un número de "llamadas" recursivas sobre si mismos. Por supuesto
existe un valor por defecto para ese número, pero se puede cambiar:

```python
Tree = recursive(lambda Tree: (
    domain.Boolean() |
    domain.Tuple(Tree(max_depth= 4), Tree(max_depth= 7)))
)
```

Si te proporciona más tranquilidad de espíritu, puedes pensar que la
función _recursive_ es la homónoma del `let rec` de otros lenguajes.


TODO: No funciona con:

```python
TreeA = recursive(lambda TreeA: (
     domain.Boolean() |
	 domain.Tuple(TreeA(), TreeB()))
)

TreeB = recursive(lambda TreeB: (
     domain.Integer() |
	 domain.Tuple(TreeA(), TreeA()))
)
```


# Trabajo futuro

## Terminar lo empezado

Hay cosas marcadas con TODO

## Máquinas de estado


## Crecimiento exponencial

Si tenemos varios cuantificadores universales en la misma propiedad,
esto es equivalente a tener un cuantificador universal sobre el
productor cartesiano de los dominios cuantificados.

Una implementación naïve toma el número establecido de muestras para
cada dominio. Esto significa que el número final de iteraciones crece
exponencialmente con el número de cuantificadores:

```
100 muestras x 100 muestras x ...
```

En estos casos, necesitamos una forma de establecer el número de
muestras de cada domino para limitar el número total de pruebas.



## Estrategias de generación y calidad de las muestras

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


Respecto a la calidad de las muestras, no sé. Algunas ideas:

  - Cobertura, número de fallos encontrados.
  
  - Variabilidad, distribución estadística de las muestras.
  

## Integración con pytest, ...

El principal problema va a ser el "reporting", en pytest no es muy
configurable.


## Shrinking

En principio no debería verse afectado por la forma en se declaran los
dominios, o sea que no parece que haya mucho trabajo por este lado.


## Combinadores

¿ Cosas como _such\_that_ ?
¿ Suponen un problema de eficiencia ?
Nada nuevo bajo el sol.


## Dominio de funciones

Un domino de funciones `A -> B` podría implementarse como un
diccionario por cada función. No parece buena idea generar el código
de la función. Como el dominio de la función normalmente también será
infinito, el diccionario tiene que ser "perezoso".


# Miscellanea

## forall y exists en el predicado

En general no tiene sentido. Pero si queremos hacerlo para dominos
suficientemente finitos, podemos usar las funciones de python. P.e.:

```python
@forall(l= domain.List(domain.Int()))
def max_returns_max_item(l):
    mx = max(l)
	return all(not x > max for x in domain.finite(l))
```

o

```python
@forall(l= domain.List(domain.Int()))
def max_returns_max_item(l):
    mx = max(l)
	return not any(x > max for x in domain.finite(l))
```


El ejemplo está forzado porque no necesitamos hacer
`domain.finite(l)`.


## Implementar un dominio "con código"

En la implementación del módulo `domain` los dominios son objetos de
tipo `domain.Domain`. Si queremos implementar un nuevo tipo de
dominio, podemos derivar esa subclase.

Por ejemplo si queremos implementar el dominio de nombres de trabajos
usando la misma librería, `faker`, que usa el módulo de dominios:

```python
class Job(domain.Domain):
    def __iter__(self) -> Iterator:
        while True:
            yield domain.fake.job()

    def __str__(self):
        return f"Job()"
```

TODO: Ahora mismo no hay una gestión explícita de las _semillas_ para
los números pseudoaleatorios. Por eso tenemos que usar `domain.fake`,
de esta forma nos aseguramos de que estamos usando la misma semilla
que el módulo `domain`.
