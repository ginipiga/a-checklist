"""
LLM을 사용하여 문서 구조를 분석하는 모듈
"""
import json
import os
from typing import List, Dict, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMDocumentAnalyzer:
    """LLM을 사용하여 문서 구조를 정확히 분석"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
            model: 사용할 모델 (gpt-4o-mini, gpt-4o, gpt-3.5-turbo 등)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI 라이브러리를 설치해주세요: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API 키가 필요합니다. "
                "환경변수 OPENAI_API_KEY를 설정하거나 api_key 매개변수를 제공하세요."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model

        # 시스템 프롬프트 로드
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """시스템 프롬프트 파일 로드"""
        prompt_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..",
            "config",
            "document_structure_prompt.md"
        )

        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # 기본 프롬프트
            return """당신은 문서를 분석하여 계층적 체크리스트 구조로 변환하는 전문가입니다.

제목, 체크리스트, 본문을 정확히 구분하고, 논리적인 계층 구조를 생성하세요.

체크리스트 항목은 반드시 실행 가능하고 측정 가능한 항목만 포함하세요.
"""

    def analyze_text_blocks(self, text_blocks: List[Dict]) -> Dict:
        """
        텍스트 블록 리스트를 LLM으로 분석하여 구조화

        Args:
            text_blocks: 텍스트 블록 리스트 (각 블록은 text, font_size, is_bold 등 포함)

        Returns:
            Dict: 계층적 토글 구조
        """
        # 입력 데이터 준비
        user_message = self._prepare_user_message(text_blocks)

        try:
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # 일관성을 위해 낮은 temperature
                max_tokens=4096
            )

            # 응답 파싱
            result_text = response.choices[0].message.content
            result = json.loads(result_text)

            return result

        except Exception as e:
            print(f"LLM 분석 오류: {e}")
            return None

    def _prepare_user_message(self, text_blocks: List[Dict]) -> str:
        """사용자 메시지 준비"""
        message = "다음 문서 텍스트 블록을 분석하여 계층적 구조로 변환해주세요.\n\n"
        message += "## 텍스트 블록:\n\n"

        for i, block in enumerate(text_blocks, 1):
            text = block.get("text", "")
            font_size = block.get("font_size", 12)
            is_bold = block.get("is_bold", False)
            style = block.get("style", "Normal")

            message += f"[블록 {i}]\n"
            message += f"텍스트: {text}\n"
            message += f"폰트크기: {font_size}, 굵기: {'굵음' if is_bold else '보통'}, 스타일: {style}\n\n"

        message += "\n## 요구사항:\n"
        message += "1. 제목, 체크리스트, 본문을 정확히 구분하세요.\n"
        message += "2. 체크리스트는 실행 가능하고 측정 가능한 항목만 포함하세요.\n"
        message += "3. 논리적인 계층 구조를 생성하세요.\n"
        message += "4. 각 체크리스트 항목에 적절한 카테고리를 지정하세요.\n"
        message += "5. JSON 형식으로 출력하세요.\n"

        return message

    def analyze_and_convert(self, text_blocks: List[Dict], file_type: str = "document") -> Dict:
        """
        텍스트 블록을 분석하고 토글 구조로 변환

        Args:
            text_blocks: 텍스트 블록 리스트
            file_type: 파일 타입 ("pdf", "word", "excel", "document")

        Returns:
            Dict: 토글 구조 데이터
        """
        if not text_blocks:
            return None

        # LLM으로 분석
        structure = self.analyze_text_blocks(text_blocks)

        if not structure:
            return None

        # 토글 구조로 변환
        toggle_data = self._convert_to_toggle_format(structure, file_type)

        return toggle_data

    def _convert_to_toggle_format(self, structure: Dict, file_type: str) -> Dict:
        """
        LLM 출력을 토글 형식으로 변환

        Args:
            structure: LLM이 생성한 구조
            file_type: 파일 타입

        Returns:
            Dict: 토글 형식 데이터
        """
        # 기본 토글 구조
        toggle = {
            "title": structure.get("title", f"{file_type.upper()} 문서"),
            "content": structure.get("content", ""),
            "current_score": 0,
            "max_score": 100,
            "children": [],
            "checklist": []
        }

        # 체크리스트 변환
        if "checklist" in structure:
            for item in structure["checklist"]:
                checklist_item = {
                    "text": item.get("text", ""),
                    "summary": item.get("summary", item.get("text", "")),
                    "detail": item.get("detail", ""),
                    "is_checked": False,
                    "score": 1
                }
                # 카테고리 정보가 있으면 추가
                if "category" in item:
                    checklist_item["category"] = item["category"]

                toggle["checklist"].append(checklist_item)

        # 하위 항목 재귀 변환
        if "children" in structure:
            for child in structure["children"]:
                child_toggle = self._convert_to_toggle_format(child, file_type)
                toggle["children"].append(child_toggle)

        return toggle


def is_llm_available() -> bool:
    """LLM 분석 기능이 사용 가능한지 확인"""
    if not OPENAI_AVAILABLE:
        return False

    # API 키가 있는지 확인
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key is not None and api_key.strip() != ""
