"""
템플릿 관리 유틸리티
파일을 프로젝트 구조로 변환할 때 사용되는 템플릿을 관리합니다.
"""
import json
import os
from typing import Dict, Any, Optional


class TemplateManager:
    """템플릿을 로드하고 적용하는 관리자"""

    def __init__(self, use_smart_analysis: bool = False, llm_mode: str = "none"):
        """
        Args:
            use_smart_analysis: LLM 스마트 분석 사용 여부
            llm_mode: LLM 모드 ("none", "ollama", "openai")
        """
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'templates'
        )

        self.use_smart_analysis = use_smart_analysis
        self.smart_processor = None

        # 스마트 분석 초기화
        if use_smart_analysis and llm_mode != "none":
            try:
                from .smart_template_processor import SmartTemplateProcessor
                self.smart_processor = SmartTemplateProcessor(llm_mode)
                if self.smart_processor.llm_mode == "none":
                    self.use_smart_analysis = False
            except ImportError as e:
                print(f"⚠️ 스마트 분석 모듈을 불러올 수 없습니다: {e}")
                self.use_smart_analysis = False

    def load_template(self, template_name: str = "project_template.json") -> Optional[Dict[str, Any]]:
        """
        템플릿 파일을 로드합니다.

        Args:
            template_name: 템플릿 파일명

        Returns:
            Dict: 템플릿 데이터
        """
        template_path = os.path.join(self.templates_dir, template_name)

        if not os.path.exists(template_path):
            print(f"템플릿 파일을 찾을 수 없습니다: {template_path}")
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"템플릿 로드 오류: {e}")
            return None

    def apply_template(self, template: Dict[str, Any], filename: str, content: str) -> Dict[str, Any]:
        """
        템플릿을 적용하여 토글 데이터를 생성합니다.

        Args:
            template: 템플릿 데이터
            filename: 파일명
            content: 파일 내용

        Returns:
            Dict: 토글 아이템 데이터
        """
        if not template or 'structure' not in template:
            # 템플릿이 없으면 기본 구조 반환
            return {
                'title': filename,
                'content': content,
                'is_expanded': True,
                'checklist': [],
                'children': []
            }

        structure = template['structure']
        result = self._apply_template_recursive(structure, {
            'filename': filename,
            'content': content
        })

        return result

    def _apply_template_recursive(self, template_node: Dict[str, Any], variables: Dict[str, str]) -> Dict[str, Any]:
        """
        재귀적으로 템플릿을 적용합니다.

        Args:
            template_node: 템플릿 노드
            variables: 치환할 변수들

        Returns:
            Dict: 변환된 토글 아이템 데이터
        """
        result = {
            'title': self._replace_variables(template_node.get('title', '새 토글'), variables),
            'content': self._replace_variables(template_node.get('content', ''), variables),
            'is_expanded': template_node.get('is_expanded', True),
            'checklist': template_node.get('checklist', []).copy(),
            'children': []
        }

        # 하위 항목들 처리
        for child_template in template_node.get('children', []):
            child_result = self._apply_template_recursive(child_template, variables)
            result['children'].append(child_result)

        return result

    def _replace_variables(self, text: str, variables: Dict[str, str]) -> str:
        """
        텍스트 내의 변수를 치환합니다.

        Args:
            text: 원본 텍스트
            variables: 변수 딕셔너리

        Returns:
            str: 변수가 치환된 텍스트
        """
        result = text
        for key, value in variables.items():
            # 너무 긴 content는 잘라내기 (최대 5000자)
            clean_value = value
            if key == 'content' and len(value) > 5000:
                clean_value = value[:5000] + "\n\n... (내용이 너무 길어 생략됨)"

            # toggle_widget_ 같은 이상한 패턴이 있으면 제거
            if 'toggle_widget_' in clean_value:
                clean_value = "[문서 추출 오류 - 내용을 확인해주세요]"

            result = result.replace(f'{{{{{key}}}}}', clean_value)
        return result

    def create_project_from_file(self, filename: str, content: str,
                                  template_name: str = "project_template.json") -> Dict[str, Any]:
        """
        파일로부터 프로젝트 구조를 생성합니다.

        Args:
            filename: 파일명
            content: 파일 내용
            template_name: 사용할 템플릿 이름

        Returns:
            Dict: 토글 아이템 데이터
        """
        # 스마트 분석 사용 시
        if self.use_smart_analysis and self.smart_processor:
            print(f"🤖 AI가 문서를 분석하여 최적의 프로젝트 구조를 생성합니다...")
            smart_result = self.smart_processor.analyze_document(filename, content)

            if smart_result:
                print("✅ AI 분석 완료! 맞춤형 프로젝트 구조가 생성되었습니다.")
                return smart_result
            else:
                print("⚠️ AI 분석 실패, 기본 템플릿을 사용합니다.")

        # 기본 템플릿 사용
        template = self.load_template(template_name)
        return self.apply_template(template, filename, content)


def is_template_supported() -> bool:
    """템플릿 기능이 지원되는지 확인"""
    return True
