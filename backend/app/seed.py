"""
Seed de datos de referencia.
Se ejecuta en el lifespan de la aplicación tras create_all.
Es idempotente — usa INSERT ... ON CONFLICT DO NOTHING para no duplicar.
"""

import uuid
from sqlalchemy import text
from app.infrastructure.database import AsyncSessionLocal

# UUID fijos y estables para el catálogo estándar.
SEED_CONDUCTORS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "owner_id": None,  # NULL → conductor global, visible para todos
        "name": "LA-110 (Hawk)",
        "description": "Conductor de aluminio-acero 110 mm² — uso frecuente en distribución.",
        "diameter_mm": 21.78,
        "r_ac_75_ohm_km": 0.119,
        "r_ac_25_ohm_km": 0.101,
        "emissivity": 0.5,
        "absorptivity": 0.5,
        "max_temp_c": 85.0,
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "owner_id": None,
        "name": "LA-280 (Condor)",
        "description": "Conductor de aluminio-acero 280 mm² — transporte en alta tensión.",
        "diameter_mm": 27.72,
        "r_ac_75_ohm_km": 0.072,
        "r_ac_25_ohm_km": 0.061,
        "emissivity": 0.5,
        "absorptivity": 0.5,
        "max_temp_c": 90.0,
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "owner_id": None,
        "name": "LA-380 (Gull)",
        "description": "Conductor de aluminio-acero 380 mm² — alta capacidad.",
        "diameter_mm": 25.4,
        "r_ac_75_ohm_km": 0.089,
        "r_ac_25_ohm_km": 0.076,
        "emissivity": 0.5,
        "absorptivity": 0.5,
        "max_temp_c": 90.0,
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "owner_id": None,
        "name": "LA-455 (Cardinal)",
        "description": "Conductor de aluminio-acero 455 mm² — muy alta capacidad.",
        "diameter_mm": 30.42,
        "r_ac_75_ohm_km": 0.059,
        "r_ac_25_ohm_km": 0.05,
        "emissivity": 0.5,
        "absorptivity": 0.5,
        "max_temp_c": 90.0,
    },
]


async def seed_default_conductors() -> None:
    """Inserta los conductores estándar si no existen. Idempotente."""
    async with AsyncSessionLocal() as db:
        for c in SEED_CONDUCTORS:
            await db.execute(
                text("""
                    INSERT INTO conductors (
                        id, owner_id, name, description,
                        diameter_mm, r_ac_75_ohm_km, r_ac_25_ohm_km,
                        emissivity, absorptivity, max_temp_c,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :owner_id, :name, :description,
                        :diameter_mm, :r_ac_75_ohm_km, :r_ac_25_ohm_km,
                        :emissivity, :absorptivity, :max_temp_c,
                        NOW(), NOW()
                    )
                    ON CONFLICT (id) DO NOTHING
                """),
                c,
            )
        await db.commit()
    print(f"[seed] {len(SEED_CONDUCTORS)} conductores estándar verificados.")
