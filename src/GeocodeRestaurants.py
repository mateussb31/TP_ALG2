from pathlib import Path

import osmnx as ox
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def getFormattedLocation(row):
    """Formata os campos de um restaurante como endereço para geocodificação."""
    parts = [
        str(row["NUMERO_IMOVEL"]) if pd.notna(row["NUMERO_IMOVEL"]) else "",
        row["COMPLEMENTO"],
        row["NOME_BAIRRO"],
        "Belo Horizonte",
        "MG",
        "Brasil",
    ]
    street_type = row["DESC_LOGRADOURO"].replace("AVE", "Avenida")
    address_parts = [str(part).strip() for part in parts if pd.notna(part) and str(part).strip()]
    return f"{street_type} {row['NOME_LOGRADOURO']} {', '.join(address_parts)}"


def generateRestaurantCoordinates(total=120):
    """Geocodifica restaurantes e salva suas coordenadas no arquivo de dados."""
    source = pd.read_csv(DATA_DIR / "bares.csv")
    addresses = source.iloc[:total].apply(getFormattedLocation, axis=1)
    results = []
    errors = 0

    for index, address in addresses.items():
        try:
            latitude, longitude = ox.geocode(address)
        except ox._errors.InsufficientResponseError:
            errors += 1
            continue
        results.append(
            {
                "NOME": source.loc[index, "NOME"],
                "LATITUDE": latitude,
                "LONGITUDE": longitude,
            }
        )

    output = pd.DataFrame(results)
    output.to_csv(DATA_DIR / "end_cord.csv")
    print(f"Endereços com erro: {errors}")
    return output


if __name__ == "__main__":
    generateRestaurantCoordinates()
