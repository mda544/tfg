import { read as readShapefile } from "shapefile";

/**
 * Lee y parsea un archivo GeoJSON cargado por el usuario.
 * @param {File} file - El archivo .geojson o .json subido mediante el input.
 * @returns {Promise<Array>} Un array de geometrías en el formato interno de la aplicación.
 */
export async function parseGeoJSON(file) {
  const text = await file.text();
  const geojson = JSON.parse(text);

  // Normalización: Un GeoJSON puede venir estructurado de varias formas.
  // Aquí forzamos a que siempre se trate como un array de "Features".
  const features =
    geojson.type === "FeatureCollection"
      ? geojson.features
      : geojson.type === "Feature"
        ? [geojson]
        : [{ type: "Feature", geometry: geojson, properties: {} }];

  // Convertimos cada Feature al formato de Leaflet/App y filtramos los nulos (puntos ignorados)
  return features.map(featureToInternalFormat).filter(Boolean);
}

/**
 * Lee y parsea un archivo Shapefile (.shp) binario.
 * @param {File} shpFile - El archivo principal con la geometría (.shp).
 * @param {File} [dbfFile=null] - (Opcional) El archivo con las propiedades y atributos (.dbf).
 * @returns {Promise<Array>} Un array de geometrías en el formato interno de la aplicación.
 */
export async function parseSHP(shpFile, dbfFile = null) {
  // Los Shapefiles son binarios, se leen como ArrayBuffer, no como texto
  const shpBuffer = await shpFile.arrayBuffer();
  const dbfBuffer = dbfFile ? await dbfFile.arrayBuffer() : undefined;

  const features = [];

  // Iniciamos la lectura del Shapefile, forzando codificación utf-8 para tildes y eñes
  const source = await readShapefile(shpBuffer, dbfBuffer, {
    encoding: "utf-8",
  });

  // Iteramos sobre las geometrías en un flujo (stream) para no saturar la memoria
  let result = await source.read();
  while (!result.done) {
    const converted = featureToInternalFormat(result.value);
    if (converted) features.push(converted);
    result = await source.read(); // Leer la siguiente geometría
  }

  return features;
}

/**
 * Función central de mapeo: Convierte una Feature estándar GeoJSON (Longitud, Latitud)
 * al formato de objetos interno necesario para los mapas de Leaflet (Latitud, Longitud).
 * @param {Object} feature - Feature individual en formato estándar GeoJSON.
 * @returns {Object|null} Objeto { tipo, coordenadas, propiedades } o null si la geometría no es soportada.
 */
function featureToInternalFormat(feature) {
  if (!feature?.geometry) return null;
  const { type, coordinates } = feature.geometry;

  switch (type) {
    case "LineString":
      return {
        tipo: "Line",
        // GeoJSON es [X, Y] (Long, Lat). Leaflet exige {lat: Y, lng: X}
        coordenadas: coordinates.map(([lng, lat]) => ({ lat, lng })),
        propiedades: feature.properties ?? {},
      };

    case "MultiLineString":
      return {
        tipo: "Line",
        // Aplana sub-segmentos en un único array continuo de coordenadas
        coordenadas: coordinates.flat().map(([lng, lat]) => ({ lat, lng })),
        propiedades: feature.properties ?? {},
      };

    case "Polygon":
      return {
        tipo: "Polygon",
        // coordinates[0] coge solo el anillo exterior, ignorando los "agujeros" internos
        coordenadas: coordinates[0].map(([lng, lat]) => ({ lat, lng })),
        propiedades: feature.properties ?? {},
      };

    default:
      // Ignoramos geometrías que no nos sirven para calcular líneas aéreas (Point, MultiPoint, MultiPolygon)
      return null;
  }
}
