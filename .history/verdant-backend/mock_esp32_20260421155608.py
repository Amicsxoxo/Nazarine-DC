import requests
import time
import random

# The endpoint of your FastAPI backend
URL = "http://127.0.0.1:8000/api/telemetry"

print("🚀 Starting Nazarine ESP32 Simulator...")
print("Press Ctrl+C to stop.")
print("-" * 30)

while True:
    # Simulate realistic voltage and current fluctuations
    voltage = random.uniform(225.0, 235.0)  # Typical 230V mains
    current = random.uniform(5.0, 25.0)     # Fluctuating amp draw
    
    # Calculate Power (P = V * I) and convert Watts to Kilowatts
    power_kw = (voltage * current) / 1000

    # The exact JSON structure your backend expects
    payload = {
        "device_id": "main_panel_esp32",
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power_kw": round(power_kw, 2)
    }

    try:
        # Blast the data to the server via HTTP POST
        response = requests.post(URL, json=payload)
        print(f"📡 Sent: {payload['power_kw']} kW | Server Response: {response.json()['status']}")
    except requests.exceptions.ConnectionError:
        print("⚠️ Connection failed. Is your FastAPI server running?")

    # Wait 3 seconds before sending the next reading (like the ESP32 loop delay)
    time.sleep(3)