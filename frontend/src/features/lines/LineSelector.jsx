import styles from "./LineSelector.module.css";
import { formatDateTime } from "../../utils/dateUtils";

/**
 * Desplegable de líneas guardadas.
 */
export default function LineSelector({
  lines = [],
  loading,
  error,
  loadLineGeoJSON,
  onLineLoaded,
  disabled,
}) {
  const handleChange = async (e) => {
    const lineId = e.target.value;
    if (!lineId) return;
    try {
      const feature = await loadLineGeoJSON(lineId);
      onLineLoaded(feature);
    } catch (err) {
      console.error("[LineSelector]", err.message);
    }
    e.target.value = "";
  };

  if (loading) {
    return <p className={styles.info}>Cargando líneas guardadas…</p>;
  }

  if (error) {
    return <p className={styles.error}>Error al cargar líneas: {error}</p>;
  }

  if (lines.length === 0) {
    return <p className={styles.info}>No tienes líneas guardadas todavía.</p>;
  }

  return (
    <div className={styles.wrap}>
      <select
        className={styles.select}
        defaultValue=""
        onChange={handleChange}
        disabled={disabled}
      >
        <option value="" disabled>
          Cargar línea guardada…
        </option>
        {lines.map((line) => (
          <option key={line.id} value={line.id}>
            {line.name}
            {line.length_km ? ` · ${line.length_km.toFixed(1)} km` : ""}
            {line.n_points ? ` · ${line.n_points} apoyos` : ""}
            {` · ${formatDateTime(line.created_at)}`}
          </option>
        ))}
      </select>
    </div>
  );
}
