# Developing guidelines

Pautas a seguir para que todos trabajemos sobre el mismo desarrollo.

## Setup


### Build tool
`poetry`
  
  
### Setup manual publishing to PyPi

Es sólo para emergencias porque ya hay un workflow en github que
publica el paquete en _pypi_ cada vez que publicamos una _release_.

Usaremos la autenticación con el api token:

`poetry config pypi-token.pypi ...`
  
  
### Setup publish to PyPiTest

También usamos autenticación con el api token:

```sh
$ poetry config repositories.testpypi https://test.pypi.org/legacy/
$ poetry config pypi-token.testpypi ...
```

```sh  
$ poetry publish -r testpypi
```


### Remote repository

La autenticación es por ssh.


### Local repository

### .gitignore

Teoría: no incluir las excepciones de tu editor de texto porque al
resto del mundo no les importa. En lugar de eso, incluir esas
excepciones en tu configuración de usuario.

Aún así, '*~' está incluido porque es muy común.


## Coding style

### Type Hinting (Python 3.5+)

Sí.


### Coding style

¿ Usar fake y similares ?


### Uso del TODO

Algunos todos tienen más sentido como comentarios en el código.
Haría falta algo para extraerlos.

¿ Los enlazamos con los issues en github ?


## Github flow

1. Una rama por issue, ya sea bugfix, feature, documentation, ...

2. Al acabar el trabajo, se hace un PR

3. Una vez mezclado con éxito, se borra la rama



## Releases

Para los nombres de versiones seguimos el _semantic versioning_.

Las _realeases_ se crean automáticamente con una GitHub Action
cuando se etiqueta una versión como `v...`, por ejemplo:

```sh
git tag v0.1.2
git push --tags
```

El workflow correspondiente en github:

1. Ejecuta los tests.
2. Comprueba que se puede construir la documentación de usuario.
3. Construye y publica el paquete en PyPi.
4. Crea una _release_ en GitHub.

Al crear la release se activa el webhook que lanza la compilación de
la documentación de usuario en ReadTheDocs.




