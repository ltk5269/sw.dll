# detect_streaming.py
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import wave
import threading
import whisper
import subprocess
import sqlite3
import platform
import tkinter as tk
from tkinter import messagebox

#  설정
CHUNK = 1024
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
TEMP_FILENAME = "temp.wav"
DB_PATH = "phishing_log.db"
SUSPICIOUS_KEYWORDS = ["계좌", "송금", "보안", "인증번호", "공무원", "검찰", "압류"]

latest_text = ""
latest_score = 0

#  오디오 녹음 함수
def record_chunk():
    print("[녹음 시작]")
    recording = sd.rec(int(RATE * RECORD_SECONDS), samplerate=RATE, channels=CHANNELS, dtype='int16')
    sd.wait()
    wav.write(TEMP_FILENAME, RATE, recording)
    print("[녹음 종료]")

#  Whisper 텍스트 변환
model = whisper.load_model("base")
def transcribe_audio(file_path):
    try:
        result = model.transcribe(file_path, language='ko')
        return result.get("text", "")
    except Exception as e:
        print("[Whisper 오류]", e)
        return ""

#  룰 기반 키워드 탐지
def check_rules(text):
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in text:
            return True
    return False

#  LLaMA2 위험도 분석
def score_with_llama(text):
    prompt = f"다음 문장이 보이스피싱일 위험도가 얼마나 되는지 0에서 100 사이 숫자로 말해줘:\n{text}"
    try:
        result = subprocess.run(
            ["ollama", "run", "llama2", prompt],
            capture_output=True,
            text=True,
            timeout=20,
            encoding='utf-8'  # 🧩 인코딩 오류 방지
        )
        stdout = result.stdout or ""
        print("[LLM 응답]", stdout.strip())

        score_str = stdout.strip().split("\n")[-1].strip()
        digits = ''.join(filter(str.isdigit, score_str))
        score = int(digits) if digits else 0

        return min(score, 100)
    except Exception as e:
        print("[LLM 오류]", e)
        return 0

#  DB 저장
def save_log(text, score):
    if not os.path.exists(DB_PATH):
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
        conn.commit()
        conn.close()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (content, risk_score) VALUES (?, ?)", (text, score))
    conn.commit()
    conn.close()

#  알림
def alert_user(message):
    print(f"[ALERT] {message}")
    if platform.system() == "Windows":
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning("경고", message)
            root.destroy()
        except Exception as e:
            print("[알림 오류]", e)
    elif platform.system() == "Darwin":
        os.system(f"osascript -e 'display notification \"{message}\"'")

# 대시보드 업데이트
def update_dashboard(text, score):
    global latest_text, latest_score
    latest_text = text
    latest_score = score

#  상태 전달
def get_latest():
    return latest_text, latest_score

#  오디오 처리 전체 흐름
def process_audio():
    record_chunk()
    text = transcribe_audio(TEMP_FILENAME)
    if os.path.exists(TEMP_FILENAME):
        os.remove(TEMP_FILENAME)

    if not text.strip():
        print("[텍스트 없음]")
        return

    print("[텍스트 변환 결과]", text)

    triggered = False
    if check_rules(text):
        alert_user("[RULE] 의심 키워드 감지됨")
        triggered = True

    score = score_with_llama(text)
    if score >= 70:
        alert_user(f"[LLM] 위험도 {score}% 감지됨")
        triggered = True

    save_log(text, score)
    if triggered:
        update_dashboard(text, score)

#  반복 스트리밍 실행
def start_streaming():
    while True:
        thread = threading.Thread(target=process_audio)
        thread.start()
        thread.join()

#  UI 대시보드
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

#  메인 실행
if __name__ == "__main__":
    threading.Thread(target=start_streaming, daemon=True).start()
    run_dashboard()
