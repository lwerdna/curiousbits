from subprocess import Popen, PIPE

from .tools import parse_python, generate, to_minterms
from .expr import *

class TruthTable(object):
    def __init__(self, n_inputs, n_outputs):
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs

        self.rows = []

    def add(self, inputs, outputs):
        assert len(inputs) == self.n_inputs
        assert len(outputs) == self.n_outputs
        irow = [str(int(i)) for i in inputs]
        orow = [str(int(o)) for o in outputs]
        self.rows.append(''.join(irow) + ' ' + ''.join(orow))

    def simplify(self):
        # form input
        lines = []
        lines.append(f'.i {self.n_inputs}')
        lines.append(f'.o {self.n_outputs}')
        lines.append(f'.type f')
        lines.extend(self.rows)
        lines.append('.e')
        script = '\n'.join(lines)
        #print('INPUT:')
        #print(script)
        script = script.encode('utf-8')

        # pipe to espresso
        process = Popen('espresso', stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (stdout, stderr) = process.communicate(script)
        stdout = stdout.decode("utf-8")
        stderr = stderr.decode("utf-8")
        #print('stdout: -%s-' % stdout)
        #print('stderr: -%s-' % stderr)
        process.wait()

        # products is list of (literals, negated_literals)
        # where each is a set of integers identifying the literal variables involved in that product
        # eg:
        # ({0,1,4}, {2}) means v0 && v1 && !v2 && v4
        products = []

        for line in stdout.split('\n'):
            if not line or line.isspace():
                continue
            if line.startswith('.'):
                continue

            # line like "1- 1"
            #print('line: ' + line)
            (inputs, outputs) = line.split(' ')
            assert len(inputs) == self.n_inputs
            assert len(outputs) == self.n_outputs
            assert outputs == '1'*self.n_outputs

            lits = {i for (i,c) in enumerate(inputs) if c=='1'}
            nlits = {i for (i,c) in enumerate(inputs) if c=='0'}
            products.append((lits, nlits))

        return products

# eg:
# ['A','B','C'] -> {'A':False, 'B':False, 'C':False}, {'A':False, 'B':False, 'C':True}, ...
def bool_gen(varnames):
    n = len(varnames)
    for i in range(2**n):
        yield {name: bool(i & (1<<(n-pos-1))) for (pos, name) in enumerate(varnames)}

def simplify(expr):
    if type(expr) == str:
        expr = parse_python(expr)

    vnames = list(expr.varnames())

    tt = TruthTable(len(vnames), 1)
    for inputs in bool_gen(vnames):
        #print(f'evaluating {expr} under {inputs}')
        result = expr.evaluate(inputs)

        tt_inputs = inputs.values()
        tt_outputs = [int(result)]
        #print(f'tt_inputs: {tt_inputs}')
        #print(f'tt_outputs: {tt_outputs}')
        tt.add(tt_inputs, tt_outputs)

    sum_ = Val(False)

    for product in tt.simplify():
        (lits, nlits) = product

        product = Val(True)
        for i in lits:
            product = And(Var(vnames[i]), product)
        for i in nlits:
            product = And(Not(Var(vnames[i])), product)

        sum_ = Or(product, sum_)

    result = sum_.reduce()

    return result

if __name__ == '__main__':
    # A + /AB
    # should simplify to
    # A + B
    tt = TruthTable(2, 1)
    tt.add([0, 0], [0])
    tt.add([0, 1], [1])
    tt.add([1, 0], [1])
    tt.add([1, 1], [1])
    #print(tt.simplify())

    # A + /AB + /A/B
    tt = TruthTable(2, 1)
    tt.add([0, 0], [1])
    tt.add([0, 1], [1])
    tt.add([1, 0], [1])
    tt.add([1, 1], [1])
    #print(tt.simplify())

    # A+/AB  ->  A+B
    tmp = simplify('A or (not A and B)')
    assert str(tmp) in ['A+B', 'B+A']

    # A/B + AB  ->  A
    tmp = simplify('(A and not B) or (A and B)')
    assert str(tmp) == 'A'

    # /A/B/C + /A/BC  ->  /A/B
    tmp = simplify('(not A and not B and not C) or (not A and not B and C)')
    assert str(tmp) in ['/B/A', '/A/B']

    # /X/YZ + /XYZ + X/Y  - > /XZ + X/Y
    tmp = simplify('(not X and not Y and Z) or (not X and Y and Z) or (X and not Y)')
    assert str(tmp) in ['/XZ+/YX', '/YX+/XZ']

    for n_nodes in range(1, 40):
        expr0 = generate(n_nodes, list('ABCDEFGHIJ'))
        expr1 = simplify(expr0)
        print(f'{expr0} -> {expr1}')

        vnames = expr0.varnames()
        assert to_minterms(expr0, vnames) == to_minterms(expr1, vnames)

    print('pass')
