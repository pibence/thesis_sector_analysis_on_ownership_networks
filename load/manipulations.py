import pandas as pd
import jellyfish
import itertools
import logging
from load.helpers import parse_csvs_from_folder, parse_financials_from_folder

logging.basicConfig(
    filename="logs/load.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
)


def standardize_tickers(column):

    ret_col = ret_col.apply(lambda x: x.split(".")[0])

    return ret_col


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
    spec_char_dict: {",": "", ".": " ", "&": " ", "/": "", "-": ""}

    column = column.astype(str)
    ret_col = column.apply(lambda x: x.lower())
    for char, value in spec_char_dict.items():
        ret_col = ret_col.str.replace(char, value, regex=False)

    ret_col = ret_col.apply(lambda x: " ".join(x.split()))

    for name in corp_name_list:
        ret_col = ret_col.str.replace(name, "", regex=True)

    ret_col = ret_col.apply(lambda x: x.strip())

    return ret_col


def create_node_info_and_filtered_edgelist(
    financials_folder, edgelist_folder, threshold, node_info_path, edgelist_path
):
    """
    Function to find the tickers and industries for all companies in the edgelist.
    It also narrows down the scope of companies to the US-based ones by joining
    the industries file on the edgelist source. For the company names it calculates
    string similirity measure (Jaro-Winkler) and joins on them above a certain
    threshold.
    """
    
    edgelist = parse_csvs_from_folder(edgelist_folder)
    financials = parse_financials_from_folder(financials_folder)
    logging.info("financials data and edgelist chunks are read.")

    financials["company_name"] = standardize_names(financials["company_name"])
    financials["identifier"] = standardize_tickers(financials["identifier"])
    edgelist["source"] = standardize_names(edgelist["source"])
    edgelist["target"] = standardize_names(edgelist["target"])
    logging.info("name standardization finished.")

    # getting unique values for sources in edgelist
    unique_target = edgelist.groupby("target").count().reset_index()[["target"]]

    sim_df = calculate_similarity_df(financials.company_name, unique_target.target)
    logging.info(
        "similarity measures are calculated for the names in two different sourcest."
    )
    filt_sim = sim_df[sim_df.value > threshold]

    edgelist = replace_names_in_edgelist(edgelist, filt_sim)
    logging.info("names are substituted in the edgelist")

    # getting unique values for sources in new edgelist
    unique_source = edgelist.groupby("source").count().reset_index()[["source"]]

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
    node_data.to_csv(node_info_path, index=False)
    logging.info(f"node info csv is written to file at {node_info_path}")

    edgelist_filt = edgelist[edgelist.target.isin(node_data.name)]
    edgelist_filt.to_csv(edgelist_path, index=False)
    logging.info(f"filtered final edgelist is written to file at {edgelist_path}")

    return 1


def calculate_similarity_df(column1, column2):
    """Function that calculates the string similarity between the two names.
    Returns a dataframe with similarity measures."""
    combinations = list(itertools.product(column1, column2))

    sim = []
    for com in combinations:
        sim.append(jellyfish.jaro_winkler_similarity(com[0], com[1]))

    sim_df = pd.DataFrame(combinations, columns=["description", "source"])
    sim_df["value"] = sim

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
