from app.schemas.servico import ServicoCreate
from typing import List


"VLRFINAL == valorunitario"
"vlrtotfin == valor total com desconto"

sql_serv_insert = """
            INSERT INTO DESPADIC (GERADOR, 
                               COD_GERADOR, 
                               DESPESA, 
                               VLRFINAL, 
                               QTD,
                               VLRTOTFIN, 
                               DESCONTO, 
                               COD_EQUIPE, 
                               COD_FUNCIONARIO) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING COD_DESPADIC
        """


def inserir_servicos(cursor, servicos:List[ServicoCreate], cod_ordem: int ):
    for serv in servicos:
        valor_total = serv.quantidade * serv.valorUnitario
        valor_desconto = (valor_total*serv.desconto)/100
        total_com_desconto = valor_total - valor_desconto
        cursor.execute(sql_serv_insert, ('ORDEM', 
                                  cod_ordem,
                                  serv.descricao, 
                                  serv.valorUnitario, 
                                  serv.quantidade, 
                                  total_com_desconto, 
                                  serv.desconto,
                                  serv.cod_equipe,
                                  serv.cods_vendedores[0]
                                  ))
        cod_serv = cursor.fetchone()[0]

        for cod_vendedor in serv.cods_vendedores:

            sql_percento_funcionario = """
                            SELECT COMISSAO_VVSER FROM FUNCARGO WHERE COD_FUNCIONARIO = ?
            """

            cursor.execute(sql_percento_funcionario, (cod_vendedor,))

            porcentagem = cursor.fetchone()[0]

            slq_comissao = """
                INSERT INTO COMPROD (COD_GERADOR, COD_FUNCIONARIO, PERCENTO, TIPO) 
                                    VALUES (?, ?, ?, ?)
            """
            cursor.execute(slq_comissao, (cod_serv, cod_vendedor, 
                                          porcentagem/len(serv.cods_vendedores), 
                                          'COMOSSERV'))