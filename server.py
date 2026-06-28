from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json, os, time

app = Flask(__name__)
CORS(app)
DATA_FILE = "users.json"
CHAT_FILE = "chat.json"

UPGRADES = {
    "tap_boost": {"base_price": 1000, "price_multiplier": 2.5, "effect": "earn_per_tap", "effect_value": 2, "max_level": 20},
    "passive_income": {"base_price": 2000, "price_multiplier": 2.0, "effect": "coins_per_hour", "effect_value": 500, "max_level": 20},
    "energy_boost": {"base_price": 5000, "price_multiplier": 2.2, "effect": "max_energy", "effect_value": 500, "max_level": 10},
    "crypto_exchange": {"base_price": 50000, "price_multiplier": 3.0, "effect": "income_multiplier", "effect_value": 0.5, "max_level": 5},
}

OWNER_ID = "8642488748"

def load(): return json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {}
def save(d): json.dump(d, open(DATA_FILE,"w"), ensure_ascii=False, indent=2)
def load_chat(): return json.load(open(CHAT_FILE)) if os.path.exists(CHAT_FILE) else []
def save_chat(c): json.dump(c, open(CHAT_FILE,"w"), ensure_ascii=False, indent=2)

def get_or_create(uid, username):
    d = load()
    if uid not in d:
        d[uid] = {"username": username, "coins": 0, "total_coins": 0, "earn_per_tap": 1, "coins_per_hour": 0, "max_energy": 1000, "energy": 1000, "last_energy_update": time.time(), "last_passive_update": time.time(), "level": 0, "upgrades": {}, "income_multiplier": 1.0, "referrals": [], "total_taps": 0}
        save(d)
    return d[uid], d

@app.route("/api/user/<uid>")
def get_user(uid):
    username = request.args.get("username", "Player")
    user, d = get_or_create(uid, username)
    now = time.time()
    elapsed = now - user["last_passive_update"]
    if elapsed > 0 and user["coins_per_hour"] > 0:
        earned = int((elapsed / 3600) * user["coins_per_hour"] * user["income_multiplier"])
        user["coins"] += earned
        user["total_coins"] += earned
    user["last_passive_update"] = now
    elapsed_e = now - user["last_energy_update"]
    regen = int(elapsed_e / 3)
    if regen > 0:
        user["energy"] = min(user["max_energy"], user["energy"] + regen)
        user["last_energy_update"] = now
    d[uid] = user
    save(d)
    return jsonify(user)

@app.route("/api/tap", methods=["POST"])
def tap():
    data = request.json
    uid = str(data.get("uid"))
    count = int(data.get("count", 1))
    multiplier = float(data.get("multiplier", 1))
    user, d = get_or_create(uid, "Player")
    taps = min(count, user["energy"])
    if taps <= 0: return jsonify({"error": "no_energy"}), 400
    earned = int(taps * user["earn_per_tap"] * user["income_multiplier"] * multiplier)
    user["coins"] += earned
    user["total_coins"] += earned
    user["energy"] -= taps
    user["total_taps"] += taps
    d[uid] = user
    save(d)
    return jsonify({"earned": earned, "coins": user["coins"], "energy": user["energy"]})

@app.route("/api/upgrade", methods=["POST"])
def upgrade():
    data = request.json
    uid = str(data.get("uid"))
    upg_id = data.get("upgrade_id")
    user, d = get_or_create(uid, "Player")
    upg = UPGRADES.get(upg_id)
    if not upg: return jsonify({"error": "not_found"}), 404
    cur = user["upgrades"].get(upg_id, 0)
    if cur >= upg["max_level"]: return jsonify({"error": "max_level"}), 400
    price = int(upg["base_price"] * (upg["price_multiplier"] ** cur))
    if user["coins"] < price: return jsonify({"error": "not_enough"}), 400
    user["coins"] -= price
    user["upgrades"][upg_id] = cur + 1
    ef = upg["effect"]
    if ef == "earn_per_tap": user["earn_per_tap"] += upg["effect_value"]
    elif ef == "coins_per_hour": user["coins_per_hour"] += upg["effect_value"]
    elif ef == "max_energy": user["max_energy"] += upg["effect_value"]
    elif ef == "income_multiplier": user["income_multiplier"] += upg["effect_value"]
    d[uid] = user
    save(d)
    return jsonify(user)

@app.route("/api/top")
def top():
    d = load()
    sorted_users = sorted(d.items(), key=lambda x: x[1].get("total_coins", 0), reverse=True)[:10]
    return jsonify([{"username": u.get("username","?"), "total_coins": u.get("total_coins",0)} for _, u in sorted_users])

@app.route("/api/chat", methods=["GET"])
def get_chat():
    return jsonify(load_chat())

@app.route("/api/chat", methods=["POST"])
def send_chat():
    data = request.json
    uid = str(data.get("uid",""))
    text = str(data.get("text","")).strip()
    username = str(data.get("username","Игрок"))
    skin = str(data.get("skin","🐹"))
    if not text or len(text) > 200:
        return jsonify({"error": "invalid"}), 400
    chat = load_chat()
    msg = {
        "uid": uid,
        "username": username,
        "skin": skin,
        "text": text,
        "time": int(time.time()),
        "is_owner": uid == OWNER_ID
    }
    chat.append(msg)
    if len(chat) > 100:
        chat = chat[-100:]
    save_chat(chat)
    return jsonify({"ok": True})

@app.route("/api/chat/delete", methods=["POST"])
def delete_msg():
    data = request.json
    uid = str(data.get("uid",""))
    if uid != OWNER_ID:
        return jsonify({"error": "forbidden"}), 403
    msg_time = data.get("time")
    chat = load_chat()
    chat = [m for m in chat if m["time"] != msg_time]
    save_chat(chat)
    return jsonify({"ok": True})

@app.route("/")
def index(): return send_file("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
