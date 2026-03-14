from app.database import get_client_pool
from app.schemas.ct_receber import CtReceberResponse, CtReceber
from typing import List
from decimal import Decimal, ROUND_HALF_UP


def list_ct_a_receber(dsn: str) -> CtReceberResponse:

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql_ct = """
                SELECT
                    c.COD_CTARECEBER,
                    c.DTLANC AS data,
                    c.HISTORICO AS descricao,
                    p2.VALOR AS valor_parcela,
                    c.COD_CLIENTE,
                    p.NOME AS nome_cliente
                FROM CTARECEBER c
                LEFT JOIN CLIENTE cl ON c.COD_CLIENTE = cl.COD_CLIENTE
                LEFT JOIN PESSOA p ON cl.COD_PESSOA = p.COD_PESSOA
                INNER JOIN PARCELACR p2
                    ON p2.COD_CTARECEBER = c.COD_CTARECEBER
                    AND p2.DTDEBITO IS NULL
                WHERE c.VALOR > 0
                ORDER BY c.DTLANC DESC
            """

            cursor.execute(sql_ct)
            rows = cursor.fetchall()

            contas: List[CtReceber] = [
                CtReceber(
                    cod_ct_receber=row[0],
                    data_lancamento=row[1],
                    descricao=row[2] or "",
                    valor=float(Decimal(str(row[3])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)) if row[3] else 0.0,
                    cod_cliente=row[4] if row[4] else 0,
                    nome_cliente=row[5] or ""
                )
                for row in rows
            ]

            valor_total = float(
                sum((Decimal(str(c.valor)) for c in contas), Decimal('0'))
                .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            )

            return CtReceberResponse(total=valor_total, cts_receber=contas)

        finally:
            cursor.close()
