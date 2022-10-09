import networkx as nx
import pandas as pd
from load.manipulations import update_values_in_edgelist
import logging

logging.basicConfig(
    filename="logs/graph.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    force=True,
)


def create_original_graph(edgelist_path, node_path, wrong_nodes):
    """
    Function that takes the nodes info and edgelist as input and returns a graph
    with attributes set to the edges (value) and to the nodes (sector, assets)
    for each node, and more for publicly traded, non financial companies (industry,
    liabilities, equity). For financial companies the asset value is the sum of the
    """

    edgelist = pd.read_csv(edgelist_path)
    node_info = pd.read_csv(node_path)
    edgelist = update_values_in_edgelist(edgelist, wrong_nodes)

    edgelist, node_info = remove_financials_not_in_source(edgelist, node_info)

    node_attrs = (
        node_info[node_info.sector != "Financials"]
        .set_index("name")
        .to_dict(orient="index")
    )
    source_attrs_df = (
        edgelist.groupby("source").sum().rename(columns={"value": "assets"})
    )
    # removing those firms from this dataframe who are not in financial sector
    # but filed 13f reports. They keep their initial value.
    helper = source_attrs_df.reset_index()
    omitted_firms = helper[
        helper.source.isin(node_info[node_info.sector != "Financials"].name)
    ].source
    source_attrs_df = source_attrs_df[~source_attrs_df.index.isin(omitted_firms)]

    source_attrs_df["sector"] = "Financials"
    source_attrs = source_attrs_df.to_dict(orient="index")

    g = nx.from_pandas_edgelist(
        edgelist,
        source="source",
        target="target",
        edge_attr="value",
        create_using=nx.DiGraph,
    )
    logging.debug("graph created")
    g.remove_edges_from(nx.selfloop_edges(g))
    logging.debug("self loop edges have been removed")
    nx.set_node_attributes(g, node_attrs)
    logging.debug("node attributes added for non-financial companies")
    g = remove_nodes_wo_out_edge(g)
    logging.debug("nodes with no out degre in the financial sector are removed.")
    nx.set_node_attributes(g, source_attrs)
    logging.debug("node attributes added for financial companies")

    return g


def remove_financials_not_in_source(edgelist, nodes):
    """
    Helper function that returns the edgelist and node info after removing the
    companies that are in the financial sector but has not submitted 13f filings.
    """

    names_to_remove = nodes[
        (nodes.sector == "Financials") & (~nodes.name.isin(edgelist.source))
    ].name
    nodes = nodes[~nodes.name.isin(names_to_remove)]

    edgelist = edgelist[(~edgelist.source.isin(names_to_remove))]

    return edgelist, nodes


def remove_nodes_wo_out_edge(g):
    # filtering for financial nodes that have no out edges, removing them
    total_nodes = set(g.nodes())
    nodes_with_sector = set(nx.get_node_attributes(g, "sector").keys())
    nodes_wo_sector = total_nodes - nodes_with_sector

    for node in nodes_wo_sector:
        if len(g.out_edges(node)) == 0:
            g.remove_node(node)

    return g


def remove_edges_between_financial_sector(g):
    """
    Function that removes edges between the financial sector players to create a
    bipartite graph than can be projected later.
    """

    sectors = nx.get_node_attributes(g, "sector")
    # iterating through the nodes, checking if it is in the financial sector
    for node, sector in sectors.items():
        if sector == "Financials":
            # if the node is in the financial sector, listing its out edges
            for (u, v) in g.out_edges(node):
                if g.nodes[v]["sector"] == "Financials":
                    # if the node where the edge leads is also in the financial sector
                    # decreasing the value of both nodes then deleting the edge
                    value = g[u][v]["value"]
                    # decreasing asset value for both nodes
                    g.nodes[u]["assets"] -= value
                    g.nodes[v]["assets"] -= value
                    g.remove_edge(u, v)

    return g
