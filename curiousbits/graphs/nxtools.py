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

def reversed_graph(G):
    T = nx.DiGraph()
    for (a,b) in G.edges():
        T.add_edge(b, a)
    return T

# Return { A: B, ... } where B is the node where all outgoing paths from A
# converge, or join. B exists for every A when graph is single-exit.
def joins(G):
    rgraph = reversed_graph(G)
    dtree = dominator_tree(rgraph)
    return {b:a for (a,b) in dtree.edges}

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

#------------------------------------------------------------------------------
# main/test
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    # draw the test CFG
    G = gen_test0()
    draw(G, '/tmp/test0.svg', verbose=True)

    # draw the test CFG, dominator tree
    D = dominator_tree(G)
    draw(D, f'/tmp/test0-domtree.svg', verbose=True)

    # draw the test CFG, join points
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

    # draw the "dream" CFG
    G = gen_dream_R2()
    draw(G, '/tmp/dream_r2.svg', verbose=True)

    # draw some randomly generated single-entry, single-exit CFG's
    for i in range(4):
        G = gen_SESE(16)
        draw(G, f'/tmp/generated{i}.svg', verbose=True)
