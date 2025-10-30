#!/usr/bin/env python3
"""
示例脚本一：读取group3的2.1-2.4来生成选择题并使用QAR Refresh进行质量控制
演示第二类QAR（记忆应用能力）的完整处理流程
"""

import sys
import os
import json
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.qa_generator import QARGenerator
from core.qa_refresher import QARRefresher
from llm_interface import LLMInterface
from utils.data_loader import DataLoader
from prompts import get_qa_prompts


def load_group3_data():
    """加载group3下的四个QAR文件"""
    group3_dir = "../data/reference_data/group3"
    qar_files = [
        "2.1.json",  # 约束型内容生成
        "2.2.json",  # 历史目标承接与进度延续
        "2.3.json",  # 矛盾记忆的推理选择
        "2.4.json"   # 主动提醒/偏好矫正
    ]
    
    file_paths = [os.path.join(group3_dir, file_name) for file_name in qar_files]
    
    try:
        # 使用DataLoader批量加载QAR主观题数据
        all_data = DataLoader.load_qar_subjective_batch(file_paths)
        print(f"✓ 成功加载 {len(all_data)} 个QAR主观题")
        return all_data
    except Exception as e:
        print(f"✗ 加载失败: {e}")
        return []


def run_group3_qa_pipeline():
    """运行group3的QAR生成和QA Refresh完整流程"""
    print("="*80)
    print("Group3 QAR选择题生成与QA Refresh示例")
    print("="*80)
    
    # 1. 加载group3数据
    print("\n1. 加载group3数据...")
    group3_data = load_group3_data()
    
    if not group3_data:
        print("✗ 没有加载到任何数据")
        return False
    
    print(f"✓ 成功加载 {len(group3_data)} 个QAR主观题")
    
    # 2. 初始化处理组件
    print("\n2. 初始化处理组件...")
    try:
        llm_interface = LLMInterface()
        generator = QARGenerator()  # QARGenerator会自己创建LLM接口
        refresher = QARRefresher(llm_interface)
        print("✓ 组件初始化成功")
    except Exception as e:
        print(f"✗ 组件初始化失败: {e}")
        return False
    
    # 3. 生成不同类型的QAR选择题并进行Refresh
    print("\n3. 生成QAR选择题并进行质量评估和刷新...")
    qa_types = ['constraint_qa', 'progress_continuation_qa', 'conflict_resolution_qa', 'active_reminder_qa']
    all_qa_entries = []
    refresh_stats = {
        'total_generated': 0,
        'passed_first_time': 0,
        'refreshed_and_passed': 0,
        'leaked': 0,
        'generation_failed': 0
    }
    
    for i, data in enumerate(group3_data):
        qa_type = qa_types[i] if i < len(qa_types) else 'constraint_qa'
        print(f"\n{'='*80}")
        print(f"处理 {i+1}/{len(group3_data)} - {qa_type}")
        print(f"{'='*80}")
        
        try:
            # 步骤1: 生成QAR条目（不进行旧的质量检测）
            print(f"  步骤1: 生成QAR选择题...")
            qa_entry = generator.generate_qa_by_type(
                data, 
                qa_type, 
                verbose=False,
                apply_quality_control=False  # 关键：不使用旧的质量检测
            )
            
            if not qa_entry:
                print(f"  ✗ 生成失败")
                refresh_stats['generation_failed'] += 1
                continue
            
            print(f"  ✓ 生成成功")
            print(f"    问题: {qa_entry.get('Question', 'N/A')[:60]}...")
            refresh_stats['total_generated'] += 1
            
            # 步骤2: 获取原始prompt（用于评估和刷新）
            original_prompt = get_qa_prompts(data, qa_type)
            
            # 步骤3: 使用QAR Refresher进行评估和刷新
            print(f"  步骤2: 质量评估和刷新...")
            processed_qa = refresher.evaluate_and_refresh(
                qa_entry,
                qa_type,
                original_prompt,
                verbose=True
            )
            
            # 更新统计
            if processed_qa.get('is_leaked', False):
                refresh_stats['leaked'] += 1
                print(f"  ✗ 标记为泄漏")
            elif processed_qa.get('refresh_count', 0) == 0:
                refresh_stats['passed_first_time'] += 1
                print(f"  ✓ 首次通过")
            else:
                refresh_stats['refreshed_and_passed'] += 1
                print(f"  ✓ 刷新后通过 (第{processed_qa['refresh_count']}次)")
            
            all_qa_entries.append(processed_qa)
            
        except Exception as e:
            print(f"  ✗ 处理错误: {e}")
            import traceback
            traceback.print_exc()
            refresh_stats['generation_failed'] += 1
    
    if not all_qa_entries:
        print("\n✗ 没有成功生成任何QAR条目")
        return False
    
    print(f"\n✓ 成功处理 {len(all_qa_entries)} 个QAR条目")
    
    # 4. 保存结果
    print(f"\n{'='*80}")
    print("4. 保存结果...")
    print(f"{'='*80}")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "../output/group3_example_results"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存QAR结果（只保存JSON）
        output_file = os.path.join(output_dir, f'group3_qa_results_{timestamp}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_qa_entries, f, ensure_ascii=False, indent=2)
        print(f"✓ QAR结果已保存到: {output_file}")
        
        # 保存统计报告
        stats_report = {
            "processing_info": {
                "timestamp": timestamp,
                "input_files": len(group3_data),
                "qa_types": qa_types,
                "output_directory": output_dir
            },
            "refresh_stats": refresh_stats,
            "refresh_summary": {
                "total_attempted": len(group3_data),
                "total_generated": refresh_stats['total_generated'],
                "generation_failed": refresh_stats['generation_failed'],
                "passed_first_time": refresh_stats['passed_first_time'],
                "refreshed_and_passed": refresh_stats['refreshed_and_passed'],
                "leaked": refresh_stats['leaked'],
                "first_pass_rate": f"{refresh_stats['passed_first_time']/max(refresh_stats['total_generated'],1)*100:.1f}%",
                "refresh_success_rate": f"{refresh_stats['refreshed_and_passed']/max(refresh_stats['total_generated'],1)*100:.1f}%",
                "leakage_rate": f"{refresh_stats['leaked']/max(refresh_stats['total_generated'],1)*100:.1f}%"
            }
        }
        
        stats_file = os.path.join(output_dir, f'group3_refresh_stats_{timestamp}.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_report, f, ensure_ascii=False, indent=2)
        print(f"✓ 统计报告已保存到: {stats_file}")
        
    except Exception as e:
        print(f"✗ 保存结果失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 显示最终统计
    print(f"\n{'='*80}")
    print("5. 最终统计")
    print(f"{'='*80}")
    print(f"总计尝试: {len(group3_data)}")
    print(f"成功生成: {refresh_stats['total_generated']}")
    print(f"生成失败: {refresh_stats['generation_failed']}")
    print(f"首次通过: {refresh_stats['passed_first_time']} ({refresh_stats['passed_first_time']/max(refresh_stats['total_generated'],1)*100:.1f}%)")
    print(f"刷新后通过: {refresh_stats['refreshed_and_passed']} ({refresh_stats['refreshed_and_passed']/max(refresh_stats['total_generated'],1)*100:.1f}%)")
    print(f"标记为泄漏: {refresh_stats['leaked']} ({refresh_stats['leaked']/max(refresh_stats['total_generated'],1)*100:.1f}%)")
    
    # 6. 分析泄漏的QAR
    leaked_qars = [qa for qa in all_qa_entries if qa.get('is_leaked', False)]
    if leaked_qars:
        print(f"\n{'='*80}")
        print(f"标记为泄漏的QAR ({len(leaked_qars)}条):")
        print(f"{'='*80}")
        for i, qa in enumerate(leaked_qars):
            print(f"\n{i+1}. 类型: {qa.get('Type', 'unknown')}")
            print(f"   问题: {qa.get('Question', '')[:80]}...")
            print(f"   刷新次数: {qa.get('refresh_count', 0)}")
            
            # 打印评估历史
            eval_history = qa.get('evaluation_history', [])
            if eval_history:
                print(f"   评估历史:")
                for eval_record in eval_history:
                    attempt = eval_record.get('attempt', 0)
                    evaluation = eval_record.get('evaluation', {})
                    overall_quality = evaluation.get('overall_quality', 'unknown')
                    needs_refresh = evaluation.get('needs_refresh', False)
                    print(f"     尝试{attempt}: {overall_quality} (需要刷新: {needs_refresh})")
    
    print(f"\n{'='*80}")
    print("✓ Group3 QAR处理完成")
    print(f"{'='*80}")
    print(f"\n📁 输出文件:")
    print(f"  QAR结果: group3_qa_results_{timestamp}.json")
    print(f"  统计报告: group3_refresh_stats_{timestamp}.json")
    
    return True


if __name__ == "__main__":
    success = run_group3_qa_pipeline()
    if success:
        print("\n🎉 Group3 QAR处理成功！")
    else:
        print("\n❌ Group3 QAR处理失败！")
        sys.exit(1)
