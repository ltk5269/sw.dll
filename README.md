# config.py
    # 오디오 녹음과 관련된 설정값 정의
CHUNK = 1024  # 한 번에 읽어올 오디오 프레임 수
CHANNELS = 1  # 모노 채널
RATE = 16000  # 샘플링 주파수 (Hz)
RECORD_SECONDS = 5  # 녹음 시간 (초)
TEMP_FILENAME = "temp.wav"  # 임시로 저장할 오디오 파일 이름
DB_PATH = "phishing_log.db"  # SQLite DB 파일 경로
SUSPICIOUS_KEYWORDS = ["계좌", "송금", "보안", "인증번호", "공무원", "검찰", "압류"]  # 의심 키워드 목록


# record.py
    # 마이크로부터 오디오를 녹음하고 WAV 파일로 저장
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from config import RATE, RECORD_SECONDS, TEMP_FILENAME

def record_chunk():
    print("[녹음 시작]")
    # 지정된 시간 동안 오디오 녹음
    recording = sd.rec(int(RATE * RECORD_SECONDS), samplerate=RATE, channels=1, dtype='int16')
    sd.wait()  # 녹음이 끝날 때까지 대기
    wav.write(TEMP_FILENAME, RATE, recording)  # WAV 파일로 저장
    print("[녹음 종료]")


# transcribe.py
    # Whisper 모델을 사용하여 음성을 텍스트로 변환
import whisper
from config import TEMP_FILENAME

model = whisper.load_model("base")  # Whisper base 모델 로드

def transcribe_audio(file_path):
    try:
        # 파일을 한국어로 변환
        result = model.transcribe(file_path, language='ko')
        return result.get("text", "")
    except Exception as e:
        print("[Whisper 오류]", e)
        return ""


# rules.py
    # 의심 키워드가 포함되어 있는지 확인
from config import SUSPICIOUS_KEYWORDS

def check_rules(text):
    # 텍스트 내에 의심 키워드가 하나라도 있으면 True 반환
    return any(keyword in text for keyword in SUSPICIOUS_KEYWORDS)


# llama.py
    # LLaMA2 모델을 통해 위험도 점수를 계산
import subprocess

def score_with_llama(text):
    prompt = f"다음 문장이 보이스피싱일 위험도가 얼마나 되는지 0에서 100 사이 숫자로 말해줘:\n{text}"
    try:
        result = subprocess.run([
            "ollama", "run", "llama2", prompt
        ], capture_output=True, text=True, timeout=20, encoding='utf-8')
        stdout = result.stdout or ""
        score_str = stdout.strip().split("\n")[-1].strip()
        digits = ''.join(filter(str.isdigit, score_str))
        return min(int(digits), 100) if digits else 0
    except Exception as e:
        print("[LLM 오류]", e)
        return 0


# database.py
    # 위험 로그를 SQLite 데이터베이스에 저장
import sqlite3
import os
from config import DB_PATH

def save_log(text, score):
    if not os.path.exists(DB_PATH):
        # DB가 존재하지 않으면 테이블 생성
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

    # DB에 텍스트와 위험도 저장
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (content, risk_score) VALUES (?, ?)", (text, score))
    conn.commit()
    conn.close()


# alert.py
    # 사용자에게 경고를 전달 (윈도우/맥 지원)
import platform
import tkinter as tk
from tkinter import messagebox

def alert_user(message):
    print(f"[ALERT] {message}")
    try:
        if platform.system() == "Windows":
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning("경고", message)
            root.destroy()
        elif platform.system() == "Darwin":  # Mac OS
            os.system(f"osascript -e 'display notification \"{message}\"'")
    except Exception as e:
        print("[알림 오류]", e)


# dashboard.py
    # 위험 텍스트 및 점수를 표시하는 GUI 대시보드
import tkinter as tk
from state import get_latest

def run_dashboard():
    def update():
        # 최근 정보 가져오기
        text, score = get_latest()
        text_var.set(f"최근 텍스트: {text}")
        score_var.set(f"위험 점수: {score}%")
        root.after(3000, update)  # 3초마다 업데이트

    root = tk.Tk()
    root.title("보이스피싱 탐지 대시보드")
    text_var = tk.StringVar()
    score_var = tk.StringVar()

    # 텍스트 및 점수 라벨 생성
    tk.Label(root, textvariable=text_var, font=("Arial", 14)).pack(pady=10)
    tk.Label(root, textvariable=score_var, font=("Arial", 14), fg="red").pack(pady=10)
    update()
    root.mainloop()


# state.py
    # 대시보드에 전달할 최근 텍스트와 점수를 저장
latest_text = ""
latest_score = 0

def update_dashboard(text, score):
    global latest_text, latest_score
    latest_text = text
    latest_score = score

def get_latest():
    return latest_text, latest_score


# main.py
    # 전체 탐지 흐름을 제어하는 메인 실행 파일
import threading
import os
from record import record_chunk
from transcribe import transcribe_audio
from rules import check_rules
from llama import score_with_llama
from database import save_log
from alert import alert_user
from dashboard import run_dashboard
from state import update_dashboard
from config import TEMP_FILENAME

    # 한 주기 음성 분석
def process_audio():
    record_chunk()  # 오디오 녹음
    text = transcribe_audio(TEMP_FILENAME)  # 텍스트 변환
    if os.path.exists(TEMP_FILENAME):
        os.remove(TEMP_FILENAME)  # 임시 파일 삭제

    if not text.strip():
        return  # 아무 텍스트도 없으면 종료

    print("[텍스트 변환 결과]", text)
    triggered = False

    if check_rules(text):
        alert_user("[RULE] 의심 키워드 감지됨")
        triggered = True

    score = score_with_llama(text)
    if score >= 70:
        alert_user(f"[LLM] 위험도 {score}% 감지됨")
        triggered = True

    save_log(text, score)  # 로그 저장
    if triggered:
        update_dashboard(text, score)  # 대시보드 업데이트

    # 연속 실행 루프
def start_streaming():
    while True:
        thread = threading.Thread(target=process_audio)
        thread.start()
        thread.join()

    # 프로그램 시작
if __name__ == "__main__":
    threading.Thread(target=start_streaming, daemon=True).start()
    run_dashboard()
