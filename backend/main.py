import os
import httpx
import math
import asyncio # <-- NUEVO: Para hacer llamadas en paralelo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Any
from dotenv import load_dotenv

# Importaciones geoespaciales
from shapely.geometry import LineString
from pyproj import Transformer
from shapely.ops import transform

load_dotenv()
API_KEY_WEATHER = os.getenv("WEATHER_API_KEY")
TOKEN_ESIOS = os.getenv("ESIOS_TOKEN") 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DatosEntrada(BaseModel):
    tipo: str
    coordenadas: List[Any]
    diametro: float
    resistencia: float
    emisividad: float
    temp_max: float
    altura_cable: float

# Shapely
def calcular_longitud_km(coordenadas):
    """
    Convierte latitudes y longitudes (grados) en metros reales
    usando la proyección Mercator y Shapely.
    """
    # 1. Extraer puntos (lon, lat)
    puntos = [(pt['lng'], pt['lat']) for pt in coordenadas]
    
    # 2. Crear la línea geométrica
    linea = LineString(puntos)
    
    # 3. Transformar de grados (EPSG:4326) a metros (EPSG:3857)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    linea_metros = transform(transformer.transform, linea)
    
    # 4. Devolver en kilómetros
    return linea_metros.length / 1000.0



# Clientes APIs
async def obtener_clima_openmeteo(client, lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m"
    respuesta = await client.get(url)
    datos = respuesta.json().get('current', {})
    
    t_amb = datos.get('temperature_2m', 25.0)
    v_viento_10m = datos.get('wind_speed_10m', 10.0) / 3.6 # Convertir a m/s
    return t_amb, v_viento_10m

async def obtener_radiacion_pvgis(client, lat, lon):
    
    url = f"https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat={lat}&lon={lon}&horpix=1&outputformat=json"
    try:
        respuesta = await client.get(url)
        datos = respuesta.json()
        # Extraemos la irradiación global horizontal (Hi) promedio del mes actual (simplificado)
        return 800.0 # W/m2 
    except:
        return 0.0 # Si es de noche o falla

# De momento es una simulacion ya que no poseo el token de REE
async def obtener_precio_esios(client):
    
    if not TOKEN_ESIOS:
        return 65.40 # €/MWh (Precio inventado)
    
    # No hay token de momento
    cabeceras = {
        'Accept': 'application/json; application/vnd.esios-api-v1+json',
        'Content-Type': 'application/json',
        'x-api-key': TOKEN_ESIOS
    }
    url = "https://api.esios.ree.es/indicators/1001" # Indicador del PVPC o Precio Spot
    respuesta = await client.get(url, headers=cabeceras)
    return 65.40 



# Calculo
def calcular_ampacidad(diametro_mm, res_ohm_km, emisividad, t_max_c, t_amb_c, vel_viento_ms_10m, radiacion_wm2, altura_cable_m):
    D = diametro_mm / 1000.0  
    R = res_ohm_km / 1000.0   
    if t_amb_c >= t_max_c: return 0.0

    Tk_max, Tk_amb = t_max_c + 273.15, t_amb_c + 273.15
    viento_corregido_ms = vel_viento_ms_10m * ((altura_cable_m / 10.0) ** 0.16)

    Ps = emisividad * radiacion_wm2 * D
    Pr = 5.67e-8 * emisividad * math.pi * D * (Tk_max**4 - Tk_amb**4)
    
    viento_efectivo = max(viento_corregido_ms, 0.1) 
    Pc = 1.01 + 0.0372 * ((D * 1000) ** 0.52) * (viento_efectivo ** 0.52) * (t_max_c - t_amb_c)

    calor_a_disipar = Pc + Pr - Ps
    if calor_a_disipar <= 0: return 0.0

    return round(math.sqrt(calor_a_disipar / R), 2)



@app.post("/calcular")
async def calcular_rendimiento(datos: DatosEntrada):
    try:
        # Verificamos que solo nos lleguen líneas (cables)
        if datos.tipo != 'Line':
            return {"status": "error", "mensaje": "Por favor, dibuja solo una línea (cable) en el mapa, no polígonos."}
            
        coordenadas_linea = datos.coordenadas

        lat_centro = coordenadas_linea[0]['lat']
        lon_centro = coordenadas_linea[0]['lng']
        
        longitud_km = calcular_longitud_km(coordenadas_linea)

        # Llamada APIs (OpenMeteo para temperatura y viento, PVGIS para radiacion, Red Electrica costes)
        async with httpx.AsyncClient() as client:
            resultados = await asyncio.gather(
                obtener_clima_openmeteo(client, lat_centro, lon_centro),
                obtener_radiacion_pvgis(client, lat_centro, lon_centro),
                obtener_precio_esios(client)
            )
            
            # Desempaquetamos los resultados en orden
            (t_amb, v_viento_10m), radiacion, precio_mwh = resultados

        ampacidad = calcular_ampacidad(
            datos.diametro, datos.resistencia, datos.emisividad, 
            datos.temp_max, t_amb, v_viento_10m, radiacion, datos.altura_cable
        )

        # Pérdidas por Efecto Joule: P_perdida = I^2 * R * Longitud
        resistencia_total = (datos.resistencia / 1000.0) * (longitud_km * 1000.0)
        # Suponemos que el cable va al 80% de su capacidad máxima (Ampacidad)
        corriente_trabajo = ampacidad * 0.80
        perdidas_watios = (corriente_trabajo ** 2) * resistencia_total
        perdidas_mw = perdidas_watios / 1_000_000

        # Coste económico de esa energía perdida en 1 hora
        coste_perdidas_hora = perdidas_mw * precio_mwh

        return {
            "status": "éxito",
            "mensaje": (
                f"INFORME DEL TRAZADO\n"
                f"------------------------\n"
                f"Longitud trazada: {round(longitud_km, 2)} km\n"
                f"Clima local: {t_amb}ºC | Viento: {round(v_viento_10m, 1)} m/s\n"
                f"Precio Spot Energía: {precio_mwh} €/MWh\n\n"
                f"Ampacidad máxima: {ampacidad} A\n"
                f"Energía perdida en calor: {round(perdidas_mw, 4)} MW\n"
                f"Coste de pérdidas (hora): {round(coste_perdidas_hora, 2)} €"
            )
        }
        
    except Exception as e:
        return {"status": "error", "mensaje": f"Error en el servidor: {str(e)}"}