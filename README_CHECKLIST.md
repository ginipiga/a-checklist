# 체크리스트 변환 및 가중치 평가 시스템

## 개요

이 시스템은 문서를 읽어서 자동으로 체크리스트 항목을 추출하고, 각 항목의 중요도를 5가지 평가축을 기반으로 가중치 평가하는 시스템입니다.

## 시스템 작성 방법

### 1. 시스템 프롬프트 ([config/checklist_system_prompt.md](config/checklist_system_prompt.md))

시스템 프롬프트에는 다음 내용이 포함되어 있습니다:

**평가축 정의 (각 1-5점)**
- **C1. 승인/법규 관문성** (가중치 30%): 인허가나 법정계획 불일치 시 사업이 멈추는가?
- **C2. 비용/일정 영향** (가중치 25%): CAPEX/OPEX, 공정 지연 파급이 큰가?
- **C3. 환경·안전 영향** (가중치 20%): EIA·민원·안전과 직결되는가?
- **C4. 운영성 영향** (가중치 15%): 공항 용량·품질(OTP, 수하물/항공기 회전율)에 미치는가?
- **C5. 대체/가역성** (가중치 10%): 뒤늦게 수정이 어려운가?

**가중치 적용**
```python
w = [0.30, 0.25, 0.20, 0.15, 0.10]  # 각각 C1~C5
```

**기본점수 계산**
```python
S_base = Σ(w_k × score(Ck))  # 범위: 1.0~5.0
```

**보정계수**
- **U (불확실성/성숙도)**: 0.9, 1.0, 1.1, 1.2
- **D (의존성/허브성)**: 1.0, 1.1, 1.2
- **G (규제 게이트 플래그)**: 0.0 또는 0.5

**최종점수 산식**
```python
S_final_raw = S_base × U × D + G
S_final = min(5, max(1, round_half_up(S_final_raw)))
```

### 2. 문서 분석 모듈 ([src/utils/document_analyzer.py](src/utils/document_analyzer.py))

이 모듈은 PDF, Word, 텍스트 파일을 읽어서 체크리스트 항목을 추출합니다.

**주요 기능:**
- PDF/Word/텍스트 파일에서 텍스트 추출
- 키워드 기반으로 문장을 카테고리별로 분류
- 실행 가능한 항목(actionable items) 식별
- 체크리스트 후보 생성

**키워드 분류:**
- 승인: 승인, 인허가, 허가, 면허 등
- 비용: 비용, CAPEX, OPEX, 예산 등
- 일정: 일정, 공정, 기한, 납기 등
- 환경: 환경, EIA, 환경영향평가, 소음 등
- 안전: 안전, 위험, 사고, 재해 등
- 운영: 운영, OTP, 수하물, 회전율 등
- 설계: 설계, 구조, 배치, 레이아웃 등
- 계획: 계획, 전략, 방침, 정책 등

### 3. 가중치 평가 엔진 ([src/utils/weight_evaluator.py](src/utils/weight_evaluator.py))

이 모듈은 체크리스트 항목의 중요도 가중치를 계산합니다.

**주요 기능:**
- 5가지 평가축 점수 입력받기
- 가중치 적용하여 기본점수 계산
- 보정계수 적용하여 최종점수 계산
- 우선순위 분류 (Critical, High, Medium, Low, Minimal)
- 권장사항 생성

**계산 예시:**
```python
from src.utils.weight_evaluator import WeightEvaluator

evaluator = WeightEvaluator()

evaluation = evaluator.evaluate_checklist_item(
    c1_score=5, c1_rationale="법정 필수 승인",
    c2_score=4, c2_rationale="공정 지연 2-3개월",
    c3_score=5, c3_rationale="환경평가 핵심",
    c4_score=2, c4_rationale="간접적 영향",
    c5_score=5, c5_rationale="변경 불가능",
    uncertainty_factor=1.0,
    dependency_factor=1.2,
    regulatory_gate_flag=0.5
)

# 결과:
# - 기본점수: 4.4
# - 최종점수(raw): 5.78
# - 최종점수: 5 (Critical)
```

### 4. 통합 모듈 ([src/utils/checklist_converter.py](src/utils/checklist_converter.py))

문서 분석과 가중치 평가를 통합하여 전체 프로세스를 관리합니다.

**주요 기능:**
- 문서 분석 수행
- 평가 템플릿 생성
- 항목 평가 수행
- JSON 형식으로 결과 저장

## 사용 방법

### 설치

```bash
cd risk-management-system
pip install -r requirements.txt
```

### 명령행 사용

**1. 템플릿 생성 (수동 평가용)**
```bash
cd src/utils
python checklist_converter.py ../../test_risk_management.pdf
```

**2. 자동 평가**
```bash
python checklist_converter.py ../../test_risk_management.pdf --auto
```

**3. 템플릿 수정 후 평가**
```bash
# 1단계: 템플릿 생성
python checklist_converter.py document.pdf -t

# 2단계: JSON 파일에서 점수 수정

# 3단계: 평가 수행
python checklist_converter.py -e document_checklist.json
```

### Python 코드에서 사용

