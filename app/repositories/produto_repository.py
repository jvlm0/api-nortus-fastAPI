from app.database import get_client_pool


def buscar_produto(dsn: str, page: int, page_size: int, q: str):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            inicio = (page - 1) * page_size + 1
            fim = page * page_size

            sql_count = """
                SELECT count(*)
                FROM SUBPRODUTO
                Left Join estoque on subproduto.cod_subproduto = estoque.cod_subprod
                WHERE SUBPRODUTO.ATIVO = 'S' AND UPPER(SUBPRODUTO.DESCRICAO) LIKE UPPER(?)
            """
            cursor.execute(sql_count, (f"%{q}%",))
            total = cursor.fetchone()[0]

            sql = f"""
                SELECT COD_SUBPRODUTO, DESCRICAO, MARCA, estoque.vendvarv
                FROM SUBPRODUTO
                Left Join estoque on subproduto.cod_subproduto = estoque.cod_subprod
                WHERE SUBPRODUTO.ATIVO = 'S' AND UPPER(SUBPRODUTO.DESCRICAO) LIKE UPPER(?)
                ROWS {inicio} TO {fim}
            """
            cursor.execute(sql, (f"%{q}%",))
            resultados = cursor.fetchall()

            return {
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": [
                    {
                        "cod_subproduto": r[0],
                        "nome": r[1],
                        "marca": r[2],
                        "preco": r[3]
                    }
                    for r in resultados
                ]
            }
        finally:
            cursor.close()