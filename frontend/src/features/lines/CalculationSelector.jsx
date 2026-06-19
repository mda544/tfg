import styles from "./CalculationSelector.module.css";
import { formatDateTime } from "../../utils/dateUtils";

const SOURCE_LABEL = {
  openmeteo: "ERA5",
  nasa: "NASA POWER",
  manual: "Manual",
};

const formatDate = formatDateTime;

/**
 * Selector de cálculos anteriores de un caso de estudio.
 *
 * Props:
 *  - calculations   — lista de CalculationResponseDTO
 *  - loading        — cargando desde la API
 *  - selectedId     — id del cálculo actualmente visible en el panel
 *  - onSelect(calc) — callback al seleccionar un cálculo anterior
 *  - onNew()        — callback para lanzar un cálculo nuevo
 *  - disabled       — deshabilita mientras se está calculando
 */
export default function CalculationSelector({
  calculations,
  loading,
  selectedId,
  onSelect,
  onNew,
  disabled,
}) {
  if (loading) {
    return <p className={styles.info}>Cargando cálculos anteriores…</p>;
  }

  const handleChange = (e) => {
    const id = e.target.value;
    if (id === "__new__") {
      onNew?.();
      return;
    }
    const calc = calculations.find((c) => c.id === id);
    if (calc) onSelect(calc);
  };

  return (
    <div className={styles.wrap}>
      <select
        className={styles.select}
        value={selectedId ?? "__new__"}
        onChange={handleChange}
        disabled={disabled}
      >
        <optgroup label="Nuevo cálculo">
          <option value="__new__">+ Lanzar nuevo cálculo</option>
        </optgroup>

        {calculations.length > 0 && (
          <optgroup label="Cálculos anteriores">
            {calculations.map((c) => (
              <option key={c.id} value={c.id}>
                {formatDate(c.created_at)}
                {" · "}
                {SOURCE_LABEL[c.climate_source] ?? c.climate_source}
                {" · "}
                {c.design_rate?.toFixed(0)} A{" · "}
                {c.n_segments} tramos
              </option>
            ))}
          </optgroup>
        )}
      </select>

      {selectedId &&
        selectedId !== "__new__" &&
        (() => {
          const calc = calculations.find((c) => c.id === selectedId);
          if (!calc) return null;
          return (
            <div className={styles.ficha}>
              <span>
                Rate de diseño:{" "}
                <strong>{calc.design_rate?.toFixed(0)} A</strong>
              </span>
              <span>
                Fuente:{" "}
                {SOURCE_LABEL[calc.climate_source] ?? calc.climate_source}
                {" · "}
                {calc.n_segments} tramos
              </span>
              <span>{formatDate(calc.created_at)}</span>
            </div>
          );
        })()}
    </div>
  );
}
