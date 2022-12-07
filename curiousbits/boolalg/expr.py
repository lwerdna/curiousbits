# low level implementation of the boolean expressions

# conventions:
# all operations are in-place
# if you want a new expression tree, do .clone() then an in-place operation
# WARNING! you still must assign with in-place operations, like:
#  e = e.reduce()
# because the root node might change! eg:
#  Or(Var('B'), True) -> Val(True)

# evaluation is done with
# one-shot evaluation is done with .evaluate()
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
    def __init__(self):
        self._str_cache = ''
        self.children = []

    def varnames(self):
        result = set()
        for c in self.children:
            result = result.union(c.varnames())
        return result

    # Var and Not need to override
    def is_literal(self):
        return False

    # Var, Not need to override
    def omnitrue(self, names):
        self.children = [c.omnitrue(names) for c in self.children]
        return self

    # Var and Val need to override
    def set_variable(self, name:str, value:bool):
        # must reassign childen, because Var could return (replace themselves with) Val
        self.children = [c.set_variable(name, bool(value)) for c in self.children]
        return self

    # Var and Val need to override
    def all_nodes(self):
        return sum([c.all_nodes() for c in self.children], [self])

    def reduce(self):
        pass

    def clone(self):
        pass

    def syntactic_equality(self, other):
        str(self)
        str(other)
        return self._str_cache == other._str_cache

    # WARNING! str() must first be called on before, after to build cache
    # Var and Val (with no children) need to override
    def replace_subtree(self, before, after):
        if self._str_cache == before._str_cache:
            return after
        else:
            self.children = [c.replace_subtree(before, after) for c in self.children]
            return self

    def __py__(self):
        pass

    def __c__(self):
        pass

    def __str_cached__(self):
        return self._str_cache

    def __str__(self):
        pass

    def __repr__(self):
        pass

class And(BoolExpr):
    def __init__(self, *children):
        super().__init__()
        assert all(isinstance(c, BoolExpr) for c in children), breakpoint()
        self.children = list(children)

    def evaluate(self, values):
        sr = [c.evaluate(values) for c in self.children]
        if any(r==False for r in sr): return False
        if all(r==True for r in sr): return True
        return None

    def reduce(self):
        self.children = [c.reduce() for c in self.children]

        # rule: annulment
        if any([c == False for c in self.children]):
            return Val(False)

        # rule: identity
        self.children = [c for c in self.children if c != True]

        # rule: complement on literals
        # (if X and /X are conjuncts, result is false)
        lnodes = [c for c in self.children if c.is_literal()]
        if len(lnodes) > 1:
            strs = {str(n) for n in lnodes}
            for name in [n.name for n in lnodes]:
                if name in strs and '/'+name in strs:
                    return Val(False)

        match len(self.children):
            case 0: return Val(True) # empty And is True like empty product is 1
            case 1: return self.children[0]
            case _:
                return self

    def clone(self):
        return And(*[c.clone() for c in self.children])

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == And and self.children == other.children

    def __repr__(self):
        return 'And(' + ','.join([repr(c) for c in self.children]) + ')'

    def __py__(self):
        return ' and '.join([f'({c.__py__()})' if isinstance(c, Or) else c.__py__() for c in self.children])

    def __c__(self):
        return ' && '.join([f'({c.__c__()})' if isinstance(c, Or) else c.__c__() for c in self.children])

    def __str__(self):
        lines = []
        for c in self.children:
            (l, r) = ('(', ')') if isinstance(c, Or) else ('', '')
            lines.append(l + str(c) + r)
        self._str_cache = ''.join(sorted(lines))
        return self._str_cache

