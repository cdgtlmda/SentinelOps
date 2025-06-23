"""
Connection pool management for Gemini models
"""

import threading
from typing import Any, Dict, List, Optional

from .common import logger, genai


class ConnectionPool:
    """Manages a pool of Gemini model instances for concurrent requests"""

    def __init__(
        self,
        model_name: str,
        pool_size: int = 5,
        safety_settings: Optional[Dict[str, Any]] = None,
    ):
        self.model_name = model_name
        self.pool_size = pool_size
        self.safety_settings = safety_settings
        self.pool: List[Any] = []
        self.available = threading.Semaphore(pool_size)
        self.lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Initialize the connection pool with model instances"""
        for _ in range(self.pool_size):
            model = genai.GenerativeModel(
                self.model_name, safety_settings=self.safety_settings
            )
            self.pool.append(model)
        logger.info(
            "Initialized connection pool with %s model instances", self.pool_size
        )

    def acquire(self) -> Any:
        """Acquire a model instance from the pool"""
        self.available.acquire()
        with self.lock:
            return self.pool.pop()

    def release(self, model: Any) -> None:
        """Release a model instance back to the pool"""
        with self.lock:
            self.pool.append(model)
        self.available.release()

    def resize(self, new_size: int) -> None:
        """Resize the connection pool"""
        with self.lock:
            current_size = len(self.pool)
            if new_size > current_size:
                # Add more connections
                for _ in range(new_size - current_size):
                    model = genai.GenerativeModel(
                        self.model_name, safety_settings=self.safety_settings
                    )
                    self.pool.append(model)
                    self.available.release()
            elif new_size < current_size:
                # Remove connections
                for _ in range(current_size - new_size):
                    if self.pool:
                        self.pool.pop()
                        self.available.acquire()

            self.pool_size = new_size
            logger.info("Resized connection pool to %s instances", new_size)
