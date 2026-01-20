import asyncio
import httpx
from typing import Any, Callable, Optional, TypeVar, Coroutine, Dict
from loguru import logger

T = TypeVar("T")

class BaseClient:
    """
    Abstract base client providing common utilities for async task polling and HTTP requests.
    """

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip('/') if base_url else ""

    def _get_headers(self) -> Dict[str, str]:
        """
        Default header provider for _request. Subclasses can override this 
        to provide dynamic headers (e.g., JWT tokens).
        """
        return {}

    async def _request(
        self, 
        method: str, 
        path: str, 
        headers: Optional[Dict[str, str]] = None, 
        timeout: float = 30.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Internal helper for making asynchronous HTTP requests using httpx.
        Automatically joins self.base_url and uses self._get_headers().
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Relative path or full URL.
            headers: Optional dictionary of HTTP headers (merges with _get_headers).
            timeout: Request timeout in seconds.
            **kwargs: Extra arguments passed to httpx.request (e.g., json, params).
            
        Returns:
            The JSON response as a dictionary.
        """
        # 1. Prepare URL
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        
        # 2. Prepare Headers
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)
            
        # 3. Perform Request
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url, headers=request_headers, **kwargs)
            response.raise_for_status()
            return response.json()

    async def poll_task(
        self, 
        task_id: str, 
        get_status_func: Callable[[str], Coroutine[Any, Any, Any]],
        check_success_func: Callable[[Any], bool],
        check_failed_func: Callable[[Any], bool],
        callback: Optional[Callable[[Any], Coroutine[Any, Any, None]]] = None,
        interval: int = 2,
        timeout: int = 300
    ) -> Any:
        """
        Generic polling mechanism for async long-running tasks.
        
        Args:
            task_id: The unique ID of the task to poll.
            get_status_func: Async function to fetch current task status/response.
            check_success_func: Function to determine if task succeeded from response.
            check_failed_func: Function to determine if task failed from response.
            callback: Optional async callback triggered on each poll cycle.
            interval: Seconds to wait between retries.
            timeout: Maximum seconds to wait before raising TimeoutError.
            
        Returns:
            The final response object when successful or failed.
            
        Raises:
            TimeoutError: If timeout is reached.
        """
        logger.info(f"Starting polling for task: {task_id} (timeout={timeout}s)")
        
        start_time = asyncio.get_running_loop().time()
        
        while (asyncio.get_running_loop().time() - start_time) < timeout:
            try:
                # 1. Fetch current status
                response = await get_status_func(task_id)
                
                # 2. Trigger optional callback
                if callback:
                    await callback(response)
                
                # 3. Check terminal states
                if check_success_func(response):
                    logger.info(f"Task {task_id} succeeded.")
                    return response
                
                if check_failed_func(response):
                    logger.warning(f"Task {task_id} failed or cancelled.")
                    return response
                
                # 4. Wait for next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error during polling for task {task_id}: {e}")
                # Optional: decide whether to break or continue on transient errors
                # For now, we continue to be robust
                await asyncio.sleep(interval)
        
        raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds.")

