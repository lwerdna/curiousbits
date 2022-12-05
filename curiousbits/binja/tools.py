import binaryninja

import networkx as nx

def llil_cfg_as_networkx(filepath, funcname):
    G = nx.DiGraph()

    with binaryninja.open_view(filepath) as bv:
        func = bv.get_functions_by_name(funcname)[0]

        # add nodes
        for bb in func.low_level_il:
            G.add_node(str(bb.index))

        # add edges
        for src in func.low_level_il:
            for dst in [e.target for e in src.outgoing_edges]:
                G.add_edge(str(src.index), str(dst.index))

    return G

#if __name__ == '__main__':
#    
