# .gitignore

Teoría: no incluir las excepciones de tu editor de texto porque al resto del mundo no les importa. En lugar de eso,
incluir esas excepciones en tu configuración de usuario.

Aún así, he incluido '*~' por si acaso.


# Uso del TODO

Algunos todos tienen más sentido como comentarios en el código.
Haría falta algo para extraerlos.


# Protocolos de uso del repositorio

  - Basar en workflow en Pull Requests

  - ¿ Al menos un branch por developer en github para que sea más fácil compartir ideas (teniendo en cuenta que somos dos) ?


# Type Hinting (Python 3.5+)

Sí.


# Coding style

¿ Usar fake y similares ?


# Comments

  > “Code tells you how; Comments tell you why.”
  >
  > — Jeff Atwood (aka Coding Horror)


# No usar faker

```python
from faker import Faker
fake = Faker() # Esta operación lleva mucho tiempo :(
               # No puede estar en ningún bucle, iterador, ...
```

Las secuencias de tipos básicos (números) no son buenas: hay demasiadas
repeticiones de elementos, no se reproducen bien con la misma semilla.
