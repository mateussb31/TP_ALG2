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


SAVE_EVERY = 10


def generateRestaurantCoordinates(total=20000):
    """Geocodifica restaurantes e salva suas coordenadas, com salvamento parcial."""
    source = pd.read_csv(DATA_DIR / "bares.csv")
    output_path = DATA_DIR / "end_cord.csv"

    # Retoma de onde parou: pula nomes que já estão no CSV
    if output_path.exists():
        done = pd.read_csv(output_path, index_col=0)
        results = done.to_dict("records")
        already = set(done["NOME"])
    else:
        results, already = [], set()

    subset = source.iloc[:total]
    addresses = subset.apply(getFormattedLocation, axis=1)
    errors = 0
    new_found = 0

    try:
        for index, address in addresses.items():
            name = source.loc[index, "NOME"]
            if name in already:
                continue
            try:
                latitude, longitude = ox.geocode(address)
            except ox._errors.InsufficientResponseError:
                errors += 1
                continue
            results.append({"NOME": name, "LATITUDE": latitude, "LONGITUDE": longitude})
            new_found += 1
            print(f"[{index + 1}/{len(subset)}] {name}")

            if new_found % SAVE_EVERY == 0:
                pd.DataFrame(results).to_csv(output_path)
    finally:
        # Roda mesmo com Ctrl+C ou erro: salva o que já foi encontrado
        output = pd.DataFrame(results)
        output.to_csv(output_path)
        print(f"Endereços com erro: {errors} | Total no CSV: {len(output)}")

    return output
if __name__ == "__main__":
    generateRestaurantCoordinates()
