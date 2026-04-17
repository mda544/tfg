import * as XLSX from "xlsx";
import proj4 from "proj4";

/**
 * Limpia y convierte valores numéricos con separadores de miles europeos o anglosajones a un número puro.
 * Ejemplo: "258.056,294" -> 258056.294
 * * @param {string|number} valor - El valor extraído de la celda del Excel.
 * @returns {number} El número validado y formateado, o NaN si es inválido.
 */
function parsearNumeroEuropeo(valor) {
  if (valor === null || valor === undefined) return NaN;
  const str = String(valor).trim();

  // Si ya es un número JS limpio, parseFloat directamente
  if (/^-?\d+(\.\d+)?$/.test(str)) return parseFloat(str);

  // Detectar si usa coma como decimal: "258.056,294"
  const tieneComaDecimal = /,\d{1,3}$/.test(str);

  if (tieneComaDecimal) {
    // Formato europeo: puntos = miles, coma = decimal
    return parseFloat(str.replace(/\./g, "").replace(",", "."));
  } else {
    // Solo puntos como separadores de miles: "4.808.272.963" → "4808272.963"
    // Heurística: si hay más de un punto, todos son separadores de miles
    const nPuntos = (str.match(/\./g) || []).length;
    if (nPuntos > 1) {
      return parseFloat(str.replace(/\./g, ""));
    }
    // Un solo punto: decimal normal
    return parseFloat(str);
  }
}

/**
 * Detecta si un par de coordenadas corresponden a UTM (metros) o WGS84 (grados).
 * Se basa en que los grados geográficos nunca superan 180 (X) y 90 (Y).
 * @param {number} x - Coordenada X (Longitud o Easting).
 * @param {number} y - Coordenada Y (Latitud o Northing).
 * @returns {"utm" | "wgs84"} El sistema de coordenadas inferido.
 */
function detectarSistema(x, y) {
  const esUTM =
    Math.abs(y) > 1000 || // Y en grados nunca supera 90
    Math.abs(x) > 180; // X en grados nunca supera 180
  return esUTM ? "utm" : "wgs84";
}

/**
 * Estima la zona UTM para la Península Ibérica basándose en el valor de la coordenada X (Easting).
 * Zonas posibles: 29N (Oeste), 30N (Centro), 31N (Este).
 * @param {number} easting - Coordenada X en el sistema UTM (en metros).
 * @returns {number} La zona UTM detectada (29, 30 o 31).
 */
function detectarZonaUTM(easting) {
  // Heurística básica por coordenada X (Easting) para España peninsular:
  if (easting > 700000) return 29; // Zona 29N (Oeste: Galicia, Portugal)
  if (easting < 500000) return 31; // Zona 31N (Este: Cataluña, Baleares)
  return 30; // Zona 30N (Centro de la península, la más habitual)
}

const PROJ_WGS84 = "EPSG:4326";

/**
 * Genera la cadena de definición de proyección Proj4 para una zona UTM específica.
 * @param {number} zona - El huso o zona UTM (ejemplo: 30).
 * @param {string} [hemisferio="N"] - "N" para Norte, "S" para Sur.
 * @returns {string} Cadena con la configuración de la proyección (formato Proj4).
 */
function obtenerProyeccionUTM(zona, hemisferio = "N") {
  return `+proj=utm +zone=${zona} +${hemisferio === "N" ? "north" : "south"} +datum=WGS84 +units=m +no_defs`;
}

/**
 * Convierte un par de coordenadas planas UTM (metros) a coordenadas esféricas WGS84 (grados).
 * Utiliza la librería matemática proj4.
 * @param {number} easting - Coordenada X (Este) en metros.
 * @param {number} northing - Coordenada Y (Norte) en metros.
 * @param {number} zona - Zona UTM del emplazamiento.
 * @returns {{lat: number, lng: number}} Objeto con la Latitud y Longitud calculadas.
 */
function utmAWgs84(easting, northing, zona) {
  const projUTM = obtenerProyeccionUTM(zona);
  const [lng, lat] = proj4(projUTM, PROJ_WGS84, [easting, northing]);
  return { lat, lng };
}

