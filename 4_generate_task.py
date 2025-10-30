#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 4: Task Generation

根据员工的Hard Skills和Communication Style生成项目和任务分配
"""

import os
import sys
import json
import time
import random
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import Counter
from tqdm import tqdm

# 第三方库
try:
    from openai import OpenAI
except ImportError as e:
    print(f"错误: 缺少必要的依赖库 - {e}")
    print("请运行: pip install openai pandas openpyxl python-dotenv tqdm")
    sys.exit(1)

# 导入配置和提示词
import config
from prompt import PromptTemplate


# ==================== OpenAI API 调用模块 ==========

def call_gpt5_phase4(prompt: str, retries: int = None) -> Optional[Dict]:
    """
    调用 OpenAI GPT-5 API（Phase 4专用）

    参数:
        prompt: 提示词
        retries: 重试次数（默认使用配置值）

    返回:
        解析后的 JSON 数据，失败返回 None
    """
    if retries is None:
        retries = config.MAX_RETRIES

    # 检查 API Key
    if not config.OPENAI_API_KEY:
        print("错误: OPENAI_API_KEY 未设置")
        return None

    # 初始化 OpenAI 客户端（通过 OpenRouter）
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

    for attempt in range(retries):
        try:
            print(f"\n正在调用 OpenAI API (尝试 {attempt + 1}/{retries})...")

            # 准备 API 参数
            api_kwargs = {
                "model": config.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的项目管理和组织架构专家，擅长任务拆解和团队协作。请严格按照要求输出 JSON 格式的数据。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }

            # 添加配置中的参数
            api_kwargs.update(config.API_PARAMS)

            print("⏳ 正在等待 GPT-5 响应...")

            response = client.chat.completions.create(**api_kwargs)

            # 提取响应内容
            content = response.choices[0].message.content.strip()

            if config.VERBOSE:
                print(f"\nAPI 响应长度: {len(content)} 字符")
                print(f"使用的 tokens: {response.usage.total_tokens}")

            # 清理响应内容（移除可能的 markdown 标记）
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # 解析 JSON
            try:
                data = json.loads(content)
                print("✓ API 调用成功，数据解析完成")
                return data
            except json.JSONDecodeError as e:
                print(f"✗ JSON 解析失败: {e}")
                print(f"响应内容（前500字符）: {content[:500]}")

                if attempt < retries - 1:
                    print(f"将在 {config.RETRY_DELAY} 秒后重试...")
                    time.sleep(config.RETRY_DELAY)
                    continue
                else:
                    return None

        except Exception as e:
            print(f"✗ API 调用失败: {e}")

            if attempt < retries - 1:
                print(f"将在 {config.RETRY_DELAY} 秒后重试...")
                time.sleep(config.RETRY_DELAY)
                continue
            else:
                return None

    return None


# ==================== 数据加载模块 ====================

def parse_hard_skills(hard_skills_str: str) -> List[Dict]:
    """
    解析Hard_Skills字符串为结构化数组

    输入: "商业模式画布(strong), SWOT分析(strong), OKR(strong), KPI(medium)"
    输出: [
        {"skill": "商业模式画布", "proficiency": "strong"},
        {"skill": "SWOT分析", "proficiency": "strong"},
        {"skill": "OKR", "proficiency": "strong"},
        {"skill": "KPI", "proficiency": "medium"}
    ]
    """
    if pd.isna(hard_skills_str) or not hard_skills_str:
        return []

    skills = []
    for item in hard_skills_str.split(', '):
        if '(' in item and ')' in item:
            skill = item[:item.index('(')].strip()
            proficiency = item[item.index('(')+1:item.index(')')].strip()
            skills.append({"skill": skill, "proficiency": proficiency})

    return skills


def load_employees_data() -> pd.DataFrame:
    """
    加载Phase 3的输出：员工数据（含Communication Style）

    注意:
    - Hard_Skills是string格式，转dict时需要用parse_hard_skills()解析
    - Communication_Style是JSON string，转dict时需要用json.loads()解析
    """
    print(f"\n{'='*60}")
    print("加载员工数据...")
    print(f"{'='*60}")

    file_path = config.EMPLOYEES_WITH_COMMUNICATION_STYLE_FILE

    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return None

    df = pd.read_excel(file_path)

    print(f"✓ 已加载 {len(df)} 名员工")
    print(f"  - Rank 1: {len(df[df['Rank']==1])} 人")
    print(f"  - Rank 2: {len(df[df['Rank']==2])} 人")
    print(f"  - Rank 3: {len(df[df['Rank']==3])} 人")

    return df


def employee_row_to_dict(row: pd.Series) -> Dict:
    """
    将DataFrame的一行转换为结构化字典

    处理:
    1. Hard_Skills字符串 -> List[Dict]
    2. Communication_Style JSON string -> Dict
    """
    employee = {
        "user_name": row["Name"],
        "team": row["Team"],
        "title": row["Title"],
        "rank": int(row["Rank"]),
        "hard_skills": parse_hard_skills(row["Hard_Skills"]),
        "communication_style": json.loads(row["Communication_Style"]) if isinstance(row["Communication_Style"], str) else row["Communication_Style"]
    }

    return employee


# ==================== Project 1: 初始化 ====================

def initialize_first_team(df: pd.DataFrame) -> List[Dict]:
    """
    随机初始化第一个项目的团队
    根据config.FIRST_TEAM_SIZE配置选择成员：
    - rank_1个 Rank 1
    - rank_2个 Rank 2
    - rank_3个 Rank 3

    Returns:
        List[Dict]: 成员的结构化数据（包含解析后的hard_skills和communication_style）
    """
    print(f"\n{'='*60}")
    print("初始化第一个项目的团队...")
    print(f"{'='*60}")

    # 设置随机种子（如果配置了）
    if config.RANDOM_SEED is not None:
        random.seed(config.RANDOM_SEED)

    # 从config读取团队规模配置
    rank1_count = config.FIRST_TEAM_SIZE['rank_1']
    rank2_count = config.FIRST_TEAM_SIZE['rank_2']
    rank3_count = config.FIRST_TEAM_SIZE['rank_3']

    print(f"团队规模配置: Rank 1={rank1_count}, Rank 2={rank2_count}, Rank 3={rank3_count}")

    rank1_employees = df[df['Rank'] == 1].sample(n=rank1_count)
    rank2_employees = df[df['Rank'] == 2].sample(n=rank2_count)
    rank3_employees = df[df['Rank'] == 3].sample(n=rank3_count)

    team_df = pd.concat([rank1_employees, rank2_employees, rank3_employees])

    # 转换为结构化字典列表
    team_members = [employee_row_to_dict(row) for _, row in team_df.iterrows()]

    print(f"✓ 团队初始化完成，共 {len(team_members)} 人")

    # 统计各职别人数并打印
    rank_counts = {}
    for member in team_members:
        rank = member['rank']
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    print(f"  - Rank 1: {rank_counts.get(1, 0)} 人")
    print(f"  - Rank 2: {rank_counts.get(2, 0)} 人")
    print(f"  - Rank 3: {rank_counts.get(3, 0)} 人")

    return team_members


def generate_project_1(team_members: List[Dict]) -> Dict:
    """
    生成第一个项目

    流程:
    1. 调用GPT生成project topic和description
    2. 调用GPT拆解任务并分配
    3. 构建完整的项目JSON数据

    Returns:
        完整的项目JSON数据
    """
    print(f"\n{'='*60}")
    print("生成 Project 1...")
    print(f"{'='*60}")

    # ========== 阶段1: 生成项目主题和描述 ==========
    print("\n[阶段1/2] 生成项目主题和描述...")

    prompt = PromptTemplate.get_project_generation_prompt(
        team_members=team_members,
        project_number=1,
        previous_projects=None
    )

    result = call_gpt5_phase4(prompt)

    if not result:
        print("✗ 生成项目主题失败")
        return None

    project_topic = result.get("project_topic", "未命名项目")
    project_description = result.get("project_description", "")

    print(f"✓ 项目主题: {project_topic}")
    print(f"  项目描述: {project_description[:80]}...")

    # ========== 阶段2: 拆解任务并分配 ==========
    print("\n[阶段2/2] 拆解任务并分配...")

    # 为Project 1，communication_style不需要调整，直接使用原始的
    # 添加original_communication_style字段
    for member in team_members:
        member['original_communication_style'] = member['communication_style'].copy()

    prompt = PromptTemplate.get_task_breakdown_and_assignment_prompt(
        project_topic=project_topic,
        project_description=project_description,
        team_members=team_members
    )

    result = call_gpt5_phase4(prompt)

    if not result:
        print("✗ 任务拆解失败")
        return None

    task_assignments = result.get("task_assignments", [])

    # 验证任务分配
    if not validate_task_assignments(task_assignments, team_members):
        print("⚠ 任务分配验证未通过，但继续执行")

    # ========== 构建完整的项目数据 ==========
    project_data = build_complete_project_data(
        project_number=1,
        project_topic=project_topic,
        project_description=project_description,
        team_members=team_members,
        task_assignments=task_assignments,
        related_projects=[],
        adjustments_made={
            "members_added": [],
            "members_removed": [],
            "communication_style_adjusted": False
        }
    )

    # 保存项目
    save_project(project_data)

    print(f"\n✓ Project 1 生成完成")
    print(f"  - 团队规模: {len(project_data['members'])} 人")
    print(f"  - 总任务数: {project_data['metadata']['total_subtasks']}")

    return project_data


# ==================== Project 2+: 迭代生成 ====================

def generate_next_project(
    project_number: int,
    previous_projects: List[Dict],
    all_employees_df: pd.DataFrame
) -> Dict:
    """
    生成第N个项目（N >= 2）

    流程:
    1. 调用GPT生成新project topic/description和调整成员
    2. 调用GPT根据项目架构调整communication style
    3. 调用GPT拆解任务并分配
    4. 保存到文件

    Returns:
        完整的项目JSON数据
    """
    print(f"\n{'='*60}")
    print(f"生成 Project {project_number}...")
    print(f"{'='*60}")

    # ========== 阶段1: 生成项目并调整成员 ==========
    project_topic, project_description, new_team, adjustment_info = stage1_generate_project_and_adjust_members(
        project_number=project_number,
        previous_projects=previous_projects,
        all_employees_df=all_employees_df
    )

    if not new_team:
        print("✗ 成员调整失败")
        return None

    # ========== 阶段2: 调整Communication Style ==========
    updated_team = stage2_adjust_communication_styles(
        project_topic=project_topic,
        project_description=project_description,
        team_members=new_team
    )

    if not updated_team:
        print("✗ Communication Style调整失败")
        return None

    # ========== 阶段3: 拆解任务并分配 ==========
    project_data = stage3_breakdown_and_assign_tasks(
        project_number=project_number,
        project_topic=project_topic,
        project_description=project_description,
        team_members=updated_team,
        related_projects=[p['project_info']['project_number'] for p in previous_projects],
        adjustments_made=adjustment_info
    )

    if not project_data:
        print("✗ 任务拆解失败")
        return None

    # 保存项目
    save_project(project_data)

    print(f"\n✓ Project {project_number} 生成完成")
    print(f"  - 团队规模: {len(project_data['members'])} 人")
    print(f"  - 总任务数: {project_data['metadata']['total_subtasks']}")
    print(f"  - 成员调整: +{len(adjustment_info.get('members_added', []))} -{len(adjustment_info.get('members_removed', []))}")

    return project_data


# ==================== 阶段1: 生成项目和调整成员 ====================

def stage1_generate_project_and_adjust_members(
    project_number: int,
    previous_projects: List[Dict],
    all_employees_df: pd.DataFrame
) -> Tuple[str, str, List[Dict], Dict]:
    """
    阶段1: 生成新项目并调整团队成员

    Returns:
        (project_topic, project_description, new_team_members, adjustment_info)
    """
    print("\n[阶段1/3] 生成项目并调整成员...")

    # 获取上一个项目的团队成员
    previous_project = previous_projects[-1]
    current_team = previous_project['members']

    # 将所有员工转换为字典列表
    all_employees = [employee_row_to_dict(row) for _, row in all_employees_df.iterrows()]

    # 首先生成新项目的topic和description
    prompt_gen = PromptTemplate.get_project_generation_prompt(
        team_members=current_team,
        project_number=project_number,
        previous_projects=previous_projects
    )

    result_gen = call_gpt5_phase4(prompt_gen)

    if not result_gen:
        print("✗ 生成项目主题失败")
        return None, None, None, None

    project_topic = result_gen.get("project_topic", "未命名项目")
    project_description = result_gen.get("project_description", "")

    print(f"✓ 新项目: {project_topic}")

    # 然后调整成员
    prompt_adj = PromptTemplate.get_member_adjustment_prompt(
        new_project_topic=project_topic,
        new_project_description=project_description,
        current_team=current_team,
        all_employees=all_employees,
        previous_projects=previous_projects
    )

    result_adj = call_gpt5_phase4(prompt_adj)

    if not result_adj:
        print("✗ 成员调整失败")
        return None, None, None, None

    # 构建新团队
    new_team = build_team_from_adjustments(result_adj, all_employees_df)

    if not new_team:
        print("✗ 构建新团队失败")
        return None, None, None, None

    # 验证约束
    if not validate_team_constraints(new_team):
        print("⚠ 团队约束验证未通过，但继续执行")

    # 计算实际的成员变化（而不是依赖GPT的声明）
    current_team_names = set([m['user_name'] for m in current_team])
    new_team_names = set([m['user_name'] for m in new_team])

    actual_added = list(new_team_names - current_team_names)
    actual_removed = list(current_team_names - new_team_names)

    adjustment_info = {
        "members_added": actual_added,  # 实际新增的成员
        "members_removed": actual_removed,  # 实际移除的成员
        "communication_style_adjusted": True
    }

    print(f"✓ 团队调整完成: 新增 {len(adjustment_info['members_added'])} 人, 移除 {len(adjustment_info['members_removed'])} 人")

    # 调试信息：对比GPT声明 vs 实际变化
    gpt_added = [m['user_name'] for m in result_adj.get('member_adjustments', {}).get('add_members', [])]
    gpt_removed = [m['user_name'] for m in result_adj.get('member_adjustments', {}).get('remove_members', [])]
    if len(gpt_added) != len(actual_added) or len(gpt_removed) != len(actual_removed):
        print(f"  ⚠️  注意: GPT声明 (+{len(gpt_added)}/-{len(gpt_removed)})与实际变化不一致")

    return project_topic, project_description, new_team, adjustment_info


def build_team_from_adjustments(adjustments: Dict, all_employees_df: pd.DataFrame) -> List[Dict]:
    """
    根据调整信息构建新团队

    参数:
        adjustments: GPT返回的调整信息
        all_employees_df: 所有员工的DataFrame

    Returns:
        新团队成员列表
    """
    member_adj = adjustments.get('member_adjustments', {})
    keep_names = set(member_adj.get('keep_members', []))
    add_names = set([m.get('user_name') for m in member_adj.get('add_members', [])])

    # 合并keep和add
    all_names = keep_names | add_names

    # 从DataFrame中提取这些员工
    team_df = all_employees_df[all_employees_df['Name'].isin(all_names)]

    # 转换为字典列表
    team_members = [employee_row_to_dict(row) for _, row in team_df.iterrows()]

    return team_members


# ==================== 阶段2: 调整Communication Style ====================

def stage2_adjust_communication_styles(
    project_topic: str,
    project_description: str,
    team_members: List[Dict]
) -> List[Dict]:
    """
    阶段2: 根据项目架构调整成员的communication style

    Returns:
        更新后的team_members（communication_style已调整）
    """
    print("\n[阶段2/3] 调整Communication Style...")

    # 保存原始communication_style
    for member in team_members:
        if 'original_communication_style' not in member:
            member['original_communication_style'] = member['communication_style'].copy()

    # 构建prompt
    prompt = PromptTemplate.get_communication_style_adjustment_prompt(
        project_topic=project_topic,
        project_description=project_description,
        team_members=team_members
    )

    # 调用GPT
    result = call_gpt5_phase4(prompt)

    if not result:
        print("✗ Communication Style调整失败")
        return None

    # 应用调整
    updated_team = apply_style_adjustments(team_members, result)

    # 验证调整后的style
    if not validate_communication_styles(updated_team):
        print("⚠ Communication Style验证未通过，但继续执行")

    print(f"✓ Communication Style调整完成")

    return updated_team


def apply_style_adjustments(team_members: List[Dict], adjustments: Dict) -> List[Dict]:
    """
    应用Communication Style调整

    参数:
        team_members: 团队成员列表
        adjustments: GPT返回的调整信息

    Returns:
        更新后的团队成员列表
    """
    adjusted_styles = adjustments.get('adjusted_styles', [])

    # 创建user_name到adjusted_style的映射
    style_map = {}
    for adj in adjusted_styles:
        user_name = adj.get('user_name')
        adjusted_style = adj.get('adjusted_style', {})
        style_map[user_name] = adjusted_style

    # 应用调整
    for member in team_members:
        user_name = member['user_name']
        if user_name in style_map:
            member['communication_style'] = style_map[user_name]

    return team_members


# ==================== 阶段3: 拆解任务 ====================

def stage3_breakdown_and_assign_tasks(
    project_number: int,
    project_topic: str,
    project_description: str,
    team_members: List[Dict],
    related_projects: List[int],
    adjustments_made: Dict
) -> Dict:
    """
    阶段3: 拆解项目任务并分配给成员

    Returns:
        完整的project JSON数据
    """
    print("\n[阶段3/3] 拆解任务并分配...")

    # 构建prompt
    prompt = PromptTemplate.get_task_breakdown_and_assignment_prompt(
        project_topic=project_topic,
        project_description=project_description,
        team_members=team_members
    )

    # 调用GPT
    result = call_gpt5_phase4(prompt)

    if not result:
        print("✗ 任务拆解失败")
        return None

    task_assignments = result.get('task_assignments', [])

    # 验证任务分配
    if not validate_task_assignments(task_assignments, team_members):
        print("⚠ 任务分配验证未通过，但继续执行")

    # 构建完整project数据
    project_data = build_complete_project_data(
        project_number=project_number,
        project_topic=project_topic,
        project_description=project_description,
        team_members=team_members,
        task_assignments=task_assignments,
        related_projects=related_projects,
        adjustments_made=adjustments_made
    )

    print(f"✓ 任务拆解完成，共 {project_data['metadata']['total_subtasks']} 个任务")

    return project_data


def build_complete_project_data(
    project_number: int,
    project_topic: str,
    project_description: str,
    team_members: List[Dict],
    task_assignments: List[Dict],
    related_projects: List[int],
    adjustments_made: Dict
) -> Dict:
    """
    构建完整的项目JSON数据

    Returns:
        完整的项目数据结构
    """
    # 构建成员到任务的映射
    user_to_tasks = {}
    for assignment in task_assignments:
        user_name = assignment.get('user_name')
        subtasks = assignment.get('subtasks', [])
        user_to_tasks[user_name] = subtasks

    # 为每个成员添加subtasks
    members_with_tasks = []
    for member in team_members:
        member_copy = member.copy()
        user_name = member['user_name']
        member_copy['subtasks'] = user_to_tasks.get(user_name, [])
        members_with_tasks.append(member_copy)

    # 计算统计数据
    rank_counts = Counter([m['rank'] for m in team_members])
    total_subtasks = sum(len(m['subtasks']) for m in members_with_tasks)
    avg_subtasks = total_subtasks / len(members_with_tasks) if members_with_tasks else 0

    # 构建完整数据
    project_data = {
        "project_info": {
            "project_number": project_number,
            "project_topic": project_topic,
            "project_description": project_description,
            "related_projects": related_projects,
            "generated_at": datetime.now().isoformat()
        },
        "team_composition": {
            "total_members": len(members_with_tasks),
            "rank_distribution": {
                "rank_1": rank_counts.get(1, 0),
                "rank_2": rank_counts.get(2, 0),
                "rank_3": rank_counts.get(3, 0)
            }
        },
        "members": members_with_tasks,
        "metadata": {
            "total_subtasks": total_subtasks,
            "avg_subtasks_per_member": round(avg_subtasks, 2),
            "generation_method": "GPT-5 Multi-stage",
            "adjustments_made": adjustments_made
        }
    }

    return project_data


# ==================== 文件操作 ====================

def save_project(project_data: Dict) -> str:
    """
    保存项目到文件

    路径: projects/{project_topic}/{project_topic}.json

    Returns:
        文件路径
    """
    project_topic = project_data['project_info']['project_topic']

    # 创建项目目录
    project_dir = os.path.join(config.PROJECTS_DIR, project_topic)
    os.makedirs(project_dir, exist_ok=True)

    # 保存文件
    file_path = os.path.join(project_dir, f"{project_topic}.json")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 项目已保存: {file_path}")

    return file_path


def load_project(project_topic: str) -> Dict:
    """
    加载已保存的项目

    参数:
        project_topic: 项目主题

    Returns:
        项目数据
    """
    file_path = os.path.join(config.PROJECTS_DIR, project_topic, f"{project_topic}.json")

    if not os.path.exists(file_path):
        print(f"✗ 项目文件不存在: {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        project_data = json.load(f)

    return project_data


# ==================== 验证函数 ====================

def validate_team_constraints(team: List[Dict]) -> bool:
    """
    验证团队约束：Rank 1必须有，Rank 2至少1个

    Returns:
        是否通过验证
    """
    rank_counts = Counter([m['rank'] for m in team])

    errors = []

    # 检查Rank 1
    if rank_counts.get(1, 0) < 1:
        errors.append("团队必须至少有1个Rank 1成员")

    # 检查Rank 2
    if rank_counts.get(2, 0) < 1:
        errors.append("团队必须至少有1个Rank 2成员")

    # 检查团队规模
    if len(team) < config.SUBSEQUENT_TEAM_SIZE_RANGE['min']:
        errors.append(f"团队规模({len(team)})小于最小值({config.SUBSEQUENT_TEAM_SIZE_RANGE['min']})")

    if len(team) > config.SUBSEQUENT_TEAM_SIZE_RANGE['max']:
        errors.append(f"团队规模({len(team)})大于最大值({config.SUBSEQUENT_TEAM_SIZE_RANGE['max']})")

    if errors:
        print("团队约束验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def validate_communication_styles(team: List[Dict]) -> bool:
    """
    验证communication style的值都是合法的

    Returns:
        是否通过验证
    """
    valid_values = {
        "Formality": ["Formal", "Semi-formal", "Casual"],
        "Verbosity": ["Detailed", "Moderate", "Concise"],
        "Humor": ["Frequent", "Occasional", "Minimal"],
        "Jargon_Usage": ["Technical", "Balanced", "Plain"],
        "Emoji_Usage": ["Frequent", "Occasional", "Rare"],
        "Directness": ["Direct", "Balanced", "Indirect"],
        "Warmth": ["Warm", "Friendly", "Neutral"],
        "Questioning_Style": ["Probing", "Clarifying", "Accepting"]
    }

    errors = []

    for member in team:
        user_name = member.get('user_name')
        cs = member.get('communication_style', {})

        for dimension, valid_vals in valid_values.items():
            value = cs.get(dimension)
            if value not in valid_vals:
                errors.append(f"{user_name}的{dimension}值({value})不合法")

    if errors:
        print("Communication Style验证失败:")
        for error in errors[:10]:  # 只显示前10个错误
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors)-10} 个错误")
        return False

    return True


def validate_task_assignments(assignments: List[Dict], team: List[Dict]) -> bool:
    """
    验证任务分配:
    - 所有团队成员都被分配了任务
    - 每个成员至少5个任务
    - user_name都存在
    - required_skills匹配成员技能

    Returns:
        是否通过验证
    """
    team_names = set([m['user_name'] for m in team])
    team_skills = {}
    for m in team:
        team_skills[m['user_name']] = set([s['skill'] for s in m['hard_skills']])

    errors = []

    # 收集已分配任务的成员
    assigned_names = set([a.get('user_name') for a in assignments])

    # ⚠️ CRITICAL: 检查是否所有团队成员都被分配了任务
    missing_members = team_names - assigned_names
    if missing_members:
        errors.append(f"以下成员没有被分配任务: {', '.join(missing_members)}")

    # 检查每个分配
    for assignment in assignments:
        user_name = assignment.get('user_name')
        subtasks = assignment.get('subtasks', [])

        # 检查user_name存在
        if user_name not in team_names:
            errors.append(f"用户 {user_name} 不在团队中")
            continue

        # 检查任务数量
        if len(subtasks) < config.MIN_SUBTASKS_PER_MEMBER:
            errors.append(f"{user_name}的任务数({len(subtasks)})少于最小值({config.MIN_SUBTASKS_PER_MEMBER})")

        # 检查required_skills (暂时跳过，因为可能不严格匹配)
        # for subtask in subtasks:
        #     required_skills = subtask.get('required_skills', [])
        #     member_skills = team_skills.get(user_name, set())
        #     # 检查是否有至少一个技能匹配
        #     # ...

    if errors:
        print("任务分配验证失败:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors)-10} 个错误")
        return False

    return True


# ==================== 统计和报告 ====================

def generate_summary_report(all_projects: List[Dict]) -> Dict:
    """
    生成所有项目的统计报告

    包括:
    - 项目数量
    - 总任务数
    - 成员参与度统计
    - 技能使用频率
    - Communication style分布
    """
    print(f"\n{'='*60}")
    print("生成统计报告...")
    print(f"{'='*60}")

    total_projects = len(all_projects)
    total_tasks = sum([p['metadata']['total_subtasks'] for p in all_projects])

    # 收集所有参与的员工
    all_participants = set()
    employee_participation = {}

    for project in all_projects:
        project_num = project['project_info']['project_number']
        for member in project['members']:
            user_name = member['user_name']
            all_participants.add(user_name)

            if user_name not in employee_participation:
                employee_participation[user_name] = {
                    "projects_participated": [],
                    "total_tasks": 0,
                    "rank": member['rank']
                }

            employee_participation[user_name]['projects_participated'].append(project_num)
            employee_participation[user_name]['total_tasks'] += len(member.get('subtasks', []))

    # 技能使用频率
    skill_usage = Counter()
    for project in all_projects:
        for member in project['members']:
            for skill in member.get('hard_skills', []):
                skill_usage[skill['skill']] += 1

    # Communication Style分布
    cs_distribution = {}
    dimensions = ["Formality", "Verbosity", "Humor", "Jargon_Usage", "Emoji_Usage",
                  "Directness", "Warmth", "Questioning_Style"]

    for dim in dimensions:
        cs_distribution[dim] = Counter()

    for project in all_projects:
        for member in project['members']:
            cs = member.get('communication_style', {})
            for dim in dimensions:
                value = cs.get(dim, 'Unknown')
                cs_distribution[dim][value] += 1

    # 项目摘要
    projects_summary = []
    for project in all_projects:
        projects_summary.append({
            "project_number": project['project_info']['project_number'],
            "project_topic": project['project_info']['project_topic'],
            "team_size": len(project['members']),
            "total_subtasks": project['metadata']['total_subtasks'],
            "related_projects": project['project_info']['related_projects']
        })

    # 构建报告
    summary = {
        "generation_time": datetime.now().isoformat(),
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "total_unique_employees": len(all_participants),
        "projects_summary": projects_summary,
        "employee_participation": employee_participation,
        "skill_usage_frequency": dict(skill_usage.most_common(20)),  # 只保留前20
        "communication_style_distribution": {
            dim: dict(cs_distribution[dim]) for dim in dimensions
        }
    }

    print(f"✓ 统计报告生成完成")
    print(f"  - 项目总数: {total_projects}")
    print(f"  - 任务总数: {total_tasks}")
    print(f"  - 参与员工: {len(all_participants)} 人")

    return summary


# ==================== 主函数 ====================

def main():
    """
    主流程
    """
    print("\n" + "="*60)
    print("Phase 4: Task Generation")
    print("="*60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建输出目录
    os.makedirs(config.PROJECTS_DIR, exist_ok=True)

    # 1. 加载数据
    print("\n[步骤 1/4] 加载员工数据...")
    df = load_employees_data()

    if df is None:
        print("✗ 加载数据失败")
        return 1

    # 2. 生成Project 1
    print("\n[步骤 2/4] 生成Project 1...")
    team_1 = initialize_first_team(df)
    project_1 = generate_project_1(team_1)

    if not project_1:
        print("✗ Project 1 生成失败")
        return 1

    print(f"\n✓ Project 1 完成: {project_1['project_info']['project_topic']}")

    all_projects = [project_1]

    # 3. 生成Project 2 到 N
    print(f"\n[步骤 3/4] 生成Project 2 到 {config.NUM_PROJECTS}...")

    for i in range(2, config.NUM_PROJECTS + 1):
        project = generate_next_project(
            project_number=i,
            previous_projects=all_projects,
            all_employees_df=df
        )

        if not project:
            print(f"✗ Project {i} 生成失败")
            return 1

        all_projects.append(project)
        print(f"\n✓ Project {i} 完成: {project['project_info']['project_topic']}")

    # 4. 生成统计报告
    print("\n[步骤 4/4] 生成统计报告...")
    summary = generate_summary_report(all_projects)

    summary_path = config.PROJECTS_SUMMARY_REPORT
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✓ 统计报告已保存: {summary_path}")

    # 5. 打印总结
    print("\n" + "="*60)
    print("✅ 所有项目生成完成！")
    print("="*60)
    print(f"总项目数: {len(all_projects)}")
    print(f"总任务数: {sum(p['metadata']['total_subtasks'] for p in all_projects)}")
    print(f"参与员工数: {len(set(m['user_name'] for p in all_projects for m in p['members']))}")
    print(f"\n项目列表:")
    for i, p in enumerate(all_projects, 1):
        topic = p['project_info']['project_topic']
        print(f"  {i}. {topic}")
        print(f"     路径: {os.path.join(config.PROJECTS_DIR, topic, topic + '.json')}")

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
