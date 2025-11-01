@echo off
echo ========================================
echo   리스크 관리 시스템 (AI 스마트 분석)
echo   모드: Ollama (로컬, 무료, 안전)
echo ========================================
echo.
echo 🤖 AI가 문서를 분석하여 맞춤형 프로젝트 구조를 생성합니다.
echo ✅ 데이터가 외부로 전송되지 않습니다.
echo.

REM Ollama 실행 여부 확인
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️ Ollama가 실행되지 않았습니다!
    echo.
    echo Ollama 설치: https://ollama.com
    echo 모델 다운로드: ollama pull llama3.2:latest
    echo.
    echo 기본 모드로 실행하려면 Enter를 누르세요...
    pause
    call 실행.bat
    exit /b
)

echo ✅ Ollama 연결 확인 완료
echo.

set LLM_MODE=ollama
call venv\Scripts\activate.bat
cd src
python main.py

pause
