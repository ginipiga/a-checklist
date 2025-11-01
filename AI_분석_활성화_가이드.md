# 🤖 AI 스마트 문서 분석 활성화 가이드

PDF, Word, Excel 파일을 드롭할 때 AI가 문서를 분석하여 **맞춤형 프로젝트 구조**를 자동 생성합니다!

## 🎯 AI 분석의 장점

### 기본 템플릿 (현재)
```
📄 파일명
├─ 📋 프로젝트 개요 (고정된 체크리스트 3개)
├─ 📅 일정 관리 (고정된 체크리스트 3개)
├─ 📄 문서 내용 (원본 텍스트 그대로)
└─ ...
```

### AI 스마트 분석 (활성화 후)
```
📄 신공항 건설 제안서
├─ 🎯 프로젝트 목표 및 범위
│   ├─ ☑ 사업 타당성 분석 완료 (점수: 15)
│   ├─ ☑ 이해관계자 승인 획득 (점수: 20)
│   └─ ☑ 환경영향평가 계획 수립 (점수: 18)
├─ 🏗️ 기술 요구사항
│   ├─ ☑ 활주로 설계 검토 (점수: 12)
│   └─ ☑ 터미널 용량 계산 (점수: 10)
└─ ⚠️ 주요 리스크 및 대응
    ├─ ☑ 예산 초과 리스크 대응 계획 (점수: 15)
    └─ ☑ 공정 지연 방지 방안 수립 (점수: 12)
```

**AI가 자동으로:**
- 문서 유형 파악 (제안서, 계획서, 보고서 등)
- 핵심 내용 추출
- 실행 가능한 체크리스트 생성
- 중요도에 따른 점수 부여
- 논리적인 계층 구조 생성

---

## 📋 활성화 방법

### 옵션 1: Ollama (권장 - 무료, 안전, 오프라인)

**장점:**
- ✅ 완전 무료
- ✅ 데이터가 외부로 전송되지 않음 (개인정보 안전)
- ✅ 인터넷 없이도 작동
- ✅ API 키 불필요

**단점:**
- ⚠️ 초기 설정 필요
- ⚠️ 약간의 컴퓨터 성능 필요

#### 1단계: Ollama 설치
1. https://ollama.com 방문
2. Windows용 다운로드 및 설치

#### 2단계: 모델 다운로드
```bash
ollama pull llama3.2:latest
```

#### 3단계: 환경변수 설정
`set_llm_ollama.bat` 파일 생성:
```batch
@echo off
set LLM_MODE=ollama
echo Ollama 스마트 분석 모드 활성화!
call 실행.bat
```

실행: `set_llm_ollama.bat`

---

### 옵션 2: OpenAI (정확하지만 비용 발생)

**장점:**
- ✅ 매우 정확한 분석
- ✅ 설정 간단

**단점:**
- ⚠️ API 사용료 발생 (문서당 약 $0.01-0.05)
- ⚠️ 문서 내용이 OpenAI 서버로 전송됨
- ⚠️ 인터넷 필요

#### 1단계: OpenAI API 키 발급
1. https://platform.openai.com 가입
2. API Keys 페이지에서 키 생성
3. 결제 수단 등록 필요

#### 2단계: 환경변수 설정
`set_llm_openai.bat` 파일 생성:
```batch
@echo off
set OPENAI_API_KEY=sk-your-api-key-here
set LLM_MODE=openai
echo OpenAI 스마트 분석 모드 활성화!
echo 주의: 문서 내용이 OpenAI 서버로 전송됩니다.
call 실행.bat
```

**중요:** `sk-your-api-key-here`를 실제 API 키로 교체하세요!

실행: `set_llm_openai.bat`

---

## 🔧 코드에서 직접 활성화

프로세서 초기화 시 `use_template=True`와 함께 LLM 모드를 설정하세요:

### PDF 프로세서
```python
from utils.pdf_processor import PDFProcessor

# Ollama 사용
processor = PDFProcessor(use_template=True)
# 환경변수 LLM_MODE=ollama 설정 필요

# 또는 OpenAI 사용
# 환경변수 LLM_MODE=openai, OPENAI_API_KEY=sk-xxx 설정 필요
```

### 템플릿 매니저 직접 사용
```python
from utils.template_manager import TemplateManager
import os

# Ollama 사용
os.environ['LLM_MODE'] = 'ollama'
manager = TemplateManager(use_smart_analysis=True, llm_mode='ollama')

# OpenAI 사용
os.environ['LLM_MODE'] = 'openai'
os.environ['OPENAI_API_KEY'] = 'sk-your-api-key'
manager = TemplateManager(use_smart_analysis=True, llm_mode='openai')

# 문서 분석
result = manager.create_project_from_file("제안서.pdf", content)
```

---

## ✅ 테스트

1. AI 분석 활성화 후 프로그램 실행
2. PDF/Word/Excel 파일을 드래그 앤 드롭
3. 콘솔에서 다음 메시지 확인:
   - `🤖 AI가 문서를 분석하여 최적의 프로젝트 구조를 생성합니다...`
   - `✅ AI 분석 완료! 맞춤형 프로젝트 구조가 생성되었습니다.`

---

## 🆚 비교표

| 기능 | 기본 템플릿 | Ollama | OpenAI |
|-----|-----------|--------|--------|
| 비용 | 무료 | 무료 | 유료 ($) |
| 개인정보 | 안전 | 안전 | 주의 |
| 정확도 | 보통 | 좋음 | 최고 |
| 맞춤화 | ❌ | ✅ | ✅ |
| 인터넷 | 불필요 | 불필요 | 필요 |
| 설정 난이도 | 쉬움 | 보통 | 쉬움 |

---

## 💡 추천

- **개인 프로젝트/민감한 문서**: Ollama 사용
- **중요한 비즈니스 문서**: OpenAI 사용
- **빠른 시작**: 기본 템플릿 사용 후 나중에 AI 활성화

---

## 🛠️ 문제 해결

### Ollama 연결 실패
```
⚠️ Ollama 서버에 연결할 수 없습니다.
```
→ Ollama가 실행 중인지 확인: `ollama serve`

### OpenAI API 오류
```
⚠️ OpenAI 분석 오류: Authentication failed
```
→ API 키 확인 및 결제 수단 등록 확인

### LLM 모드가 활성화되지 않음
→ 환경변수가 올바르게 설정되었는지 확인
→ 프로그램 재시작

---

## 📚 참고 자료

- [Ollama 공식 문서](https://ollama.com)
- [OpenAI API 문서](https://platform.openai.com/docs)
- [시스템 프롬프트 커스터마이징](src/utils/smart_template_processor.py)
