@echo off
chcp 65001 >nul
echo ============================================
echo    위험관리시스템 (로컬 AI 모드)
echo ============================================
echo.
echo ✅ 로컬 AI (Ollama) 활성화
echo    - 모델: qwen2.5:7b
echo    - 데이터 유출 걱정 없음
echo    - 완전 무료
echo    - 오프라인 작동
echo.

REM 로컬 LLM 모드 설정
set LLM_MODE=ollama

REM 프로그램 실행
echo 프로그램 시작 중...
echo.

.\venv\Scripts\python.exe src\main.py

if errorlevel 1 (
    echo.
    echo ⚠️  프로그램 실행 중 오류 발생
    echo.
    pause
)
