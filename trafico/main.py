import redis
import numpy as np
import random
import time
import json

# Configuración inicial
try:
    r = redis.Redis(host='cache', port=6379, decode_responses=True)
    r.ping()
    print("conexin éxitosa con redis")
except redis.ConnectionError:
    print("ño e pudo coñectar con redis")

ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"] # [cite: 95]
CONSULTAS = ["Q1", "Q2", "Q3", "Q4", "Q5"] # [cite: 35]
N_PEDIDOS = 10 # Cantidad de consultas por experimento

def enviar_a_sistema(key, tipo, zona, conf, modo, zona_b=None, bins=5):
    t0 = time.perf_counter()
    respuesta = r.get(key)
    latencia_ms = (time.perf_counter() - t0) * 1000
    
    if respuesta:
        # --- CACHE HIT ---
        # Usamos llaves distintas para el contador y para la lista de latencias
        r.incr(f"{modo}:hits") 
        r.rpush(f"{modo}:latencies", latencia_ms)
        r.rpush(f"{modo}:timestamps", time.time())
        print(f"[HIT ] Key: {key}") 
    else:
        # --- CACHE MISS ---
        r.incr(f"{modo}:misses")
        print(f"[MISS] Key: {key} -> Enviando a cola", flush=True)
        
        datos_consulta = {
            "tipo": tipo,
            "zona": zona,
            "zona_b": zona_b,
            "confidence_min": conf,
            "bins": bins,
            "cache_key": key,
            "modo": modo # Ahora pasamos la variable correctamente
        }
        r.lpush("cola:consultas", json.dumps(datos_consulta))

        for _ in range(20):       # máximo ~2 segundos
            time.sleep(0.1)
            if r.exists(key):
                break
    
    # Métricas de desalojo (Evictions)
    info = r.info("stats")
    r.rpush(f"{modo}:evictions", f"{time.time()}:{info['evicted_keys']}")

def ejecutar_simulacion(modo):
    print(f"=== inicio {modo} ===", flush=True)
    #r.flushall() # COMENTA ESTA LÍNEA para que Zipf aproveche lo que cargó Uniforme

    for _ in range(N_PEDIDOS):
        # 1. Selección de zona
        if modo == "zipf":
            idx = (np.random.zipf(a=1.2) - 1) % len(ZONAS)
            zona = ZONAS[idx]
        else:
            zona = random.choice(ZONAS)

        # 2. Selección de tipo
        tipo = random.choice(CONSULTAS)
        conf = round(random.uniform(0.0, 0.9), 2)

        # 3. Construcción de la Cache Key
        zona_b = None
        bins = None
        if tipo == "Q1":
            key = f"count:{zona}:conf={conf}"
        elif tipo == "Q2":
            key = f"area:{zona}:conf={conf}"
        elif tipo == "Q3":
            key = f"density:{zona}:conf={conf}"
        elif tipo == "Q4":
            zona_b = random.choice([z for z in ZONAS if z != zona])
            key = f"compare:density:{zona}:{zona_b}:conf={conf}"
        elif tipo == "Q5":
            bins = random.choice([5, 10, 20])
            key = f"confidence_dist:{zona}:bins={bins}"

        # 4. Enviar y esperar un poco (El SLEEP que pediste)
        enviar_a_sistema(key, tipo, zona, conf, modo, zona_b, bins)
        time.sleep(0.05) # 50ms es suficiente para que el backend procese

    print(f"=== fin {modo} ===", flush=True)

def esperar_engine():
    print("Esperando a que el generado de respuesta cargue el dataset", flush=True)
    while not r.get("status:engine_ready"):
        time.sleep(2)
    print("Dataset detectado, iniciando simulación")

esperar_engine()

# --- FLUJO PRINCIPAL ---
ejecutar_simulacion("uniforme")
time.sleep(5)   
ejecutar_simulacion("zipf")


