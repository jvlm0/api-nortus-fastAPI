from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime
from app.database import get_connection
from app.schemas.ordem import OrdemCreate, OrdemResponse, OrdemUpdate
from typing import List
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db


router = APIRouter(prefix="/ordens", tags=["Ordens de Serviço"])

@router.post("", status_code=201)
def inserir_ordem(ordem: OrdemCreate, token: dict = Depends(verificar_token)):

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    
    conn = get_connection(caminho_banco)

    cursor = conn.cursor()

    dt = datetime.now()

    data = dt.strftime("%Y-%m-%d")
    hora = dt.strftime("%H:%M:%S")
    observacao = (ordem.titulo or "") + " - " + (ordem.descricao or "")
    STATUS = "ABERTO"
    MONITOR = "INICIADO"
    COD_LOJA = 1 

    try:

        

        sql = """
            INSERT INTO ORDEM (COD_CLIENTE, COD_EQUIPAMENTO, DTABERT, HRABERT, OBSORDEM, STATUS, MONITOR, COD_LOJA)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING COD_ORDEM
        """
        cursor.execute(sql, (ordem.cod_cliente, ordem.cod_veiculo, data, hora, observacao, STATUS, MONITOR, COD_LOJA))
        cod_ordem = cursor.fetchone()[0]
        conn.commit()

        return {
            "status": "sucesso",
            "cod_ordem": cod_ordem
        }
    
    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cursor.close()
        conn.close()




@router.get("", response_model=List[OrdemResponse])
def listar_ordens(token: dict = Depends(verificar_token)):
    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))

    conn = get_connection(caminho_banco)
    cursor = conn.cursor()

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
        WHERE ordem.status = 'ABERTO'
        ORDER BY ordem.dtabert DESC, ordem.hrabert DESC
    """

    cursor.execute(sql)
    rows = cursor.fetchall()

    resultado = []

    for r in rows:

        titulo = r[2].split(" - ")[0] if r[2] else None
        descricao = r[2].split(" - ")[1] if r[2] and " - " in r[2] else None

        resultado.append({
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

    return resultado


@router.patch("", status_code = 200) 
def update_ordem(ordem: OrdemUpdate, token: dict = Depends(verificar_token)):

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    conn = get_connection(caminho_banco)
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
        conn.commit()

        if not resultado:
            raise HTTPException(status_code=404, detail="Ordem não encontrada")

        return {
            "status": "sucesso"
        }

    finally:
        cursor.close()
        conn.close()
