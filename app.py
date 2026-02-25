from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# เก็บค่าล่าสุด
history = []

API_KEY = "90d2c037a3e120cd335a8da7a4303aa2"
CITY = "Samut Songkhram"

# ดึงข้อมูลอากาศ
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY},TH&appid={API_KEY}&units=metric"
    r = requests.get(url, timeout=10).json()

    humidity = r["main"]["humidity"]
    pressure = r["main"]["pressure"]

    return humidity, pressure


# AI วิเคราะห์
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    pm25 = float(data.get("pm25", 0))

    history.append(pm25)
    if len(history) > 5:
        history.pop(0)

    # คำนวณแนวโน้ม
    if len(history) >= 2:
        trend = history[-1] - history[-2]
    else:
        trend = 0

    predicted = pm25 + trend
    level, advice = evaluate(predicted)

    humidity, pressure = get_weather()

    return jsonify({
        "current": pm25,
        "predicted": predicted,
        "level": level,
        "advice": advice,
        "humidity": humidity,
        "pressure": pressure
    })


# ประเมินคุณภาพอากาศ
def evaluate(pm25):
    if pm25 < 50:
        return "ปกติ", "เปิดหน้าต่างได้"
    elif pm25 < 100:
        return "เริ่มมีผลกระทบ", "ควรเปิดพัดลม"
    else:
        return "อันตราย", "เปิดพัดลมทันที"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
