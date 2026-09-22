from fastapi import APIRouter, UploadFile, File, Form
from backend.services.vision import analyze
router=APIRouter()
@router.post('/api/vision/analyze')
async def endpoint(image: UploadFile=File(...), stage: str=Form(''), work_type: str=Form(''), is_night: bool=Form(False), demo_mode: bool=Form(True)):
    return analyze(await image.read(), image.content_type or 'jpeg', {'stage':stage,'work_type':work_type,'is_night':is_night}, demo_mode)
