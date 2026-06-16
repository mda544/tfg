from functools import wraps
from sqlalchemy.exc import IntegrityError, DataError
from app.domain.exceptions import EntityConflictError, EntityNotFoundError, ValidationError


def handle_db_exceptions(func):
    """
    IntegrityError FK sobre users → EntityNotFoundError (sesión expirada)
    IntegrityError FK otras       → EntityNotFoundError (referencia inválida)
    IntegrityError UNIQUE         → EntityConflictError (registro duplicado)
    DataError                     → ValidationError (dato fuera de rango)
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except IntegrityError as e:
            detail = str(e.orig).lower()
            if "foreign key" in detail:
                if "users" in detail:
                    raise EntityNotFoundError(
                        "La sesión ha expirado o el usuario no existe. Vuelve a iniciar sesión."
                    )
                raise EntityNotFoundError(
                    "Referencia no encontrada. Comprueba que los IDs son correctos."
                )
            if "unique" in detail or "duplicate" in detail:
                raise EntityConflictError("El registro ya existe.")
            raise EntityConflictError("Conflicto de integridad en la base de datos.")
        except DataError as e:
            raise ValidationError(f"Dato fuera de rango o formato incorrecto: {e.orig}")
    return wrapper