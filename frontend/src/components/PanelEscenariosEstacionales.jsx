import { useState, useCallback } from "react";
import "./PanelEscenariosEstacionales.css";

const ESTACIONES = ["verano", "invierno", "primavera", "otono"];

const DEFAULTS = {
  verano: { temp: 38, viento: 0.6, angulo: 90, radiacion: 900 },
  invierno: { temp: 5, viento: 3.0, angulo: 90, radiacion: 200 },
  primavera: { temp: 18, viento: 2.5, angulo: 90, radiacion: 650 },
  otono: { temp: 20, viento: 2.0, angulo: 90, radiacion: 500 },
};

const META = {
  verano: {
    label: "Verano",
    descripcion: "Condición más restrictiva",
    color: "coral",
  },
  invierno: {
    label: "Invierno",
    descripcion: "Mayor capacidad de transporte",
    color: "blue",
  },
  primavera: {
    label: "Primavera",
    descripcion: "Condición intermedia",
    color: "green",
  },
  otono: {
    label: "Otoño",
    descripcion: "Condición intermedia",
    color: "amber",
  },
};

// ── IEEE 738 simplificado para preview en tiempo real ──────────────────────
function calcularAmpacidadPreview(escenario, conductorRef) {
  const {
    diametro_mm = 28.1,
    r_ac_75 = 0.072,
    temp_max = 90,
  } = conductorRef ?? {};
  const { temp, viento, angulo, radiacion } = escenario;
  if (temp >= temp_max) return 0;

  const D = diametro_mm / 1000;
  const Tc = temp_max;
  const Ta = temp;
  const tf = (Tc + Ta) / 2;

  const rho = 1.293 * (273.15 / (273.15 + tf));
  const mu = (1.458e-6 * (tf + 273.15) ** 1.5) / (tf + 273.15 + 110.4);
  const kf = 2.42e-2 + 7.2e-5 * tf;

  const phi = (angulo * Math.PI) / 180;
  const kAng =
    1.194 -
    Math.cos(phi) +
    0.194 * Math.cos(2 * phi) +
    0.368 * Math.sin(2 * phi);

  const v = Math.max(viento, 0.01);
  const Re = (rho * v * D) / mu;
  const qc = Math.max(
    kAng * (1.01 + 1.35 * Re ** 0.52) * kf * (Tc - Ta),
    kAng * 0.754 * Re ** 0.6 * kf * (Tc - Ta),
    3.645 * rho ** 0.5 * D ** 0.75 * (Tc - Ta) ** 1.25,
  );

  const sigma = 5.6704e-8;
  const qr =
    0.5 * Math.PI * D * sigma * ((Tc + 273.15) ** 4 - (Ta + 273.15) ** 4);
  const qs = 0.5 * radiacion * Math.sin(phi) * D;
  const R = r_ac_75 / 1000;

  const disipado = qc + qr - qs;
  return disipado > 0 ? Math.round(Math.sqrt(disipado / R)) : 0;
}

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

// ── Componente principal ────────────────────────────────────────────────────
const PanelEscenariosEstacionales = ({
  conductorRef,
  escenarios,
  onChange,
}) => {
  const [activa, setActiva] = useState("verano");

  const actualizarCampo = useCallback(
    (campo, valor) => {
      const nuevo = {
        ...escenarios,
        [activa]: { ...escenarios[activa], [campo]: valor },
      };
      onChange?.(nuevo);
    },
    [activa, escenarios, onChange],
  );

  const resetearEstacion = () => {
    const nuevo = { ...escenarios, [activa]: { ...DEFAULTS[activa] } };
    onChange?.(nuevo);
  };

  const resetearTodo = () => {
    const reset = Object.fromEntries(
      ESTACIONES.map((e) => [e, { ...DEFAULTS[e] }]),
    );
    onChange?.(reset);
  };

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
            className={`pes-tab pes-tab--${META[est].color} ${activa === est ? "pes-tab--activa" : ""}`}
            onClick={() => setActiva(est)}
          >
            {META[est].label}
          </button>
        ))}
      </div>

      <span className={`pes-badge pes-badge--${META[activa].color}`}>
        {META[activa].descripcion}
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
        <button
          className="pes-btn pes-btn--secundario"
          onClick={resetearTodo} // <-- CORREGIDO: Llamada directa a la función local sin parámetros
        >
          Restaurar todos
        </button>
      </div>

      <p className="pes-nota">
        Defaults: P90 temperatura / P10 viento — Península Ibérica. Los valores
        definitivos se calculan en el backend con IEEE 738 completo.
      </p>
    </div>
  );
};

export default PanelEscenariosEstacionales;

export { DEFAULTS as ESCENARIOS_DEFAULT };
