#!/usr/bin/env python3
"""
根据question_id分类计算正确率
question_id格式: "MA_U_Top004_031" -> 大类=MA, 小类=U
"""

import json
import argparse
from collections import defaultdict
from pathlib import Path


def parse_question_id(question_id: str) -> tuple[str, str]:
    """
    解析question_id，提取大类和小类
    例如: "MA_U_Top004_031" -> ("MA", "U")
    例如: "P_Skill_Top004_001" -> ("P", "Skill")
    """
    parts = question_id.split("_")
    if len(parts) >= 2:
        major_category = parts[0]
        minor_category = parts[1]
        return major_category, minor_category
    return "Unknown", "Unknown"


def calculate_accuracy(results: list[dict]) -> dict:
    """计算各分类的正确率"""
    
    # 统计数据结构
    stats = {
        "major": defaultdict(lambda: {"total": 0, "correct": 0}),
        "minor": defaultdict(lambda: {"total": 0, "correct": 0}),
        "combined": defaultdict(lambda: {"total": 0, "correct": 0}),
        "hierarchical": defaultdict(lambda: defaultdict(lambda: {"total": 0, "correct": 0})),  # 大类->小类层级
    }
    
    for item in results:
        question_id = item.get("question_id", "")
        is_correct = item.get("is_correct", False)
        
        major, minor = parse_question_id(question_id)
        combined_key = f"{major}_{minor}"
        
        # 更新大类统计
        stats["major"][major]["total"] += 1
        if is_correct:
            stats["major"][major]["correct"] += 1
        
        # 更新小类统计
        stats["minor"][minor]["total"] += 1
        if is_correct:
            stats["minor"][minor]["correct"] += 1
        
        # 更新组合统计
        stats["combined"][combined_key]["total"] += 1
        if is_correct:
            stats["combined"][combined_key]["correct"] += 1
        
        # 更新层级统计 (大类 -> 小类)
        stats["hierarchical"][major][minor]["total"] += 1
        if is_correct:
            stats["hierarchical"][major][minor]["correct"] += 1
    
    return stats


def format_results(stats: dict) -> dict:
    """格式化结果，计算正确率"""
    formatted = {}
    
    for category_type, data in stats.items():
        if category_type == "hierarchical":
            # 处理层级数据
            formatted[category_type] = {}
            for major, minor_data in sorted(data.items()):
                formatted[category_type][major] = {}
                for minor, values in sorted(minor_data.items()):
                    total = values["total"]
                    correct = values["correct"]
                    accuracy = correct / total if total > 0 else 0
                    formatted[category_type][major][minor] = {
                        "total": total,
                        "correct": correct,
                        "accuracy": round(accuracy, 4),
                        "accuracy_percent": f"{accuracy * 100:.2f}%"
                    }
        else:
            formatted[category_type] = {}
            for key, values in sorted(data.items()):
                total = values["total"]
                correct = values["correct"]
                accuracy = correct / total if total > 0 else 0
                formatted[category_type][key] = {
                    "total": total,
                    "correct": correct,
                    "accuracy": round(accuracy, 4),
                    "accuracy_percent": f"{accuracy * 100:.2f}%"
                }
    
    return formatted


def print_results(formatted: dict):
    """美观地打印结果"""
    
    print("=" * 70)
    print("📊 评估结果分类正确率分析")
    print("=" * 70)
    
    # 打印大类统计
    print("\n🔷 大类 (Major Category) 正确率:")
    print("-" * 50)
    print(f"{'分类':<10} {'总数':>8} {'正确':>8} {'正确率':>12}")
    print("-" * 50)
    
    major_stats = formatted["major"]
    total_all = sum(v["total"] for v in major_stats.values())
    correct_all = sum(v["correct"] for v in major_stats.values())
    
    for key, values in sorted(major_stats.items()):
        print(f"{key:<10} {values['total']:>8} {values['correct']:>8} {values['accuracy_percent']:>12}")
    
    print("-" * 50)
    overall_acc = correct_all / total_all if total_all > 0 else 0
    print(f"{'总计':<10} {total_all:>8} {correct_all:>8} {overall_acc * 100:>11.2f}%")
    
    # 打印小类统计
    print("\n🔹 小类 (Minor Category) 正确率:")
    print("-" * 50)
    print(f"{'分类':<10} {'总数':>8} {'正确':>8} {'正确率':>12}")
    print("-" * 50)
    
    for key, values in sorted(formatted["minor"].items()):
        print(f"{key:<10} {values['total']:>8} {values['correct']:>8} {values['accuracy_percent']:>12}")
    
    # 打印层级统计 (大类 -> 小类)
    print("\n🔶 大类+小类层级 (Hierarchical) 正确率:")
    print("-" * 55)
    
    for major, minor_data in sorted(formatted["hierarchical"].items()):
        # 计算该大类的汇总
        major_total = sum(v["total"] for v in minor_data.values())
        major_correct = sum(v["correct"] for v in minor_data.values())
        major_acc = major_correct / major_total if major_total > 0 else 0
        
        print(f"\n  📂 {major} (汇总: {major_total}题, 正确{major_correct}, {major_acc*100:.2f}%)")
        print(f"  {'-' * 50}")
        print(f"  {'小类':<10} {'总数':>8} {'正确':>8} {'正确率':>12}")
        print(f"  {'-' * 50}")
        
        for minor, values in sorted(minor_data.items()):
            print(f"  {minor:<10} {values['total']:>8} {values['correct']:>8} {values['accuracy_percent']:>12}")
    
    # 打印组合统计
    print("\n\n🔸 大类+小类组合 (Combined) 正确率:")
    print("-" * 50)
    print(f"{'分类':<15} {'总数':>8} {'正确':>8} {'正确率':>12}")
    print("-" * 50)
    
    for key, values in sorted(formatted["combined"].items()):
        print(f"{key:<15} {values['total']:>8} {values['correct']:>8} {values['accuracy_percent']:>12}")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="根据question_id分类计算评估正确率")
    parser.add_argument(
        "input_file",
        type=str,
        nargs="?",
        default="eval/results/llm/evaluation_results_004.json",
        help="评估结果JSON文件路径 (默认: eval/results/llm/evaluation_results_004.json)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出JSON文件路径 (可选)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，不打印到控制台"
    )
    
    args = parser.parse_args()
    
    # 读取文件
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"错误: 文件不存在 - {input_path}")
        return 1
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 获取详细结果
    detailed_results = data.get("detailed_results", [])
    if not detailed_results:
        print("错误: 文件中没有找到 'detailed_results' 字段")
        return 1
    
    # 计算统计
    stats = calculate_accuracy(detailed_results)
    formatted = format_results(stats)
    
    # 添加总体统计
    output_data = {
        "source_file": str(input_path),
        "total_questions": data.get("total_questions", len(detailed_results)),
        "overall_accuracy": data.get("accuracy", 0),
        "accuracy_by_major_category": formatted["major"],
        "accuracy_by_minor_category": formatted["minor"],
        "accuracy_by_hierarchical": formatted["hierarchical"],  # 大类->小类层级
        "accuracy_by_combined_category": formatted["combined"],
    }
    
    # 打印结果
    if not args.quiet:
        print_results(formatted)
    
    # 保存到文件
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n📁 结果已保存到: {output_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())

