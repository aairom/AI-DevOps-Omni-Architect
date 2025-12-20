"""
Async helper utilities for Streamlit integration
Provides utilities to run async functions in Streamlit's synchronous context
"""
import asyncio
import logging
from typing import Any, Callable, Coroutine
from functools import wraps
import streamlit as st

logger = logging.getLogger(__name__)

def run_async(coro: Coroutine) -> Any:
    """
    Run an async coroutine in a synchronous context
    Handles event loop management for Streamlit
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async function: {e}")
        raise
    finally:
        # Don't close the loop as it might be reused
        pass

def async_to_sync(async_func: Callable) -> Callable:
    """
    Decorator to convert async function to sync for Streamlit
    Usage:
        @async_to_sync
        async def my_async_function():
            await something()
    """
    @wraps(async_func)
    def wrapper(*args, **kwargs):
        return run_async(async_func(*args, **kwargs))
    return wrapper

class AsyncStreamlitRunner:
    """
    Context manager for running async operations in Streamlit
    Provides better control over event loop lifecycle
    """
    
    def __init__(self):
        self.loop = None
    
    def __enter__(self):
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_running():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Keep loop open for reuse
        pass
    
    def run(self, coro: Coroutine) -> Any:
        """Run a coroutine in the managed event loop"""
        try:
            return self.loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Error in async runner: {e}")
            raise

async def gather_with_progress(tasks: list[Coroutine], progress_callback: Callable[[int, int], None] = None) -> list[Any]:
    """
    Run multiple async tasks with progress tracking
    
    Args:
        tasks: List of coroutines to execute
        progress_callback: Optional callback function(completed, total)
    
    Returns:
        List of results from all tasks
    """
    total = len(tasks)
    completed = 0
    results = []
    
    for task in asyncio.as_completed(tasks):
        try:
            result = await task
            results.append(result)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
        except Exception as e:
            logger.error(f"Task failed: {e}")
            results.append(None)
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
    
    return results

def create_async_task_queue(max_concurrent: int = 3):
    """
    Create a task queue for managing concurrent async operations
    
    Args:
        max_concurrent: Maximum number of concurrent tasks
    
    Returns:
        Tuple of (queue, semaphore)
    """
    queue = asyncio.Queue()
    semaphore = asyncio.Semaphore(max_concurrent)
    return queue, semaphore

async def process_with_semaphore(coro: Coroutine, semaphore: asyncio.Semaphore) -> Any:
    """
    Process a coroutine with semaphore-based concurrency control
    
    Args:
        coro: Coroutine to execute
        semaphore: Semaphore for concurrency control
    
    Returns:
        Result from the coroutine
    """
    async with semaphore:
        return await coro

class AsyncBatchProcessor:
    """
    Batch processor for async operations with concurrency control
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(self, items: list[Any], processor: Callable[[Any], Coroutine]) -> list[Any]:
        """
        Process a batch of items concurrently with rate limiting
        
        Args:
            items: List of items to process
            processor: Async function to process each item
        
        Returns:
            List of results
        """
        tasks = [
            process_with_semaphore(processor(item), self.semaphore)
            for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Streamlit-specific async utilities
def st_async_spinner(message: str):
    """
    Decorator for showing Streamlit spinner during async operations
    
    Usage:
        @st_async_spinner("Processing...")
        async def my_async_function():
            await something()
    """
    def decorator(async_func: Callable) -> Callable:
        @wraps(async_func)
        def wrapper(*args, **kwargs):
            with st.spinner(message):
                return run_async(async_func(*args, **kwargs))
        return wrapper
    return decorator

async def async_retry(coro: Coroutine, max_retries: int = 3, delay: float = 1.0) -> Any:
    """
    Retry an async operation with exponential backoff
    
    Args:
        coro: Coroutine to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (doubles each time)
    
    Returns:
        Result from successful execution
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_retries):
        try:
            return await coro
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(current_delay)
                current_delay *= 2
    
    raise last_exception

# Made with Bob