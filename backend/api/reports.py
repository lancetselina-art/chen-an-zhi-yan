from fastapi import APIRouter
from backend.schemas.reports import ReportRequest
from backend.services import reports
router=APIRouter()
@router.post('/api/reports/vision')
def vision(p: ReportRequest): return {"markdown":reports.vision(p.data,p.context)}
@router.post('/api/reports/sensor')
def sensor(p: ReportRequest): return {"markdown":reports.sensor(p.data,p.features or {},p.context)}
