/**
 * Formatea un timestamp del backend (UTC) a la hora local del navegador.
 */
export function formatDateTime(iso) {
  if (!iso) return "";

  // Limpiar el formato por si viene raro de la BD
  let normalized = iso.replace(" ", "T");

  if (/[+-]\d{2}$/.test(normalized)) {
    normalized += ":00";
  }

  // Si no tiene "Z" ni offset, le ponemos la "Z" para obligar a JS a entender que es UTC
  const hasOffset =
    /[+-]\d{2}:\d{2}$/.test(normalized) || normalized.endsWith("Z");
  if (!hasOffset) {
    normalized += "Z";
  }

  const d = new Date(normalized);

  if (isNaN(d.getTime())) return iso; // Si falla, devuelve el string original

  // Convertir a hora de España (sumará las horas de tu zona horaria automáticamente)
  return d.toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
