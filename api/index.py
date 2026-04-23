from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import os

app = FastAPI(title="Nazarine Synthesis API")

# Allow your frontend (wherever it is hosted) to talk to this Vercel API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# VERCEL FIX: Route the database to the temporary writable directory
DB_PATH = '/tmp/nazarine_memory.db'
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS energy_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        voltage REAL,
        current REAL,
        power_kw REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

class EnergyReading(BaseModel):
    device_id: str
    voltage: float
    current: float
    power_kw: float

class ChatMessage(BaseModel):
    message: str

# Globals
active_dashboards = []
last_reading_time = None
daily_kwh = 0.0
PRICE_PER_KWH = 240.0  
CARBON_PER_KWH = 0.4   
ai_forecaster = None  

# --- TELEMETRY ENDPOINT ---
@app.post("/api/telemetry")
async def receive_telemetry(reading: EnergyReading):
    global last_reading_time, daily_kwh
    
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw)
        VALUES (?, ?, ?, ?)
    ''', (reading.device_id, reading.voltage, reading.current, reading.power_kw))
    conn.commit()
    
    now = datetime.now()
    if last_reading_time is not None:
        delta_hours = (now - last_reading_time).total_seconds() / 3600.0
        daily_kwh += reading.power_kw * delta_hours
    
    last_reading_time = now
    return {"status": "success", "message": "Telemetry saved to Vercel /tmp DB"}

# --- AGGREGATION ENDPOINTS ---
@app.get("/api/hourly")
async def get_hourly_summary():
    cursor.execute('''
        SELECT strftime('%H', datetime(timestamp, 'localtime')) as hour_string, AVG(power_kw) as avg_power
        FROM energy_history GROUP BY strftime('%Y-%m-%d %H', datetime(timestamp, 'localtime'))
        ORDER BY timestamp DESC LIMIT 24
    ''')
    return {"status": "success", "data": [{"hour": f"{row[0]}:00", "kwh": round(row[1], 2), "cost": round(row[1] * PRICE_PER_KWH, 2)} for row in cursor.fetchall()]}

@app.get("/api/weekly")
async def get_weekly_summary():
    cursor.execute('''
        SELECT strftime('%w', datetime(timestamp, 'localtime')) as day_index, date(timestamp, 'localtime') as exact_date, SUM(power_kw) / 12.0 as daily_kwh
        FROM energy_history GROUP BY date(timestamp, 'localtime') ORDER BY exact_date DESC LIMIT 14
    ''')
    return {"status": "success", "data": [{"day_index": int(row[0]), "date": row[1], "kwh": round(row[2], 2)} for row in cursor.fetchall()]}

@app.get("/api/monthly")
async def get_monthly_summary():
    cursor.execute('''
        SELECT strftime('%Y-%m', datetime(timestamp, 'localtime')) as month_string, SUM(power_kw) / 12.0 as monthly_kwh
        FROM energy_history GROUP BY strftime('%Y-%m', datetime(timestamp, 'localtime')) ORDER BY month_string DESC LIMIT 7
    ''')
    return {"status": "success", "data": [{"month": row[0], "kwh": round(row[1], 2), "cost": round(row[1] * PRICE_PER_KWH, 2)} for row in cursor.fetchall()]}

@app.get("/api/yearly")
async def get_yearly_summary():
    cursor.execute('''
        SELECT strftime('%Y', datetime(timestamp, 'localtime')) as year_string, SUM(power_kw) / 12.0 as yearly_kwh
        FROM energy_history GROUP BY strftime('%Y', datetime(timestamp, 'localtime')) ORDER BY year_string DESC LIMIT 5
    ''')
    return {"status": "success", "data": [{"year": row[0], "kwh": round(row[1], 2), "cost": round(row[1] * PRICE_PER_KWH, 2)} for row in cursor.fetchall()]}

# --- AI & ML ENDPOINTS ---
@app.post("/api/chat")
async def ai_support_chat(chat: ChatMessage):
    msg = chat.message.lower()
    response = "I am processing your query. Note: Hosted on Vercel, history may be limited."
    if "status" in msg or "current" in msg:
        cursor.execute('SELECT power_kw FROM energy_history ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        response = f"Your current draw is {round(row[0], 2)} kW." if row else "No live data."
    return {"status": "success", "response": response}

@app.get("/api/train")
def train_predictive_model():
    global ai_forecaster
    df = pd.read_sql_query('SELECT timestamp, power_kw FROM energy_history', conn)
    if len(df) < 100: return {"status": "error", "message": "Not enough data"}
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    
    hourly_df = df.groupby([df['timestamp'].dt.date, 'hour', 'dayofweek', 'month'])['power_kw'].mean().reset_index()
    X, y = hourly_df[['hour', 'dayofweek', 'month']], hourly_df['power_kw']
    
    ai_forecaster = RandomForestRegressor(n_estimators=50, random_state=42)
    ai_forecaster.fit(X, y)
    return {"status": "success", "message": "ML Engine trained."}

@app.get("/api/forecast")
def get_24h_forecast():
    global ai_forecaster
    if ai_forecaster is None: train_predictive_model()
    
    predictions = []
    now = datetime.now()
    for i in range(24):
        future_time = now + timedelta(hours=i)
        features = pd.DataFrame({'hour': [future_time.hour], 'dayofweek': [future_time.weekday()], 'month': [future_time.month]})
        pred_kw = ai_forecaster.predict(features)[0] if ai_forecaster else 0
        predictions.append({"time": future_time.strftime("%H:00"), "predicted_kw": round(pred_kw, 2)})
    return {"status": "success", "data": predictions}

# WebSockets will likely fail on Vercel, but kept for completeness
@app.websocket("/ws/realtime")
async def realtime_feed(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.receive_text()