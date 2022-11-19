# low level implementation of the boolean expressions

# conventions:
# all operations are in-place
# if you want a new expression tree, do .clone() then an in-place operation

# evaluation is done with
# one-shot evaluatoin is done with .evaluate()
#
# .set_variable(), .reduce()

import random

class BoolExpr(object):
#    @classmethod
#    def true(self):
#        return Val(True)
#    @classmethod
#    def false(self):
#        return Val(False)

    def varnames(self):
        result = set()
        for c in self.children:
            result = result.union(c.varnames())
        return result

    # Var and Not need to override
    def is_literal(self):
        return False

    # Var and Val need to override
    def set_variable(self, name:str, value:bool):
        self.children = [c.set_variable(name, bool(value)) for c in self.children]
        return self

    def reduce(self):
        pass

    def clone(self):
        pass

    def __repr__(self):
        pass

class And(BoolExpr):
    def __init__(self, *children):
        assert all(isinstance(c, BoolExpr) for c in children), breakpoint()
        self.children = list(children)

    def evaluate(self, values):
        sr = [c.evaluate(values) for c in self.children]
        if any(r==False for r in sr): return False
        if all(r==True for r in sr): return True
        return None

    def reduce(self):
        tmp = [c.reduce() for c in self.children]

        # short-circuit eval
        if any([c==False for c in tmp]):
            return Val(False)
        if all([c==True for c in tmp]):
            return Val(True)

        # collect children that aren't true
        tmp = [c for c in tmp if c != True]
        match len(tmp):
            case 0: return Expr.true() # empty And is True like empty product is 1
            case 1: return tmp[0]
            case _:
                self.children = tmp
                return self

    def omnitrue(self, names):
        return And(*[c.omnitrue(names) for c in self.children])

    def clone(self):
        return And(*[c.clone() for c in self.children])

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == And and self.children == other.children

    def __repr__(self):
        return 'And(' + ','.join([repr(c) for c in self.children]) + ')'

    def __str__(self):
        lines = []
        for c in self.children:
            (l, r) = ('(', ')') if isinstance(c, Or) else ('', '')
            lines.append(l + str(c) + r)
        return ''.join(lines)

class Or(BoolExpr):
    def __init__(self, *children):
        assert all(isinstance(c, BoolExpr) for c in children), breakpoint()
        self.children = list(children)

    def evaluate(self, values):
        sr = [c.evaluate(values) for c in self.children]
        if any(r==True for r in sr): return True
        if all(r==False for r in sr): return False
        return None

    def reduce(self):
        tmp = [c.reduce() for c in self.children]

        # if there's a single true being or'd, return true
        if any([c==True for c in tmp]):
            return Val(True)
        if all([c==False for c in tmp]):
            return Val(False)

        # collect children that aren't false
        tmp = [c for c in tmp if c != False]
        match len(tmp):
            case 0: return Val(False) # empty Or is False like empty sum is 0
            case 1: return tmp[0]
            case _:
                self.children = tmp
                return self

    def omnitrue(self, names):
        return Or(*[c.omnitrue(names) for c in self.children])

    def clone(self):
        return Or(*[c.clone() for c in self.children])

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == Or and self.children == other.children

    def __repr__(self):
        return 'Or(' + ','.join([repr(c) for c in self.children]) + ')'

    def __str__(self):
        return '+'.join(str(c) for c in self.children)

class Not(BoolExpr):
    def __init__(self, child):
        assert isinstance(child, BoolExpr)
        self.children = [child]

    @property
    def child(self):
        return self.children[0]

    def evaluate(self, values):
        sr = self.child.evaluate(values)
        return (not sr) if type(sr)==bool else None

    # modifies the BoolExpr
    def reduce(self):
        self.children = [self.child.reduce()]
        if isinstance(self.child, Not):
            return self.child.child
        elif isinstance(self.child, Val):
            return Val(not self.child.value)
        return self

    def varnames(self):
        return self.child.varnames()

    def omnitrue(self, names):
        if isinstance(self.child, Var) and self.child.name in names:
            return Val(True)

        return Not(self.child.omnitrue(names))

    def is_literal(self):
        return isinstance(self.child, Var)

    def all_s(self):
        return [self] + self.child.all_s()

    def clone(self):
        return Not(self.child.clone())

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == Not and self.child == other.child

    def __repr__(self):
        return 'Not(' + repr(self.child) + ')'

    def __str__(self):
        if isinstance(self.child, Var) or isinstance(self.child, Val):
            return f'/{self.child}'
        else:
            return f'/({self.child})'

class Var(BoolExpr):
    def __init__(self, name):
        assert type(name) == str
        self.name = name

    def varnames(self):
        return {self.name}

    def reduce(self):
        return self

    def evaluate(self, values):
        return values.get(self.name)

    def omnitrue(self, names):
        if self.name in names:
            return Val(True)
        else:
            return self

    def is_literal(self):
        return True

    def set_variable(self, name:str, value:bool):
        if self.name == name:
            return Val(bool(value))
        return self

    def clone(self):
        return Var(self.name)

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == Var and self.name == other.name

    def __repr__(self):
        return f'Var("{self.name}")'

    def __str__(self):
        return self.name

class Val(BoolExpr):
    def __init__(self, value):
        assert type(value) == bool
        self.value = value

    def evaluate(self, values):
        return self.value

    def varnames(self):
        return set()

    def reduce(self):
        return self

    def omnitrue(self, names):
        return self

    def clone(self):
        return Var(self.value)

    def all_s(self):
        return [self]

    def set_variable(self, name:str, value:bool):
        return self

    def __eq__(self, other):
        if type(other) == bool:
            other = Val(other)
        elif type(other) == str:
            other = parse(other)

        return type(other) == Val and self.value == other.value

    def __repr__(self):
        return f'Val({self.value})'

    def __str__(self):
        return {True:'T', False:'F'}[self.value]

if __name__ == '__main__':
    # values (True/False)
    e = Val(True)
    print(e)
    print(repr(e))
    assert e == True

    e = Val(False)
    print(e)
    print(repr(e))
    assert e == False

    # single variables
    e = Var('A')
    print(e)
    e2 = e.clone()
    print(e2)
    assert id(e) != id(e2)

    # test case for reduction
    e = Or(And(Var("B"),Val(True)),Or(And(Var("A"),Val(True)),Val(False)))
    e2 = e.reduce()
    assert str(e2) in ['A+B', 'B+A']

    # simple xor, e = A/B + /AB
    e = Or(And(Var('A'),Not(Var('B'))), And(Not(Var('A')),Var('B')))
    for (a,b,expected) in [
        (0,0,0),
        (0,1,1),
        (1,0,1),
        (1,1,0)
    ]:
        t = e.clone()
        t.set_variable('A', a)
        t.set_variable('B', b)
        t = t.reduce()
        assert t == bool(expected)

    # adder, e = /A/BC + /AB/C + A/B/C + ABC
    e = Or(And(Not(Var('A')),Not(Var('B')),Var('C')), And(Not(Var('A')),Var('B'),Not(Var('C'))), And(Var('A'),Not(Var('B')),Not(Var('C'))), And(Var('A'),Var('B'),Var('C')))
    print(e)
    for (a,b,c,expected) in [
        (0,0,0,0),
        (0,0,1,1),
        (0,1,0,1),
        (0,1,1,0),
        (1,0,0,1),
        (1,0,1,0),
        (1,1,0,0),
        (1,1,1,1)
    ]:
        t = e.clone()
        t.set_variable('A', a)
        t.set_variable('B', b)
        t.set_variable('C', c)
        t = t.reduce()
        assert t == bool(expected)

    print('pass')
