from fastapi import APIRouter, HTTPException
from app.database import get_connection_app_users
from app.schemas.user import UsuarioCreate, UsuarioResponse
from app.utils.security import hash_password

router = APIRouter(prefix="/users", tags=["Usuários do app"])


@router.post("", response_model=UsuarioResponse, status_code=201)
def criar_usuario(usuario: UsuarioCreate):
    conn = get_connection_app_users()
    cur = conn.cursor()

    try:
        # Verifica se o username já existe
        cur.execute(
            "SELECT 1 FROM USUARIO WHERE USERNAME = ?",
            (usuario.username,)
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Username já existe"
            )

        senha_hash = hash_password(usuario.senha)

        # Insere o usuário
        cur.execute(
            """
            INSERT INTO USUARIO (USERNAME, SENHA_HASH, CAMINHO_BANCO)
            VALUES (?, ?, ?)
            RETURNING ID
            """,
            (
                usuario.username,
                senha_hash,
                usuario.caminho_banco
            )
        )

        user_id = cur.fetchone()[0]
        conn.commit()

        return {
            "id": user_id,
            "username": usuario.username,
            "caminho_banco": usuario.caminho_banco
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    finally:
        cur.close()
        conn.close()
