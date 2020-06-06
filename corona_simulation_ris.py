# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 19:05:17 2020

@author: Simon
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import datetime
import imageio
import os
import pandas as pd


"""
SIR
Single node influence measuring using SIR
Using the Susceptible Influenced Recovered (SIR) model, calculate the influence that
each node has on the rest of the network. These node influence values can, arguably,
be used as the node rank 'ground truth'.
Based on: https://www.sciencedirect.com/science/article/pii/S0378437113010406?via%3Dihub
Note that the below function does not include multiple simulations yet

Input:  Graph G, a (di)graph object from networkx
        start_node, a list [] with one or more starting nodes
        save_location, string of the path to where the images should be saved
        R, the average amount of nodes an infected node will infect
        death_rate, the death_rate of the infection
        
Output: n_infected, a list with the progression of the amount of infected present each day
        n_dead, a list with the progression of the amount of deaths occuring each day
        n_recovered, a list with the progression of how many recover each day
        dead_nodes, a list with the names of the dead nodes
        recovered_nodes, a list with the names of the recovered nodes
        uninfected_nodes, a list with the names of the nodes that were never infected

        
"""
def SIR(G, start_node, save_location, R = 2.2, death_rate = 1/20):
    
    # make a copy of the graph G so we can mutate it
    G_copy = G.copy()

    # give nodes attributes
    nx.set_node_attributes(G_copy, values = 'yellow', name = 'color')
    nx.set_node_attributes(G_copy, values = 0, name = 'infected_days')
    nx.set_node_attributes(G_copy, values = 0, name = 'total_infection_time')
    
    # save the position and the first figure before infection
    day = -1
    positions = nx.spring_layout(G_copy)
    save_fig(G = G_copy, pos = positions, day = day, R = R, death_rate = death_rate, save_location = save_location)
    
    # start the outbreak at the start node(s)
    infected = []
    for i in start_node:
        
        infected.append(i)

        # set the attributes of the node where the outbreak starts
        G_copy.nodes[i]['color'] = 'red'
        G_copy.nodes[i]['infected_days'] = max(1, int(np.random.normal(14, 3.5, 1))) # change infection duration here
        G_copy.nodes[i]['total_infection_time'] = G_copy.nodes[i]['infected_days']
    
    n_infected = [len(infected)]
    

    # initialize the lists for keeping track of number of recovered and dead
    recovered_nodes = []
    n_recovered = []
    dead_nodes = []
    n_dead = []
    
    # save the second figure, onset of outbreak
    day = 0
    save_fig(G = G_copy, pos = positions, day = day, R = R, death_rate = death_rate, save_location = save_location)
    
    degree_list = dict(G_copy.degree())
    
    # keep running the simulation until there are no more infections
    while len(infected) != 0:
        
        newly_infected = []
        new_dead = 0
        new_recovered = 0
        
        # loop over all infected 
        for i in infected:
            
            # on average each person infects R people during infection span
            beta = R / degree_list.get(i) / G_copy.nodes[i]['total_infection_time']
            
            # get neighbors
            N = list(G_copy.neighbors(i))
            
            # loop over all neighbors and infect them with probability beta
            for j in N:
                
                if G_copy.nodes[j]['color'] == 'yellow':
                    if np.random.rand(1) < beta:
                        # set color to red to signify infection
                        G_copy.nodes[j]['color'] = 'red'
                        newly_infected.append(j)
                        
                        # set the recovery time
                        time_until_recovery = max(1, int(np.random.normal(14, 3.5, 1)))
                        G_copy.nodes[j]['infected_days'] = time_until_recovery
                        G_copy.nodes[j]['total_infection_time'] = time_until_recovery
            
            # get the length of how long node i will be infected
            days_infected_i = G_copy.nodes[i]['infected_days']
            
            # reduce infection length by 1 to signify a day passing
            if G_copy.nodes[i]['color'] == 'red' and days_infected_i != 0:
                G_copy.nodes[i]['infected_days'] = days_infected_i - 1
            
            # if the infection has run its course, set node to recovered or dead
            if G_copy.nodes[i]['color'] == 'red' and days_infected_i == 0:
                if np.random.rand(1) < death_rate:
                    dead_nodes.append(i)
                    # set the color to black if a node dies
                    G_copy.nodes[i]['color'] = 'black'
                    new_dead += 1
                # set the color to blue if a node recovers
                else:
                    recovered_nodes.append(i)
                    G_copy.nodes[i]['color'] = 'blue'
                    new_recovered += 1
        
        # update the lists that track progress
        n_dead.append(new_dead)
        n_recovered.append(new_recovered)        
        n_infected.append(len(newly_infected))
        
        # add newly infected to the old infected
        infected = infected + newly_infected
        
        # remove recovered and dead nodes from the infected pool
        infected = np.setdiff1d(np.array(infected), np.array(recovered_nodes))
        infected = list(np.setdiff1d(infected, np.array(dead_nodes)))
        
        # increase day timer and save the state
        day += 1
        save_fig(G = G_copy, pos = positions, day = day, R = R, death_rate = death_rate, save_location = save_location)
        #print("Amount of people recovered today: ", new_recovered)
        #print("Amount of people dead today: ", new_dead, "\n")
      
    # acquire the nodes that were not infected
    uninfected_nodes = np.setdiff1d(np.array(list(G_copy.nodes())), np.array(recovered_nodes))
    uninfected_nodes = list(np.setdiff1d(uninfected_nodes, np.array(dead_nodes)))

    return [n_infected, n_dead, n_recovered, dead_nodes, recovered_nodes, uninfected_nodes]
    

