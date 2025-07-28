import json
import subprocess
import multiprocessing
import pandas as pd
from typing import Optional
from .cache_manager import simple_cache

import json
import subprocess
import multiprocessing
import pandas as pd
from typing import Optional
from datetime import datetime
from pathlib import Path
from .cache_manager import simple_cache


def log_with_time(message: str):
    """시간과 함께 로그 출력 (간소화)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_volatility_with_cache(file_path: str, command: str, pid: Optional[int] = None) -> dict:
    """캐시를 사용한 Volatility 실행"""

    # 1. 캐시 확인
    cached = simple_cache.get(file_path, command, pid)
    if cached:
        log_with_time(f"📄 Cache hit: {command}")
        cached['from_cache'] = True
        return cached

    log_with_time(f"⚡ Executing: {command}")

    # 2. 실제 실행
    try:
        cmd = ["python3", "./volatility3/vol.py", "-f", file_path, command, "--output", "json"]
        if pid:
            cmd.extend(["--pid", str(pid)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            log_with_time(f"❌ FAILED {command}: {result.stderr[:100]}...")
            result_data = {
                "status": "error",
                "error": result.stderr,
                "command": command,
                "from_cache": False
            }
        else:
            try:
                output = json.loads(result.stdout)
                log_with_time(f"✅ SUCCESS {command}")
            except json.JSONDecodeError as e:
                log_with_time(f"⚠️ JSON parse failed for {command}")
                output = {"text_output": result.stdout}

            result_data = {
                "status": "success",
                "command": command,
                "pid": pid,
                "result": output,
                "from_cache": False
            }

        # 3. 캐시에 저장
        simple_cache.save(file_path, command, result_data, pid)

        return result_data

    except subprocess.TimeoutExpired:
        log_with_time(f"⏱️ TIMEOUT: {command}")
        result_data = {
            "status": "error",
            "error": "Analysis timeout (10 minutes)",
            "command": command,
            "from_cache": False
        }
        simple_cache.save(file_path, command, result_data, pid)
        return result_data
    except Exception as e:
        log_with_time(f"💥 EXCEPTION {command}: {e}")
        result_data = {
            "status": "error",
            "error": str(e),
            "command": command,
            "from_cache": False
        }
        simple_cache.save(file_path, command, result_data, pid)
        return result_data


def volatility_worker(file_path: str, command: str, pid: Optional[int], result_queue: multiprocessing.Queue):
    """멀티프로세싱 워커"""
    result = run_volatility_with_cache(file_path, command, pid)
    result_queue.put(result)


def run_volatility_analysis(file_path: str, command: str, pid: Optional[int] = None):
    """동기 분석"""
    return run_volatility_with_cache(file_path, command, pid)


def run_volatility_process(plugin: str, dump_path: str):
    """멀티프로세싱용 함수"""
    result = run_volatility_with_cache(dump_path, plugin)

    # 기존 인터페이스 호환성을 위한 변환
    if result["status"] == "error":
        error_msg = result["error"]
        if result.get("from_cache"):
            error_msg = f"[CACHED] {error_msg}"
        return plugin, None, error_msg
    else:
        df = None
        if "result" in result and isinstance(result["result"], list) and len(result["result"]) > 0:
            try:
                df = pd.DataFrame(result["result"])
            except Exception as e:
                log_with_time(f"⚠️ DataFrame creation failed for {plugin}: {e}")
        elif "result" in result and isinstance(result["result"], dict) and result["result"].get("text_output"):
            # 텍스트 출력을 DataFrame으로 변환
            df = pd.DataFrame({"output": [result["result"]["text_output"]]})

        return plugin, df, None


def run_pid_plugin(plugin_name: str, dump_path: str, pid: str, _mtime=None):
    """PID 기반 분석"""
    result = run_volatility_with_cache(dump_path, plugin_name, int(pid))

    if result["status"] == "error":
        error_msg = result["error"]
        if result.get("from_cache"):
            error_msg = f"[CACHED] {error_msg}"
        raise RuntimeError(error_msg)

    # DataFrame 변환
    if "result" in result and isinstance(result["result"], list):
        try:
            return pd.DataFrame(result["result"])
        except:
            pass

    return pd.DataFrame({"Info": [f"PID {pid}에 대한 결과가 없습니다."]})