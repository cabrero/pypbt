## Philosophy

Este diseño se centra en la representación de las _propiedades_ en un
lenguaje de programación concreto: python. El reto principal es
conseguir que sea sencillo definir y manipular los _dominios_ de las
variables.

La idea en la que nos basamos es emplear estructuras del lenguaje de
programación que encajen con el concepto de domino y al mismo tiempo
se puedan manipular con sus operaciones habituales.


> En relación a este trabajo. Las estructuras y operaciones que usemos
> para implementar los dominios es muy probable que existan en otros
> lenguajes de programación actuales. A priori es posible trasladar
> los resultados a esos lenguajes.


## Teminology

Usaremos la terminología más cercana posible a la formulación
matemática de una propiedad, porque:

  - Nos proporciona un lenguaje más universal.
  
  - Evitamos usar terminos cercanos a la implementación. P.e.:
    _generador_ para referirnos a un dominio.
        
  - Evitamos usar terminos confusos. P.e. _generador_ es una
    construcción en muchos lenguajes de programación.
  
  - Parece que chanamos más.
  
  


## TBD

  - Shrinking
  
  - Calidad de las muestras de los dominios generadas.
  
  - Integración con otras herramientas: `pytest`, `covertura`, ...
  
  - State machines
  


## Implementation related stuff

### Domains

Domains are represented as python iterables. However we implemt them
as objects of type `Domain` because these objects:

  - Have their own `__str__` mehtod
  
  - May have arguments in the constructor, like `min_size`,
    `max_size`, ...
	
  - We may implement additional operators like _union_: `|`.
  
  - Each one could have its own seed.
  

### Domain Expressions

Son expresiones que evaluan a un `Domain`. Es decir que son otra forma
de representar un dominio.

Las expresiones `DomainExpr` que vamos a tener en cuenta son:

- Un tipo de dato que sea iterable. Su uso principal es
  representar dominios finitos. P.e. una lista.

- Otro tipo de iterables que podamos crear con el propio lenguaje o
  algún módulo. Son muy útiles para aplicar transformaciones sobre un
  dominio. P.e. `filter`, `map`, ... o las _generator expressions_
  `(x*2 for x in ...) `

  Ejemplos:

  ```python
  @forall(x= (a for a in domain.Int() if a < 20))

  @forall(x= filter(lambda a: a > 42, domain.Int())

```
### Unbounded Domain

Viene siendo una domain expression donde tenemos variables sin ligar,
i.e. sin asignar un valor. Estas variable quedan evaluadas por un
quantificador "más externo".

Por ejemplo la variable x en la propiedad:

```
forall y in Integer[inf,x] ...
```

está sin ligar, pero en la siguiente propiedad sí está ligada:

```
forall x in Integer, y in Integer[-inf,x] ...
```

La implementación directa sería:

```python
@forall(x= Interger())
@forall(y= Integer(lower= x))
```

Pero en el segundo `forall` la `x` está fuera del _scope_ del primero
y, por tanto, está _libre_, a.k.a sin ligar. Lo natural es que durante
la ejecución de las pruebas, la librería le asigne cada uno de los
valores que va generando para el dominio del primer cuantificador.

Pero para que la librería pueda hacer esa asignación, necesitamos
alguna construcción del lenguaje que nos lo permita. Una forma natural
de hacerlo es envolver la expresión de dominio en una función cuyos
parámetros sean las variable libres de la expresión de dominio:

```python
@forall(x= Interger())
@forall(y= lambda x: Integer(lower= x))
```

Igual que hacemos con las funciones generadoras, estás funciones "de
binding" también las envolvermos en un objeto. Este objeto tendrá una
operación para ligar las variables libres y devolver un objeto
`Domain`.


## Exahustible Domains

Algunos dominios son finitos y su cardinalidad es suficientemente
pequeña como para poder comprobar una propiedad para todos los objetos
del dominio. En estos casos podríamos incluso usar un _cuantificador
existencial_.

Comprobar si un dominio es 'suficientemente' finito es demasiado
complejo. Es reponsabilidad del cliente marcar los dominios como tales:

```python
@exists(y= domain.exhaustive_domain(range(1,9)))
```

## Recurrent Domains

En la definición de los objetos de un dominio puede aparecer objetos
del propio dominio. De ahí lo de _recursivo_. El ejemplo mítico son
los árboles.

> _N.B._ Para que la recursión se pueda resolver tiene que haber al
> menos un caso base a mayores de un paso recursivo. Esta condición
> sólo se da en dominios creados a partir de operadores como el `|`.

Como primera aproximación pensemos en un dominio cuyos objetos son
árboles binarios de cualquier tamaño y cuyos nodos hoja son valores
booleanos:

TODO: formulación "más matematica"

```python
Tree = domain.Boolean() | domain.Tuple(Tree(), Tree())
```

El código anterior no se puede usar directamente porque:

- En la parte derecha la variable `Tree` todavía no está definida.

  Podríamos arreglarlo diferiendo la evaluación de `Tree()`
  envolviendola en una lambda: `lambda: Tree()`, pero nos complicaría
  la implementación del runtime y la solución del siguiente problema.

- Si `Tree` estuviese definida, entraríamos en un bucle infinito.

Para solucionar estos problemas hay que marcar explicitamente las
definiciones recursivas. El código resultante es un poco _contrived_,
pero no parece fácil hacer algo más natural sin analizar el código
fuente

```python
Tree = recursive(lambda Tree: domain.Boolean() | domain.Tuple(Tree(), Tree()))
Tree = recursive(lambda Tree: (
    domain.Boolean() |
    domain.Tuple(Tree(), Tree()))
)
```

## Things to discuss with yourself

Normalmente los __Dominios__ son conjuntos infinitos de objetos.
Incluso cuando no lo son, su cardinalidad puede ser demasiado grande
como para poder comprobar una propiedad con todos los objetos del
dominio. Por eso en PBT sólo comprobamos una propiedad contra un
subconjunto elegido al azar.

Aun así, en python podemos representar los dominios como _iterables_
porque sus _iterators_ pueden ser _lazy_.

Podemos decir que la función que nos devuelve un iterador sobre
un dominio sería:

```
iter :: Domain -> Iterator[DomainObject]
```

Pero no nos interesa iterar sobre los objetos del dominio siempre con
la misma secuencia. Para el PBT nos interesa que cada iterador recorra
el dominio en un orden al azar distinto de los otros iteradores.

Pero tampoco queremos que el orden sera realmente aleatorio, sino
_pseudoaleatorio_ porque, cuando encontramos un error, una vez
corregido, queremos repetir la misma secuencia _pseudoaleatoria_ de
objetos para comprobar que el fix es bueno.

Esto quiere decir que esa función no devuelve siempre el mismo
resultado para un mismo argumento.  Si esta falta de transparencia
referencial nos crea sarpullido, podemos pensar en la función como:

```
ite :: Domain -> Seed -> Iterator[DomainObject]
```

De esta forma para un dominio y semilla devuelve siempre un iterador
que realiza el mismo recorrido, o sea que lo podemos considerar el
mismo resultado.

De todas formas la implementación es de la primera forma ¯\_(ツ)_/¯.
