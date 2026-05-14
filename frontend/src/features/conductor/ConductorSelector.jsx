import { useState } from "react";
import { useConductors } from "../../hooks/useConductors";
import styles from "./ConductorSelector.module.css";

export default function ConductorSelector({ selected, onChange }) {
  const { conductors, loading, fromApi, create } = useConductors();
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
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const selectedConductor =
    conductors.find((c) => c.id === selected) ?? conductors[0];

  const handleSelect = (e) => {
    const c = conductors.find((c) => c.id === e.target.value);
    if (c) onChange(c);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const nuevo = await create({
        name: formData.name,
        diameter_mm: parseFloat(formData.diameter_mm),
        r_ac_75_ohm_km: parseFloat(formData.r_ac_75_ohm_km),
        r_ac_25_ohm_km: parseFloat(formData.r_ac_25_ohm_km),
        emissivity: parseFloat(formData.emissivity),
        absorptivity: parseFloat(formData.absorptivity),
        max_temp_c: parseFloat(formData.max_temp_c),
      });
      onChange(nuevo);
      setShowForm(false);
    } catch (err) {
      setFormError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className={styles.loading}>Cargando conductores…</p>;

  return (
    <div className={styles.wrap}>
      <div className={styles.row}>
        <select
          className={styles.select}
          value={selectedConductor?.id ?? ""}
          onChange={handleSelect}
        >
          {conductors.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {fromApi && (
          <button
            className={styles.addBtn}
            onClick={() => setShowForm((v) => !v)}
            title="Añadir conductor"
          >
            {showForm ? "✕" : "+"}
          </button>
        )}
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

      {!fromApi && (
        <p className={styles.hint}>
          Catálogo local — inicia sesión para gestionar conductores en la base
          de datos.
        </p>
      )}

      {showForm && (
        <form className={styles.form} onSubmit={handleCreate}>
          <p className={styles.formTitle}>Nuevo conductor</p>
          {[
            ["name", "Nombre", "text"],
            ["diameter_mm", "Diámetro (mm)", "number"],
            ["r_ac_75_ohm_km", "R AC 75°C (Ω/km)", "number"],
            ["r_ac_25_ohm_km", "R AC 25°C (Ω/km)", "number"],
            ["emissivity", "Emisividad", "number"],
            ["absorptivity", "Absortividad", "number"],
            ["max_temp_c", "Temp. máx (°C)", "number"],
          ].map(([key, label, type]) => (
            <label key={key} className={styles.formField}>
              <span>{label}</span>
              <input
                type={type}
                required
                value={formData[key]}
                step={type === "number" ? "any" : undefined}
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
