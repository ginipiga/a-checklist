"""
PDF 페이지 범위 선택 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QCheckBox,
                             QSpinBox, QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt


class PageRangeDialog(QDialog):
    """PDF 페이지 범위를 선택하는 다이얼로그"""

    def __init__(self, pdf_path: str, total_pages: int, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.total_pages = total_pages
        self.start_page = 1
        self.end_page = total_pages
        self.use_all_pages = True
        self.search_keyword = ""  # 검색어

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("PDF 페이지 범위 선택")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # 파일 정보
        info_label = QLabel(f"<b>PDF 파일:</b> {self.pdf_path}<br>"
                           f"<b>전체 페이지:</b> {self.total_pages}페이지")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 구분선
        layout.addSpacing(10)

        # 전체 페이지 사용 체크박스
        self.all_pages_checkbox = QCheckBox("전체 페이지 사용")
        self.all_pages_checkbox.setChecked(True)
        self.all_pages_checkbox.stateChanged.connect(self.on_all_pages_changed)
        layout.addWidget(self.all_pages_checkbox)

        # 페이지 범위 그룹
        self.range_group = QGroupBox("페이지 범위 선택")
        range_layout = QFormLayout()

        # 시작 페이지
        self.start_spinbox = QSpinBox()
        self.start_spinbox.setMinimum(1)
        self.start_spinbox.setMaximum(self.total_pages)
        self.start_spinbox.setValue(1)
        self.start_spinbox.valueChanged.connect(self.validate_range)
        range_layout.addRow("시작 페이지:", self.start_spinbox)

        # 종료 페이지
        self.end_spinbox = QSpinBox()
        self.end_spinbox.setMinimum(1)
        self.end_spinbox.setMaximum(self.total_pages)
        self.end_spinbox.setValue(self.total_pages)
        self.end_spinbox.valueChanged.connect(self.validate_range)
        range_layout.addRow("종료 페이지:", self.end_spinbox)

        # 선택된 페이지 수
        self.page_count_label = QLabel(f"{self.total_pages}페이지 선택됨")
        range_layout.addRow("", self.page_count_label)

        self.range_group.setLayout(range_layout)
        self.range_group.setEnabled(False)  # 초기에는 비활성화
        layout.addWidget(self.range_group)

        # 검색어 필터 그룹
        layout.addSpacing(10)
        self.search_group = QGroupBox("검색어 필터 (선택사항)")
        search_layout = QFormLayout()

        # 검색어 입력
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("예: 기본계획수립")
        search_layout.addRow("검색어:", self.search_input)

        # 설명 라벨
        search_help = QLabel("<small>검색어를 입력하면 해당 항목 하위의 체크리스트만 추출합니다.<br>"
                           "개요 수준을 자동 판단하여 바로 아래 수준까지만 체크리스트로 변환합니다.</small>")
        search_help.setWordWrap(True)
        search_help.setStyleSheet("color: #787774;")
        search_layout.addRow("", search_help)

        self.search_group.setLayout(search_layout)
        layout.addWidget(self.search_group)

        # 도움말
        layout.addSpacing(10)
        help_label = QLabel("💡 <i>선택한 페이지 범위만 체크리스트로 변환됩니다.</i>")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # 버튼
        layout.addSpacing(10)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.on_accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        # 스타일 적용
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #37352f;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e9e9e7;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: rgba(55, 53, 47, 0.08);
                border: none;
                border-radius: 3px;
                color: #37352f;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.12);
            }
            QPushButton:pressed {
                background-color: rgba(55, 53, 47, 0.16);
            }
            QPushButton:default {
                background-color: #0066cc;
                color: white;
            }
            QPushButton:default:hover {
                background-color: #0052a3;
            }
            QSpinBox {
                padding: 4px;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #0066cc;
                border-color: #0066cc;
            }
        """)

    def on_all_pages_changed(self, state):
        """전체 페이지 체크박스 상태 변경"""
        is_checked = (state == Qt.Checked)
        self.use_all_pages = is_checked
        self.range_group.setEnabled(not is_checked)

        if is_checked:
            self.start_page = 1
            self.end_page = self.total_pages
            # 전체 페이지가 10페이지 초과인 경우 경고 표시
            if self.total_pages > 10:
                self.page_count_label.setText(f"<font color='red'>{self.total_pages}페이지 선택됨 (최대 10페이지)</font>")
                self.page_count_label.setToolTip("⚠️ 처리 시간과 품질을 위해 10페이지 이하로 선택해주세요.")
            else:
                self.page_count_label.setText(f"{self.total_pages}페이지 선택됨")
                self.page_count_label.setToolTip("")
        else:
            self.validate_range()

    def validate_range(self):
        """페이지 범위 유효성 검사"""
        start = self.start_spinbox.value()
        end = self.end_spinbox.value()

        if start > end:
            # 시작 페이지가 종료 페이지보다 크면 자동 조정
            self.end_spinbox.setValue(start)
            end = start

        page_count = end - start + 1

        # 10페이지 제한 체크
        if page_count > 10:
            self.page_count_label.setText(f"<font color='red'>{page_count}페이지 선택됨 (최대 10페이지)</font>")
            self.page_count_label.setToolTip("⚠️ 처리 시간과 품질을 위해 10페이지 이하로 선택해주세요.")
        else:
            self.page_count_label.setText(f"{page_count}페이지 선택됨")
            self.page_count_label.setToolTip("")

        self.start_page = start
        self.end_page = end

    def on_accept(self):
        """확인 버튼 클릭 시 페이지 수 검증"""
        if not self.use_all_pages:
            page_count = self.end_page - self.start_page + 1
            if page_count > 10:
                reply = QMessageBox.warning(
                    self,
                    '페이지 수 제한',
                    f'선택한 페이지 수({page_count}페이지)가 너무 많습니다.\n\n'
                    '최대 10페이지까지만 선택할 수 있습니다.\n'
                    '처리 시간과 품질을 위해 페이지 범위를 줄여주세요.',
                    QMessageBox.Ok
                )
                return  # 다이얼로그를 닫지 않고 유지
        elif self.use_all_pages and self.total_pages > 10:
            reply = QMessageBox.warning(
                self,
                '페이지 수 제한',
                f'전체 페이지 수({self.total_pages}페이지)가 너무 많습니다.\n\n'
                '최대 10페이지까지만 선택할 수 있습니다.\n'
                '"페이지 범위 선택"을 체크하여 10페이지 이하로 선택해주세요.',
                QMessageBox.Ok
            )
            return  # 다이얼로그를 닫지 않고 유지

        # 검색어 저장
        self.search_keyword = self.search_input.text().strip()

        # 페이지 수가 10 이하면 승인
        self.accept()

    def get_page_range(self):
        """선택된 페이지 범위 및 검색어 반환"""
        page_range = None if self.use_all_pages else (self.start_page, self.end_page)
        return {
            'page_range': page_range,
            'search_keyword': self.search_keyword
        }

    @staticmethod
    def get_page_range_from_user(pdf_path: str, total_pages: int, parent=None):
        """
        사용자에게 페이지 범위를 입력받는 정적 메서드

        Args:
            pdf_path: PDF 파일 경로
            total_pages: 전체 페이지 수
            parent: 부모 위젯

        Returns:
            tuple: (start_page, end_page) 또는 None (전체 페이지) 또는 False (취소됨)
        """
        dialog = PageRangeDialog(pdf_path, total_pages, parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            return dialog.get_page_range()
        else:
            return False  # 취소됨