/**
 * Parsea un archivo Excel con el trazado de una línea eléctrica, detectando
 * columnas, limpiando datos espaciales y transformando todo al estándar WGS84.
 * @param {File} file - El archivo Excel (.xlsx, .xls) cargado por el usuario.
 * @param {Object} [opcionesUTM={}] - Opciones de forzado de proyección.
 * @param {number} [opcionesUTM.zona] - Forzar una zona UTM si el algoritmo falla o el usuario la especifica.
 * @returns {Promise<Object>} Promesa que resuelve en una Feature geométrica lista para el mapa.
 * @throws {Error} Si el archivo está vacío, no tiene columnas X/Y o faltan puntos.
 */
export async function parseLineExcel(file, opcionesUTM = {}) {
  const buffer = await file.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];

  // raw: true para obtener los valores sin formatear (evita que xlsx interprete ###)
  const rows = XLSX.utils.sheet_to_json(sheet, { defval: null, raw: true });

  if (!rows || rows.length === 0) {
    throw new Error("El archivo Excel está vacío.");
  }

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
  ]);
  const colAngle = encontrarColumna(columnas, [
    "line angle",
    "lineangle",
    "angle",
    "angulo",
  ]);

  if (!colX || !colY) {
    throw new Error(
      `Columnas X/Y no encontradas. Detectadas: ${columnas.join(", ")}`,
    );
  }

  // Detectar sistema de coordenadas en la primera fila válida
  let sistemaDetectado = "wgs84";
  let zonaUTM = opcionesUTM.zona ?? null;

  for (const row of rows) {
    const x = parsearNumeroEuropeo(row[colX]);
    const y = parsearNumeroEuropeo(row[colY]);
    if (!isNaN(x) && !isNaN(y)) {
      sistemaDetectado = detectarSistema(x, y);
      if (sistemaDetectado === "utm" && !zonaUTM) {
        zonaUTM = detectarZonaUTM(x);
      }
      break;
    }
  }

  const coordenadas = [];
  const puntosSingulares = [];
  const errores = [];

  rows.forEach((row, idx) => {
    const rawX = row[colX];
    const rawY = row[colY];
    const rawZ = colZ ? row[colZ] : null;

    const x = parsearNumeroEuropeo(rawX);
    const y = parsearNumeroEuropeo(rawY);
    const z = rawZ !== null ? parsearNumeroEuropeo(rawZ) : null;

    if (isNaN(x) || isNaN(y)) {
      errores.push(
        `Fila ${idx + 2}: X="${rawX}" Y="${rawY}" no son números válidos.`,
      );
      return;
    }

    let punto;
    if (sistemaDetectado === "utm") {
      try {
        punto = utmAWgs84(x, y, zonaUTM);
      } catch {
        errores.push(
          `Fila ${idx + 2}: error reproyectando UTM→WGS84 (X=${x}, Y=${y}).`,
        );
        return;
      }
    } else {
      punto = { lat: y, lng: x };
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

  if (coordenadas.length < 2) {
    throw new Error(
      `Puntos válidos insuficientes (${coordenadas.length}).` +
        (errores.length > 0 ? ` Primer error: ${errores[0]}` : ""),
    );
  }

  return {
    tipo: "Line",
    coordenadas,
    propiedades: {
      fuente: "excel",
      sistema_original: sistemaDetectado,
      zona_utm: sistemaDetectado === "utm" ? zonaUTM : null,
      n_apoyos: coordenadas.length,
      puntos_singulares: puntosSingulares,
    },
    advertencias: errores,
  };
}

/**
 * Busca el nombre exacto de una columna dentro de un listado de cabeceras,
 * permitiendo variaciones de nombre (mayúsculas, tildes, espacios).
 * @param {string[]} columnas - Array con las cabeceras leídas directamente del Excel.
 * @param {string[]} aliases - Array de posibles nombres que estamos buscando (ej: ["x", "longitud"]).
 * @returns {string|null} El nombre real de la columna si hay coincidencia, o null si no existe.
 */
function encontrarColumna(columnas, aliases) {
  return (
    columnas.find((col) =>
      aliases.some((alias) => col.trim().toLowerCase() === alias.toLowerCase()),
    ) ?? null
  );
}
