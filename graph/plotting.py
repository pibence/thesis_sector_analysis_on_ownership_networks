import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import seaborn as sns


def creating_node_df(G: nx.graph) -> pd.DataFrame:
    """
    This function takes the G as input and returns a dataframe
    containing information on the nodes such as degree.
    """

    node_df = pd.DataFrame(
        dict(
            degree=dict(G.degree()),
            assets=dict(nx.get_node_attributes(G, "assets")),
        )
    )

    return node_df


def plot_graph_features(G: nx.graph, loglog=True):
    """
    The function takes the G as input and returns the degree distribution
    plot.
    """

    # getting node_df
    plot_df = creating_node_df(G)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.scatter(
        x=plot_df.degree.value_counts().index,
        y=plot_df.degree.value_counts(),
        marker="x",
        color="b",
    )
    # setting design
    ax.set_xlabel("degree", size=14)
    ax.set_ylabel("frequency", size=14)
    ax.set_title("Degree distribution on a log-log scale", size=18)
    ax.tick_params(labelsize=12)

    if loglog == True:
        ax.set_yscale("log")
        ax.set_xscale("log")

    return fig


def plot_asset_value_dist(G):
    plot_df = creating_node_df(G)

    fig, ax = plt.subplots(figsize=(8, 5))

    sns.histplot(data=plot_df[["assets"]], x="assets", ax=ax)
    # setting design
    ax.set_ylabel("frequency", size=14)
    ax.set_xlabel("assets (in thousand $)", size=14)
    ax.set_title("Asset distribution", size=18)

    return fig
