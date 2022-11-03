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


def analyze_sectors(g, sectors):
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
        ret_dict["sector_clustering_coefficient"] = calculate_clustering_coeff(
            s, sector_nodes, "wight"
        )
        ret_dict["avg_clustering_coefficient"] = calculate_clustering_coeff(
            h, sector_nodes, "wight"
        )
        logging.debug(f"Clustering coefficients for {sector} is added.")

        equity_level = []
        edges_from_sector = 0
        edges_within_sector = 0

        for n in s.nodes():
            for neighbor in h.neighbors(n):
                if neighbor not in s:
                    edges_from_sector += 1
                else:
                    edges_within_sector += 1

            equity_level.append(s.nodes[n]["equity"] / s.nodes[n]["assets"])

        ret_dict["edge_ratio"] = edges_within_sector / (
            edges_within_sector + edges_from_sector
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
