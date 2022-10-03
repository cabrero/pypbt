from __future__ import annotations

import inspect
from itertools import cycle, islice
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
class CounterExample(NamedTuple):
    env: Env

    def __bool__(self) -> bool:
        return False

    
class PredicateError(NamedTuple):
    exc: Exception
    env: Env

    def __bool__(self) -> bool:
        return False
    
    
CheckResult = Union[
    Literal[True],
    CounterExample,
    PredicateError,
]


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
            result = self.pred(**env) or CounterExample(env)
        except Exception as e:
            result = PredicateError(exc= e, env= env)
        yield result

    def __str__(self):
        return str(self.pred.__name__)

    def get_predicate(self) -> PredicateFun:
        return self.pred
    

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
                 quantifications: dict[VarName, Domain],
                 qcproperty: QCProperty,
                 n_samples: int):
        self.quantifications = quantifications
        self.qcproperty = qcproperty
        self.n_samples = n_samples

    def __call__(self, /, env: Env) -> Iterator[CheckResult]:
        # forall(x= ..., y= ...) funciona como forall(x, y= ..., ...)
        # Es decir funciona como una suma. Igual que haria en
        # forall(t= Tuple(...,...) x,y= t
        #
        # Por otra parte el producto, a.k.a. producto cartesiano sería
        # forall(x= ...)
        #     forall(y= ...)
        
        quantifications = self.quantifications
        if any(wrong_name := var in env for var in quantifications.keys()):
            raise TypeError(f"Variable {wrong_name} is shadowed in {self}")

        prop = self.qcproperty

        # Si tenemos una única variable cuantificada y el dominio está
        # marcado como exhaustible recorremos el dominio entero. Pero si
        # tenemos una suma, aunque todos los dominios sean
        # exahustibles, no podemos hacer el recorrido exhaustivo
        # porque la cardinalidad de los dominios puede no coincidir.
        # Tampoco parece que tenga sentido ninguna forma de
        # combinarlos. El número de samples es el mismo para todos los
        # dominios.
        if len(quantifications) == 1:
            var, dom = next(iter(quantifications.items()))
            dom = reduce_expr(dom, env)
            if dom.is_exhaustible:
                samples = dom.exhaustible
            else:
                samples = islice(dom, self.n_samples)
            for sample in samples:
                yield from prop(env= {**env, var: sample})
        else:
            iterators = { var: cycle(reduce_expr(domain_obj, env))
                          for var, domain_obj in quantifications.items() }
            samples = (
                {var: next(it) for var, it in iterators.items()}
                for _ in range(self.n_samples)
            )        
            for kwargs in samples:
                yield from prop(env= {**env, **kwargs})

    def __str__(self) -> str:
        return (
            f"ForAll {self.quantified_var} in {self.domain_obj}\n"
            f"{textwrap.indent(str(self.qcproperty), '  ')}"
        )

    def get_predicate(self) -> str:
        return self.qcproperty.get_predicate()

                
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
            env = {**env, quantified_var: sample}
            for result in prop(env= env):
                if result:
                    yield True
                    break
                elif isinstance(result, PredicateError):
                    yield result
                    break
            else:
                yield CounterExample(env)

    def get_predicate(self) -> str:
        return self.qcproperty.get_predicate()
    
    def __str__(self):
        return (
            f"Exists {self.quantified_var} in {self.domain_obj}\n"
            f"{textwrap.indent(str(self.qcproperty), '  ')}"
        )
        
    
#---------------------------------------------------------------------------
# Decorators
#---------------------------------------------------------------------------
def forall(*, n_samples: int= DEFAULT_N_SAMPLES, **binds):
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
    quantifications = {var: desugar_var_value(obj) for var, obj in binds.items()}

    def factory(arg):
        return ForAll(
            quantifications= quantifications,
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

