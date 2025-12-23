import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta


class ResponseCache:
    """Simple in-memory response cache with TTL (time-to-live) support.
    
    Uses MD5 hash of message+temperature+max_tokens as key. Automatically
    expires entries after ttl_seconds.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize cache.
        
        Args:
            ttl_seconds: Cache entry lifetime in seconds (default: 1 hour).
        """
        self.cache: Dict[str, tuple] = {}
        self.ttl_seconds = ttl_seconds

    def generate_key(self, message: str, temperature: float, max_tokens: int) -> str:
        """Generate cache key from message and parameters."""
        key_data = f"{message}_{temperature}_{max_tokens}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Dict]:
        """Retrieve cached response if not expired.
        
        Returns None if key not found or TTL exceeded.
        """
        if key not in self.cache:
            return None

        response, timestamp = self.cache[key]
        if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds):
            del self.cache[key]
            return None

        return response

    def set(self, key: str, response: Dict) -> None:
        """Store response with current timestamp."""
        self.cache[key] = (response, datetime.now())

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

    def get_stats(self) -> Dict:
        """Return cache statistics."""
        return {
            "cached_items": len(self.cache),
            "ttl_seconds": self.ttl_seconds
        }


class PerformanceOptimizer:
    """Suggest optimal parameters (tokens, temperature) for different task types."""

    @staticmethod
    def get_optimal_tokens(task_type: str) -> int:
        """Get recommended max_tokens for a task type.
        
        Args:
            task_type: One of 'chat', 'decompose_goal', 'generate_tasks', 'analyze'.
        
        Returns:
            Recommended token count (default 512).
        """
        recommendations = {
            "chat": 512,
            "decompose_goal": 1024,
            "generate_tasks": 1024,
            "analyze": 768,
        }
        return recommendations.get(task_type, 512)

    @staticmethod
    def get_optimal_temperature(task_type: str) -> float:
        """Get recommended temperature for a task type.
        
        Args:
            task_type: One of 'chat', 'decompose_goal', 'generate_tasks', 'analyze'.
        
        Returns:
            Recommended temperature (default 0.5).
        """
        recommendations = {
            "chat": 0.7,
            "decompose_goal": 0.5,
            "generate_tasks": 0.6,
            "analyze": 0.3,
        }
        return recommendations.get(task_type, 0.5)


class ResponseFormatter:
    """Format and truncate AI responses for safe output."""

    @staticmethod
    def truncate_if_needed(response: str, max_length: int = 5000) -> str:
        """Truncate response if it exceeds max_length.
        
        Args:
            response: AI response text.
            max_length: Maximum allowed length (default 5000).
        
        Returns:
            Truncated response with notice if trimmed.
        """
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
        """Wrap response with metadata.
        
        Args:
            response: AI response text.
            tokens_used: Number of tokens consumed.
            processing_time: Request duration in seconds.
            model: Model identifier.
            cached: Whether response came from cache.
        
        Returns:
            Dictionary with response, metadata, and ISO timestamp.
        """
        return {
            "response": response,
            "tokens_used": tokens_used,
            "processing_time": processing_time,
            "model": model,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        }


# Singleton instances used by AIService and routes
response_cache = ResponseCache()
optimizer = PerformanceOptimizer()
formatter = ResponseFormatter()
