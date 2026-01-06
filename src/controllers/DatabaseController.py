from .BaseController import BaseController
from typing import List, Optional, Any, Dict

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
except Exception:  # pragma: no cover
    create_engine = None  # type: ignore
    Engine = Any  # type: ignore
    text = None  # type: ignore


class DatabaseController(BaseController):

    def __init__(self, connection_string: str):
        super().__init__()
        self.connection_string = connection_string
        self.engine: Optional[Engine] = None

    def connect(self) -> bool:
        if create_engine is None:
            return False
        try:
            self.engine = create_engine(self.connection_string)
            # quick test connection
            with self.engine.connect() as conn:
                _ = conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self.engine = None
            return False

    def extract_by_tables(self, tables: List[str], limit_per_table: int = 1000) -> List[Dict[str, Any]]:
        if not self.engine or text is None:
            return []
        rows: List[Dict[str, Any]] = []
        with self.engine.connect() as conn:
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT * FROM {table} LIMIT :lim"), {"lim": limit_per_table})
                    cols = list(result.keys())
                    for r in result.fetchall():
                        row_dict = {c: r[idx] for idx, c in enumerate(cols)}
                        row_dict["_table_name"] = table  # Add table name for tracking
                        rows.append(row_dict)
                except Exception:
                    continue
        return rows

    def extract_by_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.engine or text is None:
            return []
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query), params or {})
                cols = list(result.keys())
                return [{c: r[idx] for idx, c in enumerate(cols)} for r in result.fetchall()]
            except Exception:
                return []

    def rows_to_documents(self, rows: List[Dict[str, Any]], table_name: Optional[str] = None) -> List[str]:
        documents: List[str] = []
        for row in rows:
            # Get table name from row if available, otherwise use provided table_name
            tbl_name = row.pop("_table_name", None) or table_name
            parts = [f"{k}: {row[k]}" for k in row.keys() if not k.startswith("_")]
            prefix = f"[table={tbl_name}] " if tbl_name else ""
            documents.append(prefix + "; ".join(parts))
        return documents


