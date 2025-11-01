"""
가중치 평가 엔진 모듈

체크리스트 항목의 중요도 가중치를 계산합니다.
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class EvaluationCriteria:
    """평가 기준"""
    score: int  # 1-5점
    rationale: str  # 평가 근거


@dataclass
class ChecklistEvaluation:
    """체크리스트 평가 결과"""
    C1_approval: EvaluationCriteria  # 승인/법규 관문성
    C2_cost_schedule: EvaluationCriteria  # 비용/일정 영향
    C3_environment_safety: EvaluationCriteria  # 환경·안전 영향
    C4_operation: EvaluationCriteria  # 운영성 영향
    C5_reversibility: EvaluationCriteria  # 대체/가역성

    base_score: float  # 기본점수
    uncertainty_factor: float  # 불확실성 계수 (U)
    dependency_factor: float  # 의존성 계수 (D)
    regulatory_gate_flag: float  # 규제 게이트 플래그 (G)
    final_score_raw: float  # 최종점수 (보정 전)
    final_score: int  # 최종점수 (1-5)


class WeightEvaluator:
    """가중치 평가 엔진"""

    # 가중치 (프로젝트 초기 기획단계 기준)
    WEIGHTS = {
        'C1': 0.30,  # 승인/법규 관문성
        'C2': 0.25,  # 비용/일정 영향
        'C3': 0.20,  # 환경·안전 영향
        'C4': 0.15,  # 운영성 영향
        'C5': 0.10,  # 대체/가역성
    }

    # 우선순위 매핑
    PRIORITY_MAP = {
        5: "Critical",
        4: "High",
        3: "Medium",
        2: "Low",
        1: "Minimal"
    }

    # 권장사항 매핑
    RECOMMENDATION_MAP = {
        5: "즉시 검토 및 조치 필요",
        4: "빠른 시일 내 검토 필요",
        3: "정기적 검토 필요",
        2: "여유 있을 때 검토",
        1: "필요시 검토"
    }

    def __init__(self):
        """초기화"""
        pass

    def calculate_base_score(
        self,
        c1_score: int,
        c2_score: int,
        c3_score: int,
        c4_score: int,
        c5_score: int
    ) -> float:
        """
        기본점수 계산

        Args:
            c1_score: C1 점수 (1-5)
            c2_score: C2 점수 (1-5)
            c3_score: C3 점수 (1-5)
            c4_score: C4 점수 (1-5)
            c5_score: C5 점수 (1-5)

        Returns:
            float: 기본점수 (1.0-5.0)
        """
        # 점수 유효성 검증
        for score in [c1_score, c2_score, c3_score, c4_score, c5_score]:
            if not (1 <= score <= 5):
                raise ValueError(f"점수는 1-5 사이여야 합니다: {score}")

        # 가중치 적용
        base_score = (
            self.WEIGHTS['C1'] * c1_score +
            self.WEIGHTS['C2'] * c2_score +
            self.WEIGHTS['C3'] * c3_score +
            self.WEIGHTS['C4'] * c4_score +
            self.WEIGHTS['C5'] * c5_score
        )

        return round(base_score, 2)

    def calculate_final_score(
        self,
        base_score: float,
        uncertainty_factor: float = 1.0,
        dependency_factor: float = 1.0,
        regulatory_gate_flag: float = 0.0
    ) -> tuple[float, int]:
        """
        최종점수 계산

        Args:
            base_score: 기본점수
            uncertainty_factor: 불확실성 계수 (0.9, 1.0, 1.1, 1.2)
            dependency_factor: 의존성 계수 (1.0, 1.1, 1.2)
            regulatory_gate_flag: 규제 게이트 플래그 (0.0 or 0.5)

        Returns:
            tuple: (최종점수_raw, 최종점수_양자화)
        """
        # 유효성 검증
        if uncertainty_factor not in [0.9, 1.0, 1.1, 1.2]:
            raise ValueError(f"불확실성 계수는 [0.9, 1.0, 1.1, 1.2] 중 하나여야 합니다: {uncertainty_factor}")

        if dependency_factor not in [1.0, 1.1, 1.2]:
            raise ValueError(f"의존성 계수는 [1.0, 1.1, 1.2] 중 하나여야 합니다: {dependency_factor}")

        if regulatory_gate_flag not in [0.0, 0.5]:
            raise ValueError(f"규제 게이트 플래그는 0.0 또는 0.5여야 합니다: {regulatory_gate_flag}")

        # 최종점수 계산
        final_score_raw = base_score * uncertainty_factor * dependency_factor + regulatory_gate_flag

        # 양자화 (반올림하여 1-5 범위로 제한)
        final_score = self._round_half_up(final_score_raw)
        final_score = max(1, min(5, final_score))

        return round(final_score_raw, 2), final_score

    def _round_half_up(self, value: float) -> int:
        """
        0.5 이상은 올림, 미만은 내림

        Args:
            value: 반올림할 값

        Returns:
            int: 반올림된 정수
        """
        return math.floor(value + 0.5)

    def evaluate_checklist_item(
        self,
        c1_score: int,
        c1_rationale: str,
        c2_score: int,
        c2_rationale: str,
        c3_score: int,
        c3_rationale: str,
        c4_score: int,
        c4_rationale: str,
        c5_score: int,
        c5_rationale: str,
        uncertainty_factor: float = 1.0,
        dependency_factor: float = 1.0,
        regulatory_gate_flag: float = 0.0
    ) -> ChecklistEvaluation:
        """
        체크리스트 항목 평가

        Args:
            c1_score ~ c5_score: 각 평가축 점수 (1-5)
            c1_rationale ~ c5_rationale: 각 평가축 근거
            uncertainty_factor: 불확실성 계수
            dependency_factor: 의존성 계수
            regulatory_gate_flag: 규제 게이트 플래그

        Returns:
            ChecklistEvaluation: 평가 결과
        """
        # 기본점수 계산
        base_score = self.calculate_base_score(
            c1_score, c2_score, c3_score, c4_score, c5_score
        )

        # 최종점수 계산
        final_score_raw, final_score = self.calculate_final_score(
            base_score,
            uncertainty_factor,
            dependency_factor,
            regulatory_gate_flag
        )

        # 평가 결과 생성
        evaluation = ChecklistEvaluation(
            C1_approval=EvaluationCriteria(score=c1_score, rationale=c1_rationale),
            C2_cost_schedule=EvaluationCriteria(score=c2_score, rationale=c2_rationale),
            C3_environment_safety=EvaluationCriteria(score=c3_score, rationale=c3_rationale),
            C4_operation=EvaluationCriteria(score=c4_score, rationale=c4_rationale),
            C5_reversibility=EvaluationCriteria(score=c5_score, rationale=c5_rationale),
            base_score=base_score,
            uncertainty_factor=uncertainty_factor,
            dependency_factor=dependency_factor,
            regulatory_gate_flag=regulatory_gate_flag,
            final_score_raw=final_score_raw,
            final_score=final_score
        )

        return evaluation

    def get_priority(self, final_score: int) -> str:
        """우선순위 반환"""
        return self.PRIORITY_MAP.get(final_score, "Unknown")

    def get_recommendation(self, final_score: int) -> str:
        """권장사항 반환"""
        return self.RECOMMENDATION_MAP.get(final_score, "검토 필요")

    def evaluation_to_dict(self, evaluation: ChecklistEvaluation) -> Dict[str, Any]:
        """평가 결과를 딕셔너리로 변환"""
        return {
            "C1_approval": {
                "score": evaluation.C1_approval.score,
                "rationale": evaluation.C1_approval.rationale
            },
            "C2_cost_schedule": {
                "score": evaluation.C2_cost_schedule.score,
                "rationale": evaluation.C2_cost_schedule.rationale
            },
            "C3_environment_safety": {
                "score": evaluation.C3_environment_safety.score,
                "rationale": evaluation.C3_environment_safety.rationale
            },
            "C4_operation": {
                "score": evaluation.C4_operation.score,
                "rationale": evaluation.C4_operation.rationale
            },
            "C5_reversibility": {
                "score": evaluation.C5_reversibility.score,
                "rationale": evaluation.C5_reversibility.rationale
            },
            "base_score": evaluation.base_score,
            "uncertainty_factor": evaluation.uncertainty_factor,
            "dependency_factor": evaluation.dependency_factor,
            "regulatory_gate_flag": evaluation.regulatory_gate_flag,
            "final_score_raw": evaluation.final_score_raw,
            "final_score": evaluation.final_score
        }

    def create_checklist_item_result(
        self,
        item_id: int,
        category: str,
        item: str,
        evaluation: ChecklistEvaluation,
        additional_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        체크리스트 항목 결과 생성

        Args:
            item_id: 항목 ID
            category: 카테고리
            item: 항목 내용
            evaluation: 평가 결과
            additional_info: 추가 정보

        Returns:
            Dict: 체크리스트 항목 결과
        """
        priority = self.get_priority(evaluation.final_score)
        recommendation = self.get_recommendation(evaluation.final_score)

        result = {
            "id": item_id,
            "category": category,
            "item": item,
            "evaluation": self.evaluation_to_dict(evaluation),
            "priority": priority,
            "recommendation": recommendation
        }

        if additional_info:
            result["additional_info"] = additional_info

        return result


