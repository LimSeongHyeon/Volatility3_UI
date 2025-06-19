@echo off
REM Volatility3 인코딩 문제 해결을 위한 배치 파일

echo "=== Volatility3 인코딩 환경 설정 ==="

REM UTF-8 인코딩 설정
set PYTHONIOENCODING=utf-8
set LANG=en_US.UTF-8
set LC_ALL=en_US.UTF-8

REM 콘솔 코드페이지를 UTF-8로 변경
chcp 65001

echo "환경변수가 설정되었습니다:"
echo "PYTHONIOENCODING=%PYTHONIOENCODING%"
echo "LANG=%LANG%"
echo "LC_ALL=%LC_ALL%"

echo "이제 Streamlit 앱을 실행합니다..."
streamlit run main.py

pause