import pytest
import sys
import os

# 将 src 目录添加到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# 这里可以添加全局 fixtures 或其他测试配置