
from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime
from app.database import get_connection
from app.utils.auth import verificar_token
from app.utils.db_utils import get_user_db
from app.schemas.equipe import EquipeResponsavel

from typing import List



router = APIRouter(prefix="/equipes", tags=["Equipes"])


@router.get("", response_model=List[EquipeResponsavel])
def listar_equipes(token: dict = Depends(verificar_token)):
    

    usuario_id = token.get("sub")
    caminho_banco = get_user_db(int(usuario_id))

    conn = get_connection(caminho_banco)
    cursor = conn.cursor()

    try:
        sql = """
            SELECT COD_EQUIPE, DESCRICAO FROM EQUIPE    
            """
        cursor.execute(sql)
        rows = cursor.fetchall()
        equipes = []
        for r in rows:
            equipes.append({
                "cod_equipe": r[0],
                "nome": r[1]
            })

        return equipes

    finally:
        cursor.close()
        conn.close()