@echo off
chcp 65001 >nul
echo ========================================
echo 건설 시방서 분석 시스템 (Ollama AI)
echo ========================================
echo.
echo Ollama를 사용하여 AI 기능을 활성화합니다.
echo - 로컬에서 실행되어 비용이 들지 않습니다
echo - 인터넷 연결 없이도 작동합니다
echo.

set LLM_MODE=ollama
set OLLAMA_MODEL=qwen2.5:7b

echo 환경 설정:
echo - LLM 모드: %LLM_MODE%
echo - 모델: %OLLAMA_MODEL%
echo.
echo 프로그램을 시작합니다...
echo.

python src\main.py

pause
