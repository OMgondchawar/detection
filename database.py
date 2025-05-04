import sqlite3
from datetime import datetime

db_file = "plates.db"

def get_authorized_plates():
    with sqlite3.connect(db_file) as conn:
        result = conn.execute("SELECT plate, owner FROM authorized_plates").fetchall()
    return [{"plate": plate, "owner": owner} for plate, owner in result]

def get_plate_owner(plate):
    with sqlite3.connect(db_file) as conn:
        result = conn.execute("SELECT owner FROM authorized_plates WHERE plate = ?", (plate,)).fetchone()
    return result[0] if result else None

def log_detection(plate, status, source="unknown"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            INSERT INTO detection_logs (plate, status, timestamp, source) 
            VALUES (?, ?, ?, ?)
        """, (plate, status, timestamp, source))

def get_detection_logs(status=None, start_date=None):
    query = "SELECT plate, status, timestamp, source FROM detection_logs WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date.strftime('%Y-%m-%d %H:%M:%S'))

    with sqlite3.connect(db_file) as conn:
        result = conn.execute(query, params).fetchall()

    return [{"plate": plate, "status": status, "timestamp": timestamp, "source": source}
            for plate, status, timestamp, source in result]

def add_authorized_plate(plate, owner):
    with sqlite3.connect(db_file) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO authorized_plates (plate, owner)
            VALUES (?, ?)
        """, (plate.upper(), owner))

def add_authorized_plate(plate, owner):
    with sqlite3.connect(db_file) as conn:
        conn.execute("INSERT INTO authorized_plates (plate, owner) VALUES (?, ?)", (plate, owner))

def delete_authorized_plate(plate):
    with sqlite3.connect(db_file) as conn:
        conn.execute("DELETE FROM authorized_plates WHERE plate = ?", (plate,))
