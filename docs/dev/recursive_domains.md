# Dominios recursivos


Y la madre de todas las representaciones: estructuras de datos
recursivas.

En hypothesis:

```python
@st.composite
def composite_tree(draw):
	return draw(st.one_of(
		st.booleans(),
		st.tuples(composite_tree(), composite_tree()),
	))
```

Con nuestra aproximación podríamos "diferir" la creación de los
dominios para no tener un bucle infinito en tiempo de "compilación":

```python
Tree = lambda: domain.Boolean() | domain.Tuple(lambda: Tree(), lmabda: Tree())
```

Ahora falta evitar una recursión infinita durante la ejecución.

En hypotesis:

```python
tree = recursive(st.booleans(), lambda children: st.tuples(children, children), max_leaves=2)

json = recursive(
	none() | booleans() | floats() | text(printable),
	lambda children: lists(children, 1)
		| dictionaries(text(printable), children, min_size=1),
	max_leaves = 10)
)
```

La recursión se puede hace sobre el segundo parámetro, y `recursive`
funciona com un `one_of`.

Según la documentación:

> The way Hypothesis handles this is with the recursive() strategy
> which you pass in a base case and a function that, given a strategy
> for your data type, returns a new strategy for it.

> The size control of this works by limiting the maximum number of
> values that can be drawn from the base strategy.


En nuestra aproximación también tenemos que marcar el dominio como
recursivo:

```python
Tree = domain.recursive(lambda Tree: domain.Boolean() | domain.Tuple(Tree(), Tree()))
```

La idea es similar. Al fin y al cabo es la única viable: limitar el
número de "recursiones". En la práctica lo que limitamos es el
número de veces que podemos instanciar el mismo domino dentro de su
propia definición.

El número máximo tiene un valor por defecto, pero se puede
especificar como parámetro al "recursinstaciar" el dominio:

```python
Tree = domain.recursive(labmda Tree: (
		 domain.Boolean() |
		 domain.Tuple(Tree(max_depth= 6), Tree(max_depth= 4)))
)
```

```python
Json = domain.recursive(lambda Json: (
		 domain.None_() |
		 domain.Boolean() |
		 domain.Int() |
		 domain.List(Json()) |
		 domain.Dict(domain.Name(), Json())
))
``` 


