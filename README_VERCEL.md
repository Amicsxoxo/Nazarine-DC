# 🚀 Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/nazarine-dc)

## Quick Start

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Login to Vercel
```bash
vercel login
```

### 3. Deploy
```bash
cd /workspace
vercel
```

### 4. Production Deployment
```bash
vercel --prod
```

## Project Structure

```
/workspace
├── api/
│   └── index.py          # FastAPI serverless functions
├── *.html                # Dashboard pages (static)
├── nazarine_memory.db    # SQLite database
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel configuration
└── DEPLOYMENT.md         # This file
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/dashboard` | GET | Energy dashboard |
| `/history` | GET | Usage history |
| `/hourly` | GET | Hourly trends |
| `/weekly` | GET | Weekly trends |
| `/ai-support` | GET | AI chat support |
| `/api/telemetry` | POST | ESP32 sensor data |
| `/api/history` | GET | Last 10 readings |
| `/api/hourly` | GET | Hourly aggregation |
| `/api/weekly` | GET | Weekly aggregation |
| `/api/monthly` | GET | Monthly aggregation |
| `/api/yearly` | GET | Yearly aggregation |
| `/api/recommendation` | GET | Off-peak recommendations |
| `/api/chat` | POST | AI support chat |
| `/api/train` | GET | Train ML model |
| `/api/forecast` | GET | 24h forecast |
| `/ws/realtime` | WebSocket | Live telemetry |

## Features

✅ Real-time telemetry via WebSockets  
✅ Historical data aggregation (hourly, weekly, monthly, yearly)  
✅ Cost calculation in Nigerian Naira (₦)  
✅ Carbon offset tracking  
✅ Anomaly/spike detection  
✅ AI-powered chat assistant  
✅ ML-based 24h consumption forecasting  
✅ Off-peak usage recommendations  

## Configuration

- **Price per kWh:** ₦240.0
- **Carbon Factor:** 0.4 kg CO2/kWh
- **Database:** SQLite (`nazarine_memory.db`)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn api.index:app --reload
```

Then open: http://localhost:8000

## ESP32 Integration

Update your ESP32 firmware to point to your Vercel deployment URL:

```cpp
const char* serverUrl = "https://your-project.vercel.app/api/telemetry";
```

## Notes

⚠️ **Important for Production:**
- ESP32 simulator and DB seeder are disabled on Vercel
- SQLite persists data but consider PostgreSQL for production
- WebSocket requires Vercel Pro plan
- Update ESP32 firmware with your deployment URL

---

**Built with FastAPI, Tailwind CSS, Chart.js, and scikit-learn**
