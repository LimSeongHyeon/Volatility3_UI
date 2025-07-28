import streamlit as st
from pathlib import Path

def load_welcome_message():
    """웰컴 메시지 Markdown 파일 로드"""
    try:
        # 현재 파일의 위치를 기준으로 Markdown 파일 경로 설정
        current_dir = Path(__file__).parent
        md_path = current_dir.parent / "resources" / "welcome_message.md"

        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
## ❌ 웰컴 메시지 파일을 찾을 수 없습니다

`resources/welcome_message.md` 파일이 존재하지 않습니다.

### 기본 사용법
1. 좌측 사이드바에서 메모리 덤프 파일 경로를 설정하세요
2. 분석 모드를 선택하세요
3. 분석을 시작하세요
        """
    except Exception as e:
        return f"""
## ❌ 웰컴 메시지 로드 중 오류 발생

오류 내용: {str(e)}

기본 사용법을 위해 사이드바를 확인하세요.
        """


def show_welcome_page():
    """웰컴 페이지 표시"""
    welcome_content = load_welcome_message()
    st.markdown(welcome_content)