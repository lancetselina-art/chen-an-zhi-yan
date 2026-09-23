from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from backend.services.vision import analyze
from backend.services.vision import demo_asset_path
router=APIRouter()
@router.post('/api/vision/analyze')
async def endpoint(image: UploadFile | None=File(None), stage: str=Form(''), work_type: str=Form(''), is_night: bool=Form(False), demo_mode: bool=Form(True)):
    if not demo_mode and image is None:
        raise HTTPException(400, '请上传现场图片')
    image_bytes = await image.read() if image else None
    return analyze(image_bytes, image.content_type if image else 'image/jpeg', {'stage':stage,'work_type':work_type,'is_night':is_night}, demo_mode)


@router.get('/api/vision/demo/input')
def demo_input():
    return FileResponse(demo_asset_path('input'), media_type='image/jpeg')


@router.get('/api/vision/demo/overlay')
def demo_overlay():
    return FileResponse(demo_asset_path('overlay'), media_type='image/jpeg')
