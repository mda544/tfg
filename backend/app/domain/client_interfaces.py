from typing import Protocol


class IWeatherClient(Protocol):
    """Contrato común para cualquier proveedor de datos meteorológicos
    históricos. fetch_period devuelve los datos brutos del proveedor —
    la normalización a SeasonalPercentiles ocurre en ClimateProcessor,
    que sí necesita conocer el formato de origen."""

    async def fetch_period(
        self, lat: float, lon: float, start_date: str, end_date: str
    ) -> dict:
        """start_date / end_date en formato YYYY-MM-DD.
        Devuelve la respuesta JSON cruda del proveedor."""
        ...