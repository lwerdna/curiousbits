from .expr import *
from .tools import *

#------------------------------------------------------------------------------
# Tseytin transformation
# https://en.wikipedia.org/wiki/Tseytin_transformation
#------------------------------------------------------------------------------

# returns (expression equisatisfiable with proper operation of this gate,
#          variable representing output of this gate)
def Tseytin_transformation_re(node):
    if type(node) == And:
        if len(node.children) != 2:
            raise NotImplementedError()
        A_tseytin, A = Tseytin_transformation_re(node.children[0])
        B_tseytin, B = Tseytin_transformation_re(node.children[1])
        # generate variable representing this output
        C = Var(f'gate_{id(node)}')
        C_tseytin = And(Or(Not(A), Not(B), C), Or(A, Not(C)), Or(B, Not(C)))
        return (And(A_tseytin, B_tseytin, C_tseytin), C)
    elif type(node) == Or:
        if len(node.children) != 2:
            raise NotImplementedError()
        A_tseytin, A = Tseytin_transformation_re(node.children[0])
        B_tseytin, B = Tseytin_transformation_re(node.children[1])
        # generate variable representing this output
        C = Var(f'gate_{id(node)}')
        C_tseytin = And(Or(A, B, Not(C)), Or(Not(A), C), Or(Not(B), C))
        return (And(A_tseytin, B_tseytin, C_tseytin), C)
    elif type(node) == Xor:
        if len(node.children) != 2:
            raise NotImplementedError()
        A_tseytin, A = Tseytin_transformation_re(node.children[0])
        B_tseytin, B = Tseytin_transformation_re(node.children[1])
        # generate variable representing this output
        C = Var(f'gate_{id(node)}')
        C_tseytin = And(Or(Not(A), Not(B), Not(C)), Or(A, B, Not(C)), Or(A, Not(B), C), Or(Not(A), B, C))
        return (And(A_tseytin, B_tseytin, C_tseytin), C)
    elif type(node) == Not:
        if len(node.children) != 1:
            raise NotImplementedError()
        A_tseytin, A = Tseytin_transformation_re(node.children[0])
        # generate variable representing this output
        C = Var(f'gate_{id(node)}')
        C_tseytin = And(Or(Not(A), Not(C)), Or(A, C))
        return (And(A_tseytin, C_tseytin), C)
    elif type(node) == Var:
        return (Val(True), node)
    else:
        raise NotImplementedError()

def Tseytin_transformation(expr):
    if not is_binary(expr):
        expr = expr.deepen()

    expr, outvar = Tseytin_transformation_re(expr)

    # un-nest ANDs, so the final expression is one big AND
    expr.flatten()

    # discard True conjuncts, which were returned by transforming literals
    expr.reduce()

    return (expr, outvar)

if __name__ == '__main__':
    import sys

    # A should have "gate is working" expression True and output variable A
    expr = Var('A')
    texpr, v = Tseytin_transformation(expr)
    assert str(texpr)=='T' and str(v)=='A'

    # /A should have "gate is working" expression True and output variable A
    expr = Not(Var('A'))
    texpr, v = Tseytin_transformation(expr)
    print(texpr)
    print(v)

    print('TSEYTIN TRANSFORMATION')
    expr = Not(Var('A'))
    texpr, v = Tseytin_transformation(expr)
    print(f'TSEYTIN({expr}): {v} = {texpr}')

    expr = And(Var('A'), Var('B'))
    texpr, v = Tseytin_transformation(expr)
    print(f'TSEYTIN({expr}): {v} = {texpr}')

    expr = Or(Var('A'), Var('B'))
    texpr, v = Tseytin_transformation(expr)
    print(f'TSEYTIN({expr}): {v} = {texpr}')
