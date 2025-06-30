from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
import torch
import librosa

# 모델 로드
processor = Wav2Vec2Processor.from_pretrained("superb/wav2vec2-base-superb-er")
model = Wav2Vec2ForSequenceClassification.from_pretrained("superb/wav2vec2-base-superb-er")

# 오디오 파일 로드
y, sr = librosa.load("voice_sample.wav", sr=16000)
inputs = processor(y, sampling_rate=sr, return_tensors="pt")

# 예측
with torch.no_grad():
    logits = model(**inputs).logits
    emotion_id = torch.argmax(logits).item()

emotion_labels = model.config.id2label
print("감정 결과:", emotion_labels[emotion_id])
