    # 오디오 녹음과 관련된 설정값 정의
CHUNK = 1024  # 한 번에 읽어올 오디오 프레임 수
CHANNELS = 1  # 모노 채널
RATE = 16000  # 샘플링 주파수 (Hz)
RECORD_SECONDS = 5  # 녹음 시간 (초)
TEMP_FILENAME = "temp.wav"  # 임시로 저장할 오디오 파일 이름
DB_PATH = "phishing_log.db"  # SQLite DB 파일 경로
SUSPICIOUS_KEYWORDS = ["계좌", "송금", "보안", "인증번호", "공무원", "검찰", "압류"]  # 의심 키워드 목록
