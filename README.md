# 📁 main.py
from stream_audio import start_streaming
from dashboard import run_dashboard
import threading

if __name__ == "__main__":
    threading.Thread(target=start_streaming, daemon=True).start()
    run_dashboard()


# 📁 stream_audio.py
import pyaudio
import wave
import threading
from whisper_wrap import transcribe_audio
from rule_engine import check_rules
from llama_checker import check_with_llama, score_with_llama
from database import save_log
from notifier import alert_user, update_dashboard
import os

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
TEMP_FILENAME = "temp.wav"

def record_chunk():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    frames = []
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(TEMP_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def process_audio():
    record_chunk()
    text = transcribe_audio(TEMP_FILENAME)
    os.remove(TEMP_FILENAME)
    if not text.strip():
        return

    triggered = False
    if check_rules(text):
        alert_user("[RULE] 의심 키워드 감지됨")
        triggered = True
    score = score_with_llama(text)
    if score >= 70:
        alert_user(f"[LLM] 위험도 {score}% 탐지됨")
        triggered = True

    save_log(text, score)
    if triggered:
        update_dashboard(text, score)

def start_streaming():
    while True:
        thread = threading.Thread(target=process_audio)
        thread.start()
        thread.join()


# 📁 whisper_wrap.py
import whisper

model = whisper.load_model("base")

def transcribe_audio(file_path):
    result = model.transcribe(file_path, language='ko')
    return result.get("text", "")


# 📁 rule_engine.py
import re

SUSPICIOUS_KEYWORDS = ["계좌", "송금", "보안", "인증번호", "공무원", "검찰", "압류"]

def check_rules(text):
    for keyword in SUSPICIOUS_KEYWORDS:
        if re.search(keyword, text):
            return True
    return False


# 📁 llama_checker.py
import subprocess


def check_with_llama(text):
    prompt = f"다음 문장이 보이스피싱일 가능성이 있는지 간단히 yes/no로 답해줘: {text}"
    try:
        result = subprocess.run([
            "ollama", "run", "llama2", prompt
        ], capture_output=True, text=True, timeout=20)
        return "yes" in result.stdout.lower()
    except:
        return False


def score_with_llama(text):
    prompt = f"다음 문장이 보이스피싱일 위험도가 얼마나 되는지 0에서 100 사이의 숫자로 답해주세요. 숫자만 말해주세요.\n{text}"
    try:
        result = subprocess.run([
            "ollama", "run", "llama2", prompt
        ], capture_output=True, text=True, timeout=20)
        score_str = result.stdout.strip().split("\n")[-1].strip()
        score = int(''.join(filter(str.isdigit, score_str)))
        return min(score, 100)
    except:
        return 0


# 📁 database.py
import sqlite3
import os

DB_PATH = "data/phishing_log.db"

if not os.path.exists("data"):
    os.makedirs("data")

def save_log(text, score):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            risk_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT INTO logs (content, risk_score) VALUES (?, ?)", (text, score))
    conn.commit()
    conn.close()


# 📁 notifier.py
import platform
import os
import tkinter as tk
from tkinter import messagebox

latest_text = ""
latest_score = 0


def alert_user(message):
    if platform.system() == "Windows":
        os.system(f"msg * {message}")
    elif platform.system() == "Darwin":
        os.system(f"osascript -e 'display notification \"{message}\"'")
    else:
        print("[경고]", message)


def update_dashboard(text, score):
    global latest_text, latest_score
    latest_text = text
    latest_score = score


def get_latest():
    return latest_text, latest_score


# 📁 dashboard.py
import tkinter as tk
from notifier import get_latest


def run_dashboard():
    def update():
        text, score = get_latest()
        text_var.set(f"최근 텍스트: {text}")
        score_var.set(f"위험 점수: {score}%")
        root.after(3000, update)

    root = tk.Tk()
    root.title("보이스피싱 탐지 대시보드")
    text_var = tk.StringVar()
    score_var = tk.StringVar()

    tk.Label(root, textvariable=text_var, font=("Arial", 14)).pack(pady=10)
    tk.Label(root, textvariable=score_var, font=("Arial", 14), fg="red").pack(pady=10)
    update()
    root.mainloop()


# 📁 config.py
WHISPER_MODEL = "base"
