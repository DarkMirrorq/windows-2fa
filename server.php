from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("devices.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS active_devices (
                      device_name TEXT PRIMARY KEY,
                      status TEXT)''')
    conn.commit()
    conn.close()

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    device_name = data.get("device_name")
    if not device_name:
        return jsonify({"error": "Device name required"}), 400
    
    conn = sqlite3.connect("devices.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO active_devices (device_name, status) VALUES (?, 'pending')", (device_name,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Device registered", "device_name": device_name})

@app.route("/active_devices", methods=["GET"])
def active_devices():
    conn = sqlite3.connect("devices.db")
    cursor = conn.cursor()
    cursor.execute("SELECT device_name, status FROM active_devices")
    devices = cursor.fetchall()
    conn.close()
    
    return jsonify({"devices": [{"device_name": d[0], "status": d[1]} for d in devices]})

@app.route("/approve", methods=["POST"])
def approve():
    data = request.json
    device_name = data.get("device_name")
    if not device_name:
        return jsonify({"error": "Device name required"}), 400
    
    conn = sqlite3.connect("devices.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE active_devices SET status = 'approved' WHERE device_name = ?", (device_name,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Device approved", "device_name": device_name})

if __name__ == "__main__":
    init_db()
    app.run(host="IP ADRESS", port=3005, debug=True)
