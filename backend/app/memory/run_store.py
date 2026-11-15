import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "runs.db"


class RunStore:
    """
    SQLite-backed persistent store for pipeline runs and metrics.
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = str(db_path or DB_PATH)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    total_latency_ms REAL DEFAULT 0,
                    retries_used INTEGER DEFAULT 0,
                    files_count INTEGER DEFAULT 0,
                    execution_success INTEGER DEFAULT 0,
                    data TEXT NOT NULL,
                    metrics TEXT
                )
                """
            )
            conn.commit()

    def save_run(
        self,
        run_id: str,
        prompt: str,
        data: Dict[str, Any],
        metrics: Optional[Dict[str, Any]] = None,
        status: str = "completed",
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        total_latency = 0.0
        retries = data.get("retries_used", 0)
        files_count = len(data.get("files", data.get("project", {})))
        exec_success = 1 if (data.get("execution") or {}).get("success") else 0

        if metrics:
            total_latency = metrics.get("total_latency", 0.0)
            retries = metrics.get("retries_used", retries)
            files_count = metrics.get("files_generated", files_count)
            exec_success = 1 if metrics.get("execution_success") else 0

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO runs (
                    id, prompt, status, created_at,
                    total_latency_ms, retries_used, files_count,
                    execution_success, data, metrics
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    prompt,
                    status,
                    now,
                    total_latency,
                    retries,
                    files_count,
                    exec_success,
                    json.dumps(data),
                    json.dumps(metrics) if metrics else None,
                ),
            )
            conn.commit()

        return {
            "id": run_id,
            "prompt": prompt,
            "status": status,
            "created_at": now,
            "total_latency_ms": total_latency,
            "retries_used": retries,
            "files_count": files_count,
            "execution_success": bool(exec_success),
            "data": data,
            "metrics": metrics,
        }

    def list_runs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, prompt, status, created_at,
                       total_latency_ms, retries_used, files_count,
                       execution_success
                FROM runs
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "prompt": row["prompt"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "total_latency_ms": row["total_latency_ms"],
                    "retries_used": row["retries_used"],
                    "files_count": row["files_count"],
                    "execution_success": bool(row["execution_success"]),
                }
                for row in rows
            ]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, prompt, status, created_at,
                       total_latency_ms, retries_used, files_count,
                       execution_success, data, metrics
                FROM runs
                WHERE id = ?
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "prompt": row["prompt"],
                "status": row["status"],
                "created_at": row["created_at"],
                "total_latency_ms": row["total_latency_ms"],
                "retries_used": row["retries_used"],
                "files_count": row["files_count"],
                "execution_success": bool(row["execution_success"]),
                "data": json.loads(row["data"]),
                "metrics": json.loads(row["metrics"]) if row["metrics"] else None,
            }

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT metrics FROM runs WHERE metrics IS NOT NULL
                """
            )
            rows = cur.fetchall()
            return [json.loads(row["metrics"]) for row in rows]
