import os
import streamlit as st
import subprocess
import platform
import shutil
from datetime import datetime
from pathlib import Path

# 설정 로드
import sys

sys.path.append(str(Path(__file__).parent.parent))
from UI.config import env_config


def open_folder(folder_path: str):
    """폴더 열기 공통 함수"""
    try:
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", folder_path])
        else:  # Linux
            subprocess.run(["xdg-open", folder_path])
        st.success(f"✅ 폴더가 열렸습니다!")
    except Exception as e:
        st.error(f"❌ 폴더 열기 실패: {str(e)}")


def clean_dump_files():
    """덤프 파일 정리 함수"""
    try:
        dump_folder = env_config['dump_files_path']
        if os.path.exists(dump_folder):
            shutil.rmtree(dump_folder)
            os.makedirs(dump_folder)
        st.success("✅ 덤프 파일들이 정리되었습니다!")
        return True
    except Exception as e:
        st.error(f"❌ 정리 실패: {str(e)}")
        return False


def save_csv_file(data: str, plugin_name: str, pid: str = None) -> str:
    """CSV 파일 저장 함수"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if pid:
        filename = f"PID_{pid}_{plugin_name}_{timestamp}.csv"
    else:
        filename = f"{plugin_name}_{timestamp}.csv"

    output_file_path = os.path.join(env_config['output_path'], filename)

    try:
        with open(output_file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(data)
        return output_file_path
    except Exception as e:
        raise Exception(f"파일 저장 실패: {str(e)}")


def get_dump_file_count() -> int:
    """덤프 폴더의 파일 개수 반환"""
    dump_folder = env_config['dump_files_path']
    if os.path.exists(dump_folder) and os.listdir(dump_folder):
        return len([f for f in os.listdir(dump_folder) if f.startswith('file.')])
    return 0


def has_dump_files() -> bool:
    """덤프 파일이 존재하는지 확인"""
    return get_dump_file_count() > 0