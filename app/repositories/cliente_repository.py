


from datetime import datetime

from app.database import get_client_pool
from app.utils.texto import tem_letra


def buscar_cliente(dsn: str, page: int, page_size: int, q: str):

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        try:
            inicio = (page - 1) * page_size + 1
            fim = page * page_size

            total = 0

            if tem_letra(q):

                sql_count = f"""
                    SELECT count(*)
                    FROM pessoa
                    INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                    WHERE CLIENTE.ATIVO = 1 AND UPPER(PESSOA.NOME) LIKE UPPER(?)
                """
                cursor.execute(sql_count, (f"%{q}%",))

                total = cursor.fetchone()[0]


                # 🔤 Busca por nome
                sql = f"""
                    SELECT CLIENTE.COD_CLIENTE, PESSOA.NOME, PESSOA.TELREL, PESSOA.CPFCNPJ
                    FROM pessoa
                    INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                    WHERE CLIENTE.ATIVO = 1 AND UPPER(PESSOA.NOME) LIKE UPPER(?)
                    ROWS {inicio} TO {fim}
                """
                cursor.execute(sql, (f"%{q}%",))
            else:

                sql_count = f"""
                    SELECT count(*)
                    FROM pessoa
                    INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                    WHERE CLIENTE.ATIVO = 1 AND PESSOA.TELREL LIKE ?
                """
                cursor.execute(sql_count, (f"%{q}%",))
                total = cursor.fetchone()[0]

                # 🔢 Busca por telefone
                sql = f"""
                    SELECT CLIENTE.COD_CLIENTE, PESSOA.NOME, PESSOA.TELREL, PESSOA.CPFCNPJ
                    FROM pessoa
                    INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                    WHERE CLIENTE.ATIVO = 1 AND PESSOA.TELREL LIKE ?
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
                        "COD_PESSOA": r[0],
                        "nome": r[1],
                        "telefone": r[2],
                        "cpfcnpj": r[3]
                    }
                    for r in resultados
                ]
            }

        finally:
            cursor.close()


def inserir_cliente(dsn: str, cliente):

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        try:
            sql = """
                INSERT INTO pessoa (NOME, TELREL, CPFCNPJ)
                VALUES (?, ?, ?)
                RETURNING COD_PESSOA
            """
            cursor.execute(sql, (cliente.nome, cliente.telefone, cliente.cpfcnpj))
            cod_pessoa = cursor.fetchone()[0]

            sql2 = """
                INSERT INTO CLIENTE (COD_PESSOA, data_cad, ATIVO)
                VALUES (?, ?, 1)
                RETURNING COD_CLIENTE
            """

            cursor.execute(sql2, (cod_pessoa, datetime.now().date()))
            cod_cliente = cursor.fetchone()[0]


            return cod_cliente
            

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
