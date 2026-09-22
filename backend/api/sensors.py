from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from backend.services import sensors
from backend.schemas.sensors import SensorAnalyzeRequest
router=APIRouter()
@router.post('/api/sensors/features')
async def make_features(
    request: Request,
    file: UploadFile | None = File(None),
):
    try:
        if file:
            rows=__import__('pandas').read_csv(file.file).to_dict('records')
            form = await request.form()
            context={'stage': str(form.get('stage', '')), 'work_type': str(form.get('work_type', '')),
                     'city': str(form.get('city', '')), 'is_night': str(form.get('is_night', 'false')).lower() == 'true'}
        else:
            payload = await request.json()
            rows=(payload or {}).get('rows',[]); context=payload or {}
        return sensors.features(rows, context)
    except Exception as e: raise HTTPException(400, str(e))
@router.post('/api/sensors/analyze')
def analyze(payload: SensorAnalyzeRequest):
    return sensors.analyze(payload.features, payload.context, payload.demo_mode)
