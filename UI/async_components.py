import streamlit as st
import time
from common.async_manager import analysis_manager


def show_async_progress(category: str):
    """비동기 분석 진행 상황 표시"""
    progress_data = analysis_manager.get_progress(category)

    if not progress_data:
        return False

    total = progress_data.get('total', 0)
    completed = progress_data.get('completed', 0)
    current_plugin = progress_data.get('current_plugin', '')
    status = progress_data.get('status', 'idle')

    if status == 'running':
        # 진행률 표시
        progress_value = completed / total if total > 0 else 0

        # 실시간 업데이트를 위한 컨테이너
        progress_container = st.empty()
        status_container = st.empty()

        with progress_container.container():
            st.progress(progress_value, text=f"분석 진행: {completed}/{total}")

        with status_container.container():
            if current_plugin:
                st.info(f"🔄 현재 실행 중: {current_plugin}")

            # 완료된 플러그인 목록
            if completed > 0:
                last_completed = progress_data.get('last_completed', '')
                if last_completed:
                    st.success(f"✅ 최근 완료: {last_completed}")

        # 중단 버튼
        if st.button("⏹️ 분석 중단", key=f"stop_{category}"):
            analysis_manager.stop_analysis(category)
            st.warning("⚠️ 분석이 중단되었습니다.")
            st.rerun()

        # 자동 새로고침을 위한 재실행
        if completed < total:
            time.sleep(1)
            st.rerun()

        return True

    elif status == 'completed':
        st.success(f"🎉 {category} 분석이 완료되었습니다!")
        return False

    elif status == 'error':
        error_msg = progress_data.get('error', '알 수 없는 오류')
        st.error(f"❌ 분석 중 오류 발생: {error_msg}")
        return False

    elif status == 'stopped':
        st.warning("⚠️ 분석이 사용자에 의해 중단되었습니다.")
        return False

    return False


def show_async_analysis_controls(dump_path: str, selected_category: str, max_workers: int):
    """비동기 분석 제어 UI"""
    is_running = analysis_manager.is_running(selected_category)

    if is_running:
        # 진행 상황 표시
        if show_async_progress(selected_category):
            return True  # 아직 실행 중
    else:
        # 분석 시작 버튼
        if st.button("🚀 비동기 분석 시작", use_container_width=True, type="primary"):
            if analysis_manager.start_category_analysis_async(dump_path, selected_category, max_workers):
                st.session_state["analysis_running"] = True
                st.success("🔄 백그라운드에서 분석을 시작했습니다!")
                st.rerun()
            else:
                st.warning("⚠️ 해당 카테고리의 분석이 이미 실행 중입니다.")

    return False


def show_realtime_results(category: str):
    """실시간 결과 업데이트 표시"""
    progress_data = analysis_manager.get_progress(category)

    if not progress_data:
        return

    completed = progress_data.get('completed', 0)

    if completed > 0:
        st.subheader(f"📊 실시간 결과 ({completed}개 완료)")

        # 완료된 결과들을 실시간으로 표시
        for key in st.session_state.keys():
            if key.startswith(f"analysis_results_{category}_"):
                plugin_name = key.split('_')[-1]
                df, error = st.session_state[key]

                with st.expander(f"📋 {plugin_name} 결과", expanded=False):
                    if error:
                        st.error(f"❌ 오류: {error}")
                    elif df is not None:
                        st.success(f"✅ {len(df)}개 항목 발견")
                        st.dataframe(df.head(10))  # 상위 10개만 미리보기

                        if st.button(f"전체 결과 보기", key=f"view_full_{plugin_name}"):
                            st.dataframe(df)


def show_analysis_queue():
    """분석 대기열 표시"""
    running_categories = list(analysis_manager.running_tasks.keys())

    if running_categories:
        st.sidebar.subheader("🔄 실행 중인 분석")
        for category in running_categories:
            progress_data = analysis_manager.get_progress(category)
            completed = progress_data.get('completed', 0)
            total = progress_data.get('total', 0)

            st.sidebar.write(f"📊 {category}")
            st.sidebar.progress(completed / total if total > 0 else 0)
            st.sidebar.write(f"진행: {completed}/{total}")
            st.sidebar.divider()