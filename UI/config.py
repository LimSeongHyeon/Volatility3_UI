import json
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def load_plugin_categories():
    """JSON 파일에서 플러그인 카테고리 설정을 로드"""
    try:
        # 현재 파일의 위치를 기준으로 JSON 파일 경로 설정
        current_dir = Path(__file__).parent
        json_path = current_dir.parent / "res" / "plugin_categories.json"

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # JSON 객체를 튜플로 변환하여 기존 코드와 호환성 유지
        plugin_categories = {}
        for category, plugins in data.items():
            plugin_categories[category] = [
                (plugin['emoji'], plugin['label'], plugin['command'])
                for plugin in plugins
            ]

        return plugin_categories
    except FileNotFoundError:
        st.error("❌ plugin_categories.json 파일을 찾을 수 없습니다.")
        return {}
    except json.JSONDecodeError:
        st.error("❌ plugin_categories.json 파일 형식이 올바르지 않습니다.")
        return {}
    except Exception as e:
        st.error(f"❌ 플러그인 설정 로드 중 오류 발생: {str(e)}")
        return {}


def load_pid_plugin_categories():
    """JSON 파일에서 PID 플러그인 카테고리 설정을 로드"""
    try:
        # 현재 파일의 위치를 기준으로 JSON 파일 경로 설정
        current_dir = Path(__file__).parent
        json_path = current_dir.parent / "res" / "pid_plugin_categories.json"

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # JSON 객체를 튜플로 변환하여 기존 코드와 호환성 유지
        pid_plugins = [
            (plugin['emoji'], plugin['label'], plugin['command'])
            for plugin in data['pid_plugins']
        ]

        return pid_plugins
    except FileNotFoundError:
        st.error("❌ pid_plugin_categories.json 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        st.error("❌ pid_plugin_categories.json 파일 형식이 올바르지 않습니다.")
        return []
    except Exception as e:
        st.error(f"❌ PID 플러그인 설정 로드 중 오류 발생: {str(e)}")
        return []


def get_env_config():
    """환경변수에서 설정값 로드"""
    config = {
        'vol_path': os.getenv('VOL_PATH', 'vol.py'),
        'default_cores': int(os.getenv('DEFAULT_CORES', '1')),
        'output_path': os.getenv('OUTPUT_PATH', './output')
    }

    # 출력 디렉토리가 없으면 생성
    output_dir = Path(config['output_path'])
    output_dir.mkdir(parents=True, exist_ok=True)

    # 파일 덤프 디렉토리 경로 추가 (OUTPUT_PATH + /file_dumps)
    config['dump_files_path'] = str(output_dir / 'file_dumps')

    # 덤프 파일 디렉토리가 없으면 생성
    dump_dir = Path(config['dump_files_path'])
    dump_dir.mkdir(parents=True, exist_ok=True)

    return config


# 플러그인 카테고리 로드
plugin_categories = load_plugin_categories()

# PID 플러그인 카테고리 로드
pid_plugin_categories = load_pid_plugin_categories()

# 환경 설정 로드
env_config = get_env_config()