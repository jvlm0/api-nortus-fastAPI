from fastapi import APIRouter, Query, HTTPException, Depends
from app.database import get_connection
from app.utils.texto import tem_letra
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token

router = APIRouter(prefix="/veiculos", tags=["Veículos"])


@router.get("/{placa}")
def buscar_veiculo(placa: str, token: dict = Depends(verificar_token)):
    
    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    
    conn = get_connection(caminho_banco)

    cursor = conn.cursor()

    try:
        sql = """
            SELECT COD_EQUIPAMENTO, PLACA, DESCRICAO, ANO
            FROM equipamento
            WHERE UPPER(REPLACE(PLACA, '-', '')) = UPPER(?)
        """
        cursor.execute(sql, (placa,))

        resultado = cursor.fetchone()

        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")

        return {
            "cod_veiculo": resultado[0],
            "placa": resultado[1],
            "modelo": resultado[2],
            "ano": resultado[3]
        }

    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201)
def inserir_veiculo(veiculo: VeiculoCreate, token: dict = Depends(verificar_token)):

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    
    conn = get_connection(caminho_banco)

    cursor = conn.cursor()

    try:
       
        sql = """
            INSERT INTO equipamento (PLACA, COD_CLIENTE, DESCRICAO, ANO, KMATUAL)
            VALUES (?, ?, ?, ?, ?)
            RETURNING COD_EQUIPAMENTO
        """
        cursor.execute(sql, (veiculo.placa, veiculo.cod_cliente, veiculo.modelo, veiculo.ano, veiculo.kmatual))
        cod_veiculo = cursor.fetchone()[0]
        conn.commit()

        return {
            "status": "sucesso",
            "cod_veiculo": cod_veiculo
        }

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cursor.close()
        conn.close()



@router.patch("", status_code=200)
def atualizarVeiculo(veiculo: VeiculoUpdate, token: dict = Depends(verificar_token)):

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    
    conn = get_connection(caminho_banco)

    cursor = conn.cursor()

    try:
        sql = """
            UPDATE equipamento set MODELO = ?, ANO = ?, KMATUAL = ?
            WHERE COD_EQUIPAMENTO = ?
            RETURNING cod_equipamento, kmatual;
        """
        cursor.execute(sql, (veiculo.modelo, veiculo.ano, veiculo.kmatual, veiculo.cod_veiculo))

        resultado = cursor.fetchone()[0]
        conn.commit()

        if not resultado:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")

        return {
            "status": "sucesso"
        }

    finally:
        cursor.close()
        conn.close()