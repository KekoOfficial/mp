from flask import Flask, render_template, request, jsonify, session, redirect
import os, json
from config import WEB_HOST, WEB_PORT, LOG_FILE, QUEUE_FILE, WEB_USER, WEB_PASS

app = Flask(__name__)
app.secret_key = "mpserver_2026"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == WEB_USER and request.form.get("pass") == WEB_PASS:
            session["log"] = True
            return redirect("/")
    return render_template("login.html") # Crea un login simple o usa el anterior

@app.route("/")
def index():
    if not session.get("log"): return redirect("/login")
    return render_template("index.html")

@app.route("/settings")
def settings():
    if not session.get("log"): return redirect("/login")
    return render_template("set.html")

@app.route("/logs")
def get_logs():
    if not os.path.exists(LOG_FILE): return jsonify({"logs": []})
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return jsonify({"logs": [l.strip() for l in f.readlines()]})

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    q = json.load(open(QUEUE_FILE)) if os.path.exists(QUEUE_FILE) else []
    q.append({"id": data["id"], "msg": data["msg"]})
    with open(QUEUE_FILE, "w") as f: json.dump(q, f)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host=WEB_HOST, port=WEB_PORT)
