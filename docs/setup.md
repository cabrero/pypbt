# Build tool

  `poetry`
  
  
## Setup manual publishing

  `poetry config pypi-token.pypi ...`
  
  No debería hacer falta porque hay una acción en github para publicar las realeases.
  
## Setup publish to pytest

  `poetry config repositories.testpypi https://test.pypi.org/legacy/`
  
  `poetry config pypi-token.testpypi ...`
  
  `poetry publish -r testpypi`
