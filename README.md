# ⚡ Nazarine DC
### **Smart Energy Management System**

**Nazarine DC** is a high-performance, full-stack IoT platform engineered for real-time telemetry, historical data aggregation, and predictive insights. It bridges the gap between physical ESP32 hardware and high-level data visualization, providing a robust pipeline for smart home and industrial energy grids.

---

## 🚀 Key Advantages

* **High-Fidelity Telemetry**: Achieves sub-second latency via WebSockets for instantaneous power (kW), voltage, and current feedback.
* **Hardware-in-the-Loop**: Seamlessly interfaces with ESP32 microcontrollers using standardized JSON telemetry schemas.
* **Intelligent Aggregation**: Automatically converts raw power into accumulated energy (kWh), real-time costs (₦), and carbon metrics (kg CO2).
* **AI-Ready Architecture**: Infrastructure is optimized for Pandas-ready data structures, supporting future machine learning deployment for grid forecasting.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS, JavaScript (ES6+), Chart.js |
| **Backend** | Python 3.x, FastAPI, Uvicorn (ASGI), WebSockets |
| **Database** | SQLite3 (Persistent Time-Series Storage) |

---

## 💻 Local Setup & Execution

### 1. Prerequisites
Ensure you have **Python 3.7+** installed on your system.

### 2. Install Dependencies
Run the following command to install the core backend requirements:
```bash
pip install fastapi uvicorn pydantic
```

### 3. Initialize the Database
Seed your database with 24 hours of historical telemetry to avoid a blank dashboard:
```bash
python seed_db.py
```
> **Note:** This generates a `verdant_memory.db` file in your project directory.

### 4. Launch the Backend
Start the FastAPI server:
```bash
uvicorn main:app --reload
```
*The server will be live at: `http://127.0.0.1:8000`*

### 5. Access the Dashboard
Open `energy_dashboard.html` directly in your browser.

> **💡 Pro-Tip:** Avoid using VS Code "Live Server" extensions. Frequent database updates may trigger infinite refresh loops. Opening the file via `file:///` is more stable.

---

## 🔌 Simulated Hardware Testing
If you do not have a physical ESP32 connected, you can simulate data:
1.  Open the **Browser Console** (F12).
2.  Paste the **JavaScript Simulator** script (found in project documentation).
3.  Hit **Enter** to begin streaming live telemetry to your server.

---
*Developed as a professional mechatronics and aerospace-grade energy monitoring solution.*