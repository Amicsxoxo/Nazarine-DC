from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import sqlite3  # <-- NEW: The Database Library

app = FastAPI(title="Nazarine DC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW: DATABASE SETUP ---
# This creates a file called 'Nazarine_memory.db' in your folder
conn = sqlite3.connect('Nazarine_memory.db', check_same_thread=False)
cursor = conn.cursor()

# Create a table to store the telemetry history
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
# ---------------------------

class EnergyReading(BaseModel):
    device_id: str
    voltage: float
    current: float
    power_kw: float

active_dashboards = []

@app.post("/api/telemetry")
async def receive_telemetry(reading: EnergyReading):
    # --- NEW: SAVE TO DATABASE ---
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw)
        VALUES (?, ?, ?, ?)
    ''', (reading.device_id, reading.voltage, reading.current, reading.power_kw))
    conn.commit()
    # -----------------------------
    
    print(f"⚡ Saved to DB & Broadcasting: {reading.power_kw} kW")
    
    dead_connections = []
    for ws in active_dashboards:
        try:
            await ws.send_text(json.dumps(reading.dict()))
        except:
            dead_connections.append(ws)
            
    for ws in dead_connections:
        active_dashboards.remove(ws)

    return {"status": "success", "message": "Telemetry saved and broadcasted"}

@app.websocket("/ws/realtime")
async def realtime_feed(websocket: WebSocket):
    await websocket.accept()
    active_dashboards.append(websocket)
    print("🟢 Dashboard connected to real-time feed")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_dashboards.remove(websocket)
        print("🔴 Dashboard disconnected")

