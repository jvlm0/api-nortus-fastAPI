from decimal import Decimal

from fastapi import HTTPException
from app.database import get_client_pool
from app.db_utils.produto_db import buscar_produtos, deletar_produtos, inserir_produtos, get_count_prod_ordem, deletar_produtos_ordem
from app.db_utils.servico_db import buscar_servicos, inserir_servicos, deletar_servicos, get_count_serv_ordem, deletar_servicos_ordem
from datetime import datetime
from app.schemas.cliente import ClienteResponse
from app.schemas.ordem import OrdemResponse, OrdemCreate, OrdemUpdate, ProblemaOrdem, OrdemFechadaResponse, OrdensFechadasResponse, OrdemFaturadaResponse, OrdensFaturadasResponse, OrdemFaturadaResponse, OrdensFaturadasResponse, OrdemFaturadaResponse, OrdensFaturadasResponse
from app.schemas.veiculo import VeiculoResponse
from app.utils.ordem_calc import calculaTotal
from app.utils.ordem_utils import split_obs, recuperar_problemas, formatar_problemas

def inserir_ordem(dsn: str, ordem: OrdemCreate):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        dt = datetime.now()
        data = dt.strftime("%Y-%m-%d")
        hora = dt.strftime("%H:%M:%S")

        STATUS  = "ABERTO"
        MONITOR = "INICIADO"
        COD_LOJA = 1

        texto_problema, texto_solucao = None, None
        if ordem.problemas is not None:
            texto_problema, texto_solucao = formatar_problemas(ordem.problemas)

        try:
            valorTotal, valorTotalServ, valorTotalProd = calculaTotal(ordem.servicos, ordem.produtos)

            cod_funcionario = None
            if valorTotalProd > 0:
                cod_funcionario = ordem.produtos[0].cods_vendedores[0]
            elif valorTotalServ > 0:
                cod_funcionario = ordem.servicos[0].cods_vendedores[0]

            cursor.execute(
                """
                INSERT INTO ORDEM (
                    COD_CLIENTE, COD_EQUIPAMENTO, DTABERT, HRABERT, OBSORDEM,
                    STATUS, MONITOR, COD_LOJA, TOTSERV, TOTORD, TOTPROD,
                    COD_VENDEDOR, PROBREC, SOLUCAO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING COD_ORDEM
                """,
                (
                    ordem.cod_cliente, ordem.cod_veiculo, data, hora,
                    ordem.observacao, STATUS, MONITOR, COD_LOJA,
                    valorTotalServ, valorTotal, valorTotalProd,
                    cod_funcionario, texto_problema, texto_solucao
                )
            )
            cod_ordem = cursor.fetchone()[0]

            if ordem.servicos is not None:
                inserir_servicos(cursor, ordem.servicos, cod_ordem)
            if ordem.produtos is not None:
                inserir_produtos(cursor, ordem.produtos, cod_ordem, data)

            # Commit explícito antes de sair para liberar locks o mais cedo possível
            conn.commit()
            return cod_ordem

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cursor.close()


