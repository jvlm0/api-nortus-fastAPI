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



import os
os.environ["FIREBIRD_CLIENT"] = r"C:\Users\joaov\app-nortus\api-nortus\fbclient.dll"
from firebird.driver import connect
from queue import Queue, Empty
from threading import Lock


class FirebirdPool:

    def __init__(self, dsn, user, password, min_size=1, max_size=5):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size

        self._pool = Queue(maxsize=max_size)
        self._created = 0
        self._lock = Lock()

        # cria conexões iniciais
        for _ in range(min_size):
            conn = self._create_connection()
            self._pool.put(conn)

    def _create_connection(self):
        conn = connect(
            self.dsn,
            user=self.user,
            password=self.password,
            charset="UTF8"
        )
        self._created += 1
        return conn

    def acquire(self):
        try:
            return self._pool.get_nowait()
        except Empty:
            with self._lock:
                if self._created < self.max_size:
                    return self._create_connection()

            # espera se já atingiu o máximo
            return self._pool.get()

    def release(self, conn):
        self._pool.put(conn)

    def connection(self):
        return PooledConnection(self)


class PooledConnection:

    def __init__(self, pool):
        self.pool = pool
        self.conn = None

    def __enter__(self):
        self.conn = self.pool.acquire()
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        self.pool.release(self.conn)


_app_pool = None
_client_pools = {}
_lock = Lock()


def get_app_pool():
    global _app_pool

    if _app_pool is None:
        with _lock:
            if _app_pool is None:
                _app_pool = FirebirdPool(
                    dsn=os.getenv("DSN"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    min_size=1,
                    max_size=5
                )

    return _app_pool


def get_client_pool(dsn):
    if dsn not in _client_pools:
        with _lock:
            if dsn not in _client_pools:
                _client_pools[dsn] = FirebirdPool(
                    dsn=dsn,
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    min_size=1,
                    max_size=3
                )

    return _client_pools[dsn]