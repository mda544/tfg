from typing import Literal

Season = Literal["verano", "otono", "invierno", "primavera"]
SEASONS: list[Season] = ["verano", "otono", "invierno", "primavera"]

# "dem"  — se usó un modelo digital de elevaciones (DEM)
# "none" — sin elevación, cálculo a 0 m s.n.m.
ElevationSource = Literal["dem", "none"]

# Fuente climática histórica para pre-rellenar los escenarios estacionales.
ClimateSource = Literal["openmeteo", "nasa", "manual"]

# Modo de convección del cálculo IEEE 738.
# "forced_high" — viento >= 2.0 m/s
# "forced_low"  — viento >= 0.5 m/s y < 2.0 m/s
# "natural"     — viento < 0.5 m/s (convección natural)
ConvMode = Literal["forced_high", "forced_low", "natural"]
