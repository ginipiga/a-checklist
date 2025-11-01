"""
AI를 사용하여 작업 우선순위를 자동으로 분석하고 정렬하는 모듈
"""
import os
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime


class PriorityAnalyzer:
    """AI를 사용하여 작업 우선순위를 분석"""

    def __init__(self, llm_mode: str = "none"):
        """
        Args:
            llm_mode: LLM 모드 ("openai", "ollama", "none")
        """
        self.llm_mode = llm_mode or os.getenv("LLM_MODE", "none").lower()
        self.llm_analyzer = None

        # LLM 초기화
        if self.llm_mode == "openai":
            try:
                from .llm_analyzer import LLMDocumentAnalyzer, is_llm_available
                if is_llm_available():
                    self.llm_analyzer = LLMDocumentAnalyzer()
            except Exception as e:
                print(f"OpenAI 초기화 실패: {e}")
        elif self.llm_mode == "ollama":
            try:
                from .local_llm_analyzer import LocalLLMAnalyzer
                self.llm_analyzer = LocalLLMAnalyzer()
            except Exception as e:
                print(f"Ollama 초기화 실패: {e}")

    def analyze_and_sort_items(self, root_items: List[Any]) -> List[Tuple[Any, Dict[str, Any]]]:
        """
        작업 항목들을 분석하고 우선순위에 따라 정렬

        Args:
            root_items: ToggleItem 객체 리스트

        Returns:
            List[Tuple[ToggleItem, priority_info]]: (아이템, 우선순위 정보) 튜플 리스트
        """
        # 각 항목의 우선순위 분석
        items_with_priority = []

        for item in root_items:
            priority_info = self._analyze_item_priority(item)
            items_with_priority.append((item, priority_info))

        # AI를 사용한 정렬 (LLM 사용 가능 시)
        if self.llm_analyzer and self.llm_mode in ["openai", "ollama"]:
            items_with_priority = self._ai_sort_items(items_with_priority)
        else:
            # 기본 정렬 (점수 기반)
            items_with_priority.sort(key=lambda x: x[1]['priority_score'], reverse=True)

        return items_with_priority

    def _analyze_item_priority(self, item: Any) -> Dict[str, Any]:
        """개별 항목의 우선순위 분석"""
        priority_info = {
            'urgency_score': 0,      # 긴급도 (0-100)
            'importance_score': 0,    # 중요도 (0-100)
            'completion_rate': 0,     # 완료율 (0-100)
            'dependency_score': 0,    # 의존성 점수 (0-100)
            'priority_score': 0,      # 최종 우선순위 점수 (0-100)
            'priority_level': 'Medium',  # Critical, High, Medium, Low
            'reasons': []             # 우선순위 결정 이유
        }

        # 1. 완료율 계산
        priority_info['completion_rate'] = item.get_completion_percentage()

        # ✨ 완료된 작업은 우선순위를 최하위로 설정
        if priority_info['completion_rate'] >= 100:
            priority_info['priority_score'] = 0
            priority_info['priority_level'] = 'Low'
            priority_info['reasons'].append("작업 완료")
            return priority_info

        # 2. 긴급도 계산 (마감일 기준)
        if hasattr(item, 'deadline') and item.deadline:
            priority_info['urgency_score'] = self._calculate_urgency(item.deadline)
            if priority_info['urgency_score'] > 80:
                priority_info['reasons'].append(f"마감일 임박 ({item.deadline})")

        # 3. 중요도 계산 (체크리스트 우선순위 기준)
        priority_info['importance_score'] = self._calculate_importance(item)

        # 4. 의존성 점수 (하위 항목 수)
        total_descendants = len(item.get_all_descendants())
        priority_info['dependency_score'] = min(100, total_descendants * 10)
        if total_descendants > 5:
            priority_info['reasons'].append(f"{total_descendants}개의 하위 작업 포함")

        # 5. 최종 우선순위 점수 계산
        # 가중치: 긴급도 40%, 중요도 30%, 의존성 20%, 미완료율 10%
        incomplete_rate = 100 - priority_info['completion_rate']
        priority_info['priority_score'] = (
            priority_info['urgency_score'] * 0.4 +
            priority_info['importance_score'] * 0.3 +
            priority_info['dependency_score'] * 0.2 +
            incomplete_rate * 0.1
        )

        # 6. 우선순위 레벨 결정
        score = priority_info['priority_score']
        if score >= 80:
            priority_info['priority_level'] = 'Critical'
        elif score >= 60:
            priority_info['priority_level'] = 'High'
        elif score >= 40:
            priority_info['priority_level'] = 'Medium'
        else:
            priority_info['priority_level'] = 'Low'

        # 7. 추가 이유
        if priority_info['completion_rate'] < 20:
            priority_info['reasons'].append("시작 단계")
        elif priority_info['completion_rate'] > 80:
            priority_info['reasons'].append("거의 완료")

        return priority_info

    def _calculate_urgency(self, deadline_str: str) -> float:
        """마감일 기준 긴급도 계산 (0-100)"""
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            days_until = (deadline - today).days

            if days_until < 0:
                # 이미 지났으면 최고 긴급도
                return 100
            elif days_until == 0:
                return 100
            elif days_until <= 1:
                return 95
            elif days_until <= 3:
                return 85
            elif days_until <= 7:
                return 70
            elif days_until <= 14:
                return 50
            elif days_until <= 30:
                return 30
            else:
                return 10

        except:
            return 0

    def _calculate_importance(self, item: Any) -> float:
        """체크리스트 기반 중요도 계산 (0-100)"""
        if not item.checklist:
            return 50  # 기본값

        priority_weights = {
            'Critical': 100,
            'High': 75,
            'Medium': 50,
            'Low': 25
        }

        total_weight = 0
        count = 0

        for checklist_item in item.checklist:
            priority = checklist_item.get_priority()
            weight = priority_weights.get(priority, 50)
            total_weight += weight
            count += 1

        if count == 0:
            return 50

        return total_weight / count

    def _ai_sort_items(self, items_with_priority: List[Tuple[Any, Dict[str, Any]]]) -> List[Tuple[Any, Dict[str, Any]]]:
        """AI를 사용하여 항목 정렬"""
        try:
            # AI에게 제공할 항목 정보 준비
            items_info = []
            for idx, (item, priority_info) in enumerate(items_with_priority):
                info = {
                    'index': idx,
                    'title': item.title,
                    'completion_rate': priority_info['completion_rate'],
                    'urgency_score': priority_info['urgency_score'],
                    'importance_score': priority_info['importance_score'],
                    'dependency_score': priority_info['dependency_score'],
                    'priority_score': priority_info['priority_score'],
                    'deadline': getattr(item, 'deadline', None),
                    'checklist_count': len(item.checklist),
                    'children_count': len(item.children)
                }
                items_info.append(info)

            # AI 프롬프트 생성
            prompt = self._create_sorting_prompt(items_info)

            # LLM 호출
            if self.llm_mode == "openai":
                result = self._call_openai(prompt)
            elif self.llm_mode == "ollama":
                result = self._call_ollama(prompt)
            else:
                # 기본 정렬로 폴백
                items_with_priority.sort(key=lambda x: x[1]['priority_score'], reverse=True)
                return items_with_priority

            # AI 결과를 바탕으로 재정렬
            if result and 'sorted_indices' in result:
                sorted_items = []
                for idx in result['sorted_indices']:
                    if 0 <= idx < len(items_with_priority):
                        sorted_items.append(items_with_priority[idx])

                # 정렬되지 않은 항목 추가 (안전장치)
                sorted_indices_set = set(result['sorted_indices'])
                for idx, item_tuple in enumerate(items_with_priority):
                    if idx not in sorted_indices_set:
                        sorted_items.append(item_tuple)

                # AI의 추가 인사이트가 있으면 추가
                if 'insights' in result:
                    for insight in result['insights']:
                        idx = insight.get('index', -1)
                        if 0 <= idx < len(sorted_items):
                            sorted_items[idx][1]['ai_insight'] = insight.get('reason', '')

                return sorted_items
            else:
                # AI 결과가 이상하면 기본 정렬 사용
                items_with_priority.sort(key=lambda x: x[1]['priority_score'], reverse=True)
                return items_with_priority

        except Exception as e:
            print(f"AI 정렬 오류: {e}")
            # 오류 시 기본 정렬로 폴백
            items_with_priority.sort(key=lambda x: x[1]['priority_score'], reverse=True)
            return items_with_priority

    def _create_sorting_prompt(self, items_info: List[Dict[str, Any]]) -> str:
        """AI 정렬 프롬프트 생성"""
        prompt = """당신은 프로젝트 관리 전문가입니다. 다음 작업 항목들을 우선순위에 따라 정렬하세요.

## 작업 항목 정보:

"""
        for item in items_info:
            prompt += f"\n[{item['index']}] {item['title']}\n"
            prompt += f"  - 완료율: {item['completion_rate']:.1f}%\n"
            prompt += f"  - 긴급도: {item['urgency_score']:.1f}\n"
            prompt += f"  - 중요도: {item['importance_score']:.1f}\n"
            if item['deadline']:
                prompt += f"  - 마감일: {item['deadline']}\n"
            prompt += f"  - 체크리스트: {item['checklist_count']}개\n"
            prompt += f"  - 하위 작업: {item['children_count']}개\n"

        prompt += """

## 우선순위 결정 기준:
1. 마감일이 임박한 작업을 우선
2. 긴급도와 중요도가 높은 작업 우선
3. 미완료율이 낮으면서 마감일이 가까운 작업 우선 (빨리 끝낼 수 있는 것)
4. 의존성이 높은 작업 (다른 작업에 영향을 주는 작업) 우선

다음 형식의 JSON으로 응답하세요:

{
    "sorted_indices": [인덱스 순서대로 나열, 예: [2, 0, 3, 1, ...]],
    "insights": [
        {"index": 0, "reason": "우선순위 이유"},
        {"index": 1, "reason": "우선순위 이유"}
    ]
}
"""
        return prompt

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """OpenAI API 호출"""
        try:
            response = self.llm_analyzer.client.chat.completions.create(
                model=self.llm_analyzer.model,
                messages=[
                    {"role": "system", "content": "당신은 프로젝트 관리 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=2000
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"OpenAI 호출 오류: {e}")
            raise

    def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Ollama API 호출"""
        try:
            result = self.llm_analyzer.analyze_with_json_response(prompt)
            return result

        except Exception as e:
            print(f"Ollama 호출 오류: {e}")
            raise

    def get_priority_recommendations(self, root_items: List[Any]) -> str:
        """우선순위 추천 보고서 생성"""
        sorted_items = self.analyze_and_sort_items(root_items)

        report = "# 🎯 우선순위 분석 보고서\n\n"
        report += f"**분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += "## 추천 작업 순서\n\n"
        for idx, (item, priority_info) in enumerate(sorted_items, 1):
            level_emoji = {
                'Critical': '🔴',
                'High': '🟠',
                'Medium': '🟡',
                'Low': '🟢'
            }
            emoji = level_emoji.get(priority_info['priority_level'], '⚪')

            report += f"### {idx}. {emoji} {item.title}\n\n"
            report += f"- **우선순위 레벨**: {priority_info['priority_level']}\n"
            report += f"- **우선순위 점수**: {priority_info['priority_score']:.1f}/100\n"
            report += f"- **완료율**: {priority_info['completion_rate']:.1f}%\n"
            report += f"- **긴급도**: {priority_info['urgency_score']:.1f}/100\n"
            report += f"- **중요도**: {priority_info['importance_score']:.1f}/100\n"

            if hasattr(item, 'deadline') and item.deadline:
                report += f"- **마감일**: {item.deadline}\n"

            if priority_info['reasons']:
                report += f"- **주요 이유**: {', '.join(priority_info['reasons'])}\n"

            if 'ai_insight' in priority_info:
                report += f"- **AI 분석**: {priority_info['ai_insight']}\n"

            report += "\n"

        return report


def is_priority_analysis_available() -> bool:
    """우선순위 분석 기능 사용 가능 여부"""
    return True
