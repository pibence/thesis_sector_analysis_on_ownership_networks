from tempfile import TemporaryFile
import pandas as pd
import networkx as nx
import os
import numpy as np


def load_simulation_for_sector(sector_path):
    """
    Helper function to parse every simulation file to a list of dataframes
    """

    df_list = []
    for file in os.listdir(sector_path):
        df_list.append(pd.read_feather(f"{sector_path}/{file}"))

    return df_list


def load_simulation_for_all_sectors(simulations_path, run_folder, sector_list):
    """
    Function that returns a dictionary where every key is a sector and the values
    are lists of dataframes.
    """

    run_path = f"{simulations_path}/{run_folder}"

    folders = os.listdir(run_path)
    sectors = [f for f in folders if f in sector_list]

    sectors_dict = {}

    for sector in sectors:
        sector_path = f"{run_path}/{sector}"
        sectors_dict[sector] = load_simulation_for_sector(sector_path)

    return sectors_dict


def count_defaults_each_round(df_list):
    """
    Helper function that creates a dictionary with the defaulted firms in each round.
    The key of the dictionary is the default round and the valueas are lists containing
    information on each run.
    """

    result_dict = {}
    for df in df_list:

        # res = df.groupby("default_round").count()['name']
        res = df[~pd.isna(df.default_round)].groupby("default_round").count()["label"]
        for i in range(0, len(res)):
            try:
                result_dict[res.index[i]].append(res.iloc[i])
            except KeyError:
                result_dict[res.index[i]] = []
                result_dict[res.index[i]].append(res.iloc[i])

    return result_dict


def calculate_cummulative_defaults(sectors_dict):
    """
    Helper function that counts the cummulative defaults in each round for each
    shocked sector.
    """

    interim_dict = {}
    # calculating no of defaulted firms and appending their mean to a dictionary
    # where the keys are the sectors
    for (sec, df_list) in sectors_dict.items():

        defaulted_dict = count_defaults_each_round(df_list)
        interim_dict[sec] = [np.mean(value) for value in defaulted_dict.values()]

    # calculating highest default round
    len_longest_list = len(max(interim_dict.values(), key=lambda x: len(x)))

    # adding zeros to rounds where there were no defaults to have all lists
    # with the same length
    plot_dict = {}
    for sec, def_list in interim_dict.items():

        extra_zeros = len_longest_list - len(def_list)
        def_list.extend([0] * extra_zeros)

        # creating cumulative sum of defaults
        plot_dict[sec] = np.cumsum(def_list)

    return plot_dict


def calculate_effect_on_other_sectors(df_list, shocked_sector, direct=False):

    """
    Function that calculates the direct effect on the other sectors from one
    shocked sector. The returned dictionary contains the proportion of the nodes
    from one sector that fails. If direct is true, only the fails in the second
    round are counted.
    """

    result_dict = {}
    for df in df_list:

        sector_count = (
            df[df.sector != shocked_sector].groupby("sector").count()["label"]
        )

        if direct:
            res = (
                df[(df.default_round == 2) & (df.sector != shocked_sector)]
                .groupby("sector")
                .count()["label"]
            )
        else:
            res = (
                df[(~pd.isna(df.default_round)) & (df.sector != shocked_sector)]
                .groupby("sector")
                .count()["label"]
            )

        res = res / sector_count * 100  # values will be displayed as percentages
        for i in range(0, len(res)):
            try:
                result_dict[res.index[i]].append(res.iloc[i])
            except KeyError:
                result_dict[res.index[i]] = []
                result_dict[res.index[i]].append(res.iloc[i])

    return result_dict


def calculate_effect_from_other_sectors(sectors_dict):
    """
    Helper function to calculate the effect of each sectors shock on one sector.
    The returned value is a nested dictionary thats keys are the sectors that
    we want to get info on how they are effected by different sectors' shocks and
    their values are dictionaries where the key is the sector that is shocked
    and the value is a list which contains percentages of defaulted firms in the
    examined sector.

    Example: result_dict["Information Technologies"]["Health Care"] tells us
    the effect on the IT sector of the shocks coming from the situation where
    the initial shock hits the health care sector. The result is a dictionary
    of the percentages of IT sector companies failed in each iteration.
    """

    result_dict = {}

    for shocked_sector, df_list in sectors_dict.items():

        # calculating the effects of shocking the 'shocked sector'
        interim_dict = calculate_effect_on_other_sectors(df_list, shocked_sector, False)

        # saving the results of the shock on each sector to an inner dictionary where
        # the key is the shocked sector
        for sec, def_list in interim_dict.items():
            try:
                result_dict[sec][shocked_sector] = def_list
            except:
                result_dict[sec] = {}
                result_dict[sec][shocked_sector] = def_list

    return result_dict


def sort_dictionary_by_mean_of_list(d):
    """
    Helper function that orders the dictionary based on the mean of the list that
    is in the value field.
    """
    sorted_keys = sorted(d, key=lambda x: np.mean(d[x]), reverse=True)
    ret_dict = {key: d[key] for key in sorted_keys}

    return ret_dict