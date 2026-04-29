import { useEffect, forwardRef, useImperativeHandle, useRef } from "react";
import { MapContainer, TileLayer, FeatureGroup, useMap } from "react-leaflet";
import L from "leaflet";
import "@geoman-io/leaflet-geoman-free";
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";
import "leaflet/dist/leaflet.css";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// ── Distancia Haversine inline (no depende de geometryValidator) ──────────
function haversineM(a, b) {
  const R = 6_371_000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lng - a.lng) * Math.PI) / 180;
  const x =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((a.lat * Math.PI) / 180) *
      Math.cos((b.lat * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(x));
}

function formatDistance(metres) {
  return metres >= 1000
    ? `${(metres / 1000).toFixed(2)} km`
    : `${Math.round(metres)} m`;
}

// ── Capa de medición en tiempo real ──────────────────────────────────────────
// Dibuja una etiqueta flotante con la distancia al último apoyo mientras
// el usuario mueve el ratón durante el trazado.
const CapaMedicion = ({ maxSpanM }) => {
  const map = useMap();
  const labelRef = useRef(null); // div flotante
  const lastPtRef = useRef(null); // último punto confirmado
  const activeRef = useRef(false); // ¿está el usuario dibujando ahora?

  useEffect(() => {
    if (!map) return;

    // Crear el div flotante y añadirlo al contenedor del mapa
    const label = document.createElement("div");
    label.style.cssText = `
      position: absolute;
      pointer-events: none;
      z-index: 1000;
      background: rgba(0,0,0,0.72);
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 6px;
      white-space: nowrap;
      display: none;
      transform: translate(12px, -50%);
    `;
    map.getContainer().appendChild(label);
    labelRef.current = label;

    // Cuando Geoman empieza a dibujar una línea
    const onDrawStart = (e) => {
      if (e.shape !== "Line") return;
      activeRef.current = true;
      lastPtRef.current = null;
    };

    // Cuando el usuario hace clic y confirma un punto
    const onVertexAdded = (e) => {
      if (!activeRef.current) return;
      const latlngs = e.workingLayer?.getLatLngs?.() ?? [];
      if (latlngs.length > 0) {
        const last = latlngs[latlngs.length - 1];
        lastPtRef.current = { lat: last.lat, lng: last.lng };
      }
    };

    // Movimiento del ratón — actualizar etiqueta
    const onMouseMove = (e) => {
      if (!activeRef.current || !lastPtRef.current || !labelRef.current) return;

      const cursor = { lat: e.latlng.lat, lng: e.latlng.lng };
      const dist = haversineM(lastPtRef.current, cursor);
      const over = dist > maxSpanM;

      const containerPoint = map.latLngToContainerPoint(e.latlng);
      label.style.left = `${containerPoint.x}px`;
      label.style.top = `${containerPoint.y}px`;
      label.style.display = "block";
      label.style.background = over
        ? "rgba(200, 40, 30, 0.85)" // rojo si supera el umbral
        : "rgba(0, 0, 0, 0.72)";
      label.textContent = over
        ? `⚠ ${formatDistance(dist)} — se auto-segmentará`
        : formatDistance(dist);
    };

    // Fin del dibujo — ocultar etiqueta
    const onDrawEnd = () => {
      activeRef.current = false;
      lastPtRef.current = null;
      if (labelRef.current) labelRef.current.style.display = "none";
    };

    map.on("pm:drawstart", onDrawStart);
    map.on("pm:vertexadded", onVertexAdded);
    map.on("mousemove", onMouseMove);
    map.on("pm:drawend", onDrawEnd);
    map.on("pm:create", onDrawEnd);

    return () => {
      map.off("pm:drawstart", onDrawStart);
      map.off("pm:vertexadded", onVertexAdded);
      map.off("mousemove", onMouseMove);
      map.off("pm:drawend", onDrawEnd);
      map.off("pm:create", onDrawEnd);
      if (label.parentNode) label.parentNode.removeChild(label);
    };
  }, [map, maxSpanM]);

  return null;
};

