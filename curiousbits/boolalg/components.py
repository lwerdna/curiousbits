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

if __name__ == '__main__':
    import sys

    S, C_out = full_adder('A', 'B', 'C_in')

    #print('S = ', S)
    #print('C_out = ', C_out)

    print(f'writing half-adder-s.svg')
    shellout(['dot', '-Tsvg', '-o', 'half-adder-s.svg'], gen_dot(S))

    print(f'writing half-adder-c-out.svg')
    shellout(['dot', '-Tsvg', '-o', 'half-adder-c-out.svg'], gen_dot(S))
