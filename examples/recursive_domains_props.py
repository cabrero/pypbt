from pypbt import domain
from pypbt.quantifier import exists, forall


@forall(t= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))())
def prop_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)


Tree= domain.recursive(lambda Tree: (
        domain.Boolean() |
        domain.Tuple(Tree(), Tree())
    ))


@forall(t= Tree())
def prop_again_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)


Json = domain.recursive(lambda Json: (
    domain.domain_expr(None) |
    domain.Boolean() |
    domain.Int() |
    domain.List(Json()) |
    domain.Dict(domain.PyName(), Json())
))


Json = domain.recursive(lambda Json: (
    None |
    domain.Boolean() |
    domain.Int() |
    domain.List(Json()) |
    domain.Dict(domain.PyName(), Json())
))

# TODO: propiedad que use el json
