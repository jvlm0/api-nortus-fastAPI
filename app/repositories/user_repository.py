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
                INSERT INTO USUARIO (USERNAME, NOME, SENHA_HASH, CAMINHO_BANCO)
                VALUES (?, ?, ?, ?)
                RETURNING ID
                """,
                (usuario.username, usuario.nome, senha_hash, usuario.caminho_banco)
            )

            user_id = cursor.fetchone()[0]

            return {
                "id": user_id,
                "username": usuario.username,
                "nome": usuario.nome,
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


def listar_usuarios():
    with get_app_pool().connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT ID, USERNAME, NOME, CAMINHO_BANCO FROM USUARIO ORDER BY ID")
            rows = cursor.fetchall()
            return [{"id": r[0], "username": r[1], "nome": r[2], "caminho_banco": r[3]} for r in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()


def buscar_usuario(user_id: int):
    with get_app_pool().connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT ID, USERNAME, NOME, CAMINHO_BANCO FROM USUARIO WHERE ID = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")
            return {"id": row[0], "username": row[1], "nome": row[2], "caminho_banco": row[3]}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()


def atualizar_usuario(user_id: int, dados):
    with get_app_pool().connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT ID, USERNAME, NOME, CAMINHO_BANCO FROM USUARIO WHERE ID = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            novo_username = dados.username if dados.username is not None else row[1]
            novo_nome = dados.nome if dados.nome is not None else row[2]
            novo_caminho = dados.caminho_banco if dados.caminho_banco is not None else row[3]

            if dados.username and dados.username != row[1]:
                cursor.execute(
                    "SELECT 1 FROM USUARIO WHERE USERNAME = ? AND ID <> ?",
                    (dados.username, user_id)
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Username já existe")

            if dados.senha:
                from app.utils.security import hash_password
                nova_senha_hash = hash_password(dados.senha)
                cursor.execute(
                    "UPDATE USUARIO SET USERNAME = ?, NOME = ?, CAMINHO_BANCO = ?, SENHA_HASH = ? WHERE ID = ?",
                    (novo_username, novo_nome, novo_caminho, nova_senha_hash, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE USUARIO SET USERNAME = ?, NOME = ?, CAMINHO_BANCO = ? WHERE ID = ?",
                    (novo_username, novo_nome, novo_caminho, user_id)
                )

            return {"id": user_id, "username": novo_username, "nome": novo_nome, "caminho_banco": novo_caminho}

        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()


def deletar_usuario(user_id: int):
    with get_app_pool().connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT IS_ADMIN FROM USUARIO WHERE ID = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Usuário não encontrado")

            if bool(row[0]):
                raise HTTPException(
                    status_code=403,
                    detail="Não é possível remover um usuário administrador"
                )

            cursor.execute("DELETE FROM USUARIO WHERE ID = ?", (user_id,))
            return {"mensagem": "Usuário removido com sucesso"}

        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()
