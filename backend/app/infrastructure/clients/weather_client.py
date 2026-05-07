import httpx

class OpenMeteoClient:
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

    async def fetch_hourly_data(self, lat: float, lon: float, start_date: str, end_date: str) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,wind_speed_10m,shortwave_radiation",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(self.url, params=params)
            resp.raise_for_status()
            return resp.json()


class NasaPowerClient:
    
    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    async def fetch_daily_data(self, lat: float, lon: float, start_date: str, end_date: str) -> dict:
        params = {
            "parameters": "T2M,WS10M,ALLSKY_SFC_SW_DWN",
            "community": "RE",
            "longitude": lon,
            "latitude": lat,
            "start": start_date.replace("-", ""),
            "end": end_date.replace("-", ""),
            "format": "JSON",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(self.url, params=params)
            resp.raise_for_status()
            return resp.json()