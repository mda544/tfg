/**
 * Estimación rápida de ampacidad IEEE 738 para preview en tiempo real.
 * El cálculo completo y oficial lo hace el backend.
 */
export function calcularAmpacidadPreview(escenario, conductorRef) {
  const {
    diameter_mm = 28.1,
    r_ac_75_ohm_km = 0.072,
    max_temp_c = 90,
  } = conductorRef ?? {};
  const { temp, viento, angulo, radiacion } = escenario;
  if (temp >= max_temp_c) return 0;

  const D = diameter_mm / 1000;
  const Tc = max_temp_c;
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
  const R = r_ac_75_ohm_km / 1000;

  const disipado = qc + qr - qs;
  return disipado > 0 ? Math.round(Math.sqrt(disipado / R)) : 0;
}
