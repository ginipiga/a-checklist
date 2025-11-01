import json
from typing import List, Dict, Any, Optional


class ChecklistItem:
    def __init__(self, text: str = "", is_checked: bool = False, score: int = 1,
                 weight_evaluation: Optional[Dict[str, Any]] = None,
                 summary: str = "", detail: str = ""):
        self.text = text
        self.is_checked = is_checked
        self.score = score
        self.weight_evaluation = weight_evaluation or {}  # 가중치 평가 정보
        self.summary = summary or text  # 요약 (토글 접혔을 때 표시)
        self.detail = detail  # 상세 내용 (토글 펼쳤을 때 표시)

    def get_priority(self) -> str:
        """가중치 평가에서 계산된 우선순위 반환"""
        if self.weight_evaluation and 'priority' in self.weight_evaluation:
            return self.weight_evaluation['priority']
        return 'Medium'

    def get_final_score(self) -> int:
        """가중치 평가에서 계산된 최종 점수 반환"""
        if self.weight_evaluation and 'evaluation' in self.weight_evaluation:
            return self.weight_evaluation['evaluation'].get('final_score', self.score)
        return self.score

    def to_dict(self) -> Dict[str, Any]:
        result = {
            'text': self.text,
            'is_checked': self.is_checked,
            'score': self.score,
            'summary': self.summary,
            'detail': self.detail
        }
        if self.weight_evaluation:
            result['weight_evaluation'] = self.weight_evaluation
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChecklistItem':
        return cls(
            text=data.get('text', ''),
            is_checked=data.get('is_checked', False),
            score=data.get('score', 1),
            weight_evaluation=data.get('weight_evaluation', None),
            summary=data.get('summary', data.get('text', '')),
            detail=data.get('detail', '')
        )


class ToggleItem:
    def __init__(self, title: str = "새 토글", content: str = "",
                 risk_score: int = 0, max_score: int = 100, is_deletable: bool = True):
        self.title = title
        self.content = content
        self.risk_score = risk_score
        self.max_score = max_score
        self.children: List[ToggleItem] = []
        self.is_expanded = True
        self.parent: Optional[ToggleItem] = None
        self.is_deletable = is_deletable
        self.checklist: List[ChecklistItem] = []
        self.source_file: Optional[str] = None
        self.date: Optional[str] = None  # 날짜 (YYYY-MM-DD)
        self.deadline: Optional[str] = None  # 마감 기한 (YYYY-MM-DD)
    
    def add_child(self, child: 'ToggleItem'):
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'ToggleItem'):
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def get_checklist_score(self) -> int:
        return sum(item.score for item in self.checklist if item.is_checked)
    
    def get_checklist_max_score(self) -> int:
        return sum(item.score for item in self.checklist)
    
    def get_total_score(self) -> int:
        # 자신의 체크리스트 점수
        total = self.get_checklist_score()

        # 모든 하위 토글의 점수 합산
        for child in self.children:
            total += child.get_total_score()

        return total

    def get_total_max_score(self) -> int:
        # 자신의 체크리스트 최대 점수
        total = self.get_checklist_max_score()

        # 모든 하위 토글의 최대 점수 합산
        for child in self.children:
            total += child.get_total_max_score()

        return total
    
    def get_progress_text(self) -> str:
        total_score = self.get_total_score()
        total_max = self.get_total_max_score()
        return f"{total_score}/{total_max} 완료"
    
    def get_completion_percentage(self) -> float:
        total_max = self.get_total_max_score()
        if total_max == 0:
            return 0.0
        return (self.get_total_score() / total_max) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'title': self.title,
            'content': self.content,
            'risk_score': self.risk_score,
            'max_score': self.max_score,
            'is_expanded': self.is_expanded,
            'is_deletable': self.is_deletable,
            'checklist': [item.to_dict() for item in self.checklist],
            'children': [child.to_dict() for child in self.children]
        }
        if self.source_file:
            result['source_file'] = self.source_file
        if self.date:
            result['date'] = self.date
        if self.deadline:
            result['deadline'] = self.deadline
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToggleItem':
        item = cls(
            title=data.get('title', '새 토글'),
            content=data.get('content', ''),
            risk_score=data.get('risk_score', 0),
            max_score=data.get('max_score', 100),
            is_deletable=data.get('is_deletable', True)
        )
        item.is_expanded = data.get('is_expanded', True)
        item.source_file = data.get('source_file', None)
        item.date = data.get('date', None)
        item.deadline = data.get('deadline', None)

        for checklist_data in data.get('checklist', []):
            checklist_item = ChecklistItem.from_dict(checklist_data)
            item.checklist.append(checklist_item)

        for child_data in data.get('children', []):
            child = cls.from_dict(child_data)
            item.add_child(child)

        return item
    
    def get_all_descendants(self) -> List['ToggleItem']:
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_depth(self) -> int:
        depth = 0
        current = self.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth