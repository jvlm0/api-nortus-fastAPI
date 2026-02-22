from typing import List
from app.schemas.equipe import Vendedor



def buscar_vendedores(cursor, cod_gerador):


    sql2 = """
            SELECT f.COD_FUNC, p.NOME, c.PERCENTO
                    FROM FUNCIONARIO f
                    INNER JOIN PESSOA p ON f.COD_PESSOA = p.COD_PESSOA
                    INNER JOIN COMPROD c ON f.COD_FUNC =  c.COD_FUNCIONARIO
                    WHERE f.COD_PESSOA IS NOT NULL AND c.COD_GERADOR = ?;
        """
    cursor.execute(sql2, (cod_gerador,))

    rows = cursor.fetchall()

    vendedores = List[Vendedor]
    for r in rows:
        vendedores(Vendedor(cod_vendedor= r[0], nome= r[1]))

    return vendedores