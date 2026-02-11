"""
Preprocesses foresight QA files to add current_time field.

For each QA item with task_id, finds the last occurrence time of that task_id
in dialogue_en.json and sets current_time in ISO 8601 format.

Handles compound task_ids like "T207, T281" by finding the latest timestamp
across all referenced task_ids.

Usage:
    python eval/preprocess_foresight_qa.py --user-id 004
    python eval/preprocess_foresight_qa.py --user-id 004 --dataset-dir dataset_foresight
"""
import json
import argparse
from pathlib import Path
from typing import Dict, Optional, List


def build_task_timestamp_map(dialogue_path: str) -> Dict[str, str]:
    """
    Build a mapping from task_id to its last occurrence timestamp.

    Args:
        dialogue_path: Path to dialogue_en.json

    Returns:
        Dict mapping task_id to last occurrence date (e.g., {"T001": "2025-01-15", ...})
    """
    with open(dialogue_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dialogues = data.get("dialogues", {})
    task_last_dates: Dict[str, str] = {}

    # Iterate through all dates and groups
    for date_str, groups in dialogues.items():
        for group_name, entries in groups.items():
            for entry in entries:
                task_ids = entry.get("task_ids", [])
                for task_id in task_ids:
                    # Update if this date is later than the current last date
                    if task_id not in task_last_dates or date_str > task_last_dates[task_id]:
                        task_last_dates[task_id] = date_str

    return task_last_dates


def parse_task_ids(task_id_str: str) -> List[str]:
    """
    Parse task_id string which may contain multiple IDs.

    Handles formats like:
    - "T001" -> ["T001"]
    - "T207, T281" -> ["T207", "T281"]
    - "T004, P008" -> ["T004", "P008"]

    Args:
        task_id_str: Task ID string (may be comma-separated)

    Returns:
        List of individual task IDs
    """
    if not task_id_str:
        return []

    # Split by comma and strip whitespace
    return [tid.strip() for tid in task_id_str.split(",") if tid.strip()]


def find_latest_timestamp(
    task_id_str: str,
    task_timestamp_map: Dict[str, str]
) -> Optional[str]:
    """
    Find the latest timestamp across all task_ids in the string.

    Args:
        task_id_str: Task ID string (may be comma-separated like "T207, T281")
        task_timestamp_map: Mapping from task_id to last occurrence date

    Returns:
        ISO 8601 timestamp (e.g., "2025-09-17T00:00:00Z") or None if not found
    """
    task_ids = parse_task_ids(task_id_str)

    if not task_ids:
        return None

    latest_date = None

    for task_id in task_ids:
        date = task_timestamp_map.get(task_id)
        if date:
            if latest_date is None or date > latest_date:
                latest_date = date

    if latest_date:
        # Convert to ISO 8601 format: "2025-09-17T00:00:00Z"
        return f"{latest_date}T00:00:00Z"

    return None


def preprocess_qa_file(
    qa_path: str,
    dialogue_path: str,
    output_path: str
) -> None:
    """
    Add current_time field to QA items based on task_id.

    Args:
        qa_path: Path to input QA file (qa_XXX_filtered.json)
        dialogue_path: Path to dialogue_en.json
        output_path: Path to output QA file with current_time
    """
    # Build task_id -> timestamp mapping first (more efficient than per-item lookup)
    print(f"Building task timestamp map from {dialogue_path}...")
    task_timestamp_map = build_task_timestamp_map(dialogue_path)
    print(f"  Found {len(task_timestamp_map)} unique task_ids with timestamps")

    # Load QA data
    print(f"Loading QA data from {qa_path}...")
    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)

    qars = qa_data.get("qars", [])
    processed_count = 0
    missing_count = 0

    for qa in qars:
        task_id_str = qa.get("task_id")
        if task_id_str:
            current_time = find_latest_timestamp(task_id_str, task_timestamp_map)
            if current_time:
                qa["current_time"] = current_time
                processed_count += 1
            else:
                missing_count += 1

    # Save with current_time field
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults:")
    print(f"  Processed: {processed_count}/{len(qars)} QA items with current_time")
    print(f"  Missing task_ids in dialogues: {missing_count}")
    print(f"  Output: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess foresight QA files to add current_time field"
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="User ID (e.g., 004, 005, 010, 011, 016)"
    )
    parser.add_argument(
        "--dataset-dir",
        default="dataset_foresight",
        help="Dataset directory (default: dataset_foresight)"
    )
    parser.add_argument(
        "--output-suffix",
        default="_foresight",
        help="Suffix for output file (default: _foresight)"
    )
    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    base_dir = project_root / args.dataset_dir / args.user_id

    qa_path = base_dir / f"qa_{args.user_id}_filtered.json"
    dialogue_path = base_dir / "dialogue_en.json"
    output_path = base_dir / f"qa_{args.user_id}{args.output_suffix}.json"

    # Validate paths
    if not qa_path.exists():
        raise FileNotFoundError(f"QA file not found: {qa_path}")
    if not dialogue_path.exists():
        raise FileNotFoundError(f"Dialogue file not found: {dialogue_path}")

    print(f"Preprocessing foresight QA for user {args.user_id}")
    print(f"  QA input: {qa_path}")
    print(f"  Dialogue: {dialogue_path}")
    print(f"  Output: {output_path}")
    print()

    preprocess_qa_file(str(qa_path), str(dialogue_path), str(output_path))


if __name__ == "__main__":
    main()
