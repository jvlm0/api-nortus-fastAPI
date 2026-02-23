
from app.database import get_app_pool



def get_user_db(id: int):

    with get_app_pool().connection() as conn:
    
        cur = conn.cursor()

        try:

            sql = "SELECT caminho_banco FROM USUARIO WHERE ID = ?"
            # Verifica se o username já existe
            cur.execute(sql,(id,))

            resultado = cur.fetchone()

            if not resultado:
                return "Banco não encontrado"

            caminho_banco  = resultado[0]

            return caminho_banco

        finally:
            cur.close()