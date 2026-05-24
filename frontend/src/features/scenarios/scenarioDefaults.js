export const SEASONS = ["verano", "invierno", "primavera", "otono"];

export const DEFAULT_SCENARIOS = {
  verano: { temp: 38, viento: 0.6, angulo: 90, radiacion: 900 },
  invierno: { temp: 5, viento: 3.0, angulo: 90, radiacion: 200 },
  primavera: { temp: 18, viento: 2.5, angulo: 90, radiacion: 650 },
  otono: { temp: 20, viento: 2.0, angulo: 90, radiacion: 500 },
};

export const ESTACION_META = {
  verano: {
    label: "Verano",
    descripcion: "Condición más restrictiva",
    color: "coral",
  },
  invierno: {
    label: "Invierno",
    descripcion: "Mayor capacidad de transporte",
    color: "blue",
  },
  primavera: {
    label: "Primavera",
    descripcion: "Condición intermedia",
    color: "green",
  },
  otono: {
    label: "Otoño",
    descripcion: "Condición intermedia",
    color: "amber",
  },
};
