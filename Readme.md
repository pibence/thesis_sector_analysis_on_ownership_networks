# Thesis - Sector analysis on ownership network

@author: Bence Pipis, 2022

This repo contains the code for my thesis, where I investigated the sector connectedness in the US stock market. In order to do so, I used the methodology of network science and applied it on the ownership network of the stock market.

## Steps performed
1. Obtaining ownership data from individual SEC filings and parsing them to an edgelist
2. Downloading and parsing company information from Refinitiv database
3. Cleaning the data and handling different naming in filings with string similarity measures
4. Creating graph representing the ownership network
5. Projecting the graph to a smaller fraction of its nodes in order to properly model shock propagation
6. Simulating different sized shocks in the asset value of a subsection of nodes and modelling the contagion of defaulted firms
7. Evaluating the results on multiple different plots and identifying the key sectors that affect the others the most
