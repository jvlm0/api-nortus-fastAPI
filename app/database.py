import os
import logging
import time
from firebird.driver import connect
from queue import Queue, Empty
from threading import Lock

logger = logging.getLogger(__name__)

# Quantas vezes tenta reconectar automaticamente ao adquirir uma conexão
_ACQUIRE_RETRIES = 3
# Segundos de espera entre tentativas de reconexão
_RETRY_DELAY = 0.5


class FirebirdPool:

    def __init__(self, dsn, user, password, min_size=1, max_size=5):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size

        self._pool: Queue = Queue(maxsize=max_size)
        self._created = 0
        self._lock = Lock()

        for _ in range(min_size):
            try:
                conn = self._create_connection()
                with self._lock:
                    self._created += 1
                self._pool.put(conn)
            except Exception as e:
                # Falha na conexão inicial não deve impedir a API de subir;
                # as conexões serão criadas sob demanda.
                logger.warning("Pool init: não foi possível criar conexão para %s: %s", self.dsn, e)

    # ------------------------------------------------------------------
    # Criação / validação de conexões
    # ------------------------------------------------------------------

    def _create_connection(self):
        """Cria e retorna uma nova conexão Firebird."""
        return connect(
            self.dsn,
            user=self.user,
            password=self.password,
            charset="UTF8",
        )

    def _is_alive(self, conn) -> bool:
        """
        Verifica se a conexão ainda está viva sem disparar uma transação real.
        Usa uma consulta leve específica do Firebird.
        """
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM RDB$DATABASE")
            cur.fetchone()
            cur.close()
            return True
        except Exception:
            return False

    def _discard(self, conn):
        """Fecha uma conexão morta e decrementa o contador."""
        try:
            conn.close()
        except Exception:
            pass
        with self._lock:
            self._created -= 1

    # ------------------------------------------------------------------
    # Acquire com validação e retry
    # ------------------------------------------------------------------

    def acquire(self):
        """
        Retira uma conexão do pool.

        Fluxo:
        1. Tenta pegar uma conexão disponível (sem bloquear).
        2. Se a conexão estiver morta, descarta e tenta criar uma nova.
        3. Se não houver conexão disponível E o limite não foi atingido,
           cria uma nova diretamente.
        4. Se o pool estiver no limite, aguarda até uma ser devolvida.
        5. Qualquer tentativa é feita até _ACQUIRE_RETRIES vezes antes de
           levantar o erro original.
        """
        last_exc: Exception | None = None

        for attempt in range(1, _ACQUIRE_RETRIES + 1):
            # --- tenta pegar sem bloquear ---
            conn = None
            try:
                conn = self._pool.get_nowait()
            except Empty:
                conn = None

            if conn is not None:
                if self._is_alive(conn):
                    return conn
                # conexão morta: descarta e tenta criar outra no lugar
                logger.warning(
                    "Conexão morta encontrada no pool (%s) — descartando (tentativa %d/%d).",
                    self.dsn, attempt, _ACQUIRE_RETRIES
                )
                self._discard(conn)

            # --- tenta criar uma nova conexão ---
            can_create = False
            with self._lock:
                if self._created < self.max_size:
                    self._created += 1   # reserva a vaga
                    can_create = True

            if can_create:
                try:
                    new_conn = self._create_connection()
                    return new_conn
                except Exception as e:
                    with self._lock:
                        self._created -= 1
                    last_exc = e
                    logger.warning(
                        "Falha ao reconectar ao banco %s (tentativa %d/%d): %s",
                        self.dsn, attempt, _ACQUIRE_RETRIES, e
                    )
                    if attempt < _ACQUIRE_RETRIES:
                        time.sleep(_RETRY_DELAY)
                    continue

            # --- pool cheio: aguarda uma conexão ser devolvida ---
            try:
                conn = self._pool.get(timeout=5)
                if self._is_alive(conn):
                    return conn
                self._discard(conn)
                # loop de retry continua
            except Empty:
                last_exc = last_exc or Exception(f"Pool esgotado para {self.dsn}")

        raise last_exc or Exception(f"Não foi possível obter conexão com {self.dsn}")

    # ------------------------------------------------------------------
    # Release com validação
    # ------------------------------------------------------------------

    def release(self, conn):
        """
        Devolve a conexão ao pool.
        Se estiver morta, descarta em vez de devolver.
        """
        if self._is_alive(conn):
            self._pool.put(conn)
        else:
            logger.warning("Conexão morta ao devolver ao pool (%s) — descartando.", self.dsn)
            self._discard(conn)

    # ------------------------------------------------------------------

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
    """Context manager que adquire/libera conexões do pool automaticamente."""

    def __init__(self, pool: FirebirdPool):
        self.pool = pool
        self.conn = None

    def __enter__(self):
        self.conn = self.pool.acquire()
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        if self.conn is None:
            return

        if exc_type is not None:
            # Houve exceção: tenta rollback (pode já ter sido feito no repositório)
            try:
                self.conn.rollback()
            except Exception:
                pass
        else:
            # Commit seguro: se o repositório já comitou, o Firebird ignora
            # um commit numa transação limpa (sem ops pendentes), então é idempotente.
            try:
                self.conn.commit()
            except Exception:
                pass

        self.pool.release(self.conn)
        self.conn = None


# ---------------------------------------------------------------------------
# Pools singleton
# ---------------------------------------------------------------------------

_app_pool: FirebirdPool | None = None
_client_pools: dict[str, FirebirdPool] = {}
_pools_lock = Lock()


def get_app_pool() -> FirebirdPool:
    global _app_pool

    if _app_pool is None:
        with _pools_lock:
            if _app_pool is None:
                _app_pool = FirebirdPool(
                    dsn=os.getenv("DSN"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    min_size=1,
                    max_size=5,
                )
    return _app_pool


def get_client_pool(dsn: str) -> FirebirdPool:
    if dsn not in _client_pools:
        with _pools_lock:
            if dsn not in _client_pools:
                _client_pools[dsn] = FirebirdPool(
                    dsn=dsn,
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    min_size=0,   # bancos remotos: não pré-conecta
                    max_size=3,
                )
    return _client_pools[dsn]
