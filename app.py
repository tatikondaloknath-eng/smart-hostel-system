from flask import Flask, render_template, request, jsonify
import pymysql
import json
import os
import urllib.parse as urlparse

app = Flask(__name__)

# --- DATABASE CONFIGURATION (Aiven MySQL) ---
# Pulled from your screenshot: User: avnadmin | Pass: AVNS_rZA-pYBFxb8dJha_tYX
DEFAULT_URI = "mysql://avnadmin:AVNS_rZA-pYBFxb8dJha_tYX@mysql-2779b50c-tatikondaloknath-205b.k.aivencloud.com:26298/defaultdb?ssl-mode=REQUIRED"
MYSQL_URI = os.environ.get('DATABASE_URL', DEFAULT_URI)

def get_db_connection():
    try:
        url = urlparse.urlparse(MYSQL_URI)
        return pymysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            port=url.port,
            database=url.path[1:],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
            ssl={'ssl': {}}  # Required for Aiven Secure Connection
        )
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None: return
    try:
        with conn.cursor() as cursor:
            # Students Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id VARCHAR(50) PRIMARY KEY, 
                    name VARCHAR(100), 
                    course VARCHAR(50), 
                    pass VARCHAR(50),
                    booked TINYINT(1), 
                    room VARCHAR(20), 
                    bed VARCHAR(20), 
                    bookingTime BIGINT,
                    isWaitlisted TINYINT(1), 
                    waitRoom VARCHAR(20), 
                    waitBed VARCHAR(20), 
                    adminLocked TINYINT(1)
                )
            ''')
            # Queue Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queue_state (
                    id VARCHAR(10) PRIMARY KEY, 
                    queue_json TEXT
                )
            ''')
            cursor.execute("SELECT COUNT(*) as count FROM queue_state")
            if cursor.fetchone()['count'] == 0:
                cursor.execute("INSERT INTO queue_state (id, queue_json) VALUES ('1', '{}')")
        print("Aiven MySQL Initialized Successfully")
    finally:
        conn.close()

init_db()

@app.route('/')
def home():
    return render_template('hostel.html')

@app.route('/api/sync', methods=['GET'])
def pull_data():
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Connection Failed"}), 500
    try:
        with conn.cursor() as cursor:
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
            q_row = cursor.fetchone()
            queue_data = json.loads(q_row["queue_json"]) if q_row else {}
        return jsonify({"db": db_list, "queue": queue_data})
    finally:
        conn.close()

@app.route('/api/sync', methods=['POST'])
def push_data():
    data = request.json
    db_list = data.get("db", [])
    queue_data = data.get("queue", {})
    conn = get_db_connection()
    if not conn: return jsonify({"error": "DB Connection Failed"}), 500
    try:
        with conn.cursor() as cursor:
            for s in db_list:
                sql = """
                    INSERT INTO students (id, name, course, pass, booked, room, bed, bookingTime, isWaitlisted, waitRoom, waitBed, adminLocked)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    name=%s, course=%s, pass=%s, booked=%s, room=%s, bed=%s, bookingTime=%s, isWaitlisted=%s, waitRoom=%s, waitBed=%s, adminLocked=%s
                """
                b_time = int(s["bookingTime"]) if s.get("bookingTime") else 0
                v = (s["id"], s["name"], s["course"], s["pass"], int(s["booked"]), s["room"], s["bed"], b_time, int(s["isWaitlisted"]), s["waitRoom"], s["waitBed"], int(s["adminLocked"]))
                cursor.execute(sql, v + v[1:])
            cursor.execute("UPDATE queue_state SET queue_json=%s WHERE id='1'", (json.dumps(queue_data),))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
