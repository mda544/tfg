import * as XLSX from "xlsx";
import proj4 from "proj4";

/**
 * Limpia y convierte valores numéricos con separadores de miles europeos o anglosajones a un número puro.
 * Ejemplo: "4.808.318.851" -> 4808318.851
 * @param {string|number} valor - El valor extraído de la celda del Excel.
 * @returns {number} El número validado y formateado, o NaN si es inválido.
 */
function parsearNumeroEuropeo(valor) {
  if (valor === null || valor === undefined) return NaN;
  let str = String(valor).trim();

  // Si ya es un número JS limpio sin separadores de miles
  if (/^-?\d+(\.\d+)?$/.test(str)) return parseFloat(str);

  // Unificamos criterios: convertimos las comas en puntos
  str = str.replace(/,/g, ".");

  // Separamos el número por bloques de puntos
  const partes = str.split(".");

  if (partes.length > 1) {
    // Si hay más de un punto, asumimos que el ÚLTIMO trozo son los decimales
    // y todo lo que hay a la izquierda son los miles/millones.
    const enteros = partes.slice(0, -1).join(""); // Juntamos todo sin puntos
    const decimales = partes[partes.length - 1]; // Nos quedamos el final

    return parseFloat(`${enteros}.${decimales}`);
  }

  // 4. Fallback de seguridad
  return parseFloat(str);
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
 * Asigna la zona UTM por defecto. 
 * Casi toda la Península Ibérica (incluyendo Asturias y Cantabria) está en la Zona 30.
 * @param {number} easting - Coordenada X (ignorada ahora por ser irrelevante sin la longitud).
 * @returns {number} La zona UTM por defecto (30).
 */
// eslint-disable-next-line no-unused-vars
function detectarZonaUTM(easting) {
  // Las zonas UTM en España son la 29, 30 y 31.
  // Como la X se repite en todas, no se puede adivinar solo mirando la X.
  // Forzamos la 30 como estándar nacional. 
  return 30; 
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
    "structure comment",
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

    let x = parsearNumeroEuropeo(rawX);
    let y = parsearNumeroEuropeo(rawY);
    let z = rawZ !== null ? parsearNumeroEuropeo(rawZ) : null;

    if (isNaN(x) || isNaN(y)) {
      errores.push(
        `Fila ${idx + 2}: X="${rawX}" Y="${rawY}" no son números válidos.`,
      );
      return;
    }

    // Si Excel se comió la coma y los hizo gigantes, los devolvemos a su tamaño real
    if (x > 1000000) x = x / 1000;
    if (y > 10000000) y = y / 1000;
    if (z !== null && z > 10000) z = z / 1000;

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

  // Limpiamos cualquier posible NaN que haya generado proj4 en la reproyección
  const coordenadasLimpias = coordenadas.filter(
    (c) =>
      c &&
      typeof c.lat === "number" &&
      typeof c.lng === "number" &&
      !isNaN(c.lat) &&
      !isNaN(c.lng),
  );

  // Exigimos al menos 2 puntos (para poder dibujar una línea)
  if (coordenadasLimpias.length < 2) {
    throw new Error(
      `El Excel no contiene suficientes coordenadas matemáticas válidas (leídas: ${coordenadasLimpias.length}). Revisa que las celdas sean números puros.` +
        (errores.length > 0 ? ` Pista del error: ${errores[0]}` : ""),
    );
  }

  return {
    tipo: "Line",
    coordenadas: coordenadasLimpias, // Usamos la matriz purificada
    propiedades: {
      fuente: "excel",
      sistema_original: sistemaDetectado,
      zona_utm: sistemaDetectado === "utm" ? zonaUTM : null,
      n_apoyos: coordenadasLimpias.length, // Contamos solo los apoyos reales
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
