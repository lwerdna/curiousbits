#!/usr/bin/env python

import curiousbits.BoolExprs as be

import os
import sys
import random

if __name__ == '__main__':
    what = 'all'
    if sys.argv[1:]:
        what = sys.argv[1]

    if what in ['all', 'BoolExprs']:
        expr = be.parse('(not A and not B and not C) or (not A and not B and C)')
        assert str(expr) == '/A/B/C+/A/BC'

    if what == 'random-bool-exprs':
        varnames = list('ABCDEF')
        for n_nodes in range(1, 20):
            print(f'{n_nodes}: ' + str(be.generate(n_nodes, varnames)))
    
    if what == 'quine-mccluskey':
        expr0 = be.parse('A or (A and not B)')
        expr1 = be.simplify_quine_mccluskey(expr0)
        print(f'{expr0} -> {expr1}')

        expr0 = be.parse('(not A)')
        expr1 = be.simplify_quine_mccluskey(expr0)
        print(f'{expr0} -> {expr1}')

        for n_nodes in range(1, 40):
            expr0 = be.generate(n_nodes, list('ABCDEFGHIJ'))
            expr1 = be.simplify_quine_mccluskey(expr0)
            print(f'{expr0} -> {expr1}')

            vnames = expr0.varnames()
            assert be.to_minterms(expr0, vnames) == be.to_minterms(expr1, vnames)

    print('pass')
