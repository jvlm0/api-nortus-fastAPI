from app.database import get_client_pool


def listar_equipes(dsn: str):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql = "SELECT COD_EQUIPE, DESCRICAO FROM EQUIPE"
            cursor.execute(sql)
            rows = cursor.fetchall()

            return [{"cod_equipe": r[0], "nome": r[1]} for r in rows]
        finally:
            cursor.close()