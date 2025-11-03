"""
配置文件
存储所有系统配置参数
"""

import os
from dotenv import load_dotenv

# ========== OpenAI API 配置 ==========

# OpenRouter Base URL
OPENAI_BASE_URL = "https://openrouter.ai/api/v1"

# 方式1：直接在这里设置 API Key（推荐用于测试）
# 使用 OpenRouter API Key
OPENAI_API_KEY = "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"

# 方式2：从环境变量读取（备选方案，如果上面为空则使用此方式）
if not OPENAI_API_KEY:
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenRouter model name (use OpenAI models through OpenRouter)
OPENAI_MODEL = "google/gemini-2.5-pro"  # Using Gemini 2.5 Pro through OpenRouter

# API 调用参数
# 注意：GPT-5 模型对某些参数有限制，只支持默认值
API_PARAMS = {
    "temperature": 1,
    "max_completion_tokens": 32000,
}

# API 重试配置
MAX_RETRIES = 10  # 最大重试次数（由于GPT-5连接不稳定，增加到10次）
RETRY_DELAY = 2  # 重试延迟（秒）

# ========== 数据生成配置 ==========

# 员工数量配置
TOTAL_EMPLOYEES = 300  # 正式版本：300个员工，分批生成
TOP_LEADER_COUNT = 1  # 大领导数量
TEAM_LEADER_COUNT = 7  # 团队领导数量（每个团队1个）
REGULAR_EMPLOYEE_COUNT = TOTAL_EMPLOYEES - TOP_LEADER_COUNT - TEAM_LEADER_COUNT  # 292个普通员工

# 团队配置
TEAMS = [
    "技术研发部",
    "市场部",
    "产品设计部",
    "销售部",
    "运营部",
    "财务部",
    "人力资源部"
]

# 职别定义
RANKS = {
    1: "大领导",
    2: "团队领导",
    3: "普通员工"
}

# 职别对应数量
RANK_COUNTS = {
    1: TOP_LEADER_COUNT,
    2: TEAM_LEADER_COUNT,
    3: REGULAR_EMPLOYEE_COUNT
}

# ========== ID 生成配置 ==========

# User_ID 配置
USER_ID_LENGTH = 8  # User_ID 长度
USER_ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"  # 可用字符

# Dept_ID 配置
DEPT_ID_LENGTH = 5  # Dept_ID 长度
DEPT_ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"  # 可用字符

# ========== 文件输出配置 ==========

# 输出目录
OUTPUT_DIR = "output"

# 输出文件名
OUTPUT_FILENAME = "employees.xlsx"

# 完整输出路径
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# Excel 列名配置
EXCEL_COLUMNS = [
    "Name",      # 姓名
    "User_ID",   # 用户ID
    "Team",      # 团队
    "Dept_ID",   # 部门ID
    "Rank",      # 职别
    "Title"      # 职位
]

# ========== 数据验证配置 ==========

# 是否启用严格验证
STRICT_VALIDATION = True

# 验证规则
VALIDATION_RULES = {
    "check_total_count": True,      # 检查总数是否为200
    "check_unique_names": True,     # 检查姓名唯一性
    "check_unique_user_ids": True,  # 检查User_ID唯一性
    "check_rank_distribution": True, # 检查职别分布
    "check_team_coverage": True,    # 检查团队覆盖
    "check_id_format": True,        # 检查ID格式
}

# ========== 日志配置 ==========

# 日志级别
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 是否输出详细日志
VERBOSE = True

# ========== 其他配置 ==========

# 是否创建输出目录（如果不存在）
CREATE_OUTPUT_DIR = True

# 是否覆盖已存在的文件
OVERWRITE_EXISTING = True

# ========== Phase 2: Hard Skill Assignment ==========

# 输入文件（阶段1的输出）
EMPLOYEE_FILE_PATH = os.path.join(OUTPUT_DIR, "employees.xlsx")

# 输出文件（带技能）
OUTPUT_FILENAME_WITH_HARDSKILLS = "employees_with_hardskills.xlsx"
OUTPUT_PATH_WITH_HARDSKILLS = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME_WITH_HARDSKILLS)

# 技能集合备份文件（可选）
SKILL_UNIVERSE_FILE = os.path.join(OUTPUT_DIR, "skill_universe.json")

# 技能数量配置（按职别）
SKILL_COUNT_BY_RANK = {
    1: {"min": 6, "max": 10},  # 大领导
    2: {"min": 5, "max": 8},   # 团队领导
    3: {"min": 3, "max": 6}    # 普通员工
}

# 技能强度等级定义
SKILL_LEVELS = ["strong", "medium", "low"]

# 技能强度分布建议（按职别）
SKILL_LEVEL_DISTRIBUTION = {
    1: {"strong": (2, 4), "medium": (3, 5), "low": (1, 2)},  # 大领导
    2: {"strong": (2, 3), "medium": (2, 4), "low": (1, 2)},  # 团队领导
    3: {"strong": (1, 2), "medium": (1, 3), "low": (1, 2)}   # 普通员工
}

# 技能集合大小
MIN_SKILL_UNIVERSE_SIZE = 40  # 最少技能数
MAX_SKILL_UNIVERSE_SIZE = 60  # 最多技能数

# 批处理配置
SKILL_ASSIGNMENT_BATCH_SIZE = 10  # 每批分配的员工数

# 验证规则
SKILL_VALIDATION_RULES = {
    "check_all_employees_have_skills": True,     # 所有员工都有技能
    "check_skill_count_range": True,             # 技能数量在范围内
    "check_skills_in_universe": True,            # 技能在集合内
    "check_no_duplicates_per_employee": True,    # 员工内部无重复技能
    "check_skill_levels_valid": True,            # 技能强度等级有效（strong/medium/low）
    "check_level_distribution": True,            # 强度分布合理（至少有1个strong）
}

