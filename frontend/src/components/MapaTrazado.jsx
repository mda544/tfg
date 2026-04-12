import { useEffect } from "react";
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

// Le pasamos dos funciones: una para crear y otra para borrar
const HerramientasDibujo = ({ onDibujoCreado, onDibujoBorrado }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    if (map.pm) {
      // 1. Añadir barra de controles
      map.pm.addControls({
        position: "topleft",
        drawMarker: false,
        drawCircleMarker: false,
        drawText: false,
        drawCircle: false,
        drawRectangle: false,
        editMode: true,
        dragMode: true,
        cutPolygon: false,
        removalMode: true, // Esto activa el botón de la papelera
      });

      // 2. Escuchar cuando SE CREA una figura
      map.on("pm:create", (e) => {
        const layer = e.layer;
        const tipo = e.shape;
        const coordenadas = layer.getLatLngs();

        onDibujoCreado({ tipo, coordenadas, layerId: L.stamp(layer) });
      });

      // 3. Escuchar cuando SE BORRA una figura con la papelera
      map.on("pm:remove", (e) => {
        const tipo = e.shape; // Nos dice si borró 'Polygon' o 'Line'
        onDibujoBorrado(tipo);
      });
    }

    return () => {
      if (map.pm) {
        map.pm.removeControls();
        map.off("pm:create");
        map.off("pm:remove");
      }
    };
  }, [map, onDibujoCreado, onDibujoBorrado]);

  return null;
};

const MapaTrazado = ({ onDatosDibujados, onDatosBorrados }) => {
  const centroInicial = [40.4168, -3.7038];

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
        center={centroInicial}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        <FeatureGroup>
          {/* Pasamos ambas funciones al componente interno */}
          <HerramientasDibujo
            onDibujoCreado={onDatosDibujados}
            onDibujoBorrado={onDatosBorrados}
          />
        </FeatureGroup>
      </MapContainer>
    </div>
  );
};

export default MapaTrazado;
