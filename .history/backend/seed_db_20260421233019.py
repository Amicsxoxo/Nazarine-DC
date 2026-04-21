import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('nazarine_memory.db')
cursor = conn.cursor()

print("🌱 Injecting 6 MONTHS of historical data into Nazarine DC (This will take a few seconds)...")

# Calculate the time exactly 180 days ago
start_time = datetime.now() - timedelta(days=180)

# Generate a reading every 5 minutes for 180 full days
# (180 days * 24 hours * 12 readings = 51,840 rows!)
for i in range(180 * 24 * 12):
    fake_time = start_time + timedelta(minutes=5 * i)
    
    # Simulate seasonal changes (higher base draw in summer/winter)
    month = fake_time.month
    if month in [6, 7, 8, 12, 1, 2]: 
        base = 4.0 
    else:
        base = 2.5
        
    # Simulate weekend drops
    if fake_time.weekday() >= 5: 
        fake_power = round(random.uniform(base * 0.5, base * 1.5), 2)
    else:
        fake_power = round(random.uniform(base, base * 2.5), 2)
    
    cursor.execute('''
        INSERT INTO energy_history (device_id, voltage, current, power_kw, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', ("time_travel_simulator", 230.0, 15.0, fake_power, fake_time.strftime('%Y-%m-%d %H:%M:%S')))

conn.commit()
conn.close()
print("✅ Done! 6-month macro-aggregation successful. 51,840 rows generated.")