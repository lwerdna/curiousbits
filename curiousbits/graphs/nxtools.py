# TEST WITH: python -m curiousbits.graphs.nxtools

import random
from subprocess import Popen, PIPE

import networkx as nx

#------------------------------------------------------------------------------
# graphviz integration
#------------------------------------------------------------------------------

# f_node_attrs: function to return additional node attributes
# f_edge_attrs: function to return additional edge attributes
def gen_dot(G, f_node_attrs=None, f_edge_attrs=None, f_extra=None):
    dot = []
    dot.append('digraph G {')

    # global graph settings
    dot.append('// global settings')
    dot.append('node [];')
    dot.append('edge [];')

    # node list
    dot.append('// nodes')
    for n in G.nodes:
        attrs = []
        if f_node_attrs:
            attrs.extend(f_node_attrs(G, n))
        dot.append(f'{n} [' + ' '.join(attrs) + '];')

    # edge list
    dot.append('// edges')
    for (n0,n1) in G.edges:
        attrs = []
        if f_edge_attrs:
            attrs.extend(f_edge_attrs(G, n0, n1))
        dot.append(f'{n0} -> {n1} [' + ' '.join(attrs) + '];')

    if f_extra != None:
        dot.append(f_extra(G))

    dot.append('}')

    result = '\n'.join(dot)
    #print(result)
    return result

# G:            the graph
# fpath:        path to output file
# f_node_attrs: function to return additional node attributes
# f_edge_attrs: function to return additional edge attributes
def draw(G, fpath, f_node_attrs=None, f_edge_attrs=None, f_extra=None, verbose=False):
    dot = gen_dot(G, f_node_attrs, f_edge_attrs, f_extra)

    if fpath.endswith('.svg'):
        ftype = 'svg'
    elif fpath.endswith('.png'):
        ftype = 'png'
    else:
        raise Exception()

    cmd = ['dot', f'-T{ftype}', '-o', fpath]

    if verbose:
        print('cmd: ' + ' '.join(cmd))

    process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = process.communicate(dot.encode('utf-8'))
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')
    #print('stdout: -%s-' % stdout)
    #print('stderr: -%s-' % stderr)
    process.wait()

#------------------------------------------------------------------------------
# generate graphs
#------------------------------------------------------------------------------

# CFG with single entry, single exit (SESE)
# https://en.wikipedia.org/wiki/Single-entry_single-exit
def gen_SESE(num_nodes):
    G = nx.gnp_random_graph(num_nodes, 2*1/num_nodes, seed=None, directed=True)

    #print('-- removing unconnected nodes')
    for node in [n for n in G.nodes if G.degree(n) == 0]:
        #print(f'removing {node}')
        G.remove_node(node)

    assert [n for n in G.nodes if G.degree(n) == 0] == []

    #print('-- removing edges until all out degrees <= 2')
    for node in [n for n in G.nodes if G.out_degree(n) > 2]:
        out_edges = list(G.out_edges(node))
        limit = random.randint(1,2)
        for edge in out_edges[limit:]:
            #print(f'removing {edge}')
            G.remove_edge(*edge)

    assert [n for n in G.nodes if G.out_degree(n) > 2] == []

    #print('-- removing cycles')
    while True:
        try:
            cycle = nx.find_cycle(G)
        except nx.NetworkXNoCycle:
            break
        edge = random.choice(cycle)
        #print(f'removing {edge}')
        G.remove_edge(*edge)

    #print('-- adding nodes until single entry')
    node_id = num_nodes
    while True:
        nodes = [n for n in G.nodes if G.in_degree(n)==0]
        if len(nodes) == 1:
            break
        G.add_node(node_id)
        G.add_edge(node_id, nodes[0])
        G.add_edge(node_id, nodes[1])
        #print(f'adding {node_id}->{nodes[0]} and {node_id}->{nodes[1]}')
        node_id += 1

    assert len([n for n in G.nodes if G.in_degree(n)==0]) == 1

    #print('-- adding nodes until single exit')
    while True:
        nodes = [n for n in G.nodes if G.out_degree(n)==0]
        if len(nodes) == 1:
            break
        G.add_node(node_id)
        G.add_edge(nodes[0], node_id)
        G.add_edge(nodes[1], node_id)
        #print(f'adding {node_id}->{nodes[0]} and {node_id}->{nodes[1]}')
        node_id += 1

    assert len([n for n in G.nodes if G.out_degree(n)==0]) == 1

    return G

