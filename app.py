from flask import Flask, request, Response
import os
import requests
import json

app = Flask(__name__)

API_KEY = "90d2c037a3e120cd335a8da7a4303aa2"
CITY = "Samut Songkhram"

history = []
fan_state = None

fan_learning = {
    "fan_on": False,
    "start_pm": None,
    "eff_history": []
}

# FAN LEARNING SYSTEM
def update_fan_learning(pm25, fan):
    global fan_learning

    if fan == 1 and fan_learning["fan_on"] == False:
        fan_learning["fan_on"] = True
        fan_learning["start_pm"] = pm25

    elif fan == 1 and fan_learning["fan_on"] == True:
        start = fan_learning["start_pm"]
        if start and start > 0:
            reduction = start - pm25
            if reduction < 0:
                reduction = 0

            efficiency = (reduction / start) * 100
            # ป้องกันค่าผิดปกติ
            if efficiency < 0:
                efficiency = 0
            if efficiency > 100:
                efficiency = 100

            fan_learning["eff_history"].append(efficiency)

            if len(fan_learning["eff_history"]) > 20:
                fan_learning["eff_history"].pop(0)

    elif fan == 0:
        fan_learning["fan_on"] = False
        fan_learning["start_pm"] = None


def get_fan_efficiency():
    if len(fan_learning["eff_history"]) == 0:
        return 0
    return sum(fan_learning["eff_history"]) / len(fan_learning["eff_history"])


# WEATHER API
def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY},TH&appid={API_KEY}&units=metric"
        r = requests.get(url, timeout=10).json()

        return (
            r["main"]["humidity"],
            r["main"]["pressure"],
            r["main"]["temp"],
            r["weather"][0]["main"]
        )
    except:
        return 0, 0, 0, "unknown"


# AIR QUALITY EVALUATION
def evaluate(pm25):
    if pm25 < 50:
        return "ปกติ", "สามารถทำกิจกรรมได้ตามปกติ"
    elif pm25 < 100:
        return "เริ่มมีผลกระทบ", "ควรใส่หน้ากาก"
    else:
        return "อันตราย", "ควรหลีกเลี่ยงกิจกรรมกลางแจ้ง"


# ANALYZE ENDPOINT
@app.route("/analyze", methods=["POST"])
def analyze():
    global fan_state

    data = request.get_json()
    pm25 = float(data.get("pm25", 0))
    fan = int(data.get("fan", 0))

    fan_state = fan   # รับค่าจาก ESP32

    history.append(pm25)
    if len(history) > 5:
        history.pop(0)

    update_fan_learning(pm25, fan)

    trend = history[-1] - history[-2] if len(history) >= 2 else 0
    predicted = pm25 + trend

    level, advice = evaluate(predicted)
    humidity, pressure, temp, weather = get_weather()

    return Response(
        json.dumps({
            "current": pm25,
            "predicted": predicted,
            "level": level,
            "advice": advice,
            "fan": fan_state,  # ส่งสถานะพัดลมกลับ
            "fan_efficiency": get_fan_efficiency(),
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
    fan_state = int(data.get("fan", fan_state or 0))  # รับสถานะจริงจาก ESP32

    humidity, pressure, temp, weather = get_weather()

    trend_value = history[-1] - history[-2] if len(history) >= 2 else 0

    if trend_value > 3:
        trend_text = "เพิ่มขึ้น"
    elif trend_value < -3:
        trend_text = "ลดลง"
    else:
        trend_text = "คงที่"

    level, advice = evaluate(pm25)
    eff = get_fan_efficiency()

    # ===== AI RESPONSE =====
    if "ควรเปิดพัดลมไหม" in question:
        if pm25 > 50:
            reply = "🌫 ฝุ่นสูง แนะนำเปิดพัดลม"
        elif pm25 > 25 and trend_value > 0:
            reply = "📈 ฝุ่นเพิ่ม แนะนำเปิดพัดลม"
        else:
            reply = "✅ อากาศยังดี"

    elif "แนวโน้ม" in question:
        reply = f"📊 แนวโน้มฝุ่น: {trend_text}\nPM2.5 = {pm25}"

    elif "สรุป" in question or "คุณภาพอากาศ" in question:
        reply = (
            "📋 สรุปคุณภาพอากาศ\n"
            f"PM2.5 = {pm25}\n"
            f"ระดับ = {level}\n"
            f"แนวโน้ม = {trend_text}\n"
            f"พัดลมลดฝุ่นเฉลี่ย = {eff:.1f}%\n"
            f"อุณหภูมิ = {temp}°C\n"
            f"ความชื้น = {humidity}%\n"
            f"อากาศ = {weather}"
        )

    elif "ประสิทธิภาพพัดลม" in question:
        reply = f"🧠 พัดลมลดฝุ่นเฉลี่ย {eff:.1f}%"

    else:
        reply = (
            "คำสั่งที่ใช้ได้:\n"
            "ควรเปิดพัดลมไหม\n"
            "สรุปคุณภาพอากาศ\n"
            "แนวโน้มฝุ่น\n"
            "ประสิทธิภาพพัดลม"
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



