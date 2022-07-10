from pypbt import domains
from pypbt.quantifiers import exists, forall


@forall(t= domains.recursive(lambda Tree: (
        domains.Boolean() |
        domains.Tuple(Tree(), Tree())
    ))())
def prop_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)


Tree= domains.recursive(lambda Tree: (
        domains.Boolean() |
        domains.Tuple(Tree(), Tree())
    ))


@forall(t= Tree())
def prop_again_a_tree_looks_like_a_tree(t):
    return type(t) == bool or (
        type(t) == tuple and len(t) == 2)


Json = domains.recursive(lambda Json: (
    domains.domain_expr(None) |
    domains.Boolean() |
    domains.Int() |
    domains.List(Json()) |
    domains.Dict(domains.PyName(), Json())
))


Json = domains.recursive(lambda Json: (
    None |
    domains.Boolean() |
    domains.Int() |
    domains.List(Json()) |
    domains.Dict(domains.PyName(), Json())
))

# TODO: propiedad que use el json
