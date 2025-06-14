#!/usr/bin/env python3
"""
Analysis Caching Layer for LLMdiver
Provides intelligent caching for expensive operations like repomix, AST parsing, and embeddings.
"""

import hashlib
import json
import logging
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)

class AnalysisCache:
    """Simple file-based caching system for analysis operations"""
    
    def __init__(self, cache_dir: str = ".llmdiver/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # TTL values in seconds
        self.ttl = {
            'repomix': 3600,      # 1 hour
            'ast': 86400,         # 24 hours  
            'embeddings': 604800, # 7 days
            'analysis': 1800,     # 30 minutes
            'git_status': 300     # 5 minutes
        }
        
        # Initialize cache stats
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        logger.info(f"Initialized analysis cache at {self.cache_dir}")
    
    def _generate_key(self, data: Union[str, Dict]) -> str:
        """Generate a consistent cache key from input data"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_cache_file(self, key: str, cache_type: str) -> Path:
        """Get cache file path for given key and type"""
        return self.cache_dir / f"{cache_type}_{key}.cache"
    
    def _is_expired(self, cache_file: Path, ttl_type: str) -> bool:
        """Check if cache file is expired"""
        if not cache_file.exists():
            return True
        
        file_age = time.time() - cache_file.stat().st_mtime
        max_age = self.ttl.get(ttl_type, 3600)
        
        return file_age > max_age
    
    def get(self, key: str, cache_type: str) -> Optional[Any]:
        """Get item from cache"""
        cache_file = self._get_cache_file(key, cache_type)
        
        if self._is_expired(cache_file, cache_type):
            if cache_file.exists():
                cache_file.unlink()  # Remove expired cache
                self.stats['evictions'] += 1
            self.stats['misses'] += 1
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            self.stats['hits'] += 1
            logger.debug(f"Cache hit for {cache_type}:{key}")
            return data
        except Exception as e:
            logger.warning(f"Failed to read cache {cache_file}: {e}")
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, cache_type: str) -> None:
        """Set item in cache"""
        cache_file = self._get_cache_file(key, cache_type)
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            logger.debug(f"Cached {cache_type}:{key}")
        except Exception as e:
            logger.warning(f"Failed to write cache {cache_file}: {e}")
    
    def get_or_compute(self, key: str, compute_fn, cache_type: str) -> Any:
        """Get from cache or compute if not available"""
        cached_value = self.get(key, cache_type)
        if cached_value is not None:
            return cached_value
        
        # Compute value
        logger.debug(f"Computing {cache_type}:{key}")
        value = compute_fn()
        
        # Cache the result
        self.set(key, value, cache_type)
        
        return value
    
    def invalidate(self, pattern: str = "*") -> int:
        """Invalidate cache entries matching pattern"""
        count = 0
        for cache_file in self.cache_dir.glob(f"{pattern}.cache"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        logger.info(f"Invalidated {count} cache entries")
        return count
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': round(hit_rate, 2),
            'total_files': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        }
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            # Extract cache type from filename
            cache_type = cache_file.stem.split('_', 1)[0]
            if self._is_expired(cache_file, cache_type):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove expired cache {cache_file}: {e}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")
        return count

# Cache decorators for easy use
def cached_operation(cache_type: str, key_func=None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance (assumes it's available globally or as class attribute)
            cache = getattr(args[0], 'cache', None) if args else None
            if not cache:
                # Fallback to function execution without caching
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default key generation from function name and args
                key_data = f"{func.__name__}:{str(args[1:])}{str(kwargs)}"
                key = cache._generate_key(key_data)
            
            return cache.get_or_compute(key, lambda: func(*args, **kwargs), cache_type)
        
        return wrapper
    return decorator

class CachedRepomixProcessor:
    """Enhanced RepomixProcessor with intelligent caching"""
    
    def __init__(self, original_processor, cache_dir: str = ".llmdiver/cache"):
        self.processor = original_processor
        self.cache = AnalysisCache(cache_dir)
        logger.info("Initialized cached repomix processor")
    
    def run_repomix_analysis_cached(self, repo_path: str) -> str:
        """Cached version of repomix analysis"""
        # Generate cache key based on repo state
        key_data = {
            'repo_path': repo_path,
            'git_head': self._get_git_head(repo_path),
            'file_count': self._get_file_count(repo_path)
        }
        key = self.cache._generate_key(str(key_data))
        
        def compute_repomix():
            return self.processor.run_repomix_analysis(repo_path)
        
        return self.cache.get_or_compute(key, compute_repomix, 'repomix')
    
    def run_repomix_diff_analysis_cached(self, repo_path: str) -> str:
        """Cached version of diff analysis - shorter TTL since diffs change often"""
        # For diff analysis, include current diff in key
        key_data = {
            'repo_path': repo_path,
            'git_diff': self._get_git_diff_summary(repo_path)
        }
        key = self.cache._generate_key(str(key_data))
        
        def compute_diff():
            return self.processor.run_repomix_diff_analysis(repo_path)
        
        # Use shorter TTL for diff analysis
        result = self.cache.get(key, 'analysis')
        if result is None:
            result = compute_diff()
            self.cache.set(key, result, 'analysis')
        
        return result
    
    def _get_git_head(self, repo_path: str) -> str:
        """Get current git HEAD for cache invalidation"""
        try:
            import git
            repo = git.Repo(repo_path)
            return repo.head.commit.hexsha[:8]
        except:
            return "unknown"
    
    def _get_git_diff_summary(self, repo_path: str) -> str:
        """Get git diff summary for cache key"""
        try:
            import git
            repo = git.Repo(repo_path)
            # Get summary of changed files
            changed_files = [item.a_path for item in repo.index.diff(None)]
            untracked = repo.untracked_files
            return f"changed:{len(changed_files)},untracked:{len(untracked)}"
        except:
            return "unknown"
    
    def _get_file_count(self, repo_path: str) -> int:
        """Get rough file count for cache validation"""
        try:
            # Count Python, JS, TS files
            repo_path_obj = Path(repo_path)
            count = 0
            for pattern in ['**/*.py', '**/*.js', '**/*.ts', '**/*.sh']:
                count += len(list(repo_path_obj.glob(pattern)))
            return count
        except:
            return 0

# Example usage and integration
if __name__ == "__main__":
    # Test the caching system
    cache = AnalysisCache("/tmp/test_cache")
    
    # Test basic operations
    cache.set("test_key", {"data": "test_value"}, "test")
    result = cache.get("test_key", "test")
    print(f"Cache test result: {result}")
    
    # Test get_or_compute
    def expensive_computation():
        time.sleep(1)  # Simulate expensive operation
        return "computed_result"
    
    # First call - should compute
    start_time = time.time()
    result1 = cache.get_or_compute("expensive_key", expensive_computation, "test")
    time1 = time.time() - start_time
    
    # Second call - should use cache
    start_time = time.time()
    result2 = cache.get_or_compute("expensive_key", expensive_computation, "test")
    time2 = time.time() - start_time
    
    print(f"First call: {result1} ({time1:.3f}s)")
    print(f"Second call: {result2} ({time2:.3f}s)")
    print(f"Cache stats: {cache.get_stats()}")