import pandas as pd
import logging
from sec_edgar_downloader import Downloader
import os
from bs4 import BeautifulSoup
import re


logging.basicConfig(filename='logs/load_13f.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


def download_13f_filings(name_to_cik:dict, data_folder, filings_folder):
    
    dl = Downloader(data_folder)
    if os.path.exists(filings_folder):
        existing = os.listdir(filings_folder)

    for cik, name in name_to_cik.items():
        if os.path.exists(filings_folder):
            if cik not in existing:
                download_13_filing_helper(cik, name, dl)
        else:
            download_13_filing_helper(cik, name, dl)

    return 1


def download_13_filing_helper(cik, name, dl):
    try:
        res = dl.get("13F-HR", cik, amount=1)
        if res == 1:
            logging.info(f"Data downloaded for {name}, with cik {cik}")
        if res == 0:
            logging.info(f"cannot find 13f filing for {cik}")
    except Exception as e:
        logging.warning(f"when trying to download 13f filings for {name} with cik {cik} the following error occured: {e}")


def create_name_to_cik_csv(submitters):
    institutions = pd.read_csv(submitters, sep="\t", dtype={"CIK" : str})
    institutions.columns = institutions.columns.str.lower()
    institutions = institutions.groupby(["name", "cik"]).count().reset_index()[["name", "cik"]]
    institutions[["name"]] = institutions[["name"]].apply(lambda x : x.str.lower())
    
    institutions.to_csv("data/name_to_cik.csv", index=False)


def create_name_to_cik_dict(name_to_cik_path):
    df = pd.read_csv(name_to_cik_path, dtype= {"cik": str})
    ret_dict = dict(zip(df.cik, df.name))
    return ret_dict


def get_path_for_txt(filings_folder, fold):
    path = f"{filings_folder}{fold}/13F-HR"
    subfolder = os.listdir(path)[0]
    path = f"{path}/{subfolder}/full-submission.txt"
    
    return path


def parse_filing(path):
    
    """
    Function that takes the path of a txt file that contains the 13f report 
    of a given company and parses the holding into a dataframe. 3 different kind
    of shares can be hold, to obtain the total ownership, the value of 3 stock
    is summarized. The returned df contains the name of the issuer of the stock
    and the value in USD.
    """

    soup = BeautifulSoup(open(path, encoding="utf8").read(), "lxml")
    
    try:
        infotables = soup.find_all(re.compile('infotable'))

        records = []
        for table in infotables:
            # iterating through all companies that are held by the 13f reporter,
            # saving important data
            dic = {}
            dic["name_of_issuer"] = table.find(re.compile("nameofissuer")).string
            dic["title_of_class"] = table.find(re.compile("titleofclass")).string
            dic["cusip"] =table.find(re.compile("cusip")).string
            dic["value"] = int(table.find(re.compile("value")).string.replace(',', ''))*1000
            records.append(dic)
        
        df =pd.DataFrame(records)

        # summarize ownership in 3 different share types to get full ownership
        df = df.groupby("name_of_issuer")[["value"]].sum().reset_index()
        df[["name_of_issuer"]] = df[["name_of_issuer"]].apply(lambda x : x.str.lower())
        logging.info(f"holdings parsed from file {path}")

        return df

    except Exception as e:
        logging.warning(f"The following error occured when parsing data from {path}: {e}")
        
    



def create_edgelist_from_df(df, holder):
    """
    Function that takes the returned df of parse_filing and appends a new column
    that is called target with the name of the holder company. Also the name 
    of issuer column is renamed to source.
    """
    
    df.columns = ["source", "value"]
    df["target"] = holder
    edgelist = df[["source", "target", "value"]]
    return edgelist


def parse_filings_to_edgelists(filings_folder, name_to_cik_path, error_csv_path):
    """
    Function that lists all existing 13f reports and parses each of them into
    edgelists, then concatenates the edgelists together. The paths for files that
    are failed to parse are listed and saved to a csv file.
    TODO write edgelists to file, divide it into chunks.
    """

    fils = os.listdir(filings_folder)
    name_to_cik_dict = create_name_to_cik_dict(name_to_cik_path)

    edgelists = []
    failed_paths = []
    for holder in fils[0:10]:
        # get path, name for each 13f reporter company
        path = get_path_for_txt(filings_folder, holder)
        name = name_to_cik_dict[holder]

        # parse the txt filing dataframe, if succeeds, parse it to edgelist
        parsed_df = parse_filing(path)
        if parsed_df is not None:
            edgelists.append(create_edgelist_from_df(parsed_df, name))
        else:
            logging.info(f"Could not parse holdings data for {name}")
            failed_paths.append(path)
            
    edgelist = pd.concat(edgelists)
    logging.debug("A run has been finished.")

    failed_df = pd.DataFrame(failed_paths, columns=["path"])
    failed_df.to_csv(error_csv_path, index=False)
    logging.info(f"paths that failed to parse are written to csv in {error_csv_path}")

    return edgelist










