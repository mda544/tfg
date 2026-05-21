import { useEffect, forwardRef, useImperativeHandle, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  FeatureGroup,
  useMap,
  LayersControl,
} from "react-leaflet";
import L from "leaflet";
import "@geoman-io/leaflet-geoman-free";
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";
import "leaflet/dist/leaflet.css";
import { haversineM } from "../../utils/geometryValidator";

const { BaseLayer } = LayersControl;

const ROUTE_STYLE = { color: "#2563eb", weight: 4 };
const MARKER_STYLE = {
  radius: 6,
  color: "white",
  weight: 2,
  fillColor: "#ef4444",
  fillOpacity: 1,
};

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

function formatDistance(m) {
  return m >= 1000 ? `${(m / 1000).toFixed(2)} km` : `${Math.round(m)} m`;
}

// Etiqueta de distancia en tiempo real al dibujar
const MeasurementLayer = ({ maxSpanM }) => {
  const map = useMap();
  const labelRef = useRef(null);
  const lastPtRef = useRef(null);
  const activeRef = useRef(false);

  useEffect(() => {
    if (!map) return;

    const label = document.createElement("div");
    label.style.cssText = `
      position:absolute; pointer-events:none; z-index:1000;
      background:rgba(0,0,0,0.72); color:#fff; font-size:12px; font-weight:600;
      padding:4px 10px; border-radius:6px; white-space:nowrap;
      display:none; transform:translate(12px,-50%);
    `;
    map.getContainer().appendChild(label);
    labelRef.current = label;

    const onDrawStart = (e) => {
      if (e.shape !== "Line") return;
      activeRef.current = true;
      lastPtRef.current = null;
    };
    const onVertexAdded = (e) => {
      if (!activeRef.current) return;
      const latlngs = e.workingLayer?.getLatLngs?.() ?? [];
      if (latlngs.length > 0) {
        const last = latlngs[latlngs.length - 1];
        lastPtRef.current = { lat: last.lat, lng: last.lng };
      }
    };
    const onMouseMove = (e) => {
      if (!activeRef.current || !lastPtRef.current || !label) return;
      // haversineM acepta {lat, lng} porque viene de eventos Leaflet
      const cursor = { lat: e.latlng.lat, lng: e.latlng.lng };
      const dist = haversineM(
        { lat: lastPtRef.current.lat, lon: lastPtRef.current.lng },
        { lat: cursor.lat, lon: cursor.lng },
      );
      const over = dist > maxSpanM;
      const pt = map.latLngToContainerPoint(e.latlng);
      label.style.left = `${pt.x}px`;
      label.style.top = `${pt.y}px`;
      label.style.display = "block";
      label.style.background = over
        ? "rgba(200,40,30,0.85)"
        : "rgba(0,0,0,0.72)";
      label.textContent = over
        ? `${formatDistance(dist)} — se auto-segmentará`
        : formatDistance(dist);
    };
    const onDrawEnd = () => {
      activeRef.current = false;
      lastPtRef.current = null;
      if (label) label.style.display = "none";
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

// Controles de dibujo Geoman
const DrawingTools = ({ onRouteDrawn, onRouteRemoved }) => {
  const map = useMap();

  useEffect(() => {
    if (!map?.pm) return;
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
      const flat = Array.isArray(latlngs[0]) ? latlngs[0] : latlngs;
      // Leaflet devuelve {lat, lng} — convertimos a {lat, lon} (clave canónica)
      const coords = flat.map((p) => ({ lat: p.lat, lon: p.lng }));
      map.removeLayer(e.layer);
      onRouteDrawn({ tipo: e.shape, coordinates: coords });
    };
    const onRemove = (e) => onRouteRemoved(e.shape);

    map.on("pm:create", onCreate);
    map.on("pm:remove", onRemove);

    return () => {
      map.pm.removeControls();
      map.off("pm:create", onCreate);
      map.off("pm:remove", onRemove);
    };
  }, [map, onRouteDrawn, onRouteRemoved]);

  return null;
};

function buildPopup(coord, meta, idx) {
  return [
    `<div style="font-family:sans-serif">`,
    `<h3 style="margin:0 0 5px">Apoyo ${idx + 1}</h3>`,
    meta.station ? `<b>Estación:</b> ${meta.station}<br>` : "",
    meta.comment ? `<b>Comentario:</b> ${meta.comment}<br>` : "",
    meta.altitud ? `<b>Altitud:</b> ${meta.altitud.toFixed(2)} m<br>` : "",
    "</div>",
  ].join("");
}

// Componente principal
const RouteMap = forwardRef(({ onRouteDrawn, onRouteCleared }, ref) => {
  const mapRef = useRef(null);
  const featureGroupRef = useRef(null);

  useImperativeHandle(ref, () => ({
    // Recibe {lat, lon} y los convierte a [lat, lng] para Leaflet
    drawRoute(feature) {
      const map = mapRef.current;
      const fg = featureGroupRef.current;
      if (!map || !fg || !feature) return;

      fg.clearLayers();
      if (feature.tipo !== "Line" || !feature.coordinates?.length) return;

      const points = feature.coordinates;
      const singulars = feature.propiedades?.puntos_singulares ?? [];
      const latlngs = points.map((c) => [c.lat, c.lon]);

      for (let i = 0; i < latlngs.length - 1; i++) {
        L.polyline([latlngs[i], latlngs[i + 1]], ROUTE_STYLE)
          .bindTooltip(`Tramo ${i + 1}`, { sticky: true })
          .addTo(fg);
      }

      points.forEach((coord, idx) => {
        const meta =
          singulars.find((p) => p.lat === coord.lat && p.lon === coord.lon) ??
          {};
        L.circleMarker([coord.lat, coord.lon], MARKER_STYLE)
          .bindPopup(buildPopup(coord, meta, idx))
          .addTo(fg);
      });

      const bounds = L.polyline(latlngs).getBounds();
      if (bounds.isValid())
        map.fitBounds(bounds, { maxZoom: 16, padding: [20, 20] });
    },

    clearAll() {
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
        <LayersControl position="topright">
          <BaseLayer checked name="OpenStreetMap">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
          </BaseLayer>
          <BaseLayer name="Satélite">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution="© Esri"
            />
          </BaseLayer>
          <BaseLayer name="Topográfico">
            <TileLayer
              url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
              attribution="© OpenTopoMap"
            />
          </BaseLayer>
        </LayersControl>
        <FeatureGroup ref={featureGroupRef}>
          <DrawingTools
            onRouteDrawn={onRouteDrawn}
            onRouteRemoved={onRouteCleared}
          />
          <MeasurementLayer maxSpanM={500} />
        </FeatureGroup>
      </MapContainer>
    </div>
  );
});

RouteMap.displayName = "RouteMap";
export default RouteMap;
