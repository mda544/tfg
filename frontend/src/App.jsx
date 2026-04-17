import { useState } from "react";
import { enviarCalculoRendimiento } from "./services/api";
import MapaTrazado from "./components/MapaTrazado";
import "./App.css";
import { useRef } from "react";
import GeometryUploader from "./components/GeometryUploader";
import PanelEscenariosEstacionales, { ESCENARIOS_DEFAULT } from "./components/PanelEscenariosEstacionales";

function App() {
  const [datosMapa, setDatosMapa] = useState(null);

  const manejarNuevosDibujos = (datos) => {
    setDatosMapa(datos);
  };

  const manejarBorrado = (tipoBorrado) => {
    setDatosMapa(null);
    console.log(`El usuario ha borrado: ${tipoBorrado}`);
  };

  const [configCable, setConfigCable] = useState({
    diametro: 28.1,
    resistencia: 0.072,
    emisividad: 0.5,
    temp_max: 90,
    altura_cable: 20,
  });

  const [errores, setErrores] = useState({
    diametro: "",
    resistencia: "",
    emisividad: "",
    temp_max: "",
    altura_cable: "",
  });

  const manejarCambioInput = (e) => {
    const { name, value } = e.target;

    // Permitimos que borren la casilla temporalmente (se queda vacía)
    const numValue = value === "" ? "" : parseFloat(value);

    let mensajeError = "";

    // Si escriben letras o símbolos raros que no son números
    if (isNaN(numValue) && value !== "") {
      mensajeError = "Debe ser un número válido.";
    }
    // Comprobamos los rangos y asignamos el aviso
    else if (value !== "") {
      if (name === "diametro" && (numValue < 10 || numValue > 50)) {
        mensajeError = "El diámetro debe estar entre 10 y 50 mm.";
      }
      if (name === "resistencia" && (numValue <= 0 || numValue > 0.2)) {
        mensajeError = "Rango permitido: 0.001 - 0.2 Ω/km.";
      }
      if (name === "emisividad" && (numValue < 0 || numValue > 1)) {
        mensajeError = "La emisividad debe estar entre 0 y 1.";
      }
      if (name === "temp_max" && (numValue < 50 || numValue > 200)) {
        mensajeError = "La temperatura debe estar entre 50 y 200 °C.";
      }
      if (name === "altura_cable" && (numValue < 10 || numValue > 100)) {
        mensajeError = "La altura debe ser realista (10 - 100 m).";
      }
    }

    // Actualizamos el error (si hay error, se guarda; si no, se borra)
    setErrores((prev) => ({ ...prev, [name]: mensajeError }));

    // Actualizamos el valor para que la caja de texto muestre lo que el usuario teclea
    setConfigCable((prev) => ({ ...prev, [name]: value }));
  };

  // Si hay AL MENOS UN error en todo el formulario se bloquea el botón
  const hayErrores = Object.values(errores).some((error) => error !== "");

  const calcularRendimiento = async () => {
    if (!datosMapa) {
      alert("Por favor, traza primero el recorrido del cable en el mapa.");
      return;
    }

    try {
      //console.log("Preparando paquete para el servicio API...");

      // Empaquetamos los datos
      const paqueteDatos = {
        tipo: datosMapa.tipo,
        coordenadas: datosMapa.coordenadas,
        diametro: configCable.diametro || 0,
        resistencia: configCable.resistencia || 0,
        emisividad: configCable.emisividad || 0,
        temp_max: configCable.temp_max || 0,
        altura_cable: configCable.altura_cable || 0,
      };

      // LLAMAMOS AL ARCHIVO EXTERNO
      const respuestaServidor = await enviarCalculoRendimiento(paqueteDatos);

      // Mostramos el resultado
      console.log("Respuesta recibida:", respuestaServidor);
      alert(respuestaServidor.mensaje);
    } catch (error) {
      // Si el archivo api.js falla, el error llega hasta aquí
      alert(error.message);
    }
  };

  const mapaRef = useRef(null);

  const manejarGeometriaCargada = (featureOArray) => {
    // Si es array (varios features), tomamos el primero y avisamos
    const feature = Array.isArray(featureOArray)
      ? featureOArray[0]
      : featureOArray;
    mapaRef.current?.dibujarGeometria(feature);
    // El onDatosDibujados del mapa se dispara internamente → setDatosMapa se actualiza solo
  };

  const [escenarios, setEscenarios] = useState(ESCENARIOS_DEFAULT);

  const paqueteDatos = {
    coordenadas: datosMapa.coordenadas,
    conductor: { ...configCable },
    escenarios: Object.entries(escenarios).map(([estacion, s]) => ({
      estacion,
      temp_amb_c:          s.temp,
      vel_viento_ms:       s.viento,
      angulo_viento_deg:   s.angulo,
      radiacion_solar_wm2: s.radiacion,
    })),
    paso_segmentacion_m: 500,
  };

  return (
    <div className="app-container">
      <header>
        <h1>Calculadora de Rendimiento</h1>
        <p>Define los parámetros técnicos y traza la ruta en el mapa.</p>
      </header>
      <div className="contenido-principal">
        {/* PANEL IZQUIERDO */}
        <aside className="panel-configuracion">
          <h2>Ficha Técnica del Cable</h2>

          {/* Slider + Box */}
          <div className="grupo-input">
            <label>Diámetro Exterior (mm)</label>
            <div className="controles-duales">
              <input
                type="range"
                name="diametro"
                min="10"
                max="50"
                step="0.1"
                value={configCable.diametro}
                onChange={manejarCambioInput}
              />
              <input
                type="number"
                name="diametro"
                value={configCable.diametro}
                onChange={manejarCambioInput}
              />
            </div>
            {errores.diametro && (
              <span className="texto-error">{errores.diametro}</span>
            )}
          </div>

          <div className="grupo-input">
            <label>Resistencia AC (Ω/km)</label>
            <div className="controles-duales">
              <input
                type="range"
                name="resistencia"
                min="0.01"
                max="0.2"
                step="0.001"
                value={configCable.resistencia}
                onChange={manejarCambioInput}
              />
              <input
                type="number"
                name="resistencia"
                step="0.001"
                value={configCable.resistencia}
                onChange={manejarCambioInput}
              />
            </div>
            {errores.resistencia && (
              <span className="texto-error">{errores.resistencia}</span>
            )}
          </div>

          <div className="grupo-input">
            <label>Emisividad</label>
            <div className="controles-duales">
              <input
                type="range"
                name="emisividad"
                min="0"
                max="1"
                step="0.01"
                value={configCable.emisividad}
                onChange={manejarCambioInput}
              />
              <input
                type="number"
                name="emisividad"
                step="0.01"
                value={configCable.emisividad}
                onChange={manejarCambioInput}
              />
            </div>
            {errores.emisividad && (
              <span className="texto-error">{errores.emisividad}</span>
            )}
          </div>

          <div className="grupo-input">
            <label>Temp. Máxima (°C)</label>
            <div className="controles-duales">
              <input
                type="range"
                name="temp_max"
                min="50"
                max="120"
                step="1"
                value={configCable.temp_max}
                onChange={manejarCambioInput}
              />
              <input
                type="number"
                name="temp_max"
                value={configCable.temp_max}
                onChange={manejarCambioInput}
              />
            </div>
            {errores.temp_max && (
              <span className="texto-error">{errores.temp_max}</span>
            )}
          </div>

          <div className="grupo-input">
            <label>Altura del cable (m)</label>
            <div className="controles-duales">
              <input
                type="range"
                name="altura_cable"
                min="10"
                max="50"
                step="1"
                value={configCable.altura_cable}
                onChange={manejarCambioInput}
              />
              <input
                type="number"
                name="altura_cable"
                value={configCable.altura_cable}
                onChange={manejarCambioInput}
              />
            </div>
            {errores.altura_cable && (
              <span className="texto-error">{errores.altura_cable}</span>
            )}
          </div>

          <div className="estado-mapa">
            {datosMapa ? (
              <p className="ok"> Trazado listo para analizar</p>
            ) : (
              <p className="espera"> Esperando dibujo en el mapa...</p>
            )}
          </div>

          <GeometryUploader onGeometriaCargada={manejarGeometriaCargada} />

          <button
            className="btn-calcular"
            onClick={calcularRendimiento}
            disabled={!datosMapa || hayErrores}
          >
            Calcular Rendimiento
          </button>
        </aside>

        {/* PANEL DERECHO */}
        <main className="mapa-wrapper">
          <MapaTrazado
            ref={mapaRef}
            onDatosDibujados={manejarNuevosDibujos}
            onDatosBorrados={manejarBorrado}
          />
        </main>
      </div>{" "}
      {/* FIN DEL CONTENEDOR PRINCIPAL */}
    </div>
  );
}

export default App;
