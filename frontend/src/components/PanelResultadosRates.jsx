import "./PanelResultadosRates.css";

const LABEL = {
  verano: "Verano", invierno: "Invierno",
  primavera: "Primavera", otono: "Otoño",
};
const COLOR_EST = {
  verano: "#D85A30", invierno: "#185FA5",
  primavera: "#3B6D11", otono: "#BA7517",
};
const LABEL_FUENTE_ALT = {
  excel_z:           "Z del Excel",
  open_meteo_dem:    "DEM Open-Meteo",
  sin_altitud:       "Sin altitud (0 m)",
  sin_altitud_error: "Sin altitud (error DEM)",
};

function colorAmpacidad(a) {
  if (a < 500)  return { bg: "#FCEBEB", text: "#791F1F" };
  if (a < 800)  return { bg: "#FAEEDA", text: "#633806" };
  if (a < 1100) return { bg: "#EAF3DE", text: "#27500A" };
  return               { bg: "#E1F5EE", text: "#085041" };
}

const PanelResultadosRates = ({ resultado }) => {
  if (!resultado) return null;

  if (resultado.error) {
    return (
      <div className="prr-panel prr-error">
        <p className="prr-error-titulo">Error en el cálculo</p>
        <p className="prr-error-msg">{resultado.error}</p>
      </div>
    );
  }

  const {
    rate_linea_diseno_a,
    rates_por_estacion = {},
    tramos = [],
    n_tramos,
    conductor,
    info_trazado = {},
    advertencias_validacion = [],
  } = resultado;

  const estaciones   = Object.keys(rates_por_estacion);
  const tramoCritico = tramos.reduce(
    (min, t) => t.rate_diseno_a < min.rate_diseno_a ? t : min,
    tramos[0] ?? { rate_diseno_a: Infinity, id_tramo: "—" }
  );

  // Verificar si hay variación real de ampacidad entre tramos (indica DEM funcionando)
  const ampacidades = tramos.map((t) => t.rate_diseno_a);
  const hayVariacion = ampacidades.length > 1 &&
    Math.max(...ampacidades) - Math.min(...ampacidades) > 0.5;

  const fuenteAlt = info_trazado.fuente_altitud ?? "sin_altitud";
  const modoSeg   = info_trazado.modo_segmentacion ?? "";

  return (
    <div className="prr-panel">

      {/* Cabecera */}
      <div className="prr-cabecera">
        <div>
          <p className="prr-label">Rate de diseño de la línea</p>
          <p className="prr-rate-principal">
            {rate_linea_diseno_a} <span>A</span>
          </p>
          <p className="prr-sublabel">
            Tramo crítico: {tramoCritico.id_tramo}
            {tramoCritico.altitud_m > 0 ? ` · ${tramoCritico.altitud_m} m s.n.m.` : ""}
            {" · "}{info_trazado.longitud_km ?? "?"} km
            {" · "}{n_tramos} {modoSeg.includes("vanos") ? "vanos" : "tramos"}
          </p>
        </div>
        <div className="prr-badge-metodo">IEEE 738-2012</div>
      </div>

      {/* Criterio + info DEM */}
      <div className="prr-criterio">
        <span>
          Criterio: P90 temperatura / P10 viento. Rate = mínimo de todos los tramos.
        </span>
        <span className={`prr-dem-badge prr-dem-${fuenteAlt.includes("error") ? "error" : fuenteAlt === "sin_altitud" ? "off" : "ok"}`}>
          Altitud: {LABEL_FUENTE_ALT[fuenteAlt] ?? fuenteAlt}
          {info_trazado.altitud_min_m !== undefined &&
            fuenteAlt !== "sin_altitud" &&
            ` · ${info_trazado.altitud_min_m}–${info_trazado.altitud_max_m} m`}
        </span>
      </div>

      {/* Aviso si no hay variación (DEM no funcionó o altitud plana) */}
      {!hayVariacion && tramos.length > 1 && fuenteAlt !== "sin_altitud" && (
        <div className="prr-aviso-plano">
          Todos los tramos tienen el mismo rate. Comprueba que el DEM devolvió altitudes variadas
          (altitud media: {info_trazado.altitud_media_m ?? 0} m).
        </div>
      )}

      {/* Rates por estación */}
      <div className="prr-estaciones">
        {estaciones.map((est) => {
          const amp = rates_por_estacion[est];
          const c   = colorAmpacidad(amp);
          return (
            <div key={est} className="prr-est-card" style={{ borderTop: `3px solid ${COLOR_EST[est]}` }}>
              <p className="prr-est-nombre">{LABEL[est] ?? est}</p>
              <p className="prr-est-amp" style={{ color: c.text, background: c.bg }}>{amp} A</p>
              <p className="prr-est-sub">mínimo de tramos</p>
            </div>
          );
        })}
      </div>

      {/* Tabla de tramos */}
      {tramos.length > 0 && (
        <div className="prr-tabla-wrap">
          <table className="prr-tabla">
            <thead>
              <tr>
                <th>Tramo</th>
                <th>Long.</th>
                <th>Alt.</th>
                {estaciones.map((e) => (
                  <th key={e} style={{ color: COLOR_EST[e] }}>{LABEL[e]?.slice(0, 3)}.</th>
                ))}
                <th>Diseño</th>
                <th>Conv.</th>
              </tr>
            </thead>
            <tbody>
              {tramos.map((tramo) => {
                const esCritico = tramo.id_tramo === tramoCritico.id_tramo;
                const c         = colorAmpacidad(tramo.rate_diseno_a);
                const modo      =
                  tramo.detalles?.verano?.modo_conveccion ??
                  tramo.detalles?.[estaciones[0]]?.modo_conveccion ?? "—";
                const altitud   = tramo.altitud_m ?? 0;

                return (
                  <tr key={tramo.id_tramo} className={esCritico ? "prr-fila-critica" : ""}>
                    <td className="prr-td-id">{tramo.id_tramo}</td>
                    <td>{tramo.longitud_km} km</td>
                    <td className="prr-td-alt">
                      {altitud > 0 ? `${Math.round(altitud)} m` : "—"}
                    </td>
                    {estaciones.map((e) => (
                      <td key={e}>{tramo.rates?.[e] ?? "—"} A</td>
                    ))}
                    <td>
                      <span className="prr-pill" style={{ background: c.bg, color: c.text }}>
                        {tramo.rate_diseno_a} A
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

      {/* Advertencias de validación */}
      {advertencias_validacion.length > 0 && (
        <div className="prr-advertencias">
          <p className="prr-adv-titulo">{advertencias_validacion.length} advertencia(s)</p>
          <ul>{advertencias_validacion.map((a, i) => <li key={i}>{a}</li>)}</ul>
        </div>
      )}

      {/* Trazabilidad */}
      <div className="prr-trazabilidad">
        <p>
          Conductor: Ø{conductor?.diametro_mm} mm ·
          R75={conductor?.r_ac_75_ohm_km} Ω/km ·
          R25={conductor?.r_ac_25_ohm_km} Ω/km ·
          Tmax={conductor?.temp_max_c}°C ·
          ε={conductor?.emisividad} · α={conductor?.absortividad}
        </p>
        <p>
          Modelo: IEEE Std 738-2012 · Régimen estacionario ·
          Segmentación: {modoSeg} · Altitud: {LABEL_FUENTE_ALT[fuenteAlt] ?? fuenteAlt}
        </p>
      </div>
    </div>
  );
};

export default PanelResultadosRates;