#!/usr/bin/env python3
"""
Aggregate evaluation results from multiple evermemos batches.

Combines evaluation_results_004.json, 005, 010, 011, 016 into a single report.
Calculates accuracy by question_id categories (major/minor).

Usage:
    python eval/aggregate_evermemos_results.py
    python eval/aggregate_evermemos_results.py --output eval/results/evermemos/aggregated_results.json
"""

import json
import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


# User IDs for the 5 batches
USER_IDS = ["004", "005", "010", "011", "016"]


def parse_question_id(question_id: str) -> tuple[str, str]:
    """
    Parse question_id to extract major and minor categories.
    Example: "MA_U_Top004_031" -> ("MA", "U")
    Example: "P_Skill_Top004_001" -> ("P", "Skill")
    Example: "F_SH_Top004_001" -> ("F", "SH")
    """
    parts = question_id.split("_")
    if len(parts) >= 2:
        major_category = parts[0]
        minor_category = parts[1]
        return major_category, minor_category
    return "Unknown", "Unknown"


def load_evaluation_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load all evaluation result files from the specified directory.

    Returns:
        Dict mapping user_id to evaluation data
    """
    all_results = {}

    for user_id in USER_IDS:
        file_path = results_dir / f"evaluation_results_{user_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                all_results[user_id] = json.load(f)
            print(f"  Loaded: {file_path.name} ({all_results[user_id].get('total_questions', 0)} questions)")
        else:
            print(f"  Warning: {file_path.name} not found")

    return all_results


def calculate_batch_stats(all_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate per-batch statistics.
    """
    batch_stats = {}

    for user_id, data in all_results.items():
        batch_stats[user_id] = {
            "total_questions": data.get("total_questions", 0),
            "correct": data.get("correct", 0),
            "accuracy": data.get("accuracy", 0),
            "accuracy_by_type": data.get("accuracy_by_type", {}),
        }

    return batch_stats


