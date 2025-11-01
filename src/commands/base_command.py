from abc import ABC, abstractmethod


class Command(ABC):
    """명령 패턴의 기본 인터페이스"""

    @abstractmethod
    def execute(self):
        """명령 실행"""
        pass

    @abstractmethod
    def undo(self):
        """명령 취소"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """명령 설명 반환"""
        pass


class CommandHistory:
    """명령 히스토리 관리"""

    def __init__(self, max_history=50):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history

    def execute_command(self, command: Command):
        """명령 실행 및 히스토리에 추가"""
        command.execute()
        self.undo_stack.append(command)

        # 새로운 명령 실행 시 redo 스택 클리어
        self.redo_stack.clear()

        # 히스토리 크기 제한
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self):
        """마지막 명령 취소"""
        if self.can_undo():
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            return True
        return False

    def redo(self):
        """취소된 명령 다시 실행"""
        if self.can_redo():
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            return True
        return False

    def can_undo(self) -> bool:
        """Undo 가능 여부"""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Redo 가능 여부"""
        return len(self.redo_stack) > 0

    def get_undo_description(self) -> str:
        """다음 Undo될 명령의 설명"""
        if self.can_undo():
            return self.undo_stack[-1].get_description()
        return ""

    def get_redo_description(self) -> str:
        """다음 Redo될 명령의 설명"""
        if self.can_redo():
            return self.redo_stack[-1].get_description()
        return ""

    def clear(self):
        """히스토리 초기화"""
        self.undo_stack.clear()
        self.redo_stack.clear()