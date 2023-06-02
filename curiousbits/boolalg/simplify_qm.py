# convenience wrapper to the quine-mccluskey package
# pip install quine-mccluskey

from .tools import generate, to_truth_indices
from .expr import *

def simplify(expr):
    from quine_mccluskey.qm import QuineMcCluskey

    qm = QuineMcCluskey(use_xor=False)

    vnames = sorted(expr.varnames())
    ones = to_truth_indices(expr)
    result = qm.simplify(ones, dc=[], num_bits=len(vnames))

    if result == None:
        return Val(False)
    if len(result) == 1 and list(result)[0] == '-'*len(vnames):
        return Val(True)

    products = []
    # s is like '1-'
    for s in result:
        factors = []
        for (i,c) in enumerate(s):
            match c:
                case '-':
                    continue
                case '1':
                    factors.append(Var(vnames[i]))
                case '0':
                    factors.append(Not(Var(vnames[i])))
                case _:
                    raise Exception(f'error: {c}')

        products.append(And(*factors))

    return Or(*products)

if __name__ == '__main__':
    for n_nodes in range(1, 40):
        expr0 = generate(n_nodes, list('ABCDEFGHIJ'))
        expr1 = simplify(expr0)
        print(f'{expr0} -> {expr1}')

        vnames = expr0.varnames()
        assert to_truth_indices(expr0, vnames) == to_truth_indices(expr1, vnames)

    print('pass')
