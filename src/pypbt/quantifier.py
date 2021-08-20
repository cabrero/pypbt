from __future__ import annotations

import inspect
import textwrap
from typing import Callable, NamedTuple, Union

from .domain import desugar_domain, Domain, DomainCoercible, Env, take


#---------------------------------------------------------------------------
# Expresiones de dominio con variables libres
#---------------------------------------------------------------------------
# Expresiones con variables libres. Una vez ligadas las variables, si
# evaluamos la expresión, obtenemos un dominio.
#
# Se representa como una función cuyos parámetros son las variables libres.

DomainLambda = Callable[[...], DomainCoercible]

class DomainExpr(NamedTuple):
    fun: DomainLambda
    unbound_vars: list[str]

    def __str__(self) -> str:
        return f"{self.unbound_vars} => {self.fun}"


def domain_expr(fun: DomainLambda) -> DomainExpr:
    signature = inspect.signature(fun)
    unbound_vars = list(signature.parameters.keys())
    if len(unbound_vars) == 0:
        raise TypeError(f"no free variables")
    return DomainExpr(fun, unbound_vars)
    

def bind_and_eval(expr: Union[DomainExpr, Domain], env: Env) -> Domain:
    if not isinstance(expr, DomainExpr):
        return expr
    # A la hora de construir kwargs ignoramos la variables que no
    # están en env para que el error salte al llamar a la función
    kwargs = { k: env[k] for k in expr.unbound_vars if k in env}
    return desugar_domain(expr.fun(**kwargs))
    

# class DomainExpr:
#     def __init__(self, expr: DomainLambda):
#         self.expr = expr
#         signature = inspect.signature(expr)
#         self.unbound_vars = list(signature.parameters.keys())
#         if len(self.unbound_vars) == 0:
#             raise TypeError(f"no free variables")

#     def bind(self, env: Env) -> Domain:
#         # TODO: ¿ bind es el nombre adecuado ?
#         # A la hora de construir kwargs ignoramos la variables que no
#         # están en env para que el error salte al llamar a la función
#         kwargs = { k: env[k] for k in self.unbound_vars if k in env}
#         return self.expr(**kwargs)

#     def __str__(self) -> str:
#         return f"{self.unbound_vars} => {self.expr}"


#---------------------------------------------------------------------------
# Tipos.
# Syntax sugar y otras facilities
#---------------------------------------------------------------------------
# Parámetro de la variable en el decorador de cuantificación.
QArg = Union['DomainLambda', DomainCoercible]


def _preprocess_domain(arg: QArg) -> Domain:
    try:
        return desugar_domain(arg)
    except TypeError:
        pass
    if callable(arg):
        return domain_expr(arg)
    else:
        raise TypeError(f"Expected a domain, got {arg}")


class Left:
    def __init__(self, e):
        self.e = e

    def __bool__(self):
        return False

    def __str__(self):
        return f"Left({self.e})"
    
    
def is_checkable(x):
    return hasattr(x, 'qc')


# -- Either bool
Checked = Union[bool, Left]

Checkable  = Union['Predicate', 'ForAll', 'Exists']


Pred = Callable[[...], bool] # Función de predicado


PropOrPred = Union['Predicate', 'ForAll', 'Exists', Pred]


#---------------------------------------------------------------------------
# Predicados
#---------------------------------------------------------------------------
# Wrapper de predicado para hacerlo Checkable
class Predicate:
    def __init__(self, pred: Pred):
        self.pred = pred
        
    def qc(self, env: Env) -> Iterator[Checked]:
        try:
            result = self.pred(**env) or Left(env)
        except Exception as e:
            result = Left(e)
        yield result

    def __str__(self):
        return str(self.pred.__name__)


#---------------------------------------------------------------------------
# Cuantificadores
#---------------------------------------------------------------------------
class ForAll:
    def __init__(self, var_name: str, domain_obj: Domain, checkable: Checkable, n_samples: int):
        self.var_name = var_name
        self.domain_obj = domain_obj
        self.checkable = checkable
        self.n_samples = n_samples

    def qc(self, env: Env) -> Iterator[Checked]:
        # Puesto que podemos componer varios cuantificadores, tenemos que ir
        # acumulando las variables ligadas en el environment
        var_name = self.var_name
        if var_name in env:
            raise TypeError(f"Variable {var_name} is shadowed in {self}")

        domain_obj = bind_and_eval(self.domain_obj, env)
        checkable = self.checkable

        # Si el dominio está marcado como finito recorremos el dominio entero
        if domain_obj.is_finite:
            domain_samples = domain_obj.finite_iterator()
        else:
            domain_samples = take(self.n_samples, domain_obj)
            
        for sample in domain_samples:
            for checked in checkable.qc({**env, var_name: sample}):
                yield checked

    def __call__(self):
        for i, result in enumerate(self.qc({})):
            if result:
                print(".", end= "", flush= True)
            else:
                print("x")
                print(f"After {i} tests")
                print(result)
                break
        else:
            print()
            print(f"Passed {i} tests")
        print()
            
    def __str__(self):
        return f"ForAll {self.var_name}: {self.domain_obj}\n{textwrap.indent(str(self.checkable), '  ')}"
        

        
        
class Exists:
    def __init__(self, var_name: str, domain_obj: Domain, checkable: Checkable):
        if not isinstance(checkable, Predicate):
            raise TypeError(f"Cannot check Exists on another quantifier")
        
        self.var_name = var_name
        self.domain_obj = domain_obj
        self.checkable = checkable

        
    def qc(self, env: ENV) -> Iterator[Checked]:
        var_name = self.var_name
        if var_name in env:
            raise TypeError(f"Variable {var_name} is shadowed in {self}")

        domain_obj = bind_and_eval(self.domain_obj, env)
        checkable = self.checkable

        if not domain_obj.is_finite:
            raise TypeError(f"Cannot check existence in non finite domain: {domain_obj}")
        
        for sample in domain_obj.finite_iterator():
            if any(checkable.qc({**env, var_name: sample})):
                yield True
                return
                
        yield Left(f"{env} -> {str(self)}")
        return

    def __call__(self):
        return self.qc({})
    
    def __str__(self):
        return f"Exists {self.var_name}: {self.domain_obj} / {self.checkable}"
        


    
#---------------------------------------------------------------------------
# decoradores
#---------------------------------------------------------------------------
def forall(n_samples: int= 100, **binds):
    if len(binds) != 1:
        raise TypeError(f"Must bind just one variable, but {len(binds)} binded")
    
    def factory(prop_or_pred):
        if is_checkable(prop_or_pred):
            checkable = prop_or_pred
        else:
            checkable = Predicate(prop_or_pred)
        var_name, obj = list(binds.items())[0]
        domain_obj = _preprocess_domain(obj)
        return ForAll(var_name, domain_obj, checkable, n_samples= n_samples)

    return factory


def exists(**binds):
    if len(binds) != 1:
        raise TypeError(f"Must bind just one variable, but {len(binds)} binded")

    def factory(prop_or_pred):
        if is_checkable(prop_or_pred):
            checkable = prop_or_pred
        else:
            checkable = Predicate(prop_or_pred)
        var_name, obj = list(binds.items())[0]
        domain_obj = _preprocess_domain(obj)
        return Exists(var_name, domain_obj, checkable)

    return factory

