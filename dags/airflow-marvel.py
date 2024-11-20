from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import json
import time
from hashlib import md5

# Marvel API credentials
PUBLIC_KEY = "your_public_key"
PRIVATE_KEY = "your_private_key"

# Generate a hash for the Marvel API
def generate_hash(ts):
    return md5(f"{ts}{PRIVATE_KEY}{PUBLIC_KEY}".encode("utf8")).hexdigest()

# Function to get characters and comics data
def transform_load_comics_data(task_instance):
    # Extract the character data
    characters_data = task_instance.xcom_pull(task_ids="extract_characters_data")
    
    characters_comic_count = []
    
    for character in characters_data["data"]["results"]:
        character_id = character["id"]
        character_name = character["name"]
        
        # For each character, get the list of comics they are part of
        ts = str(time.time())
        hash_str = generate_hash(ts)

        # Fetch comics data for the specific character
        params = {
            "apikey": PUBLIC_KEY,
            "ts": ts,
            "hash": hash_str,
            "characters": character_id,  # Use character's ID to filter comics
        }

        response = task_instance.xcom_pull(task_ids="extract_comics_data", params=params)
        
        comics_count = response["data"]["count"]
        
        # Store character name and associated comics count
        characters_comic_count.append({
            "Character Name": character_name,
            "Comics Count": comics_count
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(characters_comic_count)

    # Save to S3
    aws_credentials = {"key": "your_aws_access_key", "secret": "your_aws_secret_key"}
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d%H%M%S")
    file_name = f"marvel_characters_comics_{dt_string}.csv"
    df.to_csv(
        f"s3://your_s3_bucket_name/{file_name}",
        index=False,
        storage_options=aws_credentials,
    )

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
    is_marvel_api_ready = HttpSensor(
        task_id="is_marvel_api_ready",
        http_conn_id="marvel_api",  # Define this connection in Airflow
        endpoint="/v1/public/characters",  # Check if characters API is available
    )

    # Task 2: Extract characters data
    extract_characters_data = SimpleHttpOperator(
        task_id="extract_characters_data",
        http_conn_id="marvel_api",
        endpoint="/v1/public/characters",  # Fetch data from the characters endpoint
        method="GET",
        response_filter=lambda r: json.loads(r.text),
        log_response=True,
    )

    # Task 3: Extract comics data for each character (filtered by character ID)
    extract_comics_data = SimpleHttpOperator(
        task_id="extract_comics_data",
        http_conn_id="marvel_api",
        endpoint="/v1/public/comics",  # Fetch data from the comics endpoint
        method="GET",
        response_filter=lambda r: json.loads(r.text),
        log_response=True,
    )

    # Task 4: Transform and load the data into a CSV
    transform_load_comics_data_task = PythonOperator(
        task_id="transform_load_comics_data",
        python_callable=transform_load_comics_data,
    )

    # Task sequence
    is_marvel_api_ready >> extract_characters_data >> extract_comics_data >> transform_load_comics_data_task
