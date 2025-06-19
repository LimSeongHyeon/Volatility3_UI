# 🔬 Volatility3 Web UI

Windows 10/11 메모리 포렌식을 위한 Volatility3 웹 기반 사용자 인터페이스

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Volatility](https://img.shields.io/badge/Volatility-3.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 주요 기능

### 🚀 **비동기 분석**
- 실시간 진행 상황 모니터링
- UI 블로킹 없는 백그라운드 실행
- 여러 카테고리 동시 분석 지원
- 분석 중단 및 재시작 기능

### 📊 **카테고리별 분석**
- **🔍 시스템 정보**: 이미지 정보, 실행 기록, 레지스트리
- **💻 프로세스 분석**: 프로세스 목록, 실행 트리, 서비스
- **🌐 네트워크 분석**: 네트워크 연결, 통계
- **🎯 악성코드 분석**: 메모리 패치, 숨김 프로세스, YARA 스캔
- **🔧 고급 분석**: 파일 스캔, 타임라인 분석

### 🎯 **PID 기반 상세 분석**
- 특정 프로세스 집중 분석
- DLL 목록, 메모리 맵, 파일 덤프
- 프로세스별 YARA 스캔

### 💾 **데이터 관리**
- CSV 형태로 결과 다운로드
- 로컬 파일 자동 저장
- 파일 덤프 자동 정리 기능

## 📋 요구사항

### **필수 소프트웨어**
- Python 3.8 이상
- [Volatility3](https://github.com/volatilityfoundation/volatility3)
- Windows 10/11 (분석 대상)

### **Python 패키지**
```bash
pip install -r requirements.txt
```

## 🛠️ 설치 및 설정

### **1. 프로젝트 클론**
```bash
git clone https://github.com/your-repo/volatility3-web-ui.git
cd volatility3-web-ui
```

### **2. 가상환경 생성 (권장)**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### **3. 패키지 설치**
```bash
pip install -r requirements.txt
```

### **4. 환경 설정**
`.env` 파일을 편집하여 환경을 설정하세요:

```env
# Volatility3 설정
VOL_PATH=C:\tools\volatility3\vol.py
DEFAULT_CORES=4
OUTPUT_PATH=C:\forensics\results

# 인코딩 문제 해결을 위한 환경변수
PYTHONIOENCODING=utf-8
LANG=en_US.UTF-8
```

### **5. 플러그인 설정 (선택사항)**
`res/plugin_categories.json`과 `res/pid_plugin_categories.json` 파일을 편집하여 사용할 플러그인을 커스터마이징할 수 있습니다.

## 🚀 실행 방법

### **기본 실행**
```bash
streamlit run main.py
```

### **인코딩 문제 해결을 위한 실행 (Windows)**
```batch
# 배치 파일 사용
fix_encoding.bat

# 또는 수동 설정
set PYTHONIOENCODING=utf-8
set LANG=en_US.UTF-8
chcp 65001
streamlit run main.py
```

### **브라우저 접속**
실행 후 브라우저에서 `http://localhost:8501`로 접속하세요.

## 📁 프로젝트 구조

```
📦 Volatility3_UI
├── 📄 main.py                          # 메인 실행 파일
├── 📄 .env                             # 환경 설정
├── 📄 requirements.txt                 # 패키지 의존성
├── 📄 fix_encoding.bat                 # 인코딩 문제 해결 스크립트
├── 📂 res/                             # 설정 파일
│   ├── 📄 plugin_categories.json       # 일반 분석 플러그인 설정
│   └── 📄 pid_plugin_categories.json   # PID 분석 플러그인 설정
├── 📂 common/                          # 공용 로직
│   ├── 📄 __init__.py
│   ├── 📄 volatility.py               # Volatility 실행 관련
│   ├── 📄 async_manager.py             # 비동기 분석 관리
│   └── 📄 utils.py                     # 유틸리티 함수
└── 📂 UI/                              # 사용자 인터페이스
    ├── 📄 __init__.py
    ├── 📄 config.py                    # 설정 관리
    ├── 📄 navbar.py                    # 사이드바 UI
    ├── 📄 mainSection.py               # 메인 UI
    ├── 📄 components.py                # UI 컴포넌트
    ├── 📄 async_components.py          # 비동기 UI 컴포넌트
    └── 📄 explain.py                   # 웰컴 페이지
```

## 🎯 사용법

### **1. 기본 분석 워크플로우**

1. **파일 설정**: 사이드바에서 메모리 덤프 파일 경로 입력
2. **분석 모드 선택**: 일반 분석 또는 PID 분석 선택
3. **카테고리 선택**: 원하는 분석 카테고리 선택
4. **분석 실행**: 비동기 분석 시작
5. **결과 확인**: 실시간으로 업데이트되는 결과 확인

### **2. PID 기반 분석**

```
💻 프로세스 분석 → 📋 프로세스 목록 → 의심 PID 확인
                ↓
🎯 PID 분석 → PID 입력 → 상세 분석 실행
```

### **3. 고급 기능**

- **여러 카테고리 동시 분석**: 사이드바에서 진행 상황 모니터링
- **파일 덤프 관리**: 자동 정리 기능으로 디스크 공간 절약
- **결과 내보내기**: CSV 다운로드 및 로컬 저장

## ⚙️ 설정 가이드

### **플러그인 추가**
`res/plugin_categories.json`:
```json
{
  "🔍 새 카테고리": [
    {
      "emoji": "🆕", 
      "label": "새 플러그인", 
      "command": "windows.newplugin"
    }
  ]
}
```

### **PID 플러그인 추가**
`res/pid_plugin_categories.json`:
```json
{
  "pid_plugins": [
    {
      "emoji": "🔍", 
      "label": "핸들 분석", 
      "command": "windows.handles"
    }
  ]
}
```

## 🐛 문제 해결

### **인코딩 오류 (UnicodeEncodeError)**
```bash
# 해결방법 1: 배치 파일 사용
fix_encoding.bat

# 해결방법 2: 환경변수 설정
set PYTHONIOENCODING=utf-8
set LANG=en_US.UTF-8
```

### **Volatility 경로 오류**
`.env` 파일에서 `VOL_PATH`를 정확한 경로로 설정:
```env
VOL_PATH=C:\tools\volatility3\vol.py
```

### **메모리 부족 오류**
`.env` 파일에서 사용할 코어 수를 줄이세요:
```env
DEFAULT_CORES=1
```

## 🔧 개발자 가이드

### **새 기능 추가**
1. `common/` 폴더에 비즈니스 로직 추가
2. `UI/` 폴더에 사용자 인터페이스 추가
3. 필요시 `res/` 폴더에 설정 파일 수정

### **코드 구조**
- **관심사 분리**: UI와 로직 완전 분리
- **모듈화**: 기능별 독립적인 모듈 구성
- **설정 관리**: JSON 기반 동적 설정

### **테스트**
```bash
# 기본 기능 테스트
python -m pytest tests/

# UI 테스트
streamlit run main.py --server.headless true
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🤝 기여하기

1. 이 저장소를 포크하세요
2. 새 기능 브랜치를 만드세요 (`git checkout -b feature/AmazingFeature`)
3. 변경사항을 커밋하세요 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시하세요 (`git push origin feature/AmazingFeature`)
5. Pull Request를 생성하세요

## 📞 지원 및 문의

- 버그 리포트: [Issues](https://github.com/your-repo/volatility3-web-ui/issues)
- 기능 요청: [Discussions](https://github.com/your-repo/volatility3-web-ui/discussions)
- 이메일: me@limseonghyeon.com

## 🙏 감사의 말

- [Volatility Foundation](https://www.volatilityfoundation.org/) - 훌륭한 메모리 포렌식 도구
- [Streamlit](https://streamlit.io/) - 빠른 웹 앱 개발 프레임워크
- 메모리 포렌식 커뮤니티의 모든 기여자들

---

⭐ **이 프로젝트가 도움이 되었다면 스타를 눌러주세요!**
