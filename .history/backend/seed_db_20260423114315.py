import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('nazarine_memory.db')
cursor = conn.cursor()

print("🌱 Injecting 2 YEARS of historical data into Nazarine DC...")

# 730 days = 2 full years of data
start_time = datetime.now() - timedelta(days=730)

# Generate a reading every 5 minutes
for i in range(730 * 24 * 12):
    fake_time = start_time + timedelta(minutes=5 * i)
    
    month = fake_time.month
    base = 4.0 if month in [6, 7, 8, 12, 1, 2] else 2.5
    fake_power = round(random.uniform(base * 0.5, base * 1.5) if fake_time.weekday() >= 5 else random.uniform(base, base * 2.5), 2)
    
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', ("time_travel_simulator", 230.0, 15.0, fake_power, fake_time.strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()
print("✅ Done! 2-Year macro-aggregation successful.")