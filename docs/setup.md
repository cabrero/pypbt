# Build tool

  `poetry`
  
  
## Setup manual publishing

  `poetry config pypi-token.pypi ...`
  
  No debería hacer falta porque hay una acción en github para publicar las realeases.
  
## Setup publish to pytest

  `poetry config repositories.testpypi https://test.pypi.org/legacy/`
  
  `poetry config pypi-token.testpypi ...`
  
  `poetry publish -r testpypi`


# Github Releases

Cuando se etiqueta una versión como `v...`, por ejemplo:

```sh
git tag v0.1.2
git push --tags
```

Se lanza un workflow en github que:

1. Ejecuta los tests.
2. Comprueba que se puede construir la documentación de usuario.
3. Construye y publica el paquete en PyPi.
4. Crea una _release_ en GitHub.

Al crear la release se activa el webhook que lanza la compilación de
la documentación de usuario en ReadTheDocs.
