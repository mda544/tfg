import { useState } from "react";
import { useConductors } from "../../hooks/useConductors";
import styles from "./ConductorSelector.module.css";

const GLOBAL_IDS = new Set([
  "00000000-0000-0000-0000-000000000001",
  "00000000-0000-0000-0000-000000000002",
  "00000000-0000-0000-0000-000000000003",
  "00000000-0000-0000-0000-000000000004",
]);

export default function ConductorSelector({ selected, onChange }) {
  const { conductors, saving, error: apiError, create } = useConductors();

  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    diameter_mm: "",
    r_ac_75_ohm_km: "",
    r_ac_25_ohm_km: "",
    emissivity: 0.5,
    absorptivity: 0.5,
    max_temp_c: 90,
  });
  const [formError, setFormError] = useState("");

  const global = conductors.filter((c) => GLOBAL_IDS.has(c.id));
  const custom = conductors.filter((c) => !GLOBAL_IDS.has(c.id));

  const selectedConductor =
    conductors.find((c) => c.id === selected) ?? conductors[0];

  const handleSelect = (e) => {
    const c = conductors.find((c) => c.id === e.target.value);
    if (c) onChange(c);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setFormError("");
    const nuevo = await create({
      name: formData.name,
      diameter_mm: parseFloat(formData.diameter_mm),
      r_ac_75_ohm_km: parseFloat(formData.r_ac_75_ohm_km),
      r_ac_25_ohm_km: parseFloat(formData.r_ac_25_ohm_km),
      emissivity: parseFloat(formData.emissivity),
      absorptivity: parseFloat(formData.absorptivity),
      max_temp_c: parseFloat(formData.max_temp_c),
    });
    if (nuevo) {
      onChange(nuevo);
      setShowForm(false);
    } else {
      setFormError(apiError ?? "Error al guardar.");
    }
  };

  // Definición estructurada de los campos del formulario con sus límites físicos
  const formFields = [
    { key: "name", label: "Nombre", type: "text" },
    {
      key: "diameter_mm",
      label: "Diámetro (mm)",
      type: "number",
      min: 1,
      max: 100,
      step: "any",
    },
    {
      key: "r_ac_75_ohm_km",
      label: "R AC 75°C (Ω/km)",
      type: "number",
      min: 0.001,
      max: 10,
      step: "any",
    },
    {
      key: "r_ac_25_ohm_km",
      label: "R AC 25°C (Ω/km)",
      type: "number",
      min: 0.001,
      max: 10,
      step: "any",
    },
    {
      key: "emissivity",
      label: "Emisividad",
      type: "number",
      min: 0.0,
      max: 1.0,
      step: 0.01,
    },
    {
      key: "absorptivity",
      label: "Absortividad",
      type: "number",
      min: 0.0,
      max: 1.0,
      step: 0.01,
    },
    {
      key: "max_temp_c",
      label: "Temp. máx (°C)",
      type: "number",
      min: 10,
      max: 300,
      step: "any",
    },
  ];

  return (
    <div className={styles.wrap}>
      <div className={styles.row}>
        <select
          className={styles.select}
          value={selectedConductor?.id ?? ""}
          onChange={handleSelect}
        >
          <optgroup label="Catálogo estándar">
            {global.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </optgroup>
          {custom.length > 0 && (
            <optgroup label="Mis conductores">
              {custom.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </optgroup>
          )}
        </select>

        <button
          className={styles.addBtn}
          onClick={() => setShowForm((v) => !v)}
          title="Añadir conductor"
        >
          {showForm ? "✕" : "+"}
        </button>
      </div>

      {selectedConductor && (
        <div className={styles.ficha}>
          <span>Ø {selectedConductor.diameter_mm} mm</span>
          <span>R75: {selectedConductor.r_ac_75_ohm_km} Ω/km</span>
          <span>R25: {selectedConductor.r_ac_25_ohm_km} Ω/km</span>
          <span>ε: {selectedConductor.emissivity}</span>
          <span>Tmax: {selectedConductor.max_temp_c} °C</span>
        </div>
      )}

      {showForm && (
        <form className={styles.form} onSubmit={handleCreate}>
          <p className={styles.formTitle}>Nuevo conductor</p>

          {formFields.map(({ key, label, type, min, max, step }) => (
            <label key={key} className={styles.formField}>
              <span>{label}</span>
              <input
                type={type}
                required
                value={formData[key]}
                min={min}
                max={max}
                step={step}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, [key]: e.target.value }))
                }
              />
            </label>
          ))}

          {formError && <p className={styles.formError}>{formError}</p>}
          <button className={styles.saveBtn} type="submit" disabled={saving}>
            {saving ? "Guardando…" : "Guardar conductor"}
          </button>
        </form>
      )}
    </div>
  );
}
