from flask import Flask, request, jsonify

app = Flask(__name__)

last_pm = None

@app.route("/")
def home():
    return "ESP32 AI OK"

@app.route("/analyze", methods=["POST"])
def analyze():
    global last_pm

    data = request.get_json()
    pm25 = float(data.get("pm25", 0))

    # คำนวณแนวโน้ม
    trend = 0
    if last_pm is not None:
        trend = pm25 - last_pm

    last_pm = pm25

    # พยากรณ์ล่วงหน้า 30 นาที (ง่ายแต่ใช้ได้จริง)
    future_pm = pm25 + trend * 3

    if future_pm <= 25:
        level = "คุณภาพอากาศดี"
    elif future_pm <= 50:
        level = "เริ่มมีผลต่อสุขภาพ"
    else:
        level = "อันตรายต่อสุขภาพ"

    return jsonify({
        "now": pm25,
        "forecast": round(future_pm,1),
        "level": level
    })
