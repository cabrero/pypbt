from __future__ import annotations

import inspect
from itertools import islice
import textwrap
from typing import Callable, get_args, Literal, NamedTuple, Union

from .domains import domain_expr, Domain, DomainCoercible


DEFAULT_N_SAMPLES = 100


# Property = ForAll Property
#          | Exists Property
#          | Predicate
#
# Críticas a esta definición de `Property`:
#
#   - `Property = Predicate` es un caso muy extremo de propiedad.
#
#   - Nada impide que el programado construya mal una propiedad. En
#     concreto puede terner variables libres, i.e., en nuestro caso,
#     sin cuantificar.  Sin embargo el conjunto de errores que puede
#     cometer un programador es infinito. No podemos evitarlos
#     todos. Tampoco es algo que pudiese evitar la mayoría de sistemas
#     de tipos.
#
# TODO: No está reflejado el hecho de que una propiedad pueda tener
# variables, libres o ligadas.
#
# TODO: Las variables libres en un predicado pueden no ser tal cosa si
# incorporamos conceptos como las `fixtures` de `pytest`. En este caso
# son variables que no están ligadas en ningún cuantificador, pero
# están ligadas en otro contexto más global (y compartido por varias
# propiedades).


# :( `property` is a built-in function in python
class QCProperty: pass


def is_qcproperty(x):
    return isinstance(x, QCProperty)


def qcproperty(arg) -> QCProperty:
    if is_qcproperty(arg):
        return arg
    else:
        return Predicate(arg)


# Entorno. Guarda las ligaduras de variables.
VarName = str
Env = dict[VarName, DomainCoercible]


# --------------------------------------------------------------------------------------
# Domain LambdaExpr
# --------------------------------------------------------------------------------------
# Abstractions containing free variables that will evaluate to a Domain.
# The term should be a DomainCoercible expression.
#
# Thus, actually, `Callable` means `lambda`.
DomainLambdaExpr = Callable[[...], Domain]

def is_lambda_expr(arg: QArg) -> bool:
    return getattr(arg, '__name__', None) == '<lambda>'


BOUND_VARS_ATTR = '__domain_lambda_expr_bound_vars__'


def domain_lambda_expr(expr: Callable) -> DomainLambdaExpr:
    # El cálculo de las bound_vars lo hacemos aquí en lugar de hacerlo
    # en `reduce_expr` porque esa función se llama por cada sample del
    # quantificador "padre":
    #
    # @forall(xs= domain.List(domain.Int(), min_len= 4, max_len= 4))
    # @forall(x= lambda xs: domain_expr(xs, is_exhaustible= True))
    signature = inspect.signature(expr)
    bound_vars = list(signature.parameters.keys())
    if len(bound_vars) == 0:
        raise TypeError(f"no bound variables in {expr}")
    setattr(expr, BOUND_VARS_ATTR, bound_vars)
    return expr


def reduce_expr(expr: DomainLambdaExpr, env: Env) -> Domain:
    bound_vars = getattr(expr, BOUND_VARS_ATTR, None)
    if bound_vars is None:
        return expr
    # A la hora de construir kwargs ignoramos la variables que no
    # están en env para que el error salte al llamar a la función
    kwargs = { k: env[k] for k in bound_vars if k in env }
    return domain_expr(expr(**kwargs))


# --------------------------------------------------------------------------------------
# Syntax sugar
# --------------------------------------------------------------------------------------
"""Values binded to the quantified variables.

It's not very sound, because a `DomainLambadTerm` is also a
`DomainCoercible`. As any object is coercible.
"""
QArg = Union[DomainLambdaExpr, DomainCoercible]


def desugar_var_value(arg: QArg) -> Domain:
    if is_lambda_expr(arg):
        return domain_lambda_expr(arg)
    else:
        return domain_expr(arg)


