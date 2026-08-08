import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder


from starlette.exceptions import HTTPException as StarletteHTTPException


class FlxException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        flx_trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.flx_trace_id = flx_trace_id or str(uuid.uuid4())
        self.details = details or {}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(FlxException)
    async def flx_exception_handler(request: Request, exc: FlxException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "flxTraceId": exc.flx_trace_id,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "FLX_VALIDATION_ERROR",
                    "message": "Erro de validação nos dados fornecidos.",
                    "flxTraceId": str(uuid.uuid4()),
                    "details": {"errors": jsonable_encoder(exc.errors())},
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        code_map = {
            401: "FLX_UNAUTHORIZED",
            403: "FLX_FORBIDDEN",
            404: "FLX_NOT_FOUND",
            405: "FLX_METHOD_NOT_ALLOWED",
            409: "FLX_CONCURRENT_UPDATE",
        }
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code_map.get(exc.status_code, "FLX_ERROR"),
                    "message": str(exc.detail),
                    "flxTraceId": str(uuid.uuid4()),
                    "details": {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "FLX_INTERNAL_ERROR",
                    "message": "Ocorreu um erro interno no servidor.",
                    "flxTraceId": str(uuid.uuid4()),
                    "details": {},
                }
            },
        )
