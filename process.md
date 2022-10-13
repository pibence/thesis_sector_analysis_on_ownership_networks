# Algorithm to test the effect of shocks

## Process:
1. shock one sector (shocks coming from Pareto dist)
2. set threshold 
    * based on E/V, if that is crossed, obvious bankruptcy or
    * set a constant
3. Calculate the new value for each firm that suffered shock. They lose value from their assets and equity on the other side. If threshold is crossed, set value to 0
   
def process:

    for firm in failed ones:

        def subprocess:

            if neigbors == 0:
                continue on next failed one
            else:
                for neighbor in neighbors:

                    calculate the new value # they might have been shocked to some extent but did not fail, also add the loss of value coming from the owned assets
                    
                    if value < threshold:
                        call this subprocess recursively
                    else:
                        continue on next neighbor

Process properties:
* shock only propagated through if there was a dafeult --> loss in value does not result in loss of other firms value if threshold is not reached

upgrade idea: recalculate values of each neighbor regardless of the failure, if failure happens value =0, otherwise only the loss --> more realistic model, they own a percentage of shares, their value drops, owner's value drops as well
change required: iterate through all the effected nodes, not olny the ones who fail

## Simulation
0. Calculate predefinied centrality measures for all nodes --> degree centrality, betweenness centrality
1. All sector shock simulated ~10.000 times --> Monte carlo sim
2. Save the state of the sector: which companies failed in the first round (*starters*), second (*propagators*), etc, save their centrality measures
3. Compare the results when shocks propagete --> TODO: define contagion
4. Calculate the ratio of contagion occurance --> the higher the ratio, the more important the sector is
5. Descriptive statistics for each sector after the sim about the centrality measures and shock propagating capabilities
6. After simulating all sectors, compare the results, choose the most important one
7. Compare the centrality measures' importance, harminize them, compare with research papers.

### Tweaks in simulation
Use different shock distributions
Try shocking individual entities as well --> not just systemic shock but idiosyncratic as well

### Macro level metrics to calculate for sectors/whole network
* degree distribution
* clustering coefficient

### Micro level metrics to calculate for given nodes
* degree centrality
* betweenness centrality


# Summary of data cleaning, modelling process
## Downloading the data
1. 13f filings from SEC
2. Sector, financial data from Refinitiv Eikon

## Cleaning the data
1. string similarity measures are calculated to match the two databases
2. creating filtered edgelist and node list 
TODO update tis part

## Creating the graph
1. The edgelist and node list is further filtered to remove nodes that are from
the financial sector but has not submitted 13f filings thus the value of the holdings is not possible to calculate.
2. Removing self-loop edges
3. adding attributes to the nodes
    - For financial companies the total assets are the summarized value of the sec filings
    - For non-financial companies its the total assets from Refinitiv Eikon database
4. Removing edges within the financial sector by decreasing the value of both holder and held companies
5. Removing edges between non-financial companies without decreasing their value
    - reason: these edges are not significant or they are a result of wrong name matching (that was necessary due to discrepancy in data sources)
6. Projecting the bipartite graph to eliminate the financial companies and focus on the other sectors
    - from directed graph we get an undirected one
    - there is a link between two nodes of they are held by the same financial company
    - principles for edge weigts:
        - it should be as simple as possible
        - if a financial institution holds more from one firm (in absolute terms), the weight should increase
        - if a portfolio suffers loss from one asset, we suppose they have to decrease their other held assets with the same amount --> this way they play only the role of an intermediary, the loss is propagated through.
        - if a portfolio is larger, the propagated loss should be smaller for the same owned asset size
    - the weight of the edge (u,v) is calculated for nodes (u, v, f), where the edgelist is: f->u, w(fu), f->v, w(fv) and the asset value of the nodes are V(u), V(v), V(f) respectively: w(new) = sum w(fu) * w(fv) /V(f) for f in portfolios holding both u,v