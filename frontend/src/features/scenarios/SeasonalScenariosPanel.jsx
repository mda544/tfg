import { useState, useCallback } from "react";
import { SEASONS, DEFAULT_SCENARIOS, ESTACION_META } from "./scenarioDefaults";
import { calcularAmpacidadPreview } from "./thermalPreview";
import styles from "./SeasonalScenariosPanel.module.css";

function degToCardinal(deg) {
  const dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"];
  return dirs[Math.round(deg / 45) % 8];
}

const SliderField = ({
  label,
  unit,
  fieldName,
  value,
  min,
  max,
  step,
  onChange,
}) => (
  <div className={styles.field}>
    <div className={styles.fieldHeader}>
      <label className={styles.fieldLabel}>{label}</label>
      <span className={styles.fieldValue}>
        {typeof value === "number" && !Number.isInteger(value)
          ? value.toFixed(1)
          : value}{" "}
        {unit}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(fieldName, parseFloat(e.target.value))}
    />
  </div>
);

export default function SeasonalScenariosPanel({
  conductorRef,
  escenarios,
  apiDefaults,
  onChange,
}) {
  const [activeTab, setActiveTab] = useState("verano");

  const updateField = useCallback(
    (fieldName, value) =>
      onChange?.({
        ...escenarios,
        [activeTab]: { ...escenarios[activeTab], [fieldName]: value },
      }),
    [activeTab, escenarios, onChange],
  );

  // Restaurar estación activa a fuente actual (ERA5 o NASA)
  const resetSeason = () => {
    const base = apiDefaults?.[activeTab] ?? DEFAULT_SCENARIOS[activeTab];
    onChange?.({
      ...escenarios,
      [activeTab]: { ...base },
    });
  };

  // Restaurar todas las estaciones a fuente actual
  const resetAll = () => {
    if (apiDefaults) {
      onChange?.({ ...apiDefaults });
    } else {
      onChange?.(
        Object.fromEntries(
          SEASONS.map((s) => [s, { ...DEFAULT_SCENARIOS[s] }]),
        ),
      );
    }
  };

  const activeScenario = escenarios[activeTab];
  const ampacity = calcularAmpacidadPreview(activeScenario, conductorRef);
  const windCondition =
    activeScenario.viento < 1
      ? "Calma — caso crítico"
      : activeScenario.viento < 3
        ? "Moderado"
        : "Fuerte";

  const hasWindDir = activeScenario.wind_dir_predominant_deg != null;

  return (
    <div className={styles.panel}>
      <div className={styles.tabs} role="tablist">
        {SEASONS.map((season) => (
          <button
            key={season}
            role="tab"
            aria-selected={activeTab === season}
            className={`${styles.tab} ${styles[`tab_${ESTACION_META[season].color}`]} ${activeTab === season ? styles.tabActive : ""}`}
            onClick={() => setActiveTab(season)}
          >
            {ESTACION_META[season].label}
          </button>
        ))}
      </div>

      <span
        className={`${styles.badge} ${styles[`badge_${ESTACION_META[activeTab].color}`]}`}
      >
        {ESTACION_META[activeTab].descripcion}
      </span>

      <SliderField
        label="Temperatura ambiente"
        unit="°C"
        fieldName="temp"
        value={activeScenario.temp}
        min={-10}
        max={50}
        step={1}
        onChange={updateField}
      />
      <SliderField
        label="Velocidad de viento"
        unit="m/s"
        fieldName="viento"
        value={activeScenario.viento}
        min={0}
        max={15}
        step={0.1}
        onChange={updateField}
      />
      <SliderField
        label="Radiación solar"
        unit="W/m²"
        fieldName="radiacion"
        value={activeScenario.radiacion}
        min={0}
        max={1200}
        step={10}
        onChange={updateField}
      />

      {hasWindDir ? (
        <div className={styles.field}>
          <div className={styles.fieldHeader}>
            <label className={styles.fieldLabel}>
              Ángulo viento / conductor
            </label>
          </div>
          <p className={styles.windDirInfo}>
            Calculado por segmento a partir de la dirección ERA5:{" "}
            <strong>
              {activeScenario.wind_dir_predominant_deg}° (
              {degToCardinal(activeScenario.wind_dir_predominant_deg)})
            </strong>
          </p>
        </div>
      ) : (
        <SliderField
          label="Ángulo viento / conductor"
          unit="°"
          fieldName="angulo"
          value={activeScenario.angulo}
          min={0}
          max={90}
          step={1}
          onChange={updateField}
        />
      )}

      <div className={styles.metrics}>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Ampacidad estimada</span>
          <span className={styles.metricValue}>{ampacity}</span>
          <span className={styles.metricUnit}>A (IEEE 738, preview)</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.metricLabel}>Condición viento</span>
          <span
            className={styles.metricValue}
            style={{ fontSize: "14px", marginTop: "4px" }}
          >
            {windCondition}
          </span>
        </div>
      </div>

      <div className={styles.actions}>
        <button className={styles.btn} onClick={resetSeason}>
          Restaurar estación
        </button>
        <button
          className={`${styles.btn} ${styles.btnSecondary}`}
          onClick={resetAll}
        >
          Restaurar todos
        </button>
      </div>

      <p className={styles.note}>
        {apiDefaults
          ? "Restaurar vuelve a los valores originales de la fuente climática seleccionada."
          : "Defaults: P90 temperatura / P10 viento — Península Ibérica."}{" "}
        Los valores definitivos se calculan en el backend con IEEE 738 completo.
      </p>
    </div>
  );
}
