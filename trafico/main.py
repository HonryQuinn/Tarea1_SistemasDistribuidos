import redis
import numpy as np
import random
import time

# Configuración inicial
try:
    r = redis.Redis(host='cache', port=6379, decode_responses=True)
    r.ping()
    print("conexin éxitosa con redis")
except redis.ConnectionError:
    print("ño e pudo coñectar con redis")
    print("ola")
ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"] # [cite: 95]
CONSULTAS = ["Q1", "Q2", "Q3", "Q4", "Q5"] # [cite: 35]
N_PEDIDOS = 1000 # Cantidad de consultas por experimento

def enviar_a_sistema(key):
# 1. Intentar obtener la respuesta desde Redis
    respuesta = r.get(key)
    
    if respuesta:
        # --- CACHE HIT ---
        # Incrementamos un contador de hits para las métricas
        r.incr("stats:hits")
        print(f"[HIT] Key: {key}") # Opcional para debug
    else:
        # --- CACHE MISS ---
        r.incr("stats:miss")
        
        # 2. Notificar al backend (generador_respuestas)
        # En sistemas distribuidos, esto se suele hacer mediante una 
        # lista de Redis (Queue) que el backend está escuchando.
        r.lpush("peticiones_pendientes", key)
        
        # 3. Bloquear hasta que el backend procese y guarde en Redis
        # (Opcional: puedes hacer un blpop o simplemente esperar a que aparezca la key)
        # Para esta tarea, el backend debería guardar el resultado en Redis usando 'key'
        print(f"[MISS] Key enviada a backend: {key}")
def ejecutar_simulacion(modo):
    print(f"=== inicio {modo} ===")
    r.flushall() # Vacía el cache para igualdad de condiciones

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
        conf = random.uniform([0.0, 0.5, 0.7])

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

        enviar_a_sistema(key)

    print(f"=== fin {modo} ===")

# --- FLUJO PRINCIPAL ---
ejecutar_simulacion("uniforme")

# Pequeña pausa entre experimentos para que el sistema de métricas procese
time.sleep(5)

ejecutar_simulacion("zipf")