#------------------------------------------------------------------------------
# graph computation
#------------------------------------------------------------------------------

def find_root(G):
    candidates = [n for n in G.nodes if G.in_degree(n) == 0]
    if len(candidates) == 0:
        raise Exception('cannot find root: no nodes with in degree 0')
    if len(candidates) > 1:
        raise Exception('cannot find root: multiple nodes with in degree 0')
    return candidates[0]

def find_single_exit(G):
    candidates = [n for n in G.nodes if G.out_degree(n) == 0]
    if len(candidates) == 0:
        raise Exception('cannot find single exit: no nodes with out degree 0')
    if len(candidates) > 1:
        raise Exception('cannot find single exit: multiple nodes with out degree 0')
    return candidates[0]

# compute the dominator tree
# incoming graph must be rooted (must have an entry node) marked by having a single node with degree 0
# https://en.wikipedia.org/wiki/Rooted_graph
def compute_dominator_tree(G):
    T = nx.DiGraph()

    root_node = find_root(G)

    for (b, a) in nx.immediate_dominators(G, root_node).items():
        T.add_node(b)

        if a == b:
            continue

        T.add_edge(a, b)

    return T

# compute the postdominator tree
# if the incoming graph does not have a single exit, a temporary node will be added
def compute_postdominator_tree(G):
    G = G.copy()

    # add single exit if needed
    if not is_single_exit(G):
        G = G.copy()
        add_single_exit(G)

    return compute_dominator_tree(reverse_graph(G))

# return a dictionary:
# { A: [ nodes that dominate A ],
#   B: [ nodes that dominate B ],
#   ...
# }
#
# this is a non-strict version: node N is considered a dominator of node N
def compute_dominators(G):
    T = compute_dominator_tree(G)

    result = {n:{n} for n in G}
    for dominator in T.nodes:
        for dominatee in nx.descendants(T, dominator):
            result[dominatee].add(dominator)

    return result

# return a dictionary:
# { A: [ nodes that postdominate A ],
#   B: [ nodes that postdominate B ],
#   ...
# }
#
# this is a non-strict version: node N is considered a postdominator of node N
def compute_postdominators(G):
    T = compute_postdominator_tree(G)

    R = find_root(T)

    if is_temporary_node(R):
        T.remove_node(R)

    result = {n:{n} for n in G}
    for dominator in T.nodes:
        for dominatee in nx.descendants(T, dominator):
            result[dominatee].add(dominator)

    return result

def reverse_graph(G):
    T = nx.DiGraph()
    for (a,b) in G.edges():
        T.add_edge(b, a)
    return T

# Return { A: B, ... } where B is the node where all outgoing paths from A
# converge, or join. B exists for every A when graph is single-exit.
def compute_joins(G):
    T = compute_postdominator_tree(G)

    R = find_root(T)
    if is_temporary_node(R):
        T.remove_node(R)

    return {b:a for (a,b) in T.edges}

def compute_control_dependency_graph(G, verbose=False):
    if not is_single_exit(G):
        G = G.copy()
        add_single_exit(G)

    postdoms = compute_postdominators(G)

    result = nx.DiGraph()
    temp_node = gen_temporary_node(G)
    result.add_edge(temp_node, find_root(G))
    result.add_edge(temp_node, find_single_exit(G))

    for n in G.nodes:
        children = list(G.successors(n))

        candidates = set()
        for c in children:
            candidates = candidates.union({spd for spd in postdoms[c] if spd != n})

        if verbose:
            print(f'node {n} has children {children} and candidates {candidates}')
        for dependent in candidates:
            if not all(dependent in postdoms[c] for c in children):
                result.add_edge(n, dependent)
                if verbose:
                    print(f'candidate {dependent} passes! adding result edge {n}->{dependent}')
            else:
                if verbose:
                    print(f'candidate {dependent} skipped because it post-dominates all children of {n}')
                pass

    return result

#------------------------------------------------------------------------------
# misc
#------------------------------------------------------------------------------

