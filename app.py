from flask import Flask, render_template, request, jsonify
import pymysql
import json
import os
import urllib.parse as urlparse

app = Flask(__name__)

# The Database URI is pulled from Render's Environment Variables.
# The second string is a "fallback" in case the environment variable isn't set.
DEFAULT_URI = "mysql://avnadmin:AVNS_rZA-pYBFxb8dJha_tYX@mysql-2779b50c-tatikondaloknath-205b.k.aivencloud.com:26298/defaultdb?ssl-mode=REQUIRED"
MYSQL_URI = os.environ.get('mysql://avnadmin:AVNS_rZA-pYBFxb8dJha_tYX@mysql-2779b50c-tatikondaloknath-205b.k.aivencloud.com:26298/defaultdb?ssl-mode=REQUIRED', "mysql://avnadmin:AVNS_rZA-pYBFxb8dJha_tYX@mysql-2779b50c-tatikondaloknath-205b.k.aivencloud.com:26298/defaultdb")

def get_db_connection():
    # This automatically splits the long URI into host, user, password, etc.
    url = urlparse.urlparse(MYSQL_URI)
    
    return pymysql.connect(
        host=mysql-2779b50c-tatikondaloknath-205b.k.aivencloud.com,
        user=avnadmin,
        password=AVNS_rZA-pYBFxb8dJha_tYX,
        port=26298,
        database='mysql://avnadmin:AVNS_rZA-pYBFxb8dJha_tYX@mysql-2779b50c-tatikondaloknath-205b.k.aivencloud.com:26298/defaultdb?ssl-mode=REQUIRED', # Removes the '/' from the start of the path
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        ssl={'ssl': {}} # Aiven requires SSL
    )

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Create Students Table
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
            # Create Queue Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queue_state (
                    id VARCHAR(10) PRIMARY KEY, 
                    queue_json TEXT
                )
            ''')
            
            cursor.execute("SELECT COUNT(*) as count FROM queue_state")
            if cursor.fetchone()['count'] == 0:
                cursor.execute("INSERT INTO queue_state (id, queue_json) VALUES ('1', '{}')")
        print("Aiven MySQL Database Initialized.")
    finally:
        conn.close()

# Initialize tables
init_db()

@app.route('/')
def home():
    return render_template('hostel.html')

@app.route('/api/sync', methods=['GET'])
def pull_data():
    conn = get_db_connection()
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
                vals = (
                    s["id"], s["name"], s["course"], s["pass"], int(s["booked"]), s["room"], s["bed"], b_time, int(s["isWaitlisted"]), s["waitRoom"], s["waitBed"], int(s["adminLocked"]),
                    s["name"], s["course"], s["pass"], int(s["booked"]), s["room"], s["bed"], b_time, int(s["isWaitlisted"]), s["waitRoom"], s["waitBed"], int(s["adminLocked"])
                )
                cursor.execute(sql, vals)
                
            cursor.execute("UPDATE queue_state SET queue_json=%s WHERE id='1'", (json.dumps(queue_data),))
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
