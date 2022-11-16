import ast
import math

import random

class ExprNode(object):
    @classmethod
    def true(self):
        return ValNode(True)
    @classmethod
    def false(self):
        return ValNode(False)

    def varnames(self):
        result = set()
        for c in self.children:
            result = result.union(c.varnames())
        return result

    def __repr__(self):
        return str(self)

class AndNode(ExprNode):
    def __init__(self, *children):
        assert all(isinstance(c, ExprNode) for c in children), breakpoint()
        self.children = list(children)

    def evaluate(self, values):
        return all(c.evaluate(values) for c in self.children)

    def prune_vals(self):
        tmp = [c.prune_vals() for c in self.children]

        # if there's a single false being anded, return false
        if [c for c in tmp if c == False]:
            return ExprNode.false()

        # collect children that aren't true
        tmp = [c for c in tmp if c != True]
        match len(tmp):
            case 0:
                return ExprNode.false()
            case 1:
                return tmp[0]
            case _:
                return AndNode(*tmp)

    def omnitrue(self, names):
        return AndNode(*[c.omnitrue(names) for c in self.children])

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == AndNode and self.children == other.children

    def __str__(self):
        lines = []
        for c in self.children:
            (l, r) = ('(', ')') if isinstance(c, OrNode) else ('', '')
            lines.append(l + str(c) + r)
        return ''.join(lines)

class OrNode(ExprNode):
    def __init__(self, *children):
        assert all(isinstance(c, ExprNode) for c in children), breakpoint()
        self.children = list(children)

    def evaluate(self, values):
        return any(c.evaluate(values) for c in self.children)

    def prune_vals(self):
        tmp = [c.prune_vals() for c in self.children]

        # if there's a single true being or'd, return true
        if [c for c in tmp if c == True]:
            return ExprNode.true()

        # collect children that aren't false
        tmp = [c for c in tmp if c != False]
        match len(tmp):
            case 0: return ExprNode.false()
            case 1: return tmp[0]
            case _: return OrNode(*tmp)

    def omnitrue(self, names):
        return OrNode(*[c.omnitrue(names) for c in self.children])

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)    
        return type(other) == OrNode and self.children == other.children

    def __str__(self):
        return '+'.join(str(c) for c in self.children)

class NotNode(ExprNode):
    def __init__(self, child):
        assert isinstance(child, ExprNode)
        self.child = child

    def evaluate(self, values):
        return not self.child.evaluate(values)

    def prune_vals(self):
        tmp = self.child.prune_vals()
        if type(tmp) == ValNode:
            return ValNode(not tmp.value)
        return NotNode(tmp)

    def varnames(self):
        return self.child.varnames()

    def omnitrue(self, names):
        if isinstance(self.child, VarNode) and self.child.name in names:
            return ValNode(True)

        return NotNode(self.child.omnitrue(names))

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)    
        return type(other) == NotNode and self.child == other.child

    def __str__(self):
        if isinstance(self.child, VarNode):
            return f'/{self.child}'
        else:
            return f'/({self.child})'

class VarNode(ExprNode):
    def __init__(self, name):
        assert type(name) == str
        self.name = name

    def varnames(self):
        return {self.name}

    def prune_vals(self):
        return self.clone()

    def evaluate(self, values):
        return values[self.name]

    def omnitrue(self, names):
        if self.name in names:
            return ValNode(True)
        else:
            return self.clone()

    def clone(self):
        return VarNode(self.name)

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)    
        return type(other) == VarNode and self.name == other.name

    def __str__(self):
        return self.name

class ValNode(ExprNode):
    def __init__(self, value):
        assert type(value) == bool
        self.value = value

    def evaluate(self, values):
        return self.value

    def varnames(self):
        return set()

    def prune_vals(self):
        return self.clone()

    def omnitrue(self, names):
        return self.clone()

    def clone(self):
        return ValNode(self.value)

    def __eq__(self, other):
        if type(other) == bool:
            other = ValNode(other)
        elif type(other) == str:
            other = parse(other)

        return type(other) == ValNode and self.value == other.value

    def __str__(self):
        return {True:'T', False:'F'}[self.value]

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
        return NotNode(refine(tree.operand))
    elif type(tree) == ast.BoolOp:
        subr = [refine(v) for v in tree.values]
        if type(tree.op) == ast.Or:
            return OrNode(*subr)
        elif type(tree.op) == ast.And:
            return AndNode(*subr)
    elif type(tree) == ast.Name:
        return VarNode(tree.id)
    else:
        breakpoint()

# generate random expression
def generate(n_nodes, varnames):
    n = 0

    expr = None

    while n < n_nodes:
        if expr == None:
            actions = ['initialize']
        else:
            actions = ['or-var', 'and-var']
            if not isinstance(expr, NotNode):
                actions.append('not')

        action = random.choice(actions)

        # these actions require creation of X or /X
        if action in ['initialize', 'or-var', 'and-var']:
            v = VarNode(random.choice(varnames))
            if random.randint(0,1):
                v = NotNode(v)
                n += 1

        match action:
            case 'initialize':
                expr = v
            case 'not':
                expr = NotNode(expr)
            case 'or-var':
                expr = OrNode(expr, v)
            case 'and-var':
                expr = AndNode(expr, v)
        n += 1

    return expr

# parse a logical expression in Python to ExprNode
def parse(input_):
    ast_tree = ast.parse(input_)
    expr_tree = refine(ast_tree)
    return expr_tree

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
        return ValNode(False)

    products = []
    for minterm in ones:
        factors = []
        for i in range(n):
            if minterm & (1<<(n-1-i)):
                factors.append(VarNode(varnames[i]))
            else:
                factors.append(NotNode(VarNode(varnames[i])))

        products.append(AndNode(*factors))

    return OrNode(*products)

def simplify_quine_mccluskey(expr):
    # pip install quine-mccluskey
    from quine_mccluskey.qm import QuineMcCluskey

    qm = QuineMcCluskey(use_xor=False)

    vnames = sorted(expr.varnames())
    ones = to_minterms(expr)
    result = qm.simplify(ones, dc=[], num_bits=len(vnames))

    if result == None:
        return ValNode(False)
    if len(result) == 1 and list(result)[0] == '-'*len(vnames):
        return ValNode(True)

    products = []
    # s is like '1-'
    for s in result:
        factors = []
        for (i,c) in enumerate(s):
            match c:
                case '-':
                    continue
                case '1':
                    factors.append(VarNode(vnames[i]))
                case '0':
                    factors.append(NotNode(VarNode(vnames[i])))
                case _:
                    raise Exception(f'error: {c}')

        products.append(AndNode(*factors))

    return OrNode(*products)

if __name__ == '__main__':
    import sys

    print('GENERATE SOME RANDOM EQUATIONS')
    varnames = list('ABCDEF')
    for n_nodes in range(1, 20):
        print(f'{n_nodes}: ' + str(generate(n_nodes, varnames)))

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
    expr0 = parse('A')
    mt0 = to_minterms(expr0)
    print(f'{expr0} -> {mt0}')
    varnames = sorted(expr0.varnames())
    expr1 = from_minterms(mt0, varnames)
    mt1 = to_minterms(expr1)
    print(f'{expr1} -> {mt1}')

    expr = parse('A and (A or B)')
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
