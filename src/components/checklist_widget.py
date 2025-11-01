from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QSpinBox, QLabel, QCheckBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.toggle_item import ChecklistItem


class ChecklistItemWidget(QFrame):
    item_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, checklist_item: ChecklistItem, parent=None):
        super().__init__(parent)
        self.checklist_item = checklist_item
        self.is_expanded = False  # 토글 상태
        self.setup_ui()
        self.setup_style()
        self.connect_signals()
        self.update_display()

    def setup_ui(self):
        self.setFrameStyle(QFrame.NoFrame)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 2, 5, 2)
        self.main_layout.setSpacing(2)

        # 헤더 레이아웃 (토글 버튼 + 체크박스 + 요약)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        # 토글 버튼
        self.toggle_btn = QPushButton("▶")
        self.toggle_btn.setFixedSize(16, 16)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                color: #4CAF50;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        header_layout.addWidget(self.toggle_btn)

        # 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.checklist_item.is_checked)
        header_layout.addWidget(self.checkbox)

        # 요약 텍스트 (읽기 전용으로 표시)
        self.summary_label = QLabel(self.checklist_item.summary or self.checklist_item.text)
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("QLabel { color: #ffffff; }")
        header_layout.addWidget(self.summary_label, 1)

        # 우선순위 표시
        self.priority_label = QLabel()
        self.priority_label.setFixedWidth(65)
        header_layout.addWidget(self.priority_label)

        header_layout.addWidget(QLabel("점수:"))
        self.score_spin = QSpinBox()
        self.score_spin.setRange(1, 100)
        self.score_spin.setValue(self.checklist_item.score)
        self.score_spin.setMaximumWidth(60)
        header_layout.addWidget(self.score_spin)

        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setStyleSheet("QPushButton { color: #ff6666; font-weight: bold; font-size: 12px; }")
        header_layout.addWidget(self.delete_btn)

        self.main_layout.addLayout(header_layout)

        # 상세 내용 위젯 (토글로 표시/숨김)
        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(35, 5, 5, 5)
        detail_layout.setSpacing(5)

        # 요약 편집 필드
        detail_layout.addWidget(QLabel("요약:"))
        self.summary_edit = QLineEdit(self.checklist_item.summary or self.checklist_item.text)
        self.summary_edit.setPlaceholderText("짧은 요약...")
        detail_layout.addWidget(self.summary_edit)

        # 상세 내용 편집 필드
        detail_layout.addWidget(QLabel("상세 내용:"))
        from PyQt5.QtWidgets import QTextEdit
        self.detail_edit = QTextEdit(self.checklist_item.detail)
        self.detail_edit.setPlaceholderText("상세 설명, 배경, 참고사항 등...")
        self.detail_edit.setMaximumHeight(80)
        detail_layout.addWidget(self.detail_edit)

        self.detail_widget.hide()  # 처음에는 숨김
        self.main_layout.addWidget(self.detail_widget)
    
    def setup_style(self):
        self.setStyleSheet("""
            ChecklistItemWidget {
                background-color: #353535;
                border-radius: 3px;
                margin: 1px;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: white;
                font-weight: bold;
            }
            QLineEdit, QSpinBox {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                color: #ffffff;
                padding: 2px;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #606060;
                border-radius: 3px;
                color: #ff6666;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
    
    def connect_signals(self):
        self.checkbox.toggled.connect(self.on_checkbox_toggled)
        self.summary_edit.textChanged.connect(self.on_summary_changed)
        self.detail_edit.textChanged.connect(self.on_detail_changed)
        self.score_spin.valueChanged.connect(self.on_score_changed)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))

    def toggle_expanded(self):
        """토글 상태 변경"""
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.toggle_btn.setText("▼")
            self.detail_widget.show()
        else:
            self.toggle_btn.setText("▶")
            self.detail_widget.hide()

    def on_checkbox_toggled(self):
        self.checklist_item.is_checked = self.checkbox.isChecked()
        self.item_changed.emit()

    def on_summary_changed(self):
        """요약 텍스트 변경"""
        summary = self.summary_edit.text()
        self.checklist_item.summary = summary
        self.checklist_item.text = summary  # text도 업데이트 (호환성)
        self.summary_label.setText(summary)  # 레이블도 업데이트
        self.item_changed.emit()

    def on_detail_changed(self):
        """상세 내용 변경"""
        self.checklist_item.detail = self.detail_edit.toPlainText()
        self.item_changed.emit()

    def on_score_changed(self):
        self.checklist_item.score = self.score_spin.value()
        self.item_changed.emit()
    
    def update_display(self):
        """위젯 표시 업데이트"""
        self.checkbox.setChecked(self.checklist_item.is_checked)
        summary = self.checklist_item.summary or self.checklist_item.text
        self.summary_label.setText(summary)
        self.summary_edit.setText(summary)
        self.detail_edit.setPlainText(self.checklist_item.detail)
        self.score_spin.setValue(self.checklist_item.score)
        self.update_priority_display()

    def update_priority_display(self):
        """가중치 평가 정보를 기반으로 우선순위 표시 업데이트"""
        priority = self.checklist_item.get_priority()
        final_score = self.checklist_item.get_final_score()

        # 우선순위별 색상
        priority_colors = {
            'Critical': '#ff6b6b',
            'High': '#ffa500',
            'Medium': '#4ecdc4',
            'Low': '#95e1d3',
            'Minimal': '#aaa'
        }

        color = priority_colors.get(priority, '#aaa')
        self.priority_label.setText(f"[{priority}]")
        self.priority_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; font-size: 10px; }}")

        # 툴팁에 상세 정보 표시
        if self.checklist_item.weight_evaluation:
            tooltip = f"우선순위: {priority}\n최종점수: {final_score}/5"
            if 'evaluation' in self.checklist_item.weight_evaluation:
                eval_data = self.checklist_item.weight_evaluation['evaluation']
                tooltip += f"\n기본점수: {eval_data.get('base_score', 'N/A')}"
                tooltip += f"\nC1(승인/법규): {eval_data.get('C1_approval', {}).get('score', 'N/A')}"
                tooltip += f"\nC2(비용/일정): {eval_data.get('C2_cost_schedule', {}).get('score', 'N/A')}"
                tooltip += f"\nC3(환경/안전): {eval_data.get('C3_environment_safety', {}).get('score', 'N/A')}"
                tooltip += f"\nC4(운영성): {eval_data.get('C4_operation', {}).get('score', 'N/A')}"
                tooltip += f"\nC5(가역성): {eval_data.get('C5_reversibility', {}).get('score', 'N/A')}"
            self.priority_label.setToolTip(tooltip)
        else:
            self.priority_label.setText("")
            self.priority_label.setToolTip("가중치 평가 없음")


class ChecklistWidget(QFrame):
    item_changed = pyqtSignal()
    
    def __init__(self, toggle_item, parent=None):
        super().__init__(parent)
        self.toggle_item = toggle_item
        self.checklist_widgets = []
        self.setup_ui()
        self.setup_style()
        self.load_checklist_items()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("체크리스트:"))
        
        self.add_btn = QPushButton("+ 항목 추가")
        self.add_btn.clicked.connect(self.add_checklist_item)
        header_layout.addWidget(self.add_btn)
        header_layout.addStretch()
        
        self.main_layout.addLayout(header_layout)
        
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout(self.items_widget)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)
        self.main_layout.addWidget(self.items_widget)
    
    def setup_style(self):
        self.setStyleSheet("""
            ChecklistWidget {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                border-radius: 5px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                border: 1px solid #45a049;
                border-radius: 3px;
                color: #ffffff;
                padding: 3px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
    
    def load_checklist_items(self):
        for checklist_item in self.toggle_item.checklist:
            self.create_checklist_widget(checklist_item)
    
    def add_checklist_item(self):
        new_item = ChecklistItem("새 항목", False, 1)
        self.toggle_item.checklist.append(new_item)
        self.create_checklist_widget(new_item)
        self.item_changed.emit()
    
    def create_checklist_widget(self, checklist_item):
        widget = ChecklistItemWidget(checklist_item)
        widget.item_changed.connect(self.on_item_changed)
        widget.delete_requested.connect(self.delete_checklist_item)
        
        self.checklist_widgets.append(widget)
        self.items_layout.addWidget(widget)
        
        return widget
    
    def delete_checklist_item(self, widget):
        if widget in self.checklist_widgets:
            self.checklist_widgets.remove(widget)
            self.toggle_item.checklist.remove(widget.checklist_item)
            self.items_layout.removeWidget(widget)
            widget.setParent(None)
            self.item_changed.emit()
    
    def on_item_changed(self):
        self.item_changed.emit()
    
    def update_display(self):
        for widget in self.checklist_widgets:
            widget.update_display()