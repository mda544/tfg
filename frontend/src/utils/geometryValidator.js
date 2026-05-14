// Cobertura geográfica de cada fuente de datos que usa la app.
const COBERTURAS_FUENTES = {
  "Open-Meteo": { minLat: -90, maxLat: 90, minLon: -180, maxLon: 180 },
  "NASA POWER": { minLat: -90, maxLat: 90, minLon: -180, maxLon: 180 },
  "Copernicus DEM GLO-30": {
    minLat: -90,
    maxLat: 84,
    minLon: -180,
    maxLon: 180,
  },
};

const LIMITES = {
  MIN_PUNTOS: 2,
  MAX_LONGITUD_KM: 500,
  MIN_LONGITUD_M: 100,
  MAX_BBOX_GRADOS: 10,
  MAX_SEPARACION_KM: 50,
};

/**
 * Valida un array de coordenadas {lat, lon}.
 * Devuelve { valido, errores, advertencias, info }.
 */
export function validarTrazado(coordenadas) {
  const errores = [];
  const advertencias = [];
  const info = {};

  if (!coordenadas || coordenadas.length < LIMITES.MIN_PUNTOS) {
    errores.push(
      `El trazado necesita al menos ${LIMITES.MIN_PUNTOS} puntos (tiene ${coordenadas?.length ?? 0}).`,
    );
    return { valido: false, errores, advertencias, info };
  }

  const invalidas = coordenadas
    .map((c, i) => ({ i, c }))
    .filter(
      ({ c }) =>
        typeof c.lat !== "number" ||
        typeof c.lon !== "number" ||
        isNaN(c.lat) ||
        isNaN(c.lon),
    );

  if (invalidas.length > 0) {
    errores.push(
      `${invalidas.length} punto(s) con coordenadas inválidas: ` +
        `índices [${invalidas
          .slice(0, 3)
          .map((x) => x.i)
          .join(", ")}${invalidas.length > 3 ? "…" : ""}].`,
    );
  }

  const fueraRango = coordenadas.filter(
    (c) => c.lat < -90 || c.lat > 90 || c.lon < -180 || c.lon > 180,
  );
  if (fueraRango.length > 0) {
    errores.push(
      `${fueraRango.length} punto(s) fuera del rango WGS84. ¿Las coordenadas son UTM sin reproyectar?`,
    );
  }

  if (errores.length > 0) return { valido: false, errores, advertencias, info };

  const lats = coordenadas.map((c) => c.lat);
  const lons = coordenadas.map((c) => c.lon);
  const bbox = {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  };
  info.bbox = bbox;

  const spanLat = bbox.maxLat - bbox.minLat;
  const spanLon = bbox.maxLon - bbox.minLon;
  if (spanLat > LIMITES.MAX_BBOX_GRADOS || spanLon > LIMITES.MAX_BBOX_GRADOS) {
    advertencias.push(
      `El trazado abarca ${spanLat.toFixed(1)}° lat × ${spanLon.toFixed(1)}° lon. ` +
        `¿Es correcto? Bounding box muy grande puede indicar coordenadas erróneas.`,
    );
  }

  let longitudTotalM = 0;
  for (let i = 0; i < coordenadas.length - 1; i++) {
    longitudTotalM += haversineM(coordenadas[i], coordenadas[i + 1]);
  }
  const longitudKm = longitudTotalM / 1000;
  info.longitud_km = Math.round(longitudKm * 10) / 10;

  if (longitudTotalM < LIMITES.MIN_LONGITUD_M) {
    errores.push(
      `Longitud del trazado demasiado corta (${longitudTotalM.toFixed(0)} m). Dibuja al menos ${LIMITES.MIN_LONGITUD_M} m.`,
    );
  }
  if (longitudKm > LIMITES.MAX_LONGITUD_KM) {
    advertencias.push(
      `Longitud muy elevada: ${longitudKm.toFixed(0)} km. Los cálculos pueden ser lentos.`,
    );
  }

  const tramosLargos = [];
  for (let i = 0; i < coordenadas.length - 1; i++) {
    const d = haversineM(coordenadas[i], coordenadas[i + 1]) / 1000;
    if (d > LIMITES.MAX_SEPARACION_KM)
      tramosLargos.push({ desde: i, hasta: i + 1, km: d.toFixed(1) });
  }
  if (tramosLargos.length > 0) {
    advertencias.push(
      `${tramosLargos.length} tramo(s) con separación > ${LIMITES.MAX_SEPARACION_KM} km entre apoyos consecutivos.`,
    );
  }

  const duplicados = coordenadas.filter(
    (c, i) =>
      i > 0 &&
      Math.abs(c.lat - coordenadas[i - 1].lat) < 1e-8 &&
      Math.abs(c.lon - coordenadas[i - 1].lon) < 1e-8,
  ).length;
  if (duplicados > 0) {
    advertencias.push(
      `${duplicados} punto(s) duplicado(s) consecutivos eliminados en el cálculo.`,
    );
  }

  for (const [fuente, cobertura] of Object.entries(COBERTURAS_FUENTES)) {
    const fueraDeFuente = coordenadas.filter(
      (c) =>
        c.lat < cobertura.minLat ||
        c.lat > cobertura.maxLat ||
        c.lon < cobertura.minLon ||
        c.lon > cobertura.maxLon,
    );
    if (fueraDeFuente.length > 0) {
      advertencias.push(
        `${fueraDeFuente.length} punto(s) fuera de la cobertura de ${fuente}.`,
      );
    }
  }

  info.n_puntos = coordenadas.length;
  info.n_duplicados = duplicados;

  return { valido: errores.length === 0, errores, advertencias, info };
}

/** Distancia Haversine en metros entre dos puntos {lat, lon} */
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

/**
 * Inserta puntos intermedios en vanos > maxVanoM.
 * Opera con {lat, lon}.
 */
export function densificarTrazado(coordenadas, maxVanoM = 500) {
  if (!coordenadas || coordenadas.length < 2) return coordenadas;

  const result = [coordenadas[0]];

  for (let i = 0; i < coordenadas.length - 1; i++) {
    const p1 = coordenadas[i];
    const p2 = coordenadas[i + 1];
    const dist = haversineM(p1, p2);

    if (dist > maxVanoM) {
      const n = Math.ceil(dist / maxVanoM);
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

/**
 * Normaliza coordenadas Leaflet (que usan `lng`) al formato interno {lat, lon}
 * que usa el backend.
 */
export function normalizarALatLon(raw) {
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

/**
 * Convierte {lat, lon} → {lat, lng} para Leaflet.
 */
export function toLngLat(coords) {
  return coords.map((c) => ({ lat: c.lat, lng: c.lon }));
}
