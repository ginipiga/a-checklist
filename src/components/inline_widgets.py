"""
노션 스타일 인라인 위젯들
상세 내용 영역에 삽입 가능한 토글, 체크박스, 날짜 등
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QCheckBox, QLabel, QFrame, QDateEdit,
                             QCalendarWidget, QDialog, QSpinBox, QTextEdit, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QEvent
from PyQt5.QtGui import QFont
from datetime import datetime


class InlineTextBlockWidget(QFrame):
    """상세 내용 안에 삽입되는 텍스트 블록 - 노션 스타일"""
    content_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    slash_pressed = pyqtSignal(object)  # 이 블록에서 / 입력됨

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.text_value = text
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """UI 설정"""
        self.setFrameShape(QFrame.NoFrame)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(8)

        # 텍스트 입력 - 노션 스타일
        self.text_edit = QTextEdit(self.text_value)
        self.text_edit.setPlaceholderText("내용을 입력하거나 '/'를 입력하여 블록 추가...")
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setMinimumHeight(30)
        # 최대 높이 제한 제거 - 내용에 따라 자동으로 확장
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #37352f;
                font-size: 14px;
                padding: 4px;
                selection-background-color: #d4e5fc;
            }
            QTextEdit:focus {
                background-color: rgba(55, 53, 47, 0.03);
                border: none;
            }
        """)

        # 텍스트 변경 시 자동 높이 조절
        def adjust_height():
            doc_height = self.text_edit.document().size().height()
            # 최대 높이 제한 제거 - 내용에 따라 무제한 확장
            self.text_edit.setFixedHeight(max(int(doc_height) + 10, 30))

        self.text_edit.textChanged.connect(adjust_height)
        self.text_edit.textChanged.connect(self.on_text_changed)
        adjust_height()

        # 이벤트 필터 설치
        self.text_edit.installEventFilter(self)

        layout.addWidget(self.text_edit)

        # 삭제 버튼 (호버 시에만 표시)
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #9b9a97;
                font-weight: bold;
                font-size: 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #eb5757;
                color: #ffffff;
            }
        """)
        self.delete_btn.setToolTip("블록 삭제")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.delete_btn.setVisible(False)  # 기본적으로 숨김
        layout.addWidget(self.delete_btn)

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            InlineTextBlockWidget {
                background-color: transparent;
                border-radius: 3px;
                margin: 1px 0px;
            }
            InlineTextBlockWidget:hover {
                background-color: rgba(55, 53, 47, 0.03);
            }
        """)

    def eventFilter(self, obj, event):
        """이벤트 필터 - '/' 입력 감지"""
        if obj == self.text_edit and event.type() == QEvent.KeyPress:
            if event.text() == "/":
                # 현재 커서 위치 확인
                cursor = self.text_edit.textCursor()
                # 현재 줄의 시작이거나 공백 다음이면 슬래시 메뉴 표시
                cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
                text_before = cursor.selectedText().strip()

                if not text_before:  # 줄의 시작이면
                    self.slash_pressed.emit(self)
                    return True  # / 입력 차단
        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        """마우스 호버 - 삭제 버튼 표시"""
        self.delete_btn.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """마우스 나감 - 삭제 버튼 숨김"""
        self.delete_btn.setVisible(False)
        super().leaveEvent(event)

    def on_text_changed(self):
        """텍스트 변경"""
        self.text_value = self.text_edit.toPlainText()
        self.content_changed.emit()

    def on_delete_clicked(self):
        """삭제 버튼 클릭"""
        self.delete_requested.emit(self)

    def focus(self):
        """포커스 설정"""
        self.text_edit.setFocus()

    def get_cursor_position(self):
        """현재 커서 위치 반환 (슬래시 메뉴 표시용)"""
        cursor = self.text_edit.textCursor()
        cursor_rect = self.text_edit.cursorRect()
        return self.text_edit.mapToGlobal(cursor_rect.bottomLeft())

    def get_data(self):
        """데이터 반환"""
        return {
            "type": "text_block",
            "text": self.text_value
        }


