import ConductorSelector    from "../conductor/ConductorSelector";
import GeometryUploader     from "../../components/GeometryUploader";
import SeasonalScenariosPanel from "../scenarios/SeasonalScenariosPanel";
import ValidationPanel      from "../../components/ValidationPanel";

export default function PanelConfig({
  conductor,            onConductorChange,
  scenarios,            onScenariosChange,
  useDem,               onUseDemChange,
  climateSource,        onClimateSourceChange,
  routeData,            validation,
  loadingClimate,       climateSlowLoad,
  onRouteLoaded,        onClear,
  onCalculate,          calculating,
  canCalculate,         calcError,
}) {
  return (
    <aside className="panel-configuracion">

      <section className="panel-section">
        <h2>Conductor</h2>
        <ConductorSelector selected={conductor?.id} onChange={onConductorChange} />
      </section>

      <section className="panel-section">
        <h2>Opciones de cálculo</h2>
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={useDem}
            onChange={(e) => onUseDemChange(e.target.checked)}
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
        <select className="select-field" value={climateSource} onChange={onClimateSourceChange}>
          <option value="openmeteo">Copernicus ERA5/ERA5-Land (Open-Meteo) — 9-25 km</option>
          <option value="nasa">MERRA-2 (NASA POWER) — ~50 km</option>
        </select>
      </section>

      <section className="panel-section">
        <h2>Geometría</h2>
        <GeometryUploader onRouteLoaded={onRouteLoaded} />
        <button className="btn-secondary" onClick={onClear}>Limpiar mapa</button>
        <div className="estado-mapa">
          {routeData
            ? <p className="ok">Trazado listo · {routeData.coordinates.length} apoyos</p>
            : <p className="espera">Dibuja o carga un trazado en el mapa</p>
          }
        </div>
        {loadingClimate && climateSlowLoad && (
          <div className="clima-banner">Consultando datos climáticos históricos…</div>
        )}
      </section>

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

      <button className="btn-calcular" onClick={onCalculate} disabled={!canCalculate}>
        {calculating ? "Calculando…" : "Calcular rates estacionales"}
      </button>

    </aside>
  );
}