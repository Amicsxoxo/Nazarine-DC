from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import sqlite3
from datetime import datetime # <-- NEW: We need this to calculate time differences

app = FastAPI(title="Nazarine DC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = sqlite3.connect('Nazarine_memory.db', check_same_thread=False)
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
# --- NEW: HOURLY AGGREGATION ENDPOINT ---
@app.get("/api/hourly")
async def get_hourly_summary():
    # Group readings by hour and calculate the average power used
    cursor.execute('''
        SELECT 
            strftime('%H', timestamp) as hour_string,
            AVG(power_kw) as avg_power
        FROM energy_history 
        GROUP BY strftime('%Y-%m-%d %H', timestamp)
        ORDER BY timestamp DESC
        LIMIT 24
    ''')
    rows = cursor.fetchall()
    
    hourly_data = []
    for row in rows:
        kwh_estimate = round(row[1], 2) # Average kW over an hour = kWh
        cost_estimate = round(kwh_estimate * PRICE_PER_KWH, 2)
        
        hourly_data.append({
            "hour": f"{row[0]}:00",
            "kwh": kwh_estimate,
            "cost": cost_estimate
        })
        
    return {"status": "success", "data": hourly_data}
@app.websocket("/ws/realtime")
async def realtime_feed(websocket: WebSocket):
    await websocket.accept()
    active_dashboards.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_dashboards.remove(websocket)