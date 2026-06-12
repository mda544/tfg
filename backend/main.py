from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    auth,
    conductors,
    lines,
    study_cases,
    calculations,
    climate,
    elevation,
)
from app.domain.exceptions import (
    EntityNotFoundError,
    EntityConflictError,
    ValidationError,
    CalculationError,
    ExternalServiceError,
)
from app.core.config import settings
from app.infrastructure.database import engine, Base
from app.infrastructure import orm_models  
from app.infrastructure.clients.http_client import startup, shutdown
from app.seed import seed_default_conductors


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_conductors()
    yield
    await shutdown()
    await engine.dispose()


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Traducción de excepciones de dominio -> HTTP 


@app.exception_handler(EntityNotFoundError)
async def not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(EntityConflictError)
async def conflict_handler(request: Request, exc: EntityConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.message,
            "errors": exc.errors,
            "warnings": exc.warnings,
        },
    )


@app.exception_handler(CalculationError)
async def calculation_handler(request: Request, exc: CalculationError):
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(ExternalServiceError)
async def external_service_handler(request: Request, exc: ExternalServiceError):
    return JSONResponse(status_code=503, content={"detail": exc.message})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url.path} — {type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# Routers

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(conductors.router, prefix="/api/v1/conductors")
app.include_router(lines.router, prefix="/api/v1/lines")
app.include_router(study_cases.router, prefix="/api/v1/study-cases")
app.include_router(
    calculations.router,
    prefix="/api/v1/study-cases/{case_id}/calculations",
)
app.include_router(climate.router, prefix="/api/v1/climate")
app.include_router(elevation.router, prefix="/api/v1/elevation")
