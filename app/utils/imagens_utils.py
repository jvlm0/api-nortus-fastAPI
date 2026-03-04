import os
import uuid
import shutil
from typing import List
from fastapi import UploadFile


# Caminho real no filesystem (relativo ao diretório de execução do servidor)
UPLOAD_BASE_DIR = "uploads"

# Prefixo de URL pública (conforme montagem em main.py: /static/uploads -> uploads/)
UPLOAD_URL_PREFIX = "/static/uploads"

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg"}
MAX_SIZE_MB = 10


def salvar_imagens_ordem(cod_ordem: int, files: List[UploadFile]) -> List[str]:
    """
    Recebe uma lista de UploadFiles, salva cada imagem diretamente em
    uploads/{cod_ordem}/{uuid}.ext e retorna a lista de URLs definitivas.
    """
    if not files:
        return []

    pasta_ordem = os.path.join(UPLOAD_BASE_DIR, str(cod_ordem))
    os.makedirs(pasta_ordem, exist_ok=True)

    urls_definitivas = []

    for file in files:
        conteudo = file.file.read()

        extensao = os.path.splitext(file.filename or "img")[1].lower() or ".jpg"
        nome_definitivo = f"{uuid.uuid4().hex}{extensao}"
        caminho_definitivo = os.path.join(pasta_ordem, nome_definitivo)

        with open(caminho_definitivo, "wb") as f:
            f.write(conteudo)

        url_definitiva = f"{UPLOAD_URL_PREFIX}/{cod_ordem}/{nome_definitivo}"
        urls_definitivas.append(url_definitiva)

    return urls_definitivas


def listar_imagens_ordem(cod_ordem: int) -> List[str]:
    """
    Retorna lista de URLs das imagens já salvas para uma ordem.
    """
    pasta_ordem = os.path.join(UPLOAD_BASE_DIR, str(cod_ordem))
    if not os.path.exists(pasta_ordem):
        return []

    arquivos = sorted([
        f for f in os.listdir(pasta_ordem)
        if os.path.isfile(os.path.join(pasta_ordem, f))
    ])

    return [f"{UPLOAD_URL_PREFIX}/{cod_ordem}/{f}" for f in arquivos]


def remover_imagens_ordem(cod_ordem: int):
    """
    Remove toda a pasta de imagens de uma ordem (usado no delete).
    """
    pasta_ordem = os.path.join(UPLOAD_BASE_DIR, str(cod_ordem))
    if os.path.exists(pasta_ordem):
        shutil.rmtree(pasta_ordem)
