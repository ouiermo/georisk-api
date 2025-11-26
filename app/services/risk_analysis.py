import ee
import geemap
import pandas as pd
import numpy as np
import os
import re
import geopandas as gpd
import json
import uuid
from datetime import datetime
from dataclasses import dataclass
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class UmbralesRiesgo:
    PENDIENTE_CRITICA: float = 30.0; PENDIENTE_ALTA: float = 20.0; PENDIENTE_MODERADA: float = 10.0
    DISTANCIA_FALLA_CRITICA: int = 5000; DISTANCIA_FALLA_MODERADA: int = 10000
    LLUVIA_DETONANTE_ALTA: int = 150; LLUVIA_DETONANTE_MODERADA: int = 100

@dataclass
class PesosFactores:
    PESO_PENDIENTE: float = 0.40; PESO_FALLA_GEOLOGICA: float = 0.30
    PESO_LLUVIA_DETONANTE: float = 0.30

def get_riesgo_deslizamiento(poi, anio=2022, umbrales=UmbralesRiesgo()):
    try:
        # 1. Elevación y Pendiente (SRTM)
        dem = ee.Image('USGS/SRTMGL1_003')
        slope = ee.Terrain.slope(dem)
        
        # 2. Lluvias (CHIRPS)
        precip = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD')\
                   .filterDate(f'{anio}-01-01', f'{anio}-12-31').max()
        
        # Reducción de datos en el punto exacto
        # Agregamos 'elevation' al reducer
        combined = dem.rename('elevation').addBands(slope).addBands(precip)
        
        vals = combined.reduceRegion(
            reducer=ee.Reducer.first(), geometry=poi, scale=30
        ).getInfo()
        
        slope_val = vals.get('slope', 0) or 0
        precip_val = vals.get('precipitation', 0) or 0
        elev_val = vals.get('elevation', 0) or 0
        
        # Cálculo de Score
        score = 0
        if slope_val > umbrales.PENDIENTE_CRITICA: score += 5
        elif slope_val > umbrales.PENDIENTE_ALTA: score += 3
        if precip_val > umbrales.LLUVIA_DETONANTE_ALTA: score += 3
        
        final_score = min(score, 10)
        
        return {
            "score": final_score,
            "datos_tecnicos": {
                "Pendiente": f"{slope_val:.1f}°",  # DATO REAL
                "Cota": f"{int(elev_val)} m.s.n.m", # DATO REAL
                "Lluvia Máx": f"{int(precip_val)} mm" # DATO REAL
            }
        }
    except Exception as e:
        logger.error(f"Error en deslizamiento: {e}")
        return {"score": 0, "datos_tecnicos": {"Error": "Sin datos"}, "error": str(e)}

def analizar_riesgo_inundacion_robusto(poi):
    try:
        año_analisis = 2022
        PRECIP_THRESHOLD, LANDCOVER_CLASSES, WATER_OCCURRENCE_THRESHOLD = 30, [50, 60], 10
        precip = ee.ImageCollection('UCSB-CHG/CHIRPS/PENTAD').filterDate(f'{año_analisis}-01-01', f'{año_analisis}-12-31').max()
        landcover = ee.ImageCollection("ESA/WorldCover/v200").first().select('Map')
        water_occurrence = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
        combined = precip.addBands(landcover).addBands(water_occurrence)
        vals = combined.reduceRegion(ee.Reducer.first(), poi, 30).getInfo()
        precip_val = vals.get('precipitation'); landcover_val = vals.get('Map'); occurrence_val = vals.get('occurrence')
        riesgo = 0
        if precip_val is not None and precip_val > PRECIP_THRESHOLD: riesgo += 1
        if landcover_val is not None and landcover_val in LANDCOVER_CLASSES: riesgo += 1
        if occurrence_val is not None and occurrence_val > WATER_OCCURRENCE_THRESHOLD: riesgo += 2
        return 2 if riesgo >= 3 else (1 if riesgo >= 1 else 0)
    except Exception as e:
        logging.error(f"Error en análisis de inundación: {e}")
        return -1

