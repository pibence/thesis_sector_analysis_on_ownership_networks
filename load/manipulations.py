import pandas as pd
import jellyfish
import itertools
import logging
from load.helpers import parse_csvs_from_folder, parse_financials_from_folder
from tqdm import tqdm

logging.basicConfig(
    filename="logs/load.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
)


def standardize_tickers(column):
    return column.apply(lambda x: x.split(".")[0])


def standardize_names(column):
    """
    Function that standardizes the names of the companies in to prepare them
    for string distance calculation.
    """

    corp_name_list = [
        r"\binc\b",
        "inc$",
        "company",
        "companies",
        "corporation",
        r"\bcorp\b",
        "corp$",
        r"\bco\b",
        "co$",
        "ltd",
        "llc",
        r"\bthe\b",
        "the$",
        "solutions",
        r"\bsolut\b",
        "solut$",
        "plc",
        "adrs",
        r"\badr\b",
        r"\band\b",
        "adr$",
        "mgmt",
        "management",
        "asset",
        r"\bcom\b",
        "com$",
        "class a",
        "class b",
        "class c",
        "class d",
        "cl a",
        "cl b",
        "cl c",
        "cl d",
        "holdings",
        "holding",
        "group",
        "pharmaceuticals",
        "therapeutics",
        "technologies",
        "technology",
        "series a",
        "series b",
        "pharma",
        "\(.*?\)",
    ]
    spec_char_dict = {",": "", ".": " ", "&": " ", "/": "", "-": ""}

    column = column.astype(str)
    ret_col = column.apply(lambda x: x.lower())
    for char, value in spec_char_dict.items():
        ret_col = ret_col.str.replace(char, value, regex=False)

    ret_col = ret_col.apply(lambda x: " ".join(x.split()))

    for name in corp_name_list:
        ret_col = ret_col.str.replace(name, "", regex=True)

    ret_col = ret_col.apply(lambda x: x.strip())

    return ret_col


def create_standardized_edgelist_node_list(
    financials_folder, edgelist_folder, node_temp_path, edgelist_temp_path
):
    """
    Function that joins the chunks for the nodes and edges and standardizes their
    names, then writes them to a temporary folder.
    """

    edgelist = parse_csvs_from_folder(edgelist_folder)
    financials = parse_financials_from_folder(financials_folder)
    logging.info("financials data and edgelist chunks are read.")

    financials["company_name"] = standardize_names(financials["company_name"])
    financials["identifier"] = standardize_tickers(financials["identifier"])
    edgelist["source"] = standardize_names(edgelist["source"])
    edgelist["target"] = standardize_names(edgelist["target"])
    logging.info("name standardization finished.")

    financials.to_csv(node_temp_path, index=False)
    edgelist.to_csv(edgelist_temp_path, index=False)
    logging.info("Standardized egdelist and node info is written to working directory.")

    return 1


def create_similarity_csv(node_temp_path, edgelist_temp_path, sim_path):
    """
    Function that calculates the Jaro-Winkler similarity for each possible
    combinations of the names in two different sources, then writes the similarity
    dataframe to a csv file.
    """

    financials = pd.read_csv(node_temp_path)
    edgelist = pd.read_csv(edgelist_temp_path)

    # getting unique values for sources in edgelist
    unique_target = edgelist.groupby("target").count().reset_index()[["target"]]

    sim_df = calculate_similarity_df(financials.company_name, unique_target.target)
    sim_df.to_csv(sim_path, index=False)
    logging.info(
        f"similarity measures are calculated for the names in two different sources, data is written to {sim_path}"
    )

    return 1


def create_node_info_and_filtered_edgelist(
    sim_path, threshold, node_temp_path, node_path, edgelist_temp_path, edgelist_path
):
    """
    Function that takes the temporary edgelist and node list and similarity
    file as input, filters the similarity file based on a threshold,
    changes the names in the edgelists and filters both edgelist and node list
    to contain only data from the US market that are in both files.
    """

    sim_df = pd.read_csv(sim_path)
    financials = pd.read_csv(node_temp_path)
    edgelist = pd.read_csv(edgelist_temp_path)

    filt_sim = sim_df[sim_df.value > threshold]

    edgelist = replace_names_in_edgelist(edgelist, filt_sim)
    logging.info("names are substituted in the edgelist")

    # getting unique values for targets in new edgelist
    unique_target = edgelist.groupby("target").count().reset_index()[["target"]]

    node_data = financials[financials.company_name.isin(unique_target.target)][
        [
            "identifier",
            "company_name",
            "gics_sector_name",
            "gics_industry_name",
            "total_assets",
            "total_liabilities",
            "total_equity",
        ]
    ]
    node_data.columns = [
        "ticker",
        "name",
        "sector",
        "industry",
        "assets",
        "liabilities",
        "equity",
    ]
    node_data.to_csv(node_path, index=False)
    logging.info(f"node info csv is written to file at {node_path}")

    edgelist_filt = edgelist[edgelist.target.isin(node_data.name)]
    edgelist_filt.to_csv(edgelist_path, index=False)
    logging.info(f"filtered final edgelist is written to file at {edgelist_path}")

    return 1


def calculate_similarity_df(column1, column2):
    """
    Function that calculates the string similarity between the two names.
    Returns a dataframe with similarity measures.
    """

    combinations = itertools.product(column1, column2)

    name_list = []
    for com in combinations:
        name_list.append(
            [com[0], com[1], jellyfish.jaro_winkler_similarity(com[0], com[1])]
        )

    sim_df = pd.DataFrame(name_list, columns=["company_name", "target", "value"])
    return sim_df


def replace_names_in_edgelist(edgelist, map_df):
    """
    Function to replace names with their similar mapping in the edgelist.
    """

    map_dict = dict(zip(map_df.target, map_df.company_name))
    edgelist.loc[edgelist.source.isin(map_dict.keys()), "source"] = edgelist[
        edgelist.source.isin(map_dict.keys())
    ]["source"].map(map_dict, na_action="ignore")

    edgelist.loc[edgelist.target.isin(map_dict.keys()), "target"] = edgelist[
        edgelist.target.isin(map_dict.keys())
    ]["target"].map(map_dict, na_action="ignore")

    return edgelist
