from typing import List

from app.schemas.produto import ItemProdutoCreate, ItemProdutoResponse
from app.schemas.equipe import Vendedor
from app.db_utils.vendedor_db import buscar_vendedores

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

            cursor.execute(sql, (cod_estoque, 
                                 cod_ordem, 
                                 prod.quantidade, 
                                 prod.valorUnitario, 
                                 prod.desconto, 
                                 valor_total, 
                                 data, 
                                 prod.cods_vendedores[0], 
                                 val_custo, 
                                 coef_div, 
                                 val_comp, 
                                 luc_moe, 
                                 luc_per, 
                                 val_rep, 
                                 comissao, 
                                 operacao, 
                                 icms, 
                                 base_icms, 
                                 valor_icms, 
                                 cod_cst))


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



         
def buscar_produtos(cursor, cod_ordem: int):



    sql =  """
        Select itprodord.cod_itprodord, 
               subproduto.descricao, 
               subproduto.marca,
               itprodord.qtd, 
               itprodord.desconto, 
               itprodord.vlrunit
               
        From itprodord left Join estoque on itprodord.cod_estoque = estoque.cod_estoque 
        Left Join subproduto on estoque.cod_subprod = subproduto.cod_subproduto 
        Where itprodord.cod_ordem = ? 
    """  

    cursor.execute(sql, (cod_ordem,)) 
     
    rows = cursor.fetchall()
    
    produtos: list[ItemProdutoResponse] = []
    
    for r in rows:
            
        vendedores = buscar_vendedores(cursor, r[0])

        prod =  ItemProdutoResponse(
                        cod_itemProduto= r[0],
                        nome=r[1] if r[1] is not None else "",
                        marca=r[2] if r[2] is not None else "",
                        quantidade=r[3] if r[3] is not None else 0,
                        desconto=r[4] if r[4] is not None else 0,
                        valorUnitario=r[5] if r[5] is not None else 0,
                        vendedores=vendedores)
        
        produtos.append(prod)

    return produtos
    

def deletar_produtos(cursor, cod_produtos_removidos: List[int]):

    total = 0
    for cod_prod in cod_produtos_removidos:

        sql = """
            DELETE FROM COMPROD WHERE COD_GERADOR = ? AND TIPO = 'COMOS'
        """

        cursor.execute(sql, (cod_prod,))

        sql = """
            DELETE FROM ITPRODORD WHERE COD_ITPRODORD = ?
            RETURNING TOTAL
        """

        cursor.execute(sql, (cod_prod,))

        valor_total_produto = cursor.fetchone()[0]

        if valor_total_produto is not None:
            total += valor_total_produto
        
    return total

def deletar_produtos_ordem(cursor, cod_ordem):

    sql = """
        SELECT COD_ITPRODORD FROM ITPRODORD WHERE COD_ORDEM = ?
    """

    cursor.execute(sql, (cod_ordem,))

    rows = cursor.fetchall()

    cod_itens_del = []
    for r in rows:
        cod_itens_del.append(r[0])

    deletar_produtos(cursor, cod_itens_del)


def get_count_prod_ordem(cursor, cod_ordem) -> int:

    sql = """
        SELECT count(*) FROM ITPRODORD WHERE COD_ORDEM = ?    
    """

    cursor.execute(sql, (cod_ordem,))

    return cursor.fetchone()[0]

    
