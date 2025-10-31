#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Phase 5: 任务时间线分配
为每个项目的所有subtasks分配deadline时间
"""

import os
import json
import re
import time
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI

import config
from prompt import get_task_timeline_assignment_prompt


def load_project_file(project_path: str) -> dict:
    """加载项目JSON文件"""
    with open(project_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_project_file(project_path: str, project_data: dict):
    """保存项目JSON文件"""
    with open(project_path, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)


def call_gpt_for_timeline(
    project_info: dict,
    members_with_subtasks: list,
    max_retries: int = None
) -> dict:
    """
    调用GPT API进行任务时间线分配

    Returns:
        包含task_timeline的字典
    """
    if max_retries is None:
        max_retries = config.MAX_RETRIES

    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

    prompt = get_task_timeline_assignment_prompt(
        project_info=project_info,
        members_with_subtasks=members_with_subtasks,
        start_date=config.TIMELINE_START_DATE,
        end_date=config.TIMELINE_END_DATE
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一位专业的项目管理专家。"},
                    {"role": "user", "content": prompt}
                ],
                **config.API_PARAMS
            )

            content = response.choices[0].message.content.strip()

            # 清理markdown代码块标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # 清理控制字符（移除未转义的换行符、制表符等）
            content = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', content)

            # 尝试提取 JSON（处理前后可能有额外文字的情况）
            # 找到第一个 { 和最后一个 }
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
                raise ValueError(f"无法在响应中找到有效的 JSON 对象\n响应前200字符: {content[:200]}")

            json_str = content[start_idx:end_idx+1]

            # 解析JSON
            result = json.loads(json_str)

            # 验证必要字段
            if 'task_timeline' not in result:
                raise ValueError("返回结果缺少 task_timeline 字段")

            return result

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON解析失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(config.RETRY_DELAY)
            else:
                raise

        except Exception as e:
            print(f"  ⚠️  API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(config.RETRY_DELAY)
            else:
                raise


def validate_timeline(
    project_data: dict,
    timeline_result: dict,
    start_date: str,
    end_date: str
) -> dict:
    """
    验证时间线分配的有效性

    Returns:
        验证报告字典 {'valid': bool, 'errors': list, 'warnings': list}
    """
    errors = []
    warnings = []

    # 1. 检查任务数量
    total_subtasks = sum(len(m.get('subtasks', [])) for m in project_data['members'])
    assigned_tasks = len(timeline_result.get('task_timeline', []))

    if assigned_tasks != total_subtasks:
        errors.append(f"任务数量不匹配: 预期{total_subtasks}个，实际分配{assigned_tasks}个")

    # 2. 检查每个任务
    task_ids_in_project = set()
    for member in project_data['members']:
        for subtask in member.get('subtasks', []):
            task_ids_in_project.add(subtask['subtask_id'])

    task_ids_assigned = set()
    for task in timeline_result.get('task_timeline', []):
        task_id = task.get('subtask_id')
        deadline = task.get('deadline')

        # 检查是否有subtask_id
        if task_id is None:
            errors.append(f"任务缺少subtask_id字段")
            continue

        task_ids_assigned.add(task_id)

        # 检查deadline格式
        if not deadline:
            errors.append(f"任务{task_id}缺少deadline字段")
            continue

        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            if not (start <= deadline_date <= end):
                errors.append(f"任务{task_id}的deadline {deadline} 超出范围 [{start_date}, {end_date}]")

        except ValueError:
            errors.append(f"任务{task_id}的deadline格式错误: {deadline}")

    # 3. 检查缺失的任务
    missing_tasks = task_ids_in_project - task_ids_assigned
    if missing_tasks:
        errors.append(f"以下任务未被分配时间: {sorted(missing_tasks)}")

    # 4. 检查多余的任务
    extra_tasks = task_ids_assigned - task_ids_in_project
    if extra_tasks:
        warnings.append(f"以下任务不在原项目中: {sorted(extra_tasks)}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'total_subtasks': total_subtasks,
        'assigned_tasks': assigned_tasks
    }


def apply_timeline_to_project(
    project_data: dict,
    timeline_result: dict
) -> dict:
    """
    将时间线分配结果应用到项目数据中

    Returns:
        更新后的project_data
    """
    # 创建subtask_id到deadline的映射
    deadline_map = {}
    for task in timeline_result.get('task_timeline', []):
        task_id = task.get('subtask_id')
        deadline = task.get('deadline')
        if task_id and deadline:
            deadline_map[task_id] = deadline

    # 更新每个member的subtasks
    for member in project_data['members']:
        for subtask in member.get('subtasks', []):
            task_id = subtask['subtask_id']
            if task_id in deadline_map:
                subtask['deadline'] = deadline_map[task_id]

    return project_data


def process_single_project(
    project_path: Path,
    output_dir: Path
) -> dict:
    """
    处理单个项目的时间线分配

    Returns:
        处理报告字典
    """
    project_name = project_path.stem
    print(f"\n处理项目: {project_name}")

    # 1. 加载项目数据
    project_data = load_project_file(str(project_path))
    # 新架构使用 sub_topic_info 而不是 project_info
    sub_topic_info = project_data.get('sub_topic_info', {})
    members = project_data.get('members', [])

    total_subtasks = sum(len(m.get('subtasks', [])) for m in members)
    print(f"  任务总数: {total_subtasks}")

    # 2. 调用GPT进行时间线分配
    print(f"  调用GPT进行时间线分配...")
    # 将 sub_topic_info 转换为 prompt 期望的格式
    project_info_for_prompt = {
        'project_number': sub_topic_info.get('sub_topic_id', ''),
        'project_topic': sub_topic_info.get('topic', ''),
        'project_description': sub_topic_info.get('description', '')
    }
    timeline_result = call_gpt_for_timeline(
        project_info=project_info_for_prompt,
        members_with_subtasks=members
    )

    # 3. 验证结果
    print(f"  验证时间线分配...")
    validation = validate_timeline(
        project_data=project_data,
        timeline_result=timeline_result,
        start_date=config.TIMELINE_START_DATE,
        end_date=config.TIMELINE_END_DATE
    )

    if not validation['valid']:
        print(f"  ❌ 验证失败:")
        for error in validation['errors']:
            print(f"    - {error}")
        raise ValueError(f"项目 {project_name} 时间线分配验证失败")

    if validation['warnings']:
        print(f"  ⚠️  警告:")
        for warning in validation['warnings']:
            print(f"    - {warning}")

    print(f"  ✅ 验证通过")

    # 4. 应用时间线到项目数据
    updated_project_data = apply_timeline_to_project(project_data, timeline_result)

    # 5. 保存更新后的项目文件
    save_project_file(str(project_path), updated_project_data)
    print(f"  💾 已保存更新后的项目文件")

    # 6. 返回处理报告
    return {
        'project_name': project_name,
        'sub_topic_id': sub_topic_info.get('sub_topic_id'),
        'parent_topic_id': sub_topic_info.get('parent_topic_id'),
        'success': True,
        'total_subtasks': total_subtasks,
        'assigned_tasks': validation['assigned_tasks'],
        'validation': validation,
        'timeline_summary': timeline_result.get('timeline_summary', {})
    }


def generate_summary_report(project_reports: list, output_dir: Path):
    """生成汇总报告"""
    report = {
        'generation_time': datetime.now().isoformat(),
        'total_projects': len(project_reports),
        'timeline_config': {
            'start_date': config.TIMELINE_START_DATE,
            'end_date': config.TIMELINE_END_DATE
        },
        'projects': project_reports,
        'statistics': {
            'total_tasks_processed': sum(p.get('total_subtasks', 0) for p in project_reports if p.get('success')),
            'successful_projects': len([p for p in project_reports if p.get('success')]),
            'failed_projects': len([p for p in project_reports if not p.get('success')])
        }
    }

    report_path = output_dir / 'timeline_assignment_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📊 汇总报告已保存: {report_path}")
    return report


def main():
    """主函数"""
    print("="*60)
    print("Phase 5: 任务时间线分配")
    print("="*60)

    # 1. 确定项目目录
    output_dir = Path(config.OUTPUT_DIR)
    projects_dir = output_dir / 'projects'

    if not projects_dir.exists():
        print(f"❌ 项目目录不存在: {projects_dir}")
        return

    # 2. 查找所有项目文件
    project_files = list(projects_dir.glob('*/*.json'))
    project_files = [f for f in project_files if f.stem != 'summary_report']

    if not project_files:
        print(f"❌ 未找到项目文件")
        return

    print(f"\n找到 {len(project_files)} 个项目")
    print(f"时间范围: {config.TIMELINE_START_DATE} ~ {config.TIMELINE_END_DATE}")
    print("")

    # 3. 处理每个项目
    project_reports = []
    for project_file in tqdm(project_files, desc="处理项目"):
        try:
            report = process_single_project(project_file, output_dir)
            project_reports.append(report)
        except Exception as e:
            print(f"\n❌ 处理失败: {project_file.stem}")
            print(f"   错误: {e}")
            project_reports.append({
                'project_name': project_file.stem,
                'success': False,
                'error': str(e)
            })

    # 4. 生成汇总报告
    generate_summary_report(project_reports, output_dir)

    # 5. 输出统计信息
    success_count = len([p for p in project_reports if p.get('success')])
    print(f"\n{'='*60}")
    print(f"✅ 成功: {success_count}/{len(project_files)} 个项目")
    if success_count < len(project_files):
        print(f"❌ 失败: {len(project_files) - success_count} 个项目")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
