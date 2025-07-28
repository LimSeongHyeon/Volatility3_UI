import multiprocessing
import time
import psutil
from typing import Dict, Any
import streamlit as st
from concurrent.futures import ProcessPoolExecutor, as_completed
from .volatility import run_volatility_process
from UI.config import plugin_categories


class ResourceMonitor:
    """시스템 리소스 모니터링 클래스"""

    def __init__(self, cpu_threshold=80, memory_threshold=85):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold

    def get_current_usage(self):
        """현재 CPU/메모리 사용률 반환"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        return cpu_percent, memory_percent

    def is_system_overloaded(self):
        """시스템이 과부하 상태인지 확인"""
        cpu_percent, memory_percent = self.get_current_usage()
        return cpu_percent > self.cpu_threshold or memory_percent > self.memory_threshold

    def get_optimal_workers(self, max_workers):
        """현재 시스템 상태에 따른 최적 워커 수 계산"""
        cpu_percent, memory_percent = self.get_current_usage()

        # CPU 사용률에 따른 조정
        if cpu_percent > 70:
            cpu_factor = 0.5
        elif cpu_percent > 50:
            cpu_factor = 0.7
        else:
            cpu_factor = 1.0

        # 메모리 사용률에 따른 조정
        if memory_percent > 80:
            memory_factor = 0.5
        elif memory_percent > 60:
            memory_factor = 0.7
        else:
            memory_factor = 1.0

        # 더 제한적인 팩터 적용
        adjustment_factor = min(cpu_factor, memory_factor)
        optimal_workers = max(1, int(max_workers * adjustment_factor))

        return optimal_workers


def monitor_resources_worker(queue: multiprocessing.Queue, category: str, stop_event: multiprocessing.Event):
    """별도 프로세스에서 리소스 모니터링"""
    monitor = ResourceMonitor()

    while not stop_event.is_set():
        try:
            cpu_percent, memory_percent = monitor.get_current_usage()

            # 큐에 리소스 정보 전송
            queue.put({
                'type': 'resource_update',
                'category': category,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'timestamp': time.time()
            })

            time.sleep(3)  # 3초마다 모니터링

        except Exception as e:
            queue.put({
                'type': 'error',
                'category': category,
                'error': f"리소스 모니터링 오류: {str(e)}"
            })
            break


def analysis_worker(dump_path: str, selected_category: str, max_workers: int,
                    result_queue: multiprocessing.Queue, progress_queue: multiprocessing.Queue):
    """별도 프로세스에서 분석 실행"""
    try:
        plugins_to_run = plugin_categories[selected_category]
        completed_count = 0
        total_count = len(plugins_to_run)

        # 시작 알림
        progress_queue.put({
            'type': 'start',
            'category': selected_category,
            'total': total_count
        })

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # 모든 작업 제출
            future_to_plugin = {}

            for plugin_data in plugins_to_run:
                if isinstance(plugin_data, dict):
                    # 새로운 딕셔너리 구조
                    emoji = plugin_data['emoji']
                    title = plugin_data['label']
                    plugin = plugin_data['command']
                else:
                    # 기존 튜플 구조
                    emoji, title, plugin = plugin_data

                future = executor.submit(run_volatility_process, plugin, dump_path)
                future_to_plugin[future] = (emoji, title, plugin)

            # 완료된 작업 처리
            for future in as_completed(future_to_plugin):
                emoji, title, plugin = future_to_plugin[future]
                completed_count += 1

                try:
                    plugin_name, df, error = future.result()

                    # 결과를 큐에 전송 (간단한 구조로)
                    result_queue.put({
                        'type': 'result',
                        'category': selected_category,
                        'plugin_name': plugin_name,
                        'plugin': plugin,
                        'title': title,
                        'df': df,
                        'error': error,
                        'from_cache': False  # 일단 기본값
                    })

                    # 진행 상황 업데이트
                    progress_queue.put({
                        'type': 'progress',
                        'category': selected_category,
                        'completed': completed_count,
                        'total': total_count,
                        'current_plugin': title,
                        'last_completed': title
                    })

                except Exception as e:
                    result_queue.put({
                        'type': 'result',
                        'category': selected_category,
                        'plugin_name': plugin,
                        'plugin': plugin,
                        'title': title,
                        'df': None,
                        'error': str(e)
                    })

        # 완료 알림
        progress_queue.put({
            'type': 'completed',
            'category': selected_category,
            'total_time': time.time()
        })

    except Exception as e:
        progress_queue.put({
            'type': 'error',
            'category': selected_category,
            'error': str(e)
        })


class AsyncAnalysisManager:
    def __init__(self):
        self.running_processes = {}
        self.resource_monitors = {}
        self.result_queues = {}
        self.progress_queues = {}
        self.resource_queues = {}
        self.stop_events = {}
        self.resource_monitor = ResourceMonitor()

    def start_category_analysis_async(self, dump_path: str, selected_category: str, max_workers: int):
        """multiprocessing으로 비동기 분석 시작"""
        if selected_category in self.running_processes:
            return False  # 이미 실행 중

        # 시스템 과부하 체크
        if self.resource_monitor.is_system_overloaded():
            st.warning("⚠️ 시스템 리소스 사용률이 높습니다. 분석을 잠시 후 다시 시도하세요.")
            return False

        # 세션 상태 초기화
        self._initialize_session_state(selected_category)

        # 최적 워커 수 계산
        optimal_workers = self.resource_monitor.get_optimal_workers(max_workers)
        if optimal_workers < max_workers:
            st.info(f"💡 시스템 성능을 고려하여 워커 수를 {max_workers}개에서 {optimal_workers}개로 조정했습니다.")

        # 큐 생성
        self.result_queues[selected_category] = multiprocessing.Queue()
        self.progress_queues[selected_category] = multiprocessing.Queue()
        self.resource_queues[selected_category] = multiprocessing.Queue()
        self.stop_events[selected_category] = multiprocessing.Event()

        # 분석 프로세스 시작
        analysis_process = multiprocessing.Process(
            target=analysis_worker,
            args=(dump_path, selected_category, optimal_workers,
                  self.result_queues[selected_category],
                  self.progress_queues[selected_category])
        )
        analysis_process.start()
        self.running_processes[selected_category] = analysis_process

        # 리소스 모니터링 프로세스 시작
        monitor_process = multiprocessing.Process(
            target=monitor_resources_worker,
            args=(self.resource_queues[selected_category],
                  selected_category,
                  self.stop_events[selected_category])
        )
        monitor_process.start()
        self.resource_monitors[selected_category] = monitor_process

        return True

    def _initialize_session_state(self, selected_category: str):
        """세션 상태 초기화"""
        plugins_to_run = plugin_categories[selected_category]

        # 기존 결과 삭제
        for plugin_data in plugins_to_run:
            # 딕셔너리 구조인지 튜플 구조인지 확인
            if isinstance(plugin_data, dict):
                plugin = plugin_data['command']
            else:
                # 튜플 구조 (emoji, title, plugin)
                emoji, title, plugin = plugin_data

            result_key = f"analysis_results_{selected_category}_{plugin}"
            if result_key in st.session_state:
                del st.session_state[result_key]

        # 진행 상태 초기화
        st.session_state[f"analysis_progress_{selected_category}"] = {
            'total': len(plugins_to_run),
            'completed': 0,
            'current_plugin': None,
            'status': 'running',
            'start_time': time.time(),
            'cpu_usage': [],
            'memory_usage': []
        }

    def update_from_queues(self, category: str):
        """큐에서 업데이트 정보 가져오기"""
        # 결과 큐 처리
        try:
            if category in self.result_queues and self.result_queues[category] is not None:
                while not self.result_queues[category].empty():
                    try:
                        data = self.result_queues[category].get_nowait()
                        if data['type'] == 'result':
                            result_key = f"analysis_results_{category}_{data['plugin_name']}"
                            st.session_state[result_key] = (data['df'], data['error'])
                    except:
                        break
        except Exception as e:
            print(f"Error processing result queue for {category}: {e}")

        # 진행 상황 큐 처리
        try:
            if category in self.progress_queues and self.progress_queues[category] is not None:
                while not self.progress_queues[category].empty():
                    try:
                        data = self.progress_queues[category].get_nowait()
                        progress_key = f"analysis_progress_{category}"

                        if data['type'] == 'progress':
                            if progress_key in st.session_state:
                                st.session_state[progress_key].update({
                                    'completed': data['completed'],
                                    'current_plugin': data['current_plugin'],
                                    'last_completed': data['last_completed']
                                })
                        elif data['type'] == 'completed':
                            if progress_key in st.session_state:
                                st.session_state[progress_key]['status'] = 'completed'
                                st.session_state[progress_key]['total_time'] = data.get('total_time', time.time())
                            st.session_state["analysis_running"] = False
                            self._cleanup_category(category)
                        elif data['type'] == 'error':
                            if progress_key in st.session_state:
                                st.session_state[progress_key]['status'] = 'error'
                                st.session_state[progress_key]['error'] = data['error']
                            st.session_state["analysis_running"] = False
                            self._cleanup_category(category)
                    except:
                        break
        except Exception as e:
            print(f"Error processing progress queue for {category}: {e}")

        # 리소스 큐 처리
        try:
            if category in self.resource_queues and self.resource_queues[category] is not None:
                while not self.resource_queues[category].empty():
                    try:
                        data = self.resource_queues[category].get_nowait()
                        if data['type'] == 'resource_update':
                            progress_key = f"analysis_progress_{category}"
                            if progress_key in st.session_state:
                                st.session_state[progress_key]['cpu_usage'].append(data['cpu_percent'])
                                st.session_state[progress_key]['memory_usage'].append(data['memory_percent'])

                                # 최근 10개 데이터만 유지
                                if len(st.session_state[progress_key]['cpu_usage']) > 10:
                                    st.session_state[progress_key]['cpu_usage'] = st.session_state[progress_key][
                                                                                      'cpu_usage'][-10:]
                                    st.session_state[progress_key]['memory_usage'] = st.session_state[progress_key][
                                                                                         'memory_usage'][-10:]
                    except:
                        break
        except Exception as e:
            print(f"Error processing resource queue for {category}: {e}")

    def _cleanup_category(self, category: str):
        """카테고리 정리"""
        try:
            if category in self.running_processes:
                process = self.running_processes[category]
                if process and process.is_alive():
                    process.terminate()
                    process.join(timeout=5)  # 5초 대기
                    if process.is_alive():
                        process.kill()  # 강제 종료
                del self.running_processes[category]
        except Exception as e:
            print(f"Error cleaning up analysis process for {category}: {e}")

        try:
            if category in self.resource_monitors:
                if category in self.stop_events:
                    self.stop_events[category].set()

                monitor = self.resource_monitors[category]
                if monitor and monitor.is_alive():
                    monitor.terminate()
                    monitor.join(timeout=3)
                    if monitor.is_alive():
                        monitor.kill()
                del self.resource_monitors[category]
        except Exception as e:
            print(f"Error cleaning up monitor process for {category}: {e}")

        # 큐들과 이벤트 정리
        for queue_dict, name in [(self.result_queues, "result"),
                                 (self.progress_queues, "progress"),
                                 (self.resource_queues, "resource")]:
            try:
                if category in queue_dict:
                    del queue_dict[category]
            except Exception as e:
                print(f"Error cleaning up {name} queue for {category}: {e}")

        try:
            if category in self.stop_events:
                del self.stop_events[category]
        except Exception as e:
            print(f"Error cleaning up stop event for {category}: {e}")

    def get_progress(self, category: str) -> Dict[str, Any]:
        """진행 상황 반환"""
        try:
            self.update_from_queues(category)
        except Exception as e:
            print(f"Error updating queues for {category}: {e}")

        progress_key = f"analysis_progress_{category}"
        return st.session_state.get(progress_key, {})

    def get_resource_info(self, category: str) -> Dict[str, Any]:
        """리소스 사용 정보 반환"""
        try:
            self.update_from_queues(category)
        except Exception as e:
            print(f"Error updating queues for resource info {category}: {e}")

        progress_data = self.get_progress(category)
        cpu_usage = progress_data.get('cpu_usage', [])
        memory_usage = progress_data.get('memory_usage', [])

        if cpu_usage and memory_usage:
            return {
                'current_cpu': cpu_usage[-1] if cpu_usage else 0,
                'current_memory': memory_usage[-1] if memory_usage else 0,
                'avg_cpu': sum(cpu_usage) / len(cpu_usage),
                'avg_memory': sum(memory_usage) / len(memory_usage),
                'max_cpu': max(cpu_usage),
                'max_memory': max(memory_usage)
            }
        else:
            try:
                current_cpu, current_memory = self.resource_monitor.get_current_usage()
                return {
                    'current_cpu': current_cpu,
                    'current_memory': current_memory,
                    'avg_cpu': current_cpu,
                    'avg_memory': current_memory,
                    'max_cpu': current_cpu,
                    'max_memory': current_memory
                }
            except Exception as e:
                print(f"Error getting current resource usage: {e}")
                return {
                    'current_cpu': 0,
                    'current_memory': 0,
                    'avg_cpu': 0,
                    'avg_memory': 0,
                    'max_cpu': 0,
                    'max_memory': 0
                }

    def is_running(self, category: str) -> bool:
        """분석이 실행 중인지 확인"""
        try:
            self.update_from_queues(category)
        except Exception as e:
            print(f"Queue update failed for {category}: {e}")

        # 프로세스가 실제로 살아있는지 확인
        if category in self.running_processes:
            process = self.running_processes[category]
            if process and process.is_alive():
                return True
            else:
                # 죽은 프로세스 정리 및 상태 업데이트
                print(f"Process for {category} is dead, cleaning up...")
                st.session_state["analysis_running"] = False
                progress_key = f"analysis_progress_{category}"
                if progress_key in st.session_state:
                    if st.session_state[progress_key].get('status') == 'running':
                        st.session_state[progress_key]['status'] = 'completed'
                self._cleanup_category(category)
                return False

        return False

    def stop_analysis(self, category: str):
        """분석 중단"""
        if category in self.running_processes:
            progress_key = f"analysis_progress_{category}"
            if progress_key in st.session_state:
                st.session_state[progress_key]["status"] = "stopped"
            st.session_state["analysis_running"] = False
            self._cleanup_category(category)


# 전역 분석 매니저 인스턴스
analysis_manager = AsyncAnalysisManager()