# ========== Phase 3: Communication Style Assignment ==========

# Communication Style Universe 文件路径
COMMUNICATION_STYLE_UNIVERSE_FILE = os.path.join(OUTPUT_DIR, "communicationstyle_universe.json")

# Communication Style分配批量大小
COMMUNICATION_STYLE_BATCH_SIZE = 10  # 每批分配10个员工

# 输入文件（Phase 2的输出）
EMPLOYEES_WITH_HARDSKILLS_FILE = os.path.join(OUTPUT_DIR, "employees_with_hardskills.xlsx")

# 输出文件（Phase 3的输出）
EMPLOYEES_WITH_COMMUNICATION_STYLE_FILE = os.path.join(OUTPUT_DIR, "employees_with_communicationstyle.xlsx")

# Communication Style分配报告
COMMUNICATION_STYLE_ASSIGNMENT_REPORT = os.path.join(OUTPUT_DIR, "communication_style_assignment_report.json")

# ==================== Phase 4: Topic-Driven Task Generation ====================

# 大 Topic 数量（可配置）
NUM_MAJOR_TOPICS = 20  # 生成5个大的项目主题

# 每个大 Topic 下的小 Topic 数量（可配置）
NUM_SUB_TOPICS_PER_MAJOR = 3  # 每个大 topic 拆分为3个小 topic

# 项目目录
PROJECTS_DIR = os.path.join(OUTPUT_DIR, "projects")

# 小 Topic 的团队规模范围
SUB_TOPIC_TEAM_SIZE = {
    "min": 20,
    "max": 60,
    "rank_1_min": 1,  # 至少1个 Rank 1
    "rank_2_min": 1,  # 至少1个 Rank 2
}

# 每个成员的最小 subtask 数量
MIN_SUBTASKS_PER_MEMBER = 5

# 大 Topic 汇总文件
MAJOR_TOPICS_FILE = os.path.join(PROJECTS_DIR, "major_topics.json")

# 小 Topic 汇总文件
SUB_TOPICS_FILE = os.path.join(PROJECTS_DIR, "sub_topics.json")

# 统计报告文件
PROJECTS_SUMMARY_REPORT = os.path.join(PROJECTS_DIR, "summary_report.json")

# ========== 配置验证 ==========

def validate_config():
    """
    验证配置的有效性
    """
    errors = []

    # 检查 API Key
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY 未设置，请在 config.py 中配置")

    # 检查员工数量配置
    if TOP_LEADER_COUNT + TEAM_LEADER_COUNT >= TOTAL_EMPLOYEES:
        errors.append("领导数量超过总员工数")

    if TEAM_LEADER_COUNT != len(TEAMS):
        errors.append(f"团队领导数量({TEAM_LEADER_COUNT})与团队数量({len(TEAMS)})不匹配")

    # 检查职别数量
    total_rank_count = sum(RANK_COUNTS.values())
    if total_rank_count != TOTAL_EMPLOYEES:
        errors.append(f"职别总数({total_rank_count})与总员工数({TOTAL_EMPLOYEES})不匹配")

    return errors

# ========== 辅助函数 ==========

def get_team_distribution():
    """
    计算每个团队的预期员工数量
    这里采用平均分配策略，剩余的员工随机分配
    """
    regular_per_team = REGULAR_EMPLOYEE_COUNT // len(TEAMS)
    remainder = REGULAR_EMPLOYEE_COUNT % len(TEAMS)

    distribution = {}
    for i, team in enumerate(TEAMS):
        # 每个团队至少有 1 个领导 + regular_per_team 个普通员工
        base_count = 1 + regular_per_team
        # 前 remainder 个团队多分配 1 个员工
        extra = 1 if i < remainder else 0
        distribution[team] = base_count + extra

    # 加上大领导（分配到第一个团队）
    distribution[TEAMS[0]] += TOP_LEADER_COUNT

    return distribution

def print_config_summary():
    """
    打印配置摘要
    """
    print("=" * 50)
    print("配置摘要")
    print("=" * 50)
    print(f"总员工数: {TOTAL_EMPLOYEES}")
    print(f"  - 大领导 (Rank 1): {TOP_LEADER_COUNT}")
    print(f"  - 团队领导 (Rank 2): {TEAM_LEADER_COUNT}")
    print(f"  - 普通员工 (Rank 3): {REGULAR_EMPLOYEE_COUNT}")
    print(f"\n团队数量: {len(TEAMS)}")
    for team in TEAMS:
        print(f"  - {team}")
    print(f"\nOpenAI 模型: {OPENAI_MODEL}")
    print(f"输出文件: {OUTPUT_PATH}")
    print("=" * 50)

# 在导入时验证配置
if __name__ != "__main__":
    config_errors = validate_config()
    if config_errors:
        print("配置错误:")
        for error in config_errors:
            print(f"  - {error}")


# ==================== Phase 5: 任务时间线分配 ====================

# 时间范围配置
TIMELINE_START_DATE = "2025-01-01"
TIMELINE_END_DATE = "2025-12-31"

# 时间线分配配置
TIMELINE_ASSIGNMENT_CONFIG = {
    "start_date": TIMELINE_START_DATE,
    "end_date": TIMELINE_END_DATE,
    "weekend_working": False,  # 是否在周末工作（暂不实现，预留）
    "holiday_list": [],  # 节假日列表（暂不实现，预留）
}

# 任务排序批处理配置
TIMELINE_BATCH_MODE = False  # True=按项目批处理, False=整个项目一次性处理

# API重试配置（继承全局配置）
# 使用 MAX_RETRIES 和 RETRY_DELAY
