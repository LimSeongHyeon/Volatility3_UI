import streamlit as st
import multiprocessing
import time
import os
from UI.navbar import setup_sidebar
from UI.mainSection import show_main_content
from UI.components import show_resource_monitoring
from common.async_manager import analysis_manager


def main():
    # Streamlit 페이지 설정
    st.set_page_config(
        page_title="Memory Analysis Tool",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 페이지 제목
    st.title("🔍 Memory Analysis Tool")
    st.markdown("**Volatility3 기반 메모리 덤프 분석 도구** - 멀티프로세싱으로 UI와 분석 작업 완전 분리")

    # 세션 상태 초기화
    if 'dump_path' not in st.session_state:
        st.session_state.dump_path = ""
    if 'max_workers' not in st.session_state:
        st.session_state.max_workers = 1
    if 'analysis_running' not in st.session_state:
        st.session_state.analysis_running = False

    # 사이드바 설정
    dump_path, analysis_mode, selected_category = setup_sidebar()

    # 메인 컨텐츠 영역
    if not dump_path:
        show_welcome_content()
    else:
        # 실행 중인 분석이 있는지 확인
        check_running_analysis(selected_category if analysis_mode == "🔍 일반 분석" else None)

        # 메인 컨텐츠 표시
        show_main_content(dump_path, analysis_mode, selected_category)


def show_welcome_content():
    """환영 메시지 및 사용법 안내"""
    st.info("👈 사이드바에서 메모리 덤프 파일 경로를 설정하고 '경로 적용' 버튼을 클릭하세요.")

    # 사용법 안내
    with st.expander("📖 사용법 안내", expanded=True):
        st.markdown("""
        ### 🚀 빠른 시작

        1. **파일 설정**: 사이드바에서 메모리 덤프 파일 경로 입력
        2. **경로 적용**: '경로 적용' 버튼 클릭
        3. **분석 모드 선택**: 일반 분석 또는 PID 분석 선택
        4. **분석 시작**: 원하는 분석 실행

        ### 📋 분석 모드

        - **🔍 일반 분석**: 카테고리별 체계적 분석
          - 시스템 정보, 프로세스 분석, 네트워크 분석 등
          - 멀티프로세싱으로 빠른 분석
        - **🎯 PID 분석**: 특정 프로세스 심화 분석
          - DLL 분석, 메모리 분석, 파일 덤프 등

        ### 💡 분석 팁

        1. **시작 권장**: '프로세스 분석' 카테고리로 시스템 전반 파악
        2. **의심 프로세스 발견**: PID 분석으로 심화 조사
        3. **네트워크 분석**: 외부 연결 및 통신 상태 확인
        4. **악성코드 분석**: 메모리 패치, 후킹 등 탐지

        ### ⚡ 멀티프로세싱 특징

        - **UI 블로킹 없음**: 분석 중에도 UI 조작 가능
        - **리소스 모니터링**: CPU/메모리 사용률 실시간 추적
        - **자동 최적화**: 시스템 부하에 따른 워커 수 조정
        - **안정성**: 분석 프로세스 크래시 시에도 UI 정상 동작
        """)

    # 시스템 정보 표시
    with st.expander("💻 시스템 정보", expanded=False):
        import psutil
        import os

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("CPU 코어 수", os.cpu_count())
            st.metric("현재 CPU 사용률", f"{psutil.cpu_percent(interval=1):.1f}%")

        with col2:
            memory = psutil.virtual_memory()
            st.metric("총 메모리", f"{memory.total / (1024 ** 3):.1f} GB")
            st.metric("현재 메모리 사용률", f"{memory.percent:.1f}%")

        with col3:
            st.metric("사용 가능한 메모리", f"{memory.available / (1024 ** 3):.1f} GB")
            st.metric("Volatility3", "✅ 준비됨" if os.path.exists("./volatility3/vol.py") else "❌ 없음")


def check_running_analysis(selected_category):
    """실행 중인 분석 확인 및 상태 업데이트"""
    if not selected_category:
        return

    # 현재 UI 상태
    ui_running = st.session_state.get("analysis_running", False)

    # 실제 프로세스 상태
    actual_running = analysis_manager.is_running(selected_category)

    print(f"DEBUG: UI state: {ui_running}, Actual: {actual_running}, Category: {selected_category}")

    if actual_running:
        # 분석이 실제로 실행 중
        st.session_state.analysis_running = True

        # 리소스 모니터링 표시
        show_resource_monitoring(analysis_manager, selected_category)

        # 진행 상황 표시
        show_analysis_progress(selected_category)

        # 자동 새로고침
        time.sleep(2)
        st.rerun()
    elif ui_running and not actual_running:
        # UI는 실행 중이라고 하는데 실제로는 끝남 - 상태 복원 필요
        print(f"DEBUG: Restoring UI state for {selected_category}")
        st.session_state.analysis_running = False

        # 완료 메시지
        progress_data = analysis_manager.get_progress(selected_category)
        status = progress_data.get('status', 'unknown')
        print(f"DEBUG: Final status: {status}")

        if status == 'completed':
            st.success("🎉 분석이 완료되었습니다!")
        elif status == 'error':
            st.error("❌ 분석 중 오류가 발생했습니다.")
        elif status == 'stopped':
            st.warning("⚠️ 분석이 중단되었습니다.")

        # 강제 새로고침
        st.rerun()


def show_analysis_progress(category):
    """분석 진행 상황 표시"""
    progress_data = analysis_manager.get_progress(category)

    if not progress_data:
        return

    total = progress_data.get('total', 0)
    completed = progress_data.get('completed', 0)
    current_plugin = progress_data.get('current_plugin', '')
    status = progress_data.get('status', 'idle')

    if status == 'running':
        # 진행률 표시
        progress_value = completed / total if total > 0 else 0

        st.markdown("---")
        st.subheader("🔄 분석 진행 상황")

        # 시스템 리소스와 워커 정보 표시
        resource_info = analysis_manager.get_resource_info(category)
        if resource_info:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("현재 CPU", f"{resource_info['current_cpu']:.1f}%")
            with col2:
                st.metric("현재 메모리", f"{resource_info['current_memory']:.1f}%")
            with col3:
                # 현재 사용 중인 워커 수 (추정)
                import psutil
                monitor = analysis_manager.resource_monitor
                optimal_workers = monitor.get_optimal_workers(st.session_state.get("max_workers", 4))
                st.metric("활성 워커", f"{optimal_workers}개")
            with col4:
                st.metric("총 코어", f"{os.cpu_count()}개")

        # 프로그레스 바
        st.progress(progress_value, text=f"분석 진행: {completed}/{total}")

        # 현재 상태
        col1, col2 = st.columns([3, 1])
        with col1:
            if current_plugin:
                st.info(f"🔄 현재 실행 중: **{current_plugin}**")

            # 완료된 플러그인
            if completed > 0:
                last_completed = progress_data.get('last_completed', '')
                if last_completed:
                    st.success(f"✅ 최근 완료: **{last_completed}**")

        with col2:
            # 중단 버튼
            if st.button("⏹️ 분석 중단", key="stop_analysis", type="secondary"):
                analysis_manager.stop_analysis(category)
                st.session_state.analysis_running = False
                st.warning("⚠️ 분석이 중단되었습니다.")
                # 즉시 새로고침하여 UI 상태 복원
                st.rerun()

        st.markdown("---")

    elif status == 'completed':
        st.success(f"🎉 **{category}** 분석이 완료되었습니다!")
        if 'total_time' in progress_data:
            st.info(f"⏱️ 총 소요 시간: {progress_data['total_time']:.1f}초")

    elif status == 'error':
        error_msg = progress_data.get('error', '알 수 없는 오류')
        st.error(f"❌ 분석 중 오류 발생: {error_msg}")

    elif status == 'stopped':
        st.warning("⚠️ 분석이 사용자에 의해 중단되었습니다.")


def setup_multiprocessing():
    """멀티프로세싱 환경 설정"""
    try:
        # Windows 호환성을 위한 spawn 방식 설정
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # 이미 설정된 경우 무시
        pass

    # 멀티프로세싱 관련 환경 변수 설정
    import os
    os.environ['PYTHONUNBUFFERED'] = '1'  # 출력 버퍼링 비활성화


if __name__ == "__main__":
    # 멀티프로세싱 환경 설정
    setup_multiprocessing()

    # Streamlit 앱 실행
    main()