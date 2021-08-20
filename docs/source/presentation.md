# Introduction

Antes de comenzar a escribir esta librería, ya existían multiples
librerías de _PBT_ para diversos lenguajes de programación, incluyendo
_python_. Entonces la pregunta obvia es "¿ por qué otra librería
?". En nuestro caso, queríamos probar:

  - ¿ es factible otra aproximación al diseño e implementación de la
    librería ?, y
  
  - en caso afirmativo, ¿ usando esa librería, las pruebas son más
    sencillas de escribir y leer ?
	
Como es lógico, con este objetivo en mente, los primeros desarrollos
se centran en responder estas preguntas. Esto significa que dejamos de
lado cuestiones como el shrinking o las estrategias de selección de
muestras.

No se nos escapa que una libería de esta naturaleza no es viable en
producción sin las características que, inicialmente, hemos dejado de
lado. Por tanto, una vez completados los primeros desarrollos y
contestadas las preguntas iniciales, si el resultado es positivo, los
siguientes pasos serían:

  - continuar el desarrollo para incorporar las características que
    faltan
	
  - usar el conocimiento adquirido para mejorar algunas librería
    existentes
	
_N.B.:_ Las opciones anteriores no son excluyentes.


## Visión

Nuestra aproximación al diseño e implementación de la librería se base
en los siguientes puntos:


  - Existe una formulación matemática de las _propiedades_.
  
    Esto quiere decir que ya tenemos una terminología estableciada y
    de ámplio reconocimiento. Ajustémonos a ella.
	
  - El concepto es simple. La implementación debe ser simple.
  
  - En la medida de lo posible, los distintos tipos de elementos que
    conforman una propiedad se deben traducir en elementos propios del
    lenguaje de programación.
	
	Esto se debe hacer creando código _idiomatic_. Hay que evitar la
    tentación de usar las construcciones del lenguaje de formas
    distintas a las formas para las que fueron diseñadas, sólo para
    conseguir que el código de las pruebas mimetize la formulación
    convencional de las propieades.

Veamos un ejemplo de estas ideas. Si tomanos la propiedad:

```
∀x∊ℤ, x·(-x) = -(x^2)
```

Una vez traducida a código python, tendríamos:

```python
@forall(x= dom.Int())
def prop_example(x) -> bool:
    return (x * -x) == -(x**2)
```
