from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    file_id: str = None
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0


class DBConnectRequest(BaseModel):
    db_type: str  # e.g. postgresql
    host: str = "localhost"
    port: int = 5432
    username: str
    password: str
    database: str

    def to_connection_string(self) -> str:
        return f"{self.db_type}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DBProcessRequest(BaseModel):
    asset_id: Optional[str] = None
    tables: Optional[list[str]] = None
    custom_query: Optional[str] = None
    limit_per_table: Optional[int] = 1000
    chunk_size: Optional[int] = 100
    overlap_size: Optional[int] = 20
    do_reset: Optional[int] = 0