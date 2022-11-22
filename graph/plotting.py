import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import networkx as nx
import pandas as pd
import seaborn as sns
import networkx as nx

from .plot_helpers import (
    calculate_effect_on_other_sectors,
    count_defaults_each_round,
    calculate_cummulative_defaults,
    calculate_effect_from_other_sectors,
    sort_dictionary_by_mean_of_list,
    calculate_pairwise_effect_for_heatmap,
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


def plot_graph_features(G: nx.Graph, log=None):
    """
    The function takes the G as input and returns the degree distribution
    plot.
    """

    # getting node_df
    plot_df = creating_node_df(G)

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.scatter(
        x=plot_df.degree.value_counts().index,
        y=plot_df.degree.value_counts(),
        marker="x",
        color="darkred",
    )
    # setting design
    ax.set_xlabel("Degree", size=18, fontweight="bold")
    ax.set_ylabel("Frequency", size=18, fontweight="bold")

    ax.set_title("Degree distribution", size=20, pad=30, fontweight="bold")

    ax.tick_params(labelsize=16)
    ax.grid(axis="y", linestyle="--")

    if log == "xy":
        ax.set_yscale("log")
        ax.set_xscale("log")

        ax.set_xlabel("Degree (log)", size=18, fontweight="bold")
        ax.set_ylabel("Frequency (log)", size=18, fontweight="bold")
    elif log == "x":
        ax.set_xscale("log")
        ax.set_xlabel("Degree (log)", size=18, fontweight="bold")

    return fig


def plot_asset_value_dist(G, log=None):
    plot_df = creating_node_df(G)

    fig, ax = plt.subplots(figsize=(8, 5))

    sns.histplot(data=plot_df[["assets"]], x="assets", ax=ax)
    # setting design
    ax.set_ylabel("Frequency", size=14)
    ax.set_xlabel("Assets (in thousand $)", size=14)
    ax.set_title("Asset value distribution", size=18)
    ax.grid(axis="y", linestyle="--")

    if log == "xy":
        ax.set_yscale("log")
        ax.set_xscale("log")

        ax.set_ylabel("Frequency (log)", size=14)
        ax.set_xlabel("Assets (log)", size=14)
    elif log == "x":
        ax.set_xscale("log")

        ax.set_xlabel("assets (log)", size=14)

    return fig


def plot_node_weighted_er_connection(sector_df):

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        data=sector_df, x="nodes", y="weighted_edge_ratio", hue="sector", s=150, ax=ax
    )
    sns.regplot(
        data=sector_df,
        x="nodes",
        y="weighted_edge_ratio",
        scatter=False,
        ci=None,
        ax=ax,
        line_kws={"color": "darkred"},
    )
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1, 1),
        markerscale=2,
        fontsize=12,
    )
    ax.grid()
    ax.set_xlabel("Nodes", size=16, fontweight="bold")
    ax.set_ylabel("Weighted edge ratio", size=16, fontweight="bold")
    ax.set_title(
        f"Connection between node count and weighted edge ratio",
        size=18,
        pad=30,
        fontweight="bold",
    )
    ax.tick_params(labelsize=12)

    return fig


def plot_sector_network_info(sector_df, x, y, siz):
    """
    The function plots the reuslts of the sector analysis with the desired x and
    y axes, where the size of the points contain extra information. Every sector
    is marked with a different color.
    """

    fig, ax = plt.subplots(figsize=(10, 6))
    sector_df = sector_df.reset_index()
    sns.scatterplot(
        data=sector_df,
        x=x,
        y=y,
        size=siz,
        sizes=(300, 900),
        hue="sector",
        markers="O",
        ax=ax,
    )
    handles, labels = ax.get_legend_handles_labels()

    labels[0] = "-----SECTORS----"
    labels[11] = "-----NODE COUNT-----"
    for h in handles[12:]:
        sizes = [s / 10 for s in h.get_sizes()]
        h.set_sizes(sizes)

    ax.legend(
        handles,
        labels,
        loc="upper left",
        bbox_to_anchor=(1, 1),
        markerscale=2,
        fontsize=12,
    )
    x = x.replace("_", " ")
    y = y.replace("_", " ")
    siz = siz.replace("_", " ")
    ax.grid()
    ax.set_xlabel(x.capitalize(), size=16, fontweight="bold")
    ax.set_ylabel(y.capitalize(), size=16, fontweight="bold")
    ax.set_title(
        f"Sector information in the \n{y}, {x}, {siz} dimensions",
        size=18,
        pad=30,
        fontweight="bold",
    )
    ax.tick_params(labelsize=14)

    return fig


