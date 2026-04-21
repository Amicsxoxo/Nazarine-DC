import sqlite3
import random
from datetime import datetime, timedelta

# Connect to your existing database
conn = sqlite3.connect('Nazarine_memory.db')
cursor = conn.cursor()

print("🌱 Injecting 24 hours of historical data...")

# Calculate the time exactly 24 hours ago
start_time = datetime.now() - timedelta(hours=24)

# Generate a fake reading every 5 minutes for the last 24 hours
for i in range(24 * 12):
    fake_time = start_time + timedelta(minutes=5 * i)
    # Simulate a realistic power draw between 1.2kW and 7.8kW
    fake_power = round(random.uniform(1.2, 7.8), 2)
    
    # Save it to the database with the artificially backdated timestamp
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', ("time_travel_simulator", 230.0, 15.0, fake_power, fake_time.strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()
print("✅ Done! Time travel successful.")