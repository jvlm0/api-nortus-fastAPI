from app.schemas.servico import ServicoCreate, ServicoResponse
from app.schemas.equipe import EquipeResponsavel
from typing import List

from app.db_utils.vendedor_db import buscar_vendedores


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
            

def buscar_servicos(cursor, cod_ordem):

    sql = """
        SELECT d.COD_DESPADIC,
               d.DESPESA, 
               d.QTD, 
               d.VLRFINAL, 
               d.DESCONTO, 
               d.COD_EQUIPE, 
               e.descricao FROM DESPADIC d
                INNER JOIN EQUIPE e ON d.COD_EQUIPE = e.COD_EQUIPE 
                WHERE d.COD_GERADOR = ?
    """

    cursor.execute(sql, (cod_ordem,))

    rows =  cursor.fetchall()
    services = List[ServicoResponse]
    for r in rows:
        serv = ServicoResponse(
                             cod_servico=r[0],
                             descricao=r[1],
                             quantidade=r[2],
                             valorUnitario=r[3],
                             desconto=r[4]
        )

        equipe =  EquipeResponsavel(
                                    cod_equipe=r[5],
                                    nome=r[6]
        )



        serv.equipe = equipe

        serv.vendedores = buscar_vendedores(cursor, serv.cod_servico)


def deletar_servicos(cursor, cod_servicos_removidos: List[int]):
    for cod_serv in cod_servicos_removidos:
        sql_delete_comissao = """
            DELETE FROM COMPROD WHERE COD_GERADOR = ? AND TIPO = 'COMOSSERV'
        """
        cursor.execute(sql_delete_comissao, (cod_serv,))

        sql_delete_servico = """
            DELETE FROM DESPADIC WHERE COD_DESPADIC = ?
        """
        cursor.execute(sql_delete_servico, (cod_serv,))



        

