import streamlit as st
import os
from .config import plugin_categories, pid_plugin_categories
from .components import show_analysis_result
from .async_components import show_realtime_results
from common.volatility import run_pid_plugin
from common.async_manager import analysis_manager


def show_tab_content(plugin_name: str, dump_path: str, label: str, category: str):
    """개별 플러그인 탭 내용 표시 (분석 결과만)"""
    result_key = f"analysis_results_{category}_{plugin_name}"

    if result_key in st.session_state:
        df, error = st.session_state[result_key]
        show_analysis_result(df, error, label, plugin_name, category)
    else:
        st.info("🔄 분석 시작 버튼을 클릭하여 분석을 진행하세요.")


def show_plugin_tabs(dump_path: str, selected_category: str):
    """선택된 카테고리의 플러그인 탭들을 표시"""
    plugins = plugin_categories[selected_category]

    # 비동기 분석이 실행 중인지 확인
    is_async_running = analysis_manager.is_running(selected_category)

    if is_async_running:
        st.info("🔄 **비동기 분석 실행 중** - 결과가 실시간으로 업데이트됩니다.")

        # 실시간 결과 표시
        show_realtime_results(selected_category)

        st.markdown("---")
        st.subheader("📋 상세 결과")

    # 탭 생성
    plugin_tabs = st.tabs([f"{emoji} {title}" for emoji, title, _ in plugins])

    # 각 탭에 내용 표시
    for (emoji, title, plugin), tab in zip(plugins, plugin_tabs):
        with tab:
            show_tab_content(plugin, dump_path, title, selected_category)


def show_pid_analysis(dump_path: str):
    """PID 기반 상세 분석"""
    st.markdown("---")
    st.header("🔍 PID 기반 상세 분석")
    st.info("🎯 **특정 프로세스에 대한 심화 분석을 수행합니다.** 의심스러운 프로세스의 PID를 입력하여 상세 분석을 진행하세요.")

    with st.form("pid_analysis_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            pid = st.text_input("🎯 분석할 PID 입력", placeholder="예: 1234")
        with col2:
            st.write("")  # 공간 조정
            analyze = st.form_submit_button("🔍 분석 시작", use_container_width=True)

    if not dump_path:
        st.warning("🔁 먼저 상단에서 유효한 메모리 덤프 경로를 적용해주세요.")
        return

    if not analyze:
        st.markdown("💡 **사용법:** 위의 '프로세스 분석' 탭에서 의심스러운 프로세스의 PID를 확인한 후, 여기에 입력하여 상세 분석을 진행하세요.")
        return

    if not pid.isdigit():
        st.warning("⚠️ PID는 숫자로만 입력해주세요.")
        return

    # JSON에서 로드한 PID 분석 전용 플러그인들 사용
    if not pid_plugin_categories:
        st.error("❌ PID 플러그인 설정을 로드할 수 없습니다.")
        return

    st.success(f"🎯 PID {pid}에 대한 상세 분석을 시작합니다.")
    tab_titles = [f"{emoji} {title}" for emoji, title, _ in pid_plugin_categories]
    tabs = st.tabs(tab_titles)

    for (tab, (emoji, label, plugin_name)) in zip(tabs, pid_plugin_categories):
        with tab:
            with st.spinner(f"{label} 실행 중..."):
                try:
                    mtime = os.path.getmtime(dump_path)
                    df = run_pid_plugin(plugin_name, dump_path, pid, _mtime=mtime)
                    show_analysis_result(df, None, label, plugin_name, pid=pid)
                except Exception as e:
                    show_analysis_result(None, str(e), label, plugin_name, pid=pid)


def show_main_content(dump_path: str, analysis_mode: str, selected_category: str):
    """메인 컨텐츠 표시"""
    if analysis_mode == "🔍 일반 분석":
        current_category = selected_category
        st.info(f"**{current_category}**   `{dump_path}`")
        # 플러그인 탭들 표시
        show_plugin_tabs(dump_path, current_category)
    elif analysis_mode == "🎯 PID 분석":
        st.info(f"**현재 분석 대상:** `{dump_path}`")
        show_pid_analysis(dump_path)