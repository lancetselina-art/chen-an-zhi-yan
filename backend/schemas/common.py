from typing import Any
from pydantic import BaseModel

class Envelope(BaseModel):
    ok: bool
    data: Any = None
    error: Any = None
    request_id: str
