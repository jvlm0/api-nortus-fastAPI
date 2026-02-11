from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials
from app.database import get_connection_app_users
from app.utils.auth import verificar_senha, criar_tokens, renovar_access_token, security
from app.utils.security import verify_password

router = APIRouter(prefix="/auth", tags=["Autenticação"])

class LoginRequest(BaseModel):
    username: str
    senha: str

@router.post("/login")
def login(credenciais: LoginRequest):
    conn = get_connection_app_users()
    cursor = conn.cursor()
    
    try:
        sql = "SELECT id, username, senha_hash, caminho_banco FROM USUARIO WHERE username = ?"
        cursor.execute(sql, (credenciais.username,))
        resultado = cursor.fetchone()
        
        if not resultado or not verify_password(credenciais.senha, resultado[2]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha incorretos"
            )
        
        data = {
            "sub": str(resultado[0]),
            "username": resultado[1]
        }

        access_token, refresh_token = criar_tokens(data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "usuario": resultado[1]
        }
    
    finally:
        cursor.close()
        conn.close()

@router.post("/refresh")
def refresh(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Endpoint para renovar o access token"""
    novo_access_token = renovar_access_token(credentials)
    
    return {
        "access_token": novo_access_token,
        "token_type": "bearer"
    }