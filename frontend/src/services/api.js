import axios from "axios";

const URL_BACKEND = "http://localhost:8000";

/**
 * Envía el paquete de datos al backend para calcular los rates estacionales.
 * Gestiona errores de red y errores de validación de FastAPI.
 */
export const enviarCalculoRendimiento = async (paqueteDatos) => {
  try {
    const respuesta = await axios.post(
      `${URL_BACKEND}/calcular/rates-estacionales`,
      paqueteDatos
    );

    // Axios ya devuelve el JSON parseado en respuesta.data
    return respuesta.data;

  } catch (error) {
    // Si el servidor respondió con un error (ej. 422 Unprocessable Entity)
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 422 && data.detail?.errores) {
        // Errores específicos de tu validador de geometría en Python
        const listaErrores = data.detail.errores.join(" | ");
        throw new Error(`Validación fallida: ${listaErrores}`);
      }
      
      throw new Error(data.detail || `Error del servidor (${status})`);
    } 
    
    // Si hubo un error de red (el servidor no responde)
    if (error.request) {
      throw new Error("No se pudo contactar con el servidor. Revisa si el backend está activo.");
    }

    throw new Error("Ocurrió un error inesperado al procesar la petición.");
  }
};

export const obtenerClimatologiaHistorica = async (lat, lon) => {
  try {
    const respuesta = await axios.get(`${URL_BACKEND}/climatologia/percentiles`, {
      params: { lat, lon }
    });

    // ¡NUEVO! Detectamos si el backend de Python capturó un error internamente
    if (respuesta.data.status === "error") {
      throw new Error(respuesta.data.mensaje || "Fallo interno en el cálculo de percentiles (Python)");
    }

    return respuesta.data.percentiles; 
  } catch (error) {
    console.error("Error al obtener histórico:", error);
    // Relanzamos el error para que App.jsx lo pueda mostrar
    throw error;
  }
};