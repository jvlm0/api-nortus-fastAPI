from fastapi import APIRouter, Query, HTTPException, Depends
from app.database import get_connection
from app.utils.db_utils import get_user_db
from app.utils.auth import verificar_token
from app.schemas.produto import ProdutoResponse


router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("")
def buscar_produto(q: str = Query(..., description="Nome do produto"),
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


        sql_count = f"""
                SELECT count(*)
                FROM SUBPRODUTO
                WHERE SUBPRODUTO.ATIVO = 'S' AND UPPER(SUBPRODUTO.DESCRICAO) LIKE UPPER(?)
            """
        
        cursor.execute(sql_count, (f"%{q}%",))

        total = cursor.fetchone()[0]

        sql = f"""
                SELECT COD_SUBPRODUTO, DESCRICAO, MARCA FROM SUBPRODUTO 
                
                WHERE SUBPRODUTO.ATIVO = 'S' AND UPPER(SUBPRODUTO.DESCRICAO) LIKE UPPER(?)
                
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
                    "cod_subproduto": r[0],
                    "nome": r[1],
                    "marca": r[2]
                }
                for r in resultados
            ]
        }

    finally:
        cursor.close()
        conn.close()
