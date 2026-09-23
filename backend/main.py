import json
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.api import health, vision, sensors, knowledge, reports, model_settings
from backend.services.runtime import settings
app=FastAPI(title='chen-an-zhi-yan')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(health.router); app.include_router(vision.router); app.include_router(sensors.router); app.include_router(knowledge.router); app.include_router(reports.router); app.include_router(model_settings.router)
@app.get('/api/config')
def config(): return settings()

def _error_response(status_code: int, message: str, request_id: str):
    return JSONResponse({'ok': False, 'data': None, 'error': {'message': message}, 'request_id': request_id}, status_code=status_code)

@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    rid = request.headers.get('x-request-id') or uuid.uuid4().hex
    detail = exc.detail if isinstance(exc.detail, str) else '请求失败'
    return _error_response(exc.status_code, detail, rid)

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    rid = request.headers.get('x-request-id') or uuid.uuid4().hex
    return _error_response(422, '请求参数格式不正确', rid)

@app.middleware('http')
async def envelope(request: Request, call_next):
    rid=request.headers.get('x-request-id') or uuid.uuid4().hex
    try:
        response=await call_next(request)
        if response.headers.get('content-type','').startswith('application/json'):
            body=b''
            async for chunk in response.body_iterator: body += chunk
            data=json.loads(body)
            if response.status_code >= 400:
                if isinstance(data, dict) and {'ok', 'data', 'error'} <= data.keys():
                    data['request_id'] = rid
                else:
                    data = {'ok': False, 'data': None, 'error': {'message': '请求失败'}, 'request_id': rid}
            elif not isinstance(data,dict) or not {'ok','data','error'} <= data.keys():
                data={'ok':True,'data':data,'error':None}
            data['request_id']=rid
            return JSONResponse(data,status_code=response.status_code)
        return response
    except Exception:
        return JSONResponse({'ok':False,'data':None,'error':{'message':'服务器内部错误'},'request_id':rid},status_code=500)
