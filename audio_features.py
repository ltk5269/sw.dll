# audio_features.py
import numpy as np
import librosa
import numpy as np
import librosa

def calculate_features(audio_data, sr):
    """
    오디오에서 ZCR(Zero Crossing Rate)과 Spectral Centroid를 계산
    """
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=audio_data).T)
    sc = np.mean(librosa.feature.spectral_centroid(y=audio_data, sr=sr).T)
    return round(zcr, 4), round(sc, 2)


def calculate_features(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        sc = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        print(f"[AI 분석] ZCR: {zcr:.4f}, SC: {sc:.2f}")
        return zcr, sc
    except Exception as e:
        print("[오디오 특징 추출 오류]", e)
        return 0.1, 1800  # 중립값
