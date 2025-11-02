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
        ok_button.clicked.connect(self.accept)
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
            self.page_count_label.setText(f"{self.total_pages}페이지 선택됨")
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
        self.page_count_label.setText(f"{page_count}페이지 선택됨")

        self.start_page = start
        self.end_page = end

    def get_page_range(self):
        """선택된 페이지 범위 반환"""
        if self.use_all_pages:
            return None  # None은 전체 페이지를 의미
        else:
            return (self.start_page, self.end_page)

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
