from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, rates, climate, elevation, conductors, lines, study_cases
from app.core.config import settings
from app.infrastructure.database import engine, Base
from app.infrastructure import orm_models
from app.infrastructure.clients.http_client import startup, shutdown 


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()                                    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await shutdown()                                   
    await engine.dispose()


app = FastAPI(
    title       = settings.api_title,
    version     = settings.api_version,
    description = settings.api_description,
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.cors_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Público
app.include_router(auth.router,        prefix="/api/v1")

# Protegidos
app.include_router(conductors.router,  prefix="/api/v1/conductors")
app.include_router(lines.router,       prefix="/api/v1/lines")
app.include_router(study_cases.router, prefix="/api/v1/study-cases")
app.include_router(rates.router,       prefix="/api/v1/rates")
app.include_router(climate.router,     prefix="/api/v1/climate")
app.include_router(elevation.router,   prefix="/api/v1/elevation")