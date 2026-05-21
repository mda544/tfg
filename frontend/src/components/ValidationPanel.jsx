import styles from "./ValidationPanel.module.css";

export default function ValidationPanel({ validation }) {
  if (!validation) return null;

  const { valid, errors = [], warnings = [], info = {} } = validation;

  if (valid && warnings.length === 0) {
    return (
      <div className={`${styles.panel} ${styles.ok}`}>
        <span className={styles.icon}>✓</span>
        <div>
          <p className={styles.title}>Trazado válido</p>
          <p className={styles.subtitle}>
            {info.n_puntos} apoyos · {info.longitud_km} km
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${styles.panel} ${!valid ? styles.error : styles.warning}`}
    >
      <span className={styles.icon}>{!valid ? "✕" : "!"}</span>
      <div className={styles.content}>
        {errors.length > 0 && (
          <>
            <p className={styles.title}>
              {errors.length} error{errors.length > 1 ? "es" : ""} — cálculo
              bloqueado
            </p>
            <ul className={styles.list}>
              {errors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </>
        )}
        {warnings.length > 0 && (
          <>
            <p className={`${styles.title} ${styles.titleWarning}`}>
              {warnings.length} advertencia{warnings.length > 1 ? "s" : ""}
            </p>
            <ul className={`${styles.list} ${styles.listWarning}`}>
              {warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </>
        )}
        {info.longitud_km && (
          <p className={styles.subtitle}>
            {info.n_puntos} apoyos · {info.longitud_km} km
          </p>
        )}
      </div>
    </div>
  );
}
