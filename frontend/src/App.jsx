import { useState, useRef } from "react";
import MapaTrazado from "./components/MapaTrazado";
import GeometryUploader from "./components/GeometryUploader";
import PanelEscenariosEstacionales, {
  ESCENARIOS_DEFAULT,
} from "./components/PanelEscenariosEstacionales";
import PanelValidacion from "./components/PanelValidacion";
import PanelResultadosRates from "./components/PanelResultadosRates";
import "./App.css";
import {
  validarTrazado,
  densificarTrazado,
  normalizarLeafletCoords,
} from "./utils/geometryValidator";
import { CATALOGO_CABLES } from "./constants/catalogoCables";
import {
  enviarCalculoRendimiento,
  obtenerClimatologiaHistorica,
} from "./services/api";

function App() {
  const mapaRef = useRef(null);

  const [datosMapa, setDatosMapa] = useState(null);
  const [escenarios, setEscenarios] = useState(ESCENARIOS_DEFAULT);
  const [tipoCable, setTipoCable] = useState("LA-280");
  const [configCable, setConfigCable] = useState({
    ...CATALOGO_CABLES["LA-280"],
    altura_cable: 20,
  });
  const [errorAltura, setErrorAltura] = useState("");
  const [resultadosCalculo, setResultadosCalculo] = useState(null);
  const [calculando, setCalculando] = useState(false);
  const [validacion, setValidacion] = useState(null);
  const [usarDEM, setUsarDEM] = useState(true);

  const [cargandoClima, setCargandoClima] = useState(false);

  // Control del mapa

  const manejarNuevosDibujos = (datos) => {
    // Geoman ya entrega coords normalizadas desde el nuevo onCreate,
    // pero por seguridad normalizamos igualmente
    const coordsPlanas = normalizarLeafletCoords(
      Array.isArray(datos.coordenadas)
        ? datos.coordenadas
        : [datos.coordenadas],
    );

    // Auto-segmentación: inserta puntos intermedios en vanos > 500 m
    const coordsDensas = densificarTrazado(coordsPlanas, 500);

    const datosFinal = { ...datos, coordenadas: coordsDensas };

    setDatosMapa(datosFinal);
    setValidacion(validarTrazado(coordsDensas));

    mapaRef.current?.dibujarGeometria(datosFinal);

    sincronizarClimaHistorico(coordsDensas);
  };

  const manejarBorrado = () => {
    setDatosMapa(null);
    setValidacion(null);
  };

  const borrarTodoElMapa = () => {
    mapaRef.current?.limpiarTodo();
    setDatosMapa(null);
    setResultadosCalculo(null);
    setValidacion(null);
  };

  const manejarGeometriaCargada = (featureOArray) => {
    const feature = Array.isArray(featureOArray)
      ? featureOArray[0]
      : featureOArray;

    // 1. Guardamos los datos del Excel en la memoria de React
    setDatosMapa(feature);

    // 2. Validamos la ruta
    setValidacion(validarTrazado(feature.coordenadas));

    mapaRef.current?.dibujarGeometria(feature);

    sincronizarClimaHistorico(feature.coordenadas);
  };

  // Control del cable

  const manejarSeleccionCable = (e) => {
    const modelo = e.target.value;
    setTipoCable(modelo);
    setConfigCable((prev) => ({ ...prev, ...CATALOGO_CABLES[modelo] }));
  };

  const manejarCambioAltura = (e) => {
    const { value } = e.target;
    const n = value === "" ? "" : parseFloat(value);
    setErrorAltura(
      isNaN(n) && value !== ""
        ? "Debe ser un número válido."
        : value !== "" && (n < 10 || n > 100)
          ? "La altura debe estar entre 10 y 100 m."
          : "",
    );
    setConfigCable((prev) => ({ ...prev, altura_cable: value }));
  };

  // Historicos

  const sincronizarClimaHistorico = async (coordenadas) => {
    if (!coordenadas || coordenadas.length === 0) return;

    const mid = coordenadas[Math.floor(coordenadas.length / 2)];
    const lat = mid.lat;
    const lon = mid.lng !== undefined ? mid.lng : mid.lon;

    setCargandoClima(true); // Encendemos el radar
    try {
      console.log(
        `[Frontend] Pidiendo clima histórico para: ${lat}, ${lon}...`,
      );

      const historico = await obtenerClimatologiaHistorica(lat, lon);
      if (!historico) throw new Error("El servidor no devolvió datos válidos.");

      console.log("[Frontend] Clima recibido perfectamente:", historico);

      const nuevosEscenarios = {};
      Object.entries(historico).forEach(([est, p]) => {
        nuevosEscenarios[est] = {
          temp: p.temp_p90_c,
          viento: p.viento_p10_ms,
          radiacion: p.radiacion_p90_wm2,
          angulo: 90,
        };
      });

      setEscenarios(nuevosEscenarios); // ¡Se mueven los sliders!
    } catch (err) {
      console.error("[Frontend] Fallo en auto-ajuste:", err);
      alert(
        `⚠️ No se pudo cargar el clima histórico del satélite.\nMotivo: ${err.message}\nSe usarán los valores por defecto.`,
      );
    } finally {
      setCargandoClima(false); // Apagamos el radar
    }
  };

  // Cálculo

  const calcularRendimiento = async () => {
    if (!datosMapa || validacion?.valido === false) return;

    setCalculando(true);
    setResultadosCalculo(null);

    const tieneZExcel = datosMapa.coordenadas.some((c) => (c.altitud ?? 0) > 0);
    const esFicheroReal = datosMapa.coordenadas.length > 10;

    const paqueteDatos = {
      coordenadas: datosMapa.coordenadas,
      conductor: {
        diametro_mm: configCable.diametro,
        r_ac_75_ohm_km: configCable.r_ac_75,
        r_ac_25_ohm_km: configCable.r_ac_25,
        emisividad: configCable.emisividad,
        absortividad: 0.5,
        temp_max_c: configCable.temp_max,
      },
      escenarios: Object.entries(escenarios).map(([estacion, s]) => ({
        estacion,
        temp_amb_c: s.temp,
        vel_viento_ms: s.viento,
        angulo_viento_deg: s.angulo,
        radiacion_solar_wm2: s.radiacion,
      })),
      paso_segmentacion_m: 500,
      usar_apoyos_reales: tieneZExcel || esFicheroReal,
      usar_dem: usarDEM && !tieneZExcel, // DEM solo si no hay Z del Excel
    };

    try {
      // Llamada limpia usando Axios a través de nuestro servicio
      const datos = await enviarCalculoRendimiento(paqueteDatos);

      setResultadosCalculo(datos);
    } catch (error) {
      setResultadosCalculo({ error: error.message });
    } finally {
      setCalculando(false);
    }
  };

  // Render

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

          <div className="grupo-input">
            <label style={{ fontWeight: "bold" }}>Seleccionar Conductor</label>
            <select
              value={tipoCable}
              onChange={manejarSeleccionCable}
              className="select-cable"
            >
              {Object.entries(CATALOGO_CABLES).map(([id, datos]) => (
                <option key={id} value={id}>
                  {datos.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="tarjeta-resumen">
            <p>
              <b>Diámetro:</b> {configCable.diametro} mm
            </p>
            <p>
              <b>R75:</b> {configCable.r_ac_75} Ω/km · <b>R25:</b>{" "}
              {configCable.r_ac_25} Ω/km
            </p>
            <p>
              <b>Emisividad:</b> {configCable.emisividad}
            </p>
            <p>
              <b>Temp. Máxima:</b> {configCable.temp_max} °C
            </p>
          </div>

          <div className="grupo-input">
            <label>Altura del cable instalada (m)</label>
            <div className="controles-duales">
              <input
                type="range"
                min="10"
                max="100"
                value={configCable.altura_cable}
                onChange={manejarCambioAltura}
              />
              <input
                type="number"
                value={configCable.altura_cable}
                onChange={manejarCambioAltura}
              />
            </div>
            {errorAltura && <span className="texto-error">{errorAltura}</span>}
          </div>

          {/* Toggle DEM */}
          <div className="grupo-input dem-toggle">
            <label className="dem-toggle-label">
              <input
                type="checkbox"
                checked={usarDEM}
                onChange={(e) => setUsarDEM(e.target.checked)}
              />
              <span>Consultar altitud DEM (Open-Meteo)</span>
            </label>
            <p className="dem-hint">
              {usarDEM
                ? "Se consultará la altitud de cada apoyo via API. Si el Excel tiene columna Z, se usa directamente."
                : "Todos los tramos se calculan a 0 m de altitud."}
            </p>
          </div>

          <GeometryUploader onGeometriaCargada={manejarGeometriaCargada} />

          <button className="btn-limpiar" onClick={borrarTodoElMapa}>
            🗑️ Limpiar Mapa
          </button>

          <div className="estado-mapa">
            {datosMapa ? (
              <p className="ok">
                ✓ Trazado listo · {datosMapa.coordenadas.length} apoyos
              </p>
            ) : (
              <p className="espera">⚠ Esperando dibujo en el mapa...</p>
            )}
          </div>

          {cargandoClima && (
            <div
              style={{
                background: "#e0f2fe",
                color: "#0284c7",
                padding: "10px",
                borderRadius: "6px",
                marginBottom: "15px",
                fontWeight: "bold",
                display: "flex",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <span className="spinner">📡</span>
              Consultando satélite (30 años de histórico)...
            </div>
          )}

          <PanelEscenariosEstacionales
            conductorRef={{
              diametro_mm: configCable.diametro,
              r_ac_75: configCable.r_ac_75,
              temp_max: configCable.temp_max,
            }}
            escenarios={escenarios}
            onChange={setEscenarios}
          />

          <PanelValidacion validacion={validacion} />

          <button
            className="btn-calcular"
            onClick={calcularRendimiento}
            disabled={
              !datosMapa ||
              errorAltura !== "" ||
              calculando ||
              validacion?.valido === false
            }
          >
            {calculando
              ? usarDEM &&
                !datosMapa?.coordenadas?.some((c) => (c.altitud ?? 0) > 0)
                ? "⏳ Consultando DEM y calculando..."
                : "⏳ Calculando..."
              : "Calcular Rendimiento"}
          </button>
        </aside>

        {/* PANEL DERECHO */}
        <main className="mapa-wrapper">
          <MapaTrazado
            ref={mapaRef}
            onDatosDibujados={manejarNuevosDibujos}
            onDatosBorrados={manejarBorrado}
          />
          {resultadosCalculo && (
            <PanelResultadosRates resultado={resultadosCalculo} />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
