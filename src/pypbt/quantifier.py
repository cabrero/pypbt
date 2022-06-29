from __future__ import annotations

import inspect
from itertools import islice
import textwrap
from typing import Callable, get_args, Literal, NamedTuple, Union

from .domain import domain_expr, Domain, DomainCoercible, Env


# Property = ForAll Property
#          | Exists Property
#          | Predicate
#
# Posibles críticas a esta definición de `Property`:
#
#   - `Property = Predicate` es un caso muy extremo de propiedad.
#
#   - Nada impide que el programado construya mal una propiedad. En concreto
#     puede terner variables libres (en nuestro caso, sin cuantificar).
#     Sin embargo el conjunto de errores que puede cometer un programador es
#     infinito. No podemos evitarlos todos.
#
# Las variables libres en un predicado pueden no ser tal cosa si incorporamos
# conceptos como las `fixtures` de `pytest`. En este caso son variables que
# no están ligadas en ningún cuantificador, pero están ligadas en otro contexto
# más global (y compartido por varias propiedades).


# :( property es una palabra clave en python
class QCProperty: pass


def is_qcproperty(x):
    return isinstance(x, QCProperty)


VarName = str




#---------------------------------------------------------------------------
# Expresiones de dominio con variables libres
#---------------------------------------------------------------------------
# Expresiones con variables libres. Una vez ligadas las variables, si
# evaluamos la expresión, obtenemos un dominio.
#
# Se representa como una función cuyos parámetros son las variables libres.

DomainLambda = Callable[[...], DomainCoercible]

class DomainExprWithFreeVars(NamedTuple):
    fun: DomainLambda
    unbound_vars: list[str]

    def __str__(self) -> str:
        return f"{self.unbound_vars} => {self.fun}"


def domain_expr_with_free_vars(fun: DomainLambda) -> DomainExprWithFreeVars:
    signature = inspect.signature(fun)
    unbound_vars = list(signature.parameters.keys())
    if len(unbound_vars) == 0:
        raise TypeError(f"no free variables")
    return DomainExprWithFreeVars(fun, unbound_vars)
    

def bind_and_eval(expr: Union[DomainExprWithFreeVars, Domain],
                  env: Env) -> Domain:
    if not isinstance(expr, DomainExprWithFreeVars):
        return expr
    # A la hora de construir kwargs ignoramos la variables que no
    # están en env para que el error salte al llamar a la función
    kwargs = { k: env[k] for k in expr.unbound_vars if k in env}
    return domain_expr(expr.fun(**kwargs))
    

#---------------------------------------------------------------------------
# Tipos.
# Syntax sugar y otras facilities
#---------------------------------------------------------------------------
# Parámetro de la variable en el decorador de cuantificación.
QArg = Union['DomainLambda', DomainCoercible]


def _preprocess_domain(arg: QArg) -> Domain:
    if getattr(arg, '__name__', None) == '<lambda>':
        return domain_expr_with_free_vars(arg)
    else:
        return domain_expr(arg)


class Left:
    def __init__(self, e):
        # TODO: e puede ser Env o [Env,Exception]
        #       regularizar esto
        self.e = e

    def __bool__(self):
        return False

    def __str__(self):
        return f"Left({self.e})"
    
    
# -- Either bool
CheckResult = Union[Left, Literal[True]]


#---------------------------------------------------------------------------
# Predicados
#---------------------------------------------------------------------------
# Implementación (función python) de un predicado
PredicateFun = Callable[..., bool]


# Adaptador de predicado a QC.
class Predicate(QCProperty):
    def __init__(self, pred: PredicateFun):
        self.pred = pred
        
    def __call__(self, /, env: Env) -> Iterator[CheckResult]:
        try:
            result = self.pred(**env) or Left(env)
        except Exception as e:
            result = Left((env, e))
        yield result

    def __str__(self):
        return str(self.pred.__name__)


#---------------------------------------------------------------------------
# Cuantificadores
#---------------------------------------------------------------------------
# Podríamos implementar los cuantificadores como funciones (cierres).
# Los implementamos así para incluir otras operaciones interesantes
# como p.e. `__str__`

# Todas las propiedades se "ejecutan" en un `Environment` que contiene
# las variables ligadas por cada uno de los cuantificadores.


