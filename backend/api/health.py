from fastapi import APIRouter
router=APIRouter()
@router.get('/api/health')
def health(): return {"ok":True,"data":{"service":"chen-an-zhi-yan","status":"ok"},"error":None}
