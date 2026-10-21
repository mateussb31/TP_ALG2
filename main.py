import math
import time

import dash
import dash_leaflet as dl
import pandas as pd
from dash import Input, Output, State, ctx, dash_table, dcc, html

from src.osmn import generateDeliverersCoordinates
from src.trie.CompressedTrie import CompressedTrie
from src.utils import encodeGeohash, getNeighborGeohashes

INITIAL_CENTER = [-19.9037, -43.9057]
INITIAL_ZOOM = 14
INITIAL_FLEET = 250
AVERAGE_SPEED_KMH = 20.0
EARTH_RADIUS_KM = 6371.0088
GEOHASH_PRECISION = 8

# Menor lado (km) das células Geohash em BH.
CELL_MIN_SIDE_KM = {3: 140.0, 4: 19.0, 5: 4.5, 6: 0.6, 7: 0.14}

app = dash.Dash(__name__, title="Entregadores BH")

# ============================================================
# Restaurantes
# ============================================================
restaurants = pd.read_csv("./data/end_cord.csv")
restaurants["LATITUDE"] = pd.to_numeric(restaurants["LATITUDE"], errors="coerce")
restaurants["LONGITUDE"] = pd.to_numeric(restaurants["LONGITUDE"], errors="coerce")
restaurants = restaurants.dropna(subset=["LATITUDE", "LONGITUDE"]).reset_index(drop=True)
restaurants["ID"] = restaurants.index.astype(str)

markers_restaurants = [
    dl.Marker(position=[r["LATITUDE"], r["LONGITUDE"]], children=[dl.Tooltip(str(r["NOME"]))])
    for _, r in restaurants.iterrows()
]

# ============================================================
# Frota + Trie
# ============================================================
trie = CompressedTrie()
deliverers = []


def rebuildFleet(quantity):
    """Substitui a frota atual por entregadores recém-gerados."""
    global deliverers
    trie.clear()
    fleet = []
    for i, p in enumerate(generateDeliverersCoordinates(quantity, restaurants)):
        p.setdefault("id", i + 1)
        p["geohash"] = encodeGeohash(p["lat"], p["lon"])[:GEOHASH_PRECISION]
        trie.insert(p["geohash"], p)
        fleet.append(p)
    deliverers = fleet