def listar_ordens_faturadas(dsn: str, data_inicio, data_fim) -> OrdensFaturadasResponse:
    from decimal import Decimal, ROUND_HALF_UP

    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    d.COD_DOCFISCORD,
                    d.COD_ORDEM,
                    COALESCE(d.VLRTOTPROD, 0) + COALESCE(d.VLRTOTSERV, 0) AS total,
                    o.OBSORDEM,
                    pc.NOME AS nome_cliente,
                    e.PLACA,
                    e.DESCRICAO AS modelo,
                    o.DTFECH
                FROM DOCFISORD d
                INNER JOIN ORDEM o ON o.COD_ORDEM = d.COD_ORDEM
                INNER JOIN CLIENTE cl ON cl.COD_CLIENTE = o.COD_CLIENTE
                INNER JOIN PESSOA pc ON pc.COD_PESSOA = cl.COD_PESSOA
                INNER JOIN EQUIPAMENTO e ON e.COD_EQUIPAMENTO = o.COD_EQUIPAMENTO
                WHERE (COALESCE(d.VLRTOTPROD, 0) + COALESCE(d.VLRTOTSERV, 0)) > 0
                  AND o.DTFECH >= ?
                  AND o.DTFECH <= ?
                ORDER BY o.DTFECH DESC
            """
            cursor.execute(sql, (data_inicio_str, data_fim_str))
            rows = cursor.fetchall()

            ordens: list[OrdemFaturadaResponse] = []
            soma = Decimal("0")

            for r in rows:
                total = float(Decimal(str(r[2])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                soma += Decimal(str(r[2]))

                ordens.append(
                    OrdemFaturadaResponse(
                        cod_docfiscord=r[0],
                        cod_ordem=r[1],
                        total=total,
                        observacao=r[3],
                        nome_cliente=r[4] or "",
                        placa=r[5],
                        modelo=r[6],
                    )
                )

            return OrdensFaturadasResponse(
                data_inicio=data_inicio_str,
                data_fim=data_fim_str,
                total_ordens=len(ordens),
                soma_total=float(soma.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                data=ordens,
            )

        finally:
            cursor.close()


def listar_ordens(dsn: str, page: int, page_size: int):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        
        try:

            inicio = (page - 1) * page_size + 1
            fim = page * page_size
            total = 0


            sql_count = """
                SELECT count(*)
                FROM ordem
                LEFT JOIN cliente ON ordem.cod_cliente = cliente.cod_cliente
                LEFT JOIN pessoa ON cliente.cod_pessoa = pessoa.cod_pessoa
                LEFT JOIN equipamento ON ordem.cod_equipamento = equipamento.cod_equipamento
                WHERE ordem.status = 'ABERTO'
            """

            cursor.execute(sql_count)
            total = cursor.fetchone()[0]



            sql = f"""
                SELECT ordem.cod_ordem,
                       ordem.status,
                       ordem.OBSORDEM,
                       cliente.cod_cliente,
                       pessoa.nome,
                       pessoa.telrel,
                       pessoa.cpfcnpj,
                       equipamento.cod_equipamento,
                       equipamento.descricao,
                       equipamento.placa,
                       equipamento.ano,
                       equipamento.kmatual,
                       ORDEM.PROBREC,
                       ORDEM.SOLUCAO
                FROM ordem
                LEFT JOIN cliente ON ordem.cod_cliente = cliente.cod_cliente
                LEFT JOIN pessoa ON cliente.cod_pessoa = pessoa.cod_pessoa
                LEFT JOIN equipamento ON ordem.cod_equipamento = equipamento.cod_equipamento
                WHERE ordem.status = 'ABERTO'
                ORDER BY ordem.dtabert DESC, ordem.hrabert DESC
                ROWS {inicio} TO {fim}
            """

            cursor.execute(sql)
            rows = cursor.fetchall()

            ordens: list[OrdemResponse] = []

            for r in rows:

                
            
                ordem = OrdemResponse(
                    cod_ordem= r[0], 
                    status=r[1], 
                    observacao=r[2],
                    cliente=ClienteResponse(COD_PESSOA=r[3], nome=r[4], telefone=r[5], cpfcnpj= r[6]), 
                    veiculo=VeiculoResponse(cod_veiculo= r[7], modelo = r[8], placa= r[9], ano= r[10], kmatual=r[11]),
                    problemas=recuperar_problemas(r[12], r[13])
                )

                ordens.append(ordem)
            return {
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": ordens
            }
        finally:
            cursor.close()

def update_ordem(dsn: str, ordem: OrdemUpdate):

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        texto_problema, texto_solucao = None, None
        if (ordem.problemas is not None):
            texto_problema, texto_solucao = formatar_problemas(ordem.problemas)
    
        try:
            valorTotal, valorTotalServ, valorTotalProd = calculaTotal(ordem.servicos, ordem.produtos)
            
            cod_funcionario = None
            if valorTotalProd > 0:
                cod_funcionario = ordem.produtos[0].cods_vendedores[0]
            elif valorTotalServ > 0:
                cod_funcionario = ordem.servicos[0].cods_vendedores[0]
            
            totalProdRemovido, totalServRemovido = 0, 0
            if ordem.servicosRemovidos != None:
                totalServRemovido += deletar_servicos(cursor, ordem.servicosRemovidos)
            
            if ordem.produtosRemovidos != None:
                totalProdRemovido += deletar_produtos(cursor, ordem.produtosRemovidos)
            
            totalRemovido = totalProdRemovido + totalServRemovido

            diffProd = Decimal(str(valorTotalProd)) - Decimal(str(totalProdRemovido))
            diffServ = Decimal(str(valorTotalServ)) - Decimal(str(totalServRemovido))
            diffTotal = Decimal(str(valorTotal)) - Decimal(str(totalRemovido))

            sql = """
                UPDATE ordem set cod_cliente = ?, cod_equipamento = ?, OBSORDEM = ?, TOTSERV = COALESCE(TOTSERV, 0) + ?, TOTORD = COALESCE(TOTORD, 0) + ?, TOTPROD = COALESCE(TOTPROD, 0) + ?, COD_VENDEDOR = COALESCE(?, COD_VENDEDOR), PROBREC = ?, SOLUCAO = ?
                WHERE COD_ORDEM = ?
                RETURNING cod_ordem;
            """
            cursor.execute(sql, (ordem.cod_cliente, ordem.cod_veiculo, ordem.observacao, diffServ, diffTotal, diffProd, cod_funcionario, texto_problema, texto_solucao, ordem.cod_ordem))
    
            resultado = cursor.fetchone()[0]
    
            if not resultado:
                raise HTTPException(status_code=404, detail="Ordem não encontrada")
            
            if ordem.servicos != None:
                inserir_servicos(cursor, ordem.servicos, ordem.cod_ordem)
            if ordem.produtos != None:
                inserir_produtos(cursor, ordem.produtos, ordem.cod_ordem, datetime.now().strftime("%Y-%m-%d"))
            
    
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


def get_ordem(dsn, cod_ordem: int):
    
    with get_client_pool(dsn).connection() as conn:    
        cursor = conn.cursor()
            
        try:
            sql = """
                SELECT ordem.cod_ordem,
                       ordem.status,
                       ordem.OBSORDEM,
                       cliente.cod_cliente,
                       pessoa.nome,
                       pessoa.telrel,
                       pessoa.cpfcnpj,
                       equipamento.cod_equipamento,
                       equipamento.descricao,
                       equipamento.placa,
                       equipamento.ano,
                       equipamento.kmatual,
                       ordem.PROBREC,
                       ordem.SOLUCAO
                FROM ordem
                LEFT JOIN cliente ON ordem.cod_cliente = cliente.cod_cliente
                LEFT JOIN pessoa ON cliente.cod_pessoa = pessoa.cod_pessoa
                LEFT JOIN equipamento ON ordem.cod_equipamento = equipamento.cod_equipamento
                WHERE ordem.cod_ordem = ?
            """
    
            cursor.execute(sql, (cod_ordem,))
            r = cursor.fetchone()
            
    
            cliente = ClienteResponse(COD_PESSOA=r[3], nome=r[4], telefone=r[5], cpfcnpj= r[6])
    
            veiculo = VeiculoResponse(cod_veiculo= r[7], 
                                      modelo = r[8], 
                                      placa= r[9], 
                                      ano= r[10], 
                                      kmatual=r[11])
    
            ordem = OrdemResponse(cod_ordem= r[0], 
                                  status=r[1], 
                                  observacao=r[2],
                                  cliente=cliente, 
                                  veiculo=veiculo,
                                  problemas=recuperar_problemas(r[12], r[13]))
    
            ordem.servicos = buscar_servicos(cursor, ordem.cod_ordem)
            ordem.produtos = buscar_produtos(cursor, cod_ordem)
    
            return ordem
    
        finally:
            cursor.close()
    
def delete_ordem(dsn, cod_ordem: int):

    with get_client_pool(dsn).connection() as conn:    
        cursor = conn.cursor()

        try:
            sql = """
                DELETE FROM ORDEM WHERE COD_ORDEM = ?
                RETURNING COD_ORDEM
            """
            cursor.execute(sql, (cod_ordem,))
            cod = cursor.fetchone()[0]
            deletar_produtos_ordem(cursor, cod_ordem)
            deletar_servicos_ordem(cursor, cod_ordem)


            return cod

        
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


def get_count_itens(dsn, cod_ordem):
    with get_client_pool(dsn).connection() as conn:
        try:
            cursor = conn.cursor()
            count = get_count_serv_ordem(cursor, cod_ordem) + get_count_prod_ordem(cursor, cod_ordem)

            return count
        finally:
                cursor.close()


def listar_ordens_fechadas(dsn: str, data_inicio, data_fim) -> OrdensFechadasResponse:
    from datetime import date
    from decimal import Decimal, ROUND_HALF_UP

    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql = """
                SELECT
                    o.COD_ORDEM,
                    o.OBSORDEM,
                    o.DTFECH,
                    o.TOTORD,
                    cliente.COD_CLIENTE,
                    pessoa.NOME,
                    pessoa.TELREL,
                    pessoa.CPFCNPJ,
                    equipamento.COD_EQUIPAMENTO,
                    equipamento.DESCRICAO,
                    equipamento.PLACA,
                    equipamento.ANO,
                    equipamento.KMATUAL
                FROM ORDEM o
                LEFT JOIN CLIENTE cliente ON o.COD_CLIENTE = cliente.COD_CLIENTE
                LEFT JOIN PESSOA pessoa ON cliente.COD_PESSOA = pessoa.COD_PESSOA
                LEFT JOIN EQUIPAMENTO equipamento ON o.COD_EQUIPAMENTO = equipamento.COD_EQUIPAMENTO
                WHERE o.STATUS = 'FECHADO'
                  AND o.DTFECH >= ?
                  AND o.DTFECH <= ?
                ORDER BY o.DTFECH DESC
            """
            cursor.execute(sql, (data_inicio_str, data_fim_str))
            rows = cursor.fetchall()

            ordens: list[OrdemFechadaResponse] = []
            soma = Decimal("0")

            for r in rows:
                total = float(Decimal(str(r[3])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) if r[3] else 0.0
                soma += Decimal(str(r[3])) if r[3] else Decimal("0")

                ordens.append(
                    OrdemFechadaResponse(
                        cod_ordem=r[0],
                        observacao=r[1],
                        data_fechamento=r[2],
                        total_ordem=total,
                        cliente=ClienteResponse(
                            COD_PESSOA=r[4],
                            nome=r[5],
                            telefone=r[6],
                            cpfcnpj=r[7],
                        ),
                        veiculo=VeiculoResponse(
                            cod_veiculo=r[8],
                            modelo=r[9],
                            placa=r[10],
                            ano=r[11],
                            kmatual=r[12],
                        ),
                    )
                )

            return OrdensFechadasResponse(
                data_inicio=data_inicio_str,
                data_fim=data_fim_str,
                total_ordens=len(ordens),
                soma_total=float(soma.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                data=ordens,
            )

        finally:
            cursor.close()