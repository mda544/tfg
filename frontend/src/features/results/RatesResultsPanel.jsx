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

  const {
    design_rate,
    rate_summer,
    rate_autumn,
    rate_winter,
    rate_spring,
    segments = [],
    n_segments,
    conductor,
    climate_source,
    elevation_source = "none",
    warnings = [],
  } = result;

  const rates_by_season = {
    verano: rate_summer,
    otono: rate_autumn,
    invierno: rate_winter,
    primavera: rate_spring,
  };

  const seasons = Object.keys(rates_by_season).filter(
    (k) => rates_by_season[k] != null,
  );

  const criticalSegment = segments.reduce(
    (min, t) => (t.design_rate < min.design_rate ? t : min),
    segments[0] ?? { design_rate: Infinity, segment_id: "—" },
  );

  const ampacidades = segments.map((t) => t.design_rate);
  const hasVariation =
    ampacidades.length > 1 &&
    Math.max(...ampacidades) - Math.min(...ampacidades) > 0.5;

  const fuenteAlt = elevation_source ?? "none";

  return (
    <div className="prr-panel">
      {/* Cabecera */}
      <div className="prr-cabecera">
        <div>
          <p className="prr-label">Rate de diseño de la línea</p>
          <p className="prr-rate-principal">
            {design_rate} <span>A</span>
          </p>
          <p className="prr-sublabel">
            Tramo crítico: {criticalSegment.segment_id}
            {criticalSegment.elevation_m > 0
              ? ` · ${criticalSegment.elevation_m} m s.n.m.`
              : ""}
            {" · "}
            {n_segments} tramos
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
          className={`prr-dem-badge prr-dem-${
            fuenteAlt.includes("error")
              ? "error"
              : fuenteAlt === "none"
                ? "off"
                : "ok"
          }`}
        >
          Altitud: {ELEVATION_SOURCE_LABEL[fuenteAlt] ?? fuenteAlt}
        </span>
      </div>

      {!hasVariation && segments.length > 1 && fuenteAlt !== "none" && (
        <div className="prr-aviso-plano">
          Todos los tramos tienen el mismo rate.
        </div>
      )}

      {/* Rates por estación */}
      <div className="prr-estaciones">
        {seasons.map((season) => {
          const amp = rates_by_season[season];
          const c = ampacityColor(amp);
          return (
            <div
              key={season}
              className="prr-est-card"
              style={{ borderTop: `3px solid ${SEASON_COLOR[season]}` }}
            >
              <p className="prr-est-nombre">{SEASON_LABEL[season] ?? season}</p>
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
                {seasons.map((s) => (
                  <th key={s} style={{ color: SEASON_COLOR[s] }}>
                    {SEASON_LABEL[s]?.slice(0, 3)}.
                  </th>
                ))}
                <th>Diseño</th>
                <th>Conv.</th>
              </tr>
            </thead>
            <tbody>
              {segments.map((seg) => {
                const isCritical =
                  seg.segment_id === criticalSegment.segment_id;
                const c = ampacityColor(seg.design_rate);
                const firstSeason = seasons[0];
                const modo =
                  seg.ratings?.[firstSeason]?.conv_mode ??
                  seg.details?.[firstSeason]?.conv_mode ??
                  "—";
                return (
                  <tr
                    key={seg.segment_id}
                    className={isCritical ? "prr-fila-critica" : ""}
                  >
                    <td className="prr-td-id">{seg.segment_id}</td>
                    <td>{seg.length_km} km</td>
                    <td className="prr-td-alt">
                      {(seg.elevation_m ?? 0) > 0
                        ? `${Math.round(seg.elevation_m)} m`
                        : "—"}
                    </td>
                    {seasons.map((s) => (
                      <td key={s}>{seg.rates?.[s] ?? "—"} A</td>
                    ))}
                    <td>
                      <span
                        className="prr-pill"
                        style={{ background: c.bg, color: c.text }}
                      >
                        {seg.design_rate} A
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

      {/* Advertencias */}
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
          Modelo: IEEE Std 738-2012 · Régimen estacionario · Fuente climática:{" "}
          {climate_source} · Altitud:{" "}
          {ELEVATION_SOURCE_LABEL[fuenteAlt] ?? fuenteAlt}
        </p>
      </div>
    </div>
  );
}
