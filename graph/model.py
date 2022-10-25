import networkx as nx
import numpy as np
import pandas as pd
from typing import Union
import logging
import os
import csv
from multiprocessing import Pool
from functools import partial
from datetime import datetime
from time import time


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

    np.random.seed()
    shock_list = (np.random.pareto(alpha, len(node_list)) + 1) * scale

    for i, n in enumerate(node_list):
        g.nodes[n]["assets"] *= np.exp(-shock_list[i])
        g.nodes[n]["equity"] = g.nodes[n]["assets"] - g.nodes[n]["liabilities"]

        if g.nodes[n]["equity"] < g.nodes[n]["equity"] * default_threshold:
            g.nodes[n]["default_round"] = 1

    return g


def simulate_one_shock_from_pareto(
    g: nx.Graph,
    node_list: str,
    alpha: float,
    scale: float,
    default_threshold: float,
    sector_path: str,
    i: int,
):
    """Function that calls the shock generation and the propagation for the
    given set of nodes. It also saves the result of the simulation to a given folder."""

    h = g.copy()
    nx.set_node_attributes(h, None, "default_round")
    nx.set_node_attributes(h, dict(h.nodes(data="equity")), "equity_orig")

    g_shocked = generate_shock_from_pareto(
        h, node_list, alpha, scale, default_threshold
    )

    g_final = propagate_default(g_shocked, default_threshold)

    save_graph_to_feather(g_final, sector_path, i + 1)
    g_final = None
    g_shocked = None
    return 1


def simulate_shocks_from_pareto(
    g: nx.Graph,
    sector: str,
    alpha: float,
    scale: float,
    default_threshold: float,
    repeat: int,
    sector_path: str,
):
    """
    Main function that generates shock for one sector and then propagates it
    through the whole graph. The function applies Monte Carlo simulation and every
    run is saved to a folder in the format of feather files containing the
    dataframe from the updated graph with every node attribute.
    """

    node_list = get_sector_nodes(g, sector)
    pool = Pool(8)
    func = partial(
        simulate_one_shock_from_pareto,
        g,
        node_list,
        alpha,
        scale,
        default_threshold,
        sector_path,
    )
    pool.map(func, range(repeat))
    """
    for i in range(repeat):
        simulate_one_shock_from_pareto(
            g, node_list, alpha, scale, default_threshold, sector_path, i
        )
    """
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
    """Currently not in use."""
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
                "Sector",
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


def simulate_shock_for_multiple_sectors(
    g: nx.Graph,
    alpha: float,
    scale: float,
    default_threshold: float,
    repeat: int,
    simulation_path: str,
    sectors_list: str,
):
    """
    Main function that runs the monte carlo simulation for multiple given sectors.
    For each simulation a new folder is created with the actual date and within them
    each sector have their own folder. The metadata about the run (shock parameters,
    default threshold, number of iterations, path, etc.) are also saved to a
    metadata file.
    """

    dir = datetime.now().strftime("%Y_%m_%d_%H%M%S")
    path = f"{simulation_path}{dir}"
    os.mkdir(path)
    logging.debug(
        f"folder for the current run is created in the simulations folder under the name {dir}"
    )

    start_time = time()

    for sector in sectors_list:
        sector_path = f"{path}/{sector}"
        os.mkdir(sector_path)

        logging.debug(
            f"folder for {sector} sector is created in the current run folder."
        )
        simulate_shocks_from_pareto(
            g, sector, alpha, scale, default_threshold, repeat, sector_path
        )
        logging.info(f"Simulation for {sector} sector is finished.")

    end_time = time()
    runtime = end_time - start_time

    metadata = {
        "date_of_run": dir,
        "shock_distribution": "pareto",
        "alpha": alpha,
        "scale_param": scale,
        "default_threshold": default_threshold,
        "no_of_iterations": repeat,
        "results_path": path,
        "time elapsed": runtime,
    }

    metadata_df = pd.DataFrame.from_dict(metadata, orient="index")
    metadata_df.to_csv(f"{path}/metadata.csv", header=False)
    logging.debug(
        f"shock simulation is finished, metadata is saved. Elapsed time: {runtime} seconds"
    )

    return 1
