from app.database import get_client_pool
from app.schemas.ct_pagar import CtPagarResponse, CtPagar
from typing import List
from decimal import Decimal, ROUND_HALF_UP


def list_ct_a_pagar(dsn: str) -> CtPagarResponse:

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql_ct = """
                SELECT c.COD_CTAPAGAR, 
                	   c.DTLANC AS data, 
                	   c.HISTORICO AS descricao, 
                	   p2.VALOR AS valor_parcela,
                	   c.COD_FORNEC AS cod_fornecedor,
                	   p.NOME AS nome_fornecedor 
                FROM CTAPAGAR c
                LEFT JOIN FORNECEDOR f ON c.COD_FORNEC  = f.COD_FORNEC 
                LEFT JOIN PESSOA p ON f.COD_PESSOA = p.COD_PESSOA
                INNER JOIN PARCELACP p2 
                    ON p2.COD_CTAPAGAR  = c.COD_CTAPAGAR 
                    AND p2.DTDEBITO IS NULL
                WHERE c.VALOR > 0
                ORDER BY c.DTLANC DESC;
            """

            cursor.execute(sql_ct)
            rows = cursor.fetchall()

            contas: List[CtPagar] = [
                CtPagar(
                    cod_ct_pagar=row[0],
                    data_lancamento=row[1],
                    descricao=row[2] or "",
                    valor=float(Decimal(str(row[3])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)) if row[3] else 0.0,
                    cod_fornecedor=row[4] if row[4] else 0,
                    nome_fornecedor=row[5] or ""
                )
                for row in rows
            ]

            valor_total = float(
                sum((Decimal(str(c.valor)) for c in contas), Decimal('0'))
                .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            )

            return CtPagarResponse(total=valor_total, cts_pagar=contas)

        finally:
            cursor.close()
