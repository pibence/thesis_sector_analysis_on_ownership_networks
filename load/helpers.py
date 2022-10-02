import yaml
import os
import pandas as pd
import logging


def parse_yaml(config):
    with open(config, "r") as stream:
        try:
            ret_dict = yaml.load(stream, Loader=yaml.Loader)
        except yaml.YAMLError as exc:
            print(exc)
    return ret_dict


def parse_csvs_from_folder(folder_path):
    files = os.listdir(folder_path)

    df_list = []
    for file in files:
        fl = pd.read_csv(f"{folder_path}/{file}")
        df_list.append(fl)

    ret_df = pd.concat(df_list)
    ret_df.columns = ret_df.columns.str.lower()
    return ret_df    