
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime
from typing import List


from app.database import get_connection
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from app.schemas.equipe import Vendedor



router = APIRouter(prefix="/vendedores", tags=["Vendedores"])


@router.get("", response_model=List[Vendedor])
def listar_vendedores(token: dict = Depends(verificar_token)):
    

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))

    conn = get_connection(caminho_banco)
    cursor = conn.cursor()


    try:

        sql = """
            SELECT f.COD_FUNC, p.NOME
                    FROM FUNCIONARIO f
                    INNER JOIN PESSOA p ON f.COD_PESSOA = p.COD_PESSOA
                    WHERE f.COD_PESSOA IS NOT NULL;
        """
        
        cursor.execute(sql)
        rows = cursor.fetchall()
        vendedores = []
        for r in rows:
            vendedores.append({
                "cod_vendedor": r[0],
                "nome": r[1]
            })

        return vendedores


    finally:
        cursor.close()
        conn.close()




