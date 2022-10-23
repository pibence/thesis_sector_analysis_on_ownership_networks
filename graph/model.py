import networkx as nx
import numpy as np
import pandas as pd
from typing import Union
import logging
import os
import csv
from datetime import datetime

from .describe import get_sector_nodes


logging.basicConfig(
    filename="logs/shock_simulation.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    force=True,
)


def propagate_default(g, default_threshold):
    """
    Function that screens the whole graph and propagates the shock from
    the defaulted nodes to the neighboring nodes. The iteration goes until there is
    a new defaulter firm in an iteration. The function returns an updated graph
    with the round of default and updated asset, equity values.
    """

    round = 1
    new_defaulter = True

    while new_defaulter:
        new_defaulter = False

        default = [
            node for node in g.nodes() if g.nodes[node]["default_round"] == round
        ]

        round += 1

        for n in default:

            # calculating the sum of weights where the edge leads to a non-defaulted node
            weight_sum = 0

            for neighbor in g.neighbors(n):
                if not g.nodes[neighbor]["default_round"]:
                    weight_sum += g[n][neighbor]["weight"]

            if weight_sum == 0:
                continue
            else:
                for neighbor in g.neighbors(n):
                    if not g.nodes[neighbor]["default_round"]:
                        proportion = g[n][neighbor]["weight"] / weight_sum
                        g.nodes[neighbor]["assets"] -= (
                            g.nodes[n]["equity_orig"] * proportion
                        )
                        g.nodes[neighbor]["equity"] -= (
                            g.nodes[n]["equity_orig"] * proportion
                        )

                        if (
                            g.nodes[neighbor]["equity"]
                            < g.nodes[neighbor]["equity"] * default_threshold
                        ):
                            new_defaulter = True
                            g.nodes[neighbor]["default_round"] = round

    return g


def generate_shock_from_pareto(
    g: nx.Graph,
    node_list: Union[list, str],
    alpha: float,
    scale: float,
    default_threshold: float,
):
    """
    The function generates shocks on one or multiple nodes from pareto distribution.
    The loss is calculated, the asset and equity values are updated and if equity
    value falls below the given threshold, the default is indicated. It returns
    the updated graph.
    """

    if isinstance(node_list, str):
        node_list = [node_list]

    shock_list = (np.random.pareto(alpha, len(node_list)) + 1) * scale

    for i, n in enumerate(node_list):
        g.nodes[n]["assets"] *= np.exp(-shock_list[i])
        g.nodes[n]["equity"] = g.nodes[n]["assets"] - g.nodes[n]["liabilities"]

        if g.nodes[n]["equity"] < g.nodes[n]["equity"] * default_threshold:
            g.nodes[n]["default_round"] = 1

    return g


def simulate_shocks_from_pareto(
    g: nx.Graph,
    sector: str,
    alpha: float,
    scale: float,
    default_threshold: float,
    repeat: int,
    simulation_path: str,
    metadata_path: str,
):
    """
    Main function that generates shock for one sector and then propagates it
    through the whole graph. The function applies Monte Carlo simulation and every
    run is saved to a folder in the format of feather files containing the
    dataframe from the updated graph with every node attribute. The metadata
    about the run (shock parameters, default threshold, number of iterations, path, etc.)
    are also appended to a metadata file.
    """

    dir = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    path = f"{simulation_path}{dir}"
    os.mkdir(path)
    logging.debug(
        f"folder for the current run is created in the simulations folder under the name {dir}"
    )
    node_list = get_sector_nodes(g, sector)
    for i in range(0, repeat):
        h = g.copy()
        nx.set_node_attributes(h, None, "default_round")
        nx.set_node_attributes(h, dict(h.nodes(data="equity")), "equity_orig")
        g_shocked = generate_shock_from_pareto(
            h, node_list, alpha, scale, default_threshold
        )
        logging.debug(f"{i+1}. iteration: initial shock is generated")

        g_final = propagate_default(g_shocked, default_threshold)
        logging.debug(f"{i+1}. iteration: initial shock is propagated")

        save_graph_to_feather(g_final, path, i + 1)
        logging.debug(f"{i+1}. iteration: graph is saved to feather")

    append_simulation_metadata_to_csv(
        metadata_path,
        sector,
        node_list,
        "pareto",
        alpha,
        scale,
        default_threshold,
        repeat,
        dir,
    )
    logging.debug(f"metadata is saved for {sector} sector, run {dir}")

    return 1


def save_graph_to_feather(g, path, iteration):

    df = pd.DataFrame.from_dict(dict(g.nodes(data=True)), orient="index")
    df = df.reset_index(drop=True)

    df.to_feather(f"{path}/{iteration}.feather", compression="zstd")


def append_simulation_metadata_to_csv(
    path,
    sector,
    shocked_nodes,
    shock_dist,
    alpha,
    scale_param,
    default_threshold,
    no_of_iterations,
    folder_name,
):
    new_line = [
        sector,
        len(shocked_nodes),
        shock_dist,
        alpha,
        scale_param,
        default_threshold,
        no_of_iterations,
        folder_name,
    ]

    if os.path.isfile(path):
        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(new_line)
    else:
        with open(path, "a", newline="") as f:
            writer = csv.writer(f)
            header = [
                "shocked_nodes",
                "shock_dist",
                "alpha",
                "scale_param",
                "default_threshold",
                "no_of_iterations",
                "folder_name",
            ]
            writer.writerow(header)
            writer.writerow(new_line)


def create_shock_for_every_sector(
    g: nx.Graph,
    alpha: float,
    scale: float,
    default_threshold: float,
    repeat: int,
    simulation_path: str,
    metadata_path: str,
    sectors_list: str,
):
    """
    Main function that runs the monte carlo simulation for each sector.
    """

    for sector in sectors_list:
        simulate_shocks_from_pareto(
            g,
            sector,
            alpha,
            scale,
            default_threshold,
            repeat,
            simulation_path,
            metadata_path,
        )
    return 1
