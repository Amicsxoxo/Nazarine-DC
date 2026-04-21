from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI(title="Nazarine DC API")

# Allow the frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Define the data structure we expect from the ESP32
class EnergyReading(BaseModel):
    device_id: str
    voltage: float
    current: float
    power_kw: float

# Store active frontend dashboard connections
active_dashboards = []

# 2. The Ingestion Endpoint (ESP32 sends data here)
@app.post("/api/telemetry")
async def receive_telemetry(reading: EnergyReading):
    # Here is where we will eventually save data to a database
    print(f"⚡ Incoming Data: {reading.power_kw} kW from {reading.device_id}")
    
    # Broadcast the fresh data to any open frontend dashboards
    dead_connections = []
    for ws in active_dashboards:
        try:
            await ws.send_text(json.dumps(reading.dict()))
        except:
            dead_connections.append(ws)
            
    # Clean up disconnected dashboards
    for ws in dead_connections:
        active_dashboards.remove(ws)

    return {"status": "success", "message": "Telemetry processed"}

# 3. The Real-Time WebSocket (Frontend listens here)
@app.websocket("/ws/realtime")
async def realtime_feed(websocket: WebSocket):
    await websocket.accept()
    active_dashboards.append(websocket)
    print("🟢 Dashboard connected to real-time feed")
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_dashboards.remove(websocket)
        print("🔴 Dashboard disconnected")