class Or(BoolExpr):
    def __init__(self, *children):
        super().__init__()
        assert all(isinstance(c, BoolExpr) for c in children), breakpoint()
        self.children = list(children)

    def evaluate(self, values):
        sr = [c.evaluate(values) for c in self.children]
        if any(r==True for r in sr): return True
        if all(r==False for r in sr): return False
        return None

    def reduce(self):
        self.children = [c.reduce() for c in self.children]

        # rule: identity
        if any([c==True for c in self.children]):
            return Val(True)

        # rule: identity
        self.children = [c for c in self.children if c != False]

        # complement on literals
        # (if X and /X are disjuncts, result is true)
        lnodes = [c for c in self.children if c.is_literal()]
        if len(lnodes) > 1:
            strs = {str(n) for n in lnodes}
            for name in [n.name for n in lnodes]:
                if name in strs and '/'+name in strs:
                    return Val(True)

        match len(self.children):
            case 0: return Val(False) # empty Or is False like empty sum is 0
            case 1: return self.children[0]
            case _:
                return self

    def clone(self):
        return Or(*[c.clone() for c in self.children])

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == Or and self.children == other.children

    def __repr__(self):
        return 'Or(' + ','.join([repr(c) for c in self.children]) + ')'

    def __py__(self):
        return ' or '.join([c.__py__() for c in self.children])

    def __c__(self):
        return ' || '.join([c.__c__() for c in self.children])

    def __str__(self):
        subresults = [str(c) for c in self.children]
        self._str_cache = '+'.join(str(c) for c in sorted(subresults))
        return self._str_cache

class Not(BoolExpr):
    def __init__(self, child):
        super().__init__()
        assert isinstance(child, BoolExpr)
        self.children = [child]

    @property
    def child(self):
        return self.children[0]

    @property
    def name(self):
        if self.is_literal():
            return self.child.name

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

        return super().omnitrue(names)

    def is_literal(self):
        return isinstance(self.child, Var)

    def clone(self):
        return Not(self.child.clone())

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == Not and self.child == other.child

    def __repr__(self):
        return 'Not(' + repr(self.child) + ')'

    def __py__(self):
        return f'not {self.child.__py__()}' if self.child.is_literal() else f'not ({self.child.__py__()})'

    def __c__(self):
        return f'!{self.child.__c__()}' if self.child.is_literal() else f'!({self.child.__c__()})'

    def __str__(self):
        if self.child.is_literal():
            self._str_cache = f'/{self.child}'
        else:
            self._str_cache = f'/({self.child})'
        return self._str_cache

class Var(BoolExpr):
    def __init__(self, name):
        super().__init__()
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

        return super().omnitrue(names)

    def is_literal(self):
        return True

    def set_variable(self, name:str, value:bool):
        if self.name == name:
            return Val(bool(value))
        return self

    def all_nodes(self):
        return [self]

    def clone(self):
        return Var(self.name)

    def replace_subtree(self, before, after):
        if self._str_cache == before._str_cache:
            return after
        else:
            return self

    def __eq__(self, other):
        if type(other) == str:
            other = parse(other)
        return type(other) == Var and self.name == other.name

    def __repr__(self):
        return f'Var("{self.name}")'

    def __py__(self):
        return str(self)

    def __c__(self):
        return str(self)

    def __str__(self):
        self._str_cache = self.name
        return self._str_cache

class Val(BoolExpr):
    def __init__(self, value):
        super().__init__()
        assert type(value) == bool
        self.value = value

    def evaluate(self, values):
        return self.value

    def varnames(self):
        return set()

    def reduce(self):
        return self

    def all_nodes(self):
        return [self]

    def clone(self):
        return Val(self.value)

    def set_variable(self, name:str, value:bool):
        return self

    def replace_subtree(self, before, after):
        if self._str_cache == before._str_cache:
            return after
        else:
            return self

    def __eq__(self, other):
        if type(other) == bool:
            other = Val(other)
        elif type(other) == str:
            other = parse(other)

        return type(other) == Val and self.value == other.value

    def __repr__(self):
        return f'Val({self.value})'

    def __py__(self):
        return str(self.value)

    def __c__(self):
        return {True:'true', False:'false'}[self.value]

    def __str__(self):
        self._str_cache = {True:'T', False:'F'}[self.value]
        return self._str_cache

