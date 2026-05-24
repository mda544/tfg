import { useState, useRef, useCallback } from "react";
import { useAuth } from "./auth/useAuth";
import { useRoute } from "./hooks/useRoute";
import { useStudyCase } from "./hooks/useStudyCase";
import { useCalculateRates } from "./hooks/useCalculateRates";
import { DEFAULT_CONDUCTORS } from "./features/conductor/conductorData";
import { DEFAULT_SCENARIOS } from "./features/scenarios/scenarioDefaults";

import AppHeader from "./components/AppHeader";
import PanelConfig from "./features/calculator/PanelConfig";
import RouteMap from "./features/map/RouteMap";
import RatesResultsPanel from "./features/results/RatesResultsPanel";
import "./App.css";

export default function App() {
  const { logout, session } = useAuth();
  const mapRef = useRef(null);

  // Conductor completo — SeasonalScenariosPanel necesita los parámetros físicos
  // para el preview de ampacidad en tiempo real
  const [conductor, setConductor] = useState(DEFAULT_CONDUCTORS[0]);
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [climateSource, setClimateSource] = useState("openmeteo");
  const [lineName, setLineName] = useState("");
  const [caseName, setCaseName] = useState("");

  // Hook de trazado — solo geometría y clima, sin persistencia
  const {
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    loadRoute,
    resyncClimate,
    clear: clearRoute,
  } = useRoute(climateSource);

  // Hook de persistencia — POST /lines + POST /study-cases
  const {
    studyCaseId,
    saving,
    error: saveError,
    save: saveStudyCase,
    reset: resetStudyCase,
  } = useStudyCase();

  // Hook de cálculo
  const {
    calculate,
    result,
    loading: calculating,
    error: calcError,
  } = useCalculateRates();

  // Handlers

  const handleRouteLoaded = useCallback(
    async (rawFeature) => {
      const { feature, scenarios: newScenarios } = await loadRoute(rawFeature);
      if (newScenarios) setScenarios(newScenarios);
      mapRef.current?.drawRoute(feature);
    },
    [loadRoute],
  );

  const handleClimateSourceChange = useCallback(
    async (e) => {
      const source = e.target.value;
      setClimateSource(source);
      const newScenarios = await resyncClimate(source);
      if (newScenarios) setScenarios(newScenarios);
    },
    [resyncClimate],
  );

  const handleClear = useCallback(() => {
    mapRef.current?.clearAll();
    clearRoute();
    resetStudyCase();
  }, [clearRoute, resetStudyCase]);

  const handleSave = useCallback(async () => {
    if (!routeData || validation?.valid === false) return;
    await saveStudyCase(routeData.coordinates, {
      lineName: lineName || `Línea ${new Date().toLocaleDateString()}`,
      caseName: caseName || `Estudio ${new Date().toLocaleDateString()}`,
      useDem: true,
    });
  }, [routeData, validation, lineName, caseName, saveStudyCase]);

  const handleCalculate = useCallback(async () => {
    if (!studyCaseId || !conductor?.id || validation?.valid === false) return;
    await calculate({
      studyCaseId,
      conductorId: conductor.id,
      scenarios,
      climateSource,
    });
  }, [studyCaseId, conductor, scenarios, climateSource, validation, calculate]);

  const canSave =
    Boolean(routeData) &&
    validation?.valid !== false &&
    !saving &&
    !studyCaseId;
  const canCalculate =
    Boolean(studyCaseId) && Boolean(conductor?.id) && !calculating;

  return (
    <div className="app-container">
      <AppHeader username={session?.user?.username} onLogout={logout} />

      <div className="contenido-principal">
        <PanelConfig
          route={{
            data: routeData,
            validation,
            loadingClimate,
            climateSlowLoad,
            onLoaded: handleRouteLoaded,
            onClear: handleClear,
          }}
          save={{
            lineName,
            caseName,
            onLineNameChange: setLineName,
            onCaseNameChange: setCaseName,
            onSave: handleSave,
            saving,
            error: saveError,
            studyCaseId,
            canSave,
          }}
          conductor={{
            value: conductor,
            onChange: setConductor,
          }}
          climate={{
            source: climateSource,
            onChange: handleClimateSourceChange,
          }}
          calculator={{
            scenarios,
            onScenariosChange: setScenarios,
            onCalculate: handleCalculate,
            calculating,
            canCalculate,
            error: calcError,
          }}
        />

        <main className="mapa-wrapper">
          <RouteMap
            ref={mapRef}
            onRouteDrawn={handleRouteLoaded}
            onRouteCleared={handleClear}
          />
          {result && <RatesResultsPanel result={result} />}
        </main>
      </div>
    </div>
  );
}
