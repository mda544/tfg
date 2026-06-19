class AmpacityGISError(Exception):
    """Excepción base del dominio AmpacityGIS."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class EntityNotFoundError(AmpacityGISError):
    """El recurso solicitado no existe o no pertenece al usuario."""

    pass


class EntityConflictError(AmpacityGISError):
    """El recurso ya existe."""

    pass


class ValidationError(AmpacityGISError):
    """Los datos de entrada no cumplen las reglas del dominio."""

    def __init__(
        self, message: str, errors: list[str] = None, warnings: list[str] = None
    ):
        self.errors = errors or []
        self.warnings = warnings or []
        super().__init__(message)


class CalculationError(AmpacityGISError):
    """Error durante la ejecución del modelo térmico."""

    pass


class ExternalServiceError(AmpacityGISError):
    """Fallo en un servicio externo — DEM, ERA5 o NASA POWER.
    El servicio no está disponible o ha devuelto una respuesta inesperada."""

    pass
