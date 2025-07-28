import json
import streamlit as st
import os
from pathlib import Path


def load_plugin_categories():
    """JSON 파일에서 플러그인 카테고리 설정을 로드"""
    try:
        with open("resources/plugins.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 새로운 구조 처리
        if "categories" in data:
            # ID 기반 새 구조
            categories = {}
            for category_id, category_data in data["categories"].items():
                title = category_data["title"]
                plugins = category_data["plugins"]
                categories[title] = plugins
            return categories
        else:
            # 기존 구조 (하위 호환성)
            return data

    except FileNotFoundError:
        st.error("❌ resources/plugins.json 파일을 찾을 수 없습니다.")
        return {}
    except json.JSONDecodeError:
        st.error("❌ plugins.json 파일 형식이 올바르지 않습니다.")
        return {}
    except Exception as e:
        st.error(f"❌ 플러그인 설정 로드 중 오류 발생: {str(e)}")
        return {}


def load_pid_plugin_categories():
    """JSON 파일에서 PID 플러그인 카테고리 설정을 로드"""
    try:
        with open("resources/pid_plugins.json", 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 새로운 구조 처리
        if "pid_plugins" in data:
            # ID 기반 새 구조
            return data["pid_plugins"]
        elif "💻 프로세스 분석" in data:
            # 기존 구조 (하위 호환성)
            return data["💻 프로세스 분석"]
        elif "💻 프로세스 상세 분석" in data:
            return data["💻 프로세스 상세 분석"]
        else:
            # 첫 번째 키의 값을 반환
            if data:
                first_key = list(data.keys())[0]
                return data[first_key]
            return []

    except FileNotFoundError:
        st.error("❌ resources/pid_plugins.json 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        st.error("❌ pid_plugins.json 파일 형식이 올바르지 않습니다.")
        return []
    except Exception as e:
        st.error(f"❌ PID 플러그인 설정 로드 중 오류 발생: {str(e)}")
        return []


def get_env_config():
    """환경 설정"""
    config = {
        'vol_path': './volatility3/vol.py',
        'default_cores': 1,
        'output_path': './output'
    }

    # 출력 디렉토리 생성
    output_dir = Path(config['output_path'])
    output_dir.mkdir(parents=True, exist_ok=True)

    return config


# 전역 설정 로드
plugin_categories = load_plugin_categories()
pid_plugin_categories = load_pid_plugin_categories()
env_config = get_env_config()