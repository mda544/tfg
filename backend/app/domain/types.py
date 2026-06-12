from typing import Literal

Season = Literal["verano", "otono", "invierno", "primavera"]

SEASONS: list[Season] = ["verano", "otono", "invierno", "primavera"]

# Fuente de los datos de elevación del trazado
# "dem"  — obtenida del servicio Copernicus DEM GLO-30 (~30m resolución)
# "file" — tomada directamente del archivo Excel (col Z) o GeoJSON (coord Z)
# "none" — sin elevación, cálculo a 0 m s.n.m.
ElevationSource = Literal["dem", "file", "none"]

# Fuente climática histórica para los escenarios estacionales
# "openmeteo" — Copernicus ERA5-Land via Open-Meteo (~9 km resolución)
# "nasa"      — NASA POWER MERRA-2 (~50 km resolución)
# "manual"    — valores introducidos directamente por el usuario
ClimateSource = Literal["openmeteo", "nasa", "manual"]

# Régimen de convección del modelo térmico IEEE 738-2012
# Los umbrales son los definidos por la norma
# "forced_high" — viento >= 2.0 m/s
# "forced_low"  — viento >= 0.5 m/s y < 2.0 m/s
# "natural"     — viento <  0.5 m/s (convección natural)
ConvMode = Literal["forced_high", "forced_low", "natural"]
