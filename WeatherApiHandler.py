import requests
import datetime
import os
import json
import sqlite3
import math
import numpy as np
from dotenv import load_dotenv
load_dotenv()

##Define as configurações da API
   ##Estudar fazer um .env com a chave da API visando escalonamento e segurança.
API_KEY = os.getenv('WEATHER_API_KEY','abee1e9bb3c878b655410c5ac7564ecb')
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
CALLS_LOG = "api_calls.json"
DAILY_LIMIT = 950
DB_PATH = 'weather_data.db'

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20)  # Added timeout parameter
        conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key support
        return conn
    except sqlite3.Error as e:
        print(f"Erro em conectar com a database: {e}")
        return None

# Initialize database (create table if not exists)
def init_database():
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        
        cursor = conn.cursor()
        
        # Check if table exists before creating it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weather'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE weather (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                temperature REAL,
                feels_like REAL,
                humidity INTEGER,
                rain REAL,
                description TEXT,
                timestamp TEXT
            )
            ''')
            conn.commit()
            print("Database inicializada e tabela criada.")
        
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Erro de inicialização de database: {e}")
        return False

#Toda arquitetura do arquivo JSON é para garantir que não ocorram chamadas demais na API, visando evitar o pagamento de taxas extras.
def load_api_log():
    if not os.path.exists(CALLS_LOG):
        return {}
    with open(CALLS_LOG, 'r') as f:
        return json.load(f)

def save_api_log(log):
    with open(CALLS_LOG, 'w') as f:
        json.dump(log, f)

def can_make_api_call():
    log = load_api_log()
    today = datetime.date.today().isoformat()

    if today not in log:
        log[today] = 0

    if log[today] >= DAILY_LIMIT:
        return False, log
    else:
        log[today] += 1
        save_api_log(log)
        return True, log

# Salvar no banco
def save_weather_to_db(weather_data):
    try:
        conn = get_db_connection()
        if conn is None:
            print("Falha na criação de database: erro de conexão.")
            return False
        
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO weather (city, temperature, feels_like, humidity, rain, description, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            weather_data['city'],
            weather_data['temp'],
            weather_data['feels_like'],
            weather_data['humidity'],
            weather_data['rain'],
            weather_data['description'],
            now
        ))
        conn.commit()
        print(f"Dados de clima para {weather_data['city']} salvo na database")
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Erro na hora de salvar os dados causado por: {e}")
        return False

# Pega o clima
def get_weather(city_name):
    allowed, log = can_make_api_call()
    if not allowed:
        print("⚠️ Limite de requests atingido")
        return

    params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric',
        'lang': 'pt_br'
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()
        city = data['name']
        temp = data['main']['temp']
        feels = data['main']['feels_like']
        humidity = data['main']['humidity']
        desc = data['weather'][0]['description']
        rain = data.get('rain', {}).get('1h', 0)
        ## rain  = data['main']['rain'] // entrada obsoleta. O erro consiste na busca pela variável rain dentro de main, quando na verdade ela está dentro de outra variável no JSON.
        ##Preciso dimensionar o ponto de orvalho
        ##preciso traduzir a desc = data
        if rain >= 50:
            rain_mood = "Chuva forte, Bianca está feliz."
        elif rain >= 20:
            rain_mood = "Chuva moderada, poderia estar melhor."
        else:
            rain_mood = "Chuva leve, Bianca está triste."

        print(f"\n🌤️  O clima em {city} está:\n")
        print(f"Temperatura: {temp}°C (Sensação térmica de {feels}°C)")
        print(f"Humidade relativa do ar: {humidity}%")
        ## print(f"Ponto de orvalho: {dew:.2f}°C")
        print(f"Descrição: {desc.capitalize()}")
        print(f"Chuva?: {rain_mood}")
        print(f"API requests hoje: {log[datetime.date.today().isoformat()]}/{DAILY_LIMIT}")

        # Salvar no banco
        weather_data = {
            'city': city,
            'temp': temp,
            'feels_like': feels,
            'humidity': humidity,
            'rain': rain,
            'description': desc
        }
        save_weather_to_db(weather_data)

    except requests.exceptions.RequestException as e:
        print("❌ Erro de rede:", e)
    except KeyError:
        print("❌ Cidade não encontrada ou erro no JSON.")
    except Exception as e:
        print("❌ Erro inesperado:", e)

# bota pa fude
def main():
    if not init_database():
        print("Falha em inicializar o banco de dados.")
        return
    
    try:
        city = input("Me diga uma cidade: ")
        get_weather(city)
    except Exception as e:
        print(f"Erro na execução do programa: {e}")
        import traceback
        traceback.print_exc()

# entrada do programa
if __name__ == "__main__":
    main()