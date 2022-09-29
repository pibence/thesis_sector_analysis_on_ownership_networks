# Algorithm to test the effect of shocks

## Process:
1. shock one sector (shocks coming from Pareto dist)
2. set threshold 
    * based on E/V, if that is crossed, obvious bankruptcy or
    * set a constant
3. Calculate the new value for each firm that suffered shock. They lose value from their assets and equity on the other side. If threshold is crossed, set value to 0
   
def process:

    for firm in failed ones:

        if neigbors == 0:
            continue on next failed one
        else:
            for neighbor in neighbors:

                calculate the new value # they might have been shocked to some extent but did not fail, also add the loss of value coming from the owned assets
                
                if value < threshold:
                    call this function recursively (from line 10, if case)
                else:
                    continue on next neighbor

Process properties:
* shock only propagated through if there was a dafeult --> loss in value does not result in loss of other firms value if threshold is not reached

upgrade idea: recalculate values of each neighbor regardless of the failure, if failure happens value =0, otherwise only the loss --> more realistic model, they own a percentage of shares, their value drops, owner's value drops as well
change required: iterate through all the effected nodes, not olny the ones who fail

## Simulation
0. Calculate predefinied centrality measures for all nodes --> TODO define the measures
1. All sector shock simulated 10.000 times --> Monte carlo sim
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
