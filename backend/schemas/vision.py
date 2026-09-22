from pydantic import BaseModel
class VisionContext(BaseModel):
    stage: str
    work_type: str
    is_night: bool = False
    demo_mode: bool = True