def plot_defaults(sectors_dict, sector, method):
    """
    General function that plots
    a) effects from one shocked sector on one plot
    b) effects from each shocked sector on subplots.
    The function has the following methods:
    - rounds: This parameter plots the defaulted firms in each round based on the
    shock resulting from one given industry.
    - sectors_total:
    - sectors_direct:

    """

    if sector == "all":
        fig, axes = plt.subplots(5, 2, figsize=(20, 30))

        for i, (sec, df_list) in enumerate(sectors_dict.items()):

            if method == "rounds":
                defaulted_df = count_defaults_each_round(df_list, percent=True)
                fig.suptitle(
                    f"Percentage of defaulted firms from shocks on different sectors",
                    size=20,
                )
                axes.flatten()[i].boxplot(defaulted_df)
                axes.flatten()[i] = add_axes_attributes(axes.flatten()[i])

            elif method == "sectors_direct":
                defaulted_dict = calculate_effect_on_other_sectors(
                    df_list, sec, direct=True
                )
                fig.suptitle(
                    f"Percentage of defaulted firms in each sector from shocks on different sectors \nDirect effect",
                    size=20,
                )
                axes.flatten()[i].boxplot(defaulted_dict.values())
                axes.flatten()[i].set_xticklabels(defaulted_dict.keys(), rotation=90)

                axes.flatten()[i] = add_axes_attributes_sector(axes.flatten()[i])

            elif method == "sectors_total":
                defaulted_dict = calculate_effect_on_other_sectors(
                    df_list, sec, direct=False
                )
                fig.suptitle(
                    f"Percentage of defaulted firms in each sector from shocks on different sectors \nTotal effect",
                    size=20,
                )
                axes.flatten()[i].boxplot(defaulted_dict.values())
                axes.flatten()[i].set_xticklabels(defaulted_dict.keys(), rotation=90)

                axes.flatten()[i] = add_axes_attributes_sector(axes.flatten()[i])

            axes.flatten()[i].yaxis.set_major_formatter(
                mtick.PercentFormatter(decimals=0)
            )
            axes.flatten()[i].set_title(f"{sec}", size=16)

        fig.tight_layout()
        fig.subplots_adjust(top=0.95)

    else:
        df_list = sectors_dict[sector]
        fig, ax = plt.subplots(figsize=(12, 9))

        if method == "rounds":
            defaulted_df = count_defaults_each_round(df_list, percent=True)
            ax.boxplot(defaulted_df)
            ax = add_axes_attributes(ax)
            ax.set_title(
                f"Defaulted firms in each round from {sector} sector's shocks", size=16
            )

        elif method == "sectors_direct":
            defaulted_dict = calculate_effect_on_other_sectors(
                df_list, sector, direct=True
            )
            ax.boxplot(
                defaulted_dict.values(),
                meanline=True,
                showmeans=True,
                meanprops=dict(linewidth=2.5),
                medianprops=dict(linewidth=2.5),
            )
            ax.set_xticklabels(defaulted_dict.keys(), rotation=45)

            ax = add_axes_attributes_sector(ax)
            ax.set_title(
                f"Percentage of defaulted firms in each sector from shocks on {sector} sector \nDirect effect"
            )

        elif method == "sectors_total":
            defaulted_dict = calculate_effect_on_other_sectors(
                df_list, sector, direct=False
            )
            bp = ax.boxplot(
                defaulted_dict.values(),
                meanline=True,
                showmeans=True,
                meanprops=dict(linewidth=2.5),
                medianprops=dict(linewidth=2.5, color="darkred"),
            )
            ax.set_xticklabels(defaulted_dict.keys(), rotation=45, ha="right")

            ax = add_axes_attributes_boxplot(ax)
            ax.set_title(
                f"Percentage of defaulted firms in each sector",
                fontweight="bold",
                size=22,
                pad=30,
            )
            ax.legend(
                [bp["medians"][0], bp["means"][0]], ["median", "mean"], fontsize=14
            )
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))

    return fig


