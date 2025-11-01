#!/bin/bash

# 맥용 실행 스크립트
echo "위험관리시스템을 시작합니다..."

# Python 및 필요한 패키지 확인
if ! command -v python3 &> /dev/null; then
    echo "Python3가 설치되어 있지 않습니다. https://python.org에서 설치해주세요."
    exit 1
fi

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
pip3 install PyQt5==5.15.10 openpyxl==3.1.2

# 프로그램 실행
echo "프로그램을 시작합니다..."
cd "$(dirname "$0")"
python3 src/main.py