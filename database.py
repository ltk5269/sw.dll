# database.py - SQLite 기반 로그 저장 기능

import sqlite3
from datetime import datetime

DB_NAME = "phishing_logs.db"

# DB 초기화
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            text TEXT,
            score INTEGER,
            zcr REAL,
            sc REAL
        )
    """)
    conn.commit()
    conn.close()

# 로그 저장
def save_log(text, score, zcr, sc):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO logs (timestamp, text, score, zcr, sc) VALUES (?, ?, ?, ?, ?)",
                   (timestamp, text, score, zcr, sc))
    conn.commit()
    conn.close()