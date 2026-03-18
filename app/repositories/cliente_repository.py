from datetime import datetime

from app.database import get_client_pool
from app.utils.texto import tem_letra
from app.schemas.cliente import ClienteCreate, ClienteUpdate


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


def inserir_cliente(dsn: str, cliente: ClienteCreate):

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        try:


            if (cliente.tipoPessoa == "PF"):
                sql = """
                    UPDATE codigo SET cod_pessoa = cod_pessoa + 1, cod_cliente = cod_cliente + 1, cod_pessoaf = cod_pessoaf + 1
                    RETURNING cod_pessoa, cod_cliente, cod_pessoaf
                """
            else:
                sql = """
                    UPDATE codigo SET cod_pessoa = cod_pessoa + 1, cod_cliente = cod_cliente + 1, cod_pessoaj = cod_pessoaj + 1
                    RETURNING cod_pessoa, cod_cliente, cod_pessoaj
                """
            cursor.execute(sql)
            row = cursor.fetchone()
            cod_pessoa = row[0]
            cod_cliente = row[1]
            cod_tipo_pessoa = row[2]

            sql = """
                INSERT INTO pessoa (COD_PESSOA, NOME, TELREL, CPFCNPJ)
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(sql, (cod_pessoa, cliente.nome, cliente.telefone, cliente.cpfcnpj))

            sql2 = """
                INSERT INTO CLIENTE (COD_CLIENTE, COD_PESSOA, data_cad, ATIVO)
                VALUES (?, ?, ?, 1)
                RETURNING COD_CLIENTE
            """


            if (cliente.tipoPessoa.upper() == "PF"):
                sql_t = """
                    INSERT INTO pessoaf (cod_pessoaf, cod_pessoa) values (?,?)
                """
            else:
                sql_t = """
                    INSERT INTO pessoaj (cod_pessoaj, cod_pessoa) values (?,?)
                """
    
            cursor.execute(sql_t, (cod_tipo_pessoa, cod_pessoa))

            cursor.execute(sql2, (cod_cliente, cod_pessoa, datetime.now().date()))
            cod_cliente = cursor.fetchone()[0]


            return cod_cliente
            

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()


def atualizar_cliente(dsn: str, cod_cliente: int, cliente: ClienteUpdate):

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        try:
            # Verifica se o cliente existe e está ativo, obtendo o COD_PESSOA
            cursor.execute(
                "SELECT COD_PESSOA FROM CLIENTE WHERE COD_CLIENTE = ? AND ATIVO = 1",
                (cod_cliente,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            cod_pessoa = row[0]

            # COALESCE: se o valor recebido for NULL, mantém o valor atual do banco
            sql = """
                UPDATE PESSOA SET
                    NOME    = COALESCE(?, NOME),
                    TELREL  = COALESCE(?, TELREL),
                    CPFCNPJ = COALESCE(?, CPFCNPJ)
                WHERE COD_PESSOA = ?
            """
            cursor.execute(sql, (cliente.nome, cliente.telefone, cliente.cpfcnpj, cod_pessoa))

            return cod_cliente

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()
