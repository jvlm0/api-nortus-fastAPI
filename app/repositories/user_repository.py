from app.database import get_app_pool
from app.utils.security import hash_password
from fastapi import HTTPException


def criar_usuario(usuario):
    with get_app_pool().connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM USUARIO WHERE USERNAME = ?",
                (usuario.username,)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username já existe")

            senha_hash = hash_password(usuario.senha)

            cursor.execute(
                """
                INSERT INTO USUARIO (USERNAME, SENHA_HASH, CAMINHO_BANCO)
                VALUES (?, ?, ?)
                RETURNING ID
                """,
                (usuario.username, senha_hash, usuario.caminho_banco)
            )

            user_id = cursor.fetchone()[0]

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
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()