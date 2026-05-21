"""通用工具函数。"""

import uuid
from datetime import datetime


def generate_id() -> str:
    """生成短 UUID。"""
    return str(uuid.uuid4())[:8]


def get_timestamp() -> str:
    """获取当前时间戳。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
