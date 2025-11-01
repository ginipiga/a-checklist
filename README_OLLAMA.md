# 🔒 로컬 AI (Ollama) 사용 가이드

## 왜 로컬 AI인가?

### ✅ 장점
- **완벽한 보안**: 문서가 절대 외부로 나가지 않음
- **완전 무료**: API 비용 없음
- **인터넷 불필요**: 오프라인에서도 작동
- **빠른 속도**: 네트워크 지연 없음
- **프라이버시**: 회사 기밀, 개인정보 걱정 없음

### ⚠️ 단점
- 초기 설정 필요 (5분)
- GPU가 있으면 좋음 (CPU로도 가능)
- 디스크 공간 필요 (모델당 4~7GB)

---

## 1️⃣ Ollama 설치

### Windows
1. https://ollama.com/download 접속
2. "Download for Windows" 클릭
3. 다운로드한 `OllamaSetup.exe` 실행
4. 설치 완료!

### Mac
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## 2️⃣ 모델 다운로드

터미널(명령 프롬프트)을 열고:

### 추천 모델: Qwen2.5 (한국어 우수)
```bash
ollama pull qwen2.5:7b
```
- 크기: 약 4.7GB
- 한국어 문서 분석에 최적화
- **강력 추천!**

### 대안 1: Llama 3.1 (영어 우수)
```bash
ollama pull llama3.1:8b
```
- 크기: 약 4.9GB
- 영어 문서에 적합

### 대안 2: Gemma 2 (경량화)
```bash
ollama pull gemma2:9b
```
- 크기: 약 5.4GB
- 균형잡힌 성능

**참고**: 처음 다운로드 시 시간이 걸립니다 (5~15분).

---

## 3️⃣ Ollama 실행

### Windows
- Ollama를 설치하면 자동으로 백그라운드에서 실행됩니다
- 시스템 트레이에서 Ollama 아이콘 확인

수동 실행 필요 시:
```cmd
ollama serve
```

### Mac/Linux
```bash
ollama serve
```

**확인**: 브라우저에서 http://localhost:11434 접속 시 "Ollama is running" 메시지가 보이면 성공!

---

## 4️⃣ 위험관리시스템에서 사용

### 환경 변수 설정

#### Windows (PowerShell)
```powershell
$env:LLM_MODE = "ollama"
```

#### Windows (CMD)
```cmd
set LLM_MODE=ollama
```

#### Mac/Linux
```bash
export LLM_MODE=ollama
```

### 프로그램 실행
```bash
python src/main.py
```

### 확인
Word/Excel/PDF 파일을 드래그 앤 드롭 시:
```
✅ 로컬 LLM(Ollama) 문서 분석 모드 활성화 - 데이터 유출 걱정 없음!
📄 OLLAMA LLM으로 문서 구조 분석 중...
✅ LLM 분석 완료
```

메시지가 표시되면 성공!

---

## 5️⃣ 모델 변경

다른 모델을 사용하려면 [src/utils/local_llm_analyzer.py](src/utils/local_llm_analyzer.py) 파일에서:

```python
def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
```

↓ 원하는 모델로 변경

```python
def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
```

---

## 6️⃣ 문제 해결

### "Ollama가 실행되지 않았습니다"
**해결책:**
1. 터미널에서 `ollama serve` 실행
2. http://localhost:11434 접속 확인
3. Windows의 경우 작업 관리자에서 ollama.exe 프로세스 확인

### "모델을 찾을 수 없습니다"
**해결책:**
```bash
# 다운로드된 모델 확인
ollama list

# 모델 다운로드
ollama pull qwen2.5:7b
```

### 분석이 너무 느림
**해결책:**
- GPU가 있으면 자동으로 사용됩니다
- CPU만 있으면 시간이 더 걸립니다 (문서당 30초~1분)
- 더 작은 모델 사용: `ollama pull qwen2.5:3b`

### 메모리 부족
**해결책:**
- 더 작은 모델 사용
- 다른 프로그램 종료
- Ollama 재시작: `ollama serve`

---

## 7️⃣ 성능 비교

| 모델 | 크기 | 한국어 | 영어 | 속도 | 추천도 |
|------|------|--------|------|------|--------|
| qwen2.5:7b | 4.7GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ 강력 추천 |
| llama3.1:8b | 4.9GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 영어 문서용 |
| gemma2:9b | 5.4GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 균형잡힌 성능 |
| qwen2.5:3b | 2GB | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 저사양 PC용 |

---

## 8️⃣ LLM 모드 비교

| 모드 | 보안 | 비용 | 정확도 | 속도 | 인터넷 | 권장 상황 |
|------|------|------|--------|------|--------|----------|
| **ollama** | ✅✅✅ | 무료 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 불필요 | **회사 기밀 문서** |
| openai | ⚠️ | 유료 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 필요 | 개인 문서 |
| none | ✅ | 무료 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 불필요 | 단순 문서 |

---

## 9️⃣ 사용 팁

### GPU 가속 확인
```bash
# Ollama가 GPU를 사용하는지 확인
ollama ps
```

### 모델 삭제 (디스크 공간 확보)
```bash
ollama rm qwen2.5:7b
```

### 여러 모델 동시 다운로드
```bash
ollama pull qwen2.5:7b & ollama pull llama3.1:8b
```

### 성능 모니터링
```bash
# Ollama 로그 확인
ollama logs
```

---

## 🔟 FAQ

**Q: Ollama는 완전히 오프라인인가요?**
A: 네! 모델을 한 번 다운로드하면 인터넷 없이 사용 가능합니다.

**Q: GPU가 없어도 되나요?**
A: 네! CPU로도 작동합니다. 다만 속도가 느립니다.

**Q: 여러 모델을 설치해도 되나요?**
A: 네! 디스크 공간만 있으면 여러 모델 설치 가능합니다.

**Q: OpenAI보다 정확도가 떨어지나요?**
A: 조금 떨어질 수 있지만, 대부분의 경우 충분히 정확합니다.

**Q: 상업적으로 사용해도 되나요?**
A: 네! Ollama와 대부분의 모델은 상업적 사용 가능합니다.

---

## 📚 참고 자료

- [Ollama 공식 사이트](https://ollama.com)
- [Ollama 모델 라이브러리](https://ollama.com/library)
- [Qwen2.5 모델 정보](https://ollama.com/library/qwen2.5)
- [Llama 3.1 모델 정보](https://ollama.com/library/llama3.1)

---

## 🎯 빠른 시작 요약

```bash
# 1. Ollama 설치
# https://ollama.com/download

# 2. 모델 다운로드
ollama pull qwen2.5:7b

# 3. 환경 변수 설정 (Windows PowerShell)
$env:LLM_MODE = "ollama"

# 4. 프로그램 실행
python src/main.py

# 5. Word/Excel/PDF 드래그 앤 드롭!
```

**데이터 유출 걱정 없이 정확한 문서 분석을 즐기세요! 🎉**
