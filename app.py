from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "ESP32 AI Server Running"

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
        pm25 = float(data.get("pm25", 0))

        if pm25 <= 25:
            level = "ดี"
            advice = "เปิดหน้าต่างได้"
        elif pm25 <= 50:
            level = "เริ่มมีผลกระทบ"
            advice = "ควรเปิดพัดลม"
        else:
            level = "อันตราย"
            advice = "ปิดหน้าต่างทันที"

        return jsonify({
            "pm25": pm25,
            "level": level,
            "advice": advice
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# สำคัญมากสำหรับ Render
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
