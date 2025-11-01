@echo off
echo ========================================
echo   리스크 관리 시스템 (AI 스마트 분석)
echo   모드: OpenAI GPT-4
echo ========================================
echo.
echo 🤖 OpenAI GPT-4가 문서를 분석합니다.
echo ⚠️ 주의: 문서 내용이 OpenAI 서버로 전송됩니다.
echo ⚠️ API 사용료가 발생합니다 (문서당 약 $0.01-0.05)
echo.

REM API 키 확인
if "%OPENAI_API_KEY%"=="" (
    echo ❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다!
    echo.
    echo 설정 방법:
    echo 1. OpenAI 계정 생성: https://platform.openai.com
    echo 2. API 키 생성
    echo 3. 시스템 환경변수에 OPENAI_API_KEY 추가
    echo.
    echo 또는 아래에 API 키를 직접 입력하세요:
    set /p OPENAI_API_KEY="API Key (sk-...): "

    if "%OPENAI_API_KEY%"=="" (
        echo.
        echo API 키가 입력되지 않았습니다.
        echo 기본 모드로 실행하려면 Enter를 누르세요...
        pause
        call 실행.bat
        exit /b
    )
)

echo ✅ API 키 확인 완료
echo.

set LLM_MODE=openai
call venv\Scripts\activate.bat
cd src
python main.py

pause
