# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes.clientes import router as clientes_router
from app.routes.veiculos import router as veiculos_router
from app.routes.ordens import router as ordens_router
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router
from app.routes.vendedores import router as vendedores_router
from app.routes.equipes import router as equipes_router
from app.routes.produtos import router as produtos_router
from app.routes.uploads import router as uploads_router


app = FastAPI()

# Garante que o diretório de uploads existe antes de montar os arquivos estáticos
os.makedirs("uploads/temp", exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEV
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clientes_router)
app.include_router(veiculos_router)
app.include_router(ordens_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(vendedores_router)
app.include_router(equipes_router)
app.include_router(produtos_router)
app.include_router(uploads_router)