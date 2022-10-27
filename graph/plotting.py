import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import networkx as nx
import pandas as pd
import seaborn as sns
import networkx as nx
import numpy as np

from .plot_helpers import (
    calculate_effect_on_other_sectors,
    count_defaults_each_round,
    calculate_cummulative_defaults,
)


def creating_node_df(G: nx.Graph) -> pd.DataFrame:
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


def plot_graph_features(G: nx.Graph, loglog=True):
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
    if loglog:
        ax.set_title("Degree distribution on a log-log scale", size=18)
    else:
        ax.set_title("Degree distribution", size=18)

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


def plot_defaults(sectors_dict, sector, method):

    if sector == "all":
        fig, axes = plt.subplots(5, 2, figsize=(20, 30))

        for i, (sec, df_list) in enumerate(sectors_dict.items()):

            if method == "rounds":
                defaulted_dict = count_defaults_each_round(df_list)
                fig.suptitle(
                    f"Number of defaulted firms from shocks on different sectors",
                    size=20,
                )
                axes.flatten()[i] = add_axes_attributes(axes.flatten()[i])

            elif method == "sectors_direct":
                defaulted_dict = calculate_effect_on_other_sectors(
                    df_list, sec, direct=True
                )
                fig.suptitle(
                    f"% of defaulted firms in each sector from shocks on different sectors \nDirect effect",
                    size=20,
                )
                axes.flatten()[i] = add_axes_attributes_sector(axes.flatten()[i])
                axes.flatten()[i].yaxis.set_major_formatter(
                    mtick.PercentFormatter(decimals=None)
                )

            elif method == "sectors_total":
                defaulted_dict = calculate_effect_on_other_sectors(
                    df_list, sec, direct=False
                )
                fig.suptitle(
                    f"% of defaulted firms in each sector from shocks on different sectors \nTotal effect",
                    size=20,
                )
                axes.flatten()[i] = add_axes_attributes_sector(axes.flatten()[i])

                axes.flatten()[i].yaxis.set_major_formatter(
                    mtick.PercentFormatter(decimals=None)
                )

            axes.flatten()[i].boxplot(defaulted_dict.values())
            axes.flatten()[i].set_xticklabels(defaulted_dict.keys(), rotation=90)
            axes.flatten()[i].set_title(f"{sec}", size=16)

        fig.tight_layout()
        fig.subplots_adjust(top=0.95)

    else:
        df_list = sectors_dict[sector]
        fig, ax = plt.subplots(figsize=(8, 5))

        if method == "rounds":
            defaulted_dict = count_defaults_each_round(df_list)
            ax = add_axes_attributes(ax)
            ax.set_title(
                f"Defaulted firms in each round from {sector} sector's shocks", size=16
            )

        elif method == "sectors_direct":
            defaulted_dict = calculate_effect_on_other_sectors(
                df_list, sector, direct=True
            )

            ax = add_axes_attributes_sector(ax)
            ax.set_title(
                f"% of defaulted firms in each sector from shocks on {sector} sector \nDirect effect"
            )
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=None))

        elif method == "sectors_total":
            defaulted_dict = calculate_effect_on_other_sectors(
                df_list, sector, direct=False
            )
            ax = add_axes_attributes_sector(ax)
            ax.set_title(
                f"% of defaulted firms in each sector from shocks on {sector} sector \nTotal effect"
            )
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=None))

        ax.boxplot(defaulted_dict.values())
        ax.set_xticklabels(defaulted_dict.keys(), rotation=90)

    return fig


def add_axes_attributes(ax):
    ax.set_ylabel("defaulted firms", size=14)
    ax.set_xlabel("default round", size=14)
    ax.tick_params(labelsize=12)

    return ax


def add_axes_attributes_sector(ax):
    ax.set_ylabel("defaulted firms", size=14)
    ax.set_xlabel("sector", size=14)
    ax.tick_params(labelsize=12)

    return ax


def plot_cummulative_defaults(sectors_dict):

    fig, ax = plt.subplots(figsize=(12, 9))

    plot_dict = calculate_cummulative_defaults(sectors_dict)

    for sector, def_list in plot_dict.items():
        ax.plot(def_list, marker="x", linestyle="--", markersize=10, label=sector)

    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))

    ax = add_axes_attributes(ax)
    ax.set_title(
        "Cummulative defaults on the network based on shocked industry", size=16
    )

    return fig
