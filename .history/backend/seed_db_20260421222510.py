import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('nazarine_memory.db')
cursor = conn.cursor()

print("🌱 Injecting 14 DAYS of historical data into Nazarine DC...")

# Calculate the time exactly 14 days ago
start_time = datetime.now() - timedelta(days=14)

# Generate a reading every 5 minutes for 14 full days
# (14 days * 24 hours * 12 readings per hour = 4,032 rows)
for i in range(14 * 24 * 12):
    fake_time = start_time + timedelta(minutes=5 * i)
    
    # Simulate a realistic power draw. Make weekends slightly lower for realism!
    if fake_time.weekday() >= 5: # 5 and 6 are Sat/Sun
        fake_power = round(random.uniform(1.0, 4.5), 2)
    else:
        fake_power = round(random.uniform(2.5, 8.8), 2)
    
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', ("time_travel_simulator", 230.0, 15.0, fake_power, fake_time.strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()
print("✅ Done! 14-day time travel successful.")