const SOURCE_COVERAGE = {
  "Open-Meteo": { minLat: -90, maxLat: 90, minLon: -180, maxLon: 180 },
  "NASA POWER": { minLat: -90, maxLat: 90, minLon: -180, maxLon: 180 },
  "Copernicus DEM GLO-30": {
    minLat: -90,
    maxLat: 84,
    minLon: -180,
    maxLon: 180,
  },
};

const LIMITS = {
  MIN_POINTS: 2,
  MAX_LENGTH_KM: 500,
  MIN_LENGTH_M: 100,
  MAX_BBOX_DEG: 10,
  MAX_SPAN_KM: 50,
};

/** Valida un array de coordenadas {lat, lon}. */
export function validateRoute(coordinates) {
  const errors = [];
  const warnings = [];
  const info = {};

  if (!coordinates || coordinates.length < LIMITS.MIN_POINTS) {
    errors.push(
      `El trazado necesita al menos ${LIMITS.MIN_POINTS} puntos (tiene ${coordinates?.length ?? 0}).`,
    );
    return { valid: false, errors, warnings, info };
  }

  const invalidPoints = coordinates
    .map((c, i) => ({ i, c }))
    .filter(
      ({ c }) =>
        typeof c.lat !== "number" ||
        typeof c.lon !== "number" ||
        isNaN(c.lat) ||
        isNaN(c.lon),
    );

  if (invalidPoints.length > 0) {
    errors.push(
      `${invalidPoints.length} punto(s) con coordenadas inválidas: ` +
        `índices [${invalidPoints
          .slice(0, 3)
          .map((x) => x.i)
          .join(", ")}${invalidPoints.length > 3 ? "…" : ""}].`,
    );
  }

  const outOfRange = coordinates.filter(
    (c) => c.lat < -90 || c.lat > 90 || c.lon < -180 || c.lon > 180,
  );
  if (outOfRange.length > 0) {
    errors.push(
      `${outOfRange.length} punto(s) fuera del rango WGS84. ¿Las coordenadas son UTM sin reproyectar?`,
    );
  }

  if (errors.length > 0) return { valid: false, errors, warnings, info };

  const lats = coordinates.map((c) => c.lat);
  const lons = coordinates.map((c) => c.lon);
  const bbox = {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  };
  info.bbox = bbox;

  const spanLat = bbox.maxLat - bbox.minLat;
  const spanLon = bbox.maxLon - bbox.minLon;
  if (spanLat > LIMITS.MAX_BBOX_DEG || spanLon > LIMITS.MAX_BBOX_DEG) {
    warnings.push(
      `El trazado abarca ${spanLat.toFixed(1)}° lat × ${spanLon.toFixed(1)}° lon. ` +
        `¿Es correcto? Bounding box muy grande puede indicar coordenadas erróneas.`,
    );
  }

  let totalLengthM = 0;
  for (let i = 0; i < coordinates.length - 1; i++) {
    totalLengthM += haversineM(coordinates[i], coordinates[i + 1]);
  }
  const lengthKm = totalLengthM / 1000;
  info.longitud_km = Math.round(lengthKm * 10) / 10;

  if (totalLengthM < LIMITS.MIN_LENGTH_M) {
    errors.push(
      `Longitud del trazado demasiado corta (${totalLengthM.toFixed(0)} m). Dibuja al menos ${LIMITS.MIN_LENGTH_M} m.`,
    );
  }
  if (lengthKm > LIMITS.MAX_LENGTH_KM) {
    warnings.push(
      `Longitud muy elevada: ${lengthKm.toFixed(0)} km. Los cálculos pueden ser lentos.`,
    );
  }

  const longSpans = [];
  for (let i = 0; i < coordinates.length - 1; i++) {
    const d = haversineM(coordinates[i], coordinates[i + 1]) / 1000;
    if (d > LIMITS.MAX_SPAN_KM)
      longSpans.push({ desde: i, hasta: i + 1, km: d.toFixed(1) });
  }
  if (longSpans.length > 0) {
    warnings.push(
      `${longSpans.length} tramo(s) con separación > ${LIMITS.MAX_SPAN_KM} km entre apoyos consecutivos.`,
    );
  }

  const duplicates = coordinates.filter(
    (c, i) =>
      i > 0 &&
      Math.abs(c.lat - coordinates[i - 1].lat) < 1e-8 &&
      Math.abs(c.lon - coordinates[i - 1].lon) < 1e-8,
  ).length;
  if (duplicates > 0) {
    warnings.push(
      `${duplicates} punto(s) duplicado(s) consecutivos eliminados en el cálculo.`,
    );
  }

  for (const [source, coverage] of Object.entries(SOURCE_COVERAGE)) {
    const outOfSource = coordinates.filter(
      (c) =>
        c.lat < coverage.minLat ||
        c.lat > coverage.maxLat ||
        c.lon < coverage.minLon ||
        c.lon > coverage.maxLon,
    );
    if (outOfSource.length > 0) {
      warnings.push(
        `${outOfSource.length} punto(s) fuera de la cobertura de ${source}.`,
      );
    }
  }

  info.n_puntos = coordinates.length;
  info.n_duplicados = duplicates;

  return { valid: errors.length === 0, errors, warnings, info };
}

/** Distancia Haversine en metros entre dos puntos {lat, lon}. */
export function haversineM(a, b) {
  const R = 6_371_000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((a.lat * Math.PI) / 180) *
      Math.cos((b.lat * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

/** Inserta puntos intermedios en vanos > maxSpanM. Opera con {lat, lon}. */
export function densifyRoute(coordinates, maxSpanM = 500) {
  if (!coordinates || coordinates.length < 2) return coordinates;

  const result = [coordinates[0]];

  for (let i = 0; i < coordinates.length - 1; i++) {
    const p1 = coordinates[i];
    const p2 = coordinates[i + 1];
    const dist = haversineM(p1, p2);

    if (dist > maxSpanM) {
      const n = Math.ceil(dist / maxSpanM);
      for (let j = 1; j < n; j++) {
        const t = j / n;
        result.push({
          lat: p1.lat + (p2.lat - p1.lat) * t,
          lon: p1.lon + (p2.lon - p1.lon) * t,
        });
      }
    }
    result.push(p2);
  }

  return result;
}

/** Normaliza coordenadas Leaflet (que usan `lng`) al formato interno {lat, lon}. */
export function normalizeToLatLon(raw) {
  const flat = Array.isArray(raw[0]) ? raw[0] : raw;
  return flat.map((p) => ({
    lat: typeof p.lat === "number" ? p.lat : p[0],
    lon:
      typeof p.lng === "number"
        ? p.lng
        : typeof p.lon === "number"
          ? p.lon
          : p[1],
  }));
}

/** Convierte {lat, lon} → {lat, lng} para Leaflet. */
export function toLngLat(coords) {
  return coords.map((c) => ({ lat: c.lat, lng: c.lon }));
}
