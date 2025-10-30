#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: Communication Style Assignment
为员工分配8维度的沟通风格特征
"""

import os
import sys
import json
import time
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import Counter

# 第三方库
try:
    from openai import OpenAI
    from tqdm import tqdm
except ImportError as e:
    print(f"错误: 缺少必要的依赖库 - {e}")
    print("请运行: pip install openai pandas openpyxl python-dotenv tqdm")
    sys.exit(1)

# 导入配置和提示词
import config
from prompt import PromptTemplate


# ========== Communication Style Universe 生成 ==========

def generate_communication_style_universe() -> Dict:
    """
    硬编码生成Communication Style Universe
    不调用GPT-5，直接在代码中定义9个维度

    返回:
        完整的沟通风格维度定义字典
    """
    print(f"\n{'='*60}")
    print("生成Communication Style Universe...")
    print(f"{'='*60}")

    universe = {
        "communication_style_universe": [
            {
                "dimension": "Formality",
                "description": "正式程度",
                "levels": {
                    "high": {
                        "label": "Formal",
                        "description": "使用正式语言，遵循商务礼仪，注重称谓和头衔"
                    },
                    "medium": {
                        "label": "Semi-formal",
                        "description": "适度正式，根据场合调整语气，保持专业但不僵化"
                    },
                    "low": {
                        "label": "Casual",
                        "description": "轻松随意，使用口语化表达，注重亲和力"
                    }
                }
            },
            {
                "dimension": "Verbosity",
                "description": "话语详细程度",
                "levels": {
                    "high": {
                        "label": "Detailed",
                        "description": "提供全面的背景信息，详细解释每个步骤和原因"
                    },
                    "medium": {
                        "label": "Moderate",
                        "description": "平衡信息量，提供必要细节但不冗余"
                    },
                    "low": {
                        "label": "Concise",
                        "description": "直击要点，精简表达，省略不必要的细节"
                    }
                }
            },
            {
                "dimension": "Humor",
                "description": "幽默感使用",
                "levels": {
                    "high": {
                        "label": "Frequent",
                        "description": "经常使用幽默、玩笑和轻松的表达方式"
                    },
                    "medium": {
                        "label": "Occasional",
                        "description": "偶尔使用幽默，视场合和对象调整"
                    },
                    "low": {
                        "label": "Minimal",
                        "description": "很少使用幽默，保持严肃和专业的沟通方式"
                    }
                }
            },
            {
                "dimension": "Jargon_Usage",
                "description": "专业术语使用",
                "levels": {
                    "high": {
                        "label": "Technical",
                        "description": "大量使用行业术语和技术语言，假设对方具备专业知识"
                    },
                    "medium": {
                        "label": "Balanced",
                        "description": "适度使用专业术语，同时提供必要的解释"
                    },
                    "low": {
                        "label": "Plain",
                        "description": "使用通俗易懂的语言，避免专业术语，强调清晰性"
                    }
                }
            },
            {
                "dimension": "Emoji_Usage",
                "description": "表情符号使用",
                "levels": {
                    "high": {
                        "label": "Frequent",
                        "description": "经常使用表情符号增强情感表达"
                    },
                    "medium": {
                        "label": "Occasional",
                        "description": "偶尔使用表情符号，保持适度"
                    },
                    "low": {
                        "label": "Rare",
                        "description": "很少或从不使用表情符号，保持正式文字沟通"
                    }
                }
            },
            {
                "dimension": "Directness",
                "description": "表达直接程度",
                "levels": {
                    "high": {
                        "label": "Direct",
                        "description": "直接表达观点和需求，不绕弯子"
                    },
                    "medium": {
                        "label": "Balanced",
                        "description": "在直接和委婉之间找到平衡，根据情况调整"
                    },
                    "low": {
                        "label": "Indirect",
                        "description": "委婉表达，注重礼貌和他人感受，避免冲突"
                    }
                }
            },
            {
                "dimension": "Warmth",
                "description": "情感温度",
                "levels": {
                    "high": {
                        "label": "Warm",
                        "description": "热情友好，表现出强烈的个人关怀和情感投入"
                    },
                    "medium": {
                        "label": "Friendly",
                        "description": "友好亲切，保持专业的同时表现出善意"
                    },
                    "low": {
                        "label": "Neutral",
                        "description": "中立客观，保持情感距离，注重事实和逻辑"
                    }
                }
            },
            {
                "dimension": "Questioning_Style",
                "description": "提问方式",
                "levels": {
                    "high": {
                        "label": "Probing",
                        "description": "深入探究，追问细节，挑战假设，寻求深层理解"
                    },
                    "medium": {
                        "label": "Clarifying",
                        "description": "澄清确认，确保理解准确，避免误解"
                    },
                    "low": {
                        "label": "Accepting",
                        "description": "接受为主，较少质疑，倾向于相信和接受他人的观点"
                    }
                }
            }
        ],
        "total_dimensions": 8,
        "metadata": {
            "version": "1.0",
            "generated_by": "3_assign_communicationstyle.py",
            "generated_at": datetime.now().isoformat(),
            "principle": "互不冲突、无父子关系、三级分类"
        }
    }

    # 保存到文件
    try:
        with open(config.COMMUNICATION_STYLE_UNIVERSE_FILE, 'w', encoding='utf-8') as f:
            json.dump(universe, f, ensure_ascii=False, indent=2)
        print(f"✓ Communication Style Universe 已保存: {config.COMMUNICATION_STYLE_UNIVERSE_FILE}")
        print(f"✓ 总维度数: {universe['total_dimensions']}")
    except Exception as e:
        print(f"✗ 保存文件失败: {e}")
        return None

    return universe


# ========== 数据加载模块 ==========

def load_employees_with_hardskills() -> Optional[pd.DataFrame]:
    """
    加载包含硬技能的员工数据（Phase 2的输出）

    返回:
        DataFrame 或 None（如果加载失败）
    """
    print(f"\n{'='*60}")
    print("加载员工数据...")
    print(f"{'='*60}")

    file_path = config.EMPLOYEES_WITH_HARDSKILLS_FILE

    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        print(f"  请先运行 2_assign_hardskill.py 生成硬技能数据")
        return None

    try:
        df = pd.read_excel(file_path)
        print(f"✓ 成功加载 {len(df)} 名员工数据")

        # 验证必要的列
        required_columns = ["Name", "Title", "Team", "Rank", "Hard_Skills"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"✗ 缺少必要的列: {', '.join(missing_columns)}")
            return None

        print(f"✓ 数据验证通过")
        return df

    except Exception as e:
        print(f"✗ 读取文件失败: {e}")
        return None


# ========== GPT API 调用模块 ==========

def call_gpt5(prompt: str, max_retries: int = None) -> Optional[Dict]:
    """
    调用 GPT-5 API

    参数:
        prompt: 提示词
        max_retries: 最大重试次数（默认使用配置值）

    返回:
        解析后的JSON数据或None
    """
    if max_retries is None:
        max_retries = config.MAX_RETRIES

    # 初始化 OpenAI 客户端（通过 OpenRouter）
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "你是一位专业的组织行为学专家。"},
                    {"role": "user", "content": prompt}
                ],
                **config.API_PARAMS
            )

            content = response.choices[0].message.content.strip()

            # 尝试提取JSON（去除markdown代码块标记）
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # 解析JSON
            data = json.loads(content)
            return data

        except json.JSONDecodeError as e:
            print(f"  ⚠ 第{attempt}次尝试: JSON解析失败 - {e}")
            if attempt < max_retries:
                print(f"  ⏳ {config.RETRY_DELAY}秒后重试...")
                time.sleep(config.RETRY_DELAY)
            else:
                print(f"  ✗ 已达到最大重试次数({max_retries})，跳过此批次")
                return None

        except Exception as e:
            print(f"  ⚠ 第{attempt}次尝试: API调用失败 - {e}")
            if attempt < max_retries:
                print(f"  ⏳ {config.RETRY_DELAY}秒后重试...")
                time.sleep(config.RETRY_DELAY)
            else:
                print(f"  ✗ 已达到最大重试次数({max_retries})，跳过此批次")
                return None

    return None


# ========== Communication Style 分配模块 ==========

def validate_communication_style(style: Dict, universe: Dict) -> Tuple[bool, List[str]]:
    """
    验证单个员工的沟通风格是否有效

    参数:
        style: 员工的沟通风格字典
        universe: 沟通风格维度定义

    返回:
        (是否有效, 错误列表)
    """
    errors = []

    # 构建维度到有效级别的映射
    valid_levels = {}
    for dim in universe.get("communication_style_universe", []):
        dimension = dim["dimension"]
        levels = dim["levels"]
        valid_levels[dimension] = [
            levels["high"]["label"],
            levels["medium"]["label"],
            levels["low"]["label"]
        ]

    # 检查每个维度
    for dimension, valid_list in valid_levels.items():
        if dimension not in style:
            errors.append(f"缺少维度: {dimension}")
        elif style[dimension] not in valid_list:
            errors.append(f"{dimension}: '{style[dimension]}' 不在有效值 {valid_list} 中")

    # 检查是否有多余的维度
    for dimension in style.keys():
        if dimension not in valid_levels:
            errors.append(f"未知维度: {dimension}")

    return len(errors) == 0, errors


def assign_communication_styles_in_batches(df: pd.DataFrame,
                                           universe: Dict,
                                           batch_size: int = 10) -> Dict[str, Dict]:
    """
    批量分配Communication Style

    参数:
        df: 员工数据DataFrame
        universe: 沟通风格维度定义
        batch_size: 每批处理的员工数

    返回:
        {员工姓名: 沟通风格字典} 的映射
    """
    print(f"\n{'='*60}")
    print("批量分配Communication Style...")
    print(f"{'='*60}")

    employees = df.to_dict('records')
    total_employees = len(employees)
    total_batches = (total_employees + batch_size - 1) // batch_size

    assignments = {}
    validation_warnings = []

    print(f"总员工数: {total_employees}")
    print(f"批量大小: {batch_size}")
    print(f"总批次数: {total_batches}")

    with tqdm(total=total_employees, desc="分配进度", unit="员工") as pbar:
        for batch_num in range(1, total_batches + 1):
            # 计算当前批次的员工
            start_idx = (batch_num - 1) * batch_size
            end_idx = min(start_idx + batch_size, total_employees)
            batch_employees = employees[start_idx:end_idx]

            print(f"\n批次 {batch_num}/{total_batches}: 处理 {len(batch_employees)} 名员工")

            # 生成提示词
            prompt = PromptTemplate.get_communication_style_assignment_prompt(
                batch_employees,
                universe,
                batch_num
            )

            # 调用 GPT-5
            response_data = call_gpt5(prompt)

            if response_data is None:
                print(f"  ✗ 批次 {batch_num} 失败，跳过")
                pbar.update(len(batch_employees))
                continue

            # 解析分配结果
            batch_assignments = response_data.get("assignments", [])

            if len(batch_assignments) != len(batch_employees):
                print(f"  ⚠ 警告: 返回的分配数({len(batch_assignments)})与批次员工数({len(batch_employees)})不匹配")

            # 验证并保存每个员工的分配
            for assignment in batch_assignments:
                name = assignment.get("name", "")
                comm_style = assignment.get("communication_style", {})
                reasoning = assignment.get("reasoning", "")

                # 验证
                is_valid, errors = validate_communication_style(comm_style, universe)

                if is_valid:
                    assignments[name] = comm_style
                else:
                    warning = f"员工 {name} 的沟通风格验证失败: {', '.join(errors)}"
                    validation_warnings.append(warning)
                    print(f"  ⚠ {warning}")

            print(f"  ✓ 批次 {batch_num} 完成: {len(batch_assignments)} 个分配")
            pbar.update(len(batch_employees))

            # 短暂延迟，避免API限流
            if batch_num < total_batches:
                time.sleep(0.5)

    print(f"\n✓ 分配完成！")
    print(f"  - 成功分配: {len(assignments)} 名员工")
    print(f"  - 验证警告: {len(validation_warnings)} 条")

    return assignments


# ========== 统计和报告生成 ==========

def generate_distribution_report(assignments: Dict[str, Dict]) -> Dict:
    """
    生成每个维度的分布统计

    参数:
        assignments: {员工姓名: 沟通风格} 映射

    返回:
        统计报告字典
    """
    print(f"\n{'='*60}")
    print("生成分布统计报告...")
    print(f"{'='*60}")

    # 收集每个维度的值
    dimension_values = {}

    for name, style in assignments.items():
        for dimension, level in style.items():
            if dimension not in dimension_values:
                dimension_values[dimension] = []
            dimension_values[dimension].append(level)

    # 计算分布
    distribution = {}
    for dimension, values in dimension_values.items():
        counter = Counter(values)
        distribution[dimension] = dict(counter)

        print(f"\n{dimension}:")
        for level, count in sorted(counter.items(), key=lambda x: -x[1]):
            percentage = (count / len(values)) * 100
            print(f"  - {level}: {count} ({percentage:.1f}%)")

    return distribution


def save_results(df: pd.DataFrame, assignments: Dict[str, Dict],
                distribution: Dict, start_time: datetime) -> None:
    """
    保存结果到Excel和JSON报告

    参数:
        df: 原始DataFrame
        assignments: 沟通风格分配
        distribution: 分布统计
        start_time: 开始时间
    """
    print(f"\n{'='*60}")
    print("保存结果...")
    print(f"{'='*60}")

    # 添加Communication_Style列
    df['Communication_Style'] = df['Name'].map(
        lambda name: json.dumps(assignments.get(name, {}), ensure_ascii=False) if name in assignments else ""
    )

    # 保存Excel
    try:
        df.to_excel(config.EMPLOYEES_WITH_COMMUNICATION_STYLE_FILE, index=False)
        print(f"✓ Excel文件已保存: {config.EMPLOYEES_WITH_COMMUNICATION_STYLE_FILE}")
    except Exception as e:
        print(f"✗ 保存Excel失败: {e}")

    # 生成JSON报告
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()

    report = {
        "summary": {
            "total_employees": len(df),
            "assigned_employees": len(assignments),
            "batch_size": config.COMMUNICATION_STYLE_BATCH_SIZE,
            "total_batches": (len(df) + config.COMMUNICATION_STYLE_BATCH_SIZE - 1) // config.COMMUNICATION_STYLE_BATCH_SIZE,
            "execution_time_seconds": round(execution_time, 2),
            "success_rate": f"{(len(assignments) / len(df) * 100):.1f}%" if len(df) > 0 else "0%",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        "dimension_distribution": distribution,
        "validation": {
            "all_employees_assigned": len(assignments) == len(df),
            "missing_assignments": len(df) - len(assignments)
        }
    }

    # 保存报告
    try:
        with open(config.COMMUNICATION_STYLE_ASSIGNMENT_REPORT, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"✓ 报告文件已保存: {config.COMMUNICATION_STYLE_ASSIGNMENT_REPORT}")
    except Exception as e:
        print(f"✗ 保存报告失败: {e}")

    # 打印摘要
    print(f"\n{'='*60}")
    print("执行摘要")
    print(f"{'='*60}")
    print(f"总员工数: {report['summary']['total_employees']}")
    print(f"成功分配: {report['summary']['assigned_employees']}")
    print(f"成功率: {report['summary']['success_rate']}")
    print(f"执行时间: {report['summary']['execution_time_seconds']} 秒")
    print(f"批量大小: {report['summary']['batch_size']}")
    print(f"总批次数: {report['summary']['total_batches']}")


# ========== 主函数 ==========

def main():
    """
    主函数：执行完整的Communication Style分配流程
    """
    print("\n" + "="*60)
    print("Phase 3: Communication Style Assignment")
    print("="*60)

    start_time = datetime.now()

    # 1. 生成Communication Style Universe
    universe = generate_communication_style_universe()
    if universe is None:
        print("\n✗ Communication Style Universe 生成失败，程序终止")
        sys.exit(1)

    # 2. 加载员工数据
    df = load_employees_with_hardskills()
    if df is None:
        print("\n✗ 员工数据加载失败，程序终止")
        sys.exit(1)

    # 3. 批量分配Communication Style
    assignments = assign_communication_styles_in_batches(
        df,
        universe,
        batch_size=config.COMMUNICATION_STYLE_BATCH_SIZE
    )

    if not assignments:
        print("\n✗ Communication Style 分配失败，程序终止")
        sys.exit(1)

    # 4. 生成分布统计
    distribution = generate_distribution_report(assignments)

    # 5. 保存结果
    save_results(df, assignments, distribution, start_time)

    print(f"\n{'='*60}")
    print("✓ Phase 3 完成！")
    print(f"{'='*60}")
    print(f"\n输出文件:")
    print(f"  - {config.EMPLOYEES_WITH_COMMUNICATION_STYLE_FILE}")
    print(f"  - {config.COMMUNICATION_STYLE_ASSIGNMENT_REPORT}")
    print(f"  - {config.COMMUNICATION_STYLE_UNIVERSE_FILE}")


if __name__ == "__main__":
    main()
