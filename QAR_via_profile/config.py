"""
QAR生成配置文件
"""

# 支持的QAR类型
SUPPORTED_QA_TYPES = [
    'profile_adaptive',        # 基于角色配置的自适应QAR
    'constraint_qa',           # 约束型内容生成（间接关联）
    'progress_continuation_qa', # 历史目标承接与进度延续
    'conflict_resolution_qa',   # 矛盾记忆的推理选择
    'active_reminder_qa'       # 主动提醒/偏好矫正
]
# OpenRouter API配置
OPENROUTER_API_KEY = "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"

# 使用Qwen3-235B模型（根据同事提供的配置）
OPENROUTER_MODEL = "qwen/qwen3-235b-a22b-2507"
MAX_TOKENS_DEFAULT = 10000  # 大幅增加token上限，避免大项目生成失败

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_SITE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_APP_NAME = "Memory System"

# 默认配置
DEFAULT_CONFIG = {
    'model': OPENROUTER_MODEL,  # 使用OpenRouter模型
    'output_dir': './output',
    'base_name': 'qar_results',
    'qa_types': SUPPORTED_QA_TYPES,
    'verbose': False,
    'apply_quality_control': False,  # 默认关闭质量控制，便于调试
    'export_raw': True,  # 默认导出原始内容
    'max_tokens': MAX_TOKENS_DEFAULT
}

# OpenRouter配置
OPENROUTER_CONFIG = {
    'api_key': OPENROUTER_API_KEY,
    'base_url': OPENROUTER_BASE_URL,
    'model': OPENROUTER_MODEL,
    'max_tokens': MAX_TOKENS_DEFAULT,
    'app_name': OPENROUTER_APP_NAME
}

# 关键信息字段要求
REQUIRED_KEY_INFO_FIELDS = {
    'profile_adaptive': ['complex_question', 'ground_truth_answer', 'supporting_evidence', 'profile_data'],
    'constraint_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence'],
    'progress_continuation_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence'],
    'conflict_resolution_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence'],
    'active_reminder_qa': ['complex_question', 'ground_truth_answer', 'supporting_evidence']
}

# 可选字段
OPTIONAL_KEY_INFO_FIELDS = {
    'profile_adaptive': ['topic'],
    'constraint_qa': ['topic'],
    'progress_continuation_qa': ['topic'],
    'conflict_resolution_qa': ['topic'],
    'active_reminder_qa': ['topic']
}

# 质量控制配置
QUALITY_CONTROL_CONFIG = {
    'max_attempts': 3,           # 问题泄露检测最大尝试次数
    'max_variance': 0.3,         # 选项长度最大方差比例
    'min_question_length': 10,   # 最小问题长度
    'max_question_length': 500, # 最大问题长度
    'max_option_length_ratio': 3 # 最大选项长度比例
}

# 输出格式配置
OUTPUT_CONFIG = {
    'json_indent': 2,
    'csv_encoding': 'utf-8',
    'backup_existing': True
}
