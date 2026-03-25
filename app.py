from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)

# =====================================================================
# 1. DATABASE INITIALIZATION (Permanent SQL Storage)
# =====================================================================
def init_db():
    conn = sqlite3.connect('smart_hostel.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY, name TEXT, course TEXT, pass TEXT,
            booked INTEGER, room TEXT, bed TEXT, bookingTime INTEGER,
            isWaitlisted INTEGER, waitRoom TEXT, waitBed TEXT, adminLocked INTEGER
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS queue_state (id TEXT PRIMARY KEY, queue_json TEXT)''')

    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        default_students = [
            ("AMRITA2001", "Aarav Kumar", "CSE", "2001", 0, "-", "-", 0, 0, "-", "-", 0),
            ("AMRITA2002", "Aditi Sharma", "AI", "2002", 0, "-", "-", 0, 0, "-", "-", 0),
            ("AMRITA2003", "Advik Singh", "EEE", "2003", 0, "-", "-", 0, 0, "-", "-", 0),
            ("AMRITA2004", "Ananya Gupta", "MBA", "2004", 0, "-", "-", 0, 0, "-", "-", 0),
            ("AMRITA2005", "Arjun Patel", "CSE", "2005", 0, "-", "-", 0, 0, "-", "-", 0),
            ("AMRITA2006", "Avni Reddy", "AI", "2006", 0, "-", "-", 0, 0, "-", "-", 0)
        ]
        cursor.executemany("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", default_students)
        cursor.execute("INSERT INTO queue_state VALUES ('1', '{}')")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('hostel.html')

# =====================================================================
# 2. API: PULL & PUSH DATA
# =====================================================================
@app.route('/api/sync', methods=['GET'])
def pull_data():
    conn = sqlite3.connect('smart_hostel.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    db_list = []
    for r in rows:
        db_list.append({
            "id": r["id"], "name": r["name"], "course": r["course"], "pass": r["pass"],
            "booked": bool(r["booked"]), "room": r["room"], "bed": r["bed"],
            "bookingTime": r["bookingTime"], "isWaitlisted": bool(r["isWaitlisted"]),
            "waitRoom": r["waitRoom"], "waitBed": r["waitBed"], "adminLocked": bool(r["adminLocked"])
        })

    cursor.execute("SELECT queue_json FROM queue_state WHERE id='1'")
    queue_data = json.loads(cursor.fetchone()["queue_json"])
    conn.close()
    return jsonify({"db": db_list, "queue": queue_data})

@app.route('/api/sync', methods=['POST'])
def push_data():
    data = request.json
    db_list = data.get("db", [])
    queue_data = data.get("queue", {})

    conn = sqlite3.connect('smart_hostel.db')
    cursor = conn.cursor()

    for s in db_list:
        cursor.execute("SELECT id FROM students WHERE id=?", (s["id"],))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE students SET
                name=?, course=?, pass=?, booked=?, room=?, bed=?, bookingTime=?,
                isWaitlisted=?, waitRoom=?, waitBed=?, adminLocked=?
                WHERE id=?
            """, (s["name"], s["course"], s["pass"], int(s["booked"]), s["room"], s["bed"],
                  s["bookingTime"] if s["bookingTime"] else 0, int(s["isWaitlisted"]),
                  s["waitRoom"], s["waitBed"], int(s["adminLocked"]), s["id"]))
        else:
            cursor.execute("""
                INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (s["id"], s["name"], s["course"], s["pass"], int(s["booked"]), s["room"], s["bed"],
                  s["bookingTime"] if s["bookingTime"] else 0, int(s["isWaitlisted"]),
                  s["waitRoom"], s["waitBed"], int(s["adminLocked"])))

    queue_json_str = json.dumps(queue_data)
    cursor.execute("UPDATE queue_state SET queue_json=? WHERE id='1'", (queue_json_str,))

    conn.commit()
    conn.close()
    return jsonify({"success": True})
    # 0.0.0.0 guarantees it works on any Wi-Fi router you connect to!
if __name__ == '__main__':
    app.run()
app.run(host='0.0.0.0', port=10000)