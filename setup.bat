@echo off
echo 위험관리시스템 설치를 시작합니다...

REM 가상환경 생성
python -m venv venv
echo 가상환경이 생성되었습니다.

REM 가상환경 활성화 및 패키지 설치
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo 필요한 패키지가 설치되었습니다.

echo.
echo 설치가 완료되었습니다!
echo 프로그램을 실행하려면 실행.bat 파일을 더블클릭하세요.
pause