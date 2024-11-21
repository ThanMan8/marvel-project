from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import time
from hashlib import md5
import requests as rq

# Marvel API credentials
PUBLIC_KEY = "af87c8c1cc729f73f5496f1ef8f36ca3"
PRIVATE_KEY = "5d709430c05fa62a0d670cc070abccb1e5dc3c93"

# Generate Marvel API parameters
def get_marvel_api_params():
    ts = str(time.time())
    hash_str = md5(f"{ts}{PRIVATE_KEY}{PUBLIC_KEY}".encode("utf8")).hexdigest()
    return {
        "apikey": PUBLIC_KEY,
        "ts": ts,
        "hash": hash_str,
    }

# Check API readiness
def check_marvel_api():
    params = get_marvel_api_params()
    url = "https://gateway.marvel.com:443/v1/public/characters"
    response = rq.get(url, params=params)
    if response.status_code == 200:
        return True
    else:
        raise ValueError(f"API not ready: {response.status_code} {response.text}")

# Extract characters data
def extract_characters():
    params = get_marvel_api_params()
    url = "https://gateway.marvel.com:443/v1/public/characters"
    params.update({"orderBy": "name", "limit": 300})
    
    try:
        response = rq.get(url, params=params)
        response.raise_for_status()
    except rq.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch characters data: {e}")
    return response.json()

# Transform and load data
def transform_load_comics_data(task_instance):
    characters_data = task_instance.xcom_pull(task_ids="extract_characters")
    characters_comic_count = []

    for character in characters_data["data"]["results"]:
        character_id = character["id"]
        character_name = character["name"]

        # Fetch comics data for this character
        params = get_marvel_api_params()
        params.update({"characters": character_id})
        url = "https://gateway.marvel.com:443/v1/public/comics"
        
        try:
            response = rq.get(url, params=params)
            response.raise_for_status()
            comics_count = response.json()["data"]["count"]
        except rq.exceptions.RequestException as e:
            raise ValueError(f"Failed to fetch comics data for character {character_name}: {e}")
        
        characters_comic_count.append({
            "Character Name": character_name,
            "Comics Count": comics_count
        })

    # Save results to a CSV
    df = pd.DataFrame(characters_comic_count)
    now = datetime.now()
    dt_string = now.strftime('%Y%m%d%H%M%S')
    dt_string = 'current_marvel_data'+ dt_string
    # file_name = f"/home/airflow/marvel_characters_comics_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    df.to_csv(f"{dt_string}.csv",index=False)

# Default DAG arguments
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
with DAG(
    "marvel_characters_comics_dag",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
) as dag:

    # Task 1: Check if the Marvel API is available
    is_marvel_api_ready = PythonOperator(
        task_id="is_marvel_api_ready",
        python_callable=check_marvel_api,
    )

    # Task 2: Extract characters data
    extract_characters_task = PythonOperator(
        task_id="extract_characters",
        python_callable=extract_characters,
    )

    # Task 3: Transform and load data into a CSV
    transform_load_comics_data_task = PythonOperator(
        task_id="transform_load_comics_data",
        python_callable=transform_load_comics_data,
    )

    # Task sequence
    is_marvel_api_ready >> extract_characters_task >> transform_load_comics_data_task
