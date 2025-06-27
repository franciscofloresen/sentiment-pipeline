# producer.py
# Este script se conecta a la API de X (Twitter), busca tweets
# y los envía a un Amazon Kinesis Data Stream.

import os
import json
import time
import requests
import boto3
from dotenv import load_dotenv
from urllib.parse import quote

# --- Configuración Inicial ---
load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Configuración de AWS y Kinesis
AWS_REGION = "us-east-1"
KINESIS_STREAM_NAME = "twittersentiment-stream"

# --- Lógica de Twitter ---
# Usamos 'lang:es' para buscar tweets en español.
# '-is:retweet' para excluir retweets y tener datos más originales.
SEARCH_QUERY = "#tecnologia OR #devops OR #cloud -is:retweet lang:es"


def create_headers(bearer_token):
    """Crea los encabezados necesarios para la autenticación con la API de Twitter."""
    headers = {"Authorization": f"Bearer {bearer_token}"}
    return headers


def connect_to_endpoint(url, headers):
    """Se conecta al endpoint de la API de Twitter y devuelve la respuesta en JSON."""
    response = requests.request("GET", url, headers=headers)
    print(f"Respuesta de la API de Twitter: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"Error en la solicitud: {response.status_code} {response.text}")
    return response.json()


# --- Lógica de AWS Kinesis ---

def send_to_kinesis(client, stream_name, data):
    """Envía un registro de datos al stream de Kinesis."""
    try:
        # Kinesis espera los datos como un string, por eso usamos json.dumps.
        # La PartitionKey ayuda a distribuir los datos entre los shards.
        # Como solo tenemos uno, podemos usar un valor simple como el ID del tweet.
        response = client.put_record(
            StreamName=stream_name,
            Data=json.dumps(data),
            PartitionKey=str(data.get('id', 'default_partition_key'))
        )
    except Exception as e:
        print(f"Error al enviar a Kinesis: {e}")


# --- Función Principal ---

def main():
    if not BEARER_TOKEN:
        print("Error: La variable de entorno TWITTER_BEARER_TOKEN no está definida.")
        return

    headers = create_headers(BEARER_TOKEN)

    encoded_query = quote(SEARCH_QUERY)

    search_url = f"https://api.twitter.com/2/tweets/search/recent?query={encoded_query}&tweet.fields=created_at,public_metrics"

    kinesis_client = boto3.client("kinesis", region_name=AWS_REGION)

    print("--- Iniciando productor de tweets ---")
    print(f"Buscando tweets con la consulta: '{SEARCH_QUERY}'")
    print(f"Enviando a Kinesis Stream: '{KINESIS_STREAM_NAME}' en la región '{AWS_REGION}'")
    print("Presiona Ctrl+C para detener.")

    try:
        while True:
            # Obtener tweets de la API
            json_response = connect_to_endpoint(search_url, headers)

            if json_response.get("meta", {}).get("result_count", 0) > 0:
                tweets = json_response.get("data", [])
                print(f"Se encontraron {len(tweets)} tweets.")

                # Enviar cada tweet a Kinesis
                for tweet in tweets:
                    print(f"\nProcesando tweet ID: {tweet['id']}")
                    print(f"Texto: {tweet['text'][:80]}...")  # Imprime los primeros 80 caracteres
                    send_to_kinesis(kinesis_client, KINESIS_STREAM_NAME, tweet)

            else:
                print("No se encontraron tweets en esta consulta.")
            print("\nEsperando 300 segundos para la siguiente consulta...")
            time.sleep(300)

    except KeyboardInterrupt:
        print("\n--- Deteniendo el productor ---")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")


if __name__ == "__main__":
    main()