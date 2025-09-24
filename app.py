from flask import Flask, render_template, request, jsonify
import json
import os
import re

app = Flask(__name__)

# Load knowledge base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "symptoms_full.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    SYMPTOMS_DB = json.load(f)

# Aliases mapping
alias_map = {}
for canonical, obj in SYMPTOMS_DB.items():
    all_aliases = list(obj.get("aliases", []))
    if canonical not in all_aliases:
        all_aliases.insert(0, canonical)
    for a in all_aliases:
        a_clean = (a or "").strip().lower()
        if not a_clean:
            continue
        alias_map[a_clean] = canonical
sorted_aliases = sorted(alias_map.keys(), key=lambda x: -len(x))

# --- Interactive chat responses ---
INTERACTIVE_RESPONSES = {
    # Greetings
    ("hii", "hi", "helo", "hey", "hello", "excuse me", "hlo"): 
        "👋 Hi, welcome to the FITHEALTH BOT. I can give remedies/solutions to your health problems.\n\nMay I know from which health problem you are suffering?\n\nExamples:\n1. low bp\n2. I am having low bp\n3. I am suffering with low bp",
    ("good morning",): "🌞 Good morning!",
    ("good afternoon",): "Good afternoon!",
    ("good night", "good night "): "🌙 Good night! Sleep well.",
    ("ok bye", "bye", "see you", "good bye", "tata", "byee", "see you bye"): 
        "🙏 Thank you for visiting us! Hope it was helpful.",

    # Help / usage
    ("help", "i need help", "i dont know how to use", "help me", "can you help me", "i want some help"): 
        "💡 Just type your health problem (for example: 'low bp'). I will give the solution.",
    ("what can you do", "what you can do", "what you do", "use", "is there any use", "what is the use", "whats the use"): 
        "🩺 I provide the basic aid/solution to your health problem.",
    ("how to use", "how to interact", "how to communicate"): 
        "👉 Just type your problem (example: 'fever', 'cough'), and I will give the basic solution.",

    # Privacy / trust
    ("how do you know my name?", "how come you know my name", "how you know my name", "you know my name"): 
        "🙂 I only use your provided name here. I do not store any personal data. It’s just to make the chat feel natural.",
    ("does it store any information?", "do it store information", "store any information"): 
        "🔒 For your kind information, it does not store any information. Thank you!",
    ("is your solution true", "solution true"): 
        "ℹ️ This is just basic aid to the symptom. The information is gathered from reliable sources like Google.",
    ("why should i trust", "why should i trust you", "should i trust you"): 
        "🤔 That depends on you. I’m just a bot that provides basic aid/solution to the problem.",
    ("is the information correct", "is information true"): 
        "✅ The information is gathered from Google. You can trust it, or double-check if you want.",
    ("is it helpful", "helpful", "is it useful", "useful"): 
        "🙌 We hope it is useful to get the basic aid/solution to your problem.",
    ("does it have any side effects", "any side effects", "side effects", "any problems if we use this"): 
        "⚠️ Very rarely. Since it’s just advice from a bot, sometimes it may go wrong. We are sorry for that.",

    # Fun / casual
    ("ya sure", "sure", "ya"): "👌 Tell me your problem!",
    ("i love you", "love you", "lv u", "i love you so much", "love you so much"): "❤️ I love you too!",
    ("thank you", "thanks", "thanks a lot", "tqs", "tq"): "You're welcome! 🙏",
    ("yes",): "Thank you! 😊",
    ("who created this bot", "created by", "who developed this", "who did this", "who created you?"): 
        "👨‍💻 This bot was developed by the FITHEALTH team as a basic health assistant."
}

def find_interactive_response(message: str):
    msg = message.lower().strip()
    for keys, reply in INTERACTIVE_RESPONSES.items():
        if msg in keys:
            return reply
    return None

def find_symptom_match(user_text: str):
    text = user_text.lower()
    for alias in sorted_aliases:
        pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
        if re.search(pattern, text):
            canonical = alias_map[alias]
            return canonical
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip().lower()
    if not user_message:
        return jsonify({"reply": "Please type a symptom or a question."})

    # 1. Interactive/small talk
    resp = find_interactive_response(user_message)
    if resp:
        return jsonify({"reply": resp})

    # 2. Symptom lookup
    symptom = find_symptom_match(user_message)
    if symptom:
        data = SYMPTOMS_DB.get(symptom, {})
        advice = data.get("advice", "No advice available.")
        reply = f"💡 Advice:\n{advice}"
        return jsonify({"reply": reply})

    # 3. Fallback
    fallback = (
        "⚠️ I’m sorry — I don't recognize that symptom.\n"
        "Try typing simpler terms like 'fever', 'headache', 'cough', or 'stomach ache'.\n"
        "If symptoms are severe or urgent, please consult a medical professional."
    )
    return jsonify({"reply": fallback})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
