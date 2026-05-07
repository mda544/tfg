from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calculos, climate, dem

app = FastAPI(
    title="Pypacity API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculos.router, prefix="/api/v1/calcular")
app.include_router(climate.router,  prefix="/api/v1/climatologia")
app.include_router(dem.router,      prefix="/api/v1/dem")
