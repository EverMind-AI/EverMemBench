#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 4: Topic-Driven Task Generation (New Architecture)

新的架构流程：
1. Stage 1: 生成大 Topic
2. Stage 2: 拆分小 Topic
3. Stage 3: 选择团队成员
4. Stage 4: 生成并排序 Subtask
5. Stage 5: 分配 Subtask 到成员
"""

import os
import sys
import json
import time
import re
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from collections import Counter
from tqdm import tqdm

# 第三方库
try:
    from openai import OpenAI
except ImportError as e:
    print(f"错误: 无法导入 openai 库: {e}")
    print("请安装依赖: pip install openai")
    sys.exit(1)

# 导入配置和提示词
import config
from prompt import PromptTemplate


# ==================== OpenAI API 调用模块 ====================

def call_gpt_phase4(prompt: str, retries: int = None) -> Optional[Dict]:
    """
    调用 OpenAI GPT API（Phase 4专用）

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

    # 初始化 OpenAI 客户端
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
                        "content": "你是一位专业的项目管理和组织架构专家。请严格按照要求输出 JSON 格式的数据。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            }

            # 添加配置中的参数
            api_kwargs.update(config.API_PARAMS)

            print("⏳ 正在等待 GPT 响应...")

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

            # 清理控制字符（移除未转义的换行符、制表符等）
            # 保留空格，移除其他ASCII控制字符（0x00-0x1F, 0x7F）
            content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', content)

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

    输入: "Python(strong), Java(medium), SQL(low)"
    输出: [
        {"skill": "Python", "proficiency": "strong"},
        {"skill": "Java", "proficiency": "medium"},
        {"skill": "SQL", "proficiency": "low"}
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


def parse_communication_style(cs_str: str) -> Dict:
    """
    解析Communication_Style JSON字符串

    输入: '{"Formality": "Formal", "Verbosity": "Concise", ...}'
    输出: {"Formality": "Formal", "Verbosity": "Concise", ...}
    """
    if pd.isna(cs_str) or not cs_str:
        return {}

    if isinstance(cs_str, str):
        return json.loads(cs_str)
    else:
        return cs_str


def load_all_employees() -> List[Dict]:
    """
    加载全量员工数据

    Returns:
        List[Dict]: 员工列表，每个员工包含：
        - user_name, user_id, team, rank, title
        - hard_skills: List[Dict]
        - communication_style: Dict
    """
    print(f"\n{'='*60}")
    print("加载员工数据...")
    print(f"{'='*60}")

    file_path = config.EMPLOYEES_WITH_COMMUNICATION_STYLE_FILE

    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return None

    df = pd.read_excel(file_path)

    print(f"✓ 成功加载 {len(df)} 名员工")
    print(f"  - Rank 1: {len(df[df['Rank']==1])} 人")
    print(f"  - Rank 2: {len(df[df['Rank']==2])} 人")
    print(f"  - Rank 3: {len(df[df['Rank']==3])} 人")

    employees = []
    for _, row in df.iterrows():
        employee = {
            "user_name": row["Name"],
            "user_id": row["User_ID"],
            "team": row["Team"],
            "rank": int(row["Rank"]),
            "title": row["Title"],
            "hard_skills": parse_hard_skills(row["Hard_Skills"]),
            "communication_style": parse_communication_style(row["Communication_Style"])
        }
        employees.append(employee)

    return employees


# ==================== Stage 1: 生成大 Topic ====================

def generate_major_topics() -> List[Dict]:
    """
    Stage 1: 生成大 Topic

    Returns:
        List[Dict]: 大 topic 列表
    """
    print(f"\n{'='*60}")
    print("Stage 1: 生成大 Topic...")
    print(f"{'='*60}")

    prompt = PromptTemplate.get_major_topics_generation_prompt()
    result = call_gpt_phase4(prompt)

    if not result:
        print("✗ 生成大 Topic 失败")
        return None

    major_topics = result.get("major_topics", [])

    print(f"✓ 成功生成 {len(major_topics)} 个大 Topic:")
    for i, topic in enumerate(major_topics, 1):
        print(f"  {i}. {topic.get('topic', '未命名')}")

    return major_topics


def save_major_topics(major_topics: List[Dict]):
    """保存大 Topic 到文件"""
    os.makedirs(config.PROJECTS_DIR, exist_ok=True)

    data = {
        "generated_at": datetime.now().isoformat(),
        "count": len(major_topics),
        "major_topics": major_topics
    }

    with open(config.MAJOR_TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ 大 Topic 已保存: {config.MAJOR_TOPICS_FILE}")


# ==================== Stage 2: 拆分小 Topic ====================

def generate_sub_topics(major_topic: Dict) -> List[Dict]:
    """
    Stage 2: 拆分小 Topic

    Args:
        major_topic: 大 topic 数据

    Returns:
        List[Dict]: 小 topic 列表
    """
    topic_name = major_topic.get('topic', '未命名')
    print(f"\n拆分大 Topic: {topic_name}")

    prompt = PromptTemplate.get_sub_topics_generation_prompt(major_topic)
    result = call_gpt_phase4(prompt)

    if not result:
        print(f"✗ 拆分 {topic_name} 失败")
        return []

    sub_topics = result.get("sub_topics", [])

    print(f"✓ 成功拆分为 {len(sub_topics)} 个小 Topic:")
    for i, st in enumerate(sub_topics, 1):
        print(f"  {i}. {st.get('topic', '未命名')}")

    return sub_topics


def save_sub_topics(sub_topics: List[Dict]):
    """保存所有小 Topic 到汇总文件"""
    data = {
        "generated_at": datetime.now().isoformat(),
        "count": len(sub_topics),
        "sub_topics": sub_topics
    }

    with open(config.SUB_TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✓ 小 Topic 已保存: {config.SUB_TOPICS_FILE}")


# ==================== Stage 3: 选择团队成员 ====================

def select_team_members(sub_topic: Dict, all_employees: List[Dict]) -> List[Dict]:
    """
    Stage 3: 选择团队成员

    Args:
        sub_topic: 小 topic 数据
        all_employees: 全量员工列表

    Returns:
        List[Dict]: 选中的团队成员列表
    """
    topic_name = sub_topic.get('topic', '未命名')
    print(f"\n为项目 '{topic_name}' 选择团队成员...")

    prompt = PromptTemplate.get_team_selection_prompt(sub_topic, all_employees)
    result = call_gpt_phase4(prompt)

    if not result:
        print(f"✗ 选择团队失败")
        return None

    # 从 all_employees 中提取完整信息
    selected_names = [m['user_name'] for m in result.get('selected_members', [])]
    team = [emp.copy() for emp in all_employees if emp['user_name'] in selected_names]

    # 添加 selection_reason
    reason_map = {m['user_name']: m['selection_reason'] for m in result.get('selected_members', [])}
    for member in team:
        member['selection_reason'] = reason_map.get(member['user_name'], '')

    # 验证团队约束
    if not validate_team_selection(team):
        print("⚠ 团队选择验证未通过，但继续执行")

    print(f"✓ 成功选择 {len(team)} 名成员:")
    rank_counts = Counter([m['rank'] for m in team])
    print(f"  - Rank 1: {rank_counts.get(1, 0)} 人")
    print(f"  - Rank 2: {rank_counts.get(2, 0)} 人")
    print(f"  - Rank 3: {rank_counts.get(3, 0)} 人")

    return team


def validate_team_selection(team: List[Dict]) -> bool:
    """
    验证团队选择是否符合要求

    检查：
    1. 至少 1 个 Rank 1
    2. 至少 1 个 Rank 2
    3. 团队规模在配置范围内
    """
    rank_counts = Counter([m['rank'] for m in team])

    errors = []

    if rank_counts.get(1, 0) < config.SUB_TOPIC_TEAM_SIZE['rank_1_min']:
        errors.append(f"Rank 1 数量不足（需要至少 {config.SUB_TOPIC_TEAM_SIZE['rank_1_min']} 人）")

    if rank_counts.get(2, 0) < config.SUB_TOPIC_TEAM_SIZE['rank_2_min']:
        errors.append(f"Rank 2 数量不足（需要至少 {config.SUB_TOPIC_TEAM_SIZE['rank_2_min']} 人）")

    team_size = len(team)
    if team_size < config.SUB_TOPIC_TEAM_SIZE['min']:
        errors.append(f"团队规模不足（{team_size} < {config.SUB_TOPIC_TEAM_SIZE['min']}）")

    if team_size > config.SUB_TOPIC_TEAM_SIZE['max']:
        errors.append(f"团队规模超限（{team_size} > {config.SUB_TOPIC_TEAM_SIZE['max']}）")

    if errors:
        print("团队选择验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


# ==================== Stage 3.5: 调整 Communication Style ====================

def adjust_communication_styles(sub_topic: Dict, team_members: List[Dict]) -> bool:
    """
    Stage 3.5: 根据项目主题和团队结构调整成员的 communication_style

    Args:
        sub_topic: 小 topic 数据
        team_members: 团队成员列表（会被修改，添加调整后的 communication_style）

    Returns:
        bool: 是否成功
    """
    topic_name = sub_topic.get('topic', '未命名')
    print(f"\n调整团队成员的 Communication Style...")

    # 保存原始 communication_style
    for member in team_members:
        if 'original_communication_style' not in member:
            member['original_communication_style'] = member['communication_style'].copy()

    # 构建 prompt
    prompt = PromptTemplate.get_communication_style_adjustment_prompt(
        project_topic=topic_name,
        project_description=sub_topic.get('description', ''),
        team_members=team_members
    )

    # 调用 GPT
    result = call_gpt_phase4(prompt)

    if not result:
        print(f"✗ Communication Style 调整失败")
        return False

    # 应用调整
    adjusted_styles = result.get('adjusted_styles', [])

    if not adjusted_styles:
        print(f"⚠ GPT 未返回调整结果，communication_style 保持不变")
        return True

    # 验证是否返回了所有成员
    if len(adjusted_styles) < len(team_members):
        print(f"⚠ 警告：GPT 只返回了 {len(adjusted_styles)}/{len(team_members)} 个成员的调整")
        missing_members = [m['user_name'] for m in team_members
                          if m['user_name'] not in [s.get('user_name') for s in adjusted_styles]]
        if len(missing_members) <= 5:
            print(f"  未调整的成员: {', '.join(missing_members)}")
        else:
            print(f"  未调整的成员: {', '.join(missing_members[:5])} 等 {len(missing_members)} 人")

    # 创建用户名到调整后风格的映射
    style_map = {}
    for item in adjusted_styles:
        user_name = item.get('user_name')
        new_style = item.get('adjusted_style', {})
        if user_name and new_style:
            style_map[user_name] = new_style

    # 更新成员的 communication_style
    updated_count = 0
    for member in team_members:
        user_name = member['user_name']
        if user_name in style_map:
            member['communication_style'] = style_map[user_name]
            updated_count += 1

    print(f"✓ Communication Style 调整完成")
    print(f"  - GPT 返回了 {len(adjusted_styles)} 个调整结果")
    print(f"  - 成功应用了 {updated_count}/{len(team_members)} 名成员的调整")

    # 显示调整统计
    adjusted_count = len([m for m in team_members if m.get('communication_style') != m.get('original_communication_style')])
    print(f"  - 实际改变了 {adjusted_count}/{len(team_members)} 名成员的沟通风格")

    return True


# ==================== Stage 4: 生成并排序 Subtask ====================

def generate_and_sequence_subtasks(sub_topic: Dict, team_members: List[Dict]) -> List[Dict]:
    """
    Stage 4: 生成并排序 Subtask

    Args:
        sub_topic: 小 topic 数据
        team_members: 团队成员列表

    Returns:
        List[Dict]: 排序后的 subtask 列表
    """
    topic_name = sub_topic.get('topic', '未命名')
    print(f"\n为项目 '{topic_name}' 生成并排序 Subtask...")

    prompt = PromptTemplate.get_subtask_generation_and_sequencing_prompt(sub_topic, team_members)
    result = call_gpt_phase4(prompt)

    if not result:
        print(f"✗ 生成任务失败")
        return None

    subtasks = result.get("subtasks", [])

    # 暂时不分配 subtask_id，在分配完成后统一分配
    print(f"✓ 成功生成 {len(subtasks)} 个任务")

    # 显示 phase 分布
    phase_dist = Counter([st.get('phase', 'Unknown') for st in subtasks])
    print(f"  Phase 分布:")
    for phase, count in phase_dist.items():
        print(f"    - {phase}: {count} 个")

    return subtasks


# ==================== Stage 5: 分配 Subtask 到成员 ====================

def assign_subtasks_to_members(subtasks: List[Dict], team_members: List[Dict]) -> bool:
    """
    Stage 5: 分配 Subtask 到成员

    Args:
        subtasks: 排序后的 subtask 列表（包含 subtask_id）
        team_members: 团队成员列表（会被修改，添加 subtasks 字段）

    Returns:
        bool: 是否成功
    """
    print(f"\n分配任务到成员...")

    prompt = PromptTemplate.get_subtask_assignment_prompt(subtasks, team_members)
    result = call_gpt_phase4(prompt)

    if not result:
        print(f"✗ 任务分配失败")
        return False

    # 将分配结果写入 team_members
    task_assignments = result.get('task_assignments', [])

    for assignment in task_assignments:
        user_name = assignment['user_name']
        assigned_subtasks = assignment.get('assigned_subtasks', [])

        # 找到对应的成员
        for member in team_members:
            if member['user_name'] == user_name:
                member['subtasks'] = assigned_subtasks
                break

    # 分配完成后，统一为所有 subtask 分配递增的 ID
    subtask_counter = 1
    for member in team_members:
        for subtask in member.get('subtasks', []):
            subtask['subtask_id'] = subtask_counter
            subtask_counter += 1

    print(f"✓ 已为 {subtask_counter - 1} 个 subtasks 分配 ID")

    # 验证任务分配
    if not validate_task_assignment(team_members):
        print("⚠ 任务分配验证未通过，但继续执行")

    print(f"✓ 任务分配完成")

    # 显示统计
    for member in team_members:
        subtasks_count = len(member.get('subtasks', []))
        print(f"  - {member['user_name']}: {subtasks_count} 个任务")

    return True


def validate_task_assignment(team_members: List[Dict]) -> bool:
    """
    验证任务分配是否符合要求

    检查：
    1. 所有成员都被分配了任务
    2. 每个成员至少 MIN_SUBTASKS_PER_MEMBER 个任务
    """
    errors = []

    for member in team_members:
        user_name = member['user_name']
        subtasks = member.get('subtasks', [])

        if len(subtasks) == 0:
            errors.append(f"{user_name} 没有被分配任务")
        elif len(subtasks) < config.MIN_SUBTASKS_PER_MEMBER:
            errors.append(f"{user_name} 的任务数量不足（{len(subtasks)} < {config.MIN_SUBTASKS_PER_MEMBER}）")

    if errors:
        print("任务分配验证失败:")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors)-10} 个错误")
        return False

    return True


# ==================== 文件保存 ====================

def save_sub_topic_project(sub_topic: Dict, team_members: List[Dict], subtasks: List[Dict]):
    """
    保存单个小 Topic 的完整项目数据

    Args:
        sub_topic: 小 topic 数据
        team_members: 团队成员列表（含 subtasks）
        subtasks: 所有 subtask 列表
    """
    topic_name = sub_topic.get('topic', '未命名项目')
    project_dir = os.path.join(config.PROJECTS_DIR, topic_name)
    os.makedirs(project_dir, exist_ok=True)

    file_path = os.path.join(project_dir, f"{topic_name}.json")

    # 计算统计数据
    rank_counts = Counter([m['rank'] for m in team_members])
    total_subtasks = sum(len(m.get('subtasks', [])) for m in team_members)
    avg_subtasks = total_subtasks / len(team_members) if team_members else 0
    phase_dist = Counter([st.get('phase', 'Unknown') for st in subtasks])

    # 构建完整数据结构
    project_data = {
        "sub_topic_info": {
            "sub_topic_id": sub_topic.get('sub_topic_id'),
            "parent_topic_id": sub_topic.get('parent_topic_id'),
            "topic": topic_name,
            "description": sub_topic.get('description', ''),
            "generated_at": datetime.now().isoformat()
        },
        "team_composition": {
            "total_members": len(team_members),
            "rank_distribution": {
                "rank_1": rank_counts.get(1, 0),
                "rank_2": rank_counts.get(2, 0),
                "rank_3": rank_counts.get(3, 0)
            }
        },
        "members": team_members,
        "metadata": {
            "total_subtasks": total_subtasks,
            "avg_subtasks_per_member": round(avg_subtasks, 2),
            "phase_distribution": dict(phase_dist),
            "generation_method": "Topic-Driven Multi-stage",
            "communication_style_adjusted": True
        }
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    print(f"✓ 项目已保存: {file_path}")


# ==================== 统计报告 ====================

def generate_summary_report(major_topics: List[Dict], sub_topics_data: List[Dict]):
    """
    生成统计报告

    Args:
        major_topics: 大 topic 列表
        sub_topics_data: 小 topic 完整数据列表（含 team_members）
    """
    print(f"\n{'='*60}")
    print("生成统计报告...")
    print(f"{'='*60}")

    total_projects = len(sub_topics_data)
    total_tasks = sum([st['metadata']['total_subtasks'] for st in sub_topics_data])

    # 员工参与度
    all_participants = set()
    employee_participation = {}

    for st in sub_topics_data:
        sub_topic_id = st['sub_topic_info']['sub_topic_id']
        for member in st['members']:
            user_name = member['user_name']
            all_participants.add(user_name)

            if user_name not in employee_participation:
                employee_participation[user_name] = {
                    "projects_participated": [],
                    "total_tasks": 0,
                    "rank": member['rank']
                }

            employee_participation[user_name]['projects_participated'].append(sub_topic_id)
            employee_participation[user_name]['total_tasks'] += len(member.get('subtasks', []))

    # 技能使用频率
    skill_usage = Counter()
    for st in sub_topics_data:
        for member in st['members']:
            for skill in member.get('hard_skills', []):
                skill_usage[skill['skill']] += 1

    # 项目摘要
    projects_summary = []
    for st in sub_topics_data:
        projects_summary.append({
            "sub_topic_id": st['sub_topic_info']['sub_topic_id'],
            "parent_topic_id": st['sub_topic_info']['parent_topic_id'],
            "topic": st['sub_topic_info']['topic'],
            "team_size": st['team_composition']['total_members'],
            "total_subtasks": st['metadata']['total_subtasks']
        })

    # 构建报告
    summary = {
        "generation_time": datetime.now().isoformat(),
        "major_topics_count": len(major_topics),
        "sub_topics_count": total_projects,
        "total_tasks": total_tasks,
        "total_unique_employees": len(all_participants),
        "major_topics_summary": [
            {
                "topic_id": mt['topic_id'],
                "topic": mt['topic'],
                "sub_topics_count": len([st for st in sub_topics_data
                                        if st['sub_topic_info']['parent_topic_id'] == mt['topic_id']])
            }
            for mt in major_topics
        ],
        "projects_summary": projects_summary,
        "employee_participation": employee_participation,
        "skill_usage_frequency": dict(skill_usage.most_common(30))
    }

    with open(config.PROJECTS_SUMMARY_REPORT, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✓ 统计报告生成完成")
    print(f"  - 大 Topic 总数: {len(major_topics)}")
    print(f"  - 小 Topic 总数: {total_projects}")
    print(f"  - 任务总数: {total_tasks}")
    print(f"  - 参与员工: {len(all_participants)} 人")
    print(f"✓ 统计报告已保存: {config.PROJECTS_SUMMARY_REPORT}")


# ==================== 主函数 ====================

def main():
    """
    主流程：Topic-Driven Task Generation
    """
    print("\n" + "="*60)
    print("Phase 4: Topic-Driven Task Generation")
    print("="*60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建输出目录
    os.makedirs(config.PROJECTS_DIR, exist_ok=True)

    # 1. 加载全量员工数据
    print("\n[步骤 1/6] 加载员工数据...")
    all_employees = load_all_employees()

    if all_employees is None:
        print("✗ 加载数据失败")
        return 1

    # 2. 生成大 Topic
    print("\n[步骤 2/6] 生成大 Topic...")
    major_topics = generate_major_topics()

    if not major_topics:
        print("✗ 生成大 Topic 失败")
        return 1

    save_major_topics(major_topics)

    # 3. 拆分小 Topic
    print(f"\n[步骤 3/6] 拆分小 Topic...")
    print(f"将为 {len(major_topics)} 个大 Topic 各拆分为 {config.NUM_SUB_TOPICS_PER_MAJOR} 个小 Topic")

    all_sub_topics = []
    for i, major_topic in enumerate(major_topics, 1):
        print(f"\n--- 处理大 Topic {i}/{len(major_topics)} ---")
        sub_topics = generate_sub_topics(major_topic)
        if sub_topics:
            all_sub_topics.extend(sub_topics)

    if not all_sub_topics:
        print("✗ 拆分小 Topic 失败")
        return 1

    save_sub_topics(all_sub_topics)
    print(f"\n✓ 共生成 {len(all_sub_topics)} 个小 Topic")

    # 4. 为每个小 Topic 选择团队、调整沟通风格、生成任务、分配任务
    print(f"\n[步骤 4/7] 为每个小 Topic 选择团队...")
    print(f"\n[步骤 5/7] 调整 Communication Style...")
    print(f"\n[步骤 6/7] 生成并排序 Subtask...")
    print(f"\n[步骤 7/7] 分配 Subtask 到成员...")

    sub_topics_full_data = []

    for i, sub_topic in enumerate(all_sub_topics, 1):
        print(f"\n{'='*60}")
        print(f"处理小 Topic {i}/{len(all_sub_topics)}")
        print(f"{'='*60}")

        # Stage 3: 选择团队
        team_members = select_team_members(sub_topic, all_employees)
        if not team_members:
            print(f"✗ 小 Topic {i} 团队选择失败，跳过")
            continue

        # Stage 3.5: 调整 Communication Style
        success = adjust_communication_styles(sub_topic, team_members)
        if not success:
            print(f"✗ 小 Topic {i} Communication Style 调整失败，跳过")
            continue

        # Stage 4: 生成并排序 Subtask
        subtasks = generate_and_sequence_subtasks(sub_topic, team_members)
        if not subtasks:
            print(f"✗ 小 Topic {i} 任务生成失败，跳过")
            continue

        # Stage 5: 分配 Subtask 到成员
        success = assign_subtasks_to_members(subtasks, team_members)
        if not success:
            print(f"✗ 小 Topic {i} 任务分配失败，跳过")
            continue

        # 保存项目
        save_sub_topic_project(sub_topic, team_members, subtasks)

        # 保存完整数据用于统计报告
        rank_counts = Counter([m['rank'] for m in team_members])
        sub_topics_full_data.append({
            "sub_topic_info": sub_topic,
            "members": team_members,
            "team_composition": {
                "total_members": len(team_members),
                "rank_1_count": rank_counts.get(1, 0),
                "rank_2_count": rank_counts.get(2, 0),
                "rank_3_count": rank_counts.get(3, 0)
            },
            "metadata": {
                "total_subtasks": len(subtasks),
                "phase_distribution": dict(Counter([st.get('phase', 'Unknown') for st in subtasks]))
            }
        })

        print(f"\n✓ 小 Topic {i} 完成")

    # 5. 生成统计报告
    print("\n[报告] 生成统计报告...")
    generate_summary_report(major_topics, sub_topics_full_data)

    # 6. 打印总结
    print("\n" + "="*60)
    print("✅ 所有项目生成完成！")
    print("="*60)
    print(f"大 Topic 数量: {len(major_topics)}")
    print(f"小 Topic 数量: {len(sub_topics_full_data)}")
    print(f"总任务数: {sum(st['metadata']['total_subtasks'] for st in sub_topics_full_data)}")

    print(f"\n大 Topic 列表:")
    for i, mt in enumerate(major_topics, 1):
        print(f"  {i}. {mt['topic']}")

    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
