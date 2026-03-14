# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routes.clientes import router as clientes_router
from app.routes.veiculos import router as veiculos_router
from app.routes.ordens import router as ordens_router
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router
from app.routes.vendedores import router as vendedores_router
from app.routes.equipes import router as equipes_router
from app.routes.produtos import router as produtos_router
from app.routes.uploads import router as uploads_router
from app.routes.ct_pagar import router as ct_pagar_router
from app.routes.ct_receber import router as ct_receber_router


app = FastAPI()

# Garante que o diretório de uploads existe antes de montar os arquivos estáticos
os.makedirs("uploads/temp", exist_ok=True)
os.makedirs("static", exist_ok=True)

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
app.include_router(ct_pagar_router)
app.include_router(ct_receber_router)


@app.get("/admin", include_in_schema=False)
def admin_redirect():
    return RedirectResponse(url="/static/admin_users.html")


# Montagem de arquivos estáticos (deve vir após os routers)
app.mount("/static/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")
