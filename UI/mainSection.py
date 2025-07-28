import streamlit as st
from UI.config import plugin_categories, pid_plugin_categories
from UI.components import show_analysis_result, show_analysis_hints
from common.async_manager import analysis_manager


def show_plugin_tabs(dump_path: str, selected_category: str):
    """선택된 카테고리의 플러그인 탭들을 표시"""
    if selected_category not in plugin_categories:
        st.error("❌ 선택된 카테고리를 찾을 수 없습니다.")
        return

    plugins = plugin_categories[selected_category]

    # 비동기 분석이 실행 중인지 확인
    is_async_running = analysis_manager.is_running(selected_category)

    if not is_async_running and not st.session_state.get("analysis_running", False):
        # 분석 시작 버튼
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**{selected_category}** 카테고리의 모든 플러그인을 실행합니다.")
        with col2:
            max_workers = st.session_state.get("max_workers", 1)
            if st.button("🚀 카테고리 분석 시작", type="primary", use_container_width=True):
                if dump_path:
                    print(f"DEBUG: Starting analysis for {selected_category}")
                    # 비동기 분석 시작
                    success = analysis_manager.start_category_analysis_async(dump_path, selected_category, max_workers)
                    print(f"DEBUG: Analysis start result: {success}")
                    if success:
                        st.session_state["analysis_running"] = True
                        print(f"DEBUG: Set analysis_running = True")
                        st.success("🔄 백그라운드에서 분석을 시작했습니다!")
                        st.rerun()
                    else:
                        st.warning("⚠️ 분석을 시작할 수 없습니다. 시스템 상태를 확인하세요.")
                else:
                    st.error("❌ 먼저 메모리 덤프 파일을 설정하세요")

    st.divider()

    # 개별 플러그인 탭 생성
    tab_names = []
    for plugin_data in plugins:
        if isinstance(plugin_data, dict):
            tab_names.append(f"{plugin_data['emoji']} {plugin_data['label']}")
        else:
            emoji, title, _ = plugin_data
            tab_names.append(f"{emoji} {title}")

    tabs = st.tabs(tab_names)

    for i, (plugin_data, tab) in enumerate(zip(plugins, tabs)):
        with tab:
            show_individual_plugin_tab(dump_path, plugin_data, selected_category)


def show_individual_plugin_tab(dump_path: str, plugin_data: dict, category: str):
    """개별 플러그인 탭 내용"""
    # 플러그인 데이터 구조 처리
    if isinstance(plugin_data, dict):
        plugin_name = plugin_data['command']
        label = plugin_data['label']
    else:
        # 튜플 구조 (하위 호환성)
        emoji, label, plugin_name = plugin_data

    # 분석 힌트 표시
    show_analysis_hints(label)

    # 결과 표시
    result_key = f"analysis_results_{category}_{plugin_name}"
    if result_key in st.session_state:
        df, error = st.session_state[result_key]

        if error:
            st.error(f"❌ {label} 분석 실패")
            # 캐시된 오류인지 확인
            if "[CACHED]" in error:
                st.info("🗄️ 이 오류는 캐시된 결과입니다.")
                st.code(error.replace("[CACHED] ", ""))
            else:
                st.code(error)
        elif df is not None:
            st.success(f"✅ {label} 완료: {len(df)}개 항목")
            st.dataframe(df, height=400)

            # CSV 다운로드 버튼
            from datetime import datetime
            csv_data = df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{plugin_name}_{timestamp}.csv"

            st.download_button(
                label="💾 CSV 다운로드",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                key=f"download_{category}_{plugin_name}"
            )
        else:
            st.info("🔄 분석 결과를 기다리는 중...")
    else:
        st.info("🔄 카테고리 분석을 시작하여 결과를 확인하세요.")


