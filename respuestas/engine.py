import pandas as pd
import time
import os

def cargar_datos():
    print("Iniciando Generador de Respuestas...")
    ruta_csv = '/app/data/buildings.csv' #docker como que crea esos directorios de carpeta en su mundo virtual, terrible ezquizofrénico no?
    
    if os.path.exists(ruta_csv):
        try:
            # carga la wea de CSV en memoria
            df = pd.read_csv(ruta_csv)
            print(f"¡Éxito! Se cargaron {len(df)} registros correctamente.")
            print("Muestra de los datos:")
            print(df.head(3)) # imprime las 3 primeras filas
            return df
        except Exception as e:
            print(f"Error fatal al leer el CSV: {e}")
            return None
    else:
        print(f"CRÍTICO: No se encontró el archivo en {ruta_csv}")
        return None

if __name__ == "__main__":
    datos = cargar_datos()
    
    # este loop infinito evita que el contenedor haga "exited with code 0"
    print("Esperando consultas desde la caché...")
    while True:
        time.sleep(10)

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
