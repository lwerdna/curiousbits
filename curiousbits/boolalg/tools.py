import ast
import random

#from . import expr
from .expr import *

#------------------------------------------------------------------------------
# string <-> expressions
#------------------------------------------------------------------------------
# refine the AST from parse()/ast.parse() to ExprNode
def refine(tree):
    if type(tree) == ast.Module:
        return refine(tree.body)
    elif type(tree) == list: # block
        assert len(tree) == 1
        return refine(tree[0])
    elif type(tree) == ast.Expr:
        return refine(tree.value)
    elif type(tree) == ast.UnaryOp:
        return Not(refine(tree.operand))
    elif type(tree) == ast.BoolOp:
        subr = [refine(v) for v in tree.values]
        if type(tree.op) == ast.Or:
            return Or(*subr)
        elif type(tree.op) == ast.And:
            return And(*subr)
    elif type(tree) == ast.Name:
        return Var(tree.id)
    else:
        breakpoint()

# parse a logical expression in Python to ExprNode
def parse_python(input_):
    ast_tree = ast.parse(input_)
    expr_tree = refine(ast_tree)
    return expr_tree

#------------------------------------------------------------------------------
# generate random expressions
#------------------------------------------------------------------------------
def generate(n_nodes, varnames):
    n = 0

    expr = None

    while n < n_nodes:
        if expr == None:
            actions = ['initialize']
        else:
            actions = ['or-var', 'and-var']
            if not isinstance(expr, Not):
                actions.append('not')

        action = random.choice(actions)

        # these actions require creation of X or /X
        if action in ['initialize', 'or-var', 'and-var']:
            v = Var(random.choice(varnames))
            if random.randint(0,1):
                v = Not(v)
                n += 1

        match action:
            case 'initialize':
                expr = v
            case 'not':
                expr = Not(expr)
            case 'or-var':
                expr = Or(expr, v)
            case 'and-var':
                expr = And(expr, v)
        n += 1

    return expr

#------------------------------------------------------------------------------
# expr <-> minterms
#------------------------------------------------------------------------------
def to_minterms(expr, varnames=None):
    result = []

    if varnames == None:
        varnames = sorted(expr.varnames())

    n = len(varnames)
    for i in range(2**n):
        inputs = {name: bool(i & (1<<(n-pos-1))) for (pos, name) in enumerate(varnames)}
        output = expr.evaluate(inputs)
        #print(f'{inputs} -> {output}')
        if expr.evaluate(inputs):
            result.append(i)

    return result

def from_minterms(ones, varnames):
    n = len(varnames)

    if not ones or not n:
        return Val(False)

    products = []
    for minterm in ones:
        factors = []
        for i in range(n):
            if minterm & (1<<(n-1-i)):
                factors.append(Var(varnames[i]))
            else:
                factors.append(Not(Var(varnames[i])))

        products.append(And(*factors))

    return Or(*products)

#------------------------------------------------------------------------------
# tests
#------------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    print('GENERATE SOME RANDOM EQUATIONS')
    varnames = list('ABCDEF')
    for n_nodes in range(1, 20):
        expr = generate(n_nodes, varnames)
        print(f'{n_nodes}: ' + str(expr))
        print(f'{n_nodes}: ' + repr(expr))

    sys.exit(0)

    print('SHOW MINTERMS')
    for n_nodes in range(1, 20):
        expr = generate(n_nodes, varnames)
        minterms = to_minterms(expr)
        print(f'{expr} -> {minterms}')

    print('GEN FROM MINTERMS')
    for minterms in [[], [0], [1], [0,1]]:
        expr = from_minterms(minterms, list('A'))
        print(f'{minterms} -> {expr}')
    for minterms in [[], [0], [1], [2], [3], [0,1], [0,2], [0,3], [1,2], [1,3], [2,3]]:
        expr = from_minterms(minterms, list('AB'))
        print(f'{minterms} -> {expr}')        

    print('CONVERT TO/FROM MINTERMS')
    expr0 = parse_python('A')
    mt0 = to_minterms(expr0)
    print(f'{expr0} -> {mt0}')
    varnames = sorted(expr0.varnames())
    expr1 = from_minterms(mt0, varnames)
    mt1 = to_minterms(expr1)
    print(f'{expr1} -> {mt1}')

    expr = parse_python('A and (A or B)')
    minterms = to_minterms(expr)
    print(f'{expr} -> {minterms}')
    varnames = sorted(expr.varnames())
    expr = from_minterms(minterms, varnames)
    print(f'{expr}')

    for n_nodes in range(1, 40):
        expr0 = generate(n_nodes, list('ABCDEF'))
        minterms0 = to_minterms(expr0)
        print(f'{expr0} -> {minterms0}')

        varnames = sorted(expr0.varnames())
        expr1 = from_minterms(minterms0, varnames)
        minterms1 = to_minterms(expr1)
        print(f'{expr1} -> {minterms1}')

    print('pass')
