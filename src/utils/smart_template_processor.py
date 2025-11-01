"""
LLM을 활용한 스마트 문서 분석 및 프로젝트 구조화
문서를 분석하여 자동으로 적절한 프로젝트 구조를 생성합니다.
"""
import json
import os
from typing import Dict, Any, Optional, List

# 시스템 프롬프트
DOCUMENT_ANALYSIS_PROMPT = """당신은 문서를 분석하여 계층적 체크리스트 구조로 변환하는 전문가입니다.

## 문서 구조 파싱 규칙

문서의 개요 수준(outline level)을 정확히 파악하여 변환하세요:

**레벨 1 (문서 제목)**
- 문서 전체를 대표하는 가장 큰 제목
- 보통 맨 위에 위치하며 볼드체이거나 큰 글씨
- 예: "클라우드 마이그레이션 프로젝트 위험관리 체크리스트"
- → 루트의 title로 사용

**레벨 2 (주요 섹션)**
- "1.", "2.", "3." 같은 숫자로 시작하는 제목
- 또는 "가.", "나.", "다." 같은 한글 순서
- 예: "1. 기술 인프라 위험", "2. 보안 및 컴플라이언스 위험"
- → children 배열에 하위 토글로 추가
- ⚠️ 번호는 제거하지 말고 그대로 유지!

**레벨 3 (체크리스트 항목)**
- "•", "-", "○", "▪" 같은 기호로 시작
- 또는 "1)", "가)", "(1)" 같은 소번호
- 예: "• 클라우드 서비스 호환성 검증 완료"
- → 해당 섹션의 checklist 배열에 추가
- ⚠️ 기호(•, -)는 제거하고 텍스트만 사용

**레벨 4+ (상세 설명)**
- 번호나 기호 없는 일반 문장
- → 무시하거나 해당 섹션의 content에 간략히 요약

## 출력 JSON 구조 (정확히 이 형식을 따르세요!)

{
  "title": "클라우드 마이그레이션 프로젝트 위험관리 체크리스트",
  "content": "",
  "checklist": [],
  "children": [
    {
      "title": "1. 기술 인프라 위험",
      "content": "",
      "checklist": [
        {"text": "클라우드 서비스 호환성 검증 완료", "is_checked": false, "score": 10},
        {"text": "네트워크 대역폭 충분성 확인", "is_checked": false, "score": 8},
        {"text": "데이터 마이그레이션 전략 수립", "is_checked": false, "score": 12},
        {"text": "레거시 시스템 연동 테스트 완료", "is_checked": false, "score": 10},
        {"text": "재해복구(DR) 계획 수립", "is_checked": false, "score": 15}
      ],
      "children": []
    },
    {
      "title": "2. 보안 및 컴플라이언스 위험",
      "content": "",
      "checklist": [
        {"text": "데이터 암호화 정책 수립", "is_checked": false, "score": 12},
        {"text": "접근 권한 관리 체계 구축", "is_checked": false, "score": 10},
        {"text": "규제 준수 요구사항 검토 (GDPR, 개인정보보호법 등)", "is_checked": false, "score": 15},
        {"text": "보안 감사 및 취약점 스캔 실시", "is_checked": false, "score": 12},
        {"text": "백업 및 복구 절차 테스트", "is_checked": false, "score": 10}
      ],
      "children": []
    }
  ]
}

## 필드별 상세 규칙

**title (제목)**
- 레벨 1: 문서 제목 그대로
- 레벨 2: 섹션 제목, 번호 포함 ("1. 기술 인프라 위험" ← "1." 유지!)
- 최대 100자

**content (내용)**
- 기본값: 빈 문자열 ""
- 설명문이 있을 때만 1줄 요약 (선택)
- 대부분의 경우 ""로 비워두세요

**checklist (체크리스트 배열)**
- text: 항목 텍스트 (•, - 제거)
- is_checked: 항상 false
- score: 5~20 사이의 정수 (항목 중요도/난이도)

**children (하위 토글 배열)**
- 레벨 1: children에 레벨 2 섹션들 포함
- 레벨 2: children은 빈 배열 []

**score 할당 기준**
- 5-8: 간단한 확인, 문서 읽기
- 9-12: 일반 작업, 검토
- 13-17: 중요 작업, 승인 필요
- 18-20: 핵심 작업, 프로젝트 성패 결정

## 금지사항
- ❌ 문서에 없는 내용 추가 금지
- ❌ 항목 임의로 합치거나 분리 금지
- ❌ content에 긴 원문 복사 금지
- ❌ 섹션 번호 제거 금지 (1., 2. 유지)
- ❌ 이상한 문자/반복 텍스트 포함 금지

## 최종 체크리스트
- [ ] 레벨 1 제목을 루트 title로 설정
- [ ] 레벨 2 섹션을 children에 토글로 추가
- [ ] 레벨 3 항목을 checklist에 추가
- [ ] 모든 content는 ""
- [ ] score는 5~20
- [ ] JSON만 출력, 설명 없음

위 규칙을 정확히 따라 주어진 문서를 JSON으로 변환하세요."""


