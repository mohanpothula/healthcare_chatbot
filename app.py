from flask import Flask, render_template, request, jsonify
import json
import openai
import os
import re
from dotenv import load_dotenv

# ------------------------------------------------------------
# 1️⃣ Load environment variables
# ------------------------------------------------------------
load_dotenv()  # loads .env file in the project root

# ------------------------------------------------------------
# 2️⃣ Load OpenAI API Key
# ------------------------------------------------------------
# This must be before any OpenAI API calls
openai.api_key = os.getenv("OPENAI_API_KEY")

# ------------------------------------------------------------
# 3️⃣ Flask app setup
# ------------------------------------------------------------
app = Flask(__name__)

# Load knowledge base JSON
with open("knowledge_base.json", "r") as f:
    kb = json.load(f)

# Safety: Medical keywords that trigger redirect
medical_keywords = [
    "pain", "symptom", "diagnosis", "medicine", "medication",
    "pill", "injury", "bleeding", "emergency", "doctor", "hospital"
]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    user_input_clean = user_input.lower().strip()

    response_text = ""

    # 1️⃣ Medical Safety Redirect
    if any(word in user_input_clean for word in medical_keywords):
        response_text = (
            "I can't help with medical issues. "
            "Please consult a healthcare professional or emergency services."
        )

    # 2️⃣ Daily DOs
    elif re.search(r"\b(do|dos|do's|daily do|daily dos)\b", user_input_clean):
        response_text = "\n".join(kb["dos"])

    # 3️⃣ Daily DON'Ts
    elif re.search(r"\b(don[\''’]?\s*t?s?|dont|donot|daily don[\''’]?ts?)\b", user_input_clean):
        response_text = "\n".join(kb["donts"])

    # 4️⃣ Diet Tips
    elif any(k in user_input_clean for k in ["diet", "tip", "meal", "hydration", "water", "nutrition", "food"]):
        response_text = "\n".join(kb["diet_tips"])

    # 5️⃣ Diet Plans
    elif "weight" in user_input_clean and "loss" in user_input_clean:
        plan = kb["plans"]["weight loss"]
        response_text = (
            "Here is a 1-day Weight Loss Plan:\n"
            f"Breakfast: {plan['breakfast']}\n"
            f"Lunch: {plan['lunch']}\n"
            f"Snack: {plan['snack']}\n"
            f"Dinner: {plan['dinner']}"
        )
    elif "maintenance" in user_input_clean:
        plan = kb["plans"]["maintenance"]
        response_text = (
            "Here is a 1-day Maintenance Plan:\n"
            f"Breakfast: {plan['breakfast']}\n"
            f"Lunch: {plan['lunch']}\n"
            f"Snack: {plan['snack']}\n"
            f"Dinner: {plan['dinner']}"
        )
    elif "muscle" in user_input_clean or "gain" in user_input_clean:
        plan = kb["plans"]["muscle gain"]
        response_text = (
            "Here is a 1-day Muscle Gain Plan:\n"
            f"Breakfast: {plan['breakfast']}\n"
            f"Lunch: {plan['lunch']}\n"
            f"Snack: {plan['snack']}\n"
            f"Dinner: {plan['dinner']}"
        )

    # 6️⃣ Fallback Response
    else:
        response_text = kb["fallback"]

    # 7️⃣ Optional LLM Enhancement (Additional note)
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You provide friendly general wellness and lifestyle advice. Never medical advice."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=80
        )
        ai_note = completion.choices[0].message.content.strip()
        response_text += f"\n\nAdditional note: {ai_note}"

    except Exception as e:
        print("OpenAI error:", e)
        response_text += "\n\n[Error retrieving additional advice. Try again later.]"

    # 8️⃣ Add Disclaimer
    response_text += (
        "\n\n⚠️ Disclaimer: This chatbot provides general wellness information only "
        "and is not a substitute for professional medical advice."
    )

    return jsonify({"response": response_text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

