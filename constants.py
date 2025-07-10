# constants.py
# constants.py - 설정 상수 모음

RATE = 16000              # 샘플링 레이트
CHANNELS = 1              # 모노 채널
CHUNK_DURATION = 2        # 분석할 오디오 청크 길이 (초 단위)
TEMP_FILENAME = "temp.wav"  # 임시 파일 경로

# 의심 키워드
SUSPICIOUS_KEYWORDS = [
    "계좌", "송금", "비밀번호", "인증번호", "신분증", "보이스피싱", "환불", "사기", "투자", "당첨"
]