class SmartTemplateProcessor:
    """LLM을 활용한 스마트 문서 분석 및 템플릿 적용"""

    def __init__(self, llm_mode: str = "none"):
        """
        Args:
            llm_mode: LLM 사용 모드
                     "none" - LLM 사용 안 함 (기본 템플릿)
                     "ollama" - 로컬 Ollama 사용 (안전, 무료)
                     "openai" - OpenAI API 사용 (정확하지만 비용 발생)
        """
        self.llm_mode = llm_mode.lower()
        self.llm_client = None

        if self.llm_mode == "ollama":
            self._init_ollama()
        elif self.llm_mode == "openai":
            self._init_openai()

    def _init_ollama(self):
        """Ollama 초기화"""
        try:
            import requests
            # Ollama 서버 확인
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                self.llm_client = "ollama"
                print("✅ 로컬 LLM(Ollama) 스마트 분석 모드 활성화")
                print("   데이터가 외부로 전송되지 않습니다!")
            else:
                print("⚠️ Ollama 서버에 연결할 수 없습니다.")
                self.llm_mode = "none"
        except Exception as e:
            print(f"⚠️ Ollama 초기화 실패: {e}")
            print("   기본 템플릿 모드로 전환합니다.")
            self.llm_mode = "none"

    def _init_openai(self):
        """OpenAI 초기화"""
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.llm_client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI 스마트 분석 모드 활성화")
                print("⚠️ 주의: 문서 내용이 OpenAI 서버로 전송됩니다.")
            else:
                print("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
                self.llm_mode = "none"
        except ImportError:
            print("⚠️ openai 라이브러리를 설치해주세요: pip install openai")
            self.llm_mode = "none"

    def analyze_document(self, filename: str, content: str) -> Optional[Dict[str, Any]]:
        """
        문서를 분석하여 프로젝트 구조 생성

        Args:
            filename: 파일명
            content: 문서 내용

        Returns:
            Dict: 토글 구조 데이터
        """
        if self.llm_mode == "none" or not self.llm_client:
            return None

        try:
            # 문서 내용이 너무 길면 요약
            max_length = 600  # 600자로 대폭 축소
            if len(content) > max_length:
                content = content[:max_length] + "\n... (생략)"

            user_prompt = f"""파일: {filename}

내용:
{content}"""

            if self.llm_mode == "ollama":
                return self._analyze_with_ollama(user_prompt)
            elif self.llm_mode == "openai":
                return self._analyze_with_openai(user_prompt)

        except Exception as e:
            print(f"❌ LLM 분석 오류: {e}")
            return None

    def _analyze_with_ollama(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Ollama로 문서 분석"""
        try:
            import requests

            print("📄 OLLAMA LLM으로 문서 구조 분석 중...")

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": f"{DOCUMENT_ANALYSIS_PROMPT}\n\n{user_prompt}",
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 512,  # 512로 축소
                        "num_ctx": 1024  # 컨텍스트도 축소
                    }
                },
                timeout=90  # 90초로 축소
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")

                # JSON 파싱
                try:
                    data = json.loads(response_text)
                    print("✅ LLM 분석 완료")
                    return data
                except json.JSONDecodeError as e:
                    print(f"⚠️ LLM 응답을 JSON으로 파싱할 수 없습니다.")
                    print(f"   응답 내용: {response_text[:200]}...")
                    return None
            else:
                print(f"⚠️ Ollama 요청 실패: {response.status_code}")
                return None

        except Exception as e:
            print(f"⚠️ Ollama 분석 오류: {e}")
            return None

    def _analyze_with_openai(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """OpenAI로 문서 분석"""
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",  # 또는 gpt-4
                messages=[
                    {"role": "system", "content": DOCUMENT_ANALYSIS_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )

            response_text = response.choices[0].message.content

            # JSON 파싱
            try:
                data = json.loads(response_text)
                return data
            except json.JSONDecodeError:
                print("⚠️ OpenAI 응답을 JSON으로 파싱할 수 없습니다.")
                return None

        except Exception as e:
            print(f"⚠️ OpenAI 분석 오류: {e}")
            return None


def is_smart_analysis_available(llm_mode: str = "none") -> bool:
    """스마트 분석 기능이 사용 가능한지 확인"""
    if llm_mode == "none":
        return False
    elif llm_mode == "ollama":
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    elif llm_mode == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    return False
