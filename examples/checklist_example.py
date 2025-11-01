"""
체크리스트 변환기 사용 예시

이 스크립트는 체크리스트 변환기의 주요 기능을 시연합니다.
"""

import sys
import os
from pathlib import Path

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.checklist_converter import ChecklistConverter
from utils.weight_evaluator import WeightEvaluator


def example1_basic_evaluation():
    """예시 1: 기본 가중치 평가"""
    print("\n" + "=" * 80)
    print("예시 1: 기본 가중치 평가")
    print("=" * 80)

    evaluator = WeightEvaluator()

    # 활주로 용량 분석 평가
    evaluation = evaluator.evaluate_checklist_item(
        c1_score=4,
        c1_rationale="항공청 승인 절차와 직결되어 지연 시 사업 진행에 영향",
        c2_score=5,
        c2_rationale="용량 분석 결과에 따라 설계 변경 시 CAPEX 20% 이상 증가 가능",
        c3_score=3,
        c3_rationale="소음 영향 평가와 연계되어 환경 보완 조치 필요",
        c4_score=5,
        c4_rationale="공항 용량과 OTP에 직접적이고 치명적인 영향",
        c5_score=4,
        c5_rationale="활주로 건설 후 수정이 매우 어렵고 비용이 막대함",
        uncertainty_factor=1.1,
        dependency_factor=1.2,
        regulatory_gate_flag=0.0
    )

    result = evaluator.create_checklist_item_result(
        item_id=1,
        category="인프라 계획",
        item="활주로 용량 분석 수행",
        evaluation=evaluation
    )

    print(f"항목: {result['item']}")
    print(f"카테고리: {result['category']}")
    print(f"\n평가 점수:")
    print(f"  C1 (승인/법규): {evaluation.C1_approval.score}점")
    print(f"  C2 (비용/일정): {evaluation.C2_cost_schedule.score}점")
    print(f"  C3 (환경/안전): {evaluation.C3_environment_safety.score}점")
    print(f"  C4 (운영성): {evaluation.C4_operation.score}점")
    print(f"  C5 (가역성): {evaluation.C5_reversibility.score}점")
    print(f"\n계산 과정:")
    print(f"  기본점수: {evaluation.base_score}")
    print(f"  불확실성 계수: {evaluation.uncertainty_factor}")
    print(f"  의존성 계수: {evaluation.dependency_factor}")
    print(f"  규제 게이트 플래그: {evaluation.regulatory_gate_flag}")
    print(f"  최종점수(raw): {evaluation.final_score_raw}")
    print(f"  최종점수: {evaluation.final_score}")
    print(f"\n결과:")
    print(f"  우선순위: {result['priority']}")
    print(f"  권장사항: {result['recommendation']}")