# function to draw and save
def save_fig(G, pos, day, R, death_rate, save_location):
    
    # get the current time down to the millisecond for unique file names
    date_object = str(datetime.datetime.now())
    date_object = date_object.replace(" ", "_")
    date_object = date_object.replace(":", "-")
    date_object = date_object.replace(".", "-")
    
    # extract the color info for each node
    color_info = list(dict(G.nodes(data = 'color')).values())
    
    # draw the graph with fixed position and node color information
    nx.draw(G, pos = pos, node_color = color_info)
    
    # add legend information and title
    yellow_uninfected = mpatches.Patch(color = 'yellow', label = 'Susceptible')
    red_infected = mpatches.Patch(color = 'red', label = 'Infected')
    black_dead = mpatches.Patch(color = 'black', label = 'Dead')
    blue_recovered = mpatches.Patch(color = 'blue', label = 'Recovered')
    plt.legend(handles = [yellow_uninfected, red_infected, black_dead, blue_recovered])
    plt.title("Coronavirus spread")
    
    if day == 0:
        plt.suptitle("Day " + str(day) + ". Infection is introduced.")
    else:
        plt.suptitle("Day " + str(day))
        
    plt.xlabel("Average infection rate: " + str(R) + "\n" + "Average mortality rate: " + str(death_rate))
    plt.savefig(save_location + date_object + ".png")
    plt.clf()


# function to create a gif from the images
# give as input the folder location, the desired fps (recommended 0.5) and if it should be a gif or not
def animate_figs(images_location, fps, gif = True):
    
    # get the files in the folder
    file_names = os.listdir(images_location)
    
    # add them to a list if they're png files
    images = []
    for i in file_names:
        if i[-4:] == '.png': # adjust this if necessary
            images.append(imageio.imread(images_location + i))
    
    if gif == True:
        imageio.mimsave(images_location + 'movie.gif', images, duration = fps)
    else:
        imageio.mimsave(images_location + 'movie.mp4', images, fps = 2)
        
        
        
def main():
    
    # read graph from file, adapt this to your own network file
    save_path = "C:/Users/TEST/Documents/FOLDER_OUTPUT/"
    temp_df = pd.read_csv("C:/Users/TEST/Documents/NETWORK_FILE", header = 0, sep = " ", index_col = False)
    graph = nx.from_pandas_edgelist(temp_df, source = 'source', target = 'target', create_using = nx.Graph())
    l_cc = max(nx.connected_components(graph), key = len)
    G = graph.subgraph(l_cc)
    
    # or create a randomly generated graph G
    #n = 100
    #unG = nx.fast_gnp_random_graph(n = n, p = (2 * np.log(n) / n), directed = False)
    #nx.is_connected(unG)
    
    # run model, change parameters to your liking
    results = SIR(G = G, start_node = [3], save_location = save_path, R = 2.2, death_rate = 1/20)
    
    # create gif or mp4, change parameters to your liking
    animate_figs(images_location = save_path, fps = 0.5, gif = True)

if __name__ == "__main__":
    
    main()




