# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.clientes import router as clientes_router
from app.routes.veiculos import router as veiculos_router
from app.routes.ordens import router as ordens_router
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router


app = FastAPI()

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
