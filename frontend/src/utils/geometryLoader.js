import { read as readShapefile } from "shapefile";

export async function parseGeoJSON(file) {
  const text = await file.text();
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
  const features = [];
  const source = await readShapefile(shpBuffer, dbfBuffer, {
    encoding: "utf-8",
  });

  let result = await source.read();
  while (!result.done) {
    const converted = featureToInternalFormat(result.value);
    if (converted) features.push(converted);
    result = await source.read();
  }
  return features;
}

/** Convierte una Feature GeoJSON al formato interno con {lat, lon, elevation_m?}. */
function featureToInternalFormat(feature) {
  if (!feature?.geometry) return null;
  const { type, coordinates } = feature.geometry;

  const toPoint = ([lon, lat, z]) => ({
    lat,
    lon,
    ...(z !== undefined && z !== null ? { elevation_m: z } : {}),
  });

  const buildSingularPoints = (coords) =>
    coords.map((c, idx) => ({
      lat: c.lat,
      lon: c.lon,
      number: idx + 1,
      ...(c.elevation_m !== undefined ? { altitud: c.elevation_m } : {}),
    }));

  switch (type) {
    case "LineString": {
      const coords = coordinates.map(toPoint);
      return {
        tipo: "Line",
        coordinates: coords,
        propiedades: {
          ...(feature.properties ?? {}),
          fuente: "geojson",
          n_apoyos: coords.length,
          puntos_singulares: buildSingularPoints(coords),
        },
      };
    }
    case "MultiLineString": {
      const coords = coordinates.flat().map(toPoint);
      return {
        tipo: "Line",
        coordinates: coords,
        propiedades: {
          ...(feature.properties ?? {}),
          fuente: "geojson",
          n_apoyos: coords.length,
          puntos_singulares: buildSingularPoints(coords),
        },
      };
    }
    case "Polygon":
      return {
        tipo: "Polygon",
        coordinates: coordinates[0].map(toPoint),
        propiedades: feature.properties ?? {},
      };
    default:
      return null;
  }
}
