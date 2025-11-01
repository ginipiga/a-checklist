# LLM 기반 문서 구조 분석 가이드

## 개요

Word, Excel, PDF 파일을 드래그 앤 드롭할 때 **LLM(GPT)을 사용하여 문서 구조를 더 정확하게 파악**할 수 있습니다.

기존 규칙 기반 방식보다 훨씬 정확하게:
- 제목과 본문 구분
- 체크리스트 항목 추출
- 계층 구조 생성

## 설정 방법

### 1. OpenAI API 키 발급

1. [OpenAI 플랫폼](https://platform.openai.com/)에 가입
2. API Keys 메뉴에서 새 API 키 생성
3. 생성된 키를 복사 (예: `sk-proj-...`)

### 2. 환경 변수 설정

#### Windows (PowerShell)
```powershell
# 현재 세션만
$env:OPENAI_API_KEY = "sk-proj-여기에-본인의-API-키-입력"
$env:USE_LLM_ANALYSIS = "true"

# 영구 설정 (시스템 환경 변수)
[System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-proj-여기에-본인의-API-키-입력", "User")
[System.Environment]::SetEnvironmentVariable("USE_LLM_ANALYSIS", "true", "User")
```

#### Windows (CMD)
```cmd
set OPENAI_API_KEY=sk-proj-여기에-본인의-API-키-입력
set USE_LLM_ANALYSIS=true
```

#### Mac/Linux
```bash
export OPENAI_API_KEY="sk-proj-여기에-본인의-API-키-입력"
export USE_LLM_ANALYSIS="true"

# 영구 설정 (~/.bashrc 또는 ~/.zshrc에 추가)
echo 'export OPENAI_API_KEY="sk-proj-여기에-본인의-API-키-입력"' >> ~/.bashrc
echo 'export USE_LLM_ANALYSIS="true"' >> ~/.bashrc
```

### 3. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

또는 openai만 설치:
```bash
pip install openai
```

## 사용 방법

### 기본 사용

1. 환경 변수 설정 완료
2. 프로그램 실행
3. Word/Excel/PDF 파일을 드래그 앤 드롭
4. LLM이 자동으로 문서 구조를 분석하여 체크리스트 생성

### LLM 비활성화

LLM을 사용하지 않고 기존 규칙 기반 방식을 사용하려면:

```powershell
# Windows
$env:USE_LLM_ANALYSIS = "false"

# Mac/Linux
export USE_LLM_ANALYSIS="false"
```

또는 환경 변수를 설정하지 않으면 기본적으로 비활성화됩니다.

## LLM 모드 vs 기본 모드 비교

### 기본 모드 (규칙 기반)
- **장점**: 무료, 빠름, 인터넷 불필요
- **단점**:
  - 폰트 크기, 굵기만 보고 판단
  - 복잡한 문서는 정확도 낮음
  - 문맥을 이해하지 못함

### LLM 모드 (GPT 기반)
- **장점**:
  - 문맥을 이해하여 정확한 분류
  - 실행 가능한 체크리스트만 추출
  - 복잡한 문서도 정확히 파악
- **단점**:
  - API 비용 발생 (문서당 약 $0.01~0.05)
  - 인터넷 연결 필요
  - 처리 시간 약간 증가 (5~10초)

## 비용

OpenAI API 요금 (2024년 기준):
- **gpt-4o-mini** (기본 모델):
  - 입력: $0.15 / 1M 토큰
  - 출력: $0.60 / 1M 토큰
  - 일반 문서 1개당 약 **$0.01~0.03**

- **gpt-4o** (고급 모델):
  - 입력: $2.50 / 1M 토큰
  - 출력: $10.00 / 1M 토큰
  - 일반 문서 1개당 약 **$0.10~0.30**

**권장**: 대부분의 경우 `gpt-4o-mini`로 충분합니다.

## 모델 변경

더 정확한 분석이 필요하면 `gpt-4o` 사용:

[src/utils/llm_analyzer.py](src/utils/llm_analyzer.py) 파일에서:
```python
def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
```

↓ 변경

```python
def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
```

## 시스템 프롬프트 커스터마이징

문서 분석 규칙을 수정하려면:

[config/document_structure_prompt.md](config/document_structure_prompt.md) 파일을 편집하세요.

예:
- 체크리스트 판단 기준 변경
- 계층 구조 규칙 수정
- 카테고리 추가/삭제

## 문제 해결

### "OPENAI_API_KEY 환경변수가 설정되지 않았습니다"
→ 환경 변수를 올바르게 설정했는지 확인
→ 프로그램을 재시작해보세요

### "LLM 분석 실패, 기본 모드로 전환합니다"
→ API 키가 유효한지 확인
→ 인터넷 연결 확인
→ OpenAI 계정에 크레딧이 있는지 확인

### LLM 모드가 활성화되지 않음
→ `USE_LLM_ANALYSIS=true` 설정 확인
→ `openai` 패키지 설치 확인: `pip install openai`

## 예시: 분석 결과 차이

### 입력 문서:
```
프로젝트 배경
본 프로젝트는 공항 확장을 목표로 한다.
- 환경영향평가 승인 획득
- 주민 설명회 개최
```

### 기본 모드 결과:
```
[제목] 프로젝트 배경
[본문] 본 프로젝트는 공항 확장을 목표로 한다.
[체크리스트] 환경영향평가 승인 획득
[체크리스트] 주민 설명회 개최
```

### LLM 모드 결과:
```
[제목] 프로젝트 배경
[본문] 본 프로젝트는 공항 확장을 목표로 한다.
[체크리스트] 환경영향평가 승인 획득 (카테고리: 승인/규제)
[체크리스트] 주민 설명회 개최 (카테고리: 이해관계자)
```

LLM은 각 항목의 의미를 파악하여 적절한 카테고리를 자동으로 지정합니다.

## 보안 주의사항

- API 키는 절대 공개 저장소에 커밋하지 마세요
- `.gitignore`에 `.env` 파일 추가 권장
- 회사 기밀 문서는 OpenAI 정책 확인 후 사용하세요

## 참고

- [OpenAI API 문서](https://platform.openai.com/docs)
- [요금 안내](https://openai.com/pricing)
- [사용량 확인](https://platform.openai.com/usage)
