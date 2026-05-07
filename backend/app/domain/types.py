from typing import Literal

# Fuente de verdad única para el tipo Season.
# Importar desde aquí en todos los módulos que lo necesiten.
Season = Literal["verano", "otono", "invierno", "primavera"]

ESTACIONES: list[Season] = ["verano", "otono", "invierno", "primavera"]