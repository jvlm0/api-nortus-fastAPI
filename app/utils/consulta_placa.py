import httpx
import os
from app.schemas.veiculo import VeiculoCreate


async def consulta_placa(placa: str) -> VeiculoCreate | None:
    url = os.getenv("URL_API_PLACAS")
    key = os.getenv("KEY_PLACAS")
    url_completa = f"{url}/{placa}/{key}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url_completa, timeout=10)
            response.raise_for_status()
            result = response.json()

        extra = result.get("extra", {}) or {}
        chassi = extra.get("chassi") or result.get("chassi")

        return VeiculoCreate(
            placa=placa,
            modelo=result.get("MODELO"),
            ano=result.get("ano"),
            cor=result.get("cor"),
            chassi=chassi or None,
            marca=result.get("marca")
        )

    except httpx.HTTPError as e:
        print(f"Erro na consulta da placa: {e}")
        return None