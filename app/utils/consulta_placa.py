import requests
import os


from app.schemas.veiculo import VeiculoCreate


def consulta_placa(placa: str):
    

    url = os.getenv("URL_API_PLACAS")
    key = os.getenv("KEY_PLACAS")

    url_completa = f"{url}/{placa}/{key}"

    try:
        response = requests.get(url_completa)
        response.raise_for_status()  # Verifica se a resposta foi bem-sucedida
        result = response.json()  # Retorna os dados da resposta em formato JSON

        modelo = result.get("MODELO", None)
        ano = result.get("ano", None)
        cor = result.get("cor", None)
        extra = result.get("extra", None)
        chassi = None
        if (extra):
            chassi = extra.get("chassi", None)

        if (chassi == None or chassi == ""):
            chassi = result.get("chassi", None)


        marca = result.get("marca", None)

        return VeiculoCreate(
            placa=placa,
            modelo=modelo,
            ano=ano,
            cor=cor,
            chassi=chassi,
            marca=marca
        )




    except requests.exceptions.RequestException as e:
        print(f"Erro na consulta da placa: {e}")
        return None