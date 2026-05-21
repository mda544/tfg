import { useState, useCallback }     from "react";
import { useAuth }                    from "./auth/useAuth";
import { useRoute }                   from "./hooks/useRoute";
import { useCalculateRates }          from "./hooks/useCalculateRates";
import { DEFAULT_CONDUCTORS }         from "./features/conductor/conductorData";
import { DEFAULT_SCENARIOS }          from "./features/scenarios/scenarioDefaults";

import AppHeader          from "./components/AppHeader";
import PanelConfig        from "./features/calculator/PanelConfig";
import RouteMap           from "./features/map/RouteMap";
import RatesResultsPanel  from "./features/results/RatesResultsPanel";
import "./App.css";

export default function App() {
  const { logout, session } = useAuth();

  const [conductor,     setConductor]     = useState(DEFAULT_CONDUCTORS[0]);
  const [scenarios,     setScenarios]     = useState(DEFAULT_SCENARIOS);
  const [useDem,        setUseDem]        = useState(true);
  const [climateSource, setClimateSource] = useState("openmeteo");

  const {
    mapRef,
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    loadRoute,
    clear,
    resyncClimate,
  } = useRoute(climateSource);

  const {
    calculate,
    result,
    loading: calculating,
    error:   calcError,
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

  const handleCalculate = useCallback(async () => {
    if (!routeData || validation?.valid === false) return;
    await calculate({ coordinates: routeData.coordinates, conductor, scenarios, useDem });
  }, [routeData, validation, conductor, scenarios, useDem, calculate]);

  const canCalculate = Boolean(routeData) && validation?.valid !== false && !calculating;

  return (
    <div className="app-container">
      <AppHeader username={session?.user?.username} onLogout={logout} />

      <div className="contenido-principal">
        <PanelConfig
          conductor={conductor}             onConductorChange={setConductor}
          scenarios={scenarios}             onScenariosChange={setScenarios}
          useDem={useDem}                   onUseDemChange={setUseDem}
          climateSource={climateSource}     onClimateSourceChange={handleClimateSourceChange}
          routeData={routeData}             validation={validation}
          loadingClimate={loadingClimate}   climateSlowLoad={climateSlowLoad}
          onRouteLoaded={handleRouteLoaded} onClear={clear}
          onCalculate={handleCalculate}     calculating={calculating}
          canCalculate={canCalculate}       calcError={calcError}
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