import os
import time
from firebird.driver import connect
from queue import Queue, Empty
from threading import Lock


# tempo em segundos que uma conexão pode ficar ociosa antes de validar
IDLE_TIMEOUT = 300.0


class PooledConn:
    """Wrapper para guardar a conexão e o timestamp do último uso"""
    def __init__(self, conn):
        self.conn = conn
        self.last_used = time.monotonic()

    def touch(self):
        self.last_used = time.monotonic()

    def is_stale(self) -> bool:
        return (time.monotonic() - self.last_used) > IDLE_TIMEOUT

    def is_alive(self) -> bool:
        try:
            self.conn.ping()
            return True
        except Exception:
            return False


class FirebirdPool:

    def __init__(self, dsn, user, password, min_size=1, max_size=5, max_retries=3, retry_delay=1.0):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._pool = Queue(maxsize=max_size)
        self._created = 0
        self._lock = Lock()

        for _ in range(min_size):
            wrapped = self._create_connection()
            self._pool.put(wrapped)

    def _create_connection(self) -> PooledConn:
        conn = connect(
            self.dsn,
            user=self.user,
            password=self.password,
            charset="UTF8"
        )
        return PooledConn(conn)

    def _discard(self, wrapped: PooledConn):
        """Fecha e desconta do contador"""
        with self._lock:
            self._created -= 1
        try:
            wrapped.conn.close()
        except Exception:
            pass

    def acquire(self) -> PooledConn:
        for attempt in range(self.max_retries):

            # tenta pegar uma conexão do pool
            while not self._pool.empty():
                try:
                    wrapped = self._pool.get_nowait()

                    # só faz ping se a conexão ficou ociosa por muito tempo
                    if wrapped.is_stale() and not wrapped.is_alive():
                        self._discard(wrapped)
                        continue

                    return wrapped

                except Empty:
                    break

            # pool vazio — tenta criar nova
            try:
                with self._lock:
                    if self._created < self.max_size:
                        wrapped = self._create_connection()
                        self._created += 1
                        return wrapped

                # pool cheio — aguarda devolução
                wrapped = self._pool.get(timeout=5)

                if wrapped.is_stale() and not wrapped.is_alive():
                    self._discard(wrapped)
                    continue

                return wrapped

            except Exception:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue

        raise Exception(f"Banco indisponível após {self.max_retries} tentativas")

    def release(self, wrapped: PooledConn):
        wrapped.touch()  # atualiza timestamp ao devolver
        self._pool.put(wrapped)

    def close_all(self):
        while not self._pool.empty():
            try:
                wrapped = self._pool.get_nowait()
                wrapped.conn.close()
            except Exception:
                pass

    def connection(self):
        return PooledConnection(self)


class PooledConnection:

    def __init__(self, pool: FirebirdPool):
        self.pool = pool
        self.wrapped = None

    def __enter__(self):
        self.wrapped = self.pool.acquire()
        return self.wrapped.conn  # expõe só a conexão para o repository

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            try:
                self.wrapped.conn.rollback()
                self.pool.release(self.wrapped)
            except Exception:
                self.pool._discard(self.wrapped)
        else:
            try:
                self.wrapped.conn.commit()
            except Exception:
                self.pool._discard(self.wrapped)
                return
            self.pool.release(self.wrapped)


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
                    max_size=5,
                    max_retries=3,
                    retry_delay=1.0
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
                    max_size=3,
                    max_retries=3,
                    retry_delay=1.0
                )

    return _client_pools[dsn]