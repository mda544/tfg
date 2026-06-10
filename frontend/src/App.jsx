import { useState, useCallback } from "react";
import { useAuth } from "./auth/useAuth";
import { useRouteManager } from "./hooks/useRouteManager";
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

  const [conductor, setConductor] = useState(DEFAULT_CONDUCTORS[0]);
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [climateSource, setClimateSource] = useState("openmeteo");
  const [lineName, setLineName] = useState("");
  const [caseName, setCaseName] = useState("");

  const {
    mapRef,
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    studyCaseId,
    saving,
    saveError,

    loadRoute,
    resyncClimate,
    saveRoute,
    clear,
  } = useRouteManager(climateSource);

  const {
    calculate,
    result,
    loading: calculating,
    error: calcError,
  } = useCalculateRates();

  const handleRouteLoaded = useCallback(
    async (rawFeature) => {
      const { scenarios: newScenarios } = await loadRoute(rawFeature);
      if (newScenarios) setScenarios(newScenarios);
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

  const handleSave = useCallback(async () => {
    await saveRoute({
      lineName: lineName || `Línea ${new Date().toLocaleDateString()}`,
      caseName: caseName || `Estudio ${new Date().toLocaleDateString()}`,
      useDem: true,
    });
  }, [lineName, caseName, saveRoute]);

  const handleCalculate = useCallback(async () => {
    await calculate({
      studyCaseId,
      conductorId: conductor.id,
      scenarios,
      climateSource,
    });
  }, [studyCaseId, conductor, scenarios, climateSource, calculate]);

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
            onClear: clear,
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
            onRouteCleared={clear}
          />
          {result && <RatesResultsPanel result={result} />}
        </main>
      </div>
    </div>
  );
}
