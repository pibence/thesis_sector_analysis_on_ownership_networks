import networkx as nx
import numpy as np
import pandas as pd

import logging

logging.basicConfig(
    filename="logs/graph.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    force=True,
)


def propagate_shock_from_one_node(G, node, shock, fraction_to_propagate, counter=0):

    """
    Not in use, not working currently!
    """
    # TODO add new graph as a returned value
    if shock < 10:
        pass

    elif G.nodes[node]["assets"] > 0:
        G.nodes[node]["assets"] -= shock

        weight_sum = 0
        for neighbor in G.neighbors(node):
            weight_sum += G[node][neighbor]["weight"]

        for neighbor in G.neighbors(node):
            proportion = G[node][neighbor]["weight"] / weight_sum
            shock_to_pass = shock * proportion * fraction_to_propagate
            return propagate_shock_from_one_node(
                G, neighbor, shock_to_pass, fraction_to_propagate, counter + 1
            )
    if counter == 0:
        return G


def propagate_default(g, failure_threshold):
    
    round = 1
    new_defaulter = True

    while new_defaulter:
        new_defaulter = False

        default = [node for node in g.nodes() if g.nodes[node]['default_round']==round] 
        
        round += 1
        
        for n in default:

            # calculating the sum of weights where the edge leads to a non-defaulted node    
            weight_sum = 0

            for neighbor in g.neighbors(n):
                if not g.nodes[neighbor]['default_round']:
                    weight_sum += g[n][neighbor]["weight"]

            if weight_sum == 0:
                continue
            else:
                for neighbor in g.neighbors(n):
                    if not g.nodes[neighbor]['default_round']:
                        proportion = g[n][neighbor]['weight'] / weight_sum
                        g.nodes[neighbor]['assets'] -= g.nodes[n]['equity'] * proportion
                        g.nodes[neighbor]['equity'] -= g.nodes[n]['equity'] * proportion

                        if g.nodes[neighbor]['equity'] < g.nodes[neighbor]['equity'] * failure_threshold:
                            new_defaulter = True
                            g.nodes[neighbor]['default_round'] = round

    return g
             