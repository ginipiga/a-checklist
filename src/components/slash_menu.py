"""
노션 스타일 슬래시(/) 명령어 메뉴
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QLabel, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime, timedelta


class SlashMenuItem:
    """슬래시 메뉴 항목"""
    def __init__(self, name: str, description: str, icon: str, command_type: str):
        self.name = name
        self.description = description
        self.icon = icon
        self.command_type = command_type


class SlashCommandMenu(QFrame):
    """노션 스타일 슬래시 명령어 메뉴"""
    command_selected = pyqtSignal(str, object)  # (command_type, data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self.setup_commands()
        self.filtered_commands = self.all_commands.copy()

    def setup_ui(self):
        """UI 설정"""
        # Qt.Popup 사용 - 클릭 시 닫히지 않도록 수정
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)

        # 제목
        title_label = QLabel("블록 타입 선택")
        title_label.setStyleSheet("QLabel { color: #888; font-size: 11px; padding: 5px; }")
        layout.addWidget(title_label)

        # 명령어 리스트
        self.command_list = QListWidget()
        self.command_list.setFixedHeight(250)
        self.command_list.setFixedWidth(300)
        # itemClicked 대신 itemPressed 사용하여 즉시 반응
        self.command_list.itemPressed.connect(self.on_item_clicked)
        layout.addWidget(self.command_list)

        self.setMaximumWidth(310)

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            SlashCommandMenu {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QListWidget {
                background-color: #2b2b2b;
                border: none;
                outline: none;
                color: #ffffff;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
            QListWidget::item:selected {
                background-color: #0d7377;
            }
        """)

    def setup_commands(self):
        """명령어 정의"""
        self.all_commands = [
            SlashMenuItem("텍스트", "일반 텍스트 블록", "📝", "add_text"),
            SlashMenuItem("체크리스트", "체크리스트 항목 (제목+점수+상세)", "☑", "add_checklist"),
            SlashMenuItem("하위 토글", "하위 토글 추가", "📂", "add_child_toggle"),
            SlashMenuItem("프로젝트 기간", "시작일과 목표일 설정", "📅", "add_date"),
            SlashMenuItem("구분선", "구분선 추가", "➖", "add_divider"),
        ]

    def show_menu(self, pos, filter_text=""):
        """
        메뉴 표시

        Args:
            pos: 표시할 위치
            filter_text: 필터 텍스트
        """
        self.filter_commands(filter_text)
        self.move(pos)
        self.show()
        self.setFocus()

        # 첫 번째 항목 선택
        if self.command_list.count() > 0:
            self.command_list.setCurrentRow(0)

    def filter_commands(self, filter_text: str):
        """
        명령어 필터링

        Args:
            filter_text: 필터 텍스트
        """
        filter_text = filter_text.lower()

        self.command_list.clear()
        self.filtered_commands = []

        for cmd in self.all_commands:
            if not filter_text or filter_text in cmd.name.lower():
                self.filtered_commands.append(cmd)

                item = QListWidgetItem(f"{cmd.icon}  {cmd.name}")
                item.setData(Qt.UserRole, cmd)

                # 설명 추가
                font = QFont()
                font.setPointSize(10)
                item.setFont(font)

                self.command_list.addItem(item)

    def on_item_clicked(self, item):
        """항목 클릭 이벤트"""
        cmd = item.data(Qt.UserRole)
        self.execute_command(cmd)

    def execute_command(self, cmd: SlashMenuItem):
        """
        명령어 실행

        Args:
            cmd: 실행할 명령어
        """
        data = None

        # 날짜 관련 명령어는 data 없이 전송 (위젯에서 직접 설정)
        self.command_selected.emit(cmd.command_type, data)
        self.hide()

    def keyPressEvent(self, event):
        """키보드 이벤트 처리"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # 선택된 항목 실행
            current_item = self.command_list.currentItem()
            if current_item:
                cmd = current_item.data(Qt.UserRole)
                self.execute_command(cmd)
        elif event.key() == Qt.Key_Up:
            # 위로 이동
            current_row = self.command_list.currentRow()
            if current_row > 0:
                self.command_list.setCurrentRow(current_row - 1)
        elif event.key() == Qt.Key_Down:
            # 아래로 이동
            current_row = self.command_list.currentRow()
            if current_row < self.command_list.count() - 1:
                self.command_list.setCurrentRow(current_row + 1)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        """포커스 잃을 때 숨기기"""
        # Popup 윈도우는 외부 클릭 시 자동으로 닫히므로
        # 여기서는 아무것도 하지 않음
        super().focusOutEvent(event)
