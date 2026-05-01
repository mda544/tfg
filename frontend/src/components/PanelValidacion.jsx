import "./PanelValidacion.css";

const PanelValidacion = ({ validacion }) => {
  if (!validacion) return null;

  const { valido, errores = [], advertencias = [], info = {} } = validacion;

  if (valido && advertencias.length === 0) {
    return (
      <div className="pv-panel pv-ok">
        <span className="pv-icono">✓</span>
        <div>
          <p className="pv-titulo">Trazado válido</p>
          <p className="pv-subtitulo">
            {info.n_puntos} apoyos · {info.longitud_km} km
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`pv-panel ${!valido ? "pv-error" : "pv-advertencia"}`}>
      <span className="pv-icono">{!valido ? "✕" : "!"}</span>
      <div className="pv-contenido">
        {errores.length > 0 && (
          <>
            <p className="pv-titulo">
              {errores.length} error{errores.length > 1 ? "es" : ""} — cálculo bloqueado
            </p>
            <ul className="pv-lista">
              {errores.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </>
        )}
        {advertencias.length > 0 && (
          <>
            <p className="pv-titulo pv-titulo-adv">
              {advertencias.length} advertencia{advertencias.length > 1 ? "s" : ""}
            </p>
            <ul className="pv-lista pv-lista-adv">
              {advertencias.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </>
        )}
        {info.longitud_km && (
          <p className="pv-subtitulo">
            {info.n_puntos} apoyos · {info.longitud_km} km
          </p>
        )}
      </div>
    </div>
  );
};

export default PanelValidacion;