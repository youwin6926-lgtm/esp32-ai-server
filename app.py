from flask import Flask, request, Response
import os
import requests
import json

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

    # คำนวณแนวโน้ม
    if len(history) >= 2:
        trend_value = history[-1] - history[-2]
    else:
        trend_value = 0

    if trend_value > 3:
        trend_text = "เพิ่มขึ้น"
    elif trend_value < -3:
        trend_text = "ลดลง"
    else:
        trend_text = "คงที่"

    # ประเมินระดับ
    level, advice = evaluate(pm25)

    if "เปิดพัดลม" in question or "ควรเปิดพัดลมไหมตอนนี้" in question:
        if pm25 > 50:
            reply = "🌫 ฝุ่นสูง ควรเปิดพัดลมทันที"
        elif pm25 > 25 and trend_value > 0:
            reply = "📈 ฝุ่นกำลังเพิ่ม แนะนำเปิดพัดลม"
        else:
            reply = "✅ อากาศยังโอเค ยังไม่จำเป็นต้องเปิดพัดลม"

    elif "แนวโน้ม" in question:
        reply = f"📊 แนวโน้มฝุ่น: {trend_text}\nค่า PM2.5 = {pm25}"

    elif "สรุป" in question or "คุณภาพอากาศ" in question:
        reply = (
            "📋 สรุปคุณภาพอากาศ\n"
            f"PM2.5 = {pm25}\n"
            f"ระดับ = {level}\n"
            f"แนวโน้ม = {trend_text}\n"
            f"คำแนะนำ = {advice}\n"
            f"ความชื้น = {humidity}%\n"
            f"ความกดอากาศ = {pressure} hPa"
        )

    elif "status" in question:
        reply = f"PM2.5 = {pm25}\nความชื้น = {humidity}%\nความกดอากาศ = {pressure} hPa"

    elif "อากาศ" in question:
        reply = f"สมุทรสงคราม\nความชื้น {humidity}%\nความกดอากาศ {pressure} hPa"

    else:
        reply = (
            "คำสั่งที่ใช้ได้:\n"
            "status\n"
            "สรุปคุณภาพอากาศ\n"
            "แนวโน้มฝุ่น\n"
            "ควรเปิดพัดลมไหมตอนนี้"
        )

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
