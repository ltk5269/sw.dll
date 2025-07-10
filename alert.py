  # 사용자에게 경고를 전달 (윈도우/맥 지원)
import os
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
