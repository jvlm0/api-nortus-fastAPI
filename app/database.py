import os
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

        for _ in range(min_size):
            conn = self._create_connection()
            self._pool.put(conn)

    def _create_connection(self):
        # _created só deve ser incrementado dentro de um lock no caller
        conn = connect(
            self.dsn,
            user=self.user,
            password=self.password,
            charset="UTF8"
        )
        return conn

    def acquire(self):
        try:
            return self._pool.get_nowait()
        except Empty:
            with self._lock:
                if self._created < self.max_size:
                    conn = self._create_connection()
                    self._created += 1       # protegido pelo lock
                    return conn
            return self._pool.get()          # aguarda se pool está cheio

    def release(self, conn):
        self._pool.put(conn)

    def close_all(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass

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
        if exc_type is not None:
            try:
                self.conn.rollback()
                self.pool.release(self.conn)
            except Exception:
                with self.pool._lock:
                    self.pool._created -= 1
                try:
                    new_conn = self.pool._create_connection()
                    with self.pool._lock:
                        self.pool._created += 1
                    self.pool.release(new_conn)
                except Exception:
                    pass
        else:
            try:
                # garante que não há transação pendente antes de devolver
                self.conn.commit()
            except Exception:
                pass
            self.pool.release(self.conn)


_app_pool: FirebirdPool | None = None
_client_pools: dict[str, FirebirdPool] = {}
_lock = Lock()


def get_app_pool() -> FirebirdPool:
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


def get_client_pool(dsn: str) -> FirebirdPool:
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