def is_single_exit(G):
    return len([n for n in G.nodes if G.out_degree(n) == 0])==1

def gen_temporary_node(G):
    return next(f'nxt_temp{i}' for i in range(999999) if not f'nxt_temp{i}' in G.nodes)

def is_temporary_node(n):
    #if re.match(r'^temp\d+$', R):
    return n.startswith('nxt_temp') and n[-1].isdigit()

# edits in-place (make an explicit copy if needed)
def add_single_exit(G):
    leaves = [n for n in G.nodes() if G.out_degree(n) == 0]

    if len(leaves) == 0:
        raise Exception('cannot add single exit: no nodes with out degree 0')
    elif len(leaves) == 1:
        raise Exception('cannot add single exit: already exists')

    exit_node = gen_temporary_node(G)
    for leaf in leaves:
        G.add_edge(leaf, exit_node)

    return G

#------------------------------------------------------------------------------
# fixed test cases
#------------------------------------------------------------------------------

def gen_dream_R2():
    G = nx.DiGraph()

    G.add_node('b1')
    G.add_node('b2')
    G.add_node('n4')
    G.add_node('n5')
    G.add_node('n6')
    G.add_node('n7')

    G.add_edge('b1', 'n4')
    G.add_edge('b1', 'b2')
    G.add_edge('n4', 'n5')
    G.add_edge('b2', 'n5')
    G.add_edge('b2', 'n6')
    G.add_edge('n5', 'n7')
    G.add_edge('n6', 'n7')

    return G

def gen_test0():
    G = nx.DiGraph()

    G.add_edge('1', '2')
    G.add_edge('1', '3')
    G.add_edge('2', '4')
    G.add_edge('2', '5')
    G.add_edge('3', '7')
    G.add_edge('4', '6')
    G.add_edge('5', '6')
    G.add_edge('6', '7')

    return G

# no single exit, no join points
def gen_test1():
    G = nx.DiGraph()

    G.add_edge('0', '1')
    G.add_edge('0', '2')
    G.add_edge('1', '3')
    G.add_edge('1', '4')
    G.add_edge('3', '5')
    G.add_edge('3', '6')
    G.add_edge('5', '7')
    G.add_edge('5', '8')

    return G

# from Optimal Control Dependence Computation and the Roman Chariots Problem -Pingali, Bilardi
def gen_test2():
    G = nx.DiGraph()
    G.add_edge('START', 'a')
    G.add_edge('START', 'END')
    G.add_edge('a', 'b')
    G.add_edge('a', 'c')
    G.add_edge('b', 'c')
    G.add_edge('c', 'd')
    G.add_edge('c', 'e')
    G.add_edge('d', 'f')
    G.add_edge('e', 'f')
    G.add_edge('f', 'b')
    G.add_edge('f', 'g')
    G.add_edge('g', 'END')
    return G