def show_pid_analysis(dump_path: str):
    """PID 기반 분석"""
    st.header("🎯 PID 기반 상세 분석")
    st.info("특정 프로세스에 대한 심화 분석을 수행합니다.")

    # 분석 실행 상태 확인
    analysis_running = st.session_state.get("analysis_running", False)

    # PID 입력
    col1, col2 = st.columns([3, 1])
    with col1:
        pid = st.text_input(
            "🎯 분석할 PID 입력",
            placeholder="예: 1234",
            disabled=analysis_running
        )
    with col2:
        st.write("")  # 공간 조정
        analyze_pid = st.button(
            "🔍 PID 분석 시작",
            use_container_width=True,
            type="primary",
            disabled=analysis_running
        )

    if analysis_running:
        return

    if not analyze_pid:
        st.markdown("💡 **사용법:** 먼저 일반 분석에서 프로세스 목록을 확인한 후, 의심스러운 프로세스의 PID를 입력하세요.")
        return

    if not dump_path:
        st.error("❌ 먼저 메모리 덤프 파일을 설정하세요")
        return

    if not pid or not pid.isdigit():
        st.error("❌ 유효한 PID를 입력하세요")
        return

    # PID 플러그인 탭 생성
    if not pid_plugin_categories:
        st.error("❌ PID 플러그인 설정을 로드할 수 없습니다")
        return

    st.success(f"🎯 PID {pid}에 대한 상세 분석을 시작합니다.")

    # PID 플러그인 탭들
    tab_names = []
    for plugin_data in pid_plugin_categories:
        if isinstance(plugin_data, dict):
            tab_names.append(f"{plugin_data['emoji']} {plugin_data['label']}")
        else:
            emoji, title, _ = plugin_data
            tab_names.append(f"{emoji} {title}")

    tabs = st.tabs(tab_names)

    for plugin_data, tab in zip(pid_plugin_categories, tabs):
        with tab:
            show_pid_plugin_tab(dump_path, plugin_data, pid)


def show_pid_plugin_tab(dump_path: str, plugin_data: dict, pid: str):
    """PID 플러그인 탭 내용"""
    # 플러그인 데이터 구조 처리
    if isinstance(plugin_data, dict):
        plugin_name = plugin_data['command']
        label = plugin_data['label']
    else:
        # 튜플 구조 (하위 호환성)
        emoji, label, plugin_name = plugin_data

    # 분석 힌트
    show_analysis_hints(label)

    # 분석 버튼
    if st.button(f"🔍 {label} 분석 (PID {pid})", key=f"pid_{pid}_{plugin_name}"):
        run_pid_analysis(dump_path, plugin_name, label, pid)

    # 결과 표시
    result_key = f"result_pid_{pid}_{plugin_name}"
    if result_key in st.session_state:
        df, error = st.session_state[result_key]

        if error:
            st.error(f"❌ PID {pid} {label} 분석 실패")
            st.code(error)
        elif df is not None:
            st.success(f"✅ PID {pid} {label} 완료: {len(df)}개 항목")
            st.dataframe(df, height=400)

            # CSV 다운로드 버튼
            from datetime import datetime
            csv_data = df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PID_{pid}_{plugin_name}_{timestamp}.csv"

            st.download_button(
                label="💾 CSV 다운로드",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                key=f"download_pid_{pid}_{plugin_name}"
            )


def run_pid_analysis(dump_path: str, command: str, label: str, pid: str):
    """PID 분석 실행 (기존 volatility.py 함수 사용)"""
    result_key = f"result_pid_{pid}_{command}"

    with st.spinner(f"PID {pid} {label} 분석 중..."):
        try:
            from common.volatility import run_pid_plugin
            import os

            # 파일 수정 시간을 캐시 키로 사용
            mtime = os.path.getmtime(dump_path)
            df = run_pid_plugin(command, dump_path, pid, _mtime=mtime)

            st.session_state[result_key] = (df, None)
            st.rerun()

        except Exception as e:
            st.session_state[result_key] = (None, str(e))
            st.rerun()


def show_main_content(dump_path: str, analysis_mode: str, selected_category: str):
    """메인 컨텐츠 표시"""
    if analysis_mode == "🔍 일반 분석":
        if selected_category:
            show_plugin_tabs(dump_path, selected_category)
        else:
            st.info("사이드바에서 분석 카테고리를 선택하세요.")

    elif analysis_mode == "🎯 PID 분석":
        show_pid_analysis(dump_path)