#---------------------------------------------------------------------------
# 
#---------------------------------------------------------------------------
class Left:
    def __init__(self, env, exc= None):
        # TODO: e puede ser Env o [Env,Exception]
        #       regularizar esto
        self.env = env
        self.exc = exc

    def __bool__(self):
        return False

    def __str__(self):
        if self.exc is None:
            return f"Left({self.env})"
        else:
            return f"Left({self.env}, {self.exc})"
    
    
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
            result = Left(env= env, exc= e)
        yield result

    def __str__(self):
        return str(self.pred.__name__)

    def get_source(self) -> str:
        source, line = inspect.getsourcelines(self.pred)
        return line, "".join(source)
    

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
                 quantified_var: VarName,
                 domain_obj: Domain,
                 qcproperty: QCProperty,
                 n_samples: int):
        self.quantified_var = quantified_var
        self.domain_obj = domain_obj
        self.qcproperty = qcproperty
        self.n_samples = n_samples

    def __call__(self, /, env: Env) -> Iterator[CheckResult]:
        quantified_var = self.quantified_var
        if quantified_var in env:
            raise TypeError(f"Variable {quantified_var} is shadowed in {self}")

        domain_obj = reduce_expr(self.domain_obj, env)
        prop = self.qcproperty

        # Si el dominio está marcado como finito recorremos el dominio entero
        if domain_obj.is_exhaustible:
            domain_samples = domain_obj.exhaustible
        else:
            domain_samples = islice(domain_obj, self.n_samples)
            
        for sample in domain_samples:
            yield from prop(env= {**env, quantified_var: sample})

    def __str__(self) -> str:
        return (
            f"ForAll {self.quantified_var} in {self.domain_obj}\n"
            f"{textwrap.indent(str(self.qcproperty), '  ')}"
        )

    def get_source(self) -> str:
        return self.qcproperty.get_source()

        
class Exists(QCProperty):
    def __init__(self,
                 quantified_var: VarName,
                 domain_obj: Domain,
                 qcproperty: QCProperty):
        if not isinstance(qcproperty, Predicate):
            # TODO: Podríamos comprobar que todos los cuantificadores dentro
            #       de este Exists son exhaustivos ?
            #       Seguramente es más sencillo añadir un parámetro opcional
            #       a la función `qc` que indique si tiene que ser exhaustive
            raise TypeError(f"This tool cannot check Exists on another quantifier")
        
        self.quantified_var = quantified_var
        self.domain_obj = domain_obj
        self.qcproperty = qcproperty

        
    def __call__(self, /, env: Env) -> Iterator[CheckResult]:
        quantified_var = self.quantified_var
        if quantified_var in env:
            raise TypeError(f"Variable {quantified_var} is shadowed in {self}")

        domain_obj = reduce_expr(self.domain_obj, env)
        prop = self.qcproperty

        if not domain_obj.is_exhaustible:
            raise TypeError(f"It's not possible to check existence "
                            f"in non exhaustive domain: {domain_obj}")
        
        for sample in domain_obj.exhaustible:
            if any(prop(env= {**env, quantified_var: sample})):
                yield True
                return
                
        yield Left(env= env)
        return

    def get_source(self) -> str:
        return self.qcproperty.get_source()
    
    def __str__(self):
        return (
            f"Exists {self.quantified_var} in {self.domain_obj}\n"
            f"{textwrap.indent(str(self.qcproperty), '  ')}"
        )
        
    
#---------------------------------------------------------------------------
# Decorators
#---------------------------------------------------------------------------
def forall(n_samples: int= DEFAULT_N_SAMPLES, **binds):
    """Decorates a predicate funcion or another decorator with a forall quantifier.

    Parameters
    ----------
    n_samples : int
        The number of samples to check.
    **binds
        The quantified variables. The number of quantified
        variables must be 1. In order to quantify more than
        one variable, you should write each variable in its own
        `@forall`.


    Returns
    -------
    ForAll
        An object implementing the property as a callable.
    """
    if len(binds) != 1:
        # TODO: ¿ queremos implementar forall(x= ..., y= ...) como
        #         forall(x,y= ...,...) ?
        #       Es decir forall(t= Tuple(...,...) x,y= t
        raise TypeError(f"Must bind just one variable, but {len(binds)} binded")
    var, obj = next(iter(binds.items()))
    
    def factory(arg):
        return ForAll(
            quantified_var= var,
            domain_obj= desugar_var_value(obj),
            qcproperty= qcproperty(arg),
            n_samples= n_samples
        )

    return factory


def exists(**binds):
    """Decorates a predicate funcion or another decorator with an existencial quantifier.

    Parameters
    ----------
    **binds
        The quantified variables. The number of quantified
        variables must be 1. In order to quantify more than
        one variable, you should write each variable in its own
        `@exists`.


    Returns
    -------
    Exists
        An object implementing the property as a callable.

    !!! warning
        Every variable must be quantified over an exhaustible domain.

    """
    if len(binds) != 1:
        raise TypeError(f"Must bind just one variable, but {len(binds)} binded")
    var, obj = next(iter(binds.items()))
    
    def factory(arg):
        return Exists(
            quantified_var= var,
            domain_obj= desugar_var_value(obj),
            qcproperty= qcproperty(arg)
        )

    return factory

