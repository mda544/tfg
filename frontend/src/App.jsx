import { useState, useCallback, useEffect } from "react";
import { useAuth } from "./auth/useAuth";
import { useRouteManager } from "./hooks/useRouteManager";
import { useCalculateRates } from "./hooks/useCalculateRates";
import { useSavedLines } from "./hooks/useSavedLines";
import { useSavedStudyCases } from "./hooks/useSavedStudyCases";
import { useSavedCalculations } from "./hooks/useSavedCalculations";
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
  const [segmentStep, setSegmentStep] = useState(500);
  const [activeSavedLineId, setActiveSavedLineId] = useState(null);
  const [selectedCalcId, setSelectedCalcId] = useState(null);

  const {
    mapRef,
    routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    studyCaseId,
    saving,
    saveError,
    apiDefaults,
    loadRoute,
    loadSavedRoute,
    resyncClimate,
    saveRoute,
    clear,
    setStudyCaseId,
  } = useRouteManager(climateSource);

  const {
    lines,
    loading: loadingLines,
    error: linesError,
    refresh: refreshLines,
    loadLineGeoJSON,
  } = useSavedLines();

  const {
    studyCases,
    loading: loadingStudyCases,
    refresh: refreshStudyCases,
    reset: resetStudyCases,
  } = useSavedStudyCases();

  const {
    calculations,
    loading: loadingCalculations,
    refresh: refreshCalculations,
    reset: resetCalculations,
  } = useSavedCalculations();

  const {
    calculate,
    result,
    setResult,
    loading: calculating,
    error: calcError,
  } = useCalculateRates();

  // Handlers

  const handleRouteLoaded = useCallback(
    async (rawFeature) => {
      setActiveSavedLineId(null);
      resetStudyCases();
      resetCalculations();
      setSelectedCalcId(null);
      const { scenarios: s } = await loadRoute(rawFeature);
      if (s) setScenarios(s);
    },
    [loadRoute, resetStudyCases, resetCalculations],
  );

  const handleSavedLineLoaded = useCallback(
    async (feature) => {
      const lineId = feature._savedLine?.id ?? null;
      setActiveSavedLineId(lineId);
      resetCalculations();
      setSelectedCalcId(null);
      const { scenarios: s } = await loadSavedRoute(feature, null);
      if (s) setScenarios(s);
      if (lineId) await refreshStudyCases(lineId);
    },
    [loadSavedRoute, refreshStudyCases, resetCalculations],
  );

  const handleStudyCaseSelected = useCallback(
    async (sc) => {
      setStudyCaseId(sc.id);
      setSelectedCalcId(null);
      if (sc.conductor) setConductor(sc.conductor);
      await refreshCalculations(sc.id);
    },
    [setStudyCaseId, refreshCalculations],
  );

  const handleCreateNewStudyCase = useCallback(() => {
    setStudyCaseId(null);
    resetCalculations();
    setSelectedCalcId(null);
  }, [setStudyCaseId, resetCalculations]);

  const handleCalculationSelected = useCallback(
    (calc) => {
      setSelectedCalcId(calc.id);
      setResult(calc);
      if (calc.season_results?.length) {
        const loadedScenarios = Object.fromEntries(
          calc.season_results.map((sr) => [
            sr.season,
            {
              temp: sr.weather_input?.temp_amb_c,
              viento: sr.weather_input?.wind_speed_ms,
              radiacion: sr.weather_input?.solar_radiation_wm2,
              angulo: sr.weather_input?.wind_angle_deg ?? 90,
              wind_dir_predominant_deg:
                sr.weather_input?.wind_dir_predominant_deg ?? null,
            },
          ]),
        );
        setScenarios(loadedScenarios);
      }
    },
    [setResult],
  );

  const handleNewCalculation = useCallback(() => {
    setSelectedCalcId(null);
    setResult(null);
    if (apiDefaults) setScenarios(apiDefaults);
    if (routeData) mapRef.current?.drawRoute(routeData);
  }, [setResult, apiDefaults, routeData, mapRef]);

  const handleClimateSourceChange = useCallback(
    async (e) => {
      const source = e.target.value;
      setClimateSource(source);
      const s = await resyncClimate(source);
      if (s) setScenarios(s);
    },
    [resyncClimate],
  );

  const handleSave = useCallback(async () => {
    const newId = await saveRoute({
      lineName: lineName || `Línea ${new Date().toLocaleDateString()}`,
      caseName: caseName || `Estudio ${new Date().toLocaleDateString()}`,
      conductorId: conductor?.id,
      segmentStep: segmentStep,
      useDem: true,
    });
    if (newId) {
      await refreshLines();
    }
    if (newId && activeSavedLineId) {
      await refreshStudyCases(activeSavedLineId);
    }
  }, [
    lineName,
    caseName,
    conductor,
    segmentStep,
    saveRoute,
    activeSavedLineId,
    refreshStudyCases,
    refreshLines,
  ]);

  const handleCalculate = useCallback(async () => {
    const calc = await calculate({ studyCaseId, scenarios, climateSource });
    if (calc) {
      setSelectedCalcId(calc.id);
      await refreshCalculations(studyCaseId);
    }
  }, [studyCaseId, scenarios, climateSource, calculate, refreshCalculations]);

  const handleClear = useCallback(() => {
    clear();
    setActiveSavedLineId(null);
    resetStudyCases();
    resetCalculations();
    setSelectedCalcId(null);
    setResult(null);
  }, [clear, resetStudyCases, resetCalculations, setResult]);

  useEffect(() => {
    if (!result?.season_results?.length) return;
    const verano =
      result.season_results.find((sr) => sr.season === "verano") ??
      result.season_results[0];
    if (verano?.segments?.length) {
      const singulars = routeData?.propiedades?.support_metadata ?? [];
      mapRef.current?.drawSegments(verano.segments, singulars);
    }
  }, [result, mapRef, routeData]);

  // Derived state

  const canSave =
    Boolean(routeData) &&
    Boolean(conductor?.id) &&
    validation?.valid !== false &&
    !saving &&
    !studyCaseId;

  const canCalculate =
    Boolean(studyCaseId) && !calculating && selectedCalcId === null;

  const showStudyCaseSelector =
    Boolean(activeSavedLineId) && Boolean(routeData);
  const showCalculationSelector =
    Boolean(studyCaseId) && Boolean(activeSavedLineId);

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
            onSavedLineLoaded: handleSavedLineLoaded,
            onClear: handleClear,
          }}
          lineSelector={{
            lines,
            loading: loadingLines,
            error: linesError,
            loadLineGeoJSON,
          }}
          studyCaseSelector={{
            show: showStudyCaseSelector,
            studyCases,
            loading: loadingStudyCases,
            selectedId: studyCaseId,
            onSelect: handleStudyCaseSelected,
            onCreate: handleCreateNewStudyCase,
            disabled: calculating,
          }}
          calculationSelector={{
            show: showCalculationSelector,
            calculations,
            loading: loadingCalculations,
            selectedId: selectedCalcId,
            onSelect: handleCalculationSelected,
            onNew: handleNewCalculation,
            disabled: calculating,
          }}
          save={{
            lineName,
            caseName,
            onLineNameChange: setLineName,
            onCaseNameChange: setCaseName,
            segmentStep,
            onSegmentStepChange: setSegmentStep,
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
            apiDefaults,
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
