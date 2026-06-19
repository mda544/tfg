import {
  SEASON_LABEL,
  SEASON_COLOR,
  ELEVATION_SOURCE_LABEL,
  ampacityColor,
} from "./resultsUtils";
import "./RatesResultsPanel.css";

const SEASONS = ["verano", "otono", "invierno", "primavera"];

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
    season_results = [],
    n_segments,
    warnings = [],
  } = result;

  // Índice season para acceso rápido
  const bySeasonMap = Object.fromEntries(
    season_results.map((sr) => [sr.season, sr]),
  );

  const elevationSource = season_results[0]?.elevation_source ?? "none";

  const criticalSR = season_results.reduce(
    (min, sr) => (sr.design_rate < (min?.design_rate ?? Infinity) ? sr : min),
    null,
  );
  const criticalSegment = criticalSR?.segments?.reduce(
    (min, s) => (s.ampacity < (min?.ampacity ?? Infinity) ? s : min),
    null,
  );

  // Todos los SeasonResult tienen los mismos segmentos (mismo índice)
  const refSegments = season_results[0]?.segments ?? [];

  return (
    <div className="prr-panel">
      {/* Cabecera */}
      <div className="prr-cabecera">
        <div>
          <p className="prr-label">Rate de diseño de la línea</p>
          <p className="prr-rate-principal">
            {design_rate?.toFixed(0)} <span>A</span>
          </p>
          <p className="prr-sublabel">
            Tramo crítico: {criticalSegment?.segment_id ?? "—"}
            {criticalSegment?.elevation_m > 0
              ? ` · ${Math.round(criticalSegment.elevation_m)} m s.n.m.`
              : ""}
            {" · "}
            {n_segments} tramos
          </p>
        </div>
        <div className="prr-badge-metodo">IEEE 738-2012</div>
      </div>

      {/* Fuente de elevación */}
      <div className="prr-criterio">
        <span>
          Criterio: P90 temperatura / P10 viento. Rate = mínimo de todos los
          tramos.
        </span>
        <span
          className={`prr-dem-badge prr-dem-${
            elevationSource === "none" ? "off" : "ok"
          }`}
        >
          Altitud: {ELEVATION_SOURCE_LABEL[elevationSource] ?? elevationSource}
        </span>
      </div>

      {/* Rates por estación */}
      <div className="prr-estaciones">
        {SEASONS.filter((s) => bySeasonMap[s]).map((season) => {
          const sr = bySeasonMap[season];
          const amp = sr.design_rate;
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
                {amp?.toFixed(0)} A
              </p>
              <p className="prr-est-sub">mínimo de tramos</p>
            </div>
          );
        })}
      </div>

      {/* Tabla de tramos — una fila por segmento, una col por estación */}
      {refSegments.length > 0 && (
        <div className="prr-tabla-wrap">
          <table className="prr-tabla">
            <thead>
              <tr>
                <th>Tramo</th>
                <th>Long.</th>
                <th>Alt.</th>
                {SEASONS.filter((s) => bySeasonMap[s]).map((s) => (
                  <th key={s} style={{ color: SEASON_COLOR[s] }}>
                    {SEASON_LABEL[s]?.slice(0, 3)}.
                  </th>
                ))}
                <th>Diseño</th>
                <th>Conv.</th>
              </tr>
            </thead>
            <tbody>
              {refSegments.map((refSeg, idx) => {
                // Ampacidad de este tramo por estación
                const ampsBySeasonMap = Object.fromEntries(
                  season_results.map((sr) => [
                    sr.season,
                    sr.segments[idx]?.ampacity,
                  ]),
                );
                const segDesignRate = Math.min(
                  ...Object.values(ampsBySeasonMap).filter(Boolean),
                );
                const esCritico =
                  refSeg.segment_id === criticalSegment?.segment_id;
                const c = ampacityColor(segDesignRate);
                const modo = criticalSR?.segments[idx]?.conv_mode ?? "—";

                return (
                  <tr
                    key={refSeg.segment_id}
                    className={esCritico ? "prr-fila-critica" : ""}
                  >
                    <td className="prr-td-id">{refSeg.segment_id}</td>
                    <td>{refSeg.length_km?.toFixed(2)} km</td>
                    <td className="prr-td-alt">
                      {refSeg.elevation_m > 0
                        ? `${Math.round(refSeg.elevation_m)} m`
                        : "—"}
                    </td>
                    {SEASONS.filter((s) => bySeasonMap[s]).map((s) => (
                      <td key={s}>{ampsBySeasonMap[s]?.toFixed(0) ?? "—"} A</td>
                    ))}
                    <td>
                      <span
                        className="prr-pill"
                        style={{ background: c.bg, color: c.text }}
                      >
                        {segDesignRate?.toFixed(0)} A
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
    </div>
  );
}
