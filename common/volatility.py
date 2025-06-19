import subprocess
import pandas as pd
import streamlit as st
from io import StringIO
import csv
from typing import Tuple
import concurrent.futures
import os
from datetime import datetime
from pathlib import Path

# 설정 로드
import sys

sys.path.append(str(Path(__file__).parent.parent))
from UI.config import env_config, plugin_categories


def _run_volatility_with_encoding(cmd: list) -> subprocess.CompletedProcess:
    """인코딩 문제를 해결하여 Volatility 실행"""
    # Windows 환경에서 UTF-8 인코딩 강제 설정
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['LANG'] = 'en_US.UTF-8'

    try:
        # UTF-8로 실행 시도
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',  # 인코딩 오류시 대체 문자 사용
            env=env
        )
        return result
    except UnicodeDecodeError:
        # UTF-8 실패시 시스템 기본 인코딩으로 재시도
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='cp949',
                errors='replace',
                env=env
            )
            return result
        except:
            # 마지막 시도: bytes로 받아서 직접 처리
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            # bytes를 안전하게 문자열로 변환
            stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
            stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""

            # CompletedProcess 객체 수동 생성
            class MockResult:
                def __init__(self, returncode, stdout, stderr):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            return MockResult(result.returncode, stdout, stderr)


def _clean_csv_data(data: str) -> str:
    """CSV 데이터에서 문제가 되는 문자들 정리"""
    # 제어 문자 및 특수 문자 제거
    import re

    # NULL 문자 제거
    data = data.replace('\x00', '')

    # 비인쇄 문자 제거 (탭, 줄바꿈, 캐리지 리턴 제외)
    data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', data)

    # 유니코드 개인용 영역 문자 제거 (U+E000–U+F8FF)
    data = re.sub(r'[\uE000-\uF8FF]', '?', data)

    # 기타 문제가 될 수 있는 특수 문자 제거
    data = re.sub(r'[\uFFF0-\uFFFF]', '?', data)

    return data


@st.cache_data(show_spinner=False)
def run_volatility(plugin: str, dump_path: str, _mtime=None) -> pd.DataFrame:
    """기본 Volatility 플러그인 실행"""
    # dumpfiles 플러그인인 경우 특별 처리
    if plugin == "windows.dumpfiles":
        cmd = [
            "python", env_config['vol_path'], "-r", "csv", "-f", dump_path,
            plugin, "--dump-dir", env_config['dump_files_path']
        ]
    else:
        cmd = [
            "python", env_config['vol_path'], "-r", "csv", "-f", dump_path, plugin
        ]

    result = _run_volatility_with_encoding(cmd)

    if result.returncode != 0:
        error_msg = result.stderr
        # 인코딩 오류인 경우 더 자세한 정보 제공
        if "UnicodeEncodeError" in error_msg or "codec can't encode" in error_msg:
            error_msg += "\n\n💡 해결 방법:\n"
            error_msg += "1. 시스템 로케일을 UTF-8로 변경\n"
            error_msg += "2. 메모리 덤프 파일 경로에 한글이 없는지 확인\n"
            error_msg += "3. 관리자 권한으로 실행"
        raise RuntimeError(error_msg)

    # 출력 데이터 정리
    clean_output = _clean_csv_data(result.stdout.strip())
    lines = clean_output.splitlines()

    if not lines:
        raise RuntimeError("분석 결과가 비어있습니다.")

    csv_data = StringIO()
    writer = csv.writer(csv_data)
    reader = csv.reader(lines)

    try:
        for row in reader:
            # 각 셀의 데이터도 정리
            cleaned_row = [_clean_csv_data(cell.strip()) for cell in row]
            writer.writerow(cleaned_row)
    except Exception as e:
        st.warning(f"⚠️ CSV 파싱 중 일부 데이터가 손실되었을 수 있습니다: {str(e)}")

    csv_data.seek(0)
    try:
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        # CSV 파싱 실패시 원본 데이터 반환
        st.error(f"CSV 파싱 실패: {str(e)}")
        # 빈 DataFrame 반환
        return pd.DataFrame({"Error": ["CSV 파싱 실패", f"원인: {str(e)}"]})


