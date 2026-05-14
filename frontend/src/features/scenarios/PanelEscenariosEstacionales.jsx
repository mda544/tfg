import { useState, useCallback } from "react";
import {
  ESTACIONES,
  ESCENARIOS_DEFAULT,
  ESTACION_META,
} from "./scenarioDefaults";
import { calcularAmpacidadPreview } from "./thermalPreview";
import "./PanelEscenariosEstacionales.css";

const CampoSlider = ({
  label,
  unidad,
  nombre,
  valor,
  min,
  max,
  paso,
  onChange,
}) => (
  <div className="pes-campo">
    <div className="pes-campo-header">
      <label className="pes-campo-label">{label}</label>
      <span className="pes-campo-valor">
        {typeof valor === "number" && !Number.isInteger(valor)
          ? valor.toFixed(1)
          : valor}{" "}
        {unidad}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={paso}
      value={valor}
      onChange={(e) => onChange(nombre, parseFloat(e.target.value))}
    />
  </div>
);

export default function PanelEscenariosEstacionales({
  conductorRef,
  escenarios,
  onChange,
}) {
  const [activa, setActiva] = useState("verano");

  const actualizarCampo = useCallback(
    (campo, valor) =>
      onChange?.({
        ...escenarios,
        [activa]: { ...escenarios[activa], [campo]: valor },
      }),
    [activa, escenarios, onChange],
  );

  const resetearEstacion = () =>
    onChange?.({ ...escenarios, [activa]: { ...ESCENARIOS_DEFAULT[activa] } });
  const resetearTodo = () =>
    onChange?.(
      Object.fromEntries(
        ESTACIONES.map((e) => [e, { ...ESCENARIOS_DEFAULT[e] }]),
      ),
    );

  const escenarioActivo = escenarios[activa];
  const ampacidad = calcularAmpacidadPreview(escenarioActivo, conductorRef);
  const condViento =
    escenarioActivo.viento < 1
      ? "Calma — caso crítico"
      : escenarioActivo.viento < 3
        ? "Moderado"
        : "Fuerte";

  return (
    <div className="pes-panel">
      <div className="pes-tabs" role="tablist">
        {ESTACIONES.map((est) => (
          <button
            key={est}
            role="tab"
            aria-selected={activa === est}
            className={`pes-tab pes-tab--${ESTACION_META[est].color} ${activa === est ? "pes-tab--activa" : ""}`}
            onClick={() => setActiva(est)}
          >
            {ESTACION_META[est].label}
          </button>
        ))}
      </div>

      <span className={`pes-badge pes-badge--${ESTACION_META[activa].color}`}>
        {ESTACION_META[activa].descripcion}
      </span>

      <CampoSlider
        label="Temperatura ambiente"
        unidad="°C"
        nombre="temp"
        valor={escenarioActivo.temp}
        min={-10}
        max={50}
        paso={1}
        onChange={actualizarCampo}
      />
      <CampoSlider
        label="Velocidad de viento"
        unidad="m/s"
        nombre="viento"
        valor={escenarioActivo.viento}
        min={0}
        max={15}
        paso={0.1}
        onChange={actualizarCampo}
      />
      <CampoSlider
        label="Radiación solar"
        unidad="W/m²"
        nombre="radiacion"
        valor={escenarioActivo.radiacion}
        min={0}
        max={1200}
        paso={10}
        onChange={actualizarCampo}
      />
      <CampoSlider
        label="Ángulo viento / conductor"
        unidad="°"
        nombre="angulo"
        valor={escenarioActivo.angulo}
        min={0}
        max={90}
        paso={1}
        onChange={actualizarCampo}
      />

      <div className="pes-metricas">
        <div className="pes-metrica">
          <span className="pes-metrica-label">Ampacidad estimada</span>
          <span className="pes-metrica-valor">{ampacidad}</span>
          <span className="pes-metrica-unidad">A (IEEE 738, preview)</span>
        </div>
        <div className="pes-metrica">
          <span className="pes-metrica-label">Condición viento</span>
          <span
            className="pes-metrica-valor"
            style={{ fontSize: "14px", marginTop: "4px" }}
          >
            {condViento}
          </span>
        </div>
      </div>

      <div className="pes-acciones">
        <button className="pes-btn" onClick={resetearEstacion}>
          Restaurar defaults
        </button>
        <button className="pes-btn pes-btn--secundario" onClick={resetearTodo}>
          Restaurar todos
        </button>
      </div>

      <p className="pes-nota">
        Defaults: P90 temperatura / P10 viento — Península Ibérica. Los valores
        definitivos se calculan en el backend con IEEE 738 completo.
      </p>
    </div>
  );
}
