from flask import Flask, request, Response
import os
import requests
import json

app = Flask(__name__)

API_KEY = "90d2c037a3e120cd335a8da7a4303aa2"
CITY = "Samut Songkhram"

history = []
fan_state = 0   # 0=ปิด 1=เปิด

# ดึงข้อมูลอากาศภายนอก
def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY},TH&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10).json()

        humidity = r["main"]["humidity"]
        pressure = r["main"]["pressure"]
        temp = r["main"]["temp"]
        weather = r["weather"][0]["main"]

        return humidity, pressure, temp, weather
    except:
        return 0, 0, 0, "unknown"

# ประเมินคุณภาพอากาศ
def evaluate(pm25):
    if pm25 < 50:
        return "ปกติ", "สามารถทำกิจกรรมได้ตามปกติ"
    elif pm25 < 100:
        return "เริ่มมีผลกระทบ", "ควรใส่หน้ากาก"
    else:
        return "อันตราย", "ควรหลีกเลี่ยงกิจกรรมกลางแจ้ง"
        
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

    humidity, pressure, temp, weather = get_weather()

    return Response(
        json.dumps({
            "current": pm25,
            "predicted": predicted,
            "level": level,
            "advice": advice,
            "humidity": humidity,
            "pressure": pressure,
            "temperature": temp,
            "weather": weather
        }, ensure_ascii=False),
        mimetype="application/json"
    )

# CHAT AI
@app.route("/chat", methods=["POST"])
def chat():
    global fan_state

    data = request.get_json()
    question = data.get("msg", "").lower()
    pm25 = float(data.get("pm25", 0))

    humidity, pressure, temp, weather = get_weather()

    # trend
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

    level, advice = evaluate(pm25)

    # ควบคุมพัดลมด้วย Chat
    if "เปิดพัดลม" in question:
        fan_state = 1
        reply = "🟢 เปิดพัดลมให้แล้ว"

    elif "ปิดพัดลม" in question:
        fan_state = 0
        reply = "🔴 ปิดพัดลมให้แล้ว"

    elif "ควรเปิดพัดลมไหม" in question:
        if pm25 > 50:
            fan_state = 1
            reply = "🌫 ฝุ่นสูง กำลังเปิดพัดลม"
        elif pm25 > 25 and trend_value > 0:
            fan_state = 1
            reply = "📈 ฝุ่นกำลังเพิ่ม แนะนำเปิดพัดลม"
        else:
            fan_state = 0
            reply = "✅ อากาศยังดี ไม่จำเป็นต้องเปิดพัดลม"

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
            f"ความกดอากาศ = {pressure} hPa\n"
            f"อุณหภูมิ = {temp}°C\n"
            f"สภาพอากาศ = {weather}"
        )

    elif "status" in question:
        reply = (
            f"PM2.5 = {pm25}\n"
            f"Fan = {'ON' if fan_state else 'OFF'}\n"
            f"Humidity = {humidity}%"
        )

    else:
        reply = (
            "คำสั่งที่ใช้ได้:\n"
            "เปิดพัดลม\n"
            "ปิดพัดลม\n"
            "ควรเปิดพัดลมไหม\n"
            "สรุปคุณภาพอากาศ\n"
            "แนวโน้มฝุ่น\n"
            "status\n"
        )

    return Response(
        json.dumps({
            "reply": reply,
            "fan": fan_state
        }, ensure_ascii=False),
        mimetype="application/json"
    )

# RUN SERVER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
