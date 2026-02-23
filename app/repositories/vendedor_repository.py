from app.database import get_client_pool


def listar_vendedores(dsn: str):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql = """
                SELECT f.COD_FUNC, p.NOME
                FROM FUNCIONARIO f
                INNER JOIN PESSOA p ON f.COD_PESSOA = p.COD_PESSOA
                WHERE f.COD_PESSOA IS NOT NULL
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            return [{"cod_vendedor": r[0], "nome": r[1]} for r in rows]
        finally:
            cursor.close()