class ForAll(QCProperty):
    def __init__(self,
                 quantifed_var: VarName,
                 domain_obj: Domain,
                 qcproperty: QCProperty,
                 n_samples: int):
        self.quantifed_var = quantifed_var
        self.domain_obj = domain_obj
        self.qcproperty = qcproperty
        self.n_samples = n_samples

    def __call__(self, /, env: Env) -> Iterator[CheckResult]:
        quantifed_var = self.quantifed_var
        if quantifed_var in env:
            raise TypeError(f"Variable {quantifed_var} is shadowed in {self}")

        domain_obj = bind_and_eval(self.domain_obj, env)
        qcproperty = self.qcproperty

        # Si el dominio está marcado como finito recorremos el dominio entero
        if domain_obj.is_exhaustible:
            domain_samples = domain_obj.exhaustible
        else:
            domain_samples = islice(domain_obj, self.n_samples)
            
        for sample in domain_samples:
            yield from qcproperty(env= {**env, quantifed_var: sample})

    def __str__(self):
        return (f"ForAll {self.quantifed_var}: {self.domain_obj}\n"
                f"{textwrap.indent(str(self.qcproperty), '  ')}")

        
class Exists(QCProperty):
    def __init__(self,
                 quantifed_var: VarName,
                 domain_obj: Domain,
                 qcproperty: QCProperty):
        if not isinstance(qcproperty, Predicate):
            # TODO: Podríamos comprobar que todos los cuantificadores dentro
            #       de este Exists son exhaustivos ?
            #       Seguramente es más sencillo añadir un parámetro opcional
            #       a la función `qc` que indique si tiene que ser exhaustive
            raise TypeError(f"This tool cannot check Exists on another quantifier")
        
        self.quantifed_var = quantifed_var
        self.domain_obj = domain_obj
        self.qcproperty = qcproperty

        
    def __call__(self, /, env: Env) -> Iterator[CheckResult]:
        quantifed_var = self.quantifed_var
        if quantifed_var in env:
            raise TypeError(f"Variable {quantifed_var} is shadowed in {self}")

        domain_obj = bind_and_eval(self.domain_obj, env)
        qcproperty = self.qcproperty

        if not domain_obj.is_exhaustible:
            raise TypeError(f"It's not possible to check existence "
                            f"in non exhaustive domain: {domain_obj}")
        
        for sample in domain_obj.exhaustible:
            if any(qcproperty(env= {**env, quantifed_var: sample})):
                yield True
                return
                
        yield Left(f"{env} -> {str(self)}")
        return

    def __str__(self):
        return f"Exists {self.quantifed_var}: {self.domain_obj} / {self.qcproperty}"
        
    
#---------------------------------------------------------------------------
# decoradores
#---------------------------------------------------------------------------
def forall(n_samples: int= 100, **binds):
    """Decorates a predicate funcion or another decorator with a forall quantifier.

    Parameters
    ----------
    n_samples : int
        The number of samples to check.
    **binds
        The quantified variables. Actually the number of quantified
        variables is limited to 1.

    Returns
    -------
    ForAll
        An object implementing the property as a callable.
    """
    if len(binds) != 1:
        # TODO: permitir esto como "azúcar sintáctico" ?
        #       Es decir que
        #           @forall(x= ..., y= ...)
        #       sea lo mismo que
        #           @forall(x= ...)
        #           @forall(y= ...)
        #       La pregunta es si el código es más inteligible.
        raise TypeError(f"Must bind just one variable, but {len(binds)} binded")
    
    def factory(arg):
        if is_qcproperty(arg):
            qcproperty = arg
        else:
            qcproperty = Predicate(arg)
        quantifed_var, obj = list(binds.items())[0]
        domain_obj = _preprocess_domain(obj)
        return ForAll(quantifed_var, domain_obj, qcproperty, n_samples= n_samples)

    return factory


def exists(**binds):
    """Decorates a predicate funcion or another decorator with an existencial quantifier.

    Parameters
    ----------
    **binds
        The quantified variables. Actually the number of quantified
        variables is limited to 1.

    Returns
    -------
    Exists
        An object implementing the property as a callable.

    !!! warning
        Every variable must be quantified over an exhaustible domain.

    """
    if len(binds) != 1:
        # TODO: permitir esto como "azúcar sintáctico" ?
        raise TypeError(f"Must bind just one variable, but {len(binds)} binded")

    def factory(arg):
        if is_qcproperty(arg):
            qcproperty = arg
        else:
            qcproperty = Predicate(arg)
        quantifed_var, obj = list(binds.items())[0]
        domain_obj = _preprocess_domain(obj)
        return Exists(quantifed_var, domain_obj, qcproperty)

    return factory

