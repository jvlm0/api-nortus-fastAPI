from app.database import get_client_pool
from app.schemas.comissao import (
    ComissaoProduto,
    ComissaoServico,
    ComissaoFuncionario,
    ComissoesResponse,
)
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from collections import defaultdict


def _to_float(value) -> float:
    if value is None:
        return 0.0
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def listar_comissoes(dsn: str, data_inicio: date, data_fim: date) -> ComissoesResponse:
    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            # ----------------------------------------------------------------
            # 1. Comissões de PRODUTOS (ITPRODORD)
            # ----------------------------------------------------------------
            sql_produtos = """
                SELECT
                    c.COD_COMPROD,
                    c.PERCENTO,
                    i.TOTAL * c.PERCENTO / 100 AS valor_comissao,
                    i.COD_ITPRODORD,
                    s.DESCRICAO,
                    i.TOTAL,
                    c.COD_FUNCIONARIO,
                    p.NOME AS nome_funcionario,
                    i.DATA,
                    o.COD_ORDEM,
                    o.OBSORDEM
                FROM COMPROD c
                INNER JOIN ITPRODORD i ON i.COD_ITPRODORD = c.COD_GERADOR
                LEFT JOIN ESTOQUE e ON e.COD_ESTOQUE = i.COD_ESTOQUE
                LEFT JOIN SUBPRODUTO s ON s.COD_SUBPRODUTO = e.COD_SUBPROD
                INNER JOIN FUNCIONARIO f ON f.COD_FUNC = c.COD_FUNCIONARIO
                INNER JOIN PESSOA p ON p.COD_PESSOA = f.COD_PESSOA
                INNER JOIN ORDEM o ON o.COD_ORDEM = i.COD_ORDEM
                WHERE i.TOTAL IS NOT NULL
                  AND i.TOTAL > 0
                  AND i.DATA IS NOT NULL
                  AND o.DTFECH IS NOT NULL
                  AND i.DATA >= ?
                  AND i.DATA <= ?
            """
            cursor.execute(sql_produtos, (data_inicio_str, data_fim_str))
            rows_produtos = cursor.fetchall()

            # ----------------------------------------------------------------
            # 2. Comissões de SERVIÇOS (DESPADIC)
            # ----------------------------------------------------------------
            sql_servicos = """
                SELECT
                    c.COD_COMPROD,
                    c.PERCENTO,
                    d.VLRTOTFIN * c.PERCENTO / 100 AS valor_comissao,
                    d.COD_DESPADIC,
                    d.DESPESA AS descricao,
                    d.VLRTOTFIN AS total,
                    c.COD_FUNCIONARIO,
                    p.NOME AS nome_funcionario,
                    o.DTFECH AS data,
                    o.COD_ORDEM,
                    o.OBSORDEM
                FROM COMPROD c
                INNER JOIN DESPADIC d ON d.COD_DESPADIC = c.COD_GERADOR
                INNER JOIN FUNCIONARIO f ON f.COD_FUNC = c.COD_FUNCIONARIO
                INNER JOIN PESSOA p ON p.COD_PESSOA = f.COD_PESSOA
                INNER JOIN ORDEM o ON o.COD_ORDEM = d.COD_GERADOR
                WHERE d.VLRTOTFIN IS NOT NULL
                  AND d.VLRFINAL > 0
                  AND o.DTFECH IS NOT NULL
                  AND o.DTFECH >= ?
                  AND o.DTFECH <= ?
            """
            cursor.execute(sql_servicos, (data_inicio_str, data_fim_str))
            rows_servicos = cursor.fetchall()

        finally:
            cursor.close()

    # ----------------------------------------------------------------
    # 3. Agrupar por funcionário
    # ----------------------------------------------------------------
    funcionarios: dict[int, dict] = defaultdict(lambda: {
        "nome": "",
        "produtos": [],
        "servicos": [],
    })

    for row in rows_produtos:
        cod_func = row[6]
        funcionarios[cod_func]["nome"] = row[7] or ""
        funcionarios[cod_func]["produtos"].append(
            ComissaoProduto(
                cod_comprod=row[0],
                percento=_to_float(row[1]),
                valor_comissao=_to_float(row[2]),
                cod_itprodord=row[3],
                descricao=row[4],
                total=_to_float(row[5]),
                cod_funcionario=cod_func,
                nome_funcionario=row[7] or "",
                data=row[8],
                cod_ordem=row[9],
                obs_ordem=row[10],
            )
        )

    for row in rows_servicos:
        cod_func = row[6]
        funcionarios[cod_func]["nome"] = row[7] or ""
        funcionarios[cod_func]["servicos"].append(
            ComissaoServico(
                cod_comprod=row[0],
                percento=_to_float(row[1]),
                valor_comissao=_to_float(row[2]),
                cod_despadic=row[3],
                descricao=row[4],
                total=_to_float(row[5]),
                cod_funcionario=cod_func,
                nome_funcionario=row[7] or "",
                data=row[8],
                cod_ordem=row[9],
                obs_ordem=row[10],
            )
        )

    resultado: list[ComissaoFuncionario] = []
    total_geral = Decimal("0")

    for cod_func, dados in funcionarios.items():
        total_prod = sum((Decimal(str(p.valor_comissao)) for p in dados["produtos"]), Decimal("0"))
        total_serv = sum((Decimal(str(s.valor_comissao)) for s in dados["servicos"]), Decimal("0"))
        total_func = total_prod + total_serv
        total_geral += total_func

        resultado.append(
            ComissaoFuncionario(
                cod_funcionario=cod_func,
                nome_funcionario=dados["nome"],
                total_comissao_produtos=float(total_prod.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                total_comissao_servicos=float(total_serv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                total_comissao=float(total_func.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                produtos=dados["produtos"],
                servicos=dados["servicos"],
            )
        )

    resultado.sort(key=lambda f: f.total_comissao, reverse=True)

    return ComissoesResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        total_geral=float(total_geral.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        funcionarios=resultado,
    )
