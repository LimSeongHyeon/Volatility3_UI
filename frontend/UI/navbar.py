import streamlit as st
import os
from .config import plugin_categories, env_config
from .async_components import show_async_analysis_controls, show_analysis_queue
from common.utils import open_folder


def setup_sidebar():
    """사이드바 UI 설정 및 반환값 처리"""
    # run_category_analysis 임포트를 함수 내부로 이동
    from common.volatility import run_category_analysis

    with st.sidebar:

        # 1. 메모리 덤프 파일 경로 입력
        st.subheader("분석 파일")
        dump_path_input = st.text_input(
            "파일 경로",
            value=st.session_state.get("dump_path", ""),
            placeholder="예: C:\\forensics\\memory.raw",
            help="메모리 덤프 파일의 전체 경로를 입력하세요",
            disabled=st.session_state["analysis_running"]
        )

        if st.button("경로 적용", use_container_width=True, disabled=st.session_state["analysis_running"]):
            if dump_path_input and os.path.exists(dump_path_input):
                st.session_state["dump_path"] = dump_path_input
                st.success("✅ 파일 경로가 적용되었습니다!")
                st.rerun()
            elif dump_path_input:
                st.error("❌ 파일을 찾을 수 없습니다")
            else:
                st.warning("⚠️ 파일 경로를 입력하세요")

        st.divider()

        # 2. 분석 모드 선택
        st.subheader("분석 모드")
        analysis_mode = st.selectbox(
            "모드 선택",
            ["🔍 일반 분석", "🎯 PID 분석"],
            help="원하는 분석 방식을 선택하세요",
            disabled=st.session_state["analysis_running"]
        )

        selected_category = None
        # 일반 분석 모드일 때 카테고리 선택
        if analysis_mode == "🔍 일반 분석":
            selected_category = st.selectbox(
                "카테고리 선택",
                list(plugin_categories.keys()),
                help="분석할 카테고리를 선택하세요",
                disabled=st.session_state["analysis_running"]
            )

            # 분석 시작/진행 상태 표시
            if st.session_state["analysis_running"]:
                # 분석 중일 때는 프로그레스 바만 표시
                st.progress(0.5, text="분석 진행 중...")
            else:
                # 분석 중이 아닐 때만 분석 시작 버튼 표시
                if st.button("🚀 분석 시작", use_container_width=True, type="primary", disabled=st.session_state["analysis_running"]):
                    if st.session_state.get("dump_path"):
                        st.session_state["analysis_running"] = True
                        st.session_state["selected_category"] = selected_category
                        # 분석 실행
                        run_category_analysis(st.session_state["dump_path"], selected_category,
                                              st.session_state.get("max_workers", 1))
                        st.rerun()
                    else:
                        st.error("❌ 먼저 메모리 덤프 파일을 설정하세요")

        st.divider()

        # 3. 시스템 정보 및 코어 설정
        st.subheader("시스템 정보")
        st.metric("사용 가능한 CPU 코어", os.cpu_count() or "알 수 없음")

        max_workers = st.number_input(
            "사용할 코어 수",
            min_value=1,
            max_value=os.cpu_count() or 8,
            value=st.session_state.get("max_workers", env_config['default_cores']),
            help=f"최대 {os.cpu_count() or 8}개 코어 사용 가능 (기본값: {env_config['default_cores']})",
            disabled=st.session_state["analysis_running"]
        )

        st.divider()

        if st.button("📁 출력 폴더", use_container_width=True):
            open_folder(env_config['output_path'])

        st.session_state["max_workers"] = max_workers

        # GitHub 정보 표시
        st.divider()
        st.markdown(
            """
            <div style='text-align: center; padding: 10px; margin-top: 20px;'>
                <p style='margin: 0; font-size: 12px; color: #666;'>Developed by</p>
                <p style='margin: 0; font-size: 14px; font-weight: bold;'>LimSeongHyeon</p>
                <a href='https://github.com/LimSeongHyeon/Volatility3_UI' target='_blank' style='text-decoration: none;'>
                    <p style='margin: 5px 0 0 0; font-size: 12px; color: #0366d6;'>
                        🔗 GitHub
                    </p>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 현재 경로 가져오기
    dump_path = st.session_state.get("dump_path", "")

    return dump_path, analysis_mode, selected_category