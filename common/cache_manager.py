import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd


class SimpleCache:
    """간단한 분석 결과 캐싱"""

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, file_path: str, command: str, pid: Optional[int] = None) -> str:
        """캐시 키 생성"""
        # 파일 정보
        try:
            stat = os.stat(file_path)
            file_info = f"{Path(file_path).name}_{stat.st_size}_{stat.st_mtime}"
        except:
            file_info = Path(file_path).name

        # 분석 정보
        analysis_info = f"{command}_{pid if pid else 'no_pid'}"

        # 해시 생성
        hash_string = f"{file_info}_{analysis_info}"
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> Path:
        """캐시 파일 경로"""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, file_path: str, command: str, pid: Optional[int] = None) -> Optional[dict]:
        """캐시 조회"""
        cache_key = self._get_cache_key(file_path, command, pid)
        cache_file = self._get_cache_file(cache_key)

        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None

    def save(self, file_path: str, command: str, result: dict, pid: Optional[int] = None):
        """캐시 저장"""
        cache_key = self._get_cache_key(file_path, command, pid)
        cache_file = self._get_cache_file(cache_key)

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        except Exception as e:
            print(f"Cache save failed: {e}")

    def clear(self) -> int:
        """캐시 정리"""
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
        except:
            pass
        return count

    def get_stats(self) -> dict:
        """캐시 통계"""
        try:
            files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files)
            return {
                'count': len(files),
                'size_mb': total_size / (1024 * 1024)
            }
        except:
            return {'count': 0, 'size_mb': 0}


# 전역 캐시 인스턴스
simple_cache = SimpleCache()