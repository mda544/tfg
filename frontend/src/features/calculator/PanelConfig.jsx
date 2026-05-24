import ConductorSelector from "../conductor/ConductorSelector";
import GeometryUploader from "../../components/GeometryUploader";
import SeasonalScenariosPanel from "../scenarios/SeasonalScenariosPanel";
import ValidationPanel from "../../components/ValidationPanel";

/**
 * Props agrupadas por responsabilidad:
 *  route     — estado y callbacks del trazado
 *  save      — guardar línea y crear caso de estudio
 *  conductor — conductor seleccionado
 *  climate   — fuente climática
 *  calculator — escenarios y cálculo
 */
export default function PanelConfig({
  route: {
    data: routeData,
    validation,
    loadingClimate,
    climateSlowLoad,
    onLoaded,
    onClear,
  },
  save: {
    lineName,
    caseName,
    onLineNameChange,
    onCaseNameChange,
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
    onScenariosChange,
    onCalculate,
    calculating,
    canCalculate,
    error: calcError,
  },
}) {
  return (
    <aside className="panel-configuracion">
      {/* Conductor */}
      <section className="panel-section">
        <h2>Conductor</h2>
        <ConductorSelector
          selected={conductor?.id}
          onChange={onConductorChange}
        />
      </section>

      {/* Opciones */}
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

      {/* Geometría */}
      <section className="panel-section">
        <h2>Geometría</h2>
        <GeometryUploader onRouteLoaded={onLoaded} />
        <button className="btn-secondary" onClick={onClear}>
          Limpiar mapa
        </button>
        <div className="estado-mapa">
          {routeData ? (
            <p className="ok">
              Trazado listo · {routeData.coordinates.length} apoyos
            </p>
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

      {/* Guardar línea */}
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
        {saveError && <div className="error-banner">Error: {saveError}</div>}
        {studyCaseId ? (
          <p className="ok" style={{ marginTop: "8px" }}>
            ✓ Línea y estudio guardados
          </p>
        ) : (
          <button
            className="btn-secondary"
            onClick={onSave}
            disabled={!canSave}
            style={{ marginTop: "8px" }}
          >
            {saving ? "Guardando…" : "Guardar línea y crear estudio"}
          </button>
        )}
      </section>

      {/* Escenarios */}
      <section className="panel-section">
        <h2>Escenarios estacionales</h2>
        <SeasonalScenariosPanel
          conductorRef={conductor}
          escenarios={scenarios}
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
