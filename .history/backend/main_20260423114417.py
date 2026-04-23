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

# --- NEW: YEARLY AGGREGATION ENDPOINT ---
@app.get("/api/yearly")
async def get_yearly_summary():
    # Group readings strictly by Year (YYYY)
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
    
    yearly_data = []
    for row in rows:
        kwh = round(row[1], 2)
        yearly_data.append({
            "year": row[0],
            "kwh": kwh,
            "cost": round(kwh * PRICE_PER_KWH, 2)
        })
        
    return {"status": "success", "data": yearly_data}

# --- UPGRADED: AI SUPPORT CHAT ENDPOINT (DATA-DRIVEN) ---
class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def ai_support_chat(chat: ChatMessage):
    msg = chat.message.lower()
    response = ""
    
    try:
        # 1. REAL-TIME STATUS CHECK
        if "status" in msg or "current" in msg or "now" in msg:
            cursor.execute('SELECT power_kw, timestamp FROM energy_history ORDER BY timestamp DESC LIMIT 1')
            row = cursor.fetchone()
            if row:
                power = round(row[0], 2)
                response = f"Monitoring live telemetry... Your current household draw is {power} kW. The ESP32 node is actively transmitting data."
            else:
                response = "I cannot see any live data currently. Please check the ESP32 hardware connection."

        # 2. SPIKE & ANOMALY DETECTION
        elif "spike" in msg or "unusual" in msg or "high" in msg or "warning" in msg:
            # Get the 24-hour average
            cursor.execute('SELECT AVG(power_kw) FROM energy_history WHERE timestamp >= datetime("now", "-1 day")')
            avg_row = cursor.fetchone()
            # Get the latest reading
            cursor.execute('SELECT power_kw FROM energy_history ORDER BY timestamp DESC LIMIT 1')
            curr_row = cursor.fetchone()

            if avg_row and curr_row and avg_row[0]:
                avg_kw = round(avg_row[0], 2)
                curr_kw = round(curr_row[0], 2)
                
                # Math logic: If current draw is 50% higher than average, flag a spike
                if curr_kw > (avg_kw * 1.5):
                    response = f"⚠️ ANOMALY DETECTED: The current draw is {curr_kw} kW, which is dangerously higher than your 24-hour average of {avg_kw} kW. Please check heavy load appliances immediately."
                elif curr_kw < (avg_kw * 0.2):
                    response = f"⚠️ UNDER-USAGE DETECTED: The current draw is only {curr_kw} kW compared to an average of {avg_kw} kW. This indicates a potential localized blackout or disconnected main line."
                else:
                    response = f"System stable. No unusual spikes detected. Your current draw ({curr_kw} kW) is operating within your normal baseline ({avg_kw} kW)."
            else:
                response = "I do not have enough historical telemetry to establish a baseline for anomaly detection yet."

        # 3. FINANCIAL & USAGE CALCULATION
        elif "cost" in msg or "bill" in msg or "spent" in msg or "today" in msg:
            # Calculate today's total kWh
            cursor.execute('''
                SELECT SUM(power_kw) / 12.0 
                FROM energy_history 
                WHERE date(timestamp) = date('now')
            ''')
            row = cursor.fetchone()
            if row and row[0]:
                kwh = round(row[0], 2)
                cost = round(kwh * PRICE_PER_KWH, 2)
                response = f"So far today, the household has consumed {kwh} kWh of energy. At the current grid rate, your estimated daily operating cost is currently ₦{cost}."
            else:
                response = "I couldn't calculate today's consumption. Waiting for sufficient ESP32 telemetry."

        # 4. DEFAULT HELP MENU
        elif "hello" in msg or "hi" in msg or "help" in msg:
            response = "Hello! I am Nazarine AI, your automated grid assistant. You can ask me to check the **current status**, scan for **unusual spikes**, or calculate **today's cost**."
            
        # 5. FALLBACK
        else:
            response = f"I received your query regarding '{chat.message}'. I am currently trained to analyze telemetry for 'status', 'spikes', and 'costs'. Could you rephrase your request?"

    except Exception as e:
        print(f"AI Engine Error: {e}")
        response = "I encountered an internal database error while trying to analyze the grid telemetry."
        
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