def example2_multiple_items():
    """예시 2: 여러 항목 평가"""
    print("\n" + "=" * 80)
    print("예시 2: 여러 항목 평가")
    print("=" * 80)

    evaluator = WeightEvaluator()

    items = [
        {
            "id": 1,
            "category": "승인/규제",
            "item": "환경영향평가 승인 획득",
            "scores": {
                "c1": (5, "법정 필수 승인으로 미획득 시 사업 진행 불가"),
                "c2": (4, "승인 지연 시 공정 지연 2-3개월 예상"),
                "c3": (5, "환경영향평가의 핵심 목적"),
                "c4": (2, "운영에는 간접적 영향"),
                "c5": (5, "승인 후 조건 변경이 거의 불가능")
            },
            "factors": {"u": 1.0, "d": 1.2, "g": 0.5}
        },
        {
            "id": 2,
            "category": "설계",
            "item": "터미널 레이아웃 최종 확정",
            "scores": {
                "c1": (3, "설계 변경 시 승인 보완 필요"),
                "c2": (4, "레이아웃 변경 시 상당한 비용 증가"),
                "c3": (2, "환경/안전에 경미한 영향"),
                "c4": (5, "승객 동선 및 운영 효율성에 치명적 영향"),
                "c5": (4, "건설 후 변경이 매우 어려움")
            },
            "factors": {"u": 1.1, "d": 1.1, "g": 0.0}
        },
        {
            "id": 3,
            "category": "운영",
            "item": "IT 시스템 벤더 선정",
            "scores": {
                "c1": (2, "승인과 간접적 관련"),
                "c2": (3, "벤더 변경 시 중간 정도 비용 발생"),
                "c3": (1, "환경/안전과 무관"),
                "c4": (3, "운영 시스템에 중간 정도 영향"),
                "c5": (2, "벤더 변경이 비교적 용이")
            },
            "factors": {"u": 1.0, "d": 1.0, "g": 0.0}
        }
    ]

    results = []

    for item_data in items:
        scores = item_data["scores"]
        factors = item_data["factors"]

        evaluation = evaluator.evaluate_checklist_item(
            c1_score=scores["c1"][0],
            c1_rationale=scores["c1"][1],
            c2_score=scores["c2"][0],
            c2_rationale=scores["c2"][1],
            c3_score=scores["c3"][0],
            c3_rationale=scores["c3"][1],
            c4_score=scores["c4"][0],
            c4_rationale=scores["c4"][1],
            c5_score=scores["c5"][0],
            c5_rationale=scores["c5"][1],
            uncertainty_factor=factors["u"],
            dependency_factor=factors["d"],
            regulatory_gate_flag=factors["g"]
        )

        result = evaluator.create_checklist_item_result(
            item_id=item_data["id"],
            category=item_data["category"],
            item=item_data["item"],
            evaluation=evaluation
        )

        results.append(result)

        print(f"\n항목 {result['id']}: {result['item']}")
        print(f"  카테고리: {result['category']}")
        print(f"  최종점수: {evaluation.final_score}")
        print(f"  우선순위: {result['priority']}")
        print(f"  권장사항: {result['recommendation']}")

    # 우선순위별 정리
    print("\n" + "-" * 80)
    print("우선순위별 정리")
    print("-" * 80)

    priority_groups = {}
    for result in results:
        priority = result['priority']
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append(result)

    for priority in ["Critical", "High", "Medium", "Low", "Minimal"]:
        if priority in priority_groups:
            print(f"\n{priority}:")
            for result in priority_groups[priority]:
                print(f"  - {result['item']}")


def example3_document_analysis():
    """예시 3: 문서 분석 (테스트 문서가 있는 경우)"""
    print("\n" + "=" * 80)
    print("예시 3: 문서 분석 예시")
    print("=" * 80)

    # 프로젝트 루트 디렉토리에서 테스트 PDF 찾기
    project_root = Path(__file__).parent.parent
    test_pdf = project_root / "test_risk_management.pdf"

    if test_pdf.exists():
        print(f"테스트 문서 발견: {test_pdf}")

        converter = ChecklistConverter()

        # 템플릿 생성
        print("\n템플릿 생성 중...")
        result = converter.process_document(
            file_path=str(test_pdf),
            auto_evaluate=False
        )

        print(f"\n상태: {result['status']}")

        if result['status'] == 'no_items':
            print(f"메시지: {result.get('message', '항목을 찾을 수 없습니다.')}")
            print("\n문서에 체크리스트 항목이 발견되지 않았습니다.")
            print("행동 키워드(필요, 수행, 검토 등)가 포함된 문장이 있는지 확인하세요.")
            return

        if 'file_name' in result:
            print(f"파일명: {result['file_name']}")
        if 'output_path' in result:
            print(f"출력 파일: {result['output_path']}")

        if 'evaluation_templates' in result:
            templates = result['evaluation_templates']
            print(f"\n추출된 체크리스트 항목: {len(templates)}개")

            # 처음 3개 항목 출력
            for template in templates[:3]:
                print(f"\n항목 {template['id']}:")
                print(f"  카테고리: {template['category']}")
                print(f"  내용: {template['item']}")
                print(f"  원본: {template['source_text'][:80]}...")

            print(f"\n전체 결과는 {result['output_path']} 파일을 참조하세요.")
    else:
        print(f"테스트 문서를 찾을 수 없습니다: {test_pdf}")
        print("문서 분석 예시를 건너뜁니다.")


def main():
    """메인 함수"""
    print("\n" + "=" * 80)
    print("체크리스트 변환기 사용 예시")
    print("=" * 80)

    try:
        # 예시 1: 기본 가중치 평가
        example1_basic_evaluation()

        # 예시 2: 여러 항목 평가
        example2_multiple_items()

        # 예시 3: 문서 분석
        example3_document_analysis()

        print("\n" + "=" * 80)
        print("모든 예시가 완료되었습니다.")
        print("=" * 80)

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