#------------------------------------------------------------------------------
# main/test
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    do_draw = '--draw' in sys.argv

    # one-off stuff
    if 0:
        sys.exit(0)

    print('-------- testing dominators, post-dominators')
    G = gen_test0()
    assert compute_dominators(G) == {'6':{'6','1','2'}, '2':{'2','1'}, '4':{'4','1','2'}, '3':{'3','1'}, '7':{'7','1'}, '5':{'5','1','2'}, '1':{'1'}}
    assert compute_postdominators(G) == {'1':{'1','7'}, '2':{'2','7','6'}, '4':{'4','7','6'}, '6':{'6','7'}, '3':{'3','7'}, '5':{'5','7','6'}, '7':{'7'}}
    if do_draw:
        draw(G, '/tmp/test0.svg', verbose=True)
        draw(compute_control_dependency_graph(G), '/tmp/test0-cdg.svg', verbose=True)

    G = gen_test1()
    assert compute_dominators(G) == {'3':{'3','0','1'}, '1':{'1','0'}, '5':{'5','0', '1', '3'}, '4':{'4','0', '1'}, '8':{'8','0', '1', '3', '5'}, '7':{'7','0', '1', '3', '5'}, '6':{'6','0', '1', '3'}, '2':{'2','0'}, '0':{'0'}}
    assert compute_postdominators(G) == {'6':{'6'}, '1':{'1'}, '3':{'3'}, '8':{'8'}, '5':{'5'}, '7':{'7'}, '4':{'4'}, '2':{'2'}, '0':{'0'}}
    if do_draw:
        draw(G, '/tmp/test1.svg', verbose=True)
        draw(compute_control_dependency_graph(G), '/tmp/test0-cdg.svg', verbose=True)

    G = gen_dream_R2()
    assert compute_dominators(G) == {'n7':{'n7','b1'}, 'n4':{'n4','b1'}, 'b2':{'b2','b1'}, 'n6':{'n6','b1', 'b2'}, 'n5':{'n5','b1'}, 'b1':{'b1'}}
    assert compute_postdominators(G) == {'n4':{'n4','n7', 'n5'}, 'b2':{'b2','n7'}, 'n5':{'n5','n7'}, 'b1':{'b1','n7'}, 'n6':{'n6','n7'}, 'n7':{'n7'}}
    if do_draw:
        draw(G, '/tmp/dream_r2.svg', verbose=True)
        draw(compute_control_dependency_graph(G), '/tmp/dream_r2-cdg.svg', verbose=True)

    G = gen_test2()
    assert compute_dominators(G) == {'START':{'START'}, 'a':{'a','START'}, 'END':{'END','START'}, 'b':{'b','START', 'a'}, 'c':{'c','START', 'a'}, 'd':{'d','START', 'a', 'c'}, 'e':{'e','START', 'a', 'c'}, 'f':{'f','START', 'a', 'c'}, 'g':{'g','START', 'a', 'c', 'f'}}
    assert compute_postdominators(G) == {'START':{'START','END'}, 'a':{'a','END', 'g', 'f', 'c'}, 'END':{'END','END'}, 'b':{'b','END', 'g', 'f', 'c'}, 'c':{'c','END', 'g', 'f'}, 'd':{'d','END', 'g', 'f'}, 'e':{'e','END', 'g', 'f'}, 'f':{'f','END', 'g'}, 'g':{'g','END'}}
    if do_draw:
        draw(G, '/tmp/test2.svg', verbose=True)
        draw(compute_control_dependency_graph(G), '/tmp/test2-cdg.svg', verbose=True)

    print('-------- testing join points')

    G = gen_test0()
    assert compute_joins(G) == {'6': '7', '3': '7', '1': '7', '5': '6', '4': '6', '2': '6'}

    red_edges = set()
    for a,b in compute_joins(G).items():
        if G.out_degree(a) > 1:
            G.add_edge(a, b)
            red_edges.add((a, b))

    def eattrs(G, a, b):
        if (a, b) in red_edges:
            return ['style="dashed"', 'color="red"']
        return []

    if do_draw:
        draw(G, '/tmp/test0-joins.svg', f_edge_attrs=eattrs, verbose=True)

    # draw the test1 CFG, join points
    G = gen_test1()
    assert compute_joins(G) == {}
    G.add_edge('7', '9')
    G.add_edge('8', '9')
    assert compute_joins(G) == {'8': '9', '7': '9', '5': '9'}
    G.add_edge('3', '10')
    G.add_edge('4', '10')
    assert compute_joins(G) == {'4': '10', '8': '9', '7': '9', '5': '9'}
    G.add_edge('6', '11')
    G.add_edge('10', '11')
    assert compute_joins(G) == {'10': '11', '6': '11', '4': '10', '8': '9', '7': '9', '5': '9'}
    G.add_edge('11', '12')
    G.add_edge('9', '12')
    assert compute_joins(G) == {'11': '12', '9': '12', '3': '12', '1': '12', '10': '11', '6': '11', '4': '10', '8': '9', '7': '9', '5': '9'}

    red_edges = set()
    for a,b in compute_joins(G).items():
        if G.out_degree(a) > 1:
            G.add_edge(a, b)
            red_edges.add((a, b))

    def eattrs(G, a, b):
        if (a, b) in red_edges:
            return ['style="dashed"', 'color="red"']
        return []

    if do_draw:
        draw(G, '/tmp/test1-joins.svg', f_edge_attrs=eattrs, verbose=True)

    # draw some randomly generated single-entry, single-exit CFG's
    for i in range(4):
        G = gen_SESE(16)
        if do_draw:
            draw(G, f'/tmp/generated{i}.svg', verbose=True)
