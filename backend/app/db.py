"""감사 로그용 SQLite 저장소 (stdlib sqlite3).

누가 언제 어떤 버전을 다운로드/업로드 했는지 기록한다.
임포트 시점에는 아무 것도 하지 않고, 최초 사용 시점에 lazy 하게 init 한다.
"""
import sqlite3
import threading
from pathlib import Path

# backend/app/db.py -> backend/data/audit.db
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DATA_DIR / "audit.db"

_lock = threading.Lock()
_initialized = False


def _connect() -> sqlite3.Connection:
    """SQLite 커넥션 생성. 멀티 스레드(FastAPI) 환경 대비."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init() -> None:
    """audit_log 테이블을 생성한다. idempotent (CREATE TABLE IF NOT EXISTS)."""
    global _initialized
    with _lock:
        if _initialized:
            return
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    action     TEXT NOT NULL,          -- 'download' | 'upload'
                    slug       TEXT NOT NULL,
                    version    TEXT NOT NULL,
                    user       TEXT,
                    detail     TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
        finally:
            conn.close()
        _initialized = True


def record(
    action: str,
    slug: str,
    version: str,
    user: str | None = None,
    detail: str | None = None,
) -> None:
    """감사 로그 한 줄을 기록한다. 최초 호출 시 테이블을 lazy init."""
    init()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO audit_log (action, slug, version, user, detail) "
            "VALUES (?, ?, ?, ?, ?)",
            (action, slug, version, user, detail),
        )
        conn.commit()
    finally:
        conn.close()


def list_events(limit: int = 200, slug: str | None = None) -> list[dict]:
    """최근 감사 로그를 created_at 내림차순으로 조회한다."""
    init()
    conn = _connect()
    try:
        sql = "SELECT id, action, slug, version, user, detail, created_at FROM audit_log"
        params: list = []
        if slug:
            sql += " WHERE slug = ?"
            params.append(slug)
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
