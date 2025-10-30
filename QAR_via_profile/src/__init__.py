"""
QAR via Profile - 基于用户画像的问答推理生成器
"""

__version__ = "1.0.0"
__author__ = "QAR Team"
__description__ = "基于用户画像的问答推理生成器"

from .core.qa_generator import QARGenerator
from .core.formatter import QARFormatter
from .quality_control import QualityController
from .llm_interface import LLMInterface

__all__ = [
    'QARGenerator',
    'QARFormatter', 
    'QualityController',
    'LLMInterface'
]
