#  main.py
from stream_audio import start_streaming  # 오디오 스트리밍 시작 함수
from dashboard import run_dashboard  # UI 대시보드 함수
import threading

if __name__ == "__main__":
    # 스트리밍은 별도 스레드로 실행
    threading.Thread(target=start_streaming, daemon=True).start()
    # 메인 스레드에서는 대시보드 실행
    run_dashboard()


#  stream_audio.py
import pyaudio  # 오디오 입력 처리
import wave     # 오디오 파일 저장
import threading
from whisper_wrap import transcribe_audio  # Whisper로 텍스트 변환
from rule_engine import check_rules        # 키워드 탐지
from llama_checker import check_with_llama, score_with_llama  # 위험 점수 분석
from database import save_log              # 로그 저장
from notifier import alert_user, update_dashboard  # 알림과 대시보드 갱신
import os

    # 오디오 녹음 파라미터
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
TEMP_FILENAME = "temp.wav"

    # 오디오 5초 녹음
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

    # 전체 오디오 처리 흐름
def process_audio():
    record_chunk()  # 5초 녹음
    text = transcribe_audio(TEMP_FILENAME)  # 텍스트 변환
    os.remove(TEMP_FILENAME)  # 임시파일 삭제
    if not text.strip():  # 아무 말 없으면 무시
        return

    triggered = False
    if check_rules(text):  # 키워드 탐지
        alert_user("[RULE] 의심 키워드 감지됨")
        triggered = True
    score = score_with_llama(text)  # LLM 기반 위험 점수
    if score >= 70:
        alert_user(f"[LLM] 위험도 {score}% 탐지됨")
        triggered = True

    save_log(text, score)  # DB 저장
    if triggered:
        update_dashboard(text, score)  # UI 갱신

    # 5초마다 반복 실행
def start_streaming():
    while True:
        thread = threading.Thread(target=process_audio)
        thread.start()
        thread.join()


#  whisper_wrap.py
import whisper

    # Whisper 모델 로드 (base 모델 사용)
model = whisper.load_model("base")

    # 오디오 파일 → 텍스트 변환
def transcribe_audio(file_path):
    result = model.transcribe(file_path, language='ko')  # 한국어 인식
    return result.get("text", "")


#  rule_engine.py
import re

    # 의심 키워드 리스트
SUSPICIOUS_KEYWORDS = ["계좌", "송금", "보안", "인증번호", "공무원", "검찰", "압류"]

    # 텍스트 내 키워드 존재 여부 탐지
def check_rules(text):
    for keyword in SUSPICIOUS_KEYWORDS:
        if re.search(keyword, text):
            return True
    return False


#  llama_checker.py
import subprocess

    # llama2로 yes/no 보이스피싱 여부 판단
def check_with_llama(text):
    prompt = f"다음 문장이 보이스피싱일 가능성이 있는지 간단히 yes/no로 답해줘: {text}"
    try:
        result = subprocess.run([
            "ollama", "run", "llama2", prompt
        ], capture_output=True, text=True, timeout=20)
        return "yes" in result.stdout.lower()
    except:
        return False

    # llama2로 0~100 위험 점수 반환
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


#  database.py
import sqlite3
import os

DB_PATH = "data/phishing_log.db"

    # data 폴더 없으면 생성
if not os.path.exists("data"):
    os.makedirs("data")

    # 텍스트와 점수 DB에 저장
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


#  notifier.py
import platform
import os
import tkinter as tk
from tkinter import messagebox

latest_text = ""
latest_score = 0

    # OS별 알림 띄우기
def alert_user(message):
    if platform.system() == "Windows":
        os.system(f"msg * {message}")
    elif platform.system() == "Darwin":
        os.system(f"osascript -e 'display notification \"{message}\"'")
    else:
        print("[경고]", message)

    # 대시보드 값 갱신
def update_dashboard(text, score):
    global latest_text, latest_score
    latest_text = text
    latest_score = score

    # 현재 상태 전달
def get_latest():
    return latest_text, latest_score


#  dashboard.py
import tkinter as tk
from notifier import get_latest

    # Tkinter 기반 실시간 UI 표시

def run_dashboard():
    def update():
        text, score = get_latest()
        text_var.set(f"최근 텍스트: {text}")
        score_var.set(f"위험 점수: {score}%")
        root.after(3000, update)  # 3초마다 갱신

    root = tk.Tk()
    root.title("보이스피싱 탐지 대시보드")
    text_var = tk.StringVar()
    score_var = tk.StringVar()

    tk.Label(root, textvariable=text_var, font=("Arial", 14)).pack(pady=10)
    tk.Label(root, textvariable=score_var, font=("Arial", 14), fg="red").pack(pady=10)
    update()
    root.mainloop()


#  config.py
WHISPER_MODEL = "base"  # 향후 설정 분리 시 활용 가능
