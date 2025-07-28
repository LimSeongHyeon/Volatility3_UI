import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show_resource_monitoring(analysis_manager, category: str):
    """리소스 모니터링 표시"""
    resource_info = analysis_manager.get_resource_info(category)

    if resource_info:
        st.subheader("📊 시스템 리소스 모니터링")

        # 현재 상태
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cpu_color = "red" if resource_info['current_cpu'] > 80 else "orange" if resource_info[
                                                                                        'current_cpu'] > 60 else "green"
            st.metric(
                "현재 CPU",
                f"{resource_info['current_cpu']:.1f}%",
                delta=None,
                help="현재 CPU 사용률"
            )

        with col2:
            memory_color = "red" if resource_info['current_memory'] > 85 else "orange" if resource_info[
                                                                                              'current_memory'] > 70 else "green"
            st.metric(
                "현재 메모리",
                f"{resource_info['current_memory']:.1f}%",
                delta=None,
                help="현재 메모리 사용률"
            )

        with col3:
            st.metric(
                "최대 CPU",
                f"{resource_info['max_cpu']:.1f}%",
                delta=None,
                help="분석 중 최대 CPU 사용률"
            )

        with col4:
            st.metric(
                "최대 메모리",
                f"{resource_info['max_memory']:.1f}%",
                delta=None,
                help="분석 중 최대 메모리 사용률"
            )

        # 리소스 사용률 그래프 (선택적)
        progress_data = analysis_manager.get_progress(category)
        cpu_history = progress_data.get('cpu_usage', [])
        memory_history = progress_data.get('memory_usage', [])

        if len(cpu_history) > 1:
            with st.expander("📈 리소스 사용률 그래프", expanded=False):
                fig = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('CPU 사용률 (%)', '메모리 사용률 (%)'),
                    vertical_spacing=0.1
                )

                # CPU 그래프
                fig.add_trace(
                    go.Scatter(
                        y=cpu_history,
                        mode='lines+markers',
                        name='CPU',
                        line=dict(color='blue'),
                        marker=dict(size=4)
                    ),
                    row=1, col=1
                )

                # 메모리 그래프
                fig.add_trace(
                    go.Scatter(
                        y=memory_history,
                        mode='lines+markers',
                        name='Memory',
                        line=dict(color='red'),
                        marker=dict(size=4)
                    ),
                    row=2, col=1
                )

                fig.update_layout(height=400, showlegend=False)
                fig.update_yaxes(range=[0, 100])

                st.plotly_chart(fig, use_container_width=True)


def show_analysis_result(result_data, plugin_name: str, label: str, category: str = None, pid: str = None):
    """분석 결과 표시 (캐시 상태 포함)"""

    # 캐시에서 온 결과인지 확인
    from_cache = result_data.get("from_cache", False)

    if result_data["status"] == "error":
        error_msg = result_data["error"]
        if from_cache:
            st.error(f"❌ {label} 분석 실패 (캐시됨)")
            st.info("🗄️ 이 결과는 이전에 캐시된 오류입니다.")
        else:
            st.error(f"❌ {label} 분석 실패")
        st.code(error_msg.replace("[CACHED] ", ""))
        return

    if result_data["status"] != "success" or "result" not in result_data:
        st.error(f"❌ {label} 분석 실패: 데이터가 없습니다.")
        return

    # 결과 데이터 처리
    result = result_data["result"]

    # 성공 메시지 (캐시 상태 포함)
    if from_cache:
        st.success(f"⚡ {label} 완료 (캐시에서 로드)")
        st.info("🗄️ 이 결과는 이전에 분석된 캐시 데이터입니다.")
    else:
        st.success(f"✅ {label} 완료")

    # JSON 결과를 DataFrame으로 변환 시도
    try:
        if isinstance(result, list) and len(result) > 0:
            df = pd.DataFrame(result)
            st.write(f"📊 **{len(df)}개 항목**")
            st.dataframe(df, height=400)

            # CSV 다운로드 버튼
            csv_data = df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cache_suffix = "_cached" if from_cache else ""
            filename = f"{plugin_name}_{timestamp}{cache_suffix}.csv"

            st.download_button(
                label="💾 CSV 다운로드",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
        else:
            st.json(result)
    except Exception as e:
        st.json(result)


def show_analysis_hints(label: str):
    """분석별 힌트 표시"""
    hints = {
        "DLL": "🔍 **DLL 분석 팁:** 의심스러운 DLL, 경로가 이상한 DLL, 서명되지 않은 DLL을 확인하세요.",
        "악성": "🦠 **악성코드 분석 팁:** 실행 가능한 메모리 영역, 코드 인젝션, 후킹된 API를 확인하세요.",
        "가상메모리": "💾 **가상메모리 분석 팁:** 비정상적인 메모리 보호 속성, RWX 권한 영역을 확인하세요.",
        "파일": "📄 **파일 분석 팁:** 의심스러운 파일 경로, 임시 파일, 숨김 파일을 확인하세요.",
        "프로세스": "🔍 **프로세스 분석 팁:** 비정상적인 프로세스 이름, 경로, PPID 관계를 확인하세요.",
        "네트워크": "🌐 **네트워크 분석 팁:** 외부 연결, 비정상적인 포트, 의심스러운 IP를 확인하세요."
    }

    for keyword, hint in hints.items():
        if keyword in label:
            st.info(hint)
            break


def show_progress_status(is_running: bool, current_plugin: str = ""):
    """진행 상태 표시"""
    if is_running:
        if current_plugin:
            st.info(f"🔄 실행 중: {current_plugin}")
        else:
            st.info("🔄 분석 진행 중...")

        # 프로그레스 바 (임시)
        progress_bar = st.progress(0)
        return progress_bar
    return None


def show_error_message(error: str, command: str):
    """에러 메시지 표시"""
    st.error(f"❌ 명령어 '{command}' 실행 중 오류 발생")

    with st.expander("오류 상세 내용"):
        st.code(error)

        # 일반적인 해결 방법 제시
        st.markdown("### 💡 해결 방법:")
        st.markdown("""
        1. **파일 경로 확인**: 메모리 덤프 파일이 올바른 경로에 있는지 확인
        2. **파일 권한 확인**: 파일 읽기 권한이 있는지 확인  
        3. **Volatility 설치 확인**: backend/volatility3 폴더가 있는지 확인
        4. **플러그인 호환성**: 메모리 덤프와 플러그인이 호환되는지 확인
        """)