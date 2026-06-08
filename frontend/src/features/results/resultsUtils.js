export const SEASON_LABEL = {
  verano:    "Verano",
  invierno:  "Invierno",
  primavera: "Primavera",
  otono:     "Otoño",
};

export const SEASON_COLOR = {
  verano:    "#D85A30",
  invierno:  "#185FA5",
  primavera: "#3B6D11",
  otono:     "#BA7517",
};

export const ELEVATION_SOURCE_LABEL = {
  dem:  "Modelo Digital de Elevaciones (DEM)",
  none: "Sin altitud (0 m)",
};

export const CLIMATE_SOURCE_LABEL = {
  openmeteo: "Copernicus ERA5 (Open-Meteo)",
  nasa:      "MERRA-2 (NASA POWER)",
  manual:    "Manual",
};

export const CONV_MODE_LABEL = {
  forced_high: "Forzada alta",
  forced_low:  "Forzada baja",
  natural:     "Natural",
};

export function ampacityColor(a) {
  if (a < 500)  return { bg: "#FCEBEB", text: "#791F1F" };
  if (a < 800)  return { bg: "#FAEEDA", text: "#633806" };
  if (a < 1100) return { bg: "#EAF3DE", text: "#27500A" };
  return              { bg: "#E1F5EE", text: "#085041" };
}