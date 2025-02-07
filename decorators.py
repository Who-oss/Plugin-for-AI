import functools
import time
from typing import Callable, Any
import logging

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
    """重试装饰器，使用指数退避策略"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logging.warning(f"第 {retry + 1} 次尝试失败: {str(e)}")
                    
                    if retry < max_retries - 1:
                        sleep_time = delay * (2 ** retry)  # 指数退避
                        logging.info(f"等待 {sleep_time} 秒后重试...")
                        time.sleep(sleep_time)
                        
            logging.error(f"所有重试都失败了: {str(last_exception)}")
            raise last_exception
            
        return wrapper
    return decorator 