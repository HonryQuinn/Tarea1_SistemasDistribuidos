import redis
import os
import time

r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=True)

def imprimir_resumen(modo):
    hits   = int(r.get(f"{modo}:hits") or 0)
    misses = int(r.get(f"{modo}:misses") or 0)
    total  = hits + misses

    lats = [float(x) for x in r.lrange(f"{modo}:latencies", 0, -1)]
    lats_sorted = sorted(lats)
    n = len(lats_sorted)
    p50 = lats_sorted[int(n * 0.50)]             if n > 0 else None
    p95 = lats_sorted[min(int(n * 0.95), n - 1)] if n > 0 else None

    timestamps = [float(t) for t in r.lrange(f"{modo}:timestamps", 0, -1)]
    now = time.time()
    recent = [t for t in timestamps if t >= now - 60]
    throughput = len(recent) / 60

    evs = r.lrange(f"{modo}:evictions", -2, -1)
    if len(evs) == 2:
        t1, c1 = evs[0].split(":")
        t2, c2 = evs[1].split(":")
        dt = float(t2) - float(t1)
        eviction_rate = ((float(c2) - float(c1)) / dt) * 60 if dt > 0 else 0.0
    else:
        eviction_rate = 0.0

    print(f"=== MÉTRICAS KLAS DE MIERDA {modo.upper()} ===")
    print(f"  Hits:          {hits}")
    print(f"  Misses:        {misses}")
    print(f"  Hit rate:      {round(hits/total, 4) if total > 0 else 0}")
    print(f"  Miss rate:     {round(misses/total, 4) if total > 0 else 0}")
    print(f"  Latencia p50:  {p50} ms")
    print(f"  Latencia p95:  {p95} ms")
    print(f"  Throughput:    {round(throughput, 4)} qps")
    print(f"  Eviction rate: {round(eviction_rate, 4)} ev/min")

# --- FLUJO PRINCIPAL ---

time.sleep(130)  # espera que terminen ambas simulaciones (1000 * 0.05s * 2 + 5s pausa)
imprimir_resumen("uniforme")
imprimir_resumen("zipf")