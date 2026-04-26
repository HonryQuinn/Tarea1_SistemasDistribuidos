import redis
import numpy as np
import random
import time
import json

# Configuración inicial
try:
    r = redis.Redis(host='cache', port=6379, decode_responses=True)
    r.ping()
    print("conexión éxitosa con redis")
except redis.ConnectionError:
    print("ño e pudo coñectar con redis")
    print("ola")
ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"] # [cite: 95]
CONSULTAS = ["Q1", "Q2", "Q3", "Q4", "Q5"] # [cite: 35]
N_PEDIDOS = 1000 # Cantidad de consultas por experimento

def enviar_a_sistema(key, tipo, zona, conf, zona_b=None, bins=5):
    # Aquí iría la lógica que mencionamos antes: 
    # 1. Ver en Redis -> 2. Si es MISS, pedir al Backend y guardar en Redis.
    respuesta = r.get(key)
    
    if respuesta:
        # CACHE HIT
        r.incr("stats:hits")
        print(f"[HIT ] Key: {key}") 
    else:
        # CACHE MISS
        r.incr("stats:miss")
        print(f"[MISS] Key: {key} -> Enviando a cola", flush=True)
        
        # 2. Crear el diccionario con el formato que engine.py espera
        datos_consulta = {
            "tipo": tipo,
            "zona": zona,
            "zona_b": zona_b,
            "confidence_min": conf,
            "bins": bins,
            "cache_key": key
        }
        
        # 3. Enviar a la cola para que el motor lo procese
        r.lpush("cola:consultas", json.dumps(datos_consulta))

def ejecutar_simulacion(modo):
    print(f"=== inicio {modo} ===")
   # r.flushall() # Vacía el cache para igualdad de condiciones
    
    for _ in range(N_PEDIDOS):
        # 1. Selección de zona según distribución
        if modo == "zipf":
            # Zipf genera valores >= 1, ajustamos al índice de la lista
            idx = (np.random.zipf(a=1.2) - 1) % len(ZONAS)
            zona = ZONAS[idx]
        else:
            zona = random.choice(ZONAS)
            
        # 2. Selección de tipo de consulta y parámetros
        tipo = random.choice(CONSULTAS)
        conf = round(random.uniform(0.0, 0.9), 2) 
        
        zona_b=None
        bins=5

        # 3. Construcción de la Cache Key según el PDF
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
        enviar_a_sistema(key, tipo, zona, conf, zona_b, bins)
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

# Pequeña pausa entre experimentos para que el sistema de métricas procese
time.sleep(5) 

ejecutar_simulacion("zipf")