class InlineToggleWidget(QFrame):
    """상세 내용 안에 삽입되는 인라인 토글"""
    content_changed = pyqtSignal()

    def __init__(self, title: str = "새 토글", content: str = "", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.content_text = content
        self.is_expanded = False
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """UI 설정"""
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # 헤더
        header_layout = QHBoxLayout()

        self.toggle_btn = QPushButton("▶")
        self.toggle_btn.setFixedSize(16, 16)
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        header_layout.addWidget(self.toggle_btn)

        self.title_edit = QLineEdit(self.title_text)
        self.title_edit.setPlaceholderText("토글 제목 입력...")
        self.title_edit.textChanged.connect(self.on_title_changed)
        header_layout.addWidget(self.title_edit)

        layout.addLayout(header_layout)

        # 내용
        self.content_edit = QLineEdit(self.content_text)
        self.content_edit.setPlaceholderText("내용 입력...")
        self.content_edit.setVisible(False)
        self.content_edit.textChanged.connect(self.on_content_changed)
        layout.addWidget(self.content_edit)

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            InlineToggleWidget {
                background-color: #f7f6f3;
                border: 1px solid #e3e2e0;
                border-radius: 3px;
                margin: 2px 0px;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: #37352f;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e3e2e0;
            }
            QLineEdit {
                background: transparent;
                border: none;
                color: #37352f;
                font-size: 13px;
                padding: 2px;
            }
        """)

    def toggle_expanded(self):
        """토글 열기/닫기"""
        self.is_expanded = not self.is_expanded
        self.toggle_btn.setText("▼" if self.is_expanded else "▶")
        self.content_edit.setVisible(self.is_expanded)
        self.content_changed.emit()

    def on_title_changed(self):
        """제목 변경"""
        self.title_text = self.title_edit.text()
        self.content_changed.emit()

    def on_content_changed(self):
        """내용 변경"""
        self.content_text = self.content_edit.text()
        self.content_changed.emit()

    def get_data(self):
        """데이터 반환"""
        return {
            "type": "inline_toggle",
            "title": self.title_text,
            "content": self.content_text,
            "is_expanded": self.is_expanded
        }


class InlineCheckboxWidget(QFrame):
    """상세 내용 안에 삽입되는 인라인 체크박스 - 토글 형식"""
    content_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)  # 삭제 요청 시그널

    # 클래스 변수로 항목 번호 카운터
    _item_counter = 0

    def __init__(self, text: str = "체크 항목", is_checked: bool = False, weight: int = 1, detail: str = "", parent=None):
        super().__init__(parent)
        self.text_value = text
        self.is_checked = is_checked
        self.weight = weight
        self.detail_value = detail
        self.is_expanded = False

        # 항목 번호 자동 할당
        InlineCheckboxWidget._item_counter += 1
        self.item_number = InlineCheckboxWidget._item_counter

        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """UI 설정 - 토글 형식"""
        self.setFrameShape(QFrame.NoFrame)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ===== 헤더 (항상 표시) =====
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # 토글 버튼
        self.toggle_btn = QPushButton("▶")
        self.toggle_btn.setFixedSize(16, 16)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #9b9a97;
                font-size: 10px;
            }
            QPushButton:hover {
                color: #37352f;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_detail)
        header_layout.addWidget(self.toggle_btn)

        # 항목 번호
        self.number_label = QLabel(f"{self.item_number}.")
        self.number_label.setStyleSheet("""
            QLabel {
                color: #9b9a97;
                font-size: 12px;
                min-width: 24px;
            }
        """)
        self.number_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.number_label)

        # 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.is_checked)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1.5px solid #d3d1cb;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                background-color: #f7f6f3;
                border-color: #9b9a97;
            }
            QCheckBox::indicator:checked {
                background-color: #2383e2;
                border-color: #2383e2;
            }
        """)
        self.checkbox.toggled.connect(self.on_checkbox_toggled)
        header_layout.addWidget(self.checkbox)

        # 제목 입력
        self.title_edit = QLineEdit(self.text_value)
        self.title_edit.setPlaceholderText(f"체크리스트 항목 {self.item_number}")
        self.title_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #37352f;
                font-size: 14px;
                padding: 4px;
            }
            QLineEdit:focus {
                background-color: rgba(55, 53, 47, 0.03);
            }
        """)
        self.title_edit.textChanged.connect(self.on_text_changed)
        header_layout.addWidget(self.title_edit)

        # 점수 표시
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(1, 100)
        self.weight_spin.setValue(self.weight)
        self.weight_spin.setPrefix("점수: ")
        self.weight_spin.setMaximumWidth(80)
        self.weight_spin.setStyleSheet("""
            QSpinBox {
                background-color: #f7f6f3;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                color: #37352f;
                font-size: 12px;
                padding: 2px 4px;
            }
            QSpinBox:focus {
                border: 1px solid #2383e2;
            }
        """)
        self.weight_spin.valueChanged.connect(self.on_weight_changed)
        header_layout.addWidget(self.weight_spin)

        # 삭제 버튼
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #9b9a97;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #eb5757;
                color: #ffffff;
                border-radius: 3px;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        header_layout.addWidget(self.delete_btn)

        main_layout.addLayout(header_layout)

        # ===== 상세 내용 (토글 시 표시) =====
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(48, 4, 4, 4)
        detail_layout.setSpacing(4)

        detail_label = QLabel("상세 내용:")
        detail_label.setStyleSheet("""
            QLabel {
                color: #787774;
                font-size: 11px;
            }
        """)
        detail_layout.addWidget(detail_label)

        self.detail_edit = QTextEdit(self.detail_value)
        self.detail_edit.setPlaceholderText("상세 내용을 입력하세요...")
        # 최대 높이 제한 제거 - 내용에 따라 자동 확장
        self.detail_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_edit.setMinimumHeight(60)
        self.detail_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.detail_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f7f6f3;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                color: #37352f;
                font-size: 13px;
                padding: 6px;
            }
            QTextEdit:focus {
                border: 1px solid #2383e2;
            }
        """)

        # 상세 내용도 자동 높이 조절
        def adjust_detail_height():
            doc_height = self.detail_edit.document().size().height()
            self.detail_edit.setFixedHeight(max(int(doc_height) + 10, 60))

        self.detail_edit.textChanged.connect(adjust_detail_height)
        self.detail_edit.textChanged.connect(self.on_detail_changed)
        adjust_detail_height()
        detail_layout.addWidget(self.detail_edit)

        self.detail_widget.setVisible(False)
        main_layout.addWidget(self.detail_widget)

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            InlineCheckboxWidget {
                background-color: #ffffff;
                border-radius: 3px;
                margin: 2px 0px;
                padding: 2px;
            }
            InlineCheckboxWidget:hover {
                background-color: #f7f6f3;
            }
        """)

    def toggle_detail(self):
        """상세 내용 토글"""
        self.is_expanded = not self.is_expanded
        self.detail_widget.setVisible(self.is_expanded)
        self.toggle_btn.setText("▼" if self.is_expanded else "▶")

    def on_checkbox_toggled(self):
        """체크박스 토글"""
        self.is_checked = self.checkbox.isChecked()
        self.update_title_style()
        self.content_changed.emit()

    def on_text_changed(self):
        """제목 텍스트 변경"""
        self.text_value = self.title_edit.text()
        self.content_changed.emit()

    def on_detail_changed(self):
        """상세 내용 변경"""
        self.detail_value = self.detail_edit.toPlainText()
        self.content_changed.emit()

    def on_weight_changed(self, value):
        """점수 변경"""
        self.weight = value
        self.content_changed.emit()

    def on_delete_clicked(self):
        """삭제 버튼 클릭"""
        self.delete_requested.emit(self)

    def update_title_style(self):
        """체크 상태에 따라 제목 스타일 변경"""
        if self.is_checked:
            self.title_edit.setStyleSheet("""
                QLineEdit {
                    background-color: transparent;
                    border: none;
                    color: #9b9a97;
                    font-size: 14px;
                    padding: 4px;
                    text-decoration: line-through;
                }
            """)
        else:
            self.title_edit.setStyleSheet("""
                QLineEdit {
                    background-color: transparent;
                    border: none;
                    color: #37352f;
                    font-size: 14px;
                    padding: 4px;
                }
                QLineEdit:focus {
                    background-color: rgba(55, 53, 47, 0.03);
                }
            """)

    def set_item_number(self, number):
        """항목 번호 설정"""
        self.item_number = number
        self.number_label.setText(f"{number}.")
        self.title_edit.setPlaceholderText(f"체크리스트 항목 {number}")

    def get_data(self):
        """데이터 반환"""
        return {
            "type": "inline_checkbox",
            "text": self.text_value,
            "detail": self.detail_value,
            "is_checked": self.is_checked,
            "weight": self.weight,
            "item_number": self.item_number
        }


class DatePickerDialog(QDialog):
    """날짜 선택 다이얼로그"""
    date_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("날짜 선택")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 캘린더
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.on_date_selected)
        layout.addWidget(self.calendar)

        # 버튼
        btn_layout = QHBoxLayout()

        today_btn = QPushButton("오늘")
        today_btn.clicked.connect(self.select_today)
        btn_layout.addWidget(today_btn)

        tomorrow_btn = QPushButton("내일")
        tomorrow_btn.clicked.connect(self.select_tomorrow)
        btn_layout.addWidget(tomorrow_btn)

        clear_btn = QPushButton("지우기")
        clear_btn.clicked.connect(self.clear_date)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #d3d3d3;
                border-radius: 5px;
            }
            QCalendarWidget {
                background-color: #ffffff;
            }
            QCalendarWidget QTableView {
                selection-background-color: #2383e2;
                selection-color: white;
            }
            QPushButton {
                background-color: #f7f6f3;
                border: 1px solid #d3d3d3;
                border-radius: 3px;
                padding: 5px 10px;
                color: #37352f;
            }
            QPushButton:hover {
                background-color: #e3e2e0;
            }
        """)

    def on_date_selected(self, date):
        """날짜 선택"""
        date_str = date.toString("yyyy-MM-dd")
        self.date_selected.emit(date_str)
        self.accept()

    def select_today(self):
        """오늘 선택"""
        today = QDate.currentDate()
        self.on_date_selected(today)

    def select_tomorrow(self):
        """내일 선택"""
        tomorrow = QDate.currentDate().addDays(1)
        self.on_date_selected(tomorrow)

    def clear_date(self):
        """날짜 지우기"""
        self.date_selected.emit("")
        self.accept()


