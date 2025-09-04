from pydantic import BaseModel
from typing import Optional

class proccessRequest(BaseModel):
    file_id: str
    chunk_size: Optional[int] = 100  
    overlap: Optional[int] = 20
    do_reset: Optional[int] = 0