def add_axes_attributes(ax):
    ax.set_ylabel("Percentage of defaulted firms", size=16, fontweight="bold")
    ax.set_xlabel("Iteration round", size=16, fontweight="bold")
    ax.tick_params(labelsize=12)
    ax.grid(axis="y", linestyle="--")

    return ax


def add_axes_attributes_cummplot(ax):
    ax.set_ylabel("Percentage of defaulted firms", size=20, fontweight="bold")
    ax.set_xlabel("Iteration round", size=20, fontweight="bold")
    ax.tick_params(labelsize=20)
    ax.grid(axis="y", linestyle="--")

    return ax


def add_axes_attributes_boxplot(ax):
    ax.set_ylabel("Percentage of defaulted firms", size=20, fontweight="bold")
    ax.set_xlabel("Sector", size=20, fontweight="bold")
    ax.tick_params(labelsize=20)
    ax.grid(axis="y", linestyle="--")

    return ax


def add_axes_attributes_sector(ax):
    ax.set_ylabel("Percentage of defaulted firms", size=16, fontweight="bold")
    ax.set_xlabel("Sector", size=16, fontweight="bold")
    ax.tick_params(labelsize=16)
    ax.grid(axis="y", linestyle="--")

    return ax


def plot_cummulative_defaults(sectors_dict):

    fig, ax = plt.subplots(figsize=(12, 9))

    plot_dict = calculate_cummulative_defaults(sectors_dict)

    for sector, def_dict in plot_dict.items():
        ax.plot(
            def_dict.keys(),
            def_dict.values(),
            marker="x",
            linestyle="--",
            linewidth=3,
            markersize=14,
            label=sector,
        )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        fancybox=True,
        ncol=3,
        fontsize=20,
    )
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=None))

    ax = add_axes_attributes_cummplot(ax)
    ax.set_title(
        "Cummulative defaults on the network\nbased on shocked industry",
        size=22,
        pad=30,
        fontweight="bold",
    )

    return fig


def plot_effect_on_sectors_from_other_sectors(sectors_dict, sectors="all"):
    """
    This function returns a plot where each subplot contains information on
    how one given sector(one sublot) is effected from shocks in other sectors(x axis).
    On the y axis the percentages of defaulted firms in the given sector are displayed.
    """

    result_dict = calculate_effect_from_other_sectors(sectors_dict)

    if sectors == "all":
        fig, axes = plt.subplots(5, 2, figsize=(20, 30))

        for i, (sec, def_dict) in enumerate(result_dict.items()):
            def_dict = sort_dictionary_by_mean_of_list(def_dict)

            axes.flatten()[i].boxplot(def_dict.values())

            axes.flatten()[i].set_xticklabels(def_dict.keys(), rotation=45)
            axes.flatten()[i] = add_axes_attributes_sector(axes.flatten()[i])
            axes.flatten()[i].set_title(f"{sec}", size=16)
            axes.flatten()[i].yaxis.set_major_formatter(
                mtick.PercentFormatter(decimals=None)
            )

        fig.suptitle(
            f"Most infulential sectors on one sector based on % of defaulted firms",
            size=20,
        )
        fig.tight_layout()
        fig.subplots_adjust(top=0.95)

    return fig


def plot_pairwise_effect(sectors_dict, include_self=False):

    plot_matrix = calculate_pairwise_effect_for_heatmap(
        sectors_dict, include_self=include_self
    )

    fig, ax = plt.subplots(figsize=(12, 9))

    sector_list = sorted(list(sectors_dict.keys()))
    cmap = sns.cm.rocket_r

    sns.heatmap(plot_matrix, ax=ax, cmap=cmap)
    ax.set_xticklabels(sector_list, rotation=45, ha="right", fontsize=20)
    ax.set_yticklabels(sector_list, fontsize=20, rotation=0)

    ax.set_xlabel("Shocked sector", size=20, fontweight="bold")
    ax.set_ylabel("Target sector", size=20, fontweight="bold")

    ax.set_title(
        "Cummulative defaults in each sector\nbased on shocked industry",
        size=22,
        pad=30,
        fontweight="bold",
    )

    cax = ax.figure.axes[-1]
    cax.tick_params(labelsize=22)
    cax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))

    return fig
