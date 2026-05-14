import * as XLSX from "xlsx";
import proj4 from "proj4";

function parsearNumeroEuropeo(valor) {
  if (valor === null || valor === undefined) return NaN;
  let str = String(valor).trim();
  if (/^-?\d+(\.\d+)?$/.test(str)) return parseFloat(str);
  str = str.replace(/,/g, ".");
  const partes = str.split(".");
  if (partes.length > 1) {
    const enteros = partes.slice(0, -1).join("");
    const decimales = partes[partes.length - 1];
    return parseFloat(`${enteros}.${decimales}`);
  }
  return parseFloat(str);
}

function detectarSistema(x, y) {
  return Math.abs(y) > 1000 || Math.abs(x) > 180 ? "utm" : "wgs84";
}

// eslint-disable-next-line no-unused-vars
function detectarZonaUTM(_easting) {
  return 30; // Por defecto zona 30N (Península Ibérica)
}

function obtenerProyeccionUTM(zona, hemisferio = "N") {
  return `+proj=utm +zone=${zona} +${hemisferio === "N" ? "north" : "south"} +datum=WGS84 +units=m +no_defs`;
}

function utmALatLon(easting, northing, zona) {
  const projUTM = obtenerProyeccionUTM(zona);
  const [lon, lat] = proj4(projUTM, "EPSG:4326", [easting, northing]);
  return { lat, lon }; // clave canónica: lon (no lng)
}

function encontrarColumna(columnas, aliases) {
  return (
    columnas.find((col) =>
      aliases.some((alias) => col.trim().toLowerCase() === alias.toLowerCase()),
    ) ?? null
  );
}

export async function parseLineExcel(file, opcionesUTM = {}) {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: null, raw: true });

  if (!rows || rows.length === 0)
    throw new Error("El archivo Excel está vacío.");

  const columnas = Object.keys(rows[0]);
  const colX = encontrarColumna(columnas, [
    "x",
    "lon",
    "longitud",
    "longitude",
    "easting",
  ]);
  const colY = encontrarColumna(columnas, [
    "y",
    "lat",
    "latitud",
    "latitude",
    "northing",
  ]);
  const colZ = encontrarColumna(columnas, [
    "z",
    "cota",
    "altitud",
    "elevation",
    "height",
  ]);
  const colNum = encontrarColumna(columnas, [
    "number",
    "numero",
    "número",
    "id",
    "num",
  ]);
  const colStation = encontrarColumna(columnas, [
    "station",
    "estacion",
    "estación",
    "pk",
  ]);
  const colComment = encontrarColumna(columnas, [
    "comment",
    "comments",
    "comentario",
    "structure",
    "structure comment",
  ]);
  const colAngle = encontrarColumna(columnas, [
    "line angle",
    "lineangle",
    "angle",
    "angulo",
  ]);

  if (!colX || !colY)
    throw new Error(
      `Columnas X/Y no encontradas. Detectadas: ${columnas.join(", ")}`,
    );

  let sistemaDetectado = "wgs84";
  let zonaUTM = opcionesUTM.zona ?? null;

  for (const row of rows) {
    const x = parsearNumeroEuropeo(row[colX]);
    const y = parsearNumeroEuropeo(row[colY]);
    if (!isNaN(x) && !isNaN(y)) {
      sistemaDetectado = detectarSistema(x, y);
      if (sistemaDetectado === "utm" && !zonaUTM) zonaUTM = detectarZonaUTM(x);
      break;
    }
  }

  const coordenadas = [];
  const puntosSingulares = [];
  const errores = [];

  rows.forEach((row, idx) => {
    let x = parsearNumeroEuropeo(row[colX]);
    let y = parsearNumeroEuropeo(row[colY]);
    const rawZ = colZ ? row[colZ] : null;
    let z = rawZ !== null ? parsearNumeroEuropeo(rawZ) : null;

    if (isNaN(x) || isNaN(y)) {
      errores.push(
        `Fila ${idx + 2}: X="${row[colX]}" Y="${row[colY]}" no son números válidos.`,
      );
      return;
    }

    if (x > 1000000) x = x / 1000;
    if (y > 10000000) y = y / 1000;
    if (z !== null && z > 10000) z = z / 1000;

    let punto;
    if (sistemaDetectado === "utm") {
      try {
        punto = utmALatLon(x, y, zonaUTM);
      } catch {
        errores.push(
          `Fila ${idx + 2}: error reproyectando UTM→WGS84 (X=${x}, Y=${y}).`,
        );
        return;
      }
    } else {
      punto = { lat: y, lon: x }; // lon (no lng) — clave canónica del backend
    }

    if (z !== null && !isNaN(z)) punto.altitud = z;
    coordenadas.push(punto);

    const meta = {};
    if (colNum && row[colNum] != null) meta.number = row[colNum];
    if (colStation && row[colStation] != null) meta.station = row[colStation];
    if (colComment && row[colComment] != null) meta.comment = row[colComment];
    if (colAngle && row[colAngle] != null) meta.lineAngle = row[colAngle];
    if (z !== null && !isNaN(z)) meta.z = z;

    puntosSingulares.push({ ...punto, ...meta });
  });

  const coordenadasLimpias = coordenadas.filter(
    (c) =>
      c &&
      typeof c.lat === "number" &&
      typeof c.lon === "number" &&
      !isNaN(c.lat) &&
      !isNaN(c.lon),
  );

  if (coordenadasLimpias.length < 2) {
    throw new Error(
      `El Excel no contiene suficientes coordenadas válidas (leídas: ${coordenadasLimpias.length}).` +
        (errores.length > 0 ? ` Pista: ${errores[0]}` : ""),
    );
  }

  return {
    tipo: "Line",
    coordenadas: coordenadasLimpias,
    propiedades: {
      fuente: "excel",
      sistema_original: sistemaDetectado,
      zona_utm: sistemaDetectado === "utm" ? zonaUTM : null,
      n_apoyos: coordenadasLimpias.length,
      puntos_singulares: puntosSingulares,
    },
    advertencias: errores,
  };
}
