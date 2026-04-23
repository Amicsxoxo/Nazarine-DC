import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('nazarine_memory.db')
cursor = conn.cursor()

print("🌱 Injecting 2 YEARS of REALISTIC historical data into Nazarine DC...")

start_time = datetime.now() - timedelta(days=730)

for i in range(730 * 24 * 12):
    fake_time = start_time + timedelta(minutes=5 * i)
    
    month = fake_time.month
    
    # REALISTIC BASE LOAD: 0.3kW (300W) normally, 0.6kW (600W) in peak seasons
    base = 0.6 if month in [6, 7, 8, 12, 1, 2] else 0.3
    
    # Weekends might use slightly more power (people at home)
    if fake_time.weekday() >= 5: 
        fake_power = round(random.uniform(base, base * 2.5), 2)
    else:
        fake_power = round(random.uniform(base * 0.5, base * 1.8), 2)
    
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', ("time_travel_simulator", 230.0, 5.0, fake_power, fake_time.strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()
print("✅ Done! 2-Year realistic macro-aggregation successful.")