def get_riesgo_incendio_clima(poi, anio=2022):
    try:
        # 1. NDVI (Vegetación)
        s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')\
               .filterDate(f'{anio}-01-01', f'{anio}-03-30')\
               .filterBounds(poi)\
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))\
               .median()
        ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # 2. Temperatura Suelo (MODIS)
        temp = ee.ImageCollection("MODIS/061/MOD11A1")\
                 .filterDate(f'{anio}-01-01', f'{anio}-03-30')\
                 .select('LST_Day_1km').mean().multiply(0.02).subtract(273.15)
        
        vals = ndvi.addBands(temp).reduceRegion(ee.Reducer.first(), poi, 30).getInfo()
        
        ndvi_val = vals.get('NDVI', 0) or 0
        temp_val = vals.get('LST_Day_1km', 0) or 0
        
        riesgo = 0
        if ndvi_val < 0.3: riesgo += 1
        if temp_val > 30: riesgo += 1
        
        return {
            "riesgo_index": riesgo,
            "datos_tecnicos": {
                "NDVI": f"{ndvi_val:.2f}", # DATO REAL
                "Temp. Suelo": f"{temp_val:.1f}°C", # DATO REAL
                "Vegetación": "Baja" if ndvi_val < 0.3 else "Media/Alta" # INFERENCIA REAL
            }
        }
    except Exception as e:
        logger.error(f"Error en incendio: {e}")
        return {"riesgo_index": 0, "datos_tecnicos": {"Error": "Sin datos"}, "error": str(e)}

def analizar_riesgo_volcanico(poi):
    try:
        path_volcanes = os.path.join(settings.DATA_DIR, "volcanes.csv")
        df_volcanes = pd.read_csv(path_volcanes)
        gdf_volcanes = gpd.GeoDataFrame(df_volcanes, geometry=gpd.points_from_xy(df_volcanes.Longitud, df_volcanes.Latitud), crs="EPSG:4326")
        ee_volcanes = geemap.geopandas_to_ee(gdf_volcanes)
        volcanes_cercanos = ee_volcanes.filterBounds(poi.buffer(100000)).filter(ee.Filter.gte('Categoría', 3)).size().getInfo()
        return 0 if volcanes_cercanos < 1 else (1 if volcanes_cercanos <= 4 else 2)
    except Exception: return -1

def analizar_clima_temperaturas(poi):
    try:
        resultados = {}
        region = poi.buffer(1000)
        año_actual = 2022
        def get_frequent_temp(band_name):
            coll = ee.ImageCollection("MODIS/061/MOD11A1").filter(ee.Filter.calendarRange(año_actual, año_actual, 'year')).select(band_name).map(lambda i: i.multiply(0.02).subtract(273.15))
            def extract(img): return ee.Feature(None, {'t': img.reduceRegion(ee.Reducer.toList(), region, 1000).get(band_name)})
            temps = [t for sl in coll.map(extract).aggregate_array('t').getInfo() if sl for t in sl if t is not None]
            if not temps: return None
            hist, bins = np.histogram(temps, bins=50)
            return (bins[np.argmax(hist)] + bins[np.argmax(hist) + 1]) / 2
        resultados['Temp_Max_Frec_Dia'] = get_frequent_temp('LST_Day_1km')
        resultados['Temp_Max_Frec_Noche'] = get_frequent_temp('LST_Night_1km')
        years = list(range(2010, año_actual + 1))
        temps_hist = [ee.ImageCollection("MODIS/061/MOD11A1").filter(ee.Filter.calendarRange(y, y, 'year')).select('LST_Day_1km').map(lambda i: i.multiply(0.02).subtract(273.15)).reduce(ee.Reducer.minMax().combine(ee.Reducer.mean(), "", True)).reduceRegion(ee.Reducer.first(), region, 1000).getInfo() for y in years]
        def get_trend(key):
            data = [d.get(key) for d in temps_hist if d.get(key) is not None]
            if len(data) < 2: return 0
            slope, _ = np.polyfit(np.arange(len(data)), data, 1)
            return 2 if slope > 0.1 else (1 if slope > 0 else (-1 if slope < -0.1 else (-2 if slope < 0 else 0)))
        resultados['Tendencia_Max'] = get_trend('LST_Day_1km_max')
        resultados['Tendencia_Media'] = get_trend('LST_Day_1km_mean')
        resultados['Tendencia_Min'] = get_trend('LST_Day_1km_min')
        return resultados
    except Exception: return {}

