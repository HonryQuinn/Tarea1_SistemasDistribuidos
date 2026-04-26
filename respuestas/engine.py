import pandas as pd
import redis
import json
import time
import os
import numpy as np
from collections import namedtuple
from statistics import mean

print("Iniciando engine.py...")
 #cambie el host a "cache" para que se conecte al contenedor de redis, pero tiene que ir cache que es el nombre del servicio en el compose
r = redis.Redis(host=os.getenv("REDIS_HOST", "cache"),port=int(os.getenv("REDIS_PORT", 6379)),decode_responses=True)

ZONAS = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760},
}

# calcular para la consulta q3
zone_area_km2 = {}
for zona_id, bbox in ZONAS.items():
    lat_km = (bbox["lat_max"] - bbox["lat_min"]) * 111
    lon_km = (bbox["lon_max"] - bbox["lon_min"]) * 111 * abs((bbox["lat_max"] + bbox["lat_min"]) / 2)
    zone_area_km2[zona_id] = lat_km * lon_km

data = {}

picos = namedtuple("picos", ["latitude", "longitude", "area", "confidence"])

def cargar_datos():
    ruta = os.getenv("DATASET_PATH", "./buildings.csv") #cambiar el /app/data/buildints.csv
    print(f"Cargando dataset desde {ruta}...")
    df = pd.read_csv(ruta)
    print(f"Dataset cargado: {len(df)} registros")

    datos_por_zona = {}
    for zona_id, bbox in ZONAS.items():
        filtrado = df[
            (df["latitude"]  >= bbox["lat_min"]) & (df["latitude"]  <= bbox["lat_max"]) &
            (df["longitude"] >= bbox["lon_min"]) & (df["longitude"] <= bbox["lon_max"])
        ]
        datos_por_zona[zona_id] = [
            picos(row.latitude, row.longitude, row.area_in_meters, row.confidence)
            for row in filtrado.itertuples()
        ]
        print(f"{zona_id}: {len(datos_por_zona[zona_id])} edificios")

    return datos_por_zona

#consultas 

def q1_count(zone_id, confidence_min=0.0):
    records = data[zone_id]
    return sum(1 for r in records if r.confidence >= confidence_min)

def q2_area(zone_id, confidence_min=0.0):
    areas = [r.area for r in data[zone_id] if r.confidence >= confidence_min]
    return {"avg_area": mean(areas), "total_area": sum(areas), "n": len(areas)}

def q3_density(zone_id, confidence_min=0.0):
    count = q1_count(zone_id, confidence_min)
    area_km2 = zone_area_km2[zone_id]
    return count / area_km2

def q4_compare(zone_a, zone_b, confidence_min=0.0):
    da = q3_density(zone_a, confidence_min)
    db = q3_density(zone_b, confidence_min)
    return {"zone_a": da, "zone_b": db, "winner": zone_a if da > db else zone_b}

def q5_confidence_dist(zone_id, bins=5):
    scores = [r.confidence for r in data[zone_id]]
    counts, edges = np.histogram(scores, bins=bins, range=(0, 1))
    return [
        {"bucket": i, "min": float(edges[i]), "max": float(edges[i+1]), "count": int(counts[i])}
        for i in range(bins)
    ]

def procesar(consulta):
    tipo           = consulta["tipo"]
    zona           = consulta["zona"]
    zona_b         = consulta.get("zona_b")
    confidence_min = consulta.get("confidence_min", 0.0)
    bins           = consulta.get("bins", 5)
    cache_key      = consulta["cache_key"]

    if tipo == "Q1":
        resultado = q1_count(zona, confidence_min)
    elif tipo == "Q2":
        resultado = q2_area(zona, confidence_min)
    elif tipo == "Q3":
        resultado = q3_density(zona, confidence_min)
    elif tipo == "Q4":
        resultado = q4_compare(zona, zona_b, confidence_min)
    elif tipo == "Q5":
        resultado = q5_confidence_dist(zona, bins)

    r.set(cache_key, json.dumps(resultado), ex=60)
    print(f"Calculado y guardado | {cache_key}")

def esperar_redis():
    while True:
        try:
            if r.ping():
                print("Conectado a Redis")
                break
        except redis.ConnectionError:
            print("Esperando a Redis...")
            time.sleep(2)

def main():
    esperar_redis()

    global data
    data = cargar_datos()

    
    r.set("status:engine_ready", "1")
    print("Generador de respuestas listo, escuchando cola...")
    while True:
        try:
            _, mensaje_crudo = r.blpop("cola_consultas", timeout=0)
            consulta = json.loads(mensaje_crudo)
            procesar(consulta)
        except Exception as e:
            print(f"Error al procesar: {e}")

if __name__ == "__main__":
    main()
