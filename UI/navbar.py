import streamlit as st
import os
from UI.config import plugin_categories, env_config


def setup_sidebar():
    """사이드바 UI 설정"""
    with st.sidebar:
        # 분석 실행 상태 확인
        analysis_running = st.session_state.get("analysis_running", False)

        # 메모리 덤프 파일 경로 입력
        st.subheader("📁 분석 파일")
        dump_path_input = st.text_input(
            "파일 경로",
            value=st.session_state.get("dump_path", ""),
            placeholder="예: C:\\forensics\\memory.raw",
            help="메모리 덤프 파일의 전체 경로를 입력하세요",
            disabled=analysis_running
        )

        if st.button("경로 적용", use_container_width=True, disabled=analysis_running):
            if dump_path_input and os.path.exists(dump_path_input):
                st.session_state["dump_path"] = dump_path_input
                st.success("✅ 파일 경로가 적용되었습니다!")
                st.rerun()
            elif dump_path_input:
                st.error("❌ 파일을 찾을 수 없습니다")
            else:
                st.warning("⚠️ 파일 경로를 입력하세요")

        st.divider()

        # 분석 모드 선택
        st.subheader("🔧 분석 모드")
        analysis_mode = st.selectbox(
            "모드 선택",
            ["🔍 일반 분석", "🎯 PID 분석"],
            help="원하는 분석 방식을 선택하세요",
            disabled=analysis_running
        )

        selected_category = None
        # 일반 분석 모드일 때 카테고리 선택
        if analysis_mode == "🔍 일반 분석":
            selected_category = st.selectbox(
                "카테고리 선택",
                list(plugin_categories.keys()),
                help="분석할 카테고리를 선택하세요",
                disabled=analysis_running
            )

        st.divider()

        # 시스템 정보 (참고용)
        st.subheader("💻 시스템 정보")
        import psutil

        col1, col2 = st.columns(2)
        with col1:
            st.metric("CPU 코어", os.cpu_count() or "N/A")
        with col2:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                st.metric("CPU 사용률", f"{cpu_percent:.1f}%")
            except:
                st.metric("CPU 사용률", "N/A")

        # 메모리 정보
        try:
            memory = psutil.virtual_memory()
            st.metric("메모리 사용률", f"{memory.percent:.1f}%")
        except:
            st.metric("메모리 사용률", "N/A")

        st.divider()

        # 캐시 정보
        st.subheader("🗄️ 캐시")
        try:
            from common.cache_manager import simple_cache
            stats = simple_cache.get_stats()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("항목", stats['count'])
            with col2:
                st.metric("크기", f"{stats['size_mb']:.1f}MB")

            if st.button("🗑️ 정리"):
                cleared = simple_cache.clear()
                st.success(f"✅ {cleared}개 정리됨")
                st.rerun()

        except:
            st.error("캐시 정보 없음")

        st.session_state["max_workers"] = os.cpu_count() or 4

        st.divider()

        # 개발자 정보
        st.markdown(
            """
            <div style='text-align: center; padding: 10px;'>
                <p style='margin: 0; font-size: 12px; color: #666;'>Memory Analysis Tool</p>
                <p style='margin: 0; font-size: 10px; color: #888;'>Powered by Volatility3</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 현재 설정 반환
    dump_path = st.session_state.get("dump_path", "")
    return dump_path, analysis_mode, selected_category