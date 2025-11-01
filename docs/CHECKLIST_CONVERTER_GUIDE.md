# 체크리스트 변환기 사용 가이드

## 개요

이 시스템은 공항 프로젝트 문서(PDF, Word, 텍스트)를 분석하여 자동으로 체크리스트 항목을 추출하고, 각 항목의 중요도 가중치를 평가합니다.

## 주요 기능

1. **문서 분석**: PDF, Word, 텍스트 파일에서 주요 의사결정 항목을 자동 추출
2. **체크리스트 변환**: 추출된 항목을 체크리스트 형식으로 변환
3. **가중치 평가**: 5가지 평가축(C1~C5)을 기반으로 중요도 점수 계산
4. **우선순위 분류**: Critical, High, Medium, Low, Minimal로 우선순위 자동 분류
5. **JSON 출력**: 구조화된 JSON 형식으로 결과 저장

## 설치

### 필수 패키지 설치

```bash
pip install PyPDF2 python-docx
```

또는 requirements.txt가 있다면:

```bash
pip install -r requirements.txt
```

## 사용 방법

### 1. 기본 사용 (템플릿 생성)

문서를 분석하여 평가 템플릿만 생성합니다. 이후 수동으로 점수를 입력할 수 있습니다.

```bash
cd src/utils
python checklist_converter.py ../../test_risk_management.pdf
```

출력: `test_risk_management_checklist.json` (템플릿)

### 2. 자동 평가 모드

기본 점수(모두 3점)로 자동 평가를 수행합니다.

```bash
python checklist_converter.py ../../test_risk_management.pdf --auto
```

### 3. 출력 경로 지정

```bash
python checklist_converter.py ../../test_risk_management.pdf -o ../../output/result.json
```

### 4. 템플릿 수정 후 평가

1단계: 템플릿 생성
```bash
python checklist_converter.py document.pdf -t
```

2단계: JSON 파일을 열고 각 항목의 점수를 수정
```json
{
  "evaluation_input": {
    "C1_score": 5,  // 1-5로 수정
    "C1_rationale": "법정 필수 승인으로 미획득 시 사업 진행 불가",
    "C2_score": 4,
    "C2_rationale": "승인 지연 시 공정 지연 2-3개월 예상",
    ...
  }
}
```

3단계: 수정된 템플릿 평가
```bash
python checklist_converter.py -e document_checklist.json
```

## 평가 기준

### 평가축 (1-5점)

**C1. 승인/법규 관문성** (가중치 30%)
- 5점: 사업 진행 불가
- 4점: 중요한 승인 지연
- 3점: 보완 조치 필요
- 2점: 간접적 영향
- 1점: 무관

**C2. 비용/일정 영향** (가중치 25%)
- 5점: CAPEX 20% 이상, 지연 3개월 이상
- 4점: CAPEX 10-20%, 지연 1-3개월
- 3점: CAPEX 5-10%, 지연 2주-1개월
- 2점: CAPEX 5% 미만, 지연 1-2주
- 1점: 영향 미미

**C3. 환경·안전 영향** (가중치 20%)
- 5점: EIA 불통과, 중대 사고 위험
- 4점: 환경규제 위반 가능성
- 3점: 보완 조치 필요
- 2점: 경미한 고려사항
- 1점: 무관

**C4. 운영성 영향** (가중치 15%)
- 5점: OTP 10% 이상 저하
- 4점: OTP 5-10% 저하
- 3점: OTP 2-5% 저하
- 2점: 경미한 영향
- 1점: 무관

**C5. 대체/가역성** (가중치 10%)
- 5점: 수정 불가능
- 4점: 수정 매우 어려움
- 3점: 상당한 시간/비용 소요
- 2점: 비교적 용이
- 1점: 쉽게 변경 가능

### 보정계수

**불확실성 계수 (U)**
- 1.2: 근거 매우 빈약, 변동성 매우 큼
- 1.1: 근거 부족, 변동성 큼
- 1.0: 보통
- 0.9: 데이터 견고

**의존성 계수 (D)**
- 1.2: 상위 허브, 영향력 매우 큼
- 1.1: 여러 의사결정에 영향
- 1.0: 독립적

**규제 게이트 플래그 (G)**
- 0.5: 인허가 미충족 시 사업 불가
- 0.0: 그 외

### 최종 점수 계산

```
기본점수 = C1×0.30 + C2×0.25 + C3×0.20 + C4×0.15 + C5×0.10
최종점수 = (기본점수 × U × D + G)를 1-5로 반올림
```

## 출력 형식

### 템플릿 JSON 구조

```json
{
  "status": "template",
  "file_name": "document.pdf",
  "message": "평가 템플릿이 생성되었습니다...",
  "evaluation_templates": [
    {
      "id": 1,
      "category": "승인",
      "item": "환경영향평가 승인 획득",
      "source_text": "환경영향평가 승인이 필수입니다.",
      "evaluation_input": {
        "C1_score": 3,
        "C1_rationale": "평가 필요",
        "C2_score": 3,
        "C2_rationale": "평가 필요",
        "C3_score": 3,
        "C3_rationale": "평가 필요",
        "C4_score": 3,
        "C4_rationale": "평가 필요",
        "C5_score": 3,
        "C5_rationale": "평가 필요",
        "uncertainty_factor": 1.0,
        "dependency_factor": 1.0,
        "regulatory_gate_flag": 0.0
      }
    }
  ],
  "system_prompt": "..."
}
```

