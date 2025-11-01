"""
AI 분석 결과를 표시하는 다이얼로그
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLabel, QProgressBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class AnalysisResultDialog(QDialog):
    """분석 결과 표시 다이얼로그"""

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 800, 600)
        self.setup_ui(content)

    def setup_ui(self, content: str):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 제목 레이블
        title_label = QLabel(self.windowTitle())
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 내용 표시 (마크다운 스타일)
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMarkdown(content)

        # 스타일 적용
        self.content_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e9e9e7;
                border-radius: 5px;
                padding: 15px;
                font-size: 11pt;
                line-height: 1.6;
            }
        """)

        layout.addWidget(self.content_text)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 복사 버튼
        copy_btn = QPushButton("📋 클립보드에 복사")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(55, 53, 47, 0.08);
                border: none;
                border-radius: 3px;
                color: #37352f;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(55, 53, 47, 0.12);
            }
        """)
        button_layout.addWidget(copy_btn)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: none;
                border-radius: 3px;
                color: white;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def copy_to_clipboard(self):
        """내용을 클립보드에 복사"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content_text.toPlainText())

        # 임시로 버튼 텍스트 변경
        sender = self.sender()
        original_text = sender.text()
        sender.setText("✅ 복사됨!")

        # 1초 후 원래대로
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, lambda: sender.setText(original_text))


class ProgressAnalysisDialog(QDialog):
    """진행 상황 분석 중 표시 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("진행 상황 분석 중...")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # 상태 레이블
        self.status_label = QLabel("AI가 프로젝트 진행 상황을 분석하고 있습니다...")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e9e9e7;
                border-radius: 3px;
                background-color: #f7f7f7;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def update_status(self, message: str):
        """상태 메시지 업데이트"""
        self.status_label.setText(message)
