from flask import Flask, request, jsonify
import os
import requests
import json
from flask import Response

app = Flask(__name__)

history = []

API_KEY = "90d2c037a3e120cd335a8da7a4303aa2"
CITY = "Samut Songkhram"

# ดึงข้อมูลอากาศภายนอก
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY},TH&appid={API_KEY}&units=metric"
    r = requests.get(url, timeout=10).json()

    humidity = r["main"]["humidity"]
    pressure = r["main"]["pressure"]

    return humidity, pressure


# วิเคราะห์ PM2.5
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    pm25 = float(data.get("pm25", 0))

    history.append(pm25)
    if len(history) > 5:
        history.pop(0)

    if len(history) >= 2:
        trend = history[-1] - history[-2]
    else:
        trend = 0

    predicted = pm25 + trend
    level, advice = evaluate(predicted)

    humidity, pressure = get_weather()

    return Response(
    json.dumps({
        "current": pm25,
        "predicted": predicted,
        "level": level,
        "advice": advice,
        "humidity": humidity,
        "pressure": pressure
    }, ensure_ascii=False),
    mimetype="application/json"
)


# Chat AI
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    question = data.get("msg", "").lower()
    pm25 = float(data.get("pm25", 0))
    humidity, pressure = get_weather()

    if "status" in question:
        reply = f"PM2.5 = {pm25}\nความชื้น = {humidity}%\nความกดอากาศ = {pressure} hPa"

    elif "เปิดพัดลม" in question:
        if pm25 > 50:
            reply = "ควรเปิดพัดลมทันที"
        else:
            reply = "ยังไม่จำเป็นต้องเปิดพัดลม"

    elif "อากาศ" in question:
        reply = f"สมุทรสงคราม\nความชื้น {humidity}%\nความกดอากาศ {pressure} hPa"

    else:
        reply = "คำสั่งที่ใช้ได้:\nstatus\nอากาศ\nควรเปิดพัดลมไหม"

   return Response(
    json.dumps({"reply": reply}, ensure_ascii=False),
    mimetype="application/json"
)


# ประเมินระดับฝุ่น
def evaluate(pm25):
    if pm25 < 50:
        return "ปกติ", "ไม่มีผลกระทบกับสุขภาพ"
    elif pm25 < 100:
        return "เริ่มมีผลกระทบ", "ควรใส่หน้ากากเมื่อออกไปข้างนอก"
    else:
        return "อันตราย", "ควรงดกิจกรรมกลางแจ้ง"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