def generar_certificado(lat, lon, nombre="Ubicación Solicitada"):
    poi = ee.Geometry.Point(lon, lat)
    
    # Execute analyses
    riesgo_deslizamiento = get_riesgo_deslizamiento(poi)
    riesgo_inundacion = analizar_riesgo_inundacion_robusto(poi)
    riesgo_incendio = get_riesgo_incendio_clima(poi)
    riesgo_volcanico = analizar_riesgo_volcanico(poi)
    clima = analizar_clima_temperaturas(poi)
    
    # Build DataFrame-like structure for the autofact logic
    # Note: Some keys might be missing if we strictly follow the new structure, but we adapt below.
    row = {
        'nombre': nombre,
        'latitud': lat,
        'longitud': lon,
        'Riesgo_Deslizamiento': riesgo_deslizamiento,
        'Riesgo_Inundacion': riesgo_inundacion,
        'Riesgo_Incendio': riesgo_incendio,
        'Riesgo_Volcanico': riesgo_volcanico,
        **clima
    }
    
    # Autofact logic adapted
    indicadores = []
    penalizacion_score = 0

    # A. Suelo
    val_deslizamiento = riesgo_deslizamiento.get('score', 0)
    if val_deslizamiento >= 5.0:
        estado_suelo = {"color": "red", "texto": "Riesgo Alto", "mensaje": "Pendiente crítica inestable."}
        penalizacion_score += 40
    elif val_deslizamiento >= 2.5:
        estado_suelo = {"color": "yellow", "texto": "Riesgo Moderado", "mensaje": "Requiere mecánica de suelos específica."}
        penalizacion_score += 15
    else:
        estado_suelo = {"color": "green", "texto": "Estable", "mensaje": "Sin riesgos evidentes de remoción."}

    indicadores.append({
        "id": "suelo",
        "titulo": "Estabilidad Geotécnica",
        "estado": estado_suelo["texto"],
        "color": estado_suelo["color"],
        "mensaje": estado_suelo["mensaje"],
        "detalles": riesgo_deslizamiento.get('datos_tecnicos', {})
    })

    # B. Agua
    val_inundacion = riesgo_inundacion
    if val_inundacion >= 2:
        estado_agua = {"color": "red", "texto": "Zona Inundable", "mensaje": "Cuerpos de agua permanentes detectados."}
        penalizacion_score += 50
    elif val_inundacion == 1:
        estado_agua = {"color": "yellow", "texto": "Precaución", "mensaje": "Saturación hídrica en eventos extremos."}
        penalizacion_score += 20
    else:
        estado_agua = {"color": "green", "texto": "Seguro", "mensaje": "Zona fuera de cauces principales."}

    indicadores.append({
        "id": "agua",
        "titulo": "Riesgo de Inundación",
        "score_tecnico": int(val_inundacion),
        "estado": estado_agua["texto"],
        "color_ui": estado_agua["color"],
        "mensaje_cliente": estado_agua["mensaje"]
    })

    # C. Fuego
    val_incendio = riesgo_incendio.get('riesgo_index', 0)
    tendencia_temp = row.get('Tendencia_Max', 0)
    if val_incendio > 0 or tendencia_temp >= 2:
        estado_fuego = {"color": "yellow", "texto": "Alerta Ambiental", "mensaje": "Tendencia de calentamiento o sequedad detectada."}
        penalizacion_score += 20
    else:
        estado_fuego = {"color": "green", "texto": "Bajo Riesgo", "mensaje": "Humedad de vegetación (NDVI) saludable."}

    indicadores.append({
        "id": "fuego",
        "titulo": "Amenaza Incendio",
        "estado": estado_fuego["texto"],
        "color": estado_fuego["color"],
        "mensaje": estado_fuego["mensaje"],
        "detalles": riesgo_incendio.get('datos_tecnicos', {})
    })

    score_final = max(0, 100 - penalizacion_score)
    if score_final >= 80:
        sello = "APTO PARA INVERSIÓN"
    elif score_final >= 50:
        sello = "APTO CON MITIGACIÓN"
    else:
        sello = "NO RECOMENDADO / RIESGO CRÍTICO"

    certificado = {
        "meta": {
            "certificado_id": f"GR-{str(uuid.uuid4())[:8].upper()}",
            "fecha_emision": datetime.now().isoformat(),
            "version_motor": "v11.2-Autofact-API"
        },
        "propiedad": {
            "nombre": nombre,
            "latitud": lat,
            "longitud": lon
        },
        "resumen_ejecutivo": {
            "score_global": score_final,
            "sello_garantia": sello,
            "color_global": "green" if score_final >= 80 else ("orange" if score_final >= 50 else "red")
        },
        "detalle_indicadores": indicadores,
        "legal": {
            "disclaimer": "Informe generado por GeoRisk AI basado en datos satelitales NASA/ESA. No reemplaza estudios de ingeniería in-situ.",
            "fuentes": ["USGS SRTM", "Sentinel-2", "MODIS", "CHIRPS"]
        }
    }
    return certificado
