// Cobertura geográfica de cada fuente de datos que usa la app.
// Si el trazado cae fuera, el backend no podrá obtener datos para esos puntos.
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

// Límites operativos para líneas aéreas peninsulares (configurable)
const LIMITES = {
  MIN_PUNTOS: 2,
  MAX_LONGITUD_KM: 500, // advertencia si supera esto
  MIN_LONGITUD_M: 100, // error si es menor (casi un punto)
  MAX_BBOX_GRADOS: 10, // advertencia si el bbox supera 10° en cualquier eje
  MAX_SEPARACION_KM: 50, // advertencia entre apoyos consecutivos muy separados
};

export function validarTrazado(coordenadas) {
  const errores = [];
  const advertencias = [];
  const info = {};

  // ── 1. Mínimo de puntos ──────────────────────────────
  if (!coordenadas || coordenadas.length < LIMITES.MIN_PUNTOS) {
    errores.push(
      `El trazado necesita al menos ${LIMITES.MIN_PUNTOS} puntos (tiene ${coordenadas?.length ?? 0}).`,
    );
    return { valido: false, errores, advertencias, info };
  }

  // ── 2. Coordenadas numéricas válidas ─────────────────
  const invalidas = coordenadas
    .map((c, i) => ({ i, c }))
    .filter(
      ({ c }) =>
        typeof c.lat !== "number" ||
        typeof c.lng !== "number" ||
        isNaN(c.lat) ||
        isNaN(c.lng),
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

  // ── 3. Rango WGS84 ───────────────────────────────────
  const fueraRango = coordenadas.filter(
    (c) => c.lat < -90 || c.lat > 90 || c.lng < -180 || c.lng > 180,
  );
  if (fueraRango.length > 0) {
    errores.push(
      `${fueraRango.length} punto(s) fuera del rango WGS84. ` +
        `¿Las coordenadas son UTM sin reproyectar?`,
    );
  }

  if (errores.length > 0) {
    return { valido: false, errores, advertencias, info };
  }

  // ── 4. Bounding box ──────────────────────────────────
  const lats = coordenadas.map((c) => c.lat);
  const lons = coordenadas.map((c) => c.lng);
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

  // ── 5. Longitud aproximada (haversine) ───────────────
  let longitudTotalM = 0;
  for (let i = 0; i < coordenadas.length - 1; i++) {
    longitudTotalM += haversineM(coordenadas[i], coordenadas[i + 1]);
  }
  const longitudKm = longitudTotalM / 1000;
  info.longitud_km = Math.round(longitudKm * 10) / 10;

  if (longitudTotalM < LIMITES.MIN_LONGITUD_M) {
    errores.push(
      `Longitud del trazado demasiado corta (${longitudTotalM.toFixed(0)} m). ` +
        `Dibuja una línea de al menos ${LIMITES.MIN_LONGITUD_M} m.`,
    );
  }
  if (longitudKm > LIMITES.MAX_LONGITUD_KM) {
    advertencias.push(
      `Longitud muy elevada: ${longitudKm.toFixed(0)} km. ` +
        `Los cálculos pueden ser lentos. Considera dividir en tramos.`,
    );
  }

  // ── 6. Separación entre apoyos consecutivos ──────────
  const tramosLargos = [];
  for (let i = 0; i < coordenadas.length - 1; i++) {
    const d = haversineM(coordenadas[i], coordenadas[i + 1]) / 1000;
    if (d > LIMITES.MAX_SEPARACION_KM) {
      tramosLargos.push({ desde: i, hasta: i + 1, km: d.toFixed(1) });
    }
  }
  if (tramosLargos.length > 0) {
    advertencias.push(
      `${tramosLargos.length} tramo(s) con separación > ${LIMITES.MAX_SEPARACION_KM} km ` +
        `entre apoyos consecutivos. Comprueba que no falten puntos intermedios.`,
    );
  }

  // ── 7. Puntos duplicados consecutivos ────────────────
  const duplicados = coordenadas.filter(
    (c, i) =>
      i > 0 &&
      Math.abs(c.lat - coordenadas[i - 1].lat) < 1e-8 &&
      Math.abs(c.lng - coordenadas[i - 1].lng) < 1e-8,
  ).length;
  if (duplicados > 0) {
    advertencias.push(
      `${duplicados} punto(s) duplicado(s) consecutivos eliminados en el cálculo.`,
    );
  }

  // ── 8. Cobertura de fuentes ──────────────────────────
  for (const [fuente, cobertura] of Object.entries(COBERTURAS_FUENTES)) {
    const fueraDeFuente = coordenadas.filter(
      (c) =>
        c.lat < cobertura.minLat ||
        c.lat > cobertura.maxLat ||
        c.lng < cobertura.minLon ||
        c.lng > cobertura.maxLon,
    );
    if (fueraDeFuente.length > 0) {
      advertencias.push(
        `${fueraDeFuente.length} punto(s) fuera de la cobertura de ${fuente}.`,
      );
    }
  }

  info.n_puntos = coordenadas.length;
  info.n_duplicados = duplicados;

  return {
    valido: errores.length === 0,
    errores,
    advertencias,
    info,
  };
}

// Fórmula de Haversine — distancia en metros entre dos puntos WGS84
export function haversineM(a, b) {
  const R = 6371000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lng - a.lng) * Math.PI) / 180;
  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((a.lat * Math.PI) / 180) *
      Math.cos((b.lat * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

export function densificarTrazado(coordenadas, maxVanoM) {
  if (!coordenadas || coordenadas.length < 2) return coordenadas;

  const nuevasCoordenadas = [coordenadas[0]];

  for (let i = 0; i < coordenadas.length - 1; i++) {
    const p1 = coordenadas[i];
    const p2 = coordenadas[i + 1];
    const distancia = haversineM(p1, p2);

    if (distancia > maxVanoM) {
      // Calculamos en cuántos trozos hay que dividir el vano
      const numTrozos = Math.ceil(distancia / maxVanoM);
      
      // Inyectamos los puntos intermedios matemáticamente calculados
      for (let j = 1; j < numTrozos; j++) {
        const fraccion = j / numTrozos;
        nuevasCoordenadas.push({
          lat: p1.lat + (p2.lat - p1.lat) * fraccion,
          lng: p1.lng + (p2.lng - p1.lng) * fraccion,
        });
      }
    }
    // Añadimos el punto original de destino
    nuevasCoordenadas.push(p2);
  }

  return nuevasCoordenadas;
}

/**
 * Normaliza un array crudo de coordenadas LatLng de Leaflet (posiblemente anidado) 
 * a un array plano de objetos simples {lat, lng} que son seguros para 
 * usar con las funciones haversineM y densificarTrazado.
 */
export function normalizarLeafletCoords(raw) {
  // Las polilíneas de Leaflet devuelven [[LatLng, LatLng, ...]] — aplanamos un nivel si es necesario
  const flat = Array.isArray(raw[0]) ? raw[0] : raw;
  
  return flat.map((p) => ({
    lat: typeof p.lat === "number" ? p.lat : p[0],
    lng: typeof p.lng === "number" ? p.lng : p[1],
  }));
}