class InlineDateWidget(QFrame):
    """상세 내용 안에 삽입되는 인라인 날짜 위젯 - 시작일과 목표일"""
    content_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)  # 삭제 요청 시그널

    def __init__(self, start_date: str = "", target_date: str = "", parent=None):
        super().__init__(parent)
        self.start_date = start_date
        self.target_date = target_date
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """UI 설정 - 시작일과 목표일 2개"""
        self.setFrameShape(QFrame.NoFrame)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # 제목
        title_layout = QHBoxLayout()
        title_label = QLabel("📅 프로젝트 기간")
        title_label.setStyleSheet("""
            QLabel {
                color: #37352f;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 삭제 버튼
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(22, 22)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #9b9a97;
                font-weight: bold;
                font-size: 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #eb5757;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #d44c4c;
            }
        """)
        self.delete_btn.setToolTip("날짜 위젯 삭제")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        title_layout.addWidget(self.delete_btn)

        main_layout.addLayout(title_layout)

        # 시작일 섹션
        start_layout = QHBoxLayout()
        start_layout.setSpacing(8)

        start_icon = QLabel("🚀")
        start_icon.setStyleSheet("font-size: 14px;")
        start_layout.addWidget(start_icon)

        start_label = QLabel("시작일:")
        start_label.setStyleSheet("""
            QLabel {
                color: #787774;
                font-size: 13px;
                min-width: 60px;
            }
        """)
        start_layout.addWidget(start_label)

        self.start_date_btn = QPushButton()
        self.update_start_date_display()
        self.start_date_btn.clicked.connect(self.show_start_date_picker)
        self.start_date_btn.setMinimumWidth(120)
        start_layout.addWidget(self.start_date_btn)

        start_layout.addStretch()
        main_layout.addLayout(start_layout)

        # 목표일 섹션
        target_layout = QHBoxLayout()
        target_layout.setSpacing(8)

        target_icon = QLabel("🎯")
        target_icon.setStyleSheet("font-size: 14px;")
        target_layout.addWidget(target_icon)

        target_label = QLabel("목표일:")
        target_label.setStyleSheet("""
            QLabel {
                color: #787774;
                font-size: 13px;
                min-width: 60px;
            }
        """)
        target_layout.addWidget(target_label)

        self.target_date_btn = QPushButton()
        self.update_target_date_display()
        self.target_date_btn.clicked.connect(self.show_target_date_picker)
        self.target_date_btn.setMinimumWidth(120)
        target_layout.addWidget(self.target_date_btn)

        target_layout.addStretch()
        main_layout.addLayout(target_layout)

        # 기간 표시
        self.duration_label = QLabel()
        self.duration_label.setStyleSheet("""
            QLabel {
                color: #9b9a97;
                font-size: 12px;
                font-style: italic;
                padding-left: 28px;
            }
        """)
        main_layout.addWidget(self.duration_label)
        self.update_duration()

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            InlineDateWidget {
                background-color: #f7f6f3;
                border: 1px solid #e9e9e7;
                border-radius: 5px;
                margin: 4px 0px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #d3d1cb;
                border-radius: 3px;
                padding: 5px 10px;
                color: #37352f;
                font-size: 13px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f7f6f3;
                border-color: #9b9a97;
            }
        """)

    def update_start_date_display(self):
        """시작일 표시 업데이트"""
        if self.start_date:
            self.start_date_btn.setText(self.start_date)
        else:
            self.start_date_btn.setText("날짜 선택...")

    def update_target_date_display(self):
        """목표일 표시 업데이트"""
        if self.target_date:
            self.target_date_btn.setText(self.target_date)
        else:
            self.target_date_btn.setText("날짜 선택...")

    def update_duration(self):
        """기간 계산 및 표시"""
        if self.start_date and self.target_date:
            try:
                from datetime import datetime
                start = datetime.strptime(self.start_date, "%Y-%m-%d")
                target = datetime.strptime(self.target_date, "%Y-%m-%d")
                duration = (target - start).days

                if duration > 0:
                    self.duration_label.setText(f"총 기간: {duration}일")
                elif duration == 0:
                    self.duration_label.setText("당일 프로젝트")
                else:
                    self.duration_label.setText("⚠️ 목표일이 시작일보다 이전입니다")
            except:
                self.duration_label.setText("")
        else:
            self.duration_label.setText("")

    def show_start_date_picker(self):
        """시작일 선택기 표시"""
        picker = DatePickerDialog(self)
        picker.date_selected.connect(self.on_start_date_selected)

        # 버튼 아래에 표시
        btn_pos = self.start_date_btn.mapToGlobal(self.start_date_btn.rect().bottomLeft())
        picker.move(btn_pos)
        picker.exec_()

    def show_target_date_picker(self):
        """목표일 선택기 표시"""
        picker = DatePickerDialog(self)
        picker.date_selected.connect(self.on_target_date_selected)

        # 버튼 아래에 표시
        btn_pos = self.target_date_btn.mapToGlobal(self.target_date_btn.rect().bottomLeft())
        picker.move(btn_pos)
        picker.exec_()

    def on_start_date_selected(self, date_str):
        """시작일 선택됨"""
        self.start_date = date_str
        self.update_start_date_display()
        self.update_duration()
        self.content_changed.emit()

    def on_target_date_selected(self, date_str):
        """목표일 선택됨"""
        self.target_date = date_str
        self.update_target_date_display()
        self.update_duration()
        self.content_changed.emit()

    def on_delete_clicked(self):
        """삭제 버튼 클릭"""
        self.delete_requested.emit(self)

    def get_data(self):
        """데이터 반환"""
        return {
            "type": "inline_date",
            "start_date": self.start_date,
            "target_date": self.target_date
        }
