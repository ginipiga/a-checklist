"""
AI를 사용하여 프로젝트 진행 상황을 분석하고 요약하는 모듈
"""
import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta


class ProgressAnalyzer:
    """AI를 사용하여 프로젝트 진행 상황을 분석"""

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

    def analyze_progress(self, root_items: List[Any]) -> Dict[str, Any]:
        """
        전체 프로젝트의 진행 상황을 분석

        Args:
            root_items: ToggleItem 객체 리스트

        Returns:
            Dict: 진행 상황 분석 결과
        """
        # 기본 통계 수집
        stats = self._collect_statistics(root_items)

        # AI 분석 (LLM 사용 가능 시)
        if self.llm_analyzer and self.llm_mode in ["openai", "ollama"]:
            ai_insights = self._generate_ai_insights(stats, root_items)
            stats['ai_insights'] = ai_insights
        else:
            # 기본 인사이트
            stats['ai_insights'] = self._generate_basic_insights(stats)

        return stats

    def _collect_statistics(self, root_items: List[Any]) -> Dict[str, Any]:
        """기본 통계 정보 수집"""
        total_items = 0
        completed_items = 0
        total_score = 0
        max_score = 0
        total_checklist = 0
        completed_checklist = 0

        # 마감일 관련 통계
        overdue_items = []
        upcoming_items = []
        today = datetime.now().date()

        # 카테고리별 통계
        category_stats = {}

        # 우선순위별 통계
        priority_stats = {
            'Critical': {'total': 0, 'completed': 0},
            'High': {'total': 0, 'completed': 0},
            'Medium': {'total': 0, 'completed': 0},
            'Low': {'total': 0, 'completed': 0}
        }

        def traverse_item(item):
            nonlocal total_items, completed_items, total_score, max_score
            nonlocal total_checklist, completed_checklist

            total_items += 1
            item_score = item.get_total_score()
            item_max = item.get_total_max_score()
            total_score += item_score
            max_score += item_max

            # 완료 여부
            if item_max > 0 and item_score == item_max:
                completed_items += 1

            # 체크리스트 통계
            for checklist_item in item.checklist:
                total_checklist += 1
                if checklist_item.is_checked:
                    completed_checklist += 1

                # 우선순위 통계
                priority = checklist_item.get_priority()
                if priority in priority_stats:
                    priority_stats[priority]['total'] += 1
                    if checklist_item.is_checked:
                        priority_stats[priority]['completed'] += 1

            # 마감일 확인
            if hasattr(item, 'deadline') and item.deadline:
                try:
                    deadline = datetime.strptime(item.deadline, '%Y-%m-%d').date()
                    days_until = (deadline - today).days

                    if days_until < 0:
                        overdue_items.append({
                            'title': item.title,
                            'deadline': item.deadline,
                            'days_overdue': abs(days_until),
                            'progress': item.get_completion_percentage()
                        })
                    elif days_until <= 7:
                        upcoming_items.append({
                            'title': item.title,
                            'deadline': item.deadline,
                            'days_left': days_until,
                            'progress': item.get_completion_percentage()
                        })
                except:
                    pass

            # 하위 항목 탐색
            for child in item.children:
                traverse_item(child)

        # 모든 항목 탐색
        for root_item in root_items:
            traverse_item(root_item)

        # 전체 진행률 계산
        overall_progress = (total_score / max_score * 100) if max_score > 0 else 0

        return {
            'total_items': total_items,
            'completed_items': completed_items,
            'total_score': total_score,
            'max_score': max_score,
            'overall_progress': overall_progress,
            'total_checklist': total_checklist,
            'completed_checklist': completed_checklist,
            'checklist_progress': (completed_checklist / total_checklist * 100) if total_checklist > 0 else 0,
            'overdue_items': sorted(overdue_items, key=lambda x: x['days_overdue'], reverse=True),
            'upcoming_items': sorted(upcoming_items, key=lambda x: x['days_left']),
            'priority_stats': priority_stats,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _generate_ai_insights(self, stats: Dict[str, Any], root_items: List[Any]) -> Dict[str, Any]:
        """AI를 사용하여 인사이트 생성"""
        try:
            # 프로젝트 데이터를 텍스트로 변환
            project_summary = self._create_project_summary(stats, root_items)

            # AI 프롬프트 생성
            prompt = self._create_analysis_prompt(project_summary)

            # LLM 호출
            if self.llm_mode == "openai":
                insights = self._call_openai(prompt)
            elif self.llm_mode == "ollama":
                insights = self._call_ollama(prompt)
            else:
                insights = self._generate_basic_insights(stats)

            return insights

        except Exception as e:
            print(f"AI 인사이트 생성 오류: {e}")
            return self._generate_basic_insights(stats)

    def _create_project_summary(self, stats: Dict[str, Any], root_items: List[Any]) -> str:
        """프로젝트 요약 텍스트 생성"""
        summary = f"## 프로젝트 전체 통계\n\n"
        summary += f"- 전체 작업: {stats['total_items']}개\n"
        summary += f"- 완료된 작업: {stats['completed_items']}개\n"
        summary += f"- 전체 진행률: {stats['overall_progress']:.1f}%\n"
        summary += f"- 체크리스트: {stats['completed_checklist']}/{stats['total_checklist']} ({stats['checklist_progress']:.1f}%)\n\n"

        if stats['overdue_items']:
            summary += f"## 지연된 작업 ({len(stats['overdue_items'])}개)\n\n"
            for item in stats['overdue_items'][:5]:
                summary += f"- {item['title']}: {item['days_overdue']}일 지연, 진행률 {item['progress']:.1f}%\n"
            summary += "\n"

        if stats['upcoming_items']:
            summary += f"## 임박한 작업 ({len(stats['upcoming_items'])}개)\n\n"
            for item in stats['upcoming_items'][:5]:
                summary += f"- {item['title']}: {item['days_left']}일 남음, 진행률 {item['progress']:.1f}%\n"
            summary += "\n"

        # 우선순위별 통계
        summary += "## 우선순위별 현황\n\n"
        for priority, data in stats['priority_stats'].items():
            if data['total'] > 0:
                progress = (data['completed'] / data['total'] * 100)
                summary += f"- {priority}: {data['completed']}/{data['total']} ({progress:.1f}%)\n"
        summary += "\n"

        # 주요 프로젝트 목록
        summary += "## 주요 프로젝트\n\n"
        for idx, root_item in enumerate(root_items[:10], 1):
            progress = root_item.get_completion_percentage()
            summary += f"{idx}. {root_item.title}: {progress:.1f}%\n"

        return summary

    def _create_analysis_prompt(self, project_summary: str) -> str:
        """AI 분석 프롬프트 생성"""
        prompt = """당신은 프로젝트 관리 전문가입니다. 다음 프로젝트 진행 상황을 분석하고 인사이트를 제공하세요.

""" + project_summary + """

다음 형식의 JSON으로 응답하세요:

{
    "summary": "전체 프로젝트 상황을 2-3문장으로 요약",
    "strengths": ["잘 진행되고 있는 점 1", "잘 진행되고 있는 점 2"],
    "concerns": ["우려되는 점 1", "우려되는 점 2"],
    "recommendations": ["개선 제안 1", "개선 제안 2", "개선 제안 3"],
    "focus_areas": ["집중해야 할 영역 1", "집중해야 할 영역 2"]
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
                temperature=0.7,
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

    def _generate_basic_insights(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """기본 인사이트 생성 (AI 없이)"""
        insights = {
            'summary': '',
            'strengths': [],
            'concerns': [],
            'recommendations': [],
            'focus_areas': []
        }

        # 요약
        progress = stats['overall_progress']
        if progress >= 80:
            insights['summary'] = f"프로젝트가 {progress:.1f}% 진행되어 거의 완료 단계입니다."
        elif progress >= 50:
            insights['summary'] = f"프로젝트가 {progress:.1f}% 진행되어 중반을 넘어섰습니다."
        elif progress >= 20:
            insights['summary'] = f"프로젝트가 {progress:.1f}% 진행되어 초기 단계를 지나고 있습니다."
        else:
            insights['summary'] = f"프로젝트가 {progress:.1f}% 진행되어 초기 단계입니다."

        # 강점
        if stats['completed_items'] > 0:
            insights['strengths'].append(f"{stats['completed_items']}개의 작업이 완료되었습니다.")
        if stats['checklist_progress'] > 70:
            insights['strengths'].append(f"체크리스트 진행률이 {stats['checklist_progress']:.1f}%로 양호합니다.")

        # 우려사항
        if stats['overdue_items']:
            insights['concerns'].append(f"{len(stats['overdue_items'])}개의 작업이 마감일을 초과했습니다.")
        if progress < 30 and stats['upcoming_items']:
            insights['concerns'].append(f"진행률이 낮은 상태에서 {len(stats['upcoming_items'])}개의 임박한 마감이 있습니다.")

        # 우선순위별 Critical/High 체크
        critical_pending = stats['priority_stats']['Critical']['total'] - stats['priority_stats']['Critical']['completed']
        high_pending = stats['priority_stats']['High']['total'] - stats['priority_stats']['High']['completed']

        if critical_pending > 0:
            insights['concerns'].append(f"{critical_pending}개의 긴급 작업이 미완료 상태입니다.")

        # 권장사항
        if stats['overdue_items']:
            insights['recommendations'].append("지연된 작업의 우선순위를 재조정하세요.")
        if critical_pending > 0:
            insights['recommendations'].append("긴급(Critical) 작업에 먼저 집중하세요.")
        if stats['upcoming_items']:
            insights['recommendations'].append("임박한 마감일이 있는 작업을 점검하세요.")

        # 집중 영역
        if stats['overdue_items']:
            insights['focus_areas'].append("지연된 작업 복구")
        if critical_pending > 0:
            insights['focus_areas'].append("긴급 작업 완료")
        if stats['upcoming_items']:
            insights['focus_areas'].append("임박한 작업 완료")

        return insights

    def generate_report(self, root_items: List[Any]) -> str:
        """마크다운 형식의 진행 상황 보고서 생성"""
        analysis = self.analyze_progress(root_items)

        report = "# 📊 프로젝트 진행 상황 보고서\n\n"
        report += f"**분석 일시**: {analysis['analysis_date']}\n\n"

        report += "## 전체 통계\n\n"
        report += f"- **전체 작업**: {analysis['total_items']}개\n"
        report += f"- **완료된 작업**: {analysis['completed_items']}개\n"
        report += f"- **전체 진행률**: {analysis['overall_progress']:.1f}%\n"
        report += f"- **체크리스트**: {analysis['completed_checklist']}/{analysis['total_checklist']} ({analysis['checklist_progress']:.1f}%)\n\n"

        # AI 인사이트
        if 'ai_insights' in analysis:
            insights = analysis['ai_insights']

            report += "## 🤖 AI 분석 요약\n\n"
            report += f"{insights.get('summary', '')}\n\n"

            if insights.get('strengths'):
                report += "### ✅ 잘 진행되고 있는 점\n\n"
                for strength in insights['strengths']:
                    report += f"- {strength}\n"
                report += "\n"

            if insights.get('concerns'):
                report += "### ⚠️ 우려 사항\n\n"
                for concern in insights['concerns']:
                    report += f"- {concern}\n"
                report += "\n"

            if insights.get('recommendations'):
                report += "### 💡 개선 제안\n\n"
                for idx, rec in enumerate(insights['recommendations'], 1):
                    report += f"{idx}. {rec}\n"
                report += "\n"

            if insights.get('focus_areas'):
                report += "### 🎯 집중 영역\n\n"
                for area in insights['focus_areas']:
                    report += f"- {area}\n"
                report += "\n"

        # 지연 작업
        if analysis['overdue_items']:
            report += "## ⏰ 지연된 작업\n\n"
            for item in analysis['overdue_items']:
                report += f"- **{item['title']}**: {item['days_overdue']}일 지연, 진행률 {item['progress']:.1f}%\n"
            report += "\n"

        # 임박 작업
        if analysis['upcoming_items']:
            report += "## 📅 임박한 마감일\n\n"
            for item in analysis['upcoming_items']:
                report += f"- **{item['title']}**: {item['days_left']}일 남음, 진행률 {item['progress']:.1f}%\n"
            report += "\n"

        # 우선순위별 통계
        report += "## 📊 우선순위별 현황\n\n"
        for priority, data in analysis['priority_stats'].items():
            if data['total'] > 0:
                progress = (data['completed'] / data['total'] * 100)
                report += f"- **{priority}**: {data['completed']}/{data['total']} ({progress:.1f}%)\n"
        report += "\n"

        return report


def is_progress_analysis_available() -> bool:
    """진행 상황 분석 기능 사용 가능 여부"""
    return True
