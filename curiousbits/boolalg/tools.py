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
    elif type(tree) == ast.Constant:
        return Val(tree.value)
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
# expr -> truth indices
#------------------------------------------------------------------------------

# eg:
#
# Truth table for XOR:
# A B C
# 0 0 0
# 0 1 1
# 1 0 1
# 1 1 0
#
# has truth indices [1,2]

# eg: A/B + /AB -> [1,2]
def to_truth_indices(expr, varnames=None):
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

#------------------------------------------------------------------------------
# truth indices -> sum of products (SOP) or conjunction of minterms
#------------------------------------------------------------------------------

# eg:
#
# Truth table for XOR:
# A B C
# 0 0 0
# 0 1 1
# 1 0 1
# 1 1 0
#
# A minterm is a term that's TRUE for exactly one combination of inputs (each row).
# There are 2^n minterms for n variables: [/A/B, /AB, A/B, /A/B]
# The output column acts as an indicator vector of which minterms will be selected in the sum of products:
#   [0, 1, 1, 0] selects [/AB, A/B] resulting in /AB + A/B

# eg:
# [1,2,3] -> A/B + /AB
def truth_indices_to_sop(ones, varnames):
    n = len(varnames)

    if not ones or not n:
        return Val(False)
    if len(ones) == 2**n:
        return Val(True)

    products = []
    for minterm in ones:
        factors = []
        for i in range(n):
            if minterm & (1<<(n-1-i)):
                factors.append(Var(varnames[i]))
            else:
                factors.append(Not(Var(varnames[i])))

        products.append(And(*factors))

    return Or(*products) if len(products)>1 else products[0]


#------------------------------------------------------------------------------
# truth indices -> sum of products (SOP) or disjunction of maxterms
#------------------------------------------------------------------------------

# eg:
#
# Truth table for XOR:
# A B C
# 0 0 0
# 0 1 1
# 1 0 1
# 1 1 0
#
# A maxterm is a term that's FALSE for exactly one combination of inputs (each row).
# There are 2^n maxterms for n variables: [A+B, A+/B, /A+B, /A+/B]
# The complement of the output column acts as an indicator vector of which maxterms will be selected in the product of sums:
#   [0, 1, 1, 0] complemented is [1, 0, 0, 1] selects [A+B, /A+/B] resulting in (A+B)(/A+/B)

def truth_indices_to_pos(ones, varnames):
    n = len(varnames)

    if not ones or not n:
        return Val(False)
    if len(ones) == 2**n:
        return Val(True)

    zeroes = sorted(set(range(2**n)) - set(ones))

    sums = []
    for row in zeroes:
        addends = []
        for i in range(n):
            if row & (1<<(n-1-i)):
                addends.append(Not(Var(varnames[i])))
            else:
                addends.append(Var(varnames[i]))

        sums.append(Or(*addends))

    return And(*sums) if len(sums)>1 else sums[0]

#------------------------------------------------------------------------------
# format testers
#------------------------------------------------------------------------------

def is_binary(expr):
    if not hasattr(expr, 'children'):
        return True

    return len(expr.children) <= 2 and all([is_binary(c) for c in expr.children])

def is_cnf(expr):
    if type(expr) != And:
        return False

    for c in expr.children:
        if type(c) != Or:
            return False

        for gc in c.children:
            if not gc.is_literal():
                return False

    return True

#------------------------------------------------------------------------------
# misc
#------------------------------------------------------------------------------

