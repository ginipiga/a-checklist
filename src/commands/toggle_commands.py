import copy
from typing import Optional, Any
from .base_command import Command


class AddToggleCommand(Command):
    """토글 추가 명령"""

    def __init__(self, app, parent_widget, item_data=None):
        self.app = app
        self.parent_widget = parent_widget
        self.item_data = item_data or {"title": "새 토글", "content": ""}
        self.created_widget = None

    def execute(self):
        from models.toggle_item import ToggleItem
        child_item = ToggleItem(self.item_data["title"], self.item_data.get("content", ""))

        if self.parent_widget:
            self.parent_widget.item.add_child(child_item)
            self.created_widget = self.app.add_widget_for_item(child_item, self.parent_widget, False)
        else:
            self.app.root_items.append(child_item)
            self.created_widget = self.app.add_widget_for_item(child_item, None, True)

        self.app.mark_modified()

    def undo(self):
        if self.created_widget:
            self.app.delete_widget(self.created_widget)

    def get_description(self) -> str:
        return f"토글 추가: {self.item_data['title']}"


class DeleteToggleCommand(Command):
    """토글 삭제 명령"""

    def __init__(self, app, widget):
        self.app = app
        self.widget = widget
        self.parent_widget = None
        self.item_data = None
        self.item_index = -1
        self.widget_index = -1

    def execute(self):
        # 삭제 전 정보 저장
        self.item_data = self.widget.item.to_dict()

        # 부모 관계 저장
        if self.widget.item.parent:
            self.parent_widget = self._find_widget_for_item(self.widget.item.parent)
            self.item_index = self.widget.item.parent.children.index(self.widget.item)
            if self.parent_widget:
                self.widget_index = self.parent_widget.child_widgets.index(self.widget)
        else:
            self.item_index = self.app.root_items.index(self.widget.item)
            self.widget_index = self.app.root_widgets.index(self.widget)

        # 실제 삭제
        self.app.delete_widget(self.widget)

    def undo(self):
        from models.toggle_item import ToggleItem
        # 아이템 복원
        restored_item = ToggleItem.from_dict(self.item_data)

        if self.parent_widget:
            # 부모가 있는 경우
            self.parent_widget.item.children.insert(self.item_index, restored_item)
            restored_item.parent = self.parent_widget.item
            self.widget = self.app.add_widget_for_item(restored_item, self.parent_widget, False)
            # 원래 위치에 삽입
            self.parent_widget.children_layout.removeWidget(self.widget)
            self.parent_widget.children_layout.insertWidget(self.widget_index, self.widget)
            self.parent_widget.child_widgets.insert(self.widget_index, self.widget)
        else:
            # 최상위 아이템인 경우
            self.app.root_items.insert(self.item_index, restored_item)
            self.widget = self.app.add_widget_for_item(restored_item, None, True)
            # 원래 위치에 삽입
            self.app.scroll_layout.removeWidget(self.widget)
            self.app.scroll_layout.insertWidget(self.widget_index, self.widget)
            self.app.root_widgets.insert(self.widget_index, self.widget)

        self.app.mark_modified()

    def _find_widget_for_item(self, item):
        """아이템에 해당하는 위젯 찾기"""
        for widget in self.app.root_widgets:
            if widget.item == item:
                return widget
        return None

    def get_description(self) -> str:
        return f"토글 삭제: {self.item_data.get('title', '알 수 없음') if self.item_data else '알 수 없음'}"


class EditToggleCommand(Command):
    """토글 편집 명령"""

    def __init__(self, widget, field_name: str, old_value: Any, new_value: Any):
        self.widget = widget
        self.field_name = field_name
        self.old_value = copy.deepcopy(old_value)
        self.new_value = copy.deepcopy(new_value)

    def execute(self):
        setattr(self.widget.item, self.field_name, self.new_value)
        self.widget.update_display()

    def undo(self):
        setattr(self.widget.item, self.field_name, self.old_value)
        self.widget.update_display()

    def get_description(self) -> str:
        field_names = {
            'title': '제목',
            'content': '내용',
            'risk_score': '현재 점수',
            'max_score': '최대 점수'
        }
        field_korean = field_names.get(self.field_name, self.field_name)
        return f"{field_korean} 변경: '{self.old_value}' → '{self.new_value}'"


class ChecklistCommand(Command):
    """체크리스트 명령"""

    def __init__(self, widget, action: str, **kwargs):
        self.widget = widget
        self.action = action  # 'add', 'remove', 'check', 'edit_text', 'edit_weight'
        self.kwargs = kwargs
        self.old_state = None

    def execute(self):
        # 현재 상태 저장
        self.old_state = copy.deepcopy(self.widget.item.checklist)

        if self.action == 'add':
            from models.toggle_item import ChecklistItem
            new_item = ChecklistItem(**self.kwargs)
            self.widget.item.checklist.append(new_item)

        elif self.action == 'remove':
            index = self.kwargs['index']
            if 0 <= index < len(self.widget.item.checklist):
                del self.widget.item.checklist[index]

        elif self.action == 'check':
            index = self.kwargs['index']
            is_checked = self.kwargs['is_checked']
            if 0 <= index < len(self.widget.item.checklist):
                self.widget.item.checklist[index].is_checked = is_checked

        elif self.action == 'edit_text':
            index = self.kwargs['index']
            text = self.kwargs['text']
            if 0 <= index < len(self.widget.item.checklist):
                self.widget.item.checklist[index].text = text

        elif self.action == 'edit_weight':
            index = self.kwargs['index']
            weight = self.kwargs['weight']
            if 0 <= index < len(self.widget.item.checklist):
                self.widget.item.checklist[index].score = weight

        self.widget.refresh_checklist()
        self.widget.update_progress_display()
        self.widget.update_checklist_count()

    def undo(self):
        # 이전 상태로 복원
        self.widget.item.checklist = copy.deepcopy(self.old_state)
        self.widget.refresh_checklist()
        self.widget.update_progress_display()
        self.widget.update_checklist_count()

    def get_description(self) -> str:
        action_names = {
            'add': '체크리스트 항목 추가',
            'remove': '체크리스트 항목 삭제',
            'check': '체크리스트 체크',
            'edit_text': '체크리스트 텍스트 수정',
            'edit_weight': '체크리스트 가중치 수정'
        }
        return action_names.get(self.action, '체크리스트 수정')