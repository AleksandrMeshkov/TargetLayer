import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class ResponseCache:
    
    def __init__(self):
        self.cache: Dict[str, tuple] = {} 
        self.ttl_seconds = 3600
    
    def generate_key(self, message: str, temperature: float, max_tokens: int) -> str:
        key_data = f"{message}_{temperature}_{max_tokens}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Dict]:
        if key not in self.cache:
            return None
        
        response, timestamp = self.cache[key]
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self.cache[key]
            return None
        
        return response
    
    def set(self, key: str, response: Dict) -> None:
        self.cache[key] = (response, datetime.now())
    
    def clear(self) -> None:
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        return {
            "cached_items": len(self.cache),
            "ttl_seconds": self.ttl_seconds
        }


class PerformanceOptimizer:
    
    @staticmethod
    def optimize_message_for_speed(message: str) -> str:
        if len(message) > 1000:
            return message[:1000]
        return message.strip()
    
    @staticmethod
    def get_optimal_tokens(task_type: str) -> int:
        recommendations = {
            "chat": 512,
            "decompose_goal": 1024,
            "generate_tasks": 1024,
            "analyze": 768,
        }
        return recommendations.get(task_type, 512)
    
    @staticmethod
    def get_optimal_temperature(task_type: str) -> float:
        recommendations = {
            "chat": 0.7,
            "decompose_goal": 0.5,
            "generate_tasks": 0.6,
            "analyze": 0.3,
        }
        return recommendations.get(task_type, 0.5)


class ResponseFormatter:
    @staticmethod
    def truncate_if_needed(response: str, max_length: int = 5000) -> str:
        if len(response) > max_length:
            return response[:max_length] + "\n\n[Ответ обрезан из-за длины]"
        return response
    
    @staticmethod
    def add_response_metadata(
        response: str,
        tokens_used: int,
        processing_time: float,
        model: str,
        cached: bool = False
    ) -> Dict:
        return {
            "response": response,
            "tokens_used": tokens_used,
            "processing_time": processing_time,
            "model": model,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        }


class QuickResponseMode:
    QUICK_MODE_CONFIG = {
        "max_tokens": 256,      # Минимум для быстрого ответа
        "temperature": 0.3,      # Точный ответ
        "timeout": 30            # 30 секунд max
    }
    
    BALANCED_MODE_CONFIG = {
        "max_tokens": 512,
        "temperature": 0.6,
        "timeout": 60
    }
    
    DETAILED_MODE_CONFIG = {
        "max_tokens": 2048,
        "temperature": 0.7,
        "timeout": 120
    }
    
    @staticmethod
    def get_config(mode: str = "balanced") -> Dict:
        configs = {
            "quick": QuickResponseMode.QUICK_MODE_CONFIG,
            "balanced": QuickResponseMode.BALANCED_MODE_CONFIG,
            "detailed": QuickResponseMode.DETAILED_MODE_CONFIG,
        }
        return configs.get(mode, QuickResponseMode.BALANCED_MODE_CONFIG)


response_cache = ResponseCache()
optimizer = PerformanceOptimizer()
formatter = ResponseFormatter()
