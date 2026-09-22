from typing import Any
from pydantic import BaseModel, Field
class ReportRequest(BaseModel):
    data: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] | None = None
