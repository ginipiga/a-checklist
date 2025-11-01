"""
로컬 LLM(Ollama)을 사용하여 문서 구조를 분석하는 모듈
완전히 로컬에서 실행되므로 데이터 유출 걱정 없음
"""
import json
import os
from typing import List, Dict, Optional
import requests


class OllamaAnalyzer:
    """Ollama를 사용한 로컬 LLM 문서 분석"""

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        """
        Args:
            model: 사용할 Ollama 모델 (기본: qwen2.5:7b)
                  추천 모델:
                  - qwen2.5:7b (한국어 우수, 7B 파라미터)
                  - llama3.1:8b (영어 우수, 8B 파라미터)
                  - mistral:7b (균형잡힌 성능)
            base_url: Ollama API 주소 (기본: http://localhost:11434)
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"

        # Ollama가 실행 중인지 확인
        if not self._check_ollama_running():
            raise ConnectionError(
                "Ollama가 실행되지 않았습니다.\n"
                "1. Ollama를 설치하세요: https://ollama.com\n"
                "2. 터미널에서 실행: ollama serve\n"
                f"3. 모델 다운로드: ollama pull {model}"
            )

        # 모델이 다운로드되어 있는지 확인
        if not self._check_model_exists():
            print(f"모델 {model}을 다운로드합니다. 시간이 걸릴 수 있습니다...")
            self._pull_model()

        # 시스템 프롬프트 로드
        self.system_prompt = self._load_system_prompt()

    def _check_ollama_running(self) -> bool:
        """Ollama가 실행 중인지 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _check_model_exists(self) -> bool:
        """모델이 다운로드되어 있는지 확인"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m.get("name") == self.model for m in models)
            return False
        except:
            return False

    def _pull_model(self):
        """모델 다운로드"""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                stream=True,
                timeout=300
            )
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "status" in data:
                        print(f"다운로드 중: {data['status']}")
        except Exception as e:
            print(f"모델 다운로드 실패: {e}")

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

출력은 반드시 유효한 JSON 형식이어야 합니다.
"""

    def analyze_text_blocks(self, text_blocks: List[Dict]) -> Dict:
        """
        텍스트 블록 리스트를 로컬 LLM으로 분석하여 구조화

        Args:
            text_blocks: 텍스트 블록 리스트 (각 블록은 text, font_size, is_bold 등 포함)

        Returns:
            Dict: 계층적 토글 구조
        """
        # 입력 데이터 준비
        user_message = self._prepare_user_message(text_blocks)

        # 전체 프롬프트 구성
        full_prompt = f"{self.system_prompt}\n\n{user_message}"

        try:
            # Ollama API 호출
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json",  # JSON 형식 강제
                    "options": {
                        "temperature": 0.3,  # 일관성을 위해 낮은 temperature
                        "num_predict": 4096  # 최대 토큰 수
                    }
                },
                timeout=120  # 2분 타임아웃
            )

            if response.status_code != 200:
                print(f"Ollama API 오류: {response.status_code}")
                return None

            # 응답 파싱
            result_data = response.json()
            result_text = result_data.get("response", "")

            # JSON 파싱
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 재시도 (코드 블록 제거)
                result_text = result_text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                result_text = result_text.strip()

                try:
                    result = json.loads(result_text)
                    return result
                except:
                    print(f"JSON 파싱 실패: {result_text[:200]}...")
                    return None

        except requests.Timeout:
            print("Ollama 요청 시간 초과 (2분). 문서가 너무 클 수 있습니다.")
            return None
        except Exception as e:
            print(f"Ollama 분석 오류: {e}")
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
        message += "5. 반드시 유효한 JSON 형식으로 출력하세요.\n"
        message += "6. JSON 외 다른 텍스트는 포함하지 마세요.\n"

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

        # 로컬 LLM으로 분석
        print(f"로컬 LLM({self.model})으로 분석 중...")
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


def is_ollama_available() -> bool:
    """Ollama가 사용 가능한지 확인"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_available_models() -> List[str]:
    """다운로드된 Ollama 모델 목록 반환"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m.get("name") for m in models]
        return []
    except:
        return []
