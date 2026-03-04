import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.utils.auth import verificar_token

router = APIRouter(prefix="/uploads", tags=["Uploads"])

TEMP_DIR = "uploads/temp"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg"}
MAX_SIZE_MB = 10


@router.post("/temp", status_code=201)
async def upload_imagem_temp(
    file: UploadFile = File(...),
    token: dict = Depends(verificar_token)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. Use JPEG, PNG, WEBP ou GIF."
        )

    conteudo = await file.read()

    tamanho_mb = len(conteudo) / (1024 * 1024)
    if tamanho_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande ({tamanho_mb:.1f}MB). Máximo permitido: {MAX_SIZE_MB}MB."
        )

    extensao = os.path.splitext(file.filename or "img")[1].lower() or ".jpg"
    nome_unico = f"{uuid.uuid4().hex}{extensao}"

    os.makedirs(TEMP_DIR, exist_ok=True)
    caminho = os.path.join(TEMP_DIR, nome_unico)

    with open(caminho, "wb") as f:
        f.write(conteudo)

    url_temp = f"/static/uploads/temp/{nome_unico}"

    return {
        "url": url_temp,
        "filename": nome_unico,
        "tamanho_kb": round(len(conteudo) / 1024, 1)
    }
