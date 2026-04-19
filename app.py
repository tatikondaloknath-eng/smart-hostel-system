from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

app = Flask(__name__)

# Render Database URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://hostel_db_9c2w_user:iBKJ0L9rcWSiO4ZHtByVAI7YFpYL7683@dpg-d748onua2pns73ahh0m0-a/hostel_db_9c2w')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY, name TEXT, course TEXT, pass TEXT,
            booked INTEGER, room TEXT, bed TEXT, bookingTime BIGINT,
            isWaitlisted INTEGER, waitRoom TEXT, waitBed TEXT, adminLocked INTEGER
        )
    ''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS queue_state (id TEXT PRIMARY KEY, queue_json TEXT)''')
    cursor.execute("SELECT COUNT(*) FROM queue_state")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO queue_state VALUES ('1', '{}')")
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('hostel.html')

@app.route('/api/sync', methods=['GET'])
def pull_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        db_list = []
        for r in rows:
            db_list.append({
                "id": r["id"], "name": r["name"], "course": r["course"], "pass": r["pass"],
                "booked": bool(r["booked"]), "room": r["room"], "bed": r["bed"],
                "bookingTime": r["bookingtime"], "isWaitlisted": bool(r["iswaitlisted"]),
                "waitRoom": r["waitroom"], "waitBed": r["waitbed"], "adminLocked": bool(r["adminlocked"])
            })
        cursor.execute("SELECT queue_json FROM queue_state WHERE id='1'")
        q_row = cursor.fetchone()
        queue_data = json.loads(q_row["queue_json"]) if q_row and q_row["queue_json"] else {}
        return jsonify({"db": db_list, "queue": queue_data})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/sync', methods=['POST'])
def push_data():
    data = request.json
    db_list = data.get("db", [])
    queue_data = data.get("queue", {})
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for s in db_list:
            cursor.execute("SELECT id FROM students WHERE id=%s", (s["id"],))
            vals = (s["name"], s["course"], s["pass"], 1 if s.get("booked") else 0, s["room"], s["bed"], 
                    int(s["bookingTime"]) if s.get("bookingTime") else 0, 1 if s.get("isWaitlisted") else 0, 
                    s["waitRoom"], s["waitBed"], 1 if s.get("adminLocked") else 0, s["id"])
            if cursor.fetchone():
                cursor.execute("UPDATE students SET name=%s,course=%s,pass=%s,booked=%s,room=%s,bed=%s,bookingTime=%s,isWaitlisted=%s,waitRoom=%s,waitBed=%s,adminLocked=%s WHERE id=%s", vals)
            else:
                cursor.execute("INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", vals)
        cursor.execute("UPDATE queue_state SET queue_json=%s WHERE id='1'", (json.dumps(queue_data),))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