@st.cache_data(show_spinner=False)
def run_pid_plugin(plugin_name: str, dump_path: str, pid: str, _mtime=None) -> pd.DataFrame:
    """PID 기반 Volatility 플러그인 실행"""
    cmd = ["python", env_config['vol_path'], "-r", "csv", "-f", dump_path, plugin_name, "--pid", pid]

    result = _run_volatility_with_encoding(cmd)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    clean_output = _clean_csv_data(result.stdout.strip())
    lines = [line for line in clean_output.splitlines() if line.strip()]

    if not lines:
        return pd.DataFrame({"Info": [f"PID {pid}에 대한 결과가 없습니다."]})

    csv_data = StringIO("\n".join(lines))
    try:
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        return pd.DataFrame({"Error": [f"CSV 파싱 실패: {str(e)}"]})


def run_volatility_process(plugin: str, dump_path: str) -> Tuple[str, pd.DataFrame, str]:
    """멀티프로세싱용 Volatility 실행 함수"""
    try:
        # dumpfiles 플러그인인 경우 특별 처리
        if plugin == "windows.dumpfiles":
            cmd = [
                "python", env_config['vol_path'], "-r", "csv", "-f", dump_path,
                plugin, "--dump-dir", env_config['dump_files_path']
            ]
        else:
            cmd = [
                "python", env_config['vol_path'], "-r", "csv", "-f", dump_path, plugin
            ]

        result = _run_volatility_with_encoding(cmd)

        if result.returncode != 0:
            return plugin, None, result.stderr

        clean_output = _clean_csv_data(result.stdout.strip())
        lines = clean_output.splitlines()

        if not lines:
            return plugin, pd.DataFrame({"Info": ["결과가 없습니다."]}), None

        csv_data = StringIO()
        writer = csv.writer(csv_data)
        reader = csv.reader(lines)

        for row in reader:
            cleaned_row = [_clean_csv_data(cell.strip()) for cell in row]
            writer.writerow(cleaned_row)

        csv_data.seek(0)
        try:
            df = pd.read_csv(csv_data)
            return plugin, df, None
        except Exception as e:
            return plugin, pd.DataFrame({"Error": [f"CSV 파싱 실패: {str(e)}"]}), None

    except Exception as e:
        return plugin, None, str(e)


def run_category_analysis(dump_path: str, selected_category: str, max_workers: int):
    """카테고리 분석 실행"""
    plugins_to_run = plugin_categories[selected_category]

    # 해당 카테고리의 기존 결과만 초기화
    for emoji, title, plugin in plugins_to_run:
        result_key = f"analysis_results_{selected_category}_{plugin}"
        if result_key in st.session_state:
            del st.session_state[result_key]

    # 진행 상황 표시용 컨테이너
    progress_container = st.empty()

    completed_count = 0
    total_count = len(plugins_to_run)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 모든 작업 제출
        future_to_plugin = {
            executor.submit(run_volatility_process, plugin, dump_path): (emoji, title, plugin)
            for emoji, title, plugin in plugins_to_run
        }

        # 완료된 작업 처리
        for future in concurrent.futures.as_completed(future_to_plugin):
            emoji, title, plugin = future_to_plugin[future]
            completed_count += 1

            # 진행률 업데이트
            progress = completed_count / total_count
            progress_container.progress(progress, text=f"분석 진행: {completed_count}/{total_count}")

            try:
                plugin_name, df, error = future.result()

                # 카테고리별로 결과 저장
                result_key = f"analysis_results_{selected_category}_{plugin_name}"
                st.session_state[result_key] = (df, error)

            except Exception as e:
                result_key = f"analysis_results_{selected_category}_{plugin}"
                st.session_state[result_key] = (None, str(e))

    # 완료 후 진행률 표시 제거
    progress_container.empty()
    st.session_state["analysis_running"] = False