// ── Herramientas de dibujo Geoman ─────────────────────────────────────────────
const HerramientasDibujo = ({ onDibujoCreado, onDibujoBorrado }) => {
  const map = useMap();

  useEffect(() => {
    if (!map?.pm) return;

    // Activar medición de longitud nativa de Geoman
    map.pm.setGlobalOptions({ showLength: true });

    map.pm.addControls({
      position: "topleft",
      drawMarker: false,
      drawCircleMarker: false,
      drawText: false,
      drawCircle: false,
      drawRectangle: false,
      drawPolygon: false,
      editMode: true,
      dragMode: true,
      cutPolygon: false,
      removalMode: true,
    });

    const onCreate = (e) => {
      const latlngs = e.layer.getLatLngs();
      // Geoman devuelve [[LatLng,...]] para polilíneas — aplanamos
      const flat = Array.isArray(latlngs[0]) ? latlngs[0] : latlngs;
      const coords = flat.map((p) => ({ lat: p.lat, lng: p.lng }));
      
      // Borramos el trazo crudo de Geoman del mapa
      map.removeLayer(e.layer);

      onDibujoCreado({
        tipo: e.shape,
        coordenadas: coords,
        // Eliminamos layerId porque ya no nos hace falta seguir esta capa
      });
    };

    const onRemove = (e) => onDibujoBorrado(e.shape);

    map.on("pm:create", onCreate);
    map.on("pm:remove", onRemove);

    return () => {
      map.pm.removeControls();
      map.off("pm:create", onCreate);
      map.off("pm:remove", onRemove);
    };
  }, [map, onDibujoCreado, onDibujoBorrado]);

  return null;
};

// ── Componente principal ──────────────────────────────────────────────────────
const MapaTrazado = forwardRef(({ onDatosDibujados, onDatosBorrados }, ref) => {
  const mapRef = useRef(null);
  const featureGroupRef = useRef(null);

  useImperativeHandle(ref, () => ({
    dibujarGeometria(feature) {
      const map = mapRef.current;
      const fg = featureGroupRef.current;
      if (!map || !fg || !feature) return;

      fg.clearLayers();
      if (feature.tipo !== "Line" || !feature.coordenadas?.length) return;

      const clean = feature.coordenadas.filter(
        (c) =>
          typeof c.lat === "number" &&
          typeof c.lng === "number" &&
          !isNaN(c.lat) &&
          !isNaN(c.lng),
      );
      if (!clean.length) return;

      const singulars = feature.propiedades?.puntos_singulares ?? [];
      const latlngs = clean.map((c) => [c.lat, c.lng]);

      // Segmentos de línea
      for (let i = 0; i < latlngs.length - 1; i++) {
        L.polyline([latlngs[i], latlngs[i + 1]], {
          color: "#2563eb",
          weight: 4,
        })
          .bindTooltip(`Tramo ${i + 1}`, { sticky: true })
          .addTo(fg);
      }

      // Marcadores de apoyo
      clean.forEach((coord, idx) => {
        const meta =
          singulars.find((p) => p.lat === coord.lat && p.lng === coord.lng) ??
          {};
        const popup = [
          `<div style="font-family:sans-serif">`,
          `<h3 style="margin:0 0 5px">Apoyo ${idx + 1}</h3>`,
          meta.station ? `<b>Estación:</b> ${meta.station}<br>` : "",
          meta.comment ? `<b>Comentario:</b> ${meta.comment}<br>` : "",
          meta.altitud
            ? `<b>Altitud:</b> ${meta.altitud.toFixed(2)} m<br>`
            : "",
          "</div>",
        ].join("");

        L.circleMarker([coord.lat, coord.lng], {
          radius: 6,
          color: "white",
          weight: 2,
          fillColor: "#ef4444",
          fillOpacity: 1,
        })
          .bindPopup(popup)
          .addTo(fg);
      });

      const base = L.polyline(latlngs);
      const bounds = base.getBounds();
      if (bounds.isValid())
        map.fitBounds(bounds, { maxZoom: 16, padding: [20, 20] });
      
      /** 
      onDatosDibujados({
        tipo: "Line",
        coordenadas: clean,
        layerId: L.stamp(base),
      });*/
    },

    limpiarTodo() {
      featureGroupRef.current?.clearLayers();
    },
  }));

  return (
    <div
      style={{
        height: "70vh",
        width: "100%",
        borderRadius: "8px",
        overflow: "hidden",
        border: "1px solid #ccc",
      }}
    >
      <MapContainer
        center={[40.4168, -3.7038]}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
        ref={mapRef}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        <FeatureGroup ref={featureGroupRef}>
          <HerramientasDibujo
            onDibujoCreado={onDatosDibujados}
            onDibujoBorrado={onDatosBorrados}
          />
          {/* Etiqueta de distancia en tiempo real — umbral 500 m */}
          <CapaMedicion maxSpanM={500} />
        </FeatureGroup>
      </MapContainer>
    </div>
  );
});

export default MapaTrazado;
