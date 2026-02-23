from app.database import get_app_pool
from app.utils.security import verify_password
from fastapi import HTTPException, status


def buscar_usuario_login(username: str, senha: str):
    with get_app_pool().connection() as conn:
        cursor = conn.cursor()
        try:
            sql = "SELECT ID, USERNAME, SENHA_HASH FROM USUARIO WHERE USERNAME = ?"
            cursor.execute(sql, (username,))
            resultado = cursor.fetchone()

            if not resultado or not verify_password(senha, resultado[2]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuário ou senha incorretos"
                )

            return {
                "sub": str(resultado[0]),
                "username": resultado[1]
            }
        finally:
            cursor.close()