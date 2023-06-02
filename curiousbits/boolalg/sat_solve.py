from subprocess import Popen, PIPE

#from . import expr
from .expr import *
from .tools import is_cnf, parse_python
from .tseytin import *

def call_solver(dimacs, program='cryptominisat5'):
    process = Popen([program], stdout=PIPE, stdin=PIPE)
    (stdout, stderr) = process.communicate(input=dimacs.encode('utf-8'))
    exit_code = process.wait()
    return stdout.decode('utf-8').rstrip()

def solve_cnf(expr, solver='cryptominisat5'):
    assert is_cnf(expr)
    dimacs, var2idx = to_dimacs(expr)

    output = call_solver(dimacs, solver)
    lines = output.split('\n')
    if lines[-2] != 's SATISFIABLE': return {}
    if not lines[-1].startswith('v '): return {}
    
    line = lines[-1]
    if not line: return {}
    if not line.startswith('v '): raise Exception('dimacs solution should start with \'v \'')
    if not line.endswith(' 0'): raise Exception('dimacs solution should end with \' 0\'')
    # like '-1 -2 -3 4 5 -6 7 -8 -9 -10 -11'
    assignments = line[2:-2]

    idx2var = {b:a for a,b in var2idx.items()}
    result = {}
    for elem in assignments.split(' '):
        value = True
        if elem.startswith('-'):
            value = False
            elem = elem[1:]
        idx = int(elem)
        result[idx2var[idx]] = value

    return result

#------------------------------------------------------------------------------
# to dimacs
#------------------------------------------------------------------------------

def to_dimacs(conj):
    assert is_cnf(conj)

    var2idx = {name: i+1 for i,name in enumerate(sorted(conj.varnames()))}

    # clause lines look like:
    # [-]<var_id> [-]<var_id> ... [-]<var_id> 0
    # where '-' indicates logical negation
    clauses = []
    for disj in conj.children:
        elems = []
        for lit in disj.children:
            prefix = '-' if type(lit) == Not else ''
            elems.append(prefix + str(var2idx[lit.name]))
        clauses.append(' '.join(elems + ['0']))
    # problem lines look like:
    # p cnf <number_of_vars> <number_of_clauses>
    dimacs = 'p cnf %d %d\n' % (len(var2idx), len(clauses))
    dimacs += '\n'.join(clauses)
    return (dimacs, var2idx)

#------------------------------------------------------------------------------
# convenience solvers
#------------------------------------------------------------------------------

def solve(expr, desired_output=True):
    varnames = expr.varnames()

    expr2, outvar = Tseytin_transformation(expr)

    # append constraint on output
    if not desired_output:
        outvar = Not(outvar)

    expr2.children.append(Or(outvar))

    # solve
    solution = solve_cnf(expr2)
    if not solution:
        return {}

    # pick out original variables (no temporaries)
    result = {name: solution[name] for name in varnames}
    print(result)
    return result

def solve_all(expr, desired_output=True):

    expr = expr.clone()

    while True:
        print('solving:', expr)
        print('solving:', expr.__py__())
        print_truth_table(expr)
        solution = solve(expr, desired_output)
        if not solution:
            break

        names = sorted(solution.keys())
        print(','.join(names) + ': ' + ''.join('1' if solution[n] else '0' for n in names))

        stopper = Or(*[Not(Var(name)) if value else Var(name) for name,value in solution.items()])
        #print('stopper:', stopper)

        expr = And(expr, stopper)
        #print(expr.__str_tabbed_tree__())

    breakpoint()

#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    # /x1 x2 + x1 /x2
    #expr = parse_python('(not x1 and x2) or (x1 and not x2)')
    #print(solve_all(expr))
    #sys.exit(0)

    # (/x1x2+/x2x1+/x2x3)(/x1+/x3+x2)(/x1+x3+x2)(/x3+x1+x2)(/x2+/x3+x1)
    # if x1 x2 x3 == 0 1 0    yes        yes        yes       yes
    expr = parse_python('(not x1 and x2 or x1 and not x2 or not x2 and x3) and (not x1 or x3 or x2) and (not x1 or not x3 or x2) and (x1 or not x3 or x2) and (x1 or not x3 or not x2)')
    print(expr)
    print_truth_table(expr)

    expr2, outvar = Tseytin_transformation(expr)
    print(expr2.varnames())
    print(len(expr2.varnames()))
    print_truth_table(expr2)

    sys.exit(0)

    print(solve_cnf(expr))
    print(solve(expr))

    # /x1 x2 + x1 /x2 + /x2 x3
    expr = parse_python('((not x1) and x2) or (x1 and (not x2)) or ((not x2) and x3)')
    print(expr)
    assert is_cnf(expr) == False

    print(solve_all(expr))
    sys.exit(0)

    print('---- TSEYTIN TRANSFORM ----')

    expr2, outvar = Tseytin_transformation(expr)

    # we also want the output to be true
    expr2.children.append(Or(outvar))

    print(expr2.__str_tabbed_tree__())

    assert is_cnf(expr2)

    dimacs, lookup = to_dimacs(expr2)
    print(dimacs)

    print(solve_cnf(expr2))
