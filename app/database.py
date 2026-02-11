# app/database.py
import fdb

def get_connection(caminhoBanco = "localhost:C:\\Multisistemas\\Bancos\\bs.GDB"):
    return fdb.connect(
        dsn=caminhoBanco,
        user="SYSDBA",
        password="masterkey",
        charset="UTF8"
    )

def get_connection_app_users():
    return fdb.connect(
        dsn = "localhost:C:\\Multisistemas\\Bancos\\APPUSERS.FDB",
        user="SYSDBA",
        password="masterkey",
        charset="UTF8"
    )