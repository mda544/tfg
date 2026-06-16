import ConductorSelector from "../conductor/ConductorSelector";
import { haversineM } from "../../utils/geometryValidator";
import GeometryUploader from "../../components/GeometryUploader";
import LineSelector from "../lines/LineSelector";
import StudyCaseSelector from "../lines/StudyCaseSelector";
import CalculationSelector from "../lines/CalculationSelector";
import SeasonalScenariosPanel from "../scenarios/SeasonalScenariosPanel";
import ValidationPanel from "../../components/ValidationPanel";

export default function PanelConfig({
  route: {
    data: routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    onLoaded,
    onSavedLineLoaded,
    onClear,
  },
  studyCaseSelector: {
    show: showStudyCaseSelector,
    studyCases,
    loading: loadingStudyCases,
    selectedId: studyCaseSelectedId,
    onSelect: onStudyCaseSelect,
    onCreate: onStudyCaseCreate,
    disabled: studyCaseSelectorDisabled,
  },
  calculationSelector: {
    show: showCalculationSelector,
    calculations,
    loading: loadingCalculations,
    selectedId: calcSelectedId,
    onSelect: onCalcSelect,
    onNew: onCalcNew,
    disabled: calcSelectorDisabled,
  },
  save: {
    lineName,
    caseName,
    onLineNameChange,
    onCaseNameChange,
    segmentStep,
    onSegmentStepChange,
    onSave,
    saving,
    error: saveError,
    studyCaseId,
    canSave,
  },
  conductor: { value: conductor, onChange: onConductorChange },
  climate: { source: climateSource, onChange: onClimateSourceChange },
  calculator: {
    scenarios,
    apiDefaults,
    onScenariosChange,
    onCalculate,
    calculating,
    canCalculate,
    error: calcError,
  },
}) {
  return (
    <aside className="panel-configuracion">
      <section className="panel-section">
        <h2>Conductor</h2>
        <ConductorSelector
          selected={conductor?.id}
          onChange={onConductorChange}
        />
      </section>

      <section className="panel-section">
        <h2>Opciones de cálculo</h2>
        <label className="field-label">Fuente climática histórica</label>
        <select
          className="select-field"
          value={climateSource}
          onChange={onClimateSourceChange}
        >
          <option value="openmeteo">
            Copernicus ERA5/ERA5-Land (Open-Meteo) — 9-25 km
          </option>
          <option value="nasa">MERRA-2 (NASA POWER) — ~50 km</option>
        </select>
      </section>

      <section className="panel-section">
        <h2>Geometría</h2>
        <LineSelector
          onLineLoaded={onSavedLineLoaded}
          disabled={Boolean(routeData)}
        />
        {showStudyCaseSelector && (
          <StudyCaseSelector
            studyCases={studyCases}
            loading={loadingStudyCases}
            selectedId={studyCaseSelectedId}
            onSelect={onStudyCaseSelect}
            onCreate={onStudyCaseCreate}
            disabled={studyCaseSelectorDisabled}
          />
        )}
        {showCalculationSelector && (
          <CalculationSelector
            calculations={calculations}
            loading={loadingCalculations}
            selectedId={calcSelectedId}
            onSelect={onCalcSelect}
            onNew={onCalcNew}
            disabled={calcSelectorDisabled}
          />
        )}
        {!routeData && <GeometryUploader onRouteLoaded={onLoaded} />}
        <button className="btn-secondary" onClick={onClear}>
          Limpiar mapa
        </button>
        <div className="estado-mapa">
          {routeData ? (
            <>
              {routeData.propiedades?.nombre && (
                <p className="ok" style={{ fontWeight: "bold" }}>
                  {routeData.propiedades.nombre}
                </p>
              )}
              <p className="ok">
                {(() => {
                  const fuente = routeData.propiedades?.fuente;
                  const termino =
                    fuente === "excel" || fuente === "geojson"
                      ? "apoyos"
                      : "vértices";
                  const n =
                    routeData.propiedades?.n_apoyos ??
                    routeData.coordinates.length;
                  const km = routeData.propiedades?.length_km;
                  return `Trazado listo · ${n} ${termino}${km ? ` · ${km.toFixed(1)} km` : ""}`;
                })()}
              </p>
            </>
          ) : (
            <p className="espera">Dibuja o carga un trazado en el mapa</p>
          )}
        </div>
        {loadingClimate && climateSlowLoad && (
          <div className="clima-banner">
            Consultando datos climáticos históricos…
          </div>
        )}
      </section>

      <section className="panel-section">
        <h2>Guardar línea</h2>
        <label className="field-label">Nombre de la línea</label>
        <input
          className="input-field"
          type="text"
          placeholder="Ej: Corredoria - Grado"
          value={lineName}
          onChange={(e) => onLineNameChange(e.target.value)}
        />
        <label className="field-label" style={{ marginTop: "8px" }}>
          Nombre del caso de estudio
        </label>
        <input
          className="input-field"
          type="text"
          placeholder="Ej: Estudio verano 2024"
          value={caseName}
          onChange={(e) => onCaseNameChange(e.target.value)}
        />
        {/* Paso de segmentación — solo cuando no hay vanos reales del Excel */}
        {routeData &&
          (routeData.propiedades?.puntos_singulares?.length ?? 0) < 2 && (
            <>
              <label className="field-label" style={{ marginTop: "8px" }}>
                Paso de segmentación (m)
              </label>
              <div
                style={{ display: "flex", gap: "8px", alignItems: "center" }}
              >
                <input
                  className="input-field"
                  type="number"
                  min={50}
                  max={500}
                  step={50}
                  value={segmentStep}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    if (v >= 50 && v <= 500) onSegmentStepChange(v);
                  }}
                  style={{ width: "100px" }}
                />
                <span style={{ fontSize: "12px", color: "#64748b" }}>
                  {(() => {
                    // Calcular longitud desde coordenadas si no está en propiedades
                    const coords = routeData?.coordinates;
                    if (!coords || coords.length < 2) return "— tramos";
                    const lengthM = coords.reduce(
                      (acc, c, i) =>
                        i === 0 ? 0 : acc + haversineM(coords[i - 1], c),
                      0,
                    );
                    return `≈ ${Math.max(1, Math.round(lengthM / segmentStep))} tramos · ${(lengthM / 1000).toFixed(1)} km`;
                  })()}
                </span>
              </div>
            </>
          )}
        {saveError && <div className="error-banner">Error: {saveError}</div>}
        {studyCaseId ? (
          <p className="ok" style={{ marginTop: "8px" }}>
            Línea y estudio guardados
          </p>
        ) : (
          <button
            className="btn-secondary"
            onClick={onSave}
            disabled={!canSave}
            style={{ marginTop: "8px" }}
          >
            {saving ? "Guardando…" : "Guardar línea y crear caso de estudio"}
          </button>
        )}
      </section>

      <section className="panel-section">
        <h2>Escenarios estacionales</h2>
        <SeasonalScenariosPanel
          conductorRef={conductor}
          escenarios={scenarios}
          apiDefaults={apiDefaults}
          onChange={onScenariosChange}
        />
      </section>

      <ValidationPanel validation={validation} />

      {calcError && <div className="error-banner">Error: {calcError}</div>}

      <button
        className="btn-calcular"
        onClick={onCalculate}
        disabled={!canCalculate}
      >
        {calculating ? "Calculando…" : "Calcular rates estacionales"}
      </button>
    </aside>
  );
}
