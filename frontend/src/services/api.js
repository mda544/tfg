import axios from "axios";

// Si el día de mañana cambias de servidor, SOLO tienes que cambiar esta línea
const URL_BACKEND = "http://localhost:8000";

/**
 * Función que se comunica con FastAPI para calcular el rendimiento.
 * Recibe un objeto con los datos y devuelve la respuesta del servidor.
 */
export const enviarCalculoRendimiento = async (datosEmpaquetados) => {
  try {
    const respuesta = await axios.post(
      `${URL_BACKEND}/calcular`,
      datosEmpaquetados,
    );
    return respuesta.data; // Devolvemos solo los datos útiles
  } catch (error) {
    console.error("Error en la comunicación con la API:", error);
    // Lanzamos el error hacia arriba para que App.jsx decida cómo avisar al usuario
    throw new Error("No se ha podido contactar con el servidor FastAPI.");
  }
};

// Aquí abajo puedes añadir en el futuro más funciones:
// export const guardarProyecto = async (datos) => { ... }
// export const obtenerClimaHistorico = async (coordenadas) => { ... }
