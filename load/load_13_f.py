import pandas as pd
import logging
from sec_edgar_downloader import Downloader
import os
from bs4 import BeautifulSoup
import re
import datetime
from tqdm import tqdm


logging.basicConfig(
    filename="logs/load_13f.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
)


def download_13f_filings(submitters_path, data_folder, result_folder):
    """
    Downloader function that iterates through the companies that submitted the
    13f form and downloads them into a given folder structure.
    """

    submitters = get_submitters(submitters_path)
    dl = Downloader(f"{data_folder}13f")
    if os.path.exists(result_folder):
        existing = os.listdir(result_folder)

    for cik in submitters():
        if os.path.exists(result_folder):
            if cik not in existing:
                download_13_filing_helper(cik, dl)
            else:
                logging.info(
                    f"skipping download for {cik} as it has been already downloaded"
                )
        else:
            download_13_filing_helper(cik, dl)

    return 1


def download_13_filing_helper(cik, dl):
    try:
        res = dl.get("13F-HR", cik, amount=1)
        if res == 1:
            logging.info(f"Data downloaded for cik {cik}")
        if res == 0:
            logging.info(f"cannot find 13f filing for {cik}")
    except Exception as e:
        logging.warning(
            f"when trying to download 13f filings for cik {cik} the following error occured: {e}"
        )


def get_submitters(submitter_path):
    """
    Function to retrieve the CIK-s for all companies who filed 13f report in
    the last year.
    """

    submission = pd.read_csv(submitter_path, sep="\t", dtype={"CIK": str})
    ret_list = submission[
        submission.SUBMISSIONTYPE.isin(["13F-HR", "13F-HR/A"])
    ].CIK.unique

    return ret_list


def get_path_for_txt(filings_folder, fold):
    """
    Helper function that concatenates the whole path for  given company.
    """

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
    and the value in 1000 USD.
    """

    soup = BeautifulSoup(open(path, encoding="utf8").read(), "lxml")

    try:
        header = soup.find_all("headerdata")[0]
        date_str = header.find("periodofreport").text
        date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date()

        if date > datetime.date(2022, 6, 1):
            # finding name if form filer company
            formdata = soup.find_all("formdata")[0]
            holder = formdata.find("filingmanager").find("name").text

            infotables = soup.find_all(re.compile("infotable"))

            records = []
            for table in infotables:
                # iterating through all companies that are held by the 13f reporter,
                # saving important data
                dic = {}
                dic["name_of_issuer"] = table.find(re.compile("nameofissuer")).text
                dic["title_of_class"] = table.find(re.compile("titleofclass")).text
                dic["cusip"] = table.find(re.compile("cusip")).text
                dic["value"] = int(
                    table.find(re.compile("value")).text.replace(",", "")
                )
                records.append(dic)

            df = pd.DataFrame(records)

            # summarize ownership in 3 different share types to get full ownership
            df = df.groupby("name_of_issuer")[["value"]].sum().reset_index()
            df[["name_of_issuer"]] = df[["name_of_issuer"]].apply(
                lambda x: x.str.lower()
            )

            # adding holder info to dataframe
            df["holder"] = holder
            logging.info(f"holdings parsed from file {path}")

            return df

        else:
            logging.info(
                f"Filing in {path} contains older data then last quarter, information is ignored."
            )

    except Exception as e:
        logging.warning(
            f"The following error occured when parsing data from {path}: {e}"
        )


def create_edgelist_from_df(df):
    """
    Function that takes the returned df of parse_filing and remanes the columns.
    The holder company is the source of the edge while the issuer of the stock
    is the target to represent ownership structure.
    """

    df.columns = ["target", "value", "source"]
    edgelist = df[["source", "target", "value"]]
    return edgelist


def parse_filings_to_edgelists(
    filings_folder, error_csv_path, edgelist_path, chunksize
):
    """
    Function that lists all existing 13f reports and parses each of them into
    edgelists, then concatenates the edgelists together. The paths for files that
    are failed to parse are listed and saved to a csv file. The edgelists are
    written to files in chunks to avoid memory overload.
    """

    fils = os.listdir(filings_folder)

    edgelists = []
    failed_paths = []
    for i, holder in enumerate(tqdm(fils)):
        # get path, name for each 13f reporter company
        path = get_path_for_txt(filings_folder, holder)

        # parse the txt filing dataframe, if succeeds, parse it to edgelist
        parsed_df = parse_filing(path)

        if parsed_df is not None:
            edgelists.append(create_edgelist_from_df(parsed_df))
        else:
            logging.info(f"Could not parse holdings data for {path}")
            failed_paths.append(path)

        # writing the concatenated edgelists to files after a given chunksize to
        # avoid memory overload
        if ((i + 1) % chunksize == 0) or ((i + 1) == len(fils)):
            edgelist = pd.concat(edgelists)
            edgelists = []
            logging.info(f"{(i+1)/chunksize}. chunk has been written to csv.")
            edgelist.to_csv(f"{edgelist_path}/{(i+1)/chunksize}_chunk.csv", index=False)

    failed_df = pd.DataFrame(failed_paths, columns=["path"])
    failed_df.to_csv(error_csv_path, index=False)
    logging.info(f"paths that failed to parse are written to csv in {error_csv_path}")
    logging.debug("A run has been finished.")

    return 1
