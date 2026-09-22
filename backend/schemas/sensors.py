from typing import Any
from pydantic import BaseModel, Field
class SensorRows(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=1)
    stage: str = ""
    work_type: str = ""
    city: str = ""
    is_night: bool = False
class SensorAnalyzeRequest(BaseModel):
    features: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    demo_mode: bool = True
