import pandas as pd
import logging
from sec_edgar_downloader import Downloader
import os
from bs4 import BeautifulSoup
import re

logging.basicConfig(filename='logs/load.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')


def get_balace_sheet_data(path):
    """
    Function to retrieve total assets, total liabilities and total equity
    for a given firm from sec 10-Q filing.
    """



def download_10q_filings(company_list, data_folder, reports_folder, missing_10q_path):
    """
    Function to download 10-q filings from sec edgar database for all given
    companies. If no 10q filing is available, the name of the company is saved,
    their value will be calculated with other methods.
    """

    dl = Downloader(f"{data_folder}10q")
    comp_wo_10q = []

    if os.path.exists(reports_folder):
        existing = os.listdir(reports_folder)

    for cname in company_list:
        if os.path.exists(reports_folder):
            if cname not in existing:
                res = download_10q_filing_helper(cname, dl)
        else:
            res = download_10q_filing_helper(cname, dl)

        if res ==0:
            comp_wo_10q.append(cname)
    failed_df = pd.DataFrame(comp_wo_10q, columns=["not_listed_companies"])
    failed_df.to_csv(missing_10q_path, index=False)
    logging.info(f"paths that failed to parse are written to csv in {missing_10q_path}")

    return 1


def download_10q_filing_helper(cname, dl):
    
    
    try:
        res = dl.get("10-Q", cname, amount=1)
        if res == 1:
            logging.info(f"Data downloaded for {cname}")
        if res == 0:
            logging.info(f"cannot find 10q filing for {cname}")
        return res
    except Exception as e:
        logging.warning(f"when trying to download 10q filings for {cname} the following error occured: {e}")


def get_unique_companies(edgelist_path):

    el = load_edgelist(edgelist_path)

    companies = []
    for col in  ["source", "target"]:
        companies.extend(el[col].unique())
    
    return companies
    



def load_edgelist(edgelist_path):
    edgelists = os.listdir(edgelist_path)
    
    el_list = []
    for edgelist in edgelists:
        el_list.append(pd.read_csv(f"{edgelist_path}{edgelist}"))
    
    df = pd.concat(el_list)
    
    return df