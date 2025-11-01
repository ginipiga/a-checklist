# 위험관리시스템 - Mac 사용 가이드

## 설치 및 실행 방법

### 방법 1: 자동 스크립트 사용
1. 터미널을 열고 프로그램 폴더로 이동
2. 실행 권한 부여: `chmod +x run_mac.sh`
3. 실행: `./run_mac.sh`

### 방법 2: 수동 설치
```bash
# 1. Python 설치 확인
python3 --version

# 2. 필요한 라이브러리 설치
pip3 install PyQt5==5.15.10 openpyxl==3.1.2

# 3. 프로그램 실행
python3 src/main.py
```

### 방법 3: Mac용 실행파일 만들기
```bash
# PyInstaller 설치
pip3 install pyinstaller

# Mac용 실행파일 생성
pyinstaller --onefile --windowed --name "위험관리시스템" src/main.py

# dist/위험관리시스템 파일 실행
./dist/위험관리시스템
```

## 문제 해결

### PyQt5 설치 오류시
```bash
# Homebrew로 PyQt5 설치
brew install pyqt5
```

### M1 Mac의 경우
```bash
# Rosetta 모드에서 실행 (필요시)
arch -x86_64 pip3 install PyQt5==5.15.10 openpyxl==3.1.2
```

## 주의사항
- macOS 버전에 따라 추가 권한 설정이 필요할 수 있습니다
- 보안 설정에서 "개발자를 확인할 수 없음" 경고가 나타날 수 있습니다