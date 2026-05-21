import {
  SEASON_LABEL,
  SEASON_COLOR,
  ELEVATION_SOURCE_LABEL,
  ampacityColor,
} from "./resultsUtils";
import "./RatesResultsPanel.css";

export default function RatesResultsPanel({ result }) {
  if (!result) return null;

  if (result.error) {
    return (
      <div className="prr-panel prr-error">
        <p className="prr-error-titulo">Error en el cálculo</p>
        <p className="prr-error-msg">{result.error}</p>
      </div>
    );
  }

  // Campos actualizados al nuevo backend
  const {
    design_rate_a,
    rates_by_season = {},
    segments = [],
    n_segments,
    conductor,
    route_info = {},
    warnings = [],
  } = result;

  const estaciones = Object.keys(rates_by_season);
  const tramoCritico = segments.reduce(
    (min, t) => (t.design_rate_a < min.design_rate_a ? t : min),
    segments[0] ?? { design_rate_a: Infinity, segment_id: "—" },
  );

  const ampacidades = segments.map((t) => t.design_rate_a);
  const hayVariacion =
    ampacidades.length > 1 &&
    Math.max(...ampacidades) - Math.min(...ampacidades) > 0.5;

  const fuenteAlt = route_info.elevation_source ?? "sin_altitud";
  const modoSeg = route_info.segment_mode ?? "";

  return (
    <div className="prr-panel">
      {/* Cabecera */}
      <div className="prr-cabecera">
        <div>
          <p className="prr-label">Rate de diseño de la línea</p>
          <p className="prr-rate-principal">
            {design_rate_a} <span>A</span>
          </p>
          <p className="prr-sublabel">
            Tramo crítico: {tramoCritico.segment_id}
            {tramoCritico.elevation_m > 0
              ? ` · ${tramoCritico.elevation_m} m s.n.m.`
              : ""}
            {" · "}
            {route_info.length_km ?? "?"} km
            {" · "}
            {n_segments} {modoSeg.includes("vanos") ? "vanos" : "tramos"}
          </p>
        </div>
        <div className="prr-badge-metodo">IEEE 738-2012</div>
      </div>

      {/* Criterio + fuente altitud */}
      <div className="prr-criterio">
        <span>
          Criterio: P90 temperatura / P10 viento. Rate = mínimo de todos los
          tramos.
        </span>
        <span
          className={`prr-dem-badge prr-dem-${fuenteAlt.includes("error") ? "error" : fuenteAlt === "sin_altitud" ? "off" : "ok"}`}
        >
          Altitud: {ELEVATION_SOURCE_LABEL[fuenteAlt] ?? fuenteAlt}
          {route_info.min_elevation_m !== undefined &&
            fuenteAlt !== "sin_altitud" &&
            ` · ${route_info.min_elevation_m}–${route_info.max_elevation_m} m`}
        </span>
      </div>

      {!hayVariacion && segments.length > 1 && fuenteAlt !== "sin_altitud" && (
        <div className="prr-aviso-plano">
          Todos los tramos tienen el mismo rate. Comprueba que el DEM devolvió
          altitudes variadas (altitud media: {route_info.avg_elevation_m ?? 0}{" "}
          m).
        </div>
      )}

      {/* Rates por estación */}
      <div className="prr-estaciones">
        {estaciones.map((est) => {
          const amp = rates_by_season[est];
          const c = ampacityColor(amp);
          return (
            <div
              key={est}
              className="prr-est-card"
              style={{ borderTop: `3px solid ${SEASON_COLOR[est]}` }}
            >
              <p className="prr-est-nombre">{SEASON_LABEL[est] ?? est}</p>
              <p
                className="prr-est-amp"
                style={{ color: c.text, background: c.bg }}
              >
                {amp} A
              </p>
              <p className="prr-est-sub">mínimo de tramos</p>
            </div>
          );
        })}
      </div>

      {/* Tabla de segmentos */}
      {segments.length > 0 && (
        <div className="prr-tabla-wrap">
          <table className="prr-tabla">
            <thead>
              <tr>
                <th>Tramo</th>
                <th>Long.</th>
                <th>Alt.</th>
                {estaciones.map((e) => (
                  <th key={e} style={{ color: SEASON_COLOR[e] }}>
                    {SEASON_LABEL[e]?.slice(0, 3)}.
                  </th>
                ))}
                <th>Diseño</th>
                <th>Conv.</th>
              </tr>
            </thead>
            <tbody>
              {segments.map((seg) => {
                const esCritico = seg.segment_id === tramoCritico.segment_id;
                const c = ampacityColor(seg.design_rate_a);
                const modo = seg.details?.[estaciones[0]]?.conv_mode ?? "—";
                const altitud = seg.elevation_m ?? 0;
                return (
                  <tr
                    key={seg.segment_id}
                    className={esCritico ? "prr-fila-critica" : ""}
                  >
                    <td className="prr-td-id">{seg.segment_id}</td>
                    <td>{seg.length_km} km</td>
                    <td className="prr-td-alt">
                      {altitud > 0 ? `${Math.round(altitud)} m` : "—"}
                    </td>
                    {estaciones.map((e) => (
                      <td key={e}>{seg.rates?.[e] ?? "—"} A</td>
                    ))}
                    <td>
                      <span
                        className="prr-pill"
                        style={{ background: c.bg, color: c.text }}
                      >
                        {seg.design_rate_a} A
                      </span>
                    </td>
                    <td className="prr-td-modo">{modo}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Advertencias del backend */}
      {warnings.length > 0 && (
        <div className="prr-advertencias">
          <p className="prr-adv-titulo">{warnings.length} advertencia(s)</p>
          <ul>
            {warnings.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Trazabilidad */}
      <div className="prr-trazabilidad">
        <p>
          Conductor: Ø{conductor?.diameter_mm} mm · R75=
          {conductor?.r_ac_75_ohm_km} Ω/km · R25={conductor?.r_ac_25_ohm_km}{" "}
          Ω/km · Tmax={conductor?.max_temp_c}°C · ε={conductor?.emissivity} · α=
          {conductor?.absorptivity}
        </p>
        <p>
          Modelo: IEEE Std 738-2012 · Régimen estacionario · Segmentación:{" "}
          {modoSeg} · Altitud: {ELEVATION_SOURCE_LABEL[fuenteAlt] ?? fuenteAlt}
        </p>
      </div>
    </div>
  );
}
