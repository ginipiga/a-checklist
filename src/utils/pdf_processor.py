"""
PDF 파일을 토글 구조로 변환하는 유틸리티
"""
import re
import os
from typing import List, Dict, Tuple, Optional
try:
    import fitz  # PyMuPDF
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class PDFProcessor:
    """PDF 파일을 처리하여 토글 구조로 변환"""

    def __init__(self, llm_mode: str = "none", use_template: bool = True):
        """
        Args:
            llm_mode: LLM 사용 모드
                     "none" - LLM 사용 안 함 (기본 규칙 기반)
                     "ollama" - 로컬 Ollama 사용 (안전, 무료)
                     "openai" - OpenAI API 사용 (정확하지만 비용 발생)
            use_template: 템플릿 사용 여부
        """
        if not PDF_SUPPORT:
            raise ImportError("PDF 처리를 위해 pymupdf와 pdfplumber를 설치해주세요: pip install pymupdf pdfplumber")

        self.llm_mode = llm_mode.lower()
        self.llm_analyzer = None
        self.use_template = use_template

        # 템플릿 매니저 초기화 (LLM 모드 전달)
        if use_template:
            try:
                from .template_manager import TemplateManager
                self.template_manager = TemplateManager(
                    use_smart_analysis=(llm_mode != "none"),
                    llm_mode=llm_mode
                )
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

    def extract_text_from_pdf(self, pdf_path: str, page_range: Optional[Tuple[int, int]] = None) -> List[Dict]:
        """
        PDF에서 텍스트를 추출하고 구조화된 데이터로 반환

        Args:
            pdf_path: PDF 파일 경로
            page_range: (시작 페이지, 종료 페이지) 튜플. None이면 전체 페이지

        Returns:
            List[Dict]: 구조화된 텍스트 블록 리스트
        """
        text_blocks = []

        try:
            doc = fitz.open(pdf_path)

            # 페이지 범위 결정
            if page_range:
                start_page, end_page = page_range
                # 1-based를 0-based로 변환
                start_idx = max(0, start_page - 1)
                end_idx = min(len(doc), end_page)
            else:
                start_idx = 0
                end_idx = len(doc)

            for page_num in range(start_idx, end_idx):
                page = doc[page_num]
                page_dict = page.get_text("dict")

                for block in page_dict["blocks"]:
                    if block["type"] == 0:  # 텍스트 블록
                        block_text = ""
                        font_sizes = []
                        is_bold = False

                        for line in block["lines"]:
                            for span in line["spans"]:
                                block_text += span["text"]
                                font_sizes.append(span["size"])
                                # bold 플래그 확인
                                if span["flags"] & 2**4:
                                    is_bold = True
                            block_text += " "

                        block_text = block_text.strip()

                        if block_text and len(block_text) > 1:
                            avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0

                            text_blocks.append({
                                "text": block_text,
                                "page": page_num + 1,
                                "font_size": avg_font_size,
                                "is_bold": is_bold,
                                "y_pos": block["bbox"][1]
                            })

            doc.close()

        except Exception as e:
            print(f"PDF 텍스트 추출 오류: {e}")

        return text_blocks

    def detect_structure(self, text_blocks: List[Dict]) -> List[Dict]:
        """
        텍스트 블록에서 제목, 부제목, 본문을 구분

        Args:
            text_blocks: 텍스트 블록 리스트

        Returns:
            List[Dict]: 구조화된 항목 리스트
        """
        if not text_blocks:
            return []

        # 폰트 크기 통계
        font_sizes = [block["font_size"] for block in text_blocks if block["font_size"] > 0]
        avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        max_size = max(font_sizes) if font_sizes else 12

        structured_items = []

        for block in text_blocks:
            text = block["text"].strip()
            if not text:
                continue

            # 구조 분석
            level = self._determine_level(block, avg_size, max_size)
            item_type = self._determine_type(text)

            structured_items.append({
                "text": text,
                "level": level,
                "type": item_type,
                "page": block["page"],
                "is_bold": block["is_bold"]
            })

        return structured_items

    def _determine_level(self, block: Dict, avg_size: float, max_size: float) -> int:
        """
        텍스트 블록의 계층 레벨 결정 (0: 루트, 1: 섹션, 2: 체크리스트, 3: 본문)

        Args:
            block: 텍스트 블록
            avg_size: 평균 폰트 크기
            max_size: 최대 폰트 크기

        Returns:
            int: 계층 레벨
        """
        text = block["text"]
        font_size = block["font_size"]
        is_bold = block["is_bold"]

        # 우선순위: 번호/기호 패턴 > 폰트 크기

        # 체크리스트 항목 (레벨 2)
        if re.match(r'^[•\-–—·○●◦◉▪▫]\s+', text):  # •, -, ○ 등
            return 2
        elif re.match(r'^\d+\)\s+', text):  # 1) 2) 3)
            return 2
        elif re.match(r'^[가-힣]\)\s+', text):  # 가) 나) 다)
            return 2
        elif re.match(r'^\(\d+\)\s+', text):  # (1) (2)
            return 2

        # 섹션 제목 (레벨 1)
        elif re.match(r'^\d+\.\s+', text):  # 1. 2. 3.
            return 1
        elif re.match(r'^[가-힣]\.\s+', text):  # 가. 나. 다.
            return 1
        elif re.match(r'^\d+\.\d+\s+', text):  # 1.1 1.2 (점 하나)
            return 1

        # 최상위 제목 (레벨 0)
        elif re.match(r'^[IVX]+\.\s+', text):  # I. II. III.
            return 0

        # 폰트 크기와 굵기로 레벨 결정
        elif font_size >= max_size * 0.9 and is_bold:
            return 0  # 최상위 제목
        elif font_size >= avg_size * 1.2 and is_bold:
            return 1  # 섹션 제목
        elif is_bold:
            return 2  # 소제목 또는 강조
        else:
            return 3  # 본문

    def _determine_type(self, text: str) -> str:
        """
        텍스트 타입 결정 (header, list, paragraph)

        Args:
            text: 텍스트

        Returns:
            str: 타입
        """
        # 체크리스트 항목 패턴
        if re.match(r'^[•\-–—·○●◦◉▪▫]\s+', text):
            return "list"
        elif re.match(r'^\d+\)\s+', text):
            return "list"
        elif re.match(r'^[가-힣]\)\s+', text):
            return "list"
        elif re.match(r'^\(\d+\)\s+', text):
            return "list"

        # 섹션 제목 패턴
        elif re.match(r'^\d+\.\s+', text):
            return "header"
        elif re.match(r'^[가-힣]\.\s+', text):
            return "header"

        # 짧은 텍스트는 제목으로 간주
        elif len(text) < 100:
            return "header"

        return "paragraph"

    def convert_to_toggle_structure(self, structured_items: List[Dict], filename: str = None, page_range: Optional[Tuple[int, int]] = None) -> Dict:
        """
        구조화된 항목을 토글 구조로 변환

        Args:
            structured_items: 구조화된 항목 리스트
            filename: PDF 파일명
            page_range: (시작 페이지, 종료 페이지) 튜플

        Returns:
            Dict: 토글 구조 데이터
        """
        if not structured_items:
            return None

        # 최상위 항목 생성
        if filename:
            # 파일명에서 확장자 제거
            filename_without_ext = os.path.splitext(filename)[0]
            if page_range:
                root_title = f"{filename_without_ext}, {page_range[0]}p-{page_range[1]}p"
            else:
                root_title = f"{filename_without_ext}"
        else:
            root_title = "PDF 문서"

        # 첫 번째 항목이 큰 제목이면 제목에 추가
        if structured_items and structured_items[0]["level"] == 0:
            first_title = self._clean_title(structured_items[0]["text"])
            # 페이지 정보가 있으면 함께 표시
            if filename and page_range:
                root_title = f"{filename_without_ext}, {page_range[0]}p-{page_range[1]}p"
            elif filename:
                root_title = f"{filename_without_ext}"
            else:
                root_title = first_title
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
        text = re.sub(r'^\(\d+\)\s+', '', text)
        text = re.sub(r'^[가-힣]\)\s+', '', text)

        return text.strip()

    def _clean_list_text(self, text: str) -> str:
        """목록 텍스트 정리"""
        # 목록 기호 제거
        text = re.sub(r'^[-•·]\s+', '', text)
        text = re.sub(r'^\d+[.)]\s+', '', text)
        text = re.sub(r'^[가-힣][.)]\s+', '', text)

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

        # 키워드 기반 자동 점수 부여
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

    def get_page_count(self, pdf_path: str) -> int:
        """
        PDF 파일의 전체 페이지 수 반환

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            int: 페이지 수
        """
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            print(f"PDF 페이지 수 확인 오류: {e}")
            return 0

    def filter_by_keyword(self, structured_items: List[Dict], search_keyword: str, parent_widget=None) -> List[Dict]:
        """
        검색어로 항목을 필터링하고 바로 아래 개요 수준까지만 추출

        Args:
            structured_items: 구조화된 항목 리스트
            search_keyword: 검색어
            parent_widget: 부모 위젯 (선택 다이얼로그 표시용)

        Returns:
            필터링된 항목 리스트
        """
        # 검색어를 포함하는 모든 항목 찾기 (띄어쓰기 무시)
        matched_items = []
        search_keyword_normalized = search_keyword.lower().replace(' ', '')

        for i, item in enumerate(structured_items):
            item_text = item['text'].lower()
            item_text_normalized = item_text.replace(' ', '')

            # 정확한 매칭 또는 띄어쓰기 무시 매칭
            if search_keyword.lower() in item_text or search_keyword_normalized in item_text_normalized:
                matched_items.append({
                    'index': i,
                    'text': item['text'],
                    'level': item['level']
                })

        if not matched_items:
            return []

        # 매칭된 항목이 여러 개인 경우 사용자에게 선택하도록 함
        found_index = matched_items[0]['index']  # 기본값: 첫 번째

        if len(matched_items) > 1:
            from components.keyword_selection_dialog import KeywordSelectionDialog

            dialog = KeywordSelectionDialog(search_keyword, matched_items, parent_widget)
            if dialog.exec_() == dialog.Accepted:
                selected_idx = dialog.get_selected_index()
                if selected_idx is not None:
                    found_index = selected_idx
                else:
                    return []  # 선택 취소
            else:
                return []  # 다이얼로그 취소

        # 선택된 항목 기준으로 필터링
        found_item = structured_items[found_index]
        parent_level = found_item['level']
        target_level = parent_level + 1  # 바로 아래 수준

        # 찾은 항목 이후의 항목들 중에서 target_level인 항목만 추출
        filtered_items = []

        for i in range(found_index + 1, len(structured_items)):
            item = structured_items[i]

            # 같거나 더 높은 수준의 항목이 나오면 중단 (다른 섹션 시작)
            if item['level'] <= parent_level:
                break

            # 바로 아래 수준의 항목만 추가
            if item['level'] == target_level:
                filtered_items.append(item)

        return filtered_items

    def process_pdf(self, pdf_path: str, page_range: Optional[Tuple[int, int]] = None, search_keyword: str = "", parent_widget=None) -> tuple:
        """
        PDF 파일을 처리하여 토글 구조로 변환

        Args:
            pdf_path: PDF 파일 경로
            page_range: (시작 페이지, 종료 페이지) 튜플. None이면 전체 페이지
            search_keyword: 검색어. 입력하면 해당 항목 하위만 추출
            parent_widget: 부모 위젯 (선택 다이얼로그 표시용)

        Returns:
            tuple: (토글 구조 데이터 또는 None, 에러 메시지 또는 None)
        """
        filename = os.path.basename(pdf_path)
        filename_without_ext = os.path.splitext(filename)[0]

        # 1. 텍스트 추출
        text_blocks = self.extract_text_from_pdf(pdf_path, page_range)

        if not text_blocks:
            return None, "PDF에서 텍스트를 추출할 수 없습니다"

        # 2. 지능형 구조 분석 (개선된 알고리즘)
        structured_items = self.detect_structure(text_blocks)

        # 3. 검색어 필터링 (검색어가 있는 경우)
        if search_keyword:
            filtered_items = self.filter_by_keyword(structured_items, search_keyword, parent_widget)
            if not filtered_items:
                return None, f"검색어 '{search_keyword}'를 찾을 수 없거나 선택이 취소되었습니다"

            # 필터링된 항목들을 체크리스트로 직접 변환
            toggle_data = {
                "title": f"{filename_without_ext} - {search_keyword}",
                "content": "",
                "current_score": 0,
                "max_score": 0,
                "children": [],
                "checklist": []
            }

            # 각 항목을 체크리스트 항목으로 변환
            for item in filtered_items:
                checklist_item = {
                    "text": self._clean_title(item['text']),
                    "is_checked": False,
                    "score": 1
                }
                toggle_data["checklist"].append(checklist_item)
                toggle_data["max_score"] += 1

            return toggle_data, None

        # 4. 토글 구조로 변환 (검색어가 없는 경우)
        toggle_data = self.convert_to_toggle_structure(structured_items, filename, page_range)

        return toggle_data, None


def is_pdf_supported() -> bool:
    """PDF 처리가 지원되는지 확인"""
    return PDF_SUPPORT
