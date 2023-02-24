#!/usr/bin/env python

import curiousbits.boolalg.tools as batools

import os
import sys
import random

if __name__ == '__main__':
    what = 'all'
    if sys.argv[1:]:
        what = sys.argv[1]

    if what in ['all', 'BoolExprs']:
        expr = batools.parse_python('(not A and not B and not C) or (not A and not B and C)')
        assert str(expr) == '/A/B/C+/A/BC'

    if what in ['all', 'combinatorics']:
        from curiousbits.math.combinatorics import *
        for a in range(1,50):
            for b in range(1,50):
                assert MultiChoose(a,b) == C(a+b-1, b) == StarsBars2(b, a) == MultiChoose(b+1, a-1)

    if what in ['all', 'random-bool-exprs']:
        varnames = list('ABCDEF')
        for n_nodes in range(1, 20):
            print(f'{n_nodes}: ' + str(batools.generate(n_nodes, varnames)))
    
    if what in ['all', 'quine-mccluskey']:
        from curiousbits.boolalg.simplify_qm import simplify
        expr0 = batools.parse_python('A or (A and not B)')
        expr1 = simplify(expr0)
        print(f'{expr0} -> {expr1}')

        expr0 = batools.parse_python('(not A)')
        expr1 = simplify(expr0)
        print(f'{expr0} -> {expr1}')

        for n_nodes in range(1, 40):
            expr0 = batools.generate(n_nodes, list('ABCDEFGHIJ'))
            expr1 = simplify(expr0)
            print(f'{expr0} -> {expr1}')

            vnames = expr0.varnames()
            assert batools.to_minterms(expr0, vnames) == batools.to_minterms(expr1, vnames)

    print('pass')
