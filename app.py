from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "ESP32 AI Server Running"

@app.route("/analyze", methods=["POST", "GET"])
def analyze():
    try:
        data = request.get_json(silent=True) or {}
        pm25 = float(data.get("pm25", 0))
    except:
        pm25 = 0

    if pm25 <= 25:
        result = "good"
    elif pm25 <= 50:
        result = "warn"
    else:
        result = "danger"

    return jsonify({
        "status": "ok",
        "pm25": pm25,
        "result": result
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
