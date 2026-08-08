import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder


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
