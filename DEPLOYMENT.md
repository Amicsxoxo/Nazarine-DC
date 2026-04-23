# Nazarine DC - Vercel Deployment Guide

## Smart Energy Management System

This is a full-stack IoT platform for real-time energy monitoring, historical data aggregation, and predictive analytics.

## 🚀 Deploy to Vercel

### One-Click Deploy
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/nazarine-dc)

### Manual Deployment

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   cd /workspace
   vercel
   ```

4. **Production Deployment:**
   ```bash
   vercel --prod
   ```

## 📁 Project Structure

```
/workspace
├── api/
│   └── index.py          # Vercel serverless functions (FastAPI)
├── *.html                # Dashboard pages (static files)
├── nazarine_memory.db    # SQLite database (persisted)
├── requirements.txt      # Python dependencies
└── vercel.json           # Vercel configuration
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/dashboard` | GET | Energy dashboard |
| `/history` | GET | Usage history page |
| `/hourly` | GET | Hourly trends page |
| `/weekly` | GET | Weekly trends page |
| `/ai-support` | GET | AI chat support page |
| `/api/telemetry` | POST | Receive ESP32 sensor data |
| `/api/history` | GET | Last 10 readings |
| `/api/hourly` | GET | Hourly aggregated data |
| `/api/weekly` | GET | Weekly aggregated data |
| `/api/monthly` | GET | Monthly aggregated data |
| `/api/yearly` | GET | Yearly aggregated data |
| `/api/recommendation` | GET | Best time for energy usage |
| `/api/chat` | POST | AI support chat |
| `/api/train` | GET | Train ML prediction model |
| `/api/forecast` | GET | 24h consumption forecast |
| `/ws/realtime` | WebSocket | Real-time telemetry stream |

## ⚙️ Configuration

- **Price per kWh:** ₦240.0
- **Carbon Factor:** 0.4 kg CO2/kWh
- **Database:** SQLite (`nazarine_memory.db`)

## 🧠 Features

- ✅ Real-time telemetry via WebSockets
- ✅ Historical data aggregation (hourly, weekly, monthly, yearly)
- ✅ Cost calculation in Nigerian Naira (₦)
- ✅ Carbon offset tracking
- ✅ Anomaly/spike detection
- ✅ AI-powered chat assistant
- ✅ ML-based 24h consumption forecasting
- ✅ Off-peak usage recommendations

## 🛠️ Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Vercel environment simulation
uvicorn api.index:app --reload
```

## 📊 Dashboards

Access these routes after deployment:
- `https://your-project.vercel.app/` - Main Dashboard
- `https://your-project.vercel.app/history` - Usage History
- `https://your-project.vercel.app/hourly` - Hourly Trends
- `https://your-project.vercel.app/weekly` - Weekly Trends
- `https://your-project.vercel.app/ai-support` - AI Support Center

## 📝 Notes

- The ESP32 simulator and database seeder are **disabled** in Vercel deployment
- Data persistence relies on SQLite file (consider upgrading to PostgreSQL for production)
- WebSocket support is available on Vercel Pro plan
- For ESP32 integration, update the telemetry endpoint URL in your device firmware

## 🔗 ESP32 Integration Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

void sendTelemetry(float voltage, float current, float power_kw) {
  HTTPClient http;
  http.begin("https://your-project.vercel.app/api/telemetry");
  http.addHeader("Content-Type", "application/json");
  
  String json = "{\"device_id\":\"ESP32_001\",\"voltage\":" + 
                String(voltage) + 
                ",\"current\":" + String(current) + 
                ",\"power_kw\":" + String(power_kw) + "}";
  
  http.POST(json);
  http.end();
}
```

---

**Built with FastAPI, Tailwind CSS, Chart.js, and scikit-learn**
