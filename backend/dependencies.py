import uuid
from fastapi import Request
def request_id(request: Request):
    return request.headers.get("x-request-id") or uuid.uuid4().hex
