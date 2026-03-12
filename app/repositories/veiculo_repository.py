from app.database import get_client_pool
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate
from fastapi import HTTPException


def buscar_veiculo_por_placa(dsn: str, placa: str):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:
            sql = """
                SELECT COD_EQUIPAMENTO, PLACA, DESCRICAO, ANO, COR, MARCA
                FROM equipamento
                WHERE UPPER(REPLACE(PLACA, '-', '')) = UPPER(?)
            """
            cursor.execute(sql, (placa,))
            return cursor.fetchone()
        finally:
            cursor.close()


def inserir_veiculo(dsn: str, veiculo: VeiculoCreate):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()
        try:

            sql = """
                  UPDATE codigo SET cod_equipamento = cod_equipamento + 1

                  returning cod_equipamento
            """

            cursor.execute(sql)

            cod_veiculo = cursor.fetchone()[0]

            sql = """
                INSERT INTO equipamento (cod_equipamento, PLACA, COD_CLIENTE, DESCRICAO, ANO, KMATUAL, MARCA, MODELO, COR, CHASSI)
                VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            desc = f"{veiculo.marca}/{veiculo.modelo}"
            cursor.execute(sql, (cod_veiculo,
                                 veiculo.placa, 
                                 veiculo.cod_cliente, 
                                 desc, 
                                 veiculo.ano, 
                                 veiculo.kmatual,
                                 veiculo.marca,
                                 veiculo.modelo,
                                 veiculo.cor,
                                 veiculo.chassi))
            conn.commit()
            return cod_veiculo
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()



def atualizar_veiculo(dsn: str, veiculo: VeiculoUpdate):
    with get_client_pool(dsn).connection() as conn:
        cursor = conn.cursor()

        setQuery = ""
        if veiculo.cod_cliente:
            setQuery += f"COD_CLIENTE = ? "
        try:
            sql = f"""
                UPDATE equipamento SET KMATUAL = COALESCE(?, KMATUAL), {setQuery}
                WHERE COD_EQUIPAMENTO = ?
                RETURNING COD_EQUIPAMENTO
            """
            if setQuery:
                cursor.execute(sql, (veiculo.kmatual, veiculo.cod_cliente, veiculo.cod_veiculo))
            else:
                cursor.execute(sql, (veiculo.kmatual, veiculo.cod_veiculo))
            resultado = cursor.fetchone()

            if not resultado:
                raise HTTPException(status_code=404, detail="Veículo não encontrado")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()