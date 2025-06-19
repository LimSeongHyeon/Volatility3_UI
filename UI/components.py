import streamlit as st
import os
from datetime import datetime
from .config import env_config
from common.utils import open_folder, clean_dump_files, save_csv_file, get_dump_file_count, has_dump_files


def show_analysis_hints(label: str):
    """분석별 힌트 표시"""
    if "DLL" in label:
        st.info("🔍 **DLL 분석 팁:** 의심스러운 DLL, 경로가 이상한 DLL, 서명되지 않은 DLL을 확인하세요.")
    elif "악성" in label:
        st.info("🦠 **악성코드 분석 팁:** 실행 가능한 메모리 영역, 코드 인젝션, 후킹된 API를 확인하세요.")
    elif "가상메모리" in label:
        st.info("💾 **가상메모리 분석 팁:** 비정상적인 메모리 보호 속성, RWX 권한 영역을 확인하세요.")
    elif "파일 덤프" in label:
        st.info("📄 **파일 덤프 팁:** 해당 프로세스가 사용하는 파일들을 추출합니다. 의심 파일 분석에 유용합니다.")


def show_dump_file_management(pid: str = None, plugin_name: str = ""):
    """덤프 파일 관리 UI"""
    if has_dump_files():
        file_count = get_dump_file_count()
        if pid:
            st.warning(f"⚠️ PID {pid}의 파일들이 덤프되었습니다. ({file_count}개 파일)")
        else:
            st.warning(f"⚠️ 덤프 폴더에 {file_count}개의 파일이 있습니다. (용량 주의)")

        col1, col2 = st.columns(2)
        with col1:
            key_suffix = f"_{pid}_{plugin_name}" if pid else f"_{plugin_name}"
            if st.button("📁 덤프 폴더 열기", key=f"open_dump{key_suffix}"):
                open_folder(env_config['dump_files_path'])
        with col2:
            if st.button("🗑️ 덤프 파일 정리", key=f"clean_dump{key_suffix}"):
                clean_dump_files()


def show_download_buttons(df, plugin_name: str, label: str, category: str = None, pid: str = None):
    """다운로드 및 저장 버튼 표시"""
    csv_data = df.to_csv(index=False)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if pid:
        filename = f"PID_{pid}_{plugin_name}_{timestamp}.csv"
        download_key = f"download_pid_{pid}_{plugin_name}"
        save_key = f"save_pid_{pid}_{plugin_name}"
    else:
        filename = f"{plugin_name}_{timestamp}.csv"
        download_key = f"download_{category}_{plugin_name}"
        save_key = f"save_{category}_{plugin_name}"

    # 다운로드 버튼
    st.download_button(
        label=f"💾 다운로드",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=download_key
    )


def show_analysis_result(df, error, label: str, plugin_name: str, category: str = None, pid: str = None):
    """분석 결과 표시 (성공/실패 공통)"""
    if error:
        st.error(f"❌ {label} 분석 실패")
        st.code(error)
        return

    if df is None:
        st.error(f"❌ {label} 분석 실패: 데이터가 없습니다.")
        return

    st.success(f"✅ {label} 완료: {len(df)}개 항목")

    # 특별한 처리가 필요한 플러그인
    if plugin_name == "windows.dumpfiles":
        st.info("📁 **파일 덤프 완료!** 실제 파일들은 `file_dumps` 폴더에 저장되었습니다.")
        show_dump_file_management(pid, plugin_name)

    # 분석 힌트 표시
    show_analysis_hints(label)

    # 데이터 표시
    st.dataframe(df, height=800)

    # 다운로드 버튼
    show_download_buttons(df, plugin_name, label, category, pid)