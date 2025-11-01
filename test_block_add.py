"""블록 추가 기능 테스트"""
import sys
sys.path.insert(0, 'src')

from PyQt5.QtWidgets import QApplication
from models.toggle_item import ToggleItem
from components.toggle_widget import ToggleWidget

app = QApplication(sys.argv)

# 테스트용 토글 아이템 및 위젯 생성
item = ToggleItem("테스트 토글", "")
widget = ToggleWidget(item)

# 토글 펼치기
widget.item.is_expanded = True
widget.update_content_visibility()

print(f"초기 블록 개수: {widget.blocks_layout.count()}")

# 텍스트 블록 추가 테스트
print("\n텍스트 블록 추가 중...")
widget.on_slash_command("add_text", None)
print(f"텍스트 블록 추가 후: {widget.blocks_layout.count()}")

# 체크리스트 블록 추가 테스트
print("\n체크리스트 블록 추가 중...")
widget.on_slash_command("add_checklist", None)
print(f"체크리스트 블록 추가 후: {widget.blocks_layout.count()}")

# 구분선 블록 추가 테스트
print("\n구분선 블록 추가 중...")
widget.on_slash_command("add_divider", None)
print(f"구분선 블록 추가 후: {widget.blocks_layout.count()}")

print("\n모든 테스트 완료!")
print(f"최종 블록 개수: {widget.blocks_layout.count()}")

# 각 블록 확인
print("\n추가된 블록들:")
for i in range(widget.blocks_layout.count()):
    block = widget.blocks_layout.itemAt(i).widget()
    print(f"  {i}: {type(block).__name__}")
