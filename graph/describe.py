import pandas as pd
import networkx as nx
import numpy as np
import logging


logging.basicConfig(
    filename="logs/graph.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    force=True,
)


def create_descriptive_table(graphs: list):
    """
    Function to create a descriptive analysis on both graphs.Node count, edge count,
    connectedness, largest connected components, diameter, and clustering coefficients
    are calculated. Graphs should be given in original, projected order.
    """

    names = ["original", "projected"]
    ret_list = []
    for i, graph in enumerate(graphs):
        ret_dict = {}
        ret_dict["name"] = names[i]
        ret_dict["nodes"] = len(graph.nodes())
        ret_dict["edges"] = len(graph.edges())

        if isinstance(graph, nx.DiGraph):
            ret_dict["is_directed"] = True
            ret_dict["is_connected"] = nx.is_strongly_connected(graph)
            largest_cc = max(nx.strongly_connected_components(graph), key=len)

        elif isinstance(graph, nx.Graph):
            ret_dict["is_directed"] = False
            ret_dict["is_connected"] = nx.is_connected(graph)
            largest_cc = max(nx.connected_components(graph), key=len)

        s = graph.subgraph(largest_cc).copy()

        ret_dict["largest_comp_frac"] = len(largest_cc) / ret_dict["nodes"]
        logging.debug("Low calculating capacity basic metrics are calculated")

        ret_dict["diameter_of_largest_cc"] = nx.diameter(s)
        logging.debug(f"diameter is calculated for the {i}. graph")
        ret_dict["clustering_coefficient"] = calculate_clustering_coeff(
            s, s.nodes(), "weight"
        )
        logging.debug(f"clustering coefficient is calculated for the {i}. graph")

        ret_list.append(ret_dict)

    ret_df = pd.DataFrame.from_dict(ret_list)
    ret_df = ret_df.set_index("name")

    return ret_df


def analyze_sectors(g, sectors, cc_weight="Arithm"):
    """
     Return the nodes, absolute and relative size, clustering coefficient and
    rthe edges within sector to all edges of the sector ratio.
     The difference between sector_clustering_coefficient and avg_clustering_coefficient
     is that the sector one takes only the subgraph for the sector as input and
     calculates the global cc for the sector, while the avg calculates the cc for
     every node in the sector and takes the average of them. Both cc metrics are
     weighted with geometric average.
     weighted cc ref:
     https://www.sciencedirect.com/science/article/abs/pii/S0378873309000070?via%3Dihub
    """

    largest_cc = max(nx.connected_components(g), key=len)
    h = g.subgraph(largest_cc).copy()

    total_market_size = get_graph_size_by_assets(h)

    ret_list = []
    for sector in sectors:
        ret_dict = {}
        ret_dict["sector"] = sector

        sector_nodes = get_sector_nodes(h, sector)
        s = h.subgraph(sector_nodes).copy()
        ret_dict["nodes"] = len(sector_nodes)

        total_sector_size = get_graph_size_by_assets(s)

        ret_dict["total_sector_size"] = total_sector_size
        ret_dict["rel_sector_size"] = total_sector_size / total_market_size
        logging.debug(f"Node and size info for {sector} is added.")

        if cc_weight == "Geom":
            ret_dict["sector_clustering_coefficient"] = calculate_clustering_coeff(
                s, sector_nodes, "weight"
            )
            ret_dict["avg_clustering_coefficient"] = calculate_clustering_coeff(
                h, sector_nodes, "weight"
            )
        elif cc_weight == "Arithm":
            ret_dict[
                "sector_clustering_coefficient"
            ] = calculate_modified_clustering_coeff(s, sector_nodes, "weight")
            ret_dict[
                "avg_clustering_coefficient"
            ] = calculate_modified_clustering_coeff(h, sector_nodes, "weight")
        logging.debug(f"Clustering coefficients for {sector} is added.")

        equity_level = []
        edge_weights_in_sector = []
        edge_weights_from_sector = []
        for n in s.nodes():
            for neighbor in h.neighbors(n):
                if neighbor not in s:
                    edge_weights_from_sector.append(h[n][neighbor]["weight"])
                else:
                    edge_weights_in_sector.append(h[n][neighbor]["weight"])

            equity_level.append(s.nodes[n]["equity"] / s.nodes[n]["assets"])

        ret_dict["edge_ratio"] = len(edge_weights_in_sector) / (
            len(edge_weights_in_sector) + len(edge_weights_from_sector)
        )
        ret_dict["weighted_edge_ratio"] = np.sum(edge_weights_in_sector) / (
            np.sum(edge_weights_in_sector) + np.sum(edge_weights_from_sector)
        )
        ret_dict["equity_level"] = np.mean(equity_level)
        logging.debug(f"edge ratio and equity level for {sector} is added.")

        ret_list.append(ret_dict)
        logging.info(f"{sector} sector metrics calculation is finished.")

    ret_df = pd.DataFrame.from_dict(ret_list)
    ret_df = ret_df.set_index("sector")

    return ret_df


def get_sector_nodes(g, sector: str):
    """Helper function to get every node in one sector."""
    return [n for n in g.nodes() if g.nodes[n]["sector"] == sector]


def get_graph_size_by_assets(g):
    """Helper function to summarize asset values in a graph."""
    total_size = 0
    for n in g.nodes():
        total_size += g.nodes[n]["assets"]

    return total_size