def main():
    """테스트용 메인 함수"""
    evaluator = WeightEvaluator()

    # 예시 1: 활주로 용량 분석
    print("=" * 80)
    print("예시 1: 활주로 용량 분석")
    print("=" * 80)

    evaluation1 = evaluator.evaluate_checklist_item(
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

    result1 = evaluator.create_checklist_item_result(
        item_id=1,
        category="인프라 계획",
        item="활주로 용량 분석 수행",
        evaluation=evaluation1,
        additional_info="프로젝트 초기에 즉시 수행 필수. 외부 전문가 자문 권장."
    )

    print(f"기본점수: {evaluation1.base_score}")
    print(f"최종점수(raw): {evaluation1.final_score_raw}")
    print(f"최종점수: {evaluation1.final_score}")
    print(f"우선순위: {result1['priority']}")
    print(f"권장사항: {result1['recommendation']}")
    print()

    # 예시 2: 환경영향평가 승인
    print("=" * 80)
    print("예시 2: 환경영향평가 승인")
    print("=" * 80)

    evaluation2 = evaluator.evaluate_checklist_item(
        c1_score=5,
        c1_rationale="법정 필수 승인으로 미획득 시 사업 진행 불가",
        c2_score=4,
        c2_rationale="승인 지연 시 공정 지연 2-3개월 예상",
        c3_score=5,
        c3_rationale="환경영향평가의 핵심 목적",
        c4_score=2,
        c4_rationale="운영에는 간접적 영향",
        c5_score=5,
        c5_rationale="승인 후 조건 변경이 거의 불가능",
        uncertainty_factor=1.0,
        dependency_factor=1.2,
        regulatory_gate_flag=0.5
    )

    result2 = evaluator.create_checklist_item_result(
        item_id=2,
        category="승인/규제",
        item="환경영향평가 승인 획득",
        evaluation=evaluation2,
        additional_info="사업 착수 전 필수 획득. 충분한 시간과 자원 배정 필요."
    )

    print(f"기본점수: {evaluation2.base_score}")
    print(f"최종점수(raw): {evaluation2.final_score_raw}")
    print(f"최종점수: {evaluation2.final_score}")
    print(f"우선순위: {result2['priority']}")
    print(f"권장사항: {result2['recommendation']}")
    print()


if __name__ == "__main__":
    main()
