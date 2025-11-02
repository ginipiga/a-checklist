"""
체크리스트 프린트 유틸리티
A4 용지 크기로 체크리스트를 포맷하여 프린트하는 기능 제공
"""

from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtGui import QTextDocument, QTextCursor, QFont, QTextCharFormat, QTextTableFormat, QPageLayout, QTextBlockFormat, QTextLength
from PyQt5.QtCore import Qt, QMarginsF


class ChecklistPrinter:
    """체크리스트를 A4 용지에 프린트하는 클래스"""

    def __init__(self):
        self.printer = QPrinter(QPrinter.HighResolution)
        self.setup_printer()

    def setup_printer(self):
        """프린터 기본 설정"""
        # A4 용지 크기 설정
        self.printer.setPageSize(QPrinter.A4)
        # 세로 방향
        self.printer.setOrientation(QPrinter.Portrait)
        # 여백 설정 (mm 단위) - PyQt5 호환 방식
        try:
            # 최신 PyQt5 방식
            layout = self.printer.pageLayout()
            layout.setUnits(QPageLayout.Millimeter)
            layout.setMargins(QMarginsF(15, 15, 15, 15))
            self.printer.setPageLayout(layout)
        except:
            # 구 버전 PyQt5 방식
            self.printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

    def create_checklist_document(self, root_items):
        """체크리스트 데이터를 HTML 문서로 변환"""
        document = QTextDocument()
        cursor = QTextCursor(document)

        # 문서 제목 설정
        title_format = QTextCharFormat()
        title_font = QFont("맑은 고딕", 16, QFont.Bold)
        title_format.setFont(title_font)

        cursor.insertText("리스크 관리 체크리스트\n\n", title_format)

        # 전체 통계 정보 추가
        from datetime import datetime
        info_format = QTextCharFormat()
        info_font = QFont("맑은 고딕", 9)
        info_format.setFont(info_font)
        info_format.setForeground(Qt.darkGray)

        total_score = sum(item.get_total_score() for item in root_items)
        total_max = sum(item.get_total_max_score() for item in root_items)
        completion = (total_score / total_max * 100) if total_max > 0 else 0

        cursor.insertText(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", info_format)
        cursor.insertText(f"전체 진행률: {total_score}/{total_max}점 ({completion:.1f}%)\n", info_format)
        cursor.insertText(f"총 작업 수: {len(root_items)}개\n\n", info_format)

        # 구분선
        separator_format = QTextCharFormat()
        separator_format.setForeground(Qt.lightGray)
        cursor.insertText("=" * 80 + "\n\n", separator_format)

        # 일반 텍스트 포맷
        normal_format = QTextCharFormat()
        normal_font = QFont("맑은 고딕", 10)
        normal_format.setFont(normal_font)

        # 각 루트 아이템에 대해 처리
        for idx, root_item in enumerate(root_items, 1):
            # 루트 아이템 제목
            header_format = QTextCharFormat()
            header_font = QFont("맑은 고딕", 12, QFont.Bold)
            header_format.setFont(header_font)

            cursor.insertText(f"{idx}. {root_item.title}\n", header_format)

            # 진행률, 마감기한 등 메타 정보 표시
            meta_format = QTextCharFormat()
            meta_font = QFont("맑은 고딕", 9)
            meta_format.setFont(meta_font)
            meta_format.setForeground(Qt.darkGray)

            item_score = root_item.get_total_score()
            item_max = root_item.get_total_max_score()
            item_completion = (item_score / item_max * 100) if item_max > 0 else 0

            meta_info = f"   진행률: {item_score}/{item_max}점 ({item_completion:.1f}%)"

            if hasattr(root_item, 'deadline') and root_item.deadline:
                meta_info += f" | 마감기한: {root_item.deadline}"

            if hasattr(root_item, 'date') and root_item.date:
                meta_info += f" | 날짜: {root_item.date}"

            cursor.insertText(meta_info + "\n", meta_format)

            # 내용이 있으면 표시
            if root_item.content:
                cursor.insertText(f"   {root_item.content}\n", normal_format)

            # 체크리스트 항목들
            if hasattr(root_item, 'checklist') and root_item.checklist:
                cursor.insertText("\n", normal_format)
                self._add_checklist_items(cursor, root_item.checklist, normal_format, indent=1)

            # 하위 토글들도 처리
            if root_item.children:
                self._add_children_items(cursor, root_item.children, normal_format, level=1)

            cursor.insertText("\n", normal_format)

        return document

    def _add_checklist_items(self, cursor, checklist_items, text_format, indent=0):
        """체크리스트 항목들을 문서에 추가"""
        indent_str = "   " * indent

        for idx, item in enumerate(checklist_items, 1):
            # 테이블 생성 (번호/체크박스/내용 | 우선순위 | 점수)
            table_format = QTextTableFormat()
            table_format.setBorder(0)
            table_format.setCellPadding(2)
            table_format.setCellSpacing(0)
            table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))

            # 컬럼 너비 설정: 내용 70%, 우선순위 15%, 점수 15%
            constraints = [
                QTextLength(QTextLength.PercentageLength, 70),
                QTextLength(QTextLength.PercentageLength, 15),
                QTextLength(QTextLength.PercentageLength, 15)
            ]
            table_format.setColumnWidthConstraints(constraints)

            # 1행 3열 테이블 생성
            table = cursor.insertTable(1, 3, table_format)

            # 첫 번째 셀: 번호, 체크박스와 텍스트 (왼쪽 정렬)
            cell = table.cellAt(0, 0)
            cell_cursor = cell.firstCursorPosition()

            checkbox = "☑" if item.is_checked else "☐"
            text = item.summary if hasattr(item, 'summary') and item.summary else item.text

            left_format = QTextCharFormat()
            left_format.setFont(QFont("맑은 고딕", 10))
            cell_cursor.insertText(f"{indent_str}{idx}. {checkbox} {text}", left_format)

            # 두 번째 셀: 우선순위 (가운데 정렬)
            cell = table.cellAt(0, 1)
            cell_cursor = cell.firstCursorPosition()

            priority_format = QTextCharFormat()
            priority_format.setFont(QFont("맑은 고딕", 9))

            priority = ""
            if hasattr(item, 'get_priority'):
                p = item.get_priority()
                if p and p != 'N/A':
                    priority = f"[{p}]"
                    # 우선순위별 색상
                    priority_colors = {
                        'Critical': Qt.red,
                        'High': Qt.darkYellow,
                        'Medium': Qt.blue,
                        'Low': Qt.darkGreen,
                        'Minimal': Qt.gray
                    }
                    if p in priority_colors:
                        priority_format.setForeground(priority_colors[p])

            block_format = QTextBlockFormat()
            block_format.setAlignment(Qt.AlignCenter)
            cell_cursor.setBlockFormat(block_format)
            cell_cursor.insertText(priority, priority_format)

            # 세 번째 셀: 점수 (오른쪽 정렬)
            cell = table.cellAt(0, 2)
            cell_cursor = cell.firstCursorPosition()

            score_format = QTextCharFormat()
            score_format.setFont(QFont("맑은 고딕", 10, QFont.Bold))
            score_info = f"{item.score}점" if hasattr(item, 'score') else ""

            block_format = QTextBlockFormat()
            block_format.setAlignment(Qt.AlignRight)
            cell_cursor.setBlockFormat(block_format)
            cell_cursor.insertText(score_info, score_format)

            # 테이블 이후 커서 위치 조정
            cursor.movePosition(QTextCursor.End)

            # 상세 내용이 있으면 추가
            if hasattr(item, 'detail') and item.detail:
                detail_format = QTextCharFormat()
                detail_font = QFont("맑은 고딕", 9)
                detail_format.setFont(detail_font)
                detail_format.setForeground(Qt.darkGray)

                cursor.insertText(f"{indent_str}   상세: {item.detail}\n", detail_format)

    def _add_children_items(self, cursor, children, text_format, level=0):
        """하위 토글 항목들을 재귀적으로 추가"""
        indent_str = "   " * level

        for child in children:
            # 하위 토글 제목
            child_format = QTextCharFormat()
            child_font = QFont("맑은 고딕", 11, QFont.Bold)
            child_format.setFont(child_font)

            cursor.insertText(f"\n{indent_str}▸ {child.title}\n", child_format)

            # 하위 토글의 메타 정보
            meta_format = QTextCharFormat()
            meta_font = QFont("맑은 고딕", 9)
            meta_format.setFont(meta_font)
            meta_format.setForeground(Qt.darkGray)

            child_score = child.get_total_score()
            child_max = child.get_total_max_score()
            child_completion = (child_score / child_max * 100) if child_max > 0 else 0

            child_meta_info = f"{indent_str}  진행률: {child_score}/{child_max}점 ({child_completion:.1f}%)"

            if hasattr(child, 'deadline') and child.deadline:
                child_meta_info += f" | 마감기한: {child.deadline}"

            if hasattr(child, 'date') and child.date:
                child_meta_info += f" | 날짜: {child.date}"

            cursor.insertText(child_meta_info + "\n", meta_format)

            # 내용
            if child.content:
                cursor.insertText(f"{indent_str}  {child.content}\n", text_format)

            # 체크리스트
            if hasattr(child, 'checklist') and child.checklist:
                cursor.insertText("\n", text_format)
                self._add_checklist_items(cursor, child.checklist, text_format, indent=level+1)

            # 더 하위 항목들
            if child.children:
                self._add_children_items(cursor, child.children, text_format, level=level+1)

    def print_preview(self, root_items, parent_widget=None):
        """프린트 미리보기 다이얼로그 표시"""
        document = self.create_checklist_document(root_items)

        preview = QPrintPreviewDialog(self.printer, parent_widget)
        preview.setWindowTitle("프린트 미리보기")
        preview.paintRequested.connect(lambda p: document.print_(p))

        # 전체화면으로 표시
        preview.showMaximized()

        return preview.exec_()

    def print_dialog(self, root_items, parent_widget=None):
        """프린트 다이얼로그를 통해 프린트"""
        document = self.create_checklist_document(root_items)

        dialog = QPrintDialog(self.printer, parent_widget)
        dialog.setWindowTitle("체크리스트 프린트")

        if dialog.exec_() == QPrintDialog.Accepted:
            document.print_(self.printer)
            return True
        return False

    def export_to_pdf(self, root_items, filename):
        """PDF 파일로 내보내기"""
        document = self.create_checklist_document(root_items)

        # PDF로 저장
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(filename)

        document.print_(self.printer)

        return True
