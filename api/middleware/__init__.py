"""
中间件模块
"""
from .error_handler import register_error_handlers
from .cors import setup_cors

__all__ = [
    'register_error_handlers',
    'setup_cors',
]

