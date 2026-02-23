from fastapi import HTTPException
from app.database import get_client_pool
from app.db_utils.produto_db import buscar_produtos, deletar_produtos, inserir_produtos
from app.db_utils.servico_db import buscar_servicos, inserir_servicos, deletar_servicos
from datetime import datetime
from app.schemas.cliente import ClienteResponse
from app.schemas.ordem import OrdemResponse
from app.schemas.ordem import OrdemResponse
from app.schemas.veiculo import VeiculoResponse
from app.utils.ordem_calc import calculaTotal
from app.utils.ordem_utils import split_obs


def inserir_ordem(dsn: str, ordem): 
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        dt = datetime.now()

        data = dt.strftime("%Y-%m-%d")
        hora = dt.strftime("%H:%M:%S")
        observacao = (ordem.titulo or "") + " - " + (ordem.descricao or "")
        STATUS = "ABERTO"
        MONITOR = "INICIADO"
        COD_LOJA = 1 

        try:

            valorTotal, valorTotalServ = calculaTotal(ordem.servicos)

            sql = """
                INSERT INTO ORDEM (COD_CLIENTE, COD_EQUIPAMENTO, DTABERT, HRABERT, OBSORDEM, STATUS, MONITOR,   COD_LOJA, TOTSERV, TOTORD)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING COD_ORDEM
            """
            cursor.execute(sql, (ordem.cod_cliente, ordem.cod_veiculo, data, hora, observacao, STATUS, MONITOR,     COD_LOJA, valorTotalServ, valorTotal))
            cod_ordem = cursor.fetchone()[0]

            if (ordem.servicos != None):
                inserir_servicos(cursor, ordem.servicos, cod_ordem)
            if ordem.produtos != None:
                inserir_produtos(cursor, ordem.produtos, cod_ordem, data)



            conn.commit()

            return cod_ordem

        except Exception as e:
            conn.rollback()
            raise e

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
                       equipamento.kmatual
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

            ordens = []

            for r in rows:

                titulo, descricao = split_obs(r[2])

                ordens.append({
                    "cod_ordem": r[0],
                    "status": r[1],
                    "titulo": titulo,
                    "descricao": descricao,
                    "cliente": {
                        "COD_PESSOA": r[3],
                        "nome": r[4],
                        "telefone": r[5],
                        "cpfcnpj": r[6]
                    },
                    "veiculo": {
                        "cod_veiculo": r[7],
                        "modelo": r[8],
                        "placa": r[9],
                        "ano": r[10],
                        "kmatual": r[11]
                    }
                })
            return {
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": ordens
            }
        finally:
            cursor.close()

def update_ordem(dsn: str, ordem):

    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        observacao = (ordem.titulo or "") + " - " + (ordem.descricao or "")
    
        try:
        
            
            sql = """
                UPDATE ordem set cod_cliente = ?, cod_equipamento = ?, OBSORDEM = ?
                WHERE COD_ORDEM = ?
                RETURNING cod_ordem;
            """
            cursor.execute(sql, (ordem.cod_cliente, ordem.cod_veiculo, observacao, ordem.cod_ordem))
    
            resultado = cursor.fetchone()[0]
    
            if not resultado:
                raise HTTPException(status_code=404, detail="Ordem não encontrada")
            
            if ordem.servicos != None:
                inserir_servicos(cursor, ordem.servicos, ordem.cod_ordem)
            if ordem.produtos != None:
                inserir_produtos(cursor, ordem.produtos, ordem.cod_ordem, datetime.now().strftime("%Y-%m-%d"))
            
            if ordem.servicosRemovidos != None:
                deletar_servicos(cursor, ordem.servicosRemovidos)
            
            if ordem.produtosRemovidos != None:
                deletar_produtos(cursor, ordem.produtosRemovidos)
            
            conn.commit()
    
            
    
            return True
    
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
                       equipamento.kmatual
                FROM ordem
                LEFT JOIN cliente ON ordem.cod_cliente = cliente.cod_cliente
                LEFT JOIN pessoa ON cliente.cod_pessoa = pessoa.cod_pessoa
                LEFT JOIN equipamento ON ordem.cod_equipamento = equipamento.cod_equipamento
                WHERE ordem.cod_ordem = ?
            """
    
            cursor.execute(sql, (cod_ordem,))
            r = cursor.fetchone()
            
            titulo, descricao = split_obs(r[2])
    
            cliente = ClienteResponse(COD_PESSOA=r[3], nome=r[4], telefone=r[5], cpfcnpj= r[6])
    
            veiculo = VeiculoResponse(cod_veiculo= r[7], 
                                      descricao = r[8], 
                                      placa= r[9], 
                                      ano= r[10], 
                                      kmatual=r[11])
    
            ordem = OrdemResponse(cod_ordem= r[0], 
                                  status=r[1], 
                                  titulo=titulo, 
                                  descricao= descricao, 
                                  cliente=cliente, 
                                  veiculo=veiculo)
    
            ordem.servicos = buscar_servicos(cursor, ordem.cod_ordem)
            ordem.produtos = buscar_produtos(cursor, cod_ordem)
    
            return ordem
    
        finally:
            cursor.close()
    