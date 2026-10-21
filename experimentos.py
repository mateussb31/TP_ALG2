import math
import time
import numpy as np
import pandas as pd
from src.utils import encodeGeohash, getNeigbhors
from src.osmn import generateDeliverersCoordinates
from src.trie.CompressedTrie import CompressedTrie

RESTAURANTES = ["CHURRASCARIA E RESTAURANTE CAICARA GRILL LTDA", "BAR E LANCHONETE ZUM ZUM LTDA"]
FROTAS = [250, 1000, 5000]
RAIOS = [1, 2, 4]
REPETICOES = 10

restaurants = pd.read_csv("./end_cord.csv")


def distancia(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) * 111.0


def buscar(trie, lat, lon, raio):
    inicio = time.perf_counter()
    candidatos = {}
    for h in getNeigbhors(encodeGeohash(lat, lon)[:5]):
        for d in trie.search(h):
            candidatos[d["id"]] = d
    meio = time.perf_counter()
    no_raio = [d for d in candidatos.values() if distancia(lat, lon, d["lat"], d["lon"]) <= raio]
    fim = time.perf_counter()
    return len(candidatos), len(no_raio), meio - inicio, fim - inicio


def linear(frota, lat, lon, raio):
    inicio = time.perf_counter()
    no_raio = [d for d in frota if distancia(lat, lon, d["lat"], d["lon"]) <= raio]
    return len(no_raio), time.perf_counter() - inicio


resultados = []
for n in FROTAS:
    np.random.seed(42)
    frota = generateDeliverersCoordinates(n, restaurants)
    trie = CompressedTrie()
    for d in frota:
        trie.insert(encodeGeohash(d["lat"], d["lon"]), d)

    for nome in RESTAURANTES:
        r = restaurants[restaurants["NOME"] == nome].iloc[0]
        for raio in RAIOS:
            medicoes = [buscar(trie, r["LATITUDE"], r["LONGITUDE"], raio) for _ in range(REPETICOES)]
            lineares = [linear(frota, r["LATITUDE"], r["LONGITUDE"], raio) for _ in range(REPETICOES)]
            resultados.append({
                "restaurante": nome,
                "n": len(frota),
                "raio_km": raio,
                "candidatos": medicoes[0][0],
                "no_raio": medicoes[0][1],
                "no_raio_linear": lineares[0][0],
                "tempo_trie_ms": round(np.mean([m[2] for m in medicoes]) * 1000, 4),
                "tempo_total_ms": round(np.mean([m[3] for m in medicoes]) * 1000, 4),
                "tempo_linear_ms": round(np.mean([l[1] for l in lineares]) * 1000, 4),
            })

tabela = pd.DataFrame(resultados)
tabela.to_csv("resultados.csv", index=False)
print(tabela.to_string(index=False))