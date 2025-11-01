"""
심플한 체크리스트 스타일 토글 위젯
노션 스타일 블록 시스템 없이 전통적인 체크리스트만 제공
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QFrame, QCheckBox, QSpinBox,
                             QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.toggle_item import ToggleItem, ChecklistItem


class SimpleChecklistItemWidget(QWidget):
    """심플한 체크리스트 항목 위젯"""

    checked_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, checklist_item: ChecklistItem, parent=None):
        super().__init__(parent)
        self.checklist_item = checklist_item
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.checklist_item.is_checked)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d9d9d9;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #0066cc;
                border-color: #0066cc;
                image: url(none);
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
                color: white;
            }
        """)
        layout.addWidget(self.checkbox)

        # 텍스트 입력
        self.text_edit = QLineEdit(self.checklist_item.text)
        self.text_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #37352f;
                font-size: 14px;
            }
            QLineEdit:focus {
                background-color: #f7f6f3;
            }
        """)
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit, 1)

        # 점수 (가중치)
        score_label = QLabel("점수:")
        score_label.setStyleSheet("color: #787774; font-size: 12px;")
        layout.addWidget(score_label)

        self.score_spin = QSpinBox()
        self.score_spin.setRange(1, 100)
        self.score_spin.setValue(self.checklist_item.score)
        self.score_spin.setMaximumWidth(60)
        self.score_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                padding: 2px 4px;
                background: white;
            }
        """)
        self.score_spin.valueChanged.connect(self.on_score_changed)
        layout.addWidget(self.score_spin)

        # 삭제 버튼
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9b9a97;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffe0e0;
                color: #eb5757;
                border-radius: 3px;
            }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(self.delete_btn)

    def on_checkbox_changed(self, state):
        self.checklist_item.is_checked = (state == Qt.Checked)

        # 체크되면 텍스트에 취소선
        if self.checklist_item.is_checked:
            self.text_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    background: transparent;
                    color: #9b9a97;
                    font-size: 14px;
                    text-decoration: line-through;
                }
            """)
        else:
            self.text_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    background: transparent;
                    color: #37352f;
                    font-size: 14px;
                }
            """)

        self.checked_changed.emit()

    def on_text_changed(self, text):
        self.checklist_item.text = text
        self.checked_changed.emit()

    def on_score_changed(self, value):
        self.checklist_item.score = value
        self.checked_changed.emit()