# ============================================================
# Auxiliares
# ============================================================
def calculateHaversineDistanceKm(lat1, lon1, lat2, lon2):
    """Calcula em quilômetros a distância entre duas coordenadas."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((phi2 - phi1) / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))



def chooseGeohashPrefixLength(radius_km):
    """Escolhe a precisão Geohash adequada para o raio informado."""
    for precision in sorted(CELL_MIN_SIDE_KM, reverse=True):
        if CELL_MIN_SIDE_KM[precision] >= radius_km:
            return precision
    return min(CELL_MIN_SIDE_KM)


def getNeighborCells(base):
    """Retorna a célula Geohash e suas células vizinhas."""
    neighbors = getNeighborGeohashes(base)
    if isinstance(neighbors, dict):
        neighbors = neighbors.values()
    return {base, *[n for n in neighbors if n]}


def createDelivererMarkers(fleet, selected_ids):
    """Cria marcadores do mapa para a frota e os entregadores selecionados."""
    gray, red = [], []
    for d in fleet:
        selected = d["id"] in selected_ids
        marker = dl.CircleMarker(
            center=[d["lat"], d["lon"]],
            radius=7 if selected else 4,
            color="red" if selected else "gray",
            fillColor="red" if selected else "gray",
            fillOpacity=0.9 if selected else 0.35,
            children=[dl.Tooltip(f"Entregador #{d['id']} | {d['geohash']}")],
        )
        (red if selected else gray).append(marker)
    return gray + red


def createSummaryLines(items):
    """Cria linhas de resumo formatadas para a interface."""
    return [
        html.Div([html.B(f"{label}: "), value], style={"marginBottom": "2px"})
        for label, value in items
    ]


# Frota inicial
rebuildFleet(INITIAL_FLEET)

# ============================================================
# Layout
# ============================================================
SECTION = {"marginBottom": "16px"}
LABEL = {"fontWeight": "bold", "display": "block", "marginBottom": "4px"}

sidebar = html.Div(
    [
        html.H3("Entregadores em BH", style={"marginTop": 0}),
        html.Div(
            [
                html.Label("Restaurante", style=LABEL),
                dcc.Dropdown(
                    id="restaurant-search",
                    options=[
                        {"label": str(r["NOME"]), "value": r["ID"]} for _, r in restaurants.iterrows()
                    ],
                    placeholder="Digite o nome...",
                ),
            ],
            style=SECTION,
        ),
        html.Div(
            [
                html.Label("Raio de atendimento (km)", style=LABEL),
                dcc.Slider(
                    id="distance-slider",
                    min=0.5,
                    max=20,
                    step=0.5,
                    value=2,
                    marks={0.5: "0,5", 5: "5", 10: "10", 15: "15", 20: "20"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style=SECTION,
        ),
        html.Div(
            [
                html.Label("Quantidade de entregadores", style=LABEL),
                html.Div(
                    [
                        dcc.Input(
                            id="fleet-size",
                            type="number",
                            min=1,
                            step=1,
                            value=INITIAL_FLEET,
                            style={"flex": "1", "minWidth": 0},
                        ),
                        html.Button("Gerar", id="generate-fleet-button", n_clicks=0),
                    ],
                    style={"display": "flex", "gap": "8px"},
                ),
                html.Div(
                    f"{INITIAL_FLEET} entregadores na frota.",
                    id="fleet-status",
                    style={"fontSize": "13px", "color": "#555", "marginTop": "4px"},
                ),
            ],
            style=SECTION,
        ),
        html.Hr(),
        html.Div(
            [
                html.H4("Resumo", style={"margin": "0 0 6px 0"}),
                html.Div("Selecione um restaurante.", id="summary", style={"fontSize": "14px"}),
            ],
            style=SECTION,
        ),
        html.H4("Entregadores próximos", style={"margin": "0 0 6px 0"}),
        dash_table.DataTable(
            id="deliverers-table",
            columns=[
                {"name": "ID", "id": "id"},
                {"name": "Dist. (km)", "id": "distance"},
                {"name": "Tempo (min)", "id": "time_min"},
                {"name": "Geohash", "id": "geohash"},
            ],
            data=[],
            page_size=10,
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "4px 6px", "fontSize": "13px"},
            style_header={"fontWeight": "bold"},
        ),
    ],
    style={
        "width": "380px",
        "flexShrink": 0,
        "height": "100vh",
        "overflowY": "auto",
        "boxSizing": "border-box",
        "padding": "16px",
        "borderRight": "1px solid #ddd",
    },
)

map_panel = dl.Map(
    children=[
        dl.TileLayer(),
        dl.LayerGroup(markers_restaurants),
        dl.LayerGroup(id="radius-layer"),
        dl.LayerGroup(id="deliverers-layer", children=createDelivererMarkers(deliverers, set())),
    ],
    id="restaurant-map",
    center=INITIAL_CENTER,
    zoom=INITIAL_ZOOM,
    style={"flex": "1", "height": "100vh"},
)

app.layout = html.Div(
    [sidebar, map_panel],
    style={"display": "flex", "fontFamily": "Arial, sans-serif", "margin": "-8px"},
)


# ============================================================
# Callbacks -> basicamente o que manipula a interface
# ============================================================
@app.callback(
    Output("restaurant-map", "center"),
    Output("restaurant-map", "zoom"),
    Output("deliverers-table", "data"),
    Output("summary", "children"),
    Output("deliverers-layer", "children"),
    Output("radius-layer", "children"),
    Output("fleet-status", "children"),
    Input("restaurant-search", "value"),
    Input("distance-slider", "value"),
    Input("generate-fleet-button", "n_clicks"),
    State("fleet-size", "value"),
)
def updateQuery(selected_restaurant, max_distance, n_clicks, fleet_size):
    status = dash.no_update

    if ctx.triggered_id == "generate-fleet-button":
        if not fleet_size or fleet_size < 1:
            return (dash.no_update,) * 6 + ("Informe uma quantidade válida.",)
        rebuildFleet(int(fleet_size))
        status = f"Frota atualizada: {len(deliverers)} entregadores."

    match = restaurants.loc[restaurants["ID"] == str(selected_restaurant)]
    if match.empty:
        return (
            INITIAL_CENTER, INITIAL_ZOOM, [], "Selecione um restaurante.",
            createDelivererMarkers(deliverers, set()), [], status,
        )

    r = match.iloc[0]
    r_lat, r_lon = float(r["LATITUDE"]), float(r["LONGITUDE"])

    # Marcacao de tempo
    t0 = time.perf_counter()

    prefix_len = chooseGeohashPrefixLength(max_distance)
    base = encodeGeohash(r_lat, r_lon)[:prefix_len]

    candidates = {}
    for cell in getNeighborCells(base):  # problema da borda
        for d in trie.searchPrefix(cell):
            candidates[d["id"]] = d

    nearby, selected_ids = [], set()
    for d in candidates.values():
        dist = calculateHaversineDistanceKm(r_lat, r_lon, d["lat"], d["lon"])
        if dist <= max_distance:
            selected_ids.add(d["id"])
            nearby.append(
                {
                    "id": d["id"],
                    "distance": round(dist, 3),
                    "time_min": round(dist / AVERAGE_SPEED_KMH * 60, 1),
                    "geohash": d["geohash"],
                }
            )
    nearby.sort(key=lambda x: x["distance"])

    elapsed_ms = (time.perf_counter() - t0) * 1000

    # --- Resumo ---
    if nearby:
        avg_dist = sum(n["distance"] for n in nearby) / len(nearby)
        avg_time = sum(n["time_min"] for n in nearby) / len(nearby)
        summary = createSummaryLines(
            [
                ("Restaurante", str(r["NOME"])),
                ("No raio", f"{len(nearby)} de {len(deliverers)}"),
                ("Mais próximo", f"{nearby[0]['distance']:.2f} km ({nearby[0]['time_min']} min)"),
                ("Distância média", f"{avg_dist:.2f} km"),
                ("Tempo médio", f"{avg_time:.1f} min"),
                ("Consulta", f"{elapsed_ms:.2f} ms"),
                ("Candidatos", f"{len(candidates)} (prefixo {base})"),
            ]
        )
    else:
        summary = createSummaryLines(
            [
                ("Restaurante", str(r["NOME"])),
                ("No raio", f"0 de {len(deliverers)}"),
                ("Consulta", f"{elapsed_ms:.2f} ms"),
                ("Candidatos", f"{len(candidates)} (prefixo {base})"),
            ]
        )

    circle = [
        dl.Circle(center=[r_lat, r_lon], radius=max_distance * 1000, color="#3388ff", fillOpacity=0.12)
    ]
    zoom = int(max(10, min(17, round(16 - math.log2(max(max_distance, 0.5) / 0.5)))))

    return [r_lat, r_lon], zoom, nearby, summary, createDelivererMarkers(deliverers, selected_ids), circle, status


if __name__ == "__main__":
    app.run(debug=True)
