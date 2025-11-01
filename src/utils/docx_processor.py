"""
Word(DOCX) 파일을 토글 구조로 변환하는 유틸리티
"""
import re
import os
from typing import List, Dict

try:
    from docx import Document
    from docx.document import Document as DocumentType
    from docx.text.paragraph import Paragraph
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False


class DOCXProcessor:
    """Word 파일을 처리하여 토글 구조로 변환"""

    def __init__(self, llm_mode: str = "none", use_template: bool = True):
        """
        Args:
            llm_mode: LLM 사용 모드
                     "none" - LLM 사용 안 함 (기본 규칙 기반)
                     "ollama" - 로컬 Ollama 사용 (안전, 무료)
                     "openai" - OpenAI API 사용 (정확하지만 비용 발생)
            use_template: 템플릿 사용 여부
        """
        if not DOCX_SUPPORT:
            raise ImportError("Word 처리를 위해 python-docx를 설치해주세요: pip install python-docx")

        self.llm_mode = llm_mode.lower()
        self.llm_analyzer = None
        self.use_template = use_template

        # 템플릿 매니저 초기화
        if use_template:
            try:
                from .template_manager import TemplateManager
                self.template_manager = TemplateManager()
            except ImportError:
                self.template_manager = None
                self.use_template = False

        # LLM 분석기 초기화
        if self.llm_mode == "ollama":
            try:
                from .local_llm_analyzer import OllamaAnalyzer, is_ollama_available
                if is_ollama_available():
                    self.llm_analyzer = OllamaAnalyzer()
                    print("✅ 로컬 LLM(Ollama) 문서 분석 모드 활성화 - 데이터 유출 걱정 없음!")
                else:
                    print("⚠️ Ollama가 실행되지 않았습니다. 기본 모드로 전환합니다.")
                    print("   설치: https://ollama.com")
                    self.llm_mode = "none"
            except Exception as e:
                print(f"⚠️ Ollama 초기화 실패: {e}")
                print("   기본 모드로 전환합니다.")
                self.llm_mode = "none"

        elif self.llm_mode == "openai":
            try:
                from .llm_analyzer import LLMDocumentAnalyzer, is_llm_available
                if is_llm_available():
                    self.llm_analyzer = LLMDocumentAnalyzer()
                    print("✅ OpenAI LLM 문서 분석 모드 활성화")
                    print("⚠️ 주의: 문서 내용이 OpenAI 서버로 전송됩니다.")
                else:
                    print("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                    print("   기본 모드로 전환합니다.")
                    self.llm_mode = "none"
            except ImportError as e:
                print(f"⚠️ OpenAI 라이브러리를 불러올 수 없습니다: {e}")
                print("   설치: pip install openai")
                print("   기본 모드로 전환합니다.")
                self.llm_mode = "none"

        # 가중치 평가기 초기화
        try:
            from .weight_evaluator import WeightEvaluator
            self.evaluator = WeightEvaluator()
            self.use_weight_evaluation = True
        except ImportError:
            self.evaluator = None
            self.use_weight_evaluation = False

    def extract_paragraphs_from_docx(self, docx_path: str) -> List[Dict]:
        """
        Word 문서에서 문단을 추출하고 구조화된 데이터로 반환

        Args:
            docx_path: Word 파일 경로

        Returns:
            List[Dict]: 구조화된 문단 리스트
        """
        paragraphs = []

        try:
            doc = Document(docx_path)

            for para in doc.paragraphs:
                text = para.text.strip()

                if not text:
                    continue

                # 스타일 정보 추출
                style_name = para.style.name if para.style else "Normal"
                is_heading = 'Heading' in style_name
                heading_level = 0

                if is_heading:
                    # Heading 1, Heading 2 등에서 레벨 추출
                    match = re.search(r'Heading (\d+)', style_name)
                    if match:
                        heading_level = int(match.group(1))

                # 폰트 정보 (첫 번째 run의 정보 사용)
                is_bold = False
                font_size = 12

                if para.runs:
                    first_run = para.runs[0]
                    if first_run.bold:
                        is_bold = True
                    if first_run.font.size:
                        font_size = first_run.font.size.pt

                paragraphs.append({
                    "text": text,
                    "style": style_name,
                    "is_heading": is_heading,
                    "heading_level": heading_level,
                    "is_bold": is_bold,
                    "font_size": font_size
                })

        except Exception as e:
            print(f"Word 문서 읽기 오류: {e}")

        return paragraphs

    def detect_structure(self, paragraphs: List[Dict]) -> List[Dict]:
        """
        문단에서 제목, 부제목, 본문을 구분

        Args:
            paragraphs: 문단 리스트

        Returns:
            List[Dict]: 구조화된 항목 리스트
        """
        if not paragraphs:
            return []

        structured_items = []

        for para in paragraphs:
            text = para["text"].strip()
            if not text:
                continue

            # 구조 분석
            level = self._determine_level(para)
            item_type = self._determine_type(text, para)

            structured_items.append({
                "text": text,
                "level": level,
                "type": item_type,
                "is_bold": para["is_bold"]
            })

        return structured_items

    def _determine_level(self, para: Dict) -> int:
        """
        문단의 계층 레벨 결정 (0: 루트, 1: 하위, 2: 하위의 하위...)

        Args:
            para: 문단 정보

        Returns:
            int: 계층 레벨
        """
        text = para["text"]

        # Heading 스타일이 있으면 우선 사용
        if para["is_heading"]:
            return max(0, para["heading_level"] - 1)

        # 숫자 패턴으로 레벨 결정
        if re.match(r'^[IVX]+\.\s+', text):  # I. II. III.
            return 0
        elif re.match(r'^\d+\.\s+', text):  # 1. 2. 3.
            return 1
        elif re.match(r'^\d+\.\d+\.\s+', text):  # 1.1. 1.2.
            return 2
        elif re.match(r'^\d+\.\d+\.\d+\.\s+', text):  # 1.1.1.
            return 3
        elif re.match(r'^\(\d+\)\s+', text):  # (1) (2)
            return 2
        elif re.match(r'^[가-힣]\)\s+', text):  # 가) 나) 다)
            return 3
        elif re.match(r'^[①-⑳]\s+', text):  # ① ② ③
            return 3

        # 굵기로 레벨 결정
        if para["is_bold"]:
            if para["font_size"] >= 14:
                return 0
            elif para["font_size"] >= 12:
                return 1
            else:
                return 2

        return 3  # 일반 본문

    def _determine_type(self, text: str, para: Dict) -> str:
        """
        텍스트 타입 결정 (header, list, paragraph)

        Args:
            text: 텍스트
            para: 문단 정보

        Returns:
            str: 타입
        """
        # 제목 스타일
        if para["is_heading"]:
            return "header"

        # 목록 패턴
        if re.match(r'^[-•·]\s+', text):
            return "list"
        elif re.match(r'^\d+[.)]\s+', text):
            return "list"
        elif re.match(r'^[가-힣][.)]\s+', text):
            return "list"
        elif re.match(r'^[①-⑳]\s+', text):
            return "list"

        # 짧고 굵은 텍스트는 제목
        if len(text) < 100 and para["is_bold"]:
            return "header"

        return "paragraph"

    def convert_to_toggle_structure(self, structured_items: List[Dict]) -> Dict:
        """
        구조화된 항목을 토글 구조로 변환

        Args:
            structured_items: 구조화된 항목 리스트

        Returns:
            Dict: 토글 구조 데이터
        """
        if not structured_items:
            return None

        # 최상위 항목 생성
        root_title = "Word 문서"

        # 첫 번째 항목이 큰 제목이면 사용
        if structured_items and structured_items[0]["level"] == 0:
            root_title = self._clean_title(structured_items[0]["text"])
            structured_items = structured_items[1:]  # 첫 항목 제거

        root_toggle = {
            "title": root_title,
            "content": "",
            "current_score": 0,
            "max_score": 100,
            "children": [],
            "checklist": []
        }

        # 계층 구조 생성
        self._build_hierarchy(root_toggle, structured_items, 0, 0)

        return root_toggle

    def _build_hierarchy(self, parent: Dict, items: List[Dict], start_idx: int, parent_level: int) -> int:
        """
        재귀적으로 계층 구조 생성

        Args:
            parent: 부모 토글
            items: 항목 리스트
            start_idx: 시작 인덱스
            parent_level: 부모 레벨

        Returns:
            int: 처리된 마지막 인덱스
        """
        i = start_idx
        current_child = None

        while i < len(items):
            item = items[i]
            level = item["level"]
            text = item["text"]
            item_type = item["type"]

            # 같은 레벨이거나 상위 레벨이면 종료
            if level <= parent_level:
                break

            # 바로 하위 레벨인 경우
            if level == parent_level + 1:
                # 목록 항목은 체크리스트로
                if item_type == "list":
                    checklist_text = self._clean_list_text(text)
                    checklist_item = {
                        "text": checklist_text,
                        "is_checked": False,
                        "score": 1
                    }

                    # 가중치 평가 자동 적용
                    if self.use_weight_evaluation and self.evaluator:
                        weight_eval = self._auto_evaluate_checklist(checklist_text)
                        if weight_eval:
                            checklist_item["weight_evaluation"] = weight_eval
                            checklist_item["score"] = weight_eval["evaluation"]["final_score"]

                    parent["checklist"].append(checklist_item)
                    i += 1
                else:
                    # 새 하위 토글 생성
                    child_title = self._clean_title(text)
                    current_child = {
                        "title": child_title[:100],  # 제목 길이 제한
                        "content": "",
                        "current_score": 0,
                        "max_score": 100,
                        "children": [],
                        "checklist": []
                    }
                    parent["children"].append(current_child)
                    i += 1

            # 더 하위 레벨인 경우 - 재귀 호출
            elif level > parent_level + 1:
                if current_child:
                    i = self._build_hierarchy(current_child, items, i, level - 1)
                else:
                    # 부모가 없으면 본문에 추가
                    if parent["content"]:
                        parent["content"] += "\n\n"
                    parent["content"] += text
                    i += 1
            else:
                i += 1

        return i

    def _clean_title(self, text: str) -> str:
        """제목 텍스트 정리"""
        # 번호 패턴 제거
        text = re.sub(r'^[IVX]+\.\s+', '', text)
        text = re.sub(r'^\d+\.\s+', '', text)
        text = re.sub(r'^\d+\.\d+\.\s+', '', text)
        text = re.sub(r'^\d+\.\d+\.\d+\.\s+', '', text)
        text = re.sub(r'^\(\d+\)\s+', '', text)
        text = re.sub(r'^[가-힣]\)\s+', '', text)
        text = re.sub(r'^[①-⑳]\s+', '', text)

        return text.strip()

    def _clean_list_text(self, text: str) -> str:
        """목록 텍스트 정리"""
        # 목록 기호 제거
        text = re.sub(r'^[-•·]\s+', '', text)
        text = re.sub(r'^\d+[.)]\s+', '', text)
        text = re.sub(r'^[가-힣][.)]\s+', '', text)
        text = re.sub(r'^[①-⑳]\s+', '', text)

        return text.strip()

    def _auto_evaluate_checklist(self, text: str) -> Dict:
        """
        체크리스트 항목을 자동으로 평가

        Args:
            text: 체크리스트 항목 텍스트

        Returns:
            Dict: 가중치 평가 정보
        """
        if not self.evaluator:
            return None

        # 키워드 기반 자동 점수 부여 (PDF와 동일한 로직 사용)
        scores = self._analyze_text_for_scores(text)

        # 평가 수행
        try:
            evaluation = self.evaluator.evaluate_checklist_item(
                c1_score=scores["C1"],
                c1_rationale=scores["C1_rationale"],
                c2_score=scores["C2"],
                c2_rationale=scores["C2_rationale"],
                c3_score=scores["C3"],
                c3_rationale=scores["C3_rationale"],
                c4_score=scores["C4"],
                c4_rationale=scores["C4_rationale"],
                c5_score=scores["C5"],
                c5_rationale=scores["C5_rationale"],
                uncertainty_factor=scores["U"],
                dependency_factor=scores["D"],
                regulatory_gate_flag=scores["G"]
            )

            result = self.evaluator.create_checklist_item_result(
                item_id=0,
                category=scores["category"],
                item=text,
                evaluation=evaluation
            )

            return result

        except Exception as e:
            print(f"가중치 평가 실패: {e}")
            return None

    def _analyze_text_for_scores(self, text: str) -> Dict:
        """
        텍스트 분석하여 자동으로 점수 산정

        Args:
            text: 분석할 텍스트

        Returns:
            Dict: 점수 및 근거
        """
        text_lower = text.lower()

        # 기본 점수
        scores = {
            "C1": 3, "C1_rationale": "일반적인 검토 항목",
            "C2": 3, "C2_rationale": "일반적인 비용/일정 영향",
            "C3": 3, "C3_rationale": "일반적인 환경/안전 고려사항",
            "C4": 3, "C4_rationale": "일반적인 운영 영향",
            "C5": 3, "C5_rationale": "일반적인 수정 난이도",
            "U": 1.0,
            "D": 1.0,
            "G": 0.0,
            "category": "일반"
        }

        # C1: 승인/법규 관문성
        approval_keywords = ["승인", "인허가", "허가", "면허", "등록", "신고", "협의", "법정", "규제"]
        if any(k in text for k in approval_keywords):
            scores["C1"] = 4
            scores["C1_rationale"] = "인허가 또는 승인 관련 항목"
            scores["category"] = "승인/규제"
            if "필수" in text or "법정" in text:
                scores["C1"] = 5
                scores["C1_rationale"] = "법정 필수 승인 항목"
                scores["G"] = 0.5

        # C2: 비용/일정 영향
        cost_keywords = ["비용", "예산", "capex", "opex", "투자", "지출"]
        schedule_keywords = ["일정", "공정", "지연", "납기", "완료", "기한"]
        if any(k in text_lower for k in cost_keywords):
            scores["C2"] = 4
            scores["C2_rationale"] = "비용 영향이 있는 항목"
            scores["category"] = "비용"
        if any(k in text_lower for k in schedule_keywords):
            scores["C2"] = max(scores["C2"], 4)
            scores["C2_rationale"] = "일정 영향이 있는 항목"

        # C3: 환경·안전 영향
        env_keywords = ["환경", "eia", "환경영향평가", "소음", "대기", "수질", "폐기물", "민원"]
        safety_keywords = ["안전", "위험", "사고", "재해", "보안", "화재", "방재"]
        if any(k in text_lower for k in env_keywords):
            scores["C3"] = 4
            scores["C3_rationale"] = "환경 영향이 있는 항목"
            scores["category"] = "환경"
            if "환경영향평가" in text or "eia" in text_lower:
                scores["C3"] = 5
                scores["C3_rationale"] = "환경영향평가 관련 핵심 항목"
        if any(k in text for k in safety_keywords):
            scores["C3"] = max(scores["C3"], 4)
            scores["C3_rationale"] = "안전 관련 항목"

        # C4: 운영성 영향
        operation_keywords = ["운영", "otp", "수하물", "회전율", "용량", "처리량", "서비스", "효율"]
        if any(k in text_lower for k in operation_keywords):
            scores["C4"] = 4
            scores["C4_rationale"] = "운영에 영향을 미치는 항목"
            scores["category"] = "운영"
            if "용량" in text or "처리량" in text:
                scores["C4"] = 5
                scores["C4_rationale"] = "공항 용량에 치명적 영향"

        # C5: 대체/가역성
        irreversible_keywords = ["건설", "구조물", "인프라", "설계", "배치", "레이아웃", "설치"]
        if any(k in text for k in irreversible_keywords):
            scores["C5"] = 4
            scores["C5_rationale"] = "구조적 변경으로 수정이 어려움"
            if "건설" in text or "구조물" in text:
                scores["C5"] = 5
                scores["C5_rationale"] = "건설 후 수정 불가능"

        # 불확실성 계수
        if "계획" in text or "검토" in text:
            scores["U"] = 1.1  # 아직 확정되지 않아 불확실성 있음

        # 의존성 계수
        if "기본" in text or "핵심" in text or "주요" in text:
            scores["D"] = 1.2  # 다른 결정에 영향을 미치는 허브성

        return scores

    def process_docx(self, docx_path: str) -> Dict:
        """
        Word 파일을 처리하여 토글 구조로 변환

        Args:
            docx_path: Word 파일 경로

        Returns:
            Dict: 토글 구조 데이터
        """
        filename = os.path.basename(docx_path)
        filename_without_ext = os.path.splitext(filename)[0]

        # 1. 문단 추출
        paragraphs = self.extract_paragraphs_from_docx(docx_path)

        if not paragraphs:
            return None

        # 템플릿 사용 시
        if self.use_template and self.template_manager:
            # 전체 텍스트를 문자열로 합치기
            content = "\n\n".join([p["text"] for p in paragraphs])

            # 템플릿 적용
            toggle_data = self.template_manager.create_project_from_file(
                filename_without_ext,
                content
            )

            return toggle_data

        # 템플릿 미사용 시
        # LLM 모드 사용
        if self.llm_mode != "none" and self.llm_analyzer:
            print(f"📄 {self.llm_mode.upper()} LLM으로 문서 구조 분석 중...")
            toggle_data = self.llm_analyzer.analyze_and_convert(paragraphs, "word")
            if toggle_data:
                print("✅ LLM 분석 완료")
                return toggle_data
            else:
                print("❌ LLM 분석 실패, 기본 모드로 전환합니다.")

        # 2. 구조 분석 (기본 모드)
        structured_items = self.detect_structure(paragraphs)

        # 3. 토글 구조로 변환
        toggle_data = self.convert_to_toggle_structure(structured_items)

        return toggle_data


def is_docx_supported() -> bool:
    """Word 처리가 지원되는지 확인"""
    return DOCX_SUPPORT
