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

# CFG with single entry, single successor (SESE)
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

# compute the dominator tree
# incoming graph must be rooted (must have an entry node) marked by having a single node with degree 0
# https://en.wikipedia.org/wiki/Rooted_graph
def dominator_tree(G):
    T = nx.DiGraph()

    dzeros = [n for n in G.nodes if G.in_degree(n) == 0]
    assert len(dzeros) == 1
    root = dzeros[0]

    for (b, a) in nx.immediate_dominators(G, root).items():
        T.add_node(b)
        T.nodes[b]['label'] = G.nodes[b].get('label', str(b))

        if a == b:
            continue

        T.add_edge(a, b)

    return T

# return a dictionary:
# { A: [ nodes that dominate A ],
#   B: [ nodes that dominate B ],
#   ...
# }
def dominators(G):
    T = dominator_tree(G)

    result = {}
    for dominator in T.nodes:
        for dominatee in nx.descendants(T, dominator):
            result[dominatee] = result.get(dominatee, []) + [dominator]

    return result

def postdominators(G):
    NSE = not is_single_exit(G)

    if NSE:
        temp = next(f'temp{i}' for i in range(999999) if not f'temp{i}' in G.nodes)
        for src in [n for n in G.nodes() if G.out_degree(n) == 0]:
            G.add_edge(src, temp)

    result = dominators(reversed_graph(G))

    if NSE:
        G.remove_node(temp)
        for n in result:
            result[n].remove(temp)

    return result

def reversed_graph(G):
    T = nx.DiGraph()
    for (a,b) in G.edges():
        T.add_edge(b, a)
    return T

# Return { A: B, ... } where B is the node where all outgoing paths from A
# converge, or join. B exists for every A when graph is single-exit.
def joins(G):
    temp = None

    # generate dummy node
    NSE = not is_single_exit(G)
    if NSE:
        temp = next(f'temp{i}' for i in range(999999) if not f'temp{i}' in G.nodes)
        for src in [n for n in G.nodes() if G.out_degree(n) == 0]:
            G.add_edge(src, temp)

    rgraph = reversed_graph(G)
    #draw(rgraph, '/tmp/reversed.svg', verbose=True)
    dtree = dominator_tree(rgraph)
    #draw(dtree, '/tmp/dominator.svg', verbose=True)
    if NSE:
        G.remove_node(temp)

    return {b:a for (a,b) in dtree.edges if a != temp and G.out_degree(b) > 1}

#------------------------------------------------------------------------------
# misc
#------------------------------------------------------------------------------

def is_single_exit(G):
    return len([n for n in G.nodes if G.out_degree(n) == 0])==1

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

#------------------------------------------------------------------------------
# main/test
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    print('-------- testing dominators, post-dominators')
    G = gen_test0()
    assert dominators(G) == {'6': ['1', '2'], '2': ['1'], '4': ['1', '2'], '3': ['1'], '7': ['1'], '5': ['1', '2']}
    assert postdominators(G) == {'1': ['7'], '2': ['7', '6'], '4': ['7', '6'], '6': ['7'], '3': ['7'], '5': ['7', '6']}
    G = gen_test1()
    assert dominators(G) == {'3': ['0', '1'], '1': ['0'], '5': ['0', '1', '3'], '4': ['0', '1'], '8': ['0', '1', '3', '5'], '7': ['0', '1', '3', '5'], '6': ['0', '1', '3'], '2': ['0']}
    assert postdominators(G) == {'6': [], '1': [], '3': [], '8': [], '5': [], '7': [], '4': [], '2': [], '0': []}

    G = gen_dream_R2()
    assert dominators(G) == {'n7': ['b1'], 'n4': ['b1'], 'b2': ['b1'], 'n6': ['b1', 'b2'], 'n5': ['b1']}
    assert postdominators(G) == {'n4': ['n7', 'n5'], 'b2': ['n7'], 'n5': ['n7'], 'b1': ['n7'], 'n6': ['n7']}

    print('-------- drawing, testing joins')

    # draw the test CFG
    G = gen_test0()
    draw(G, '/tmp/test0.svg', verbose=True)

    # draw the test0 CFG, dominator tree
    D = dominator_tree(G)
    draw(D, f'/tmp/test0-domtree.svg', verbose=True)

    # draw the test CFG, join points
    assert joins(G) == {'1':'7', '2':'6'}

    red_edges = set()
    for a,b in joins(G).items():
        if G.out_degree(a) > 1:
            G.add_edge(a, b)
            red_edges.add((a, b))

    def eattrs(G, a, b):
        if (a, b) in red_edges:
            return ['style="dashed"', 'color="red"']
        return []

    draw(G, '/tmp/test0-joins.svg', f_edge_attrs=eattrs, verbose=True)

    # draw the test1 CFG, join points
    G = gen_test1()
    assert joins(G) == {}
    G.add_edge('7', '9')
    G.add_edge('8', '9')
    assert joins(G) == {'5':'9'}
    G.add_edge('3', '10')
    G.add_edge('4', '10')
    assert joins(G) == {'5':'9'}
    G.add_edge('6', '11')
    G.add_edge('10', '11')
    assert joins(G) == {'5':'9'}
    G.add_edge('11', '12')
    G.add_edge('9', '12')
    assert joins(G) == {'5':'9', '1':'12', '3':'12'}

    red_edges = set()
    for a,b in joins(G).items():
        if G.out_degree(a) > 1:
            G.add_edge(a, b)
            red_edges.add((a, b))

    def eattrs(G, a, b):
        if (a, b) in red_edges:
            return ['style="dashed"', 'color="red"']
        return []

    draw(G, '/tmp/test1-joins.svg', f_edge_attrs=eattrs, verbose=True)

    # draw the "dream" CFG
    G = gen_dream_R2()
    draw(G, '/tmp/dream_r2.svg', verbose=True)

    # draw some randomly generated single-entry, single-exit CFG's
    for i in range(4):
        G = gen_SESE(16)
        draw(G, f'/tmp/generated{i}.svg', verbose=True)
