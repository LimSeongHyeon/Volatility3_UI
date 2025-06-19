import asyncio
import threading
import time
from typing import Dict, List, Callable, Any
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from .volatility import run_volatility_process
from UI.config import plugin_categories


class AsyncAnalysisManager:
    def __init__(self):
        self.running_tasks = {}
        self.completed_tasks = {}
        self.task_progress = {}

    def start_category_analysis_async(self, dump_path: str, selected_category: str, max_workers: int):
        """비동기로 카테고리 분석 시작"""
        if selected_category in self.running_tasks:
            return False  # 이미 실행 중

        # 세션 상태 초기화
        self._initialize_session_state(selected_category)

        # 백그라운드 스레드에서 분석 시작
        thread = threading.Thread(
            target=self._run_analysis_background,
            args=(dump_path, selected_category, max_workers),
            daemon=True
        )
        thread.start()

        self.running_tasks[selected_category] = thread
        return True

    def _initialize_session_state(self, selected_category: str):
        """세션 상태 초기화"""
        plugins_to_run = plugin_categories[selected_category]

        # 기존 결과 삭제
        for emoji, title, plugin in plugins_to_run:
            result_key = f"analysis_results_{selected_category}_{plugin}"
            if result_key in st.session_state:
                del st.session_state[result_key]

        # 진행 상태 초기화
        st.session_state[f"analysis_progress_{selected_category}"] = {
            'total': len(plugins_to_run),
            'completed': 0,
            'current_plugin': None,
            'status': 'running'
        }

    def _run_analysis_background(self, dump_path: str, selected_category: str, max_workers: int):
        """백그라운드에서 분석 실행"""
        try:
            plugins_to_run = plugin_categories[selected_category]
            completed_count = 0
            total_count = len(plugins_to_run)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 모든 작업 제출
                future_to_plugin = {
                    executor.submit(run_volatility_process, plugin, dump_path): (emoji, title, plugin)
                    for emoji, title, plugin in plugins_to_run
                }

                # 완료된 작업 처리
                for future in as_completed(future_to_plugin):
                    emoji, title, plugin = future_to_plugin[future]
                    completed_count += 1

                    try:
                        plugin_name, df, error = future.result()

                        # 결과 저장
                        result_key = f"analysis_results_{selected_category}_{plugin_name}"
                        st.session_state[result_key] = (df, error)

                        # 진행 상태 업데이트
                        st.session_state[f"analysis_progress_{selected_category}"].update({
                            'completed': completed_count,
                            'current_plugin': title,
                            'last_completed': title
                        })

                    except Exception as e:
                        result_key = f"analysis_results_{selected_category}_{plugin}"
                        st.session_state[result_key] = (None, str(e))

            # 완료 처리
            st.session_state[f"analysis_progress_{selected_category}"]["status"] = "completed"
            st.session_state["analysis_running"] = False

            if selected_category in self.running_tasks:
                del self.running_tasks[selected_category]

        except Exception as e:
            st.session_state[f"analysis_progress_{selected_category}"]["status"] = "error"
            st.session_state[f"analysis_progress_{selected_category}"]["error"] = str(e)
            st.session_state["analysis_running"] = False

    def get_progress(self, category: str) -> Dict[str, Any]:
        """진행 상황 반환"""
        return st.session_state.get(f"analysis_progress_{category}", {})

    def is_running(self, category: str) -> bool:
        """분석이 실행 중인지 확인"""
        return category in self.running_tasks

    def stop_analysis(self, category: str):
        """분석 중단 (완전한 중단은 어려우므로 상태만 변경)"""
        if category in self.running_tasks:
            st.session_state[f"analysis_progress_{category}"]["status"] = "stopped"
            st.session_state["analysis_running"] = False


# 전역 분석 매니저 인스턴스
analysis_manager = AsyncAnalysisManager()