def calculate_clustering_coeff(g, nodes, weight):
    cc = list(nx.clustering(g, nodes=nodes, weight=weight).values())
    return np.mean(cc)


def calculate_modified_clustering_coeff(g, nodes, weight):
    cc = list(modified_clustering(g, nodes=nodes, weight=weight).values())
    return np.mean(cc)


def _weighted_triangles_and_degree_iter(G, nodes=None, weight="weight"):
    """
    @copyright: networkx package, clustering function

    Return an iterator of (node, degree, weighted_triangles).

    Used for weighted clustering.
    Note: this returns the geometric average weight of edges in the triangle.
    Also, each triangle is counted twice (each direction).
    So you may want to divide by 2.

    """

    if weight is None or G.number_of_edges() == 0:
        max_weight = 1
    else:
        max_weight = max(d.get(weight, 1) for u, v, d in G.edges(data=True))
    if nodes is None:
        nodes_nbrs = G.adj.items()
    else:
        nodes_nbrs = ((n, G[n]) for n in G.nbunch_iter(nodes))

    def wt(u, v):
        return G[u][v].get(weight, 1) / max_weight

    for i, nbrs in nodes_nbrs:
        inbrs = set(nbrs) - {i}
        weighted_triangles = 0
        seen = set()
        for j in inbrs:
            seen.add(j)
            # This avoids counting twice -- we double at the end.
            jnbrs = set(G[j]) - seen
            # Only compute the edge weight once, before the inner inner
            # loop.
            wij = wt(i, j)
            weighted_triangles += sum(
                [(wij + wt(j, k) + wt(k, i)) / 3 for k in inbrs & jnbrs]
            )
        yield (i, len(inbrs), 2 * weighted_triangles)


def _directed_weighted_triangles_and_degree_iter(G, nodes=None, weight="weight"):
    """
    @copyright: networkx package, clustering function. only copied to update weight functions.
    Return an iterator of
    (node, total_degree, reciprocal_degree, directed_weighted_triangles).

    Used for directed weighted clustering.
    Note that unlike `_weighted_triangles_and_degree_iter()`, this function counts
    directed triangles so does not count triangles twice.

    """
    import numpy as np

    if weight is None or G.number_of_edges() == 0:
        max_weight = 1
    else:
        max_weight = max(d.get(weight, 1) for u, v, d in G.edges(data=True))

    nodes_nbrs = ((n, G._pred[n], G._succ[n]) for n in G.nbunch_iter(nodes))

    def wt(u, v):
        return G[u][v].get(weight, 1) / max_weight

    for i, preds, succs in nodes_nbrs:
        ipreds = set(preds) - {i}
        isuccs = set(succs) - {i}

        directed_triangles = 0
        for j in ipreds:
            jpreds = set(G._pred[j]) - {j}
            jsuccs = set(G._succ[j]) - {j}
            directed_triangles += sum(
                [(wt(j, i) + wt(k, i) + wt(k, j)) / 3 for k in ipreds & jpreds]
            )
            directed_triangles += sum(
                [(wt(j, i) + wt(k, i) + wt(j, k)) / 3 for k in ipreds & jsuccs]
            )
            directed_triangles += sum(
                [(wt(j, i) + wt(i, k) + wt(k, j)) / 3 for k in isuccs & jpreds]
            )
            directed_triangles += sum(
                [(wt(j, i) + wt(i, k) + wt(j, k)) / 3 for k in isuccs & jsuccs]
            )

        for j in isuccs:
            jpreds = set(G._pred[j]) - {j}
            jsuccs = set(G._succ[j]) - {j}
            directed_triangles += sum(
                [(wt(i, j) + wt(k, i) + wt(k, j)) / 3 for k in ipreds & jpreds]
            )
            directed_triangles += sum(
                [(wt(i, j) + wt(k, i) + wt(j, k)) / 3 for k in ipreds & jsuccs]
            )
            directed_triangles += sum(
                [(wt(i, j) + wt(i, k) + wt(k, j)) / 3 for k in isuccs & jpreds]
            )
            directed_triangles += sum(
                [(wt(i, j) + wt(i, k) + wt(j, k)) / 3 for k in isuccs & jsuccs]
            )

        dtotal = len(ipreds) + len(isuccs)
        dbidirectional = len(ipreds & isuccs)
        yield (i, dtotal, dbidirectional, directed_triangles)


def modified_clustering(G, nodes=None, weight=None):
    """
    @copyright: networkx package, clustering function
    Only copied to apply arithmetic mean for edge weights instead of geometric
    """
    if G.is_directed():
        if weight is not None:
            td_iter = _directed_weighted_triangles_and_degree_iter(G, nodes, weight)
            clusterc = {
                v: 0 if t == 0 else t / ((dt * (dt - 1) - 2 * db) * 2)
                for v, dt, db, t in td_iter
            }
        else:
            pass
    else:
        # The formula 2*T/(d*(d-1)) from docs is t/(d*(d-1)) here b/c t==2*T
        if weight is not None:
            td_iter = _weighted_triangles_and_degree_iter(G, nodes, weight)
            clusterc = {v: 0 if t == 0 else t / (d * (d - 1)) for v, d, t in td_iter}
        else:
            pass
    if nodes in G:
        # Return the value of the sole entry in the dictionary.
        return clusterc[nodes]
    return clusterc
