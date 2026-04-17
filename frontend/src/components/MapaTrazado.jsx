import { useEffect } from "react";
import { MapContainer, TileLayer, FeatureGroup, useMap } from "react-leaflet";
import L from "leaflet";
import "@geoman-io/leaflet-geoman-free";
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";
import "leaflet/dist/leaflet.css";

// Configuración de los iconos de Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl:
    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Dos funciones: una para crear y otra para borrar
const HerramientasDibujo = ({ onDibujoCreado, onDibujoBorrado }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    if (map.pm) {
      // Añadir barra de controles
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
        removalMode: true, // Botón de la papelera
      });

      // Escuchar cuando se crea una figura
      map.on("pm:create", (e) => {
        const layer = e.layer;
        const tipo = e.shape;
        const coordenadas = layer.getLatLngs();

        onDibujoCreado({ tipo, coordenadas, layerId: L.stamp(layer) });
      });

      // Escuchar cuando se borra una figura con la papelera
      map.on("pm:remove", (e) => {
        const tipo = e.shape; // Nos dice si borró 'Polygon' o 'Line'
        onDibujoBorrado(tipo);
      });
    }

    // Cleanup function al desmontar el componente
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
  const centroInicial = [40.4168, -3.7038]; // Centro Madrid

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
