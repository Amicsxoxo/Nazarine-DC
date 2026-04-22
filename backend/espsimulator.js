console.log("🚀 Verdant ESP32 Simulator Started!");

// Run this loop every 3 seconds
const simInterval = setInterval(() => {
    // Generate a random power reading between 2.0 and 8.0 kW
    let randomPower = (Math.random() * (8.0 - 2.0) + 2.0).toFixed(2);
    
    let payload = {
        device_id: "console_simulated_esp32",
        voltage: 230.0,
        current: 15.0,
        power_kw: parseFloat(randomPower)
    };

    // Send the POST request to your FastAPI backend
    fetch("http://127.0.0.1:8000/api/telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => console.log(`📡 Beamed to Server: ${randomPower} kW`))
    .catch(err => console.error("🛑 Backend connection failed. Is the server running?", err));

}, 3000);