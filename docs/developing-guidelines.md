# Coding style

## Comments

  > “Code tells you how; Comments tell you why.”
  >
  > — Jeff Atwood (aka Coding Horror)


## External libraries

- Use as few as possible. Ideally no one. Avoid libraries that depend on
  many other libraries.

- Do not use `faker`

  ```python
  from faker import Faker
  fake = Faker() # Esta operación lleva mucho tiempo :(
                 # No puede estar en ningún bucle, iterador, ...
  ```

  Las secuencias de tipos básicos (números) no son buenas: hay demasiadas
  repeticiones de elementos, no se reproducen bien con la misma semilla.


## Pythonic

Exploiting the features of the Python language to produce code that is
clear, concise and maintainable.

Pythonic means code that doesn't just get the syntax right but that
follows the conventions of the Python community and uses the language
in the way it is intended to be used.

This is maybe easiest to explain by negative example, as in the linked
article from the other answers. Examples of unpythonic code often come
from users of other languages, who instead of learning a Python
programming patterns such as list comprehensions or generator
expressions, attempt to crowbar in patterns more commonly used in C or
java. Loops are particularly common examples of this.

For example in Java I might use:

```java
for(int index=0; index < items.length; index++) { items[index].performAction(); }
```

In Python we can try and replicate this using while loops but it would be cleaner to use:

```python
for item in items:
    item.perform_action()
```

Or, even a generator expression:

```python
(item.some_attribute for item in items)
```

So essentially when someone says something is unpythonic, they are
saying that the code could be re-written in a way that is a better fit
for pythons coding style.

Typing `import this` at the command line gives a summary of Python
principles. Less well known is that the source code for `import this`
is decidedly, and by design, unpythonic! Take a look at it for an
example of what not to do.

edited Feb 28 at 4:39

Toastrackenigma

answered Jul 29 '14 at 8:52

James

For an example of some more complex code, an "unpythonic"
implementation of the Vigenere cipher is made progressively more
"pythonic" in this answer (disclosure: my code and
opinions): stackoverflow.com/questions/2490334/… – Nick Nov 8 '17 at
0:46

Also perhaps worth noting that the general term is "idiomatic" – Louis Maddox Nov 13 '20 at 12:19

Idiomatic means following the conventions of the language. You want to
find the easiest and most common ways of accomplishing a task rather
than porting your knowledge from a different language.

non-idiomatic python using a loop with append:

```python
mylist = [1, 2, 3, 4]
newlist = []
for i in mylist:
    newlist.append(i * 2)
```

idiomatic python using a list comprehension:

```python
mylist = [1, 2, 3, 4]
newlist = [(i * 2) for i in mylist]
```


Un ejemplo un poco más skilled. Aparece en la intro de hypothesis y
está tomado de https://rosettacode.org/wiki/Run-length_encoding

Primero totalmente c-style

```python
def decode(lst):
    q = ""
    for i in range(0, len(lst)):
        character = lst[i][0] 
        count = lst[i][1] 
        q += character * count
    return q
        
```

Versión de la página. Más pythonic

```python
def decode(lst):
    q = ""
    for character, count in list:
        q += character * count
    return q
```

Versión más pythonic y más performant

```python
def decode(lst):
    return "".join(character * count for character, count in list)
```


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