if __name__ == '__main__':
    # values (True/False)
    e = Val(True)
    print(e)
    print(repr(e))
    assert e == True
    assert len(e.all_nodes()) == 1

    e = Val(False)
    print(e)
    print(repr(e))
    assert e == False
    assert len(e.all_nodes()) == 1

    # single variables
    e = Var('A')
    print(e)
    e2 = e.clone()
    print(e2)
    assert id(e) != id(e2)

    e = And(Or(Var('A'), Var('B')), Not(Or(Var('C'),Var('D'))))
    assert len(e.all_nodes()) == 8
    assert e.__py__() == '(A or B) and not (C or D)'
    assert e.__c__() == '(A || B) && !(C || D)'

    # test case for reduction
    print('-------- synthesize XOR from truth table --------')
    e = Or(And(Var("B"),Val(True)),Or(And(Var("A"),Val(True)),Val(False)))
    assert len(e.all_nodes()) == 9
    print(f'PYTHON: {e.__py__()}')
    print(f'     C: {e.__c__()}')
    assert e.__py__() == 'B and True or A and True or False'
    e2 = e.reduce()
    assert str(e2) in ['A+B', 'B+A']
    assert e2.__py__() in ['A or B', 'B or A']

    # simple xor, e = A/B + /AB
    print('-------- test XOR evaluation --------')
    xor = Or(And(Var('A'),Not(Var('B'))), And(Not(Var('A')),Var('B')))

    assert len(xor.all_nodes()) == 9

    print(f'PYTHON: {xor.__py__()}')
    print(f'     C: {xor.__c__()}')
    assert xor.__py__() == 'A and not B or not A and B'

    for (a,b,expected) in [
        (0,0,0),
        (0,1,1),
        (1,0,1),
        (1,1,0)
    ]:
        e = xor.clone()
        e.set_variable('A', a)
        e.set_variable('B', b)
        e = e.reduce()
        assert e == bool(expected)

    # adder, e = /A/BC + /AB/C + A/B/C + ABC
    print('-------- synthesize ADDER from truth table --------')
    e = Or(And(Not(Var('A')),Not(Var('B')),Var('C')), And(Not(Var('A')),Var('B'),Not(Var('C'))), And(Var('A'),Not(Var('B')),Not(Var('C'))), And(Var('A'),Var('B'),Var('C')))
    assert len(e.all_nodes()) == 23
    print(e)
    print(f'PYTHON: {e.__py__()}')
    print(f'     C: {e.__c__()}')
    assert e.__py__() == 'not A and not B and C or not A and B and not C or A and not B and not C or A and B and C'
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

    print('-------- test annulment rule --------')
    e = And(Var('X'), Val(False))
    e = e.reduce()
    assert e.__py__() == 'False'
    e = Or(Var('X'), Val(True))
    e = e.reduce()
    assert e.__py__() == 'True'

    print('-------- test identity rule --------')
    e = And(Var('X'), Val(True))
    e = e.reduce()
    assert e.__py__() == 'X'
    e = Or(Var('X'), Val(False))
    e = e.reduce()
    assert e.__py__() == 'X'

    print('-------- test complement rule --------')
    e = And(Var('X'), Not(Var('X')))
    e = e.reduce()
    assert e.__py__() == 'False'
    e = Or(Var('X'), Not(Var('X')))
    e = e.reduce()
    assert e.__py__() == 'True'

    print('-------- test omnitrue --------')

    # make A and /A true
    e = xor.clone()
    e.omnitrue(['A'])
    assert e.__py__() == 'True and not B or True and B'
    e = e.reduce()
    assert e.__py__() == 'True'

    # make B and /B true
    e = xor.clone()
    e.omnitrue(['B'])
    assert e.__py__() == 'A and True or not A and True'
    e = e.reduce()
    assert e.__py__() == 'True'

    # make all vars true
    e = xor.clone()
    e.omnitrue(['A', 'B'])
    assert e.__py__() == 'True and True or True and True'
    e = e.reduce()
    assert e.__py__() == 'True'

    print('pass')
