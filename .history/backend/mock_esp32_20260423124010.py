import requests
import time
import random

URL = "http://127.0.0.1:8000/api/telemetry"

print("🚀 Starting Nazarine ESP32 Simulator (Realistic Residential Mode)...")
print(f"Targeting backend at: {URL}")
print("-" * 30)

while True:
    # Standard Nigerian/UK Grid Voltage
    voltage = random.uniform(225.0, 235.0)
    
    # REALISTIC CURRENT: 1.0 to 4.5 Amps (roughly 230W to 1,035W)
    current = random.uniform(1.0, 4.5) 
    
    power_kw = (voltage * current) / 1000

    # Occasional AC / Pump Spike Simulator (10% chance to jump to 2.5kW)
    if random.random() > 0.90:
        power_kw += random.uniform(1.0, 1.5)

    payload = {
        "device_id": "main_panel_esp32",
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power_kw": round(power_kw, 2)
    }

    try:
        print(f"Attempting to send {payload['power_kw']} kW...")
        response = requests.post(URL, json=payload, timeout=5) 
        
        if response.status_code == 200:
            print(f"✅ Success! Server replied: {response.json()['status']}")
        else:
            print(f"❌ Server rejected the data. Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"🛑 CRITICAL ERROR: Could not connect to {URL}. Is FastAPI running?")

    # Send data every 2 seconds
    time.sleep(2)