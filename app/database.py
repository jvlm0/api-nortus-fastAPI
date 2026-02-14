# app/database.py
import fdb
import os

def get_connection(caminhoBanco: str):
    return fdb.connect(
        dsn=caminhoBanco,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        charset="UTF8"
    )

def get_connection_app_users():
    # Dentro do Docker, use o nome do serviço
    return fdb.connect(
        dsn=os.getenv("DSN"),
        user="SYSDBA",
        password="masterkey",
        charset="UTF8"
    )