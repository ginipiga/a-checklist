"""
체크리스트 변환기 통합 모듈

문서를 분석하고 가중치를 평가하여 체크리스트를 생성합니다.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# 모듈 임포트
from .document_analyzer import DocumentAnalyzer, load_system_prompt
from .weight_evaluator import WeightEvaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChecklistConverter:
    """체크리스트 변환기"""

    def __init__(self):
        """초기화"""
        self.analyzer = DocumentAnalyzer()
        self.evaluator = WeightEvaluator()
        self.system_prompt = None

    def load_system_prompt(self, prompt_path: Optional[str] = None):
        """시스템 프롬프트 로드"""
        try:
            self.system_prompt = load_system_prompt(prompt_path)
            logger.info("시스템 프롬프트를 로드했습니다.")
        except Exception as e:
            logger.error(f"시스템 프롬프트 로드 실패: {e}")
            raise

    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        문서 분석

        Args:
            file_path: 분석할 문서 파일 경로

        Returns:
            Dict: 분석 결과
        """
        logger.info(f"문서 분석 시작: {file_path}")
        result = self.analyzer.analyze_document(file_path)
        logger.info(f"체크리스트 후보 {len(result['analysis']['checklist_candidates'])}개 추출")
        return result

    def create_evaluation_template(
        self,
        checklist_candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        평가 템플릿 생성

        Args:
            checklist_candidates: 체크리스트 후보 목록

        Returns:
            List: 평가 템플릿 목록
        """
        templates = []

        for candidate in checklist_candidates:
            template = {
                "id": candidate["id"],
                "category": candidate["category"],
                "item": candidate["item"],
                "source_text": candidate.get("source_text", ""),
                "evaluation_input": {
                    "C1_score": 3,  # 기본값
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
            templates.append(template)

        return templates

    def evaluate_items(
        self,
        evaluation_templates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        항목 평가

        Args:
            evaluation_templates: 평가 템플릿 목록

        Returns:
            List: 평가 결과 목록
        """
        results = []

        for template in evaluation_templates:
            eval_input = template["evaluation_input"]

            # 평가 수행
            evaluation = self.evaluator.evaluate_checklist_item(
                c1_score=eval_input["C1_score"],
                c1_rationale=eval_input["C1_rationale"],
                c2_score=eval_input["C2_score"],
                c2_rationale=eval_input["C2_rationale"],
                c3_score=eval_input["C3_score"],
                c3_rationale=eval_input["C3_rationale"],
                c4_score=eval_input["C4_score"],
                c4_rationale=eval_input["C4_rationale"],
                c5_score=eval_input["C5_score"],
                c5_rationale=eval_input["C5_rationale"],
                uncertainty_factor=eval_input["uncertainty_factor"],
                dependency_factor=eval_input["dependency_factor"],
                regulatory_gate_flag=eval_input["regulatory_gate_flag"]
            )

            # 결과 생성
            result = self.evaluator.create_checklist_item_result(
                item_id=template["id"],
                category=template["category"],
                item=template["item"],
                evaluation=evaluation
            )

            # 원본 텍스트 추가
            result["source_text"] = template.get("source_text", "")

            results.append(result)

        return results

    def process_document(
        self,
        file_path: str,
        output_path: Optional[str] = None,
        auto_evaluate: bool = False
    ) -> Dict[str, Any]:
        """
        문서 전체 처리

        Args:
            file_path: 입력 문서 경로
            output_path: 출력 파일 경로 (None이면 자동 생성)
            auto_evaluate: 자동 평가 여부 (False면 템플릿만 생성)

        Returns:
            Dict: 처리 결과
        """
        # 시스템 프롬프트 로드 (아직 안 했으면)
        if self.system_prompt is None:
            self.load_system_prompt()

        # 문서 분석
        analysis_result = self.analyze_document(file_path)

        # 체크리스트 후보 추출
        candidates = analysis_result["analysis"]["checklist_candidates"]

        if not candidates:
            logger.warning("체크리스트 항목이 발견되지 않았습니다.")
            return {
                "status": "no_items",
                "message": "체크리스트 항목이 발견되지 않았습니다.",
                "analysis": analysis_result
            }

        # 평가 템플릿 생성
        templates = self.create_evaluation_template(candidates)

        if auto_evaluate:
            # 자동 평가 수행
            evaluated_items = self.evaluate_items(templates)
            result = {
                "status": "evaluated",
                "file_name": analysis_result["file_name"],
                "checklist_items": evaluated_items,
                "summary": {
                    "total_items": len(evaluated_items),
                    "critical": sum(1 for item in evaluated_items if item["priority"] == "Critical"),
                    "high": sum(1 for item in evaluated_items if item["priority"] == "High"),
                    "medium": sum(1 for item in evaluated_items if item["priority"] == "Medium"),
                    "low": sum(1 for item in evaluated_items if item["priority"] == "Low"),
                    "minimal": sum(1 for item in evaluated_items if item["priority"] == "Minimal")
                }
            }
        else:
            # 템플릿만 반환 (사용자가 직접 평가)
            result = {
                "status": "template",
                "file_name": analysis_result["file_name"],
                "message": "평가 템플릿이 생성되었습니다. 각 항목의 점수를 입력한 후 평가를 수행하세요.",
                "evaluation_templates": templates,
                "system_prompt": self.system_prompt
            }

        # 파일로 저장
        if output_path:
            output_path = Path(output_path)
        else:
            # 자동으로 출력 파일명 생성
            input_path = Path(file_path)
            output_filename = f"{input_path.stem}_checklist.json"
            output_path = input_path.parent / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, ensure_ascii=False, indent=2, f=f)

        logger.info(f"결과를 저장했습니다: {output_path}")

        result["output_path"] = str(output_path)

        return result

    def load_and_evaluate_template(
        self,
        template_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        템플릿을 로드하고 평가

        Args:
            template_path: 템플릿 파일 경로
            output_path: 출력 파일 경로

        Returns:
            Dict: 평가 결과
        """
        # 템플릿 로드
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        if template_data["status"] != "template":
            raise ValueError("올바른 템플릿 파일이 아닙니다.")

        # 평가 수행
        evaluated_items = self.evaluate_items(template_data["evaluation_templates"])

        result = {
            "status": "evaluated",
            "file_name": template_data["file_name"],
            "checklist_items": evaluated_items,
            "summary": {
                "total_items": len(evaluated_items),
                "critical": sum(1 for item in evaluated_items if item["priority"] == "Critical"),
                "high": sum(1 for item in evaluated_items if item["priority"] == "High"),
                "medium": sum(1 for item in evaluated_items if item["priority"] == "Medium"),
                "low": sum(1 for item in evaluated_items if item["priority"] == "Low"),
                "minimal": sum(1 for item in evaluated_items if item["priority"] == "Minimal")
            }
        }

        # 파일로 저장
        if output_path:
            output_path = Path(output_path)
        else:
            # 자동으로 출력 파일명 생성
            template_path = Path(template_path)
            output_filename = template_path.name.replace("_template.json", "_evaluated.json")
            output_path = template_path.parent / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, ensure_ascii=False, indent=2, f=f)

        logger.info(f"평가 결과를 저장했습니다: {output_path}")

        result["output_path"] = str(output_path)

        return result


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='문서를 체크리스트로 변환하고 가중치를 평가합니다.')
    parser.add_argument('input', help='입력 문서 파일 경로')
    parser.add_argument('-o', '--output', help='출력 파일 경로', default=None)
    parser.add_argument('-a', '--auto', action='store_true', help='자동 평가 (기본값 사용)')
    parser.add_argument('-t', '--template', action='store_true', help='템플릿 모드 (평가 없이 템플릿만 생성)')
    parser.add_argument('-e', '--evaluate', help='템플릿 파일 평가', default=None)

    args = parser.parse_args()

    converter = ChecklistConverter()

    try:
        if args.evaluate:
            # 템플릿 평가 모드
            result = converter.load_and_evaluate_template(args.evaluate, args.output)
        else:
            # 문서 처리 모드
            auto_evaluate = args.auto and not args.template
            result = converter.process_document(args.input, args.output, auto_evaluate)

        # 결과 요약 출력
        print("\n" + "=" * 80)
        print("처리 완료")
        print("=" * 80)
        print(f"상태: {result['status']}")
        print(f"출력 파일: {result.get('output_path', 'N/A')}")

        if "summary" in result:
            print("\n요약:")
            print(f"  전체 항목: {result['summary']['total_items']}")
            print(f"  Critical: {result['summary']['critical']}")
            print(f"  High: {result['summary']['high']}")
            print(f"  Medium: {result['summary']['medium']}")
            print(f"  Low: {result['summary']['low']}")
            print(f"  Minimal: {result['summary']['minimal']}")

    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
