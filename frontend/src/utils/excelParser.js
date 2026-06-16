import * as XLSX from "xlsx";
import proj4 from "proj4";

function parseEuropeanNumber(value) {
  if (value === null || value === undefined) return NaN;
  let str = String(value).trim();
  if (/^-?\d+(\.\d+)?$/.test(str)) return parseFloat(str);
  str = str.replace(/,/g, ".");
  const parts = str.split(".");
  if (parts.length > 1) {
    const integerPart = parts.slice(0, -1).join("");
    const decimalPart = parts[parts.length - 1];
    return parseFloat(`${integerPart}.${decimalPart}`);
  }
  return parseFloat(str);
}

function detectCoordinateSystem(x, y) {
  return Math.abs(y) > 1000 || Math.abs(x) > 180 ? "utm" : "wgs84";
}

// eslint-disable-next-line no-unused-vars
function detectUTMZone(_easting) {
  return 30; // Península Ibérica
}

function getUTMProjection(zone, hemisphere = "N") {
  return `+proj=utm +zone=${zone} +${hemisphere === "N" ? "north" : "south"} +datum=WGS84 +units=m +no_defs`;
}

function utmToLatLon(easting, northing, zone) {
  const utmProj = getUTMProjection(zone);
  const [lon, lat] = proj4(utmProj, "EPSG:4326", [easting, northing]);
  return { lat, lon };
}

function findColumn(columns, aliases) {
  return (
    columns.find((col) =>
      aliases.some((alias) => col.trim().toLowerCase() === alias.toLowerCase()),
    ) ?? null
  );
}

export async function parseLineExcel(file, utmOptions = {}) {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: null, raw: true });

  if (!rows || rows.length === 0)
    throw new Error("El archivo Excel está vacío.");

  const columns = Object.keys(rows[0]);
  const colX = findColumn(columns, [
    "x",
    "lon",
    "longitud",
    "longitude",
    "easting",
  ]);
  const colY = findColumn(columns, [
    "y",
    "lat",
    "latitud",
    "latitude",
    "northing",
  ]);
  const colZ = findColumn(columns, [
    "z",
    "cota",
    "altitud",
    "elevation",
    "height",
  ]);
  const colNum = findColumn(columns, [
    "number",
    "numero",
    "número",
    "id",
    "num",
  ]);
  const colStation = findColumn(columns, [
    "station",
    "estacion",
    "estación",
    "pk",
  ]);
  const colComment = findColumn(columns, [
    "comment",
    "comments",
    "comentario",
    "structure",
    "structure comment",
  ]);
  const colAngle = findColumn(columns, [
    "line angle",
    "lineangle",
    "angle",
    "angulo",
  ]);

  if (!colX || !colY)
    throw new Error(
      `Columnas X/Y no encontradas. Detectadas: ${columns.join(", ")}`,
    );

  let detectedSystem = "wgs84";
  let utmZone = utmOptions.zona ?? null;

  for (const row of rows) {
    const x = parseEuropeanNumber(row[colX]);
    const y = parseEuropeanNumber(row[colY]);
    if (!isNaN(x) && !isNaN(y)) {
      detectedSystem = detectCoordinateSystem(x, y);
      if (detectedSystem === "utm" && !utmZone) utmZone = detectUTMZone(x);
      break;
    }
  }

  const coordinates = [];
  const singularPoints = [];
  const errors = [];

  rows.forEach((row, idx) => {
    let x = parseEuropeanNumber(row[colX]);
    let y = parseEuropeanNumber(row[colY]);
    const rawZ = colZ ? row[colZ] : null;
    let z = rawZ !== null ? parseEuropeanNumber(rawZ) : null;

    if (isNaN(x) || isNaN(y)) {
      errors.push(
        `Fila ${idx + 2}: X="${row[colX]}" Y="${row[colY]}" no son números válidos.`,
      );
      return;
    }

    if (x > 1000000) x = x / 1000;
    if (y > 10000000) y = y / 1000;
    if (z !== null && z > 10000) z = z / 1000;

    let point;
    if (detectedSystem === "utm") {
      try {
        point = utmToLatLon(x, y, utmZone);
      } catch {
        errors.push(
          `Fila ${idx + 2}: error reproyectando UTM→WGS84 (X=${x}, Y=${y}).`,
        );
        return;
      }
    } else {
      point = { lat: y, lon: x };
    }

    if (z !== null && !isNaN(z)) point.altitud = z;
    coordinates.push(point);

    const meta = {};
    if (colNum && row[colNum] != null) meta.number = row[colNum];
    if (colStation && row[colStation] != null) meta.station = row[colStation];
    if (colComment && row[colComment] != null) meta.comment = row[colComment];
    if (colAngle && row[colAngle] != null) meta.lineAngle = row[colAngle];
    if (z !== null && !isNaN(z)) meta.z = z;

    singularPoints.push({ ...point, ...meta });
  });

  const cleanCoordinates = coordinates.filter(
    (c) =>
      c &&
      typeof c.lat === "number" &&
      typeof c.lon === "number" &&
      !isNaN(c.lat) &&
      !isNaN(c.lon),
  );

  if (cleanCoordinates.length < 2) {
    throw new Error(
      `El Excel no contiene suficientes coordenadas válidas (leídas: ${cleanCoordinates.length}).` +
        (errors.length > 0 ? ` Pista: ${errors[0]}` : ""),
    );
  }

  return {
    tipo: "Line",
    coordinates: cleanCoordinates,
    propiedades: {
      fuente: "excel",
      sistema_original: detectedSystem,
      zona_utm: detectedSystem === "utm" ? utmZone : null,
      n_apoyos: cleanCoordinates.length,
      support_metadata: singularPoints,
    },
    advertencias: errors,
  };
}
