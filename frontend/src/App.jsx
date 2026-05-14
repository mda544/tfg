import { useState, useRef, useCallback } from "react";
import { useAuth } from "./auth/useAuth";
import MapaTrazado from "./features/map/MapaTrazado";
import GeometryUploader from "./components/GeometryUploader";
import PanelEscenariosEstacionales from "./features/scenarios/PanelEscenariosEstacionales";
import PanelValidacion from "./components/PanelValidacion";
import PanelResultadosRates from "./features/results/PanelResultadosRates";
import ConductorSelector from "./features/conductor/ConductorSelector";
import { useConductors } from "./hooks/useConductors";
import { useClimateSync } from "./hooks/useClimateSync";
import { useRateCalculation } from "./hooks/useRateCalculation";
import {
  validarTrazado,
  densificarTrazado,
  normalizarALatLon,
} from "./utils/geometryValidator";
import { ESCENARIOS_DEFAULT } from "./features/scenarios/scenarioDefaults";
import "./App.css";

export default function App() {
  const mapaRef = useRef(null);
  const { logout, session } = useAuth();

  // Estado de trazado
  const [datosMapa, setDatosMapa] = useState(null);
  const [validacion, setValidacion] = useState(null);

  // Estado de configuración
  const [escenarios, setEscenarios] = useState(ESCENARIOS_DEFAULT);
  const [useDem, setUseDem] = useState(true);
  const [fuenteClima, setFuenteClima] = useState("openmeteo");

  // Conductor seleccionado (objeto completo del backend)
  const { conductors } = useConductors();
  const [conductorId, setConductorId] = useState(null);
  const conductor = conductors.find((c) => c.id === conductorId) ?? conductors[0];

  // Hooks de negocio
  const { sync: syncClima, loading: cargandoClima } = useClimateSync();
  const {
    calculate,
    resultado,
    loading: calculando,
    error: errorCalculo,
  } = useRateCalculation();

  // Helpers de trazado
  const procesarCoordenadas = useCallback(async (rawCoords) => {
    const normalizadas = normalizarALatLon(rawCoords);
    const densas = densificarTrazado(normalizadas, 500);
    setValidacion(validarTrazado(densas));
    return densas;
  }, []);

  const sincronizarClima = useCallback(
    async (coordenadas, fuente) => {
      const nuevosEscenarios = await syncClima(
        coordenadas,
        fuente ?? fuenteClima,
      );
      if (nuevosEscenarios) setEscenarios(nuevosEscenarios);
    },
    [syncClima, fuenteClima],
  );

  // Eventos del mapa
  const manejarNuevosDibujos = useCallback(
    async (datos) => {
      const densas = await procesarCoordenadas(datos.coordenadas);
      const feature = { ...datos, coordenadas: densas };
      setDatosMapa(feature);
      mapaRef.current?.dibujarGeometria(feature);
      sincronizarClima(densas);
    },
    [procesarCoordenadas, sincronizarClima],
  );

  const manejarGeometriaCargada = useCallback(
    async (featureOArray) => {
      const feature = Array.isArray(featureOArray)
        ? featureOArray[0]
        : featureOArray;
      const densas = await procesarCoordenadas(feature.coordenadas);
      const featureFinal = { ...feature, coordenadas: densas };
      setDatosMapa(featureFinal);
      mapaRef.current?.dibujarGeometria(featureFinal);
      sincronizarClima(densas);
    },
    [procesarCoordenadas, sincronizarClima],
  );

  const manejarBorrado = useCallback(() => {
    setDatosMapa(null);
    setValidacion(null);
  }, []);

  const borrarTodoElMapa = useCallback(() => {
    mapaRef.current?.limpiarTodo();
    setDatosMapa(null);
    setValidacion(null);
  }, []);

  // Cambio de fuente climática
  const manejarCambioFuenteClima = useCallback(
    (e) => {
      const nueva = e.target.value;
      setFuenteClima(nueva);
      if (datosMapa?.coordenadas)
        sincronizarClima(datosMapa.coordenadas, nueva);
    },
    [datosMapa, sincronizarClima],
  );

  // Cálculo
  const calcular = useCallback(async () => {
    if (!datosMapa || !conductor || validacion?.valido === false) return;
    await calculate({
      coordenadas: datosMapa.coordenadas,
      conductor,
      escenarios,
      useDem,
    });
  }, [datosMapa, conductor, escenarios, useDem, validacion, calculate]);

  const puedeCalcular =
    Boolean(datosMapa) && validacion?.valido !== false && !calculando;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <span className="header-icon">⚡</span>
          <h1>AmpacityGIS</h1>
        </div>
        <div className="header-user">
          <span>{session?.user?.username}</span>
          <button className="btn-logout" onClick={logout}>
            Cerrar sesión
          </button>
        </div>
      </header>

      <div className="contenido-principal">
        {/* ── PANEL IZQUIERDO ── */}
        <aside className="panel-configuracion">
          <section className="panel-section">
            <h2>Conductor</h2>
            <ConductorSelector
              selected={conductorId}
              onChange={(c) => setConductorId(c.id)}
            />
          </section>

          <section className="panel-section">
            <h2>Opciones de cálculo</h2>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={useDem}
                onChange={(e) => setUseDem(e.target.checked)}
              />
              <span>Consultar altitud DEM</span>
            </label>
            <p className="hint-text">
              {useDem
                ? "Se consultará la altitud via API. Si el Excel tiene columna Z, se usa directamente."
                : "Todos los tramos se calculan a 0 m de altitud."}
            </p>

            <label className="field-label" style={{ marginTop: "10px" }}>
              Fuente climática histórica
            </label>
            <select
              className="select-field"
              value={fuenteClima}
              onChange={manejarCambioFuenteClima}
            >
              <option value="openmeteo">
                Copernicus ERA5 (Open-Meteo) — 9 km
              </option>
              <option value="nasa">
                MERRA-2 (NASA POWER) — ~50 km
              </option>
            </select>
          </section>

          <section className="panel-section">
            <h2>Geometría</h2>
            <GeometryUploader onGeometriaCargada={manejarGeometriaCargada} />
            <button className="btn-secondary" onClick={borrarTodoElMapa}>
              Limpiar mapa
            </button>
            <div className="estado-mapa">
              {datosMapa ? (
                <p className="ok">
                  Trazado listo · {datosMapa.coordenadas.length} apoyos
                </p>
              ) : (
                <p className="espera"> Dibuja o carga un trazado en el mapa</p>
              )}
            </div>
            {cargandoClima && (
              <div className="clima-banner">
                Consultando datos climáticos históricos…
              </div>
            )}
          </section>

          <section className="panel-section">
            <h2>Escenarios estacionales</h2>
            <PanelEscenariosEstacionales
              conductorRef={conductor}
              escenarios={escenarios}
              onChange={setEscenarios}
            />
          </section>

          <PanelValidacion validacion={validacion} />

          {errorCalculo && (
            <div className="error-banner">Error: {errorCalculo}</div>
          )}

          <button
            className="btn-calcular"
            onClick={calcular}
            disabled={!puedeCalcular}
          >
            {calculando ? " Calculando…" : "Calcular rates estacionales"}
          </button>
        </aside>

        {/* ── PANEL DERECHO ── */}
        <main className="mapa-wrapper">
          <MapaTrazado
            ref={mapaRef}
            onDatosDibujados={manejarNuevosDibujos}
            onDatosBorrados={manejarBorrado}
          />
          {resultado && <PanelResultadosRates resultado={resultado} />}
        </main>
      </div>
    </div>
  );
}
