import dash
from dash import html, dcc, Output, Input, State
import dash_leaflet as dl
import datetime
from utils import geohashConverter
app = dash.Dash(__name__)

# Função de exemplo que retorna um texto dinâmico (pode ser consulta a API, cálculo, etc.)
def obter_dados_ficticios():
    agora = datetime.datetime.now().strftime("%H:%M:%S")
    return f"Dados atualizados às {agora}: Temperatura 24°C, Vento 12 km/h."

app.layout = html.Div([
    html.H2("Exemplo Dash Leaflet com Botão e Texto Dinâmico"),
    
    # Botão e texto de exibição acima do mapa
    html.Div([
        html.Button("Atualizar Informações", id="btn-atualizar", n_clicks=0, style={"padding": "10px 15px", "fontSize": "16px", "cursor": "pointer"}),
        html.Div(id="texto-info", style={"marginTop": "15px", "fontSize": "18px", "fontWeight": "bold", "color": "#2c3e50"})
    ], style={"marginBottom": "20px"}),
    
    # Componente de Mapa Leaflet
    dl.Map([
        dl.TileLayer(),
        dl.Marker(position=[-23.5505, -46.6333], children=[
            dl.Tooltip("São Paulo")
        ])
    ], center=[-23.5505, -46.6333], zoom=10, style={'width': '100%', 'height': '500px'})
])

# Callback: quando o botão for clicado, executa a função e atualiza o texto
@app.callback(
    Output("texto-info", "children"),
    Input("btn-atualizar", "n_clicks"),
    prevent_initial_call=True  # Evita disparar a função antes do primeiro clique
)
def atualizar_texto(n_clicks):
    # Chama a função python que gera/busca o texto
    texto_atualizado = geohashConverter(-18.0,-43.0) 
    return f"Clique nº {n_clicks} -> {texto_atualizado if n_clicks%2 == 0 else "impar"} "

if __name__ == "__main__":
    print(geohashConverter(-18.0,-43.0))
    app.run(debug=True)
