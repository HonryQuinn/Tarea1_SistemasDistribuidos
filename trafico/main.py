import redis
import time
import json

r = redis.Redis(host='cache', port=6379, decode_responses=True)

while True:
    data={"sensor_id":1, "status": "activo", "payload": "..."}
    r.rpush('cola_mensajes', json.dumps(data))
    print("Mensaje enviado")
    time.sleep(2)
