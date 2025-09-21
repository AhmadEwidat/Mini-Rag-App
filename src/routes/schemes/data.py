from pydantic import BaseModel
from typing import Optional

class ProccessRequest(BaseModel):
    file_id: Optional[str] =None
    chunk_size: Optional[int] = 100  
    overlap: Optional[int] = 20
    do_reset: Optional[int] = 0