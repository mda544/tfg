import styles from "./StudyCaseSelector.module.css";
import { formatDateTime } from "../../utils/dateUtils";

/**
 * Selector de casos de estudio para una línea cargada.
 *
 * Props:
 *  - studyCases      — lista de StudyCaseResponseDTO de la línea activa
 *  - loading         — cargando casos desde la API
 *  - selectedId      — id del caso seleccionado actualmente
 *  - onSelect(sc)    — callback cuando el usuario selecciona un caso existente
 *  - onCreate()      — callback cuando el usuario quiere crear un caso nuevo
 *  - disabled        — deshabilita el selector (ej. durante el cálculo)
 */
export default function StudyCaseSelector({
  studyCases,
  loading,
  selectedId,
  onSelect,
  onCreate,
  disabled,
}) {
  if (loading) {
    return <p className={styles.info}>Cargando casos de estudio…</p>;
  }

  const handleChange = (e) => {
    const id = e.target.value;
    if (id === "__new__") {
      onCreate?.();
      return;
    }
    const sc = studyCases.find((s) => s.id === id);
    if (sc) onSelect(sc);
  };

  return (
    <div className={styles.wrap}>
      <select
        className={styles.select}
        value={selectedId ?? ""}
        onChange={handleChange}
        disabled={disabled}
      >
        <option value="" disabled>
          Selecciona un caso de estudio…
        </option>

        {studyCases.length > 0 && (
          <optgroup label="Casos existentes">
            {studyCases.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.name}
                {sc.conductor?.name ? ` · ${sc.conductor.name}` : ""}
                {sc.use_real_spans
                  ? " · vanos reales"
                  : ` · ${sc.segment_step_m}m`}
              </option>
            ))}
          </optgroup>
        )}

        <optgroup label="─────────────">
          <option value="__new__">+ Crear nuevo caso de estudio</option>
        </optgroup>
      </select>

      {selectedId &&
        studyCases.length > 0 &&
        (() => {
          const sc = studyCases.find((s) => s.id === selectedId);
          if (!sc) return null;
          return (
            <div className={styles.ficha}>
              <span>Conductor: {sc.conductor?.name ?? sc.conductor_id}</span>
              <span>
                Segmentación:{" "}
                {sc.use_real_spans ? "vanos reales" : `${sc.segment_step_m} m`}
              </span>
              <span>Creado el: {formatDateTime(sc.created_at)}</span>

              {sc.conductor && (
                <span>
                  Ø {sc.conductor.diameter_mm} mm · R75:{" "}
                  {sc.conductor.r_ac_75_ohm_km} Ω/km
                </span>
              )}
            </div>
          );
        })()}
    </div>
  );
}
