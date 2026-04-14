import pandas as pd
import redis
import time
import os

r=redis.Redis(host="cache", port=6379, decode_responses=True)

def cargar_dataset():
    path = "/app/data/967_buildings.csv"

    print(f"Cargando dataset desde {path}")
    df = pd.read_csv(path)
    print(f"Dataset cargado: {len(df)} registros")
    return df

def main():
    while True:
        try:
            if r.ping():
                    print("Conectado a Redis")
                    break
        except redis.ConnectionError:
                print("Esperando a Redis")
                time.sleep(2)


    df = cargar_dataset()

    print("Generador de respuestas listo")
    while True:
        try:
            _, mensaje_crudo =r.blpop('cola_mensajjes', timeout=0)
            datos_evento = json.loads(mensaje_crudo)

            print(f"Evento procesado: {datos_evento}")
        except Exception as e:
            print(f"error al procesar mensaje:{e}")

if __name__ == "__main__":
    main()
