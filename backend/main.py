from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes import (
    auth,
    conductors,
    lines,
    study_cases,
    rates,
    climate,
    elevation,
)
from app.core.config import settings
from app.infrastructure.database import engine, Base
from app.infrastructure import orm_models
from app.infrastructure.clients.http_client import startup, shutdown
from app.seed import seed_default_conductors

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


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

# Registrar el limiter y el handler de error 429
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Público
app.include_router(auth.router, prefix="/api/v1/auth")

# Protegidos
app.include_router(conductors.router, prefix="/api/v1/conductors")
app.include_router(lines.router, prefix="/api/v1/lines")
app.include_router(study_cases.router, prefix="/api/v1/study-cases")
app.include_router(rates.router, prefix="/api/v1/rates")
app.include_router(climate.router, prefix="/api/v1/climate")
app.include_router(elevation.router, prefix="/api/v1/elevation")
