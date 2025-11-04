"""
검색어 매칭 항목 선택 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt


class KeywordSelectionDialog(QDialog):
    """검색어에 매칭된 여러 항목 중 하나를 선택하는 다이얼로그"""

    def __init__(self, search_keyword: str, matched_items: list, parent=None):
        super().__init__(parent)
        self.search_keyword = search_keyword
        self.matched_items = matched_items
        self.selected_index = None

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"'{self.search_keyword}' 검색 결과")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 설명
        info_label = QLabel(f"검색어 '<b>{self.search_keyword}</b>'가 {len(self.matched_items)}개 항목에서 발견되었습니다.<br>"
                           "하나를 선택하면 해당 항목의 하위 체크리스트만 추출합니다.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 목록
        layout.addSpacing(10)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        for item_info in self.matched_items:
            text = item_info['text']
            level = item_info['level']

            # 레벨에 따라 들여쓰기 표시
            indent = "  " * level
            display_text = f"{indent}[Level {level}] {text}"

            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item_info['index'])
            self.list_widget.addItem(list_item)

        # 첫 번째 항목 선택
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

        layout.addWidget(self.list_widget)

        # 버튼
        layout.addSpacing(10)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("선택")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def on_item_double_clicked(self, item):
        """항목 더블클릭 시 바로 선택"""
        self.accept()

    def accept(self):
        """선택 확인"""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_index = current_item.data(Qt.UserRole)
        super().accept()

    def get_selected_index(self):
        """선택된 항목의 인덱스 반환"""
        return self.selected_index
