from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import subprocess
import threading
import os

app = FastAPI(title="Nazarine Synthesis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (HTML dashboards)
app.mount("/static", StaticFiles(directory="."), name="static")

# Database path - use relative path for Vercel compatibility
DB_PATH = os.path.join(os.path.dirname(__file__), 'nazarine_memory.db')

def get_db_connection():
    """Get database connection with proper path handling."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# Initialize database on startup
def init_database():
    """Initialize database schema if not exists."""
    conn = get_db_connection()
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
    conn.close()

# Global variables
ai_forecaster = None
last_reading_time = None
daily_kwh = 0.0
PRICE_PER_KWH = 240.0
CARBON_PER_KWH = 0.4
active_dashboards = []

class EnergyReading(BaseModel):
    device_id: str
    voltage: float
    current: float
    power_kw: float

class ChatMessage(BaseModel):
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("🔌 Nazarine DC - Smart Energy Management System Starting...")
    init_database()
    print("✅ Database initialized!")

@app.get("/")
async def root():
    """Serve the main dashboard."""
    return FileResponse('energy_dashboard.html')

@app.get("/dashboard")
async def dashboard():
    """Serve the main dashboard."""
    return FileResponse('energy_dashboard.html')

@app.get("/history")
async def history_page():
    """Serve energy usage history page."""
    return FileResponse('energy_usage_history.html')

@app.get("/hourly")
async def hourly_page():
    """Serve hourly energy usage page."""
    return FileResponse('hourly_energy_usage.html')

@app.get("/weekly")
async def weekly_page():
    """Serve weekly energy trends page."""
    return FileResponse('weekly_energy_trends.html')

@app.get("/ai-support")
async def ai_support_page():
    """Serve AI support center page."""
    return FileResponse('ai_support_center.html')

@app.get("/account-settings")
async def account_settings_page():
    """Serve account settings page."""
    return FileResponse('account_settings.html')

@app.post("/api/telemetry")
async def receive_telemetry(reading: EnergyReading):
    global last_reading_time, daily_kwh
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save to Database
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw)
        VALUES (?, ?, ?, ?)
    ''', (reading.device_id, reading.voltage, reading.current, reading.power_kw))
    conn.commit()
    conn.close()
    
    # Integrate Power over Time (kW -> kWh)
    now = datetime.now()
    if last_reading_time is not None:
        delta_hours = (now - last_reading_time).total_seconds() / 3600.0
        daily_kwh += reading.power_kw * delta_hours
    
    last_reading_time = now
    
    # Calculate Derived Metrics
    daily_cost = daily_kwh * PRICE_PER_KWH
    carbon_offset = daily_kwh * CARBON_PER_KWH
    
    print(f"⚡ {reading.power_kw} kW | Total: {daily_kwh:.4f} kWh | Cost: ₦{daily_cost:.2f}")
    
    # Package and Broadcast
    payload = reading.dict()
    payload["daily_kwh"] = round(daily_kwh, 4)
    payload["daily_cost"] = round(daily_cost, 2)
    payload["carbon_offset"] = round(carbon_offset, 2)

    dead_connections = []
    for ws in active_dashboards:
        try:
            await ws.send_text(json.dumps(payload))
        except:
            dead_connections.append(ws)
            
    for ws in dead_connections:
        active_dashboards.remove(ws)

    return {"status": "success", "message": "Telemetry processed"}

@app.get("/api/history")
async def get_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM energy_history ORDER BY timestamp DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "device_id": row[1],
            "voltage": row[2],
            "current": row[3],
            "power_kw": row[4],
            "timestamp": row[5]
        })
        
    return {"status": "success", "data": history}

@app.get("/api/hourly")
async def get_hourly_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            strftime('%H', datetime(timestamp, 'localtime')) as hour_string,
            AVG(power_kw) as avg_power
        FROM energy_history 
        GROUP BY strftime('%Y-%m-%d %H', datetime(timestamp, 'localtime'))
        ORDER BY timestamp DESC
        LIMIT 24
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    hourly_data = []
    for row in rows:
        kwh_estimate = round(row[1], 2) 
        cost_estimate = round(kwh_estimate * PRICE_PER_KWH, 2)
        
        hourly_data.append({
            "hour": f"{row[0]}:00",
            "kwh": kwh_estimate,
            "cost": cost_estimate
        })
        
    return {"status": "success", "data": hourly_data}

@app.get("/api/weekly")
async def get_weekly_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            strftime('%w', datetime(timestamp, 'localtime')) as day_index,
            date(timestamp, 'localtime') as exact_date,
            SUM(power_kw) / 12.0 as daily_kwh
        FROM energy_history 
        GROUP BY date(timestamp, 'localtime')
        ORDER BY exact_date DESC
        LIMIT 14
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    weekly_data = []
    for row in rows:
        weekly_data.append({
            "day_index": int(row[0]),
            "date": row[1],
            "kwh": round(row[2], 2)
        })
        
    return {"status": "success", "data": weekly_data}

@app.get("/api/monthly")
async def get_monthly_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            strftime('%Y-%m', datetime(timestamp, 'localtime')) as month_string,
            SUM(power_kw) / 12.0 as monthly_kwh
        FROM energy_history 
        GROUP BY strftime('%Y-%m', datetime(timestamp, 'localtime'))
        ORDER BY month_string DESC
        LIMIT 7
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    monthly_data = []
    for row in rows:
        kwh = round(row[1], 2)
        monthly_data.append({
            "month": row[0],
            "kwh": kwh,
            "cost": round(kwh * PRICE_PER_KWH, 2)
        })
        
    return {"status": "success", "data": monthly_data}

@app.get("/api/yearly")
async def get_yearly_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            strftime('%Y', datetime(timestamp, 'localtime')) as year_string,
            SUM(power_kw) / 12.0 as yearly_kwh
        FROM energy_history 
        GROUP BY strftime('%Y', datetime(timestamp, 'localtime'))
        ORDER BY year_string DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    yearly_data = []
    for row in rows:
        kwh = round(row[1], 2)
        yearly_data.append({
            "year": row[0],
            "kwh": kwh,
            "cost": round(kwh * PRICE_PER_KWH, 2)
        })
        
    return {"status": "success", "data": yearly_data}

@app.get("/api/recommendation")
async def get_best_time():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            strftime('%H:00', datetime(timestamp, 'localtime')) as hour,
            SUM(power_kw) / 12.0 as kwh
        FROM energy_history 
        WHERE timestamp >= datetime('now', '-1 day')
        GROUP BY hour
        ORDER BY hour ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    if len(rows) < 3:
        return {"status": "error", "message": "Not enough data for a recommendation."}
        
    best_window = None
    lowest_avg = float('inf')
    
    for i in range(len(rows) - 2):
        window_avg = (rows[i][1] + rows[i+1][1] + rows[i+2][1]) / 3
        if window_avg < lowest_avg:
            lowest_avg = window_avg
            best_window = f"{rows[i][0]} - {str(int(rows[i+2][0].split(':')[0]) + 1).zfill(2)}:00"
            
    return {
        "status": "success", 
        "best_window": best_window, 
        "average_kwh": round(lowest_avg, 2),
        "cost_estimate": round(lowest_avg * PRICE_PER_KWH, 2)
    }

@app.post("/api/chat")
async def ai_support_chat(chat: ChatMessage):
    msg = chat.message.lower()
    response = ""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if "status" in msg or "current" in msg or "now" in msg:
            cursor.execute('SELECT power_kw, timestamp FROM energy_history ORDER BY timestamp DESC LIMIT 1')
            row = cursor.fetchone()
            if row:
                power = round(row[0], 2)
                response = f"Monitoring live telemetry... Your current household draw is {power} kW."
            else:
                response = "I cannot see any live data currently."

        elif "spike" in msg or "unusual" in msg or "high" in msg:
            cursor.execute('SELECT AVG(power_kw) FROM energy_history WHERE timestamp >= datetime("now", "-1 day")')
            avg_row = cursor.fetchone()
            cursor.execute('SELECT power_kw FROM energy_history ORDER BY timestamp DESC LIMIT 1')
            curr_row = cursor.fetchone()

            if avg_row and curr_row and avg_row[0]:
                avg_kw = round(avg_row[0], 2)
                curr_kw = round(curr_row[0], 2)
                
                if curr_kw > (avg_kw * 1.5):
                    response = f"⚠️ ANOMALY DETECTED: Current draw is {curr_kw} kW vs average {avg_kw} kW."
                elif curr_kw < (avg_kw * 0.2):
                    response = f"⚠️ UNDER-USAGE: Current draw is {curr_kw} kW vs average {avg_kw} kW."
                else:
                    response = f"System stable. Current: {curr_kw} kW, Average: {avg_kw} kW."
            else:
                response = "Not enough data for anomaly detection."

        elif "cost" in msg or "bill" in msg or "today" in msg:
            cursor.execute('''
                SELECT SUM(power_kw) / 12.0 
                FROM energy_history 
                WHERE date(timestamp) = date('now')
            ''')
            row = cursor.fetchone()
            if row and row[0]:
                kwh = round(row[0], 2)
                cost = round(kwh * PRICE_PER_KWH, 2)
                response = f"Today's consumption: {kwh} kWh. Estimated cost: ₦{cost}."
            else:
                response = "No data for today's calculation."

        elif "hello" in msg or "hi" in msg or "help" in msg:
            response = "Hello! I am Nazarine AI. Ask me about **status**, **spikes**, or **costs**."
            
        else:
            response = f"Query received: '{chat.message}'. Try asking about 'status', 'spikes', or 'costs'."

    except Exception as e:
        print(f"AI Engine Error: {e}")
        response = "Internal database error."
    finally:
        conn.close()
        
    return {"status": "success", "response": response}

@app.get("/api/train")
def train_predictive_model():
    global ai_forecaster
    print("🧠 Booting up Nazarine ML Engine...")

    conn = get_db_connection()
    query = 'SELECT timestamp, power_kw FROM energy_history'
    df = pd.read_sql_query(query, conn)
    conn.close()

    if len(df) < 100:
        return {"status": "error", "message": "Not enough data to train ML."}

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['dayofweek'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month

    hourly_df = df.groupby([df['timestamp'].dt.date, 'hour', 'dayofweek', 'month'])['power_kw'].mean().reset_index()

    X = hourly_df[['hour', 'dayofweek', 'month']]
    y = hourly_df['power_kw']

    ai_forecaster = RandomForestRegressor(n_estimators=50, random_state=42)
    ai_forecaster.fit(X, y)

    return {"status": "success", "message": "Nazarine ML Engine trained successfully."}

@app.get("/api/forecast")
def get_24h_forecast():
    global ai_forecaster

    if ai_forecaster is None:
        train_result = train_predictive_model()
        if train_result.get("status") == "error":
            return train_result

    predictions = []
    now = datetime.now()

    for i in range(24):
        future_time = now + timedelta(hours=i)

        features = pd.DataFrame({
            'hour': [future_time.hour],
            'dayofweek': [future_time.weekday()],
            'month': [future_time.month]
        })

        predicted_kw = ai_forecaster.predict(features)[0]

        predictions.append({
            "time": future_time.strftime("%H:00"),
            "predicted_kw": round(predicted_kw, 2)
        })

    return {"status": "success", "data": predictions}

@app.websocket("/ws/realtime")
async def realtime_feed(websocket: WebSocket):
    await websocket.accept()
    active_dashboards.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_dashboards.remove(websocket)
