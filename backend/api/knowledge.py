from fastapi import APIRouter, HTTPException
from backend.services import knowledge
router=APIRouter()
@router.get('/api/knowledge/search')
def search(q: str=''):
    return knowledge.search(q)
@router.get('/api/knowledge/{file}')
def get_file(file: str):
    try: return {"file":file,"content":knowledge.get_file(file)}
    except FileNotFoundError: raise HTTPException(404,"knowledge file not found")
