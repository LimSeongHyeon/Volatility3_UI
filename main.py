import streamlit as st
import os
from UI.navbar import setup_sidebar
from UI.mainSection import show_main_content
from UI.explain import show_welcome_page

def main():
    st.set_page_config(page_title="Volatility Web UI", layout="wide")

    # 분석 상태 초기화
    if "analysis_running" not in st.session_state:
        st.session_state["analysis_running"] = False

    # 사이드바 설정
    dump_path, analysis_mode, selected_category = setup_sidebar()

    # 메인 타이틀
    st.title("🔬 Volatility3 UI for Windows 10/11")

    # 메인 컨텐츠 표시
    if dump_path and analysis_mode in ["🔍 일반 분석", "🎯 PID 분석"]:
        show_main_content(dump_path, analysis_mode, selected_category)
    else:
        show_welcome_page()

if __name__ == "__main__":
    main()