def print_truth_table(expr, varnames=None):
    if varnames == None:
        varnames = sorted(expr.varnames())

    n = len(varnames)

    indices = set(to_truth_indices(expr, varnames))

    print(', '.join(varnames) + ', output')
    for i in range(2**n):
        binstr = ''.join(['1' if i&(1<<(n-k-1)) else '0' for k in range(n)])
        print(f'{binstr} {1 if i in indices else 0}')

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

    print('BASIC CONVERSIONS ON XOR')
    expr = parse_python('(A and not B) or (not A and B)')
    print(expr)
    assert str(expr) in ['/AB+/BA', '/BA+/AB']

    indices = to_truth_indices(expr)
    print(indices)
    assert indices == [1, 2]

    sop = truth_indices_to_sop(indices, ['A', 'B'])
    print(sop)
    assert str(sop) in ['/AB+/BA', '/BA+/AB']
    pos = truth_indices_to_pos(indices, ['A', 'B'])
    print(pos)
    assert str(pos) in ['(/A+/B)(A+B)', '(A+B)(/A+/B)']

    assert to_truth_indices(sop) == to_truth_indices(pos)

    print('SHOW TRUTH INDICES')
    for n_nodes in range(1, 20):
        expr = generate(n_nodes, varnames)
        indices = to_truth_indices(expr)
        print(f'{expr} -> {indices}')

    print('GEN FROM TRUTH INDICES')
    for indices in [[], [0], [1], [0,1]]:
        sop = truth_indices_to_sop(indices, list('A'))
        print(f'{indices} -(sop)-> {sop}')
        pos = truth_indices_to_pos(indices, list('A'))
        print(f'{indices} -(pos)-> {pos}')
        assert to_truth_indices(sop) == to_truth_indices(pos)

    for indices in [[], [0], [1], [2], [3], [0,1], [0,2], [0,3], [1,2], [1,3], [2,3]]:
        sop = truth_indices_to_sop(indices, list('AB'))
        print(f'{indices} -(sop)-> {sop}')
        pos = truth_indices_to_pos(indices, list('AB'))
        print(f'{indices} -(pos)-> {pos}')
        assert to_truth_indices(sop) == to_truth_indices(pos)

    print('CONVERT TO BINARY SHOULDNT CHANGE TRUTH VALUES')
    for n_nodes in range(1, 40):
        expr0 = generate(n_nodes, list('ABCDEF'))
        print(expr0)
        expr1 = expr0.deepen()
        print('converted to binary...')
        print(expr1)
        assert to_truth_indices(expr0) == to_truth_indices(expr1)

    print('CONVERT TO/FROM TRUTH INDICES')
    expr0 = parse_python('A')
    indices0 = to_truth_indices(expr0)
    print(f'{expr0} -> {indices0}')
    varnames = sorted(expr0.varnames())
    expr1 = truth_indices_to_sop(indices0, varnames)
    indices1 = to_truth_indices(expr1)
    print(f'{expr1} -> {indices1}')

    expr = parse_python('A and (A or B)')
    indices = to_truth_indices(expr)
    print(f'{expr} -> {indices}')
    varnames = sorted(expr.varnames())
    expr = truth_indices_to_sop(indices, varnames)
    print(f'{expr}')

    for n_nodes in range(1, 40):
        expr0 = generate(n_nodes, list('ABCDEF'))
        indices0 = to_truth_indices(expr0)
        print(f'{expr0} -> {indices0}')

        varnames = sorted(expr0.varnames())
        expr1 = truth_indices_to_sop(indices0, varnames)
        indices1 = to_truth_indices(expr1)
        print(f'{expr1} -> {indices1}')

    print('FACTOR OUT SUBTREE')
    a = parse_python('A')
    b = parse_python('B')
    str(a)
    str(b)
    expr = a.replace_subtree(a, b)
    assert str(expr) == 'B'

    a = parse_python('A and B')
    b = parse_python('B')
    c = parse_python('True')
    str(a)
    str(b)
    expr = a.replace_subtree(b, c)
    assert str(expr) == 'AT'
    expr = expr.reduce()
    assert str(expr) == 'A'

    # replace complicated expression with itself
    a = parse_python('A and B and C and D and E and F')
    b = parse_python('B and F and E and D and A and C')
    c = parse_python('True')
    str(a)
    str(b)
    expr = a.replace_subtree(b, c)
    assert str(expr) == 'T'

    a = parse_python('G or (A and B and C and D and E and F)')
    b = parse_python('B and F and E and D and A and C')
    c = parse_python('H')
    str(a)
    str(b)
    expr = a.replace_subtree(b, c)
    assert str(expr) == 'G+H'

    a = parse_python('(v0 and v1) or (not v0 and v3)')
    b = parse_python('(v0 and v1)')
    c = parse_python('True')
    str(a)
    str(b)
    expr = a.replace_subtree(b, c)
    assert str(expr) == '/v0v3+T'
    expr = expr.reduce()
    assert str(expr) == 'T'

    a = parse_python('A and ((v0 and v1) or (not v0 and v3))')
    b = parse_python('(v0 and v1) or (not v0 and v3)')
    c = parse_python('True')
    str(a)
    str(b)
    expr = a.replace_subtree(b, c)
    assert str(expr) == 'AT'
    expr = expr.reduce()
    assert str(expr) == 'A'

    print('pass')
