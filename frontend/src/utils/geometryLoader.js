import { read as readShapefile } from "shapefile";

export async function parseGeoJSON(file) {
  const text    = await file.text();
  const geojson = JSON.parse(text);

  const features =
    geojson.type === "FeatureCollection"
      ? geojson.features
      : geojson.type === "Feature"
        ? [geojson]
        : [{ type: "Feature", geometry: geojson, properties: {} }];

  return features.map(featureToInternalFormat).filter(Boolean);
}

export async function parseSHP(shpFile, dbfFile = null) {
  const shpBuffer = await shpFile.arrayBuffer();
  const dbfBuffer = dbfFile ? await dbfFile.arrayBuffer() : undefined;
  const features  = [];
  const source    = await readShapefile(shpBuffer, dbfBuffer, { encoding: "utf-8" });

  let result = await source.read();
  while (!result.done) {
    const converted = featureToInternalFormat(result.value);
    if (converted) features.push(converted);
    result = await source.read();
  }
  return features;
}

/** Convierte una Feature GeoJSON al formato interno con {lat, lon}. */
function featureToInternalFormat(feature) {
  if (!feature?.geometry) return null;
  const { type, coordinates } = feature.geometry;

  switch (type) {
    case "LineString":
      return {
        tipo:        "Line",
        // GeoJSON: [lon, lat] → interno: { lat, lon }
        coordinates: coordinates.map(([lon, lat]) => ({ lat, lon })),
        propiedades: feature.properties ?? {},
      };
    case "MultiLineString":
      return {
        tipo:        "Line",
        coordinates: coordinates.flat().map(([lon, lat]) => ({ lat, lon })),
        propiedades: feature.properties ?? {},
      };
    case "Polygon":
      return {
        tipo:        "Polygon",
        coordinates: coordinates[0].map(([lon, lat]) => ({ lat, lon })),
        propiedades: feature.properties ?? {},
      };
    default:
      return null;
  }
}