### 평가 결과 JSON 구조

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
        "C1_approval": {
          "score": 5,
          "rationale": "법정 필수 승인으로 미획득 시 사업 진행 불가"
        },
        "C2_cost_schedule": {
          "score": 4,
          "rationale": "승인 지연 시 공정 지연 2-3개월 예상"
        },
        "C3_environment_safety": {
          "score": 5,
          "rationale": "환경영향평가의 핵심 목적"
        },
        "C4_operation": {
          "score": 2,
          "rationale": "운영에는 간접적 영향"
        },
        "C5_reversibility": {
          "score": 5,
          "rationale": "승인 후 조건 변경이 거의 불가능"
        },
        "base_score": 4.4,
        "uncertainty_factor": 1.0,
        "dependency_factor": 1.2,
        "regulatory_gate_flag": 0.5,
        "final_score_raw": 5.78,
        "final_score": 5
      },
      "priority": "Critical",
      "recommendation": "즉시 검토 및 조치 필요",
      "source_text": "환경영향평가 승인이 필수입니다."
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

## 워크플로우 예시

### 시나리오 1: 빠른 평가

```bash
# 1. 문서 분석 및 자동 평가
python checklist_converter.py project_plan.pdf --auto

# 2. 결과 확인
cat project_plan_checklist.json
```

### 시나리오 2: 정밀 평가

```bash
# 1. 템플릿 생성
python checklist_converter.py project_plan.pdf -t

# 2. JSON 파일 수정 (텍스트 에디터에서)
#    - 각 항목의 C1~C5 점수 입력
#    - 근거(rationale) 작성
#    - 보정계수 조정

# 3. 평가 수행
python checklist_converter.py -e project_plan_checklist.json

# 4. 결과 확인
cat project_plan_evaluated.json
```

## Python 코드에서 사용

```python
from src.utils.checklist_converter import ChecklistConverter

# 변환기 초기화
converter = ChecklistConverter()

# 문서 처리 (템플릿 생성)
result = converter.process_document(
    file_path="document.pdf",
    output_path="output.json",
    auto_evaluate=False
)

# 또는 자동 평가
result = converter.process_document(
    file_path="document.pdf",
    output_path="output.json",
    auto_evaluate=True
)

# 템플릿 평가
result = converter.load_and_evaluate_template(
    template_path="template.json",
    output_path="evaluated.json"
)

print(f"총 {result['summary']['total_items']}개 항목")
print(f"Critical: {result['summary']['critical']}개")
```

## 직접 가중치 계산

```python
from src.utils.weight_evaluator import WeightEvaluator

evaluator = WeightEvaluator()

# 평가 수행
evaluation = evaluator.evaluate_checklist_item(
    c1_score=5,
    c1_rationale="법정 필수 승인",
    c2_score=4,
    c2_rationale="공정 지연 2-3개월",
    c3_score=5,
    c3_rationale="환경평가 핵심",
    c4_score=2,
    c4_rationale="간접적 영향",
    c5_score=5,
    c5_rationale="변경 불가능",
    uncertainty_factor=1.0,
    dependency_factor=1.2,
    regulatory_gate_flag=0.5
)

print(f"기본점수: {evaluation.base_score}")
print(f"최종점수: {evaluation.final_score}")

# 결과 딕셔너리로 변환
result = evaluator.create_checklist_item_result(
    item_id=1,
    category="승인/규제",
    item="환경영향평가 승인 획득",
    evaluation=evaluation
)

print(f"우선순위: {result['priority']}")
print(f"권장사항: {result['recommendation']}")
```

## 주의사항

1. **문서 품질**: 문서의 텍스트 추출 품질에 따라 결과가 달라질 수 있습니다.
2. **키워드 기반**: 현재는 키워드 기반으로 항목을 추출하므로, 전문적인 검토가 필요합니다.
3. **평가 주관성**: 점수 평가는 주관적일 수 있으므로, 여러 전문가의 검토를 권장합니다.
4. **보정계수**: 보정계수는 신중하게 적용해야 하며, 근거를 명확히 해야 합니다.

## 문제 해결

### ImportError: PyPDF2가 없습니다
```bash
pip install PyPDF2
```

### ImportError: python-docx가 없습니다
```bash
pip install python-docx
```

### 파일을 찾을 수 없습니다
- 파일 경로가 올바른지 확인
- 절대 경로 사용 권장

### 체크리스트 항목이 발견되지 않았습니다
- 문서에 행동 키워드가 포함되어 있는지 확인
- 키워드 목록을 `document_analyzer.py`에서 수정 가능

## 향후 개선 사항

1. LLM 통합으로 더 정확한 항목 추출 및 자동 평가
2. GUI 인터페이스 추가
3. Excel 출력 기능
4. 다국어 지원
5. 템플릿 커스터마이징

## 라이센스

이 시스템은 risk-management-system 프로젝트의 일부입니다.
