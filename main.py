import requests
import os
import json
from google.cloud import bigquery, pubsub_v1
from functions_framework import http, cloud_event
from datetime import datetime

# Load API Key from environment variables
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT = "52.2298"  # Latitude for Warsaw
LON = "21.0122"  # Longitude for Warsaw
BQ_TABLE = "datatestingproject2025.warsaw.weather_data"  
TOPIC = 'projects/datatestingproject2025/topics/weather-scheduler'



@http
def get_weather_data(_):
    """Fetch weather data from OpenWeather API"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"

    response = requests.get(url)

    
    if response.status_code == 200:
        client = pubsub_v1.PublisherClient()
        client.publish(TOPIC, response.text.encode('utf-8'))
        return "Success: weather data fetched and sent to pub/sub", 200
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def insert_into_bigquery(weather_data):
    """Insert weather data into BigQuery"""
    client = bigquery.Client()

    # Extract relevant data based on the new API response format
    timestamp = datetime.utcfromtimestamp(weather_data["dt"]).strftime('%Y-%m-%d %H:%M')
    temp = weather_data["main"]["temp"]
    humidity = weather_data["main"]["humidity"]
    pressure = weather_data["main"]["pressure"]
    weather_desc = weather_data["weather"][0]["description"]

    rows_to_insert = [
        {
            "timestamp": timestamp,
            "temperature": temp,
            "humidity": humidity,
            "pressure": pressure,
            "weather_description": weather_desc
        }
    ]

    table = client.get_table(BQ_TABLE)
    errors = client.insert_rows_json(table, rows_to_insert)

    if errors:
        raise Exception(f"BigQuery Insertion Errors: {errors}")

@cloud_event
def send_weather_data(event):
    """Triggered by Pub/Sub messaget"""
    try:
        weather_data = event.data['message']['data'].decode('utf-8')
        insert_into_bigquery(json.loads(weather_data))
        return "Success: weather data written to BigQuery successfully", 200
    except Exception as e:
        return str(e), 500
