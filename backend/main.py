from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import sqlite3
from datetime import datetime # <-- NEW: We need this to calculate time differences

app = FastAPI(title="Nazarine Synthesis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = sqlite3.connect('nazarine_memory.db', check_same_thread=False)
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

active_dashboards = []

# --- NEW: INTEGRATION ENGINE VARIABLES ---
last_reading_time = None
daily_kwh = 0.0
PRICE_PER_KWH = 240.0  # Base grid rate (₦240 per kWh)
CARBON_PER_KWH = 0.4   # Estimated kg of CO2 offset per renewable kWh

@app.post("/api/telemetry")
async def receive_telemetry(reading: EnergyReading):
    global last_reading_time, daily_kwh
    
    # 1. Save to Database
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw)
        VALUES (?, ?, ?, ?)
    ''', (reading.device_id, reading.voltage, reading.current, reading.power_kw))
    conn.commit()
    
    # 2. Integrate Power over Time (kW -> kWh)
    now = datetime.now()
    if last_reading_time is not None:
        # Calculate time passed since the last reading in hours
        delta_hours = (now - last_reading_time).total_seconds() / 3600.0
        # Add the area under the curve (Power * Time) to the daily total
        daily_kwh += reading.power_kw * delta_hours
    
    last_reading_time = now
    
    # 3. Calculate Derived Metrics
    daily_cost = daily_kwh * PRICE_PER_KWH
    carbon_offset = daily_kwh * CARBON_PER_KWH
    
    print(f"⚡ {reading.power_kw} kW | Total: {daily_kwh:.4f} kWh | Cost: ${daily_cost:.2f}")
    
    # 4. Package and Broadcast Everything
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
    cursor.execute("SELECT * FROM energy_history ORDER BY timestamp DESC LIMIT 10")
    rows = cursor.fetchall()
    
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
# --- UPDATED: HOURLY AGGREGATION ENDPOINT ---
@app.get("/api/hourly")
async def get_hourly_summary():
    # We added 'localtime' to both strftime functions to fix the timezone offset
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

# --- NEW: WEEKLY AGGREGATION ENDPOINT ---
@app.get("/api/weekly")
async def get_weekly_summary():
    # Group readings by day, calculating the total daily kWh
    # (Dividing by 12 because we simulate 12 readings an hour)
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
    
    weekly_data = []
    for row in rows:
        weekly_data.append({
            "day_index": int(row[0]), # 0=Sun, 1=Mon, ..., 6=Sat
            "date": row[1],
            "kwh": round(row[2], 2)
        })
        
    return {"status": "success", "data": weekly_data}

# --- NEW: MONTHLY AGGREGATION ENDPOINT ---
@app.get("/api/monthly")
async def get_monthly_summary():
    # Group readings by Month (YYYY-MM)
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
    
    monthly_data = []
    for row in rows:
        kwh = round(row[1], 2)
        monthly_data.append({
            "month": row[0], # e.g., "2024-07"
            "kwh": kwh,
            "cost": round(kwh * PRICE_PER_KWH, 2)
        })
        
    return {"status": "success", "data": monthly_data}

# --- NEW: AI SUPPORT CHAT ENDPOINT ---
class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def ai_support_chat(chat: ChatMessage):
    msg = chat.message.lower()
    
    # Simulated ML Keyword Analysis (Expert System Rules)
    if "hvac" in msg or "cooling" in msg or "ac" in msg:
        response = "I'm analyzing the HVAC telemetry. The current draw is 3.5kW, which is 15% higher than the baseline. I recommend checking the compressor's mechanical resistance."
    elif "cost" in msg or "price" in msg or "bill" in msg:
        response = "Currently, the main grid is in Tier 3 pricing (₦0.24/kWh). I suggest shifting non-essential loads, such as the EV Charger, to off-peak hours after 20:00."
    elif "solar" in msg or "battery" in msg:
        response = "Solar generation is currently at 2.8kW. Battery storage is at 84%. The system is fully optimized for current weather conditions."
    elif "hello" in msg or "hi" in msg:
        response = "Hello! Nazarine AI is online. How can I assist you with your grid telemetry today?"
    else:
        # Fallback response for unrecognized queries
        response = f"I've processed your query regarding '{chat.message}'. Based on current Nazarine DC models, all grid parameters are operating within normal tolerances. Would you like me to run a deep-level diagnostic?"
        
    return {"status": "success", "response": response}

@app.websocket("/ws/realtime")
async def realtime_feed(websocket: WebSocket):
    await websocket.accept()
    active_dashboards.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_dashboards.remove(websocket)