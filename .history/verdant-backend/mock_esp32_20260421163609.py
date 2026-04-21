import requests
import time
import random

URL = "http://127.0.0.1:8000/api/telemetry"

print("🚀 Starting Nazarine ESP32 Simulator...")
print(f"Targeting backend at: {URL}")
print("-" * 30)

while True:
    voltage = random.uniform(225.0, 235.0)
    current = random.uniform(5.0, 25.0)
    power_kw = (voltage * current) / 1000

    payload = {
        "device_id": "main_panel_esp32",
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power_kw": round(power_kw, 2)
    }

    try:
        print(f"Attempting to send {payload['power_kw']} kW...")
        # Timeout added so it doesn't hang forever if the server is missing
        response = requests.post(URL, json=payload, timeout=5) 
        
        if response.status_code == 200:
            print(f"✅ Success! Server replied: {response.json()['status']}")
        else:
            print(f"❌ Server rejected the data. Status Code: {response.status_code}")
            print(f"Reason: {response.text}")
            
    except Exception as e:
        print(f"🛑 CRITICAL ERROR sending data: {e}")

    time.sleep(3)