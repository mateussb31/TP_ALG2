import numpy as np
import osmnx as ox
import os

GRAPH_PATH = "./data/bh_graph.graphml"

def generateNormalDistribution(restaurants, qtt_deliverers: int):
    """Gera coordenadas aleatórias ao redor dos restaurantes."""
    centers = qtt_deliverers//len(restaurants)
    lats=[]
    longs = []
    for index,row in restaurants.iterrows():
        longs.extend(np.random.normal(loc=row["LONGITUDE"],scale=0.003,size=centers))
        lats.extend(np.random.normal(loc=row["LATITUDE"],scale=0.003,size=centers))
    return lats,longs

def getRealNodes(G, lats,longs):
    rn = ox.distance.nearest_nodes(G,X=longs, Y=lats)
    deliverers = []
    for deliverer_id, node_id in enumerate(rn):
        node = G.nodes[node_id]
        deliverers.append({
            "id": deliverer_id+1,
            "lat": float(node["y"]),
            "lon": float(node["x"]),
        })

    return deliverers

def generateDeliverersCoordinates(N: int, restaurants):
    """Gera posições de entregadores associadas à malha viária de Belo Horizonte."""
    if os.path.isfile(GRAPH_PATH):
        G = ox.load_graphml(filepath=str(GRAPH_PATH))
    else:
        G = ox.graph_from_place("Belo Horizonte, Minas Gerais, Brazil") 
        ox.save_graphml(G, filepath=str(GRAPH_PATH))


    data = generateNormalDistribution(restaurants, N)
    result = getRealNodes(G,data[0],data[1])
    return result