```python
from src.utils.checklist_converter import ChecklistConverter

converter = ChecklistConverter()

# 문서 처리
result = converter.process_document(
    file_path="document.pdf",
    output_path="output.json",
    auto_evaluate=True  # 자동 평가
)

print(f"총 {result['summary']['total_items']}개 항목")
print(f"Critical: {result['summary']['critical']}개")
```

### 예시 실행

```bash
python examples/checklist_example.py
```

이 예시는 다음을 시연합니다:
1. 기본 가중치 평가
2. 여러 항목 평가
3. 문서 분석 (PDF가 있는 경우)

## 출력 예시

### 예시 1: 활주로 용량 분석

```
항목: 활주로 용량 분석 수행
카테고리: 인프라 계획

평가 점수:
  C1 (승인/법규): 4점
  C2 (비용/일정): 5점
  C3 (환경/안전): 3점
  C4 (운영성): 5점
  C5 (가역성): 4점

계산 과정:
  기본점수: 4.2
  불확실성 계수: 1.1
  의존성 계수: 1.2
  규제 게이트 플래그: 0.0
  최종점수(raw): 5.54
  최종점수: 5

결과:
  우선순위: Critical
  권장사항: 즉시 검토 및 조치 필요
```

### 예시 2: 여러 항목 평가

```
항목 1: 환경영향평가 승인 획득
  카테고리: 승인/규제
  최종점수: 5
  우선순위: Critical
  권장사항: 즉시 검토 및 조치 필요

항목 2: 터미널 레이아웃 최종 확정
  카테고리: 설계
  최종점수: 4
  우선순위: High
  권장사항: 빠른 시일 내 검토 필요

항목 3: IT 시스템 벤더 선정
  카테고리: 운영
  최종점수: 2
  우선순위: Low
  권장사항: 여유 있을 때 검토
```

## JSON 출력 구조

### 평가 결과 JSON

```json
{
  "status": "evaluated",
  "file_name": "document.pdf",
  "checklist_items": [
    {
      "id": 1,
      "category": "승인/규제",
      "item": "환경영향평가 승인 획득",
      "evaluation": {
        "C1_approval": {"score": 5, "rationale": "법정 필수 승인으로..."},
        "C2_cost_schedule": {"score": 4, "rationale": "승인 지연 시..."},
        "C3_environment_safety": {"score": 5, "rationale": "환경영향평가의..."},
        "C4_operation": {"score": 2, "rationale": "운영에는..."},
        "C5_reversibility": {"score": 5, "rationale": "승인 후..."},
        "base_score": 4.4,
        "uncertainty_factor": 1.0,
        "dependency_factor": 1.2,
        "regulatory_gate_flag": 0.5,
        "final_score_raw": 5.78,
        "final_score": 5
      },
      "priority": "Critical",
      "recommendation": "즉시 검토 및 조치 필요"
    }
  ],
  "summary": {
    "total_items": 10,
    "critical": 3,
    "high": 4,
    "medium": 2,
    "low": 1,
    "minimal": 0
  }
}
```

## 파일 구조

```
risk-management-system/
├── config/
│   └── checklist_system_prompt.md    # 시스템 프롬프트 (평가 기준 정의)
├── src/
│   └── utils/
│       ├── document_analyzer.py      # 문서 분석 모듈
│       ├── weight_evaluator.py       # 가중치 평가 엔진
│       └── checklist_converter.py    # 통합 모듈
├── examples/
│   └── checklist_example.py          # 사용 예시
├── docs/
│   └── CHECKLIST_CONVERTER_GUIDE.md  # 상세 가이드
└── README_CHECKLIST.md               # 이 문서
```

## 상세 문서

더 자세한 사용 방법은 [docs/CHECKLIST_CONVERTER_GUIDE.md](docs/CHECKLIST_CONVERTER_GUIDE.md)를 참조하세요.

## 평가 기준 커스터마이징

평가 기준을 변경하려면 다음 파일들을 수정하세요:

1. **가중치 변경**: [src/utils/weight_evaluator.py](src/utils/weight_evaluator.py)의 `WEIGHTS` 딕셔너리
2. **키워드 변경**: [src/utils/document_analyzer.py](src/utils/document_analyzer.py)의 `keywords` 딕셔너리
3. **평가 기준 설명**: [config/checklist_system_prompt.md](config/checklist_system_prompt.md)

## 예시 출력

실제 실행 결과:

```
================================================================================
체크리스트 변환기 사용 예시
================================================================================

================================================================================
예시 1: 기본 가중치 평가
================================================================================
항목: 활주로 용량 분석 수행
카테고리: 인프라 계획

평가 점수:
  C1 (승인/법규): 4점
  C2 (비용/일정): 5점
  C3 (환경/안전): 3점
  C4 (운영성): 5점
  C5 (가역성): 4점

계산 과정:
  기본점수: 4.2
  불확실성 계수: 1.1
  의존성 계수: 1.2
  규제 게이트 플래그: 0.0
  최종점수(raw): 5.54
  최종점수: 5

결과:
  우선순위: Critical
  권장사항: 즉시 검토 및 조치 필요
```

## 라이센스

이 시스템은 risk-management-system 프로젝트의 일부입니다.
