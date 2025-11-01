from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QTextEdit, QSpinBox, QLabel, QFrame,
                             QSizePolicy, QMenu, QAction, QCheckBox, QScrollArea,
                             QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QEvent, QTimer
from PyQt5.QtGui import QFont, QPalette, QDrag, QPainter, QPixmap
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.toggle_item import ToggleItem


class ToggleWidget(QFrame):
    item_changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    add_child_requested = pyqtSignal(object)
    save_requested = pyqtSignal(object)
    selection_changed = pyqtSignal(object)
    move_requested = pyqtSignal(object, int)  # widget, new_position
    
    def __init__(self, item: ToggleItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.child_widgets = []
        self.is_selected = False
        self.drag_start_position = None
        self.parent_toggle_widget = None  # 부모 ToggleWidget 참조
        self.setup_ui()
        self.setup_style()
        self.connect_signals()
        self.update_display()

        # 드래그 앤 드롭 설정
        self.setAcceptDrops(True)

        # 자식 위젯들에 이벤트 필터 설치
        self.install_event_filters()

        # 기존 데이터를 블록으로 로드
        self.load_blocks_from_item()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)
        
        self.header_widget = self.create_header()
        self.main_layout.addWidget(self.header_widget)
        
        self.content_widget = self.create_content()
        self.main_layout.addWidget(self.content_widget)
        
        self.children_widget = QWidget()
        self.children_layout = QVBoxLayout(self.children_widget)
        self.children_layout.setContentsMargins(20, 0, 0, 0)
        self.children_layout.setSpacing(2)
        self.main_layout.addWidget(self.children_widget)
        
        self.update_children_visibility()
        self.update_content_visibility()
        self.update_score_inputs_visibility()
    
    def create_header(self):
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.toggle_btn = QPushButton("▼" if self.item.is_expanded else "▶")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.toggle_btn)
        
        self.title_edit = QLineEdit(self.item.title)
        self.title_edit.setStyleSheet("QLineEdit { border: none; background: transparent; color: #37352f; }")
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.title_edit.setFont(font)
        layout.addWidget(self.title_edit)

        self.source_file_label = QLabel()
        self.source_file_label.setStyleSheet("QLabel { color: #9b9a97; font-style: italic; font-size: 10px; }")
        self.source_file_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.source_file_label)
        
        layout.addStretch()
        
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setMinimumWidth(80)
        layout.addWidget(self.progress_label)
        
        self.save_btn = QPushButton("💾")
        self.save_btn.setFixedSize(20, 20)
        self.save_btn.setStyleSheet("QPushButton { color: #66ff66; font-weight: bold; }")
        self.save_btn.setToolTip("이 토글 업데이트/저장")
        self.save_btn.clicked.connect(self.request_save)
        layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setStyleSheet("QPushButton { color: #ff6666; font-weight: bold; }")
        self.delete_btn.clicked.connect(self.request_delete)
        layout.addWidget(self.delete_btn)
        
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(20, 20)
        self.menu_btn.clicked.connect(self.show_context_menu)
        layout.addWidget(self.menu_btn)
        
        return header
    
    def create_content(self):
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(20, 5, 5, 5)
        self.content_layout.setSpacing(2)

        # 노션 스타일 - 블록 컨테이너
        self.blocks_container = QWidget()
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        self.blocks_layout.setSpacing(2)
        self.content_layout.addWidget(self.blocks_container)

        # 슬래시 명령어 메뉴
        from components.slash_menu import SlashCommandMenu
        self.slash_menu = SlashCommandMenu(self)
        self.slash_menu.command_selected.connect(self.on_slash_command)
        self.slash_menu.hide()

        # 현재 슬래시 메뉴를 호출한 블록 추적
        self.current_slash_block = None

        # "+ 블록 추가" 버튼
        self.add_block_btn = QPushButton("+ 블록 추가")
        self.add_block_btn.setMaximumWidth(150)
        self.add_block_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 3px;
                color: #787774;
                font-size: 13px;
                padding: 4px 8px;
                text-align: left;
                margin-top: 2px;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.08);
                color: #37352f;
            }
        """)
        self.add_block_btn.clicked.connect(self.on_add_block_clicked)
        self.content_layout.addWidget(self.add_block_btn, 0, Qt.AlignLeft)

        return content
    # ====================================================================
    # 아래 메서드들은 블록 기반 시스템으로 대체되어 더 이상 사용되지 않습니다
    # ====================================================================

    def create_checklist_header(self):
        """체크리스트 헤더 (접기/펼치기 버튼 포함) - DEPRECATED"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 5, 0, 2)
        layout.setSpacing(5)
        
        # 접기/펼치기 버튼 - Notion 스타일
        self.checklist_toggle_btn = QPushButton("▼")
        self.checklist_toggle_btn.setFixedSize(20, 20)
        self.checklist_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #9b9a97;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #37352f;
                background-color: rgba(55, 53, 47, 0.08);
                border-radius: 3px;
            }
        """)
        self.checklist_toggle_btn.clicked.connect(self.toggle_checklist)
        layout.addWidget(self.checklist_toggle_btn)
        
        # 체크리스트 라벨 - Notion 스타일
        checklist_label = QLabel("체크리스트")
        checklist_label.setStyleSheet("""
            QLabel {
                color: #787774;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        layout.addWidget(checklist_label)

        # 항목 개수 표시 - Notion 스타일
        self.checklist_count_label = QLabel()
        self.checklist_count_label.setStyleSheet("""
            QLabel {
                color: #9b9a97;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.checklist_count_label)
        
        layout.addStretch()
        
        # 체크리스트 접힘 상태 초기화
        self.checklist_expanded = True
        self.update_checklist_count()
        
        return header
    
    def toggle_checklist(self):
        """체크리스트 접기/펼치기"""
        self.checklist_expanded = not self.checklist_expanded
        self.checklist_widget.setVisible(self.checklist_expanded)
        self.checklist_toggle_btn.setText("▼" if self.checklist_expanded else "▶")
    
    def update_checklist_count(self):
        """체크리스트 개수 및 완료 상태 업데이트"""
        total_items = len(self.item.checklist)
        checked_items = sum(1 for item in self.item.checklist if item.is_checked)
        
        if total_items > 0:
            self.checklist_count_label.setText(f"({checked_items}/{total_items})")
        else:
            self.checklist_count_label.setText("(0/0)")
    
    def create_checklist_widget(self):
        """체크리스트 위젯 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(3)
        
        # 체크리스트 컨테이너 (스크롤 없이 직접 배치)
        self.checklist_container = QWidget()
        self.checklist_layout = QVBoxLayout(self.checklist_container)
        self.checklist_layout.setContentsMargins(0, 0, 0, 5)
        self.checklist_layout.setSpacing(2)
        
        layout.addWidget(self.checklist_container)
        
        # 체크리스트 추가 버튼 - Notion 스타일
        self.add_checklist_btn = QPushButton("+ 항목 추가")
        self.add_checklist_btn.setMaximumWidth(120)
        self.add_checklist_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 3px;
                color: #787774;
                font-size: 13px;
                padding: 4px 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.08);
                color: #37352f;
            }
        """)
        self.add_checklist_btn.clicked.connect(self.add_checklist_item)
        layout.addWidget(self.add_checklist_btn, 0, Qt.AlignLeft)
        
        # 기존 체크리스트 항목들 로드
        self.refresh_checklist()
        
        return widget
    
    def add_checklist_item(self):
        """새 체크리스트 항목 추가"""
        from models.toggle_item import ChecklistItem

        new_item = ChecklistItem(text="", is_checked=False, score=1)
        self.item.checklist.append(new_item)
        self.refresh_checklist()
        self.update_checklist_count()
        self.update_max_score_display()  # 최대 점수 자동 업데이트
        self.item_changed.emit()
    
    def remove_checklist_item(self, item_index):
        """체크리스트 항목 제거"""
        if 0 <= item_index < len(self.item.checklist):
            del self.item.checklist[item_index]
            self.refresh_checklist()
            self.update_checklist_count()
            self.update_max_score_display()  # 최대 점수 자동 업데이트
            self.item_changed.emit()
    
    def refresh_checklist(self):
        """체크리스트 UI 새로고침"""
        # 기존 위젯들 제거
        for i in reversed(range(self.checklist_layout.count())):
            child = self.checklist_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 체크리스트 항목들 다시 생성
        for i, checklist_item in enumerate(self.item.checklist):
            item_widget = self.create_checklist_item_widget(checklist_item, i)
            self.checklist_layout.addWidget(item_widget)
    
    def create_checklist_item_widget(self, checklist_item, item_index):
        """개별 체크리스트 항목 위젯 생성 - Notion 스타일"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 3px;
                margin: 2px 0px;
                padding: 2px;
            }
            QWidget:hover {
                background-color: #f7f6f3;
            }
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # 항목 번호 - Notion 스타일
        number_label = QLabel(f"{item_index + 1}.")
        number_label.setStyleSheet("""
            QLabel {
                color: #9b9a97;
                font-size: 12px;
                font-weight: 400;
                min-width: 24px;
            }
        """)
        number_label.setAlignment(Qt.AlignRight)
        layout.addWidget(number_label)

        # 체크박스 - Notion 스타일
        checkbox = QCheckBox()
        checkbox.setChecked(checklist_item.is_checked)
        checkbox.setStyleSheet("""
            QCheckBox {
                color: #37352f;
                font-size: 14px;
            }
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
            QCheckBox::indicator:checked:after {
                content: "✓";
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        checkbox.stateChanged.connect(lambda state, idx=item_index: self.on_checklist_checked(idx, state == Qt.Checked))
        layout.addWidget(checkbox)
        
        # 텍스트 입력 - Notion 스타일 (반응형 QTextEdit)
        text_edit = QTextEdit(checklist_item.text)
        text_edit.setPlaceholderText(f"체크리스트 항목 {item_index + 1}")
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_edit.setMinimumHeight(30)
        text_edit.setMaximumHeight(150)
        text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #37352f;
                font-size: 14px;
                padding: 4px;
                selection-background-color: #d4e5fc;
            }
            QTextEdit:focus {
                background-color: #ffffff;
                border: none;
            }
            QTextEdit:hover {
                background-color: rgba(55, 53, 47, 0.03);
            }
        """)

        # 텍스트 변경 시 자동 높이 조절
        def adjust_height():
            doc_height = text_edit.document().size().height()
            text_edit.setFixedHeight(min(max(int(doc_height) + 10, 30), 150))

        text_edit.textChanged.connect(adjust_height)
        text_edit.textChanged.connect(lambda idx=item_index: self.on_checklist_text_changed(idx, text_edit.toPlainText()))
        adjust_height()  # 초기 높이 설정

        layout.addWidget(text_edit)
        
        # 가중치 입력 - Notion 스타일
        weight_label = QLabel("가중치:")
        weight_label.setStyleSheet("""
            QLabel {
                color: #9b9a97;
                font-size: 12px;
                min-width: 50px;
            }
        """)
        layout.addWidget(weight_label)

        weight_spin = QSpinBox()
        weight_spin.setRange(1, 100)
        weight_spin.setValue(checklist_item.score)
        weight_spin.setMaximumWidth(60)
        weight_spin.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                color: #37352f;
                font-size: 13px;
                padding: 2px;
            }
            QSpinBox:focus {
                border: 1px solid #2383e2;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 14px;
                background-color: rgba(55, 53, 47, 0.08);
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: rgba(55, 53, 47, 0.12);
            }
        """)
        weight_spin.valueChanged.connect(lambda value, idx=item_index: self.on_checklist_weight_changed(idx, value))
        layout.addWidget(weight_spin)

        # 삭제 버튼 - Notion 스타일
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(22, 22)
        delete_btn.setStyleSheet("""
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
        delete_btn.setToolTip("항목 삭제")
        delete_btn.clicked.connect(lambda checked, idx=item_index: self.remove_checklist_item(idx))
        layout.addWidget(delete_btn)
        
        return widget
    
    def on_checklist_checked(self, item_index, is_checked):
        """체크리스트 항목 체크 상태 변경"""
        if 0 <= item_index < len(self.item.checklist):
            self.item.checklist[item_index].is_checked = is_checked
            self.update_progress_display()
            self.update_checklist_count()
            self.item_changed.emit()

            # 부모 위젯들의 점수도 업데이트
            self.propagate_update_to_parents()
    
    def on_checklist_text_changed(self, item_index, text):
        """체크리스트 항목 텍스트 변경"""
        if 0 <= item_index < len(self.item.checklist):
            self.item.checklist[item_index].text = text
            self.item_changed.emit()
    
    def on_checklist_weight_changed(self, item_index, weight):
        """체크리스트 항목 가중치 변경"""
        if 0 <= item_index < len(self.item.checklist):
            self.item.checklist[item_index].score = weight
            self.update_max_score_display()  # 최대 점수 자동 업데이트
            self.update_progress_display()
            self.item_changed.emit()

            # 부모 위젯들의 점수도 업데이트
            self.propagate_update_to_parents()

    def propagate_update_to_parents(self):
        """부모 위젯들에 업데이트 전파"""
        # 직접 참조된 부모 ToggleWidget 업데이트
        if self.parent_toggle_widget:
            self.parent_toggle_widget.update_progress_display()
            # 재귀적으로 상위 부모들도 업데이트
            self.parent_toggle_widget.propagate_update_to_parents()

    def setup_style(self):
        # 초기 테두리 스타일 설정
        self.update_border_style()
        
        # 자식 요소들에 개별적으로 스타일 적용 (테두리 스타일과 분리)
        self.apply_child_styles()
    
    def apply_child_styles(self):
        # Notion 라이트 모드 버튼 스타일
        button_style = """
            QPushButton {
                background-color: rgba(55, 53, 47, 0.08);
                border: none;
                border-radius: 3px;
                color: #37352f;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.12);
            }
            QPushButton:pressed {
                background-color: rgba(55, 53, 47, 0.16);
            }
        """

        # Notion 라이트 모드 입력 필드 스타일
        input_style = """
            QLineEdit, QTextEdit, QSpinBox {
                background-color: #ffffff;
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                color: #37352f;
                padding: 4px;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border: 1px solid #2383e2;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: rgba(55, 53, 47, 0.08);
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: rgba(55, 53, 47, 0.12);
            }
        """

        # Notion 라이트 모드 레이블 스타일
        label_style = """
            QLabel {
                color: #37352f;
            }
        """

        # 모든 자식 위젯에 스타일 적용
        for child in self.findChildren(QWidget):
            if child.parent() == self:
                child.setStyleSheet(button_style + input_style + label_style)
    
    def connect_signals(self):
        self.title_edit.textChanged.connect(self.on_title_changed)
        # content_edit는 블록 기반 시스템으로 대체되어 제거됨

    def on_title_changed(self):
        self.item.title = self.title_edit.text()
        self.item_changed.emit()

    def on_content_changed(self):
        """블록 기반 시스템에서는 사용하지 않음"""
        pass
    
    def toggle_expanded(self):
        self.item.is_expanded = not self.item.is_expanded

        # 토글을 펼칠 때 블록이 없으면 다시 로드
        if self.item.is_expanded and self.blocks_layout.count() == 0:
            print(f"[DEBUG] '{self.item.title}' 토글 펼침 - 블록이 없음, 다시 로드")
            self.load_blocks_from_item()

        self.update_children_visibility()
        self.update_content_visibility()
        self.toggle_btn.setText("▼" if self.item.is_expanded else "▶")

        # 디버깅: 블록 개수 확인
        print(f"[DEBUG] 토글 '{self.item.title}' {'펼침' if self.item.is_expanded else '접힘'}, 블록 개수: {self.blocks_layout.count()}")

        self.item_changed.emit()
    
    def update_children_visibility(self):
        self.children_widget.setVisible(self.item.is_expanded and len(self.child_widgets) > 0)
    
    def update_content_visibility(self):
        self.content_widget.setVisible(self.item.is_expanded)
    
    def update_score_inputs_visibility(self):
        # 점수 입력 필드는 항상 숨김 (체크리스트로만 점수 계산)
        # 하위 항목이 있든 없든 점수는 체크리스트 합계로만 결정됨
        pass
    
    def update_max_score_display(self):
        """체크리스트 합계로 최대 점수를 자동 계산 (화면 표시는 진행률에만 표시)"""
        # max_score는 get_total_max_score()에서 자동으로 계산되므로 별도 업데이트 불필요
        pass

    def update_progress_display(self):
        progress_text = self.item.get_progress_text()
        percentage = self.item.get_completion_percentage()

        # Notion 스타일 색상
        color = "#eb5757"  # 빨강
        if percentage >= 80:
            color = "#0f7b6c"  # 초록
        elif percentage >= 50:
            color = "#d9730d"  # 주황

        self.progress_label.setText(progress_text)
        self.progress_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: 600; font-size: 12px; }}")

        # 최대 점수도 함께 업데이트
        self.update_max_score_display()
    
    def update_source_file_display(self):
        if self.item.source_file:
            filename = os.path.basename(self.item.source_file)
            self.source_file_label.setText(f"📁 {filename}")
            self.source_file_label.setToolTip(f"연결된 파일: {self.item.source_file}\n💾 저장 버튼으로 이 파일을 업데이트할 수 있습니다")
        else:
            self.source_file_label.setText("")
            self.source_file_label.setToolTip("")
    
    def update_display(self):
        self.title_edit.setText(self.item.title)
        # content는 블록들로 표시되므로 별도 처리 불필요
        self.toggle_btn.setText("▼" if self.item.is_expanded else "▶")
        self.update_source_file_display()
        self.update_progress_display()
        self.update_children_visibility()
        self.update_content_visibility()

    def update_layout(self):
        """레이아웃을 즉시 업데이트하여 텍스트 블록 높이 변경 반영"""
        # 블록 컨테이너 레이아웃 업데이트
        self.blocks_layout.update()
        self.blocks_layout.activate()

        # 콘텐츠 레이아웃 업데이트
        self.content_layout.update()
        self.content_layout.activate()

        # 메인 레이아웃 업데이트
        self.main_layout.update()
        self.main_layout.activate()

        # 위젯 크기 재계산
        self.updateGeometry()

        # 부모 위젯들도 업데이트
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'updateGeometry'):
                parent.updateGeometry()
            parent = parent.parentWidget()
    
    def add_child_widget(self, child_widget):
        if child_widget not in self.child_widgets:
            self.child_widgets.append(child_widget)
            self.children_layout.addWidget(child_widget)
            self.update_children_visibility()
            self.update_score_inputs_visibility()

            # 부모 위젯 참조 설정
            child_widget.parent_toggle_widget = self
            child_widget.item_changed.connect(self.on_child_changed)

            # 새로운 자식 위젯에도 이벤트 필터 설치
            for child in child_widget.findChildren(QWidget):
                if child != child_widget:
                    child.installEventFilter(child_widget)
    
    def remove_child_widget(self, child_widget):
        if child_widget in self.child_widgets:
            self.child_widgets.remove(child_widget)
            self.children_layout.removeWidget(child_widget)
            child_widget.parent_toggle_widget = None  # 참조 정리
            child_widget.setParent(None)
            self.update_children_visibility()
            self.update_score_inputs_visibility()
    
    def on_child_changed(self):
        self.update_progress_display()
        self.item_changed.emit()

        # 부모 위젯이 있다면 부모의 표시도 업데이트
        if hasattr(self.parent(), 'update_progress_display'):
            self.parent().update_progress_display()
    
    def on_child_delete_requested(self, child_widget):
        # 최상위 부모에서만 삭제 처리
        pass
    
    def on_child_add_requested(self, parent_widget):
        self.add_child_requested.emit(parent_widget)
    
    def request_delete(self):
        self.delete_requested.emit(self)
    
    def request_save(self):
        self.save_requested.emit(self)
    
    def show_context_menu(self):
        menu = QMenu(self)
        
        add_child_action = QAction("하위 토글 추가", self)
        add_child_action.triggered.connect(lambda: self.add_child_requested.emit(self))
        menu.addAction(add_child_action)
        
        menu.exec_(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
    
    def install_event_filters(self):
        """자식 위젯들에 이벤트 필터 설치"""
        for child in self.findChildren(QWidget):
            if child != self:
                child.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """이벤트 필터 - 자식 위젯의 마우스 이벤트를 부모로 전달"""
        # content_edit는 블록 기반 시스템으로 대체됨
        # 각 블록이 자체적으로 "/" 입력을 처리함

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # Ctrl 키가 눌렸거나 위젯이 버튼이 아닌 경우에만 드래그 가능
            if (QApplication.keyboardModifiers() & Qt.ControlModifier) or \
               not isinstance(obj, (QPushButton, QCheckBox)):
                self.mousePressEvent(event)
        elif event.type() == QEvent.MouseMove:
            if (QApplication.keyboardModifiers() & Qt.ControlModifier) or \
               not isinstance(obj, (QPushButton, QCheckBox)):
                self.mouseMoveEvent(event)
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if (QApplication.keyboardModifiers() & Qt.ControlModifier) or \
               not isinstance(obj, (QPushButton, QCheckBox)):
                self.mouseReleaseEvent(event)

        return super().eventFilter(obj, event)

    def on_slash_command(self, command_type, data):
        """슬래시 명령어 실행 - 블록 기반"""
        # "+ 블록 추가" 버튼 바로 위에 추가
        insert_index = self.blocks_layout.count()

        if command_type == "add_text":
            # 텍스트 블록 추가
            self.add_text_block("", insert_index)

        elif command_type == "add_checklist":
            # 체크리스트 블록 추가
            self.add_checklist_block("", insert_index)

        elif command_type == "add_child_toggle":
            # 하위 토글 추가
            self.add_child_requested.emit(self)

        elif command_type == "add_date":
            # 프로젝트 기간 블록 추가
            self.add_date_block(insert_index)

        elif command_type == "add_divider":
            # 구분선 블록 추가
            self.add_divider_block(insert_index)

        self.item_changed.emit()

    def on_add_block_clicked(self):
        """+ 블록 추가 버튼 클릭"""
        self.current_slash_block = None
        pos = self.add_block_btn.mapToGlobal(self.add_block_btn.rect().bottomLeft())
        self.slash_menu.show_menu(pos, "")

    def add_text_block(self, text="", insert_index=-1):
        """텍스트 블록 추가"""
        from components.inline_widgets import InlineTextBlockWidget

        text_block = InlineTextBlockWidget(text)
        text_block.content_changed.connect(self.item_changed.emit)
        text_block.content_changed.connect(self.update_layout)  # 레이아웃 즉시 업데이트
        text_block.delete_requested.connect(self.on_block_delete)
        text_block.slash_pressed.connect(self.on_block_slash_pressed)

        if insert_index == -1 or insert_index >= self.blocks_layout.count():
            self.blocks_layout.addWidget(text_block)
        else:
            self.blocks_layout.insertWidget(insert_index, text_block)

        # 초기 높이 조절 (텍스트가 있을 때)
        if text:
            QTimer.singleShot(0, lambda: self._adjust_text_block_height(text_block))

        text_block.focus()
        return text_block

    def _adjust_text_block_height(self, text_block):
        """텍스트 블록 높이를 내용에 맞게 조절"""
        if hasattr(text_block, 'text_edit'):
            doc_height = text_block.text_edit.document().size().height()
            text_block.text_edit.setFixedHeight(max(int(doc_height) + 10, 30))
            self.update_layout()

    def add_checklist_block(self, text="", insert_index=-1):
        """체크리스트 블록 추가"""
        from components.inline_widgets import InlineCheckboxWidget

        checkbox = InlineCheckboxWidget(text, False, 1)
        checkbox.content_changed.connect(self.item_changed.emit)
        checkbox.content_changed.connect(self.update_progress_from_blocks)
        checkbox.content_changed.connect(self.update_layout)  # 레이아웃 즉시 업데이트
        checkbox.delete_requested.connect(self.on_block_delete)

        if insert_index == -1 or insert_index >= self.blocks_layout.count():
            self.blocks_layout.addWidget(checkbox)
        else:
            self.blocks_layout.insertWidget(insert_index, checkbox)

        self.update_inline_checkbox_numbers()
        return checkbox

    def add_date_block(self, insert_index=-1):
        """날짜 블록 추가"""
        from components.inline_widgets import InlineDateWidget

        date_widget = InlineDateWidget("", "")
        date_widget.content_changed.connect(self.item_changed.emit)
        date_widget.delete_requested.connect(self.on_block_delete)

        if insert_index == -1 or insert_index >= self.blocks_layout.count():
            self.blocks_layout.addWidget(date_widget)
        else:
            self.blocks_layout.insertWidget(insert_index, date_widget)

        return date_widget

    def add_divider_block(self, insert_index=-1):
        """구분선 블록 추가"""
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("""
            QFrame {
                background-color: #e9e9e7;
                border: none;
                max-height: 1px;
                margin: 8px 0px;
            }
        """)

        if insert_index == -1 or insert_index >= self.blocks_layout.count():
            self.blocks_layout.addWidget(divider)
        else:
            self.blocks_layout.insertWidget(insert_index, divider)

        return divider

    def on_block_delete(self, block_widget):
        """블록 삭제"""
        self.blocks_layout.removeWidget(block_widget)
        block_widget.setParent(None)
        block_widget.deleteLater()

        # 체크박스 번호 재정렬
        self.update_inline_checkbox_numbers()
        # 점수 업데이트
        self.update_progress_from_blocks()
        self.item_changed.emit()

    def on_block_slash_pressed(self, block_widget):
        """블록에서 / 입력됨"""
        self.current_slash_block = block_widget
        pos = block_widget.get_cursor_position()
        self.slash_menu.show_menu(pos, "")

    def update_progress_from_blocks(self):
        """블록들로부터 점수 계산 및 업데이트"""
        from components.inline_widgets import InlineCheckboxWidget

        total_score = 0
        total_weight = 0

        for i in range(self.blocks_layout.count()):
            widget = self.blocks_layout.itemAt(i).widget()
            if isinstance(widget, InlineCheckboxWidget):
                total_weight += widget.weight
                if widget.is_checked:
                    total_score += widget.weight

        # item.checklist 동기화 (저장을 위해)
        self.item.checklist.clear()
        for i in range(self.blocks_layout.count()):
            widget = self.blocks_layout.itemAt(i).widget()
            if isinstance(widget, InlineCheckboxWidget):
                from models.toggle_item import ChecklistItem
                checklist_item = ChecklistItem(
                    text=widget.text_value,
                    is_checked=widget.is_checked,
                    score=widget.weight
                )
                self.item.checklist.append(checklist_item)

        self.update_progress_display()
        self.propagate_update_to_parents()

    def on_inline_checkbox_delete(self, checkbox_widget):
        """인라인 체크박스 삭제 (하위 호환성)"""
        self.on_block_delete(checkbox_widget)

    def on_inline_date_delete(self, date_widget):
        """인라인 날짜 위젯 삭제"""
        # 레이아웃에서 제거
        self.content_layout.removeWidget(date_widget)
        date_widget.setParent(None)
        date_widget.deleteLater()
        self.item_changed.emit()

    def has_date_widget(self):
        """날짜 위젯이 이미 존재하는지 확인"""
        from components.inline_widgets import InlineDateWidget

        for i in range(self.blocks_layout.count()):
            widget = self.blocks_layout.itemAt(i).widget()
            if isinstance(widget, InlineDateWidget):
                return True
        return False

    def update_inline_checkbox_numbers(self):
        """인라인 체크박스 항목 번호 업데이트"""
        from components.inline_widgets import InlineCheckboxWidget

        checkbox_count = 0
        for i in range(self.blocks_layout.count()):
            widget = self.blocks_layout.itemAt(i).widget()
            if isinstance(widget, InlineCheckboxWidget):
                checkbox_count += 1
                widget.set_item_number(checkbox_count)

    def load_blocks_from_item(self):
        """기존 item 데이터를 블록으로 로드"""
        # 기존 content가 있으면 텍스트 블록으로 추가 (한 줄씩 분리)
        if self.item.content and self.item.content.strip():
            # 줄바꿈으로 분리
            lines = self.item.content.split('\n')
            for line in lines:
                line = line.strip()
                if line:  # 빈 줄은 무시
                    self.add_text_block(line)

        # 기존 checklist가 있으면 체크리스트 블록으로 추가
        for checklist_item in self.item.checklist:
            checkbox = self.add_checklist_block(
                text=checklist_item.text,
                insert_index=-1
            )
            checkbox.checkbox.setChecked(checklist_item.is_checked)
            checkbox.weight_spin.setValue(checklist_item.score)

        # 블록이 하나도 없으면 초기 텍스트 블록 추가
        if self.blocks_layout.count() == 0:
            self.add_text_block("")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_selected(True)
            self.selection_changed.emit(self)
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not self.drag_start_position:
            return
            
        # 드래그 거리 체크
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
            
        # 드래그 시작
        self.start_drag()
        self.drag_start_position = None  # 드래그 완료 후 초기화
    
    def mouseReleaseEvent(self, event):
        """마우스 릴리즈 이벤트"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = None
        super().mouseReleaseEvent(event)
        
    def start_drag(self):
        """드래그 시작"""
        drag = QDrag(self)
        mimeData = QMimeData()
        
        # 이 위젯의 고유 식별자를 저장
        mimeData.setText(f"toggle_widget_{id(self)}")
        drag.setMimeData(mimeData)
        
        # 드래그 이미지 생성
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)
        
        # 드래그 실행
        drop_action = drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """드래그가 위젯 위에 들어왔을 때"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("toggle_widget_"):
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet() + "QFrame { border: 2px dashed #0078d4; }")
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        """드래그가 위젯을 벗어났을 때"""
        self.update_border_style()
        self.apply_child_styles()
    
    def dropEvent(self, event):
        """드롭 이벤트"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("toggle_widget_"):
            # 원래 스타일로 복원
            self.update_border_style()
            self.apply_child_styles()
            
            # 드롭된 위젯의 ID 추출
            dragged_widget_id = event.mimeData().text().replace("toggle_widget_", "")
            
            # 부모에게 이동 요청 전달
            self.move_requested.emit(self, int(dragged_widget_id))
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_border_style()
    
    def update_border_style(self):
        if self.is_selected:
            border_color = "#e9e9e7"
            background_color = "#f7f6f3"
            border_width = "1px"
        else:
            border_color = "transparent"
            background_color = "#ffffff"
            border_width = "1px"

        # Notion 스타일 - 깔끔한 라이트 모드
        widget_style = f"""
            ToggleWidget {{
                background-color: {background_color};
                border: {border_width} solid {border_color};
                border-radius: 3px;
                margin: 2px;
                padding: 8px;
            }}
            ToggleWidget:hover {{
                background-color: #f7f6f3;
                border-color: #e9e9e7;
            }}
        """
        self.setStyleSheet(widget_style)

        # 자식 요소들의 스타일을 다시 적용
        self.apply_child_styles()