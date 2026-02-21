from typing import List

from app.schemas.produto import ItemProdutoCreate, ProdutoResponse

from decimal import Decimal


def inserir_produtos(cursor, produtos: List[ItemProdutoCreate], cod_ordem: int, data):
    for prod in produtos:
            

        
            sql = """
                    select CSTTRIB from loja where cod_loja = ?
            """

            cursor.execute(sql, (1,))

            cod_cst = cursor.fetchone()[0]


            quantidadeDecimal = Decimal(str(prod.quantidade))

            valorUnitarioDecimal = Decimal(str(prod.valorUnitario))

            descontoDecimal = Decimal(str(prod.desconto))

            
            sql = """
                SELECT COD_ESTOQUE, VALCUSTO, VALREP, ICMS, COEFDIV FROM ESTOQUE WHERE COD_SUBPROD = ?
            """

            cursor.execute(sql, (prod.cod_subproduto,))
            result = cursor.fetchone()
            cod_estoque= result[0]
            val_custo = result[1]
            val_rep = result[2]
            icms = result[3]
            luc_moe = valorUnitarioDecimal*quantidadeDecimal - val_custo*quantidadeDecimal
            operacao = 'VND'
            base_icms = valorUnitarioDecimal*quantidadeDecimal - (valorUnitarioDecimal*quantidadeDecimal*quantidadeDecimal)/Decimal("100")
            valor_icms = Decimal("0")
            if icms is not None:
                valor_icms = (base_icms * icms)/Decimal("100")

            

            coef_div = result[4]

            val_comp = val_custo*quantidadeDecimal

            luc_per = luc_moe/(valorUnitarioDecimal*quantidadeDecimal)

            comissao = 0

            valor_total = valorUnitarioDecimal*quantidadeDecimal

           



            sql = """
                  INSERT INTO ITPRODORD (COD_ESTOQUE, COD_ORDEM, QTD, VLRUNIT, DESCONTO, TOTAL, DATA, COD_FUNCIONARIO, VALCUSTO, COEFDIV, VALCOMP, LUCMOE, LUCPER, VALREP, COMISSAO, OPERACAO, ALIQICMS, BASEICMS, VLRICMS, COD_CST) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                  RETURNING COD_ITPRODORD
            """

            cursor.execute(sql, (cod_estoque, cod_ordem, prod.quantidade, prod.valorUnitario, quantidadeDecimal, valor_total, data, prod.cods_vendedores[0], val_custo, coef_div, val_comp, luc_moe, luc_per, val_rep, comissao, operacao, icms, base_icms, valor_icms, cod_cst))


            cod_itprodord = cursor.fetchone()[0]


            for cod_vendedor in prod.cods_vendedores:

                sql_percento_funcionario = """
                                SELECT COMISSAO_VVSER FROM FUNCARGO WHERE COD_FUNCIONARIO = ?
                """

                cursor.execute(sql_percento_funcionario, (cod_vendedor,))

                porcentagem = cursor.fetchone()[0]

                slq_comissao = """
                    INSERT INTO COMPROD (COD_GERADOR, COD_FUNCIONARIO, PERCENTO, TIPO) 
                                        VALUES (?, ?, ?, ?)
                """
                cursor.execute(slq_comissao, (cod_itprodord, cod_vendedor, 
                                              porcentagem/len(prod.cods_vendedores), 
                                              'COMOS'))



         


