
from app.database import get_connection_app_users



def get_user_db(id: int):
    conn = get_connection_app_users()
    cur = conn.cursor()

    try:

        sql = "SELECT caminho_banco FROM USUARIO WHERE ID = ?"
        # Verifica se o username já existe
        cur.execute(sql,(id,))
        
        resultado = cur.fetchone()

        if not resultado:
            return "Banoco não encontrado"

        caminho_banco  = resultado[0]

        return caminho_banco
    
    finally:
        cur.close()
        conn.close()