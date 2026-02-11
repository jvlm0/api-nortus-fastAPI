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
    host = os.getenv("FIREBIRD_HOST", "firebird")
    database = os.getenv("FIREBIRD_DATABASE", "APPUSERS.FDB")
    
    return fdb.connect(
        dsn=f"{host}:/firebird/data/{database}",
        user="SYSDBA",
        password="masterkey",
        charset="UTF8"
    )