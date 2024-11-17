from airflow import DAG
from datetime import timedelta,datetime
from airflow.providers.http.sensors.http import HttpSensor
import json
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
import pandas as pd
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.postgres.operators.postgres import PostgresOperator


def kelvin_to_fahrenheit(temp_in_kelvin):
    temp_in_fahrenheit = (temp_in_kelvin - 273.15) * (9/5) + 32
    return round(temp_in_fahrenheit, 3)

def transform_load_data(task_instance):
    data = task_instance.xcom_pull(task_ids="group_a.extract_weather_data")  ## xcom_pull belongs to airflow
    
    city = data["name"]
    weather_description = data["weather"][0]['description']
    temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp"])
    feels_like_farenheit= kelvin_to_fahrenheit(data["main"]["feels_like"])
    min_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_min"])
    max_temp_farenheit = kelvin_to_fahrenheit(data["main"]["temp_max"])
    pressure = data["main"]["pressure"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    time_of_record = datetime.utcfromtimestamp(data['dt'] + data['timezone'])
    sunrise_time = datetime.utcfromtimestamp(data['sys']['sunrise'] + data['timezone'])
    sunset_time = datetime.utcfromtimestamp(data['sys']['sunset'] + data['timezone'])

    transformed_data = {"city": city,
                        "description": weather_description,
                        "temperature_farenheit": temp_farenheit,
                        "feels_like_farenheit": feels_like_farenheit,
                        "minimun_temp_farenheit":min_temp_farenheit,
                        "maximum_temp_farenheit": max_temp_farenheit,
                        "pressure": pressure,
                        "humidity": humidity,
                        "wind_speed": wind_speed,
                        "time_of_record": time_of_record,
                        "sunrise_local_time)":sunrise_time,
                        "sunset_local_time)": sunset_time                        
                        }
    transformed_data_list = [transformed_data]
    df_data = pd.DataFrame(transformed_data_list)
    
    df_data.to_csv("current_weather_data.csv", index=False, header=False)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 9, 10),
    'email': ['manoloudas88@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}


with DAG('weather_dag_2',
        default_args=default_args,
        schedule = '@daily',
        catchup=False) as dag:
    
        start_pipeline = DummyOperator(
                task_id = 'tsk_start_pipeline'
        )

        with TaskGroup(group_id='group_a', tooltip='extraxt_from_s3_weatherapi') as group_A:
                create_table_1 = PostgresOperator(
                        task_id = 'tsk_create_table_1',
                        postgres_conn_id = "postgres_conn",
                        sql = ''' 
                                CREATE TABLE IF NOT EXISTS city_look_up (
                                city TEXT NOT NULL,
                                state TEXT NOT NULL,
                                cencus_2020 numeric NOT NULL,
                                land_Area_sq_mile_2020 numeric NOT NULL
                                );
                                '''
                )

                truncate_table = PostgresOperator(
                        task_id = 'tsk_truncate_table',
                        postgres_conn_id = "postgres_conn",
                        sql = ''' TRUNCATE TABLE city_look_up;
                              '''
                )

                uploadS3_to_postgres  = PostgresOperator(
                        task_id = "tsk_uploadS3_to_postgres",
                        postgres_conn_id = "postgres_conn",
                        sql = "SELECT aws_s3.table_import_from_s3('city_look_up', '', '(format csv, DELIMITER '','', HEADER true)', 'youtube-dataengineering', 'us_city.csv', 'us-east-1');"
                )
                
                create_table_2 = PostgresOperator(
                task_id='tsk_create_table_2',
                postgres_conn_id = "postgres_conn",
                sql= ''' 
                    CREATE TABLE IF NOT EXISTS weather_data (
                    city TEXT,
                    description TEXT,
                    temperature_farenheit NUMERIC,
                    feels_like_farenheit NUMERIC,
                    minimun_temp_farenheit NUMERIC,
                    maximum_temp_farenheit NUMERIC,
                    pressure NUMERIC,
                    humidity NUMERIC,
                    wind_speed NUMERIC,
                    time_of_record TIMESTAMP,
                    sunrise_local_time TIMESTAMP,
                    sunset_local_time TIMESTAMP                    
                );
                '''
                )
                
                is_weather_api_ready = HttpSensor(          ## this sensor check if conditions are met before trigger the pipeline
                tsk_id ='is_weather_api_ready',            ## Here if API is ready before go further
                httap_conn_id='weathermap_api',
                endpoint='/data/2.5/weather?q=Portland&APPID=2bcc5f2a1b1f3cbb4ea403d41f271c63'
                )

                extract_weather_data = SimpleHttpOperator(      
                task_id = 'extract_weather_data',
                http_conn_id = 'weathermap_api',
                endpoint='/data/2.5/weather?q=Portland&APPID=2bcc5f2a1b1f3cbb4ea403d41f271c63',
                method = 'GET',
                response_filter= lambda r: json.loads(r.text),
                log_response=True
                )

                transform_load_weather_data = PythonOperator(
                task_id= 'transform_load_weather_data',
                pyttransform_load_weather_datahon_callable=transform_load_data
                )
                





                create_table_1 >> truncate_table >> uploadS3_to_postgres
                create_table_2 >> is_weather_api_ready >> extract_weather_data >> transform_load_weather_data
        start_pipeline >> group_A
