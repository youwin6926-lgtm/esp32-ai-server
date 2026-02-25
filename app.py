from flask import Flask, request, jsonify
import os

# เก็บค่าล่าสุด
history = []

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    pm25 = float(data.get("pm25", 0))

    history.append(pm25)
    if len(history) > 10:
        history.pop(0)

    level, advice = evaluate(pm25)

    return jsonify({
        "pm25": pm25,
        "level": level,
        "advice": advice
    })

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    pm25 = float(data.get("pm25", 0))

    history.append(pm25)
    if len(history) > 5:
        history.pop(0)

    # คาดการณ์ trend
    if len(history) >= 2:
        trend = history[-1] - history[-2]
    else:
        trend = 0

    predicted = pm25 + trend

    level, advice = evaluate(predicted)

    return jsonify({
        "current": pm25,
        "predicted": predicted,
        "level": level,
        "advice": advice
    })

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