def calculate_category_accuracy(all_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate accuracy by major/minor categories across all batches.
    """
    # Aggregate all detailed results
    all_detailed = []
    for user_id, data in all_results.items():
        detailed = data.get("detailed_results", [])
        all_detailed.extend(detailed)

    # Statistics structure
    stats = {
        "major": defaultdict(lambda: {"total": 0, "correct": 0}),
        "minor": defaultdict(lambda: {"total": 0, "correct": 0}),
        "combined": defaultdict(lambda: {"total": 0, "correct": 0}),
        "hierarchical": defaultdict(lambda: defaultdict(lambda: {"total": 0, "correct": 0})),
    }

    for item in all_detailed:
        question_id = item.get("question_id", "")
        is_correct = item.get("is_correct", False)

        major, minor = parse_question_id(question_id)
        combined_key = f"{major}_{minor}"

        # Update major category stats
        stats["major"][major]["total"] += 1
        if is_correct:
            stats["major"][major]["correct"] += 1

        # Update minor category stats
        stats["minor"][minor]["total"] += 1
        if is_correct:
            stats["minor"][minor]["correct"] += 1

        # Update combined stats
        stats["combined"][combined_key]["total"] += 1
        if is_correct:
            stats["combined"][combined_key]["correct"] += 1

        # Update hierarchical stats (major -> minor)
        stats["hierarchical"][major][minor]["total"] += 1
        if is_correct:
            stats["hierarchical"][major][minor]["correct"] += 1

    return stats


def format_category_results(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format category statistics with accuracy percentages.
    """
    formatted = {}

    for category_type, data in stats.items():
        if category_type == "hierarchical":
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


def print_results(batch_stats: Dict[str, Any], formatted: Dict[str, Any], overall: Dict[str, Any]):
    """
    Print aggregated results in a formatted way.
    """
    print("\n" + "=" * 70)
    print("📊 EverMemos Evaluation Results - Aggregated from 5 Batches")
    print("=" * 70)

    # Per-batch summary
    print("\n🔷 Per-Batch Summary:")
    print("-" * 60)
    print(f"{'User ID':<10} {'Total':>10} {'Correct':>10} {'Accuracy':>15}")
    print("-" * 60)

    for user_id in USER_IDS:
        if user_id in batch_stats:
            stats = batch_stats[user_id]
            acc_pct = f"{stats['accuracy'] * 100:.2f}%"
            print(f"{user_id:<10} {stats['total_questions']:>10} {stats['correct']:>10} {acc_pct:>15}")

    print("-" * 60)
    print(f"{'Total':<10} {overall['total_questions']:>10} {overall['correct']:>10} {overall['accuracy_percent']:>15}")

    # By question type
    print("\n🔹 By Question Type:")
    print("-" * 60)
    print(f"{'Type':<20} {'Total':>10} {'Correct':>10} {'Accuracy':>15}")
    print("-" * 60)

    for qtype, data in overall["accuracy_by_type"].items():
        acc_pct = f"{data['accuracy'] * 100:.2f}%"
        print(f"{qtype:<20} {data['total']:>10} {data['correct']:>10} {acc_pct:>15}")

    # Major category accuracy
    print("\n🔷 Major Category Accuracy:")
    print("-" * 60)
    print(f"{'Category':<10} {'Total':>10} {'Correct':>10} {'Accuracy':>15}")
    print("-" * 60)

    for key, values in sorted(formatted["major"].items()):
        print(f"{key:<10} {values['total']:>10} {values['correct']:>10} {values['accuracy_percent']:>15}")

    # Hierarchical (major -> minor)
    print("\n🔶 Hierarchical (Major -> Minor) Accuracy:")
    print("-" * 65)

    for major, minor_data in sorted(formatted["hierarchical"].items()):
        major_total = sum(v["total"] for v in minor_data.values())
        major_correct = sum(v["correct"] for v in minor_data.values())
        major_acc = major_correct / major_total if major_total > 0 else 0

        print(f"\n  📂 {major} (Total: {major_total}, Correct: {major_correct}, {major_acc*100:.2f}%)")
        print(f"  {'-' * 55}")
        print(f"  {'Minor':<12} {'Total':>10} {'Correct':>10} {'Accuracy':>15}")
        print(f"  {'-' * 55}")

        for minor, values in sorted(minor_data.items()):
            print(f"  {minor:<12} {values['total']:>10} {values['correct']:>10} {values['accuracy_percent']:>15}")

    # Combined category accuracy
    print("\n\n🔸 Combined (Major_Minor) Accuracy:")
    print("-" * 60)
    print(f"{'Category':<15} {'Total':>10} {'Correct':>10} {'Accuracy':>15}")
    print("-" * 60)

    for key, values in sorted(formatted["combined"].items()):
        print(f"{key:<15} {values['total']:>10} {values['correct']:>10} {values['accuracy_percent']:>15}")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate evaluation results from multiple evermemos batches"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="eval/results/evermemos",
        help="Directory containing evaluation_results_*.json files (default: eval/results/evermemos)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output JSON file path (optional)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode - don't print to console"
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Error: Results directory not found - {results_dir}")
        return 1

    print(f"Loading evaluation results from {results_dir}...")
    all_results = load_evaluation_results(results_dir)

    if not all_results:
        print("Error: No evaluation results found")
        return 1

    # Calculate per-batch stats
    batch_stats = calculate_batch_stats(all_results)

    # Calculate overall stats
    total_questions = sum(data.get("total_questions", 0) for data in all_results.values())
    total_correct = sum(data.get("correct", 0) for data in all_results.values())
    overall_accuracy = total_correct / total_questions if total_questions > 0 else 0

    # Aggregate by question type
    type_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for data in all_results.values():
        for qtype, stats in data.get("accuracy_by_type", {}).items():
            type_stats[qtype]["total"] += stats.get("total", 0)
            type_stats[qtype]["correct"] += stats.get("correct", 0)

    accuracy_by_type = {}
    for qtype, stats in type_stats.items():
        accuracy_by_type[qtype] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        }

    overall = {
        "total_questions": total_questions,
        "correct": total_correct,
        "accuracy": overall_accuracy,
        "accuracy_percent": f"{overall_accuracy * 100:.2f}%",
        "accuracy_by_type": accuracy_by_type,
    }

    # Calculate category accuracy
    category_stats = calculate_category_accuracy(all_results)
    formatted = format_category_results(category_stats)

    # Print results
    if not args.quiet:
        print_results(batch_stats, formatted, overall)

    # Build output data
    output_data = {
        "source_directory": str(results_dir),
        "batches": USER_IDS,
        "batches_found": list(all_results.keys()),
        "overall": overall,
        "per_batch": batch_stats,
        "accuracy_by_major_category": formatted["major"],
        "accuracy_by_minor_category": formatted["minor"],
        "accuracy_by_hierarchical": formatted["hierarchical"],
        "accuracy_by_combined_category": formatted["combined"],
    }

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n📁 Results saved to: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