class SimpleToggleWidget(QFrame):
    """심플한 체크리스트 토글 위젯"""

    item_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    add_child_requested = pyqtSignal(object)
    save_requested = pyqtSignal(object)
    selection_changed = pyqtSignal(object)
    move_requested = pyqtSignal(object, int)  # 드래그 앤 드롭용

    def __init__(self, item: ToggleItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.child_widgets = []
        self.checklist_widgets = []
        self.is_selected = False

        self.setup_ui()
        self.setup_style()
        self.update_display()

    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)

        # 헤더
        self.header_widget = self.create_header()
        self.main_layout.addWidget(self.header_widget)

        # 체크리스트 컨테이너
        self.checklist_container = QWidget()
        self.checklist_layout = QVBoxLayout(self.checklist_container)
        self.checklist_layout.setContentsMargins(30, 4, 0, 4)
        self.checklist_layout.setSpacing(2)
        self.main_layout.addWidget(self.checklist_container)

        # 체크리스트 추가 버튼
        self.add_checklist_btn = QPushButton("+ 체크리스트 추가")
        self.add_checklist_btn.setMaximumWidth(150)
        self.add_checklist_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #787774;
                text-align: left;
                padding: 4px 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.08);
                color: #37352f;
            }
        """)
        self.add_checklist_btn.clicked.connect(self.add_checklist_item)
        self.checklist_layout.addWidget(self.add_checklist_btn)

        # 하위 토글 컨테이너
        self.children_widget = QWidget()
        self.children_layout = QVBoxLayout(self.children_widget)
        self.children_layout.setContentsMargins(20, 0, 0, 0)
        self.children_layout.setSpacing(4)
        self.main_layout.addWidget(self.children_widget)

        self.update_children_visibility()
        self.update_checklist_visibility()

    def create_header(self):
        """헤더 생성"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 토글 버튼
        self.toggle_btn = QPushButton("▼" if self.item.is_expanded else "▶")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9b9a97;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.08);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.toggle_btn)

        # 제목
        self.title_edit = QLineEdit(self.item.title)
        self.title_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: #37352f;
                font-size: 15px;
                font-weight: 600;
            }
            QLineEdit:focus {
                background-color: #f7f6f3;
            }
        """)
        self.title_edit.textChanged.connect(self.on_title_changed)
        layout.addWidget(self.title_edit, 1)

        # 진행률
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setMinimumWidth(100)
        layout.addWidget(self.progress_label)

        # 메뉴 버튼
        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(24, 24)
        menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9b9a97;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.08);
            }
        """)
        menu_btn.clicked.connect(self.show_menu)
        layout.addWidget(menu_btn)

        return header

    def setup_style(self):
        """스타일 설정"""
        self.setStyleSheet("""
            SimpleToggleWidget {
                background-color: white;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
            }
            SimpleToggleWidget:hover {
                border-color: #d3d3d3;
            }
        """)

    def toggle_expanded(self):
        """토글 확장/축소"""
        self.item.is_expanded = not self.item.is_expanded
        self.toggle_btn.setText("▼" if self.item.is_expanded else "▶")
        self.update_children_visibility()
        self.update_checklist_visibility()
        self.item_changed.emit()

    def update_children_visibility(self):
        """하위 토글 표시/숨김"""
        self.children_widget.setVisible(self.item.is_expanded and len(self.child_widgets) > 0)

    def update_checklist_visibility(self):
        """체크리스트 표시/숨김"""
        self.checklist_container.setVisible(self.item.is_expanded)

    def add_checklist_item(self):
        """체크리스트 항목 추가"""
        new_item = ChecklistItem(text="새 체크리스트", is_checked=False, score=1)
        self.item.checklist.append(new_item)

        widget = SimpleChecklistItemWidget(new_item)
        widget.checked_changed.connect(self.on_checklist_changed)
        widget.delete_requested.connect(self.delete_checklist_item)

        # 추가 버튼 바로 위에 삽입
        insert_index = self.checklist_layout.count() - 1
        self.checklist_layout.insertWidget(insert_index, widget)
        self.checklist_widgets.append(widget)

        self.on_checklist_changed()

    def delete_checklist_item(self, widget):
        """체크리스트 항목 삭제"""
        if widget in self.checklist_widgets:
            self.checklist_widgets.remove(widget)
            self.item.checklist.remove(widget.checklist_item)
            self.checklist_layout.removeWidget(widget)
            widget.deleteLater()
            self.on_checklist_changed()

    def on_checklist_changed(self):
        """체크리스트 변경 시"""
        self.update_progress_display()
        self.item_changed.emit()

    def on_title_changed(self, text):
        """제목 변경 시"""
        self.item.title = text
        self.item_changed.emit()

    def update_progress_display(self):
        """진행률 표시 업데이트"""
        total = self.item.get_total_score()
        max_score = self.item.get_total_max_score()
        percentage = self.item.get_completion_percentage()

        # 색상 결정
        if percentage >= 80:
            color = "#0f7b6c"  # 초록
        elif percentage >= 50:
            color = "#d9730d"  # 주황
        else:
            color = "#eb5757"  # 빨강

        self.progress_label.setText(f"{total}/{max_score} ({percentage:.0f}%)")
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-weight: 600;
                font-size: 13px;
            }}
        """)

    def update_display(self):
        """화면 업데이트"""
        self.title_edit.setText(self.item.title)
        self.toggle_btn.setText("▼" if self.item.is_expanded else "▶")

        # 기존 체크리스트 위젯 제거
        for widget in self.checklist_widgets:
            self.checklist_layout.removeWidget(widget)
            widget.deleteLater()
        self.checklist_widgets.clear()

        # 체크리스트 다시 로드
        for checklist_item in self.item.checklist:
            widget = SimpleChecklistItemWidget(checklist_item)
            widget.checked_changed.connect(self.on_checklist_changed)
            widget.delete_requested.connect(self.delete_checklist_item)

            # 추가 버튼 바로 위에 삽입
            insert_index = self.checklist_layout.count() - 1
            self.checklist_layout.insertWidget(insert_index, widget)
            self.checklist_widgets.append(widget)

        self.update_progress_display()
        self.update_children_visibility()
        self.update_checklist_visibility()

    def show_menu(self):
        """컨텍스트 메뉴 표시"""
        menu = QMenu(self)

        add_child_action = QAction("하위 토글 추가", self)
        add_child_action.triggered.connect(lambda: self.add_child_requested.emit(self))
        menu.addAction(add_child_action)

        menu.addSeparator()

        save_action = QAction("저장", self)
        save_action.triggered.connect(lambda: self.save_requested.emit(self))
        menu.addAction(save_action)

        menu.addSeparator()

        delete_action = QAction("삭제", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self))
        menu.addAction(delete_action)

        menu.exec_(self.mapToGlobal(self.sender().pos()))

    def add_child_widget(self, child_widget):
        """하위 위젯 추가"""
        self.child_widgets.append(child_widget)
        self.children_layout.addWidget(child_widget)
        self.update_children_visibility()

    def remove_child_widget(self, child_widget):
        """하위 위젯 제거"""
        if child_widget in self.child_widgets:
            self.child_widgets.remove(child_widget)
            self.children_layout.removeWidget(child_widget)
            self.update_children_visibility()

    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                SimpleToggleWidget {
                    background-color: #f7f6f3;
                    border: 2px solid #0066cc;
                    border-radius: 3px;
                }
            """)
        else:
            self.setup_style()
