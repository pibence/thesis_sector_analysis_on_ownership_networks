from platform import node
import pandas as pd
import yfinance as yf
import logging

logging.basicConfig(
    filename="logs/load.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
)


def download_financial_info(ticker):
    ticker_info = yf.Ticker(ticker)

    bs = ticker_info.quarterly_balance_sheet
    total_liab = bs.loc["Total Liab"][0] / 1000
    total_asset = bs.loc["Total Assets"][0] / 1000
    sh_eq = bs.loc["Total Stockholder Equity"][0] / 1000

    ret_list = [ticker, total_asset, total_liab, sh_eq]

    return ret_list


def add_financial_info_to_nodes(node_info_path):
    """
    Function that downloads financial data for tickers and appends them to
    the node_info table.
    """

    node_info = pd.read_csv(node_info_path)

    tickers = node_info.symbol

    financials = []
    for ticker in tickers:
        try:
            financials.append(download_financial_info(ticker))
            logging.info(f"financial data is retrieved for {ticker}.")
        except Exception as e:
            logging.warning(
                f"could not retrieve financial data for {ticker} as the following error occured: {e}"
            )
    financials_df = pd.DataFrame(
        financials, columns=["ticker", "total_asset", "total_liab", "sh_eq"]
    )

    ret_df = node_info.merge(
        financials_df, how="inner", left_on="symbol", right_on="ticker"
    )

    ret_df.to_csv("data/final/node_info_extended.csv")

    return 1
