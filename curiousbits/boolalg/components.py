#from . import expr
from .expr import *
from .tools import gen_dot, shellout
from .tseytin import *

def half_adder(A, B):
    A = Var(A) if type(A)==str else A
    B = Var(B) if type(B)==str else B

    S = Xor(A, B)
    C_out = And(A.clone(), B.clone())

    return (S, C_out)

def full_adder(A, B, C_in):
    A = Var(A) if type(A)==str else A
    B = Var(B) if type(B)==str else B
    C_in = Var(C_in) if type(C_in)==str else C_in

    t0, t1 = half_adder(A, B)
    S, t2 = half_adder(t0, C_in)
    C_out = Or(t1, t2)

    return (S, C_out)

# eg:
# addends0: ['A0', 'A1', 'A2', 'A3']
# addends1: ['B0', 'B1', 'B2', 'B3']
#
# returns n+1 equations (carry out for the last dude)

def register_adder(addends0, addends1):
    assert len(addends0) == len(addends1)

    addends0 = [Var(x) if type(x)==str else x for x in addends0]
    addends1 = [Var(x) if type(x)==str else x for x in addends1]

    result = []
    expr_carry = None
    while addends0:
        a = addends0.pop(0)
        b = addends1.pop(0)

        if expr_carry == None:
            expr_sum, expr_carry = half_adder(a, b)
        else:
            expr_sum, expr_carry = full_adder(a, b, expr_carry)

        result.append(expr_sum)

    result.append(expr_carry)
    return result

if __name__ == '__main__':
    import sys

    print('Generate and test a 4-bit adder.')
    #   0111
    # + 0011
    # ------
    #   1010
    equations = register_adder(['A0', 'A1', 'A2', 'A3'], ['B0', 'B1', 'B2', 'B3'])

    values = {'A0':True, 'B0':True}
    assert equations[0].evaluate(values) == False
    values['A1'] = True
    values['B1'] = True
    assert equations[1].evaluate(values) == True
    values['A2'] = True
    values['B2'] = False
    assert equations[2].evaluate(values) == False
    values['A3'] = False
    values['B3'] = False
    assert equations[3].evaluate(values) == True

    print(f'writing 4-bit-adder-msb.svg')
    shellout(['dot', '-Tsvg', '-o', '4-bit-adder-msb.svg'], gen_dot(equations[3]))

    print('Generate and draw a 1-bit full adder.')
    S, C_out = full_adder('A', 'B', 'C_in')
    print(f'writing full-adder-s.svg')
    shellout(['dot', '-Tsvg', '-o', 'full-adder-s.svg'], gen_dot(S))
    print(f'writing full-adder-c-out.svg')
    shellout(['dot', '-Tsvg', '-o', 'full-adder-c-out.svg'], gen_dot(C_out))

    
