 # 위험 텍스트 및 점수를 표시하는 GUI 대시보드
import time
import threading
import tkinter as tk

latest_text = ""
latest_score = 0

def run_dashboard(get_latest_func):  # ← 여기서 함수 인자 받도록 수정
    def update():
        while True:
            global latest_text, latest_score
            latest_text, latest_score = get_latest_func()
            time.sleep(1)

    def refresh_ui():
        text_label.config(text=f"최근 텍스트:\n{latest_text}")
        score_label.config(text=f"위험도 점수: {latest_score}%")
        root.after(1000, refresh_ui)

    threading.Thread(target=update, daemon=True).start()

    root = tk.Tk()
    root.title("AI 보이스피싱 탐지 대시보드")
    root.geometry("400x200")

    text_label = tk.Label(root, text="", wraplength=380, justify="left", font=("맑은 고딕", 12))
    text_label.pack(pady=10)

    score_label = tk.Label(root, text="", font=("맑은 고딕", 14, "bold"))
    score_label.pack(pady=10)

    refresh_ui()
    root.mainloop()