from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends
from app.database import get_connection
from app.schemas.cliente import ClienteCreate
from app.utils.texto import tem_letra
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.get("")
def buscar_cliente(q: str = Query(..., description="Nome ou telefone"),
                   page: int = Query(1, ge=1), 
                   page_size: int = Query(10, ge=1, le=100),
                   token: dict = Depends(verificar_token)):
    
    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    
    conn = get_connection(caminho_banco)
    
    cursor = conn.cursor()

    try:
        inicio = (page - 1) * page_size + 1
        fim = page * page_size

        total = 0
        
        if tem_letra(q):
            
            sql_count = f"""
                SELECT count(*)
                FROM pessoa
                INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                WHERE CLIENTE.ATIVO = 1 AND UPPER(PESSOA.NOME) LIKE UPPER(?)
            """
            cursor.execute(sql_count, (f"%{q}%",))

            total = cursor.fetchone()[0]
            

            # 🔤 Busca por nome
            sql = f"""
                SELECT CLIENTE.COD_CLIENTE, PESSOA.NOME, PESSOA.TELREL, PESSOA.CPFCNPJ
                FROM pessoa
                INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                WHERE CLIENTE.ATIVO = 1 AND UPPER(PESSOA.NOME) LIKE UPPER(?)
                ROWS {inicio} TO {fim}
            """
            cursor.execute(sql, (f"%{q}%",))
        else:
            
            sql_count = f"""
                SELECT count(*)
                FROM pessoa
                INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                WHERE CLIENTE.ATIVO = 1 AND PESSOA.TELREL LIKE ?
            """
            cursor.execute(sql_count, (f"%{q}%",))
            total = cursor.fetchone()[0]

            # 🔢 Busca por telefone
            sql = f"""
                SELECT CLIENTE.COD_CLIENTE, PESSOA.NOME, PESSOA.TELREL, PESSOA.CPFCNPJ
                FROM pessoa
                INNER JOIN CLIENTE ON CLIENTE.COD_PESSOA =  PESSOA.COD_PESSOA
                WHERE CLIENTE.ATIVO = 1 AND PESSOA.TELREL LIKE ?
                ROWS {inicio} TO {fim}
            """
            cursor.execute(sql, (f"%{q}%",))

        resultados = cursor.fetchall()
        
        return {
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": [
                {
                    "COD_PESSOA": r[0],
                    "nome": r[1],
                    "telefone": r[2],
                    "cpfcnpj": r[3]
                }
                for r in resultados
            ]
        }

    finally:
        cursor.close()
        conn.close()


@router.post("", status_code=201)
def inserir_cliente(cliente: ClienteCreate, token: dict = Depends(verificar_token)):
    
    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))
    
    conn = get_connection(caminho_banco)
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO pessoa (NOME, TELREL, CPFCNPJ)
            VALUES (?, ?, ?)
            RETURNING COD_PESSOA
        """
        cursor.execute(sql, (cliente.nome, cliente.telefone, cliente.cpfcnpj))
        cod_pessoa = cursor.fetchone()[0]

        sql2 = """
            INSERT INTO CLIENTE (COD_PESSOA, data_cad)
            VALUES (?, ?)
            RETURNING COD_CLIENTE
        """

        cursor.execute(sql2, (cod_pessoa, datetime.now().date()))
        cod_cliente = cursor.fetchone()[0]

        conn.commit()

        return {
            "status": "sucesso",
            "cod_pessoa": cod_cliente
        }

    except Exception as e:
        conn.rollback()
        raise e

    finally:
        